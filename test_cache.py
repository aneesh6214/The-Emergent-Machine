import pickle
import random
import os
from config import DEFAULT_SUBREDDITS, DEFAULT_TIME_RANGE, MIN_SCORE, MIN_BODY_LENGTH
import datasets
from datetime import datetime

# Use a single unified cache file
cache_path = "cache/reddit_cache/subreddit_index.pkl"
DATASET_NAME = "fddemarco/pushshift-reddit"
SPLIT = "train"

# Configuration flags (modify these variables to control behavior)
FLAG_CLEAN_CACHE = True
FLAG_VALIDATE_CACHE = False     # Set to True to validate the cache structure
FLAG_BUILD_CACHE = False        # Set to True to force rebuild the cache
FLAG_SUBREDDIT = "philosophy"             # Set to a subreddit (e.g., "philosophy") to test a specific subreddit. Leave empty to use default.
FLAG_TIME_RANGE = DEFAULT_TIME_RANGE  # e.g., "2012-2016"

# Checkpoint configuration
CHECKPOINT_INTERVAL = 1000000  # Save cache checkpoint every 1mil posts
checkpoint_path = cache_path + ".checkpoint"


def print_post(post):
    print("\n--- Random Quality Reddit Post ---")
    print(f"Subreddit: r/{post.get('subreddit', '')}")
    print(f"Year: {datetime.fromtimestamp(post['created_utc']).year if 'created_utc' in post else 'N/A'}")
    print(f"Title: {post.get('title', '')}")
    body = post.get('selftext', '')
    if len(body) > 500:
        body = body[:500] + '... [truncated]'
    print(f"Body: {body}")
    print(f"Score: {post.get('score', 'N/A')}")
    print(f"ID: {post.get('id', '')}")
    print("-------------------------\n")


def validate_cache(cache):
    """Validate that the cache is a dictionary mapping each subreddit (string) to a list of (index, year) tuples."""
    errors = []
    if not isinstance(cache, dict):
        errors.append("Cache is not a dictionary.")
        return errors
    for subreddit, posts in cache.items():
        if not isinstance(subreddit, str):
            errors.append(f"Subreddit key {subreddit} is not a string.")
        if not isinstance(posts, list):
            errors.append(f"Posts for subreddit {subreddit} is not a list.")
        else:
            for item in posts:
                if not (isinstance(item, (tuple, list)) and len(item) == 2):
                    errors.append(f"Invalid post {item} in subreddit {subreddit}, expected (index, year) tuple.")
                else:
                    idx, year = item
                    if not isinstance(idx, int):
                        errors.append(f"Invalid index {idx} in subreddit {subreddit}, should be an integer.")
                    if not isinstance(year, int):
                        errors.append(f"Invalid year {year} in subreddit {subreddit}, should be an integer.")
    return errors


def clean_cache(cache):
    """Clean the cache by removing invalid entries.
    Each entry should be a tuple (index, year) where both values can be converted to int.
    Invalid entries are dropped. Returns the cleaned cache dictionary.
    """
    cleaned_cache = {}
    total_invalid = 0
    for subreddit, posts in cache.items():
        valid_posts = []
        for item in posts:
            try:
                idx = int(item[0])
                year = int(item[1])
                valid_posts.append((idx, year))
            except Exception as e:
                total_invalid += 1
        if valid_posts:
            cleaned_cache[subreddit] = valid_posts
    if total_invalid:
        print(f"Dropped {total_invalid} invalid entries during cache cleaning.")
    return cleaned_cache


def post_year(post):
    """Extract year from a post's timestamp."""
    created_utc = post.get("created_utc", None)
    if created_utc is None:
        return None
    return datetime.fromtimestamp(created_utc).year


def is_quality_post(post):
    """Check if a post meets quality requirements."""
    score = post.get("score")
    if score is None or score < MIN_SCORE:
        return False
    body = post.get("selftext", "")
    if not body or len(body) < MIN_BODY_LENGTH:
        return False
    if body.strip().lower() in ["[deleted]", "[removed]", "none", "null", ""]:
        return False
    return True


def build_subreddit_cache():
    """Build subreddit-to-quality-indices cache from local HuggingFace dataset."""
    print(f"🔄 Building subreddit-to-quality-indices cache (with years) from local HuggingFace dataset...")
    # Load dataset
    dataset = datasets.load_dataset(
        DATASET_NAME,
        split=SPLIT,
        verification_mode="no_checks",
        streaming=False
    )
    total = len(dataset)
    # Load or initialize cache and resume index
    if os.path.exists(checkpoint_path):
        print(f"🛠️ Resuming from checkpoint: {checkpoint_path}")
        with open(checkpoint_path, 'rb') as f:
            ckpt = pickle.load(f)
        subreddit_to_indices = ckpt.get("cache", {})
        start_idx = ckpt.get("last_idx", 0) + 1
        print(f"Resuming processing at post {start_idx}/{total}...")
    else:
        subreddit_to_indices = {}
        start_idx = 0
    print(f"Processing posts {start_idx} to {total}...")
    # Ensure checkpoint directory exists
    os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)

    for idx in range(start_idx, total):
        # Periodic status update
        if idx % 100000 == 0:
            print(f"Processed {idx}/{total} posts...")

        post = dataset[idx]
        subreddit = post.get("subreddit", None)
        year = post_year(post)
        if subreddit and year and is_quality_post(post):
            key = subreddit.lower()
            if key not in subreddit_to_indices:
                subreddit_to_indices[key] = []
            subreddit_to_indices[key].append((idx, year))
        # Save checkpoint at intervals
        if idx > 0 and idx % CHECKPOINT_INTERVAL == 0:
            with open(checkpoint_path, 'wb') as f:
                pickle.dump({"cache": subreddit_to_indices, "last_idx": idx}, f)
            print(f"🔖 Checkpoint saved at post {idx}")

    # Once complete, remove any checkpoint and save final cache
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print(f"🗑️ Removed checkpoint file {checkpoint_path}")
    # Ensure cache directory exists
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    # Save the final cache
    with open(cache_path, "wb") as f:
        pickle.dump(subreddit_to_indices, f)
    print(f"✅ Cache built and saved to {cache_path}.")
    print(f"Total subreddits indexed: {len(subreddit_to_indices)}")
    return subreddit_to_indices


def main():
    # Check if cache needs to be built
    if FLAG_BUILD_CACHE or not os.path.exists(cache_path):
        print("Building cache...")
        cache = build_subreddit_cache()
    else:
        # Load the existing cache
        try:
            with open(cache_path, "rb") as f:
                cache = pickle.load(f)
                print(f"Loaded existing cache: {len(cache)} subreddits")
        except Exception as ex:
            print(f"Error loading cache: {ex}")
            print("Building new cache...")
            cache = build_subreddit_cache()

    if FLAG_CLEAN_CACHE:
        # Clean the cache by removing any invalid entries
        original_entries = sum(len(v) for v in cache.values())
        cache = clean_cache(cache)
        cleaned_entries = sum(len(v) for v in cache.values())
        print(f"Cleaned cache: {len(cache)} subreddits with {cleaned_entries} valid entries (dropped {original_entries - cleaned_entries} invalid entries).")
        
        # Save cleaned cache back to disk
        if cleaned_entries < original_entries:
            with open(cache_path, "wb") as f:
                pickle.dump(cache, f)
            print("Saved cleaned cache to disk.")

    if FLAG_VALIDATE_CACHE:
        print("\nValidating cache:")
        errors = validate_cache(cache)
        if errors:
            print("Found errors in cache:")
            for err in errors:
                print(" -", err)
        else:
            print("Cache is valid.")
        return

    if FLAG_SUBREDDIT:
        sub = FLAG_SUBREDDIT.lower()
        print(f"\nTesting using cache for r/{sub} with time range {FLAG_TIME_RANGE}")
        if sub not in cache:
            print(f"No entries for r/{sub} in cache.")
        else:
            try:
                start_year, end_year = [int(x) for x in FLAG_TIME_RANGE.split("-")]
            except Exception as ex:
                print("Invalid time range format. Please use e.g., 2012-2016.")
                return
            candidates = [(idx, year) for (idx, year) in cache[sub] if start_year <= year <= end_year]
            if not candidates:
                print(f"No posts for r/{sub} in cache for time range {FLAG_TIME_RANGE}.")
            else:
                idx, year = random.choice(candidates)
                print(f"Selected post index: {idx}, year: {year}")
                dataset = datasets.load_dataset(
                    DATASET_NAME,
                    split=SPLIT,
                    verification_mode="no_checks",
                    streaming=False
                )
                post = dataset[int(idx)]
                print_post(post)
        return

    # Default testing using a default subreddit from config or 'philosophy'
    default_sub = DEFAULT_SUBREDDITS[0].lower() if DEFAULT_SUBREDDITS else "philosophy"
    print(f"\nTesting using cache for default subreddit r/{default_sub} with time range {DEFAULT_TIME_RANGE}")
    if default_sub not in cache:
        print(f"No entries for r/{default_sub} in cache.")
    else:
        try:
            start_year, end_year = [int(x) for x in DEFAULT_TIME_RANGE.split("-")]
        except Exception as ex:
            print("Invalid default time range format.")
            return
        candidates = [(idx, year) for (idx, year) in cache[default_sub] if start_year <= year <= end_year]
        if not candidates:
            print(f"No posts for r/{default_sub} in cache for time range {DEFAULT_TIME_RANGE}.")
        else:
            idx, year = random.choice(candidates)
            print(f"Selected post index: {idx}, year: {year}")
            dataset = datasets.load_dataset(
                DATASET_NAME,
                split=SPLIT,
                verification_mode="no_checks",
                streaming=False
            )
            post = dataset[int(idx)]
            print_post(post)


if __name__ == "__main__":
    main()