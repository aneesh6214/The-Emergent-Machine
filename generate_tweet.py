import openai
import os
from dotenv import load_dotenv
from prompts import PERCEIVE_PROMPT, REFLECT_PROMPT, TWEET_PROMPT
import random
import re

# === Load .env and set up OpenAI ===
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def should_reflect():
    """Determine if we should trigger a reflection based on novelty/randomness."""
    return random.random() < 0.3  # 30% chance to reflect

def perceive_event(event_text):
    """Process a new event through the perception prompt."""
    system_prompt = "You silently notice something on Twitter and jot a brief, factual note for your private journal."
    user_prompt = f"What you noticed:\n{event_text}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print("\n🤖 Perceive Prompt:")
    print(f"System: {system_prompt}")
    print(f"User: {user_prompt}")
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=50
    )
    
    return response.choices[0].message.content.strip()

def reflect_on_memories(memory_snippets):
    """Process memories through the reflection prompt."""
    system_prompt = "You pause to think about recent experiences."
    memory_text = "\n".join(f"• {m}" for m in memory_snippets)
    user_prompt = f"Below are some of your latest journal entries (newest first):\n\n{memory_text}\n\nIn ≤ 2 sentences, record any higher‑level pattern, question, or insight you notice. Avoid headings; just write the thought."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print("\n🤖 Reflect Prompt:")
    print(f"System: {system_prompt}")
    print(f"User: {user_prompt}")
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.8,
        max_tokens=100
    )
    
    return response.choices[0].message.content.strip()

def generate_tweet(memory_snippets):
    """Generate a tweet using the tweet prompt."""
    system_prompt = "Compose a public tweet (≤ 280 chars). You may draw inspiration from your memories but do not copy them word‑for‑word."
    memory_text = "\n".join(f"• {m}" for m in memory_snippets)
    user_prompt = f"Here are some recent thoughts and observations:\n\n{memory_text}\n\nWrite a tweet that shares your perspective on these ideas. Include a brief thought process in <thinking> tags that won't be posted."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print("\n🤖 Tweet Prompt:")
    print(f"System: {system_prompt}")
    print(f"User: {user_prompt}")
    
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.9,
        max_tokens=300
    )
    
    tweet = response.choices[0].message.content.strip()
    print(f"\n🤖 Raw response: {tweet}")
    
    # Remove the thinking line if present
    if "<thinking>" in tweet and "</thinking>" in tweet:
        tweet = re.sub(r"<thinking>.*?</thinking>", "", tweet, flags=re.DOTALL).strip()
    
    return tweet

def process_new_event(event_text, memory_snippets):
    """
    Process a new event through the complete pipeline:
    1. Perceive the event
    2. Optionally reflect
    3. Generate a tweet
    """
    # 1. Perceive the event
    perception = perceive_event(event_text)
    
    # 2. Optionally reflect
    reflection = None
    if should_reflect():
        reflection = reflect_on_memories(memory_snippets)
    
    # 3. Generate tweet
    tweet = generate_tweet(memory_snippets)
    
    # 4. Store the tweet itself as a new perception
    tweet_perception = perceive_event(f"noticed I tweeted: {tweet}")
    
    return {
        "perception": perception,
        "reflection": reflection,
        "tweet": tweet,
        "tweet_perception": tweet_perception
    }
