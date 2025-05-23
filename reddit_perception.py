"""
Module for fetching and processing Reddit posts from the Pushshift dataset
"""

import os
import json
import random
import pickle
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set

import datasets
import numpy as np

from config import (
    REDDIT_CACHE_DIR,
    MIN_SCORE,
    MIN_BODY_LENGTH,
    MAX_BODY_LENGTH,
    REDDIT_PERCEPTION_SYSTEM_PROMPT,
    DEFAULT_TIME_RANGE,
    DEFAULT_SUBREDDITS
)
from model import call_llm, embed_text
from state_of_mind import get_followed_subreddits
from helpers import cosine_similarity

# Cache for seen post IDs
_seen_post_ids: Set[str] = set()
_cache_file = os.path.join(REDDIT_CACHE_DIR, "seen_posts.json")

# Cache file for subreddit-to-indices
CACHE_FILENAME = os.path.join(REDDIT_CACHE_DIR, "subreddit_index.pkl")
DATASET_NAME = "fddemarco/pushshift-reddit"
SPLIT = "train"
CHECKPOINT_INTERVAL = 5_000_000

# Ensure cache dir exists
os.makedirs(REDDIT_CACHE_DIR, exist_ok=True)

# Add module-level cache for the local dataset
_local_dataset = None

def _load_seen_posts():
    """Load the cache of seen post IDs"""
    global _seen_post_ids
    
    # Create cache directory if it doesn't exist
    os.makedirs(REDDIT_CACHE_DIR, exist_ok=True)
    
    # Load seen posts if the file exists
    if os.path.exists(_cache_file):
        with open(_cache_file, "r", encoding="utf-8") as f:
            try:
                _seen_post_ids = set(json.load(f))
                print(f"📝 Loaded {len(_seen_post_ids)} seen post IDs from cache")
            except json.JSONDecodeError:
                _seen_post_ids = set()
                print("⚠️ Error loading seen posts cache, starting fresh")
    else:
        _seen_post_ids = set()
        print("📝 Starting fresh seen posts cache")

def _save_seen_posts():
    """Save the set of seen post IDs to cache"""
    with open(_cache_file, "w", encoding="utf-8") as f:
        json.dump(list(_seen_post_ids), f)

def _process_post(post: Dict) -> Dict:
    """Process a post dictionary to prepare it for the model"""
    # Extract year from created_utc timestamp
    year = datetime.fromtimestamp(post["created_utc"]).year
    
    # Get subreddit without 'r/' prefix
    subreddit = post["subreddit"]
    
    # Get title and body
    title = post["title"] if "title" in post else ""
    
    # Handle selftext - truncate if too long
    body = post.get("selftext", "")
    if len(body) > MAX_BODY_LENGTH:
        body = body[:MAX_BODY_LENGTH] + "... [truncated]"
    
    return {
        "subreddit": subreddit,
        "year": year,
        "title": title,
        "body": body,
        "id": post["id"]
    }

def get_random_post() -> Optional[Dict]:
    """Fetch a random post from the cache based on current preferences (subreddits and time range), avoiding duplicates."""
    try:
        # Load seen posts if not already loaded
        if not _seen_post_ids:
            _load_seen_posts()
        
        # Get current preferences
        subreddits = get_followed_subreddits()
        time_range = DEFAULT_TIME_RANGE
        random_subreddits = subreddits[:]
        random.shuffle(random_subreddits)
        
        cache = load_subreddit_cache() # This loads and cleans the cache
        dataset = load_local_dataset()

        for subreddit_name_from_prefs in random_subreddits:
            key = subreddit_name_from_prefs.lower().replace("r/", "")
            if key not in cache:
                print(f"❌ Subreddit r/{key} does NOT exist in cache (originally {subreddit_name_from_prefs}).")
                continue
            
            start_year, end_year = parse_time_range(time_range)
            # Ensure candidates are actually tuples from the cache
            # and that cache[key] is a list of tuples as expected.
            if not isinstance(cache[key], list):
                print(f"⚠️ WARNING: cache entry for {key} is not a list, but {type(cache[key])}. Skipping.")
                continue

            candidates_for_subreddit = []
            for item in cache[key]:
                if not isinstance(item, (tuple, list)) or len(item) != 2:
                    print(f"⚠️ WARNING: Invalid item structure in cache for {key}: {repr(item)}. Skipping.")
                    continue
                # item[0] is idx, item[1] is year. Both should be integers after clean_cache.
                candidates_for_subreddit.append(item) # item should be (int_idx, int_year)
            
            # Filter by year again, just to be safe, using the integer years from cache
            current_candidates = [(idx_val, year_val) for idx_val, year_val in candidates_for_subreddit if start_year <= year_val <= end_year]
            
            if not current_candidates:
                print(f"❌ No posts found for r/{key} in time range {time_range} after filtering cleaned cache.")
                continue
                
            random.shuffle(current_candidates)
            
            for idx_from_cache, year_from_cache in current_candidates:
                # This is the critical point. idx_from_cache should be an integer.
                print(f"DEBUG: In get_random_post for subreddit '{key}'. Attempting to use idx: {repr(idx_from_cache)}, type: {type(idx_from_cache)}, year: {year_from_cache}")
                
                # Ensure idx_from_cache is indeed an integer before int() call, though int(int_val) is fine.
                if not isinstance(idx_from_cache, int):
                    print(f"ERROR_EXPECTED: idx_from_cache is {repr(idx_from_cache)} (type {type(idx_from_cache)}), NOT an int, right before int() conversion! This will likely fail.")
                    # Attempt conversion, which is expected to fail if it's 'present'
                
                post = dataset[int(idx_from_cache)] # This is where the error occurs
                post_id = post.get("id")
                if post_id and post_id not in _seen_post_ids:
                    _seen_post_ids.add(post_id)
                    _save_seen_posts()
                    return _process_post(post)
            
            print(f"❌ All posts for r/{key} in {time_range} have been seen or failed processing.")
        
        print("❌ No unseen posts found in any followed subreddit and preferred time range.")
        return None
    except Exception as e:
        print(f"❌ Error fetching Reddit post from cache: {e}")
        # Adding traceback here for more context on the error itself
        import traceback
        print(traceback.format_exc())
        return None

def reddit_perception_phase() -> Optional[str]:
    """Run the Reddit perception phase"""
    # Get a random post
    post = get_random_post()
    
    if not post:
        print("❌ No suitable Reddit post found for perception")
        return None
    
    # Format the post for the model
    formatted_prompt = REDDIT_PERCEPTION_SYSTEM_PROMPT.format(
        subreddit=post["subreddit"],
        year=post["year"],
        title=post["title"],
        body=post["body"]
    )
    
    # Log what we're processing
    print(f"🔍 Processing Reddit post from r/{post['subreddit']} ({post['year']}): {post['title'][:50]}...")
    
    # Call the model
    response = call_llm(
        system_prompt=formatted_prompt,
        response_type="reddit_perception"
    )
    
    return response 

def post_in_time_range(post, time_range):
    years = time_range.split("-")
    start_year = int(years[0])
    end_year = int(years[-1])
    created_utc = post.get("created_utc", None)
    if created_utc is None:
        return False
    year = datetime.fromtimestamp(created_utc).year
    return start_year <= year <= end_year

def post_year(post) -> Optional[int]:
    created_utc = post.get("created_utc", None)
    if created_utc is None:
        return None
    return datetime.fromtimestamp(created_utc).year

def is_quality_post(post):
    score = post.get("score")
    if score is None or score < MIN_SCORE:
        return False
    body = post.get("selftext", "")
    if not body or len(body) < MIN_BODY_LENGTH:
        return False
    if body.strip().lower() in ["[deleted]", "[removed]", "none", "null", ""]:
        return False
    return True

def clean_cache(cache):
    """Clean the cache by removing invalid entries.
    Each entry should be a tuple (index, year) where both values can be converted to int.
    Invalid entries are dropped. Returns the cleaned cache dictionary."""
    cleaned_cache = {}
    total_invalid = 0
    for subreddit, posts in cache.items():
        valid_posts = []
        for item in posts:
            try:
                idx = int(item[0])
                year = int(item[1])
                valid_posts.append((idx, year))
            except Exception:
                print(f"Invalid entry found in subreddit {subreddit}: {item}")  # Log invalid entry
                total_invalid += 1
        if valid_posts:
            cleaned_cache[subreddit] = valid_posts
    if total_invalid:
        print(f"Dropped {total_invalid} invalid entries during cache cleaning.")
    return cleaned_cache

def build_subreddit_cache():
    print(f"🔄 Building subreddit-to-quality-indices cache (with years) from local HuggingFace dataset...")
    dataset = datasets.load_dataset(
        DATASET_NAME,
        split=SPLIT,
        verification_mode="no_checks",
        streaming=False
    )
    subreddit_to_indices = {}
    total = len(dataset)
    for idx in range(total):
        post = dataset[idx]
        subreddit = post.get("subreddit", None)
        year = post_year(post)
        if subreddit and year and is_quality_post(post):
            key = subreddit.lower()
            if key not in subreddit_to_indices:
                subreddit_to_indices[key] = []
            subreddit_to_indices[key].append((idx, year))
    with open(CACHE_FILENAME, "wb") as f:
        pickle.dump(subreddit_to_indices, f)
    print(f"✅ Cache built and saved to {CACHE_FILENAME}.")
    print(f"Total subreddits indexed: {len(subreddit_to_indices)}")
    return subreddit_to_indices

def load_subreddit_cache():
    if not os.path.exists(CACHE_FILENAME):
        print(f"❌ Cache not found at {CACHE_FILENAME}. Please build the cache using test_cache.py.")
        return {}
    with open(CACHE_FILENAME, "rb") as f:
        original_cache = pickle.load(f)
    print(f"Loaded cache with {sum(len(v) for v in original_cache.values())} entries before cleaning.")  # Log before cleaning
    original_entries = sum(len(v) for v in original_cache.values())
    cleaned_cache = clean_cache(original_cache)
    cleaned_entries = sum(len(v) for v in cleaned_cache.values())
    if cleaned_entries < original_entries:
        with open(CACHE_FILENAME, "wb") as f:
            pickle.dump(cleaned_cache, f)
        print(f"Cache updated: dropped {original_entries - cleaned_entries} invalid entries and wrote cleaned cache back to disk.")
    print(f"✅ Loaded subreddit cache from {CACHE_FILENAME} ({len(cleaned_cache)} subreddits after cleaning)")
    return cleaned_cache

def load_local_dataset():
    global _local_dataset
    if _local_dataset is not None:
        return _local_dataset
    print("📦 Loading local HuggingFace dataset (non-streaming)...")
    _local_dataset = datasets.load_dataset(
        DATASET_NAME,
        split=SPLIT,
        verification_mode="no_checks",
        streaming=False
    )
    return _local_dataset

def filter_post_by_time(post, time_range=DEFAULT_TIME_RANGE):
    years = time_range.split("-")
    start_year = int(years[0])
    end_year = int(years[-1])
    created_utc = post.get("created_utc", None)
    if created_utc is None:
        return False
    year = datetime.fromtimestamp(created_utc).year
    return start_year <= year <= end_year

def get_random_post_from_subreddit(subreddit: str, time_range=DEFAULT_TIME_RANGE) -> Optional[Dict]:
    """Return a random post from a specific subreddit and time range using the cache."""
    cache = load_subreddit_cache()
    dataset = load_local_dataset()
    key = subreddit.lower().replace("r/", "")
    if key not in cache:
        print(f"❌ Subreddit r/{key} does NOT exist in cache.")
        return None
    indices = cache[key]
    # Filter indices by time range
    filtered_indices = [i for i in indices if filter_post_by_time(dataset[int(i)], time_range)]
    if not filtered_indices:
        print(f"❌ No posts found for r/{key} in time range {time_range}.")
        return None
    idx = random.choice(filtered_indices)
    post = dataset[int(idx)]
    return post

def parse_time_range(time_range: str) -> Tuple[int, int]:
    years = time_range.split("-")
    if len(years) == 1:
        return int(years[0]), int(years[0])
    return int(years[0]), int(years[-1])

def get_random_quality_post(subreddit: str, time_range: str = DEFAULT_TIME_RANGE) -> Optional[Dict]:
    cache = load_subreddit_cache()
    dataset = load_local_dataset()
    key = subreddit.lower().replace("r/", "")
    if key not in cache:
        print(f"❌ Subreddit r/{key} does NOT exist in cache.")
        return None
    start_year, end_year = parse_time_range(time_range)
    candidates = [(idx, year) for (idx, year) in cache[key] if start_year <= year <= end_year]
    if not candidates:
        print(f"❌ No quality posts found for r/{key} in time range {time_range}.")
        return None
    idx, year = random.choice(candidates)
    post = dataset[int(idx)]
    return post

def print_post(post: Dict):
    print("\n--- Random Quality Reddit Post ---")
    print(f"Subreddit: r/{post.get('subreddit', '')}")
    print(f"Year: {datetime.fromtimestamp(post['created_utc']).year if 'created_utc' in post else 'N/A'}")
    print(f"Title: {post.get('title', '')}")
    body = post.get('selftext', '')
    if len(body) > 500:
        body = body[:500] + '... [truncated]'  # For display
    print(f"Body: {body}")
    print(f"Score: {post.get('score', 'N/A')}")
    print(f"ID: {post.get('id', '')}")
    print("-------------------------\n")

def search_reddit_embeddings(query_text: str, top_n: int = 3):
    EMBEDDED_CACHE_FILENAME = "cache/reddit_cache/embedded_subreddit_index.pkl"
    if not os.path.exists(EMBEDDED_CACHE_FILENAME):
        print(f"❌ Embedded subreddit index file not found: {EMBEDDED_CACHE_FILENAME}")
        return []
    with open(EMBEDDED_CACHE_FILENAME, "rb") as f:
        embedded_subreddit_cache = pickle.load(f)
    query_embedding = embed_text(query_text)
    subreddit_scores = []
    for subreddit, embedding in embedded_subreddit_cache.items():
        similarity = cosine_similarity(query_embedding, embedding)
        subreddit_scores.append((similarity, subreddit))
    top_subreddits = sorted(subreddit_scores, key=lambda x: x[0], reverse=True)[:top_n]
    return [sub for sim, sub in top_subreddits]

def main():
    # Import default subreddits and time range from config
    from config import DEFAULT_SUBREDDITS, DEFAULT_TIME_RANGE
    cache = load_subreddit_cache()
    for subreddit in DEFAULT_SUBREDDITS:
        print(f"Fetching post for subreddit: r/{subreddit} (Time Range: {DEFAULT_TIME_RANGE})")
        post = get_random_quality_post(subreddit, DEFAULT_TIME_RANGE)
        if post:
            print_post(post)
        else:
            print(f"No quality post found for subreddit '{subreddit}' in {DEFAULT_TIME_RANGE}.")

if __name__ == "__main__":
    print("TESTING REDDIT PERCEPTION")
    main() 