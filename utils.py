import json
import os
import re

def load_json(path, seed):
    """Load a JSON file or create it with seed data if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(seed, f, indent=2)
        return dict(seed)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    """Save data to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def extract_final_tweet(text, max_len=280):
    """Extract the tweet text from a full reflection."""
    m = re.search(r"\*\*Tweet:\*\*\s*(.+)", text, re.DOTALL)
    if m:
        tweet = m.group(1).strip().strip('"')
        return tweet[:max_len]
    return text[-max_len:] 