import os
import re
from datetime import datetime
from config import REFLECTIONS_DIR

def get_recent_tweets(n=20):
    """
    Get the n most recent tweets from the reflection files.
    Used for building ban lists and other analysis.
    """
    tweets = []
    for fn in sorted(os.listdir(REFLECTIONS_DIR), reverse=True):
        if len(tweets) >= n: 
            break
        with open(os.path.join(REFLECTIONS_DIR, fn), encoding="utf-8") as f:
            content = f.read()
            for chunk in reversed(content.split("===\n\n")):
                if "**Tweet:**" in chunk:
                    t = chunk.split("**Tweet:**", 1)[1].strip()
                    tweets.append(t)
                    if len(tweets) >= n: 
                        break
    return tweets[:n]

def save_reflection(reflection, today=None):
    """Save a reflection to the appropriate file."""
    if today is None:
        today = datetime.now().strftime("%Y-%m-%d")
    outpath = os.path.join(REFLECTIONS_DIR, f"{today}.txt")
    with open(outpath, "a", encoding="utf-8") as f:
        f.write(reflection + "\n\n===\n\n")
    return outpath

def recent_reflections(memory_db, n=3):
    """Convenience wrapper to get newest reflections from memory DB."""
    return memory_db.recent(kind="reflection", n=n) 