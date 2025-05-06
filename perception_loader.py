import os
import re
from datetime import datetime, timedelta
from config import PERCEPTIONS_DIR
from pull_perceptions import get_relevant_tweets, write_to_perception_file

def load_latest_perceptions():
    """
    Load the latest perceptions from the perception files.
    If no recent perceptions exist, fetch new ones from Twitter.
    """
    for days_ago in range(3):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        path = os.path.join(PERCEPTIONS_DIR, f"{date}.txt")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                tweets = re.findall(r'Text: (.+?)\n', f.read())
                start, end = days_ago*3, days_ago*3+3
                return tweets[start:end]
            
    # no recent file → fetch & save
    print("🧠 Perception: No recent perceptions, pulling from Twitter.")
    data = get_relevant_tweets()
    write_to_perception_file(data)
    
    # retry load (now file exists)
    return load_latest_perceptions()

def init_perception_memory(mem, perceptions_dir=PERCEPTIONS_DIR):
    """
    On a cold start (empty faiss index), scan every *.txt in perceptions_dir,
    extract lines beginning 'Text: …', and add them as 'perception' memories.
    """
    # only do this once if the index is truly empty
    if mem.index.ntotal > 0:
        return

    total = 0
    for fn in sorted(os.listdir(perceptions_dir)):
        if not fn.endswith(".txt"):
            continue
        path = os.path.join(perceptions_dir, fn)
        content = open(path, encoding="utf-8").read()
        # pull all Text: lines
        for match in re.findall(r"^Text:\s*(.+)$", content, flags=re.MULTILINE):
            text = match.strip()
            if text:
                mem.add_memory(text, kind="perception")
                total += 1

    print(f"✅ Bootstrapped {total} perceptions into vector memory (from {perceptions_dir}).") 