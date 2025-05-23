import pickle
import random
from config import DEFAULT_SUBREDDITS, DEFAULT_TIME_RANGE
import datasets
from datetime import datetime

# Use a single unified cache file
cache_path = "cache/reddit_cache/subreddit_index.pkl"
DATASET_NAME = "fddemarco/pushshift-reddit"
SPLIT = "train"

# Configuration flags (modify these variables to control behavior)
FLAG_CLEAN_CACHE = True
FLAG_VALIDATE_CACHE = False     # Set to True to validate the cache structure
FLAG_SUBREDDIT = "philosophy"             # Set to a subreddit (e.g., "philosophy") to test a specific subreddit. Leave empty to use default.
FLAG_TIME_RANGE = DEFAULT_TIME_RANGE  # e.g., "2012-2016"


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


def main():
    # Load the unified cache
    try:
        with open(cache_path, "rb") as f:
            cache = pickle.load(f)
    except Exception as ex:
        print(f"Error loading cache: {ex}")
        cache = {}

    print(f"Loaded cache: {len(cache)} subreddits")

    if FLAG_CLEAN_CACHE:
        # Clean the cache by removing any invalid entries
        original_entries = sum(len(v) for v in cache.values())
        cache = clean_cache(cache)
        cleaned_entries = sum(len(v) for v in cache.values())
        print(f"Cleaned cache: {len(cache)} subreddits with {cleaned_entries} valid entries (dropped {original_entries - cleaned_entries} invalid entries).")

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