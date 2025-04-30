import os
import time
import random
from datetime import datetime
from generate_tweet import generate_reflective_tweet, extract_final_tweet, load_recent_reflections
import tweepy
from dotenv import load_dotenv
from CONFIG import TESTING

load_dotenv()

# === Configuration ===
HOURS  = 8    # total window in hours
TWEETS = 12   # total number of tweets to post over that window

# compute total window in seconds
total_window = HOURS * 3600

# generate TWEETS random timestamps (in seconds) within [0, total_window)
# sorted so we know how long to sleep between posts
schedule = sorted([0.0] + [random.uniform(0, total_window) for _ in range(TWEETS - 1)])

REFLECTIONS_DIR  = "testing/reflections" if TESTING else "memory/reflections"
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

ALT_PROMPT_TYPES = ["pivot", "reframe", "invent_concept", "dream"]

# counters for default-vs-special sequencing
defaults_since_special = 0
next_special_in       = random.randint(1, 3)

# track the last event time (in seconds from start)
last_time = 0.0

print(f"Scheduling {TWEETS} tweets randomly over {HOURS} hours (total {int(total_window)}s).")
for i, event_time in enumerate(schedule, start=1):
    # how long to sleep from now
    wait = event_time - last_time
    last_time = event_time

    if i == 1:
        wait = 0
        print(f"\n--- Scheduled Tweet {i}/{TWEETS} at +0s (1st tweet) (wait {int(wait)}s) ---")
    else:
        print(f"\n--- Scheduled Tweet {i}/{TWEETS} at +{int(event_time)}s (wait {int(wait)}s) ---")

    if not TESTING:
        print(f"⏳ Sleeping for {int(wait)}s until next tweet...\n")
        time.sleep(wait)
    else:
        print("⏩ (testing mode — skipping sleep)\n")

    # 1) choose length mode
    mode = random.choices(["short", "medium", "long"], weights=[0.6, 0.3, 0.1])[0]
    print(f"🧠 Mode: {mode.upper()}")

    # 2) load recent reflections
    reflections = load_recent_reflections()

    # 3) decide prompt type: 1–3 defaults, then one special
    if not reflections:
        PROMPT_TYPE = "default_reflection"
        defaults_since_special += 1

    elif defaults_since_special < next_special_in:
        PROMPT_TYPE = "default_reflection"
        defaults_since_special += 1

    else:
        PROMPT_TYPE = random.choice(ALT_PROMPT_TYPES)
        defaults_since_special = 0
        next_special_in       = random.randint(1, 3)

    print(f"🧠 Prompt type: {PROMPT_TYPE} "
          f"(defaults since special: {defaults_since_special}/{next_special_in})")

    # 4) generate reflection + tweet
    reflection, _ = generate_reflective_tweet(mode=mode, prompt_type=PROMPT_TYPE)
    print("\n🧠 Reflection:\n", reflection)

    limit = 280 if mode == "short" else 3000 if mode == "medium" else 7000
    tweet = extract_final_tweet(reflection, max_len=limit)
    print("\n🐦 Final Tweet:\n", tweet)

    # 5) output or post
    if TESTING:
        with open(TEST_OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(f"= Tweet - {PROMPT_TYPE} =: " + tweet + "\n\n")
    else:
        post_to_twitter(tweet)

    # 6) persist the full reflection
    today   = datetime.now().strftime("%Y-%m-%d")
    outpath = os.path.join(REFLECTIONS_DIR, f"{today}.txt")
    with open(outpath, "a", encoding="utf-8") as f:
        f.write(reflection + "\n\n===\n\n")

print("\n✅ All scheduled tweets have been generated.")
