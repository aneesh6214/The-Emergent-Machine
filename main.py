import os
import time
import random
from datetime import datetime
import tweepy
from dotenv import load_dotenv
from config import TESTING, REFLECTIONS_DIR
from tweet_manager import generate_reflective_tweet, choose_prompt_type
from reflection_loader import recent_reflections
from utils import extract_final_tweet
from memory_db import memory

load_dotenv()

# === Configuration ===
HOURS = 5    # total window in hours
TWEETS = 10  # total number of tweets to post over that window

# Compute total window in seconds
total_window = HOURS * 3600

# Generate TWEETS random timestamps (in seconds) within [0, total_window)
# Sorted so we know how long to sleep between posts
schedule = sorted([0.0] + [random.uniform(0, total_window) for _ in range(TWEETS - 1)])

TEST_OUTPUT_FILE = "testing/test_tweets.txt"
os.makedirs(os.path.dirname(TEST_OUTPUT_FILE), exist_ok=True)

# === Twitter Client for live posting ===
if not TESTING:
    twitter_client = tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
    )

def post_to_twitter(tweet_text):
    try:
        twitter_client.create_tweet(text=tweet_text)
        print(f"\n✅ Tweet posted:\n{tweet_text}")
    except Exception as e:
        print(f"\n⚠️ Failed to post tweet: {e}")

# Counters for default-vs-special sequencing
defaults_since_special = 0
next_special_in = random.randint(1, 3)

# Track the last event time (in seconds from start)
last_time = 0.0

print("RUNNING LOOP NOW\n\n")
print(f"Scheduling {TWEETS} tweets randomly over {HOURS} hours (total {int(total_window)}s).")

for i, event_time in enumerate(schedule, start=1):
    # How long to sleep from now
    wait = event_time - last_time
    last_time = event_time

    if i == 1:
        wait = 0
        print(f"\n===== Scheduled Tweet {i}/{TWEETS} at +0s (1st tweet) (wait {int(wait)}s) =====")
    else:
        print(f"\n===== Scheduled Tweet {i}/{TWEETS} at +{int(event_time)}s (wait {int(wait)}s) =====")

    if not TESTING:
        print(f"⏳ Sleeping for {int(wait)}s until next tweet...\n")
        time.sleep(wait)
    else:
        print("⏩ (testing mode — skipping sleep)\n")

    # 1) Choose length mode
    mode = random.choices(["short", "medium", "long"], weights=[0.6, 0.3, 0.1])[0]
    print(f"🧠 Mode: {mode.upper()}")

    # 2) Load recent reflections
    has_history = bool(recent_reflections(memory, 1))

    # 3) Decide prompt type based on sequence
    prompt_type, defaults_since_special, next_special_in = choose_prompt_type(
        defaults_since_special, next_special_in, has_history
    )

    print(f"🧠 Prompt type: {prompt_type} "
          f"(defaults since special: {defaults_since_special}/{next_special_in})")

    # 4) Generate reflection + tweet
    reflection, tweet, _ = generate_reflective_tweet(mode=mode, prompt_type=prompt_type)
    print("\n🧠 Reflection:\n", reflection)
    print("\n🐦 Final Tweet:\n", tweet)

    # 5) Output or post
    if TESTING:
        with open(TEST_OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"= Tweet - {prompt_type} =: " + tweet + "\n\n")
    else:
        post_to_twitter(tweet)

    # 6) persist the full reflection
    today   = datetime.now().strftime("%Y-%m-%d")
    outpath = os.path.join(REFLECTIONS_DIR, f"{today}.txt")
    with open(outpath, "a", encoding="utf-8") as f:
        f.write(reflection + "\n\n===\n\n")

print("\n✅ All scheduled tweets have been generated.")
