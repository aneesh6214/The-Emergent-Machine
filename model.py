# model.py
# Handles local LLM calls using llama-cpp-python and provides embeddings.

from __future__ import annotations

import os
import threading
from typing import List, Dict, Any

from llama_cpp import Llama  # type: ignore

from config import IDENTITY_PREFIX, LLAMA_MODEL_PATH, FULL_PRINT
from state_of_mind import get_identity_summary
from memory import memory_db

# --------------------------------------------------------------------------------------
# Thread-safe singleton for the llama.cpp model
# --------------------------------------------------------------------------------------

_llm_instance: Llama | None = None
_llm_lock = threading.Lock()


def _get_llm() -> Llama:
    """Load the GGUF model once and reuse it for subsequent calls."""
    global _llm_instance
    if _llm_instance is None:
        with _llm_lock:
            if _llm_instance is None:  # double-check inside the lock
                model_path = os.getenv("LLAMA_MODEL_PATH", LLAMA_MODEL_PATH)
                if not os.path.isfile(model_path):
                    raise FileNotFoundError(
                        f"GGUF model not found at '{model_path}'. Set LLAMA_MODEL_PATH env var or update config."
                    )

                # Initialise the model. Adjust n_ctx / n_gpu_layers to match your hardware.
                _llm_instance = Llama(
                    model_path=model_path,
                    n_ctx=8192,
                    n_threads=os.cpu_count() or 8,
                    n_gpu_layers=-1,  # Use GPU acceleration when available
                    embedding=True,  # Enables create_embedding
                    verbose=FULL_PRINT,
                )
    return _llm_instance


# --------------------------------------------------------------------------------------
# Embeddings
# --------------------------------------------------------------------------------------

def embed_text(text: str) -> List[float]:
    """Return an embedding for the given text using the same model."""
    llm = _get_llm()
    response: Dict[str, Any] = llm.create_embedding(input=text)
    # llama-cpp returns {"data": [{"embedding": [...] , ...}], ...}
    return response["data"][0]["embedding"]


# --------------------------------------------------------------------------------------
# Chat completion wrapper
# --------------------------------------------------------------------------------------

def call_llm(*, prompt: str | None = None, store_in_memory: bool = True, response_type: str = "unknown", system_prompt: str | None = None, user_prompt: str | None = None, temperature: float = 0.7, max_tokens: int = 128) -> str:
    """Generate a response using the local Mixtral model (instruct style).

    The function signature is unchanged so other modules continue to work, but
    internally we now build a *single* prompt string instead of a list of chat
    messages, since Mixtral (instruct‐tuned) expects plain text prompts.
    """

    # ------------------------------------------------------------------
    # Build unified prompt
    # ------------------------------------------------------------------
    identity_summary = get_identity_summary()
    identity_prefix = IDENTITY_PREFIX.replace("{CURRENT_SUMMARY}", identity_summary)

    unified_prompt_parts: list[str] = [identity_prefix]

    if system_prompt:
        unified_prompt_parts.append("[Instruction]\n" + system_prompt.strip())
    if user_prompt:
        unified_prompt_parts.append("[Input]\n" + user_prompt.strip())
    if prompt and not (system_prompt or user_prompt):
        # For calls that only supply a single prompt argument
        unified_prompt_parts.append(prompt.strip())

    unified_prompt_parts.append("[Response]:")
    unified_prompt = "\n\n".join(unified_prompt_parts)

    # Debug print
    print(f"🤖 Prompting model w/prompt -->\n--- BEGIN PROMPT ---\n{unified_prompt}\n--- END PROMPT ---")

    # ------------------------------------------------------------------
    # Call the local LLM using completion endpoint
    # ------------------------------------------------------------------
    llm = _get_llm()
    llm_response = llm.create_completion(
        prompt=unified_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    reply: str = llm_response.get("choices", [{}])[0].get("text", "").strip()
    print(f"🤖 LLM Responded -->\n{reply}")

    # ------------------------------------------------------------------
    # Store in memory (optional)
    # ------------------------------------------------------------------
    if store_in_memory:
        persisted_text = reply[7:] if response_type == "tweet" and reply.startswith("Tweet: ") else reply
        vector = embed_text(persisted_text)
        memory_db.add(persisted_text, vector, response_type=response_type)

    return reply 