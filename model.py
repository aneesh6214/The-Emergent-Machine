# model.py
# Handles LLM calls using Ollama and provides embeddings.

from __future__ import annotations

import os
import threading
from typing import List

import ollama
from sentence_transformers import SentenceTransformer

from config import IDENTITY_PREFIX, FULL_PRINT
from state_of_mind import get_identity_summary
from memory import memory_db
from helpers import format_prompt_for_display, strip_surrounding_quotes

# --------------------------------------------------------------------------------------
# Ollama configuration
# --------------------------------------------------------------------------------------

OLLAMA_MODEL = "mixtral"  # The model you pulled with ollama pull mixtral

# --------------------------------------------------------------------------------------
# Embeddings
# Using a fast embedding model (all-MiniLM) via sentence-transformers
# --------------------------------------------------------------------------------------

_embedding_model = None
_embedding_lock = threading.Lock()

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        with _embedding_lock:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model

def embed_text(text: str) -> List[float]:
    """Return an embedding for the given text using a fast embedding model (all-MiniLM).
    Uses sentence-transformers all-MiniLM-L6-v2 for efficient embeddings.
    """
    model = get_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


# --------------------------------------------------------------------------------------
# Chat completion wrapper
# --------------------------------------------------------------------------------------

def call_llm(*, 
            prompt: str | None = None, 
            store_in_memory: bool = True, 
            response_type: str = "unknown", 
            system_prompt: str | None = None, 
            user_prompt: str | None = None, 
            temperature: float = 0.7, 
            max_tokens: int = 256) -> str:
    """Generate a response using Ollama.
    
    Creates a unified prompt from system/user input and manages storing 
    responses in memory if requested.
    """
    # Build unified prompt with identity context
    identity_summary = get_identity_summary()
    identity_prefix = IDENTITY_PREFIX.replace("{CURRENT_SUMMARY}", identity_summary)

    unified_prompt_parts: list[str] = [identity_prefix]

    if system_prompt:
        unified_prompt_parts.append("[Instruction]\n" + system_prompt.strip())
    if user_prompt:
        unified_prompt_parts.append("[Input]\n" + user_prompt.strip())
    if prompt and not (system_prompt or user_prompt):
        unified_prompt_parts.append(prompt.strip())

    unified_prompt_parts.append("[Response]:")
    unified_prompt = "\n\n".join(unified_prompt_parts)
    
    # Format prompt for display
    display_prompt = format_prompt_for_display(unified_prompt)
    if FULL_PRINT:
        print(f"🤖 Prompting model w/prompt -->\n--- BEGIN PROMPT ---\n{display_prompt}\n--- END PROMPT ---")

    # Call Ollama API
    try:
        response = ollama.generate(
            model=OLLAMA_MODEL,
        prompt=unified_prompt,
            options={
                'temperature': temperature,
                'num_predict': max_tokens,
            }
    )

        reply: str = response['response'].strip()
        
    except Exception as e:
        print(f"❌ Error calling Ollama: {e}")
        reply = ""
    
    # Strip surrounding quotes if present
    reply = strip_surrounding_quotes(reply)
    
    if FULL_PRINT:
        print(f"🤖 LLM Responded -->\n{reply}")

    # Store in memory if requested
    if store_in_memory and reply:
        persisted_text = reply[7:] if response_type == "tweet" and reply.startswith("Tweet: ") else reply
        vector = embed_text(persisted_text)
        memory_db.add(persisted_text, vector, response_type=response_type)

    return reply 