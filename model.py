# model.py
# Handles LLM calls using OpenAI

import os
from dotenv import load_dotenv
import openai
from memory import memory_db
from config import IDENTITY_PREFIX
from state_of_mind import get_identity_summary

load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dummy embed function for now (replace with real embedding model)
def embed_text(text):
    response = openai_client.embeddings.create(
        input=[text],
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding


def call_llm(prompt=None, store_in_memory=True, response_type="unknown", system_prompt=None, user_prompt=None, temperature=0.7, max_tokens=128):
    # Always prepend the identity prefix with the current summary to the system prompt
    identity_summary = get_identity_summary()
    identity_prefix = IDENTITY_PREFIX.replace("{CURRENT_SUMMARY}", identity_summary)
    if system_prompt is not None:
        system_prompt = identity_prefix + system_prompt
    elif prompt is not None:
        prompt = identity_prefix + prompt

    # If system_prompt and user_prompt are provided, use them as separate messages
    if system_prompt is not None and user_prompt is not None:
        if response_type == "perception":
            print(f"🧠 Prompting model w/prompt -->\nSYSTEM\n{system_prompt}\nUSER\n{user_prompt}")
        elif response_type == "reflection":
            print(f"🤔 Prompting model w/prompt -->\nSYSTEM\n{system_prompt}\nUSER\n{user_prompt}")
        else:
            print(f"🤖 Prompting model w/prompt -->\nSYSTEM\n{system_prompt}\nUSER\n{user_prompt}")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    elif prompt is not None:
        print(f"🤖 Prompting model w/prompt -->\nSYSTEM\n{prompt}")
        messages = [
            {"role": "system", "content": prompt}
        ]
    else:
        raise ValueError("Must provide either (system_prompt and user_prompt) or prompt.")

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature
    )
    reply = response.choices[0].message.content.strip()
    print(f"🤖 LLM Responded -->\n{reply}")
    if store_in_memory:
        if response_type == "tweet" and reply[0:7] == "Tweet: ":    
            reply = reply[7:]
        vector = embed_text(reply)
        memory_db.add(reply, vector, response_type=response_type)
    return reply 