import os
import time
import random
from datetime import datetime
from generate_tweet import generate_reflective_tweet, extract_final_tweet
import tweepy
from dotenv import load_dotenv

load_dotenv()

# === Configuration ===
HOURS = 5  # Total number of tweet cycles
TESTING = True  # Toggle for testing

REFLECTIONS_DIR = "testing/reflections" if TESTING else "memory/reflections"
TEST_OUTPUT_FILE = "testing/test_tweets.txt"
os.makedirs(REFLECTIONS_DIR, exist_ok=True)

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

# === Main tweet loop ===
if TESTING:
    open(TEST_OUTPUT_FILE, "w").close()

for i in range(HOURS):
    print(f"\n--- Tweet Cycle {i+1}/{HOURS} ---")

    mode = random.choices(["short", "medium", "long"], weights=[0.6, 0.3, 0.1])[0]
    print(f"🧠 Mode: {mode.upper()}")

    reflection, _ = generate_reflective_tweet(mode)
    print("\n🧠 Reflection:\n", reflection)

    limit = 280 if mode == "short" else 700 if mode == "medium" else 3000
    tweet = extract_final_tweet(reflection, max_len=limit)
    print("\n🐦 Final Tweet:\n", tweet)

    if TESTING:
        with open(TEST_OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write("BOT WOULD TWEET: " + tweet + "\n\n")
    else:
        post_to_twitter(tweet)

    # Save full reflection
    today = datetime.now().strftime("%Y-%m-%d")
    outfile = os.path.join(REFLECTIONS_DIR, f"{today}.txt")
    with open(outfile, "a", encoding="utf-8") as f:
        f.write(reflection + "\n\n===\n\n")

    if i < HOURS - 1 and not TESTING:
        print("\n⏳ Sleeping for 1 hour...\n")
        time.sleep(3600)
    elif i < HOURS - 1 and TESTING:
        print("\n⏩ Skipping sleep (testing mode)...\n")
