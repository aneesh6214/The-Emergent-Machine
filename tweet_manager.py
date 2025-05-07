import re
import random
import json
from datetime import datetime
import os

from config import TESTING, LOG_FILE
from generate_tweet import process_new_event
from memory_db import memory
from perception_loader import load_latest_perceptions

def log_tweet_generation(log_entry):
    """Log the tweet generation to a JSONL file for future analysis/training."""
    if not TESTING:
        with open(LOG_FILE, "a", encoding="utf-8") as logf:
            logf.write(json.dumps(log_entry) + "\n")

def generate_reflective_tweet():
    """
    Main function to generate a reflective tweet using unified memory:
    1. Load new perceptions and store into unified memory
    2. Retrieve relevant memories for context
    3. Process through the new prompt system
    4. Store results and log generation
    """
    # 1) Load new perceptions and store into unified memory
    print("🧠 Loading perceptions...")
    perceptions = load_latest_perceptions()
    
    # Process each new perception
    for p in perceptions:
        # Extract the tweet text from the perception
        if "Text:" in p:
            tweet_text = p.split("Text:", 1)[1].split("\n")[0].strip()
            print(f"\n📝 Found tweet: {tweet_text}")
            
            # Get relevant memories
            memory_snippets = memory.retrieve(tweet_text, k=4)
            print(f"\n🧠 Retrieved memories: {memory_snippets}")
            
            # Process through the new system
            result = process_new_event(tweet_text, memory_snippets)
            print(f"\n🤔 Generated perception: {result['perception']}")
            if result["reflection"]:
                print(f"💭 Generated reflection: {result['reflection']}")
            print(f"🐦 Generated tweet: {result['tweet']}")
            
            # Store the perception and any reflection
            memory.add_memory(result["perception"], kind="perception")
            if result["reflection"]:
                memory.add_memory(result["reflection"], kind="reflection")
            
            # Store the tweet perception
            memory.add_memory(result["tweet_perception"], kind="perception")
            
            # Log for fine-tuning
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "perception": result["perception"],
                "reflection": result["reflection"],
                "tweet": result["tweet"],
                "tweet_perception": result["tweet_perception"],
                "context_tweet": tweet_text
            }
            log_tweet_generation(log_entry)
            
            return result["tweet"]
    
    # If no new perceptions, generate a tweet from memory
    print("\n📝 No new perceptions found, generating from memory...")
    memory_snippets = memory.retrieve("", k=4)  # Get most recent memories
    print(f"\n🧠 Retrieved memories: {memory_snippets}")
    
    result = process_new_event("", memory_snippets)
    print(f"\n🤔 Generated perception: {result['perception']}")
    if result["reflection"]:
        print(f"💭 Generated reflection: {result['reflection']}")
    print(f"🐦 Generated tweet: {result['tweet']}")
    
    # Store the tweet perception
    memory.add_memory(result["tweet_perception"], kind="perception")
    
    # Log for fine-tuning
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "perception": result["perception"],
        "reflection": result["reflection"],
        "tweet": result["tweet"],
        "tweet_perception": result["tweet_perception"],
        "context_memories": memory_snippets
    }
    log_tweet_generation(log_entry)
    
    return result["tweet"] 