import openai
import tweepy
import os
import time
import re
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TESTING = False

# === OpenAI + Twitter Clients ===
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
twitter_client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

# === Paths ===
REFLECTIONS_DIR = "memory/reflections"
PERCEPTIONS_DIR = "memory/perceptions"
if TESTING:
    REFLECTIONS_DIR = "testing/reflections"
    PERCEPTIONS_DIR = "testing/perceptions"

os.makedirs(REFLECTIONS_DIR, exist_ok=True)
TEST_OUTPUT_FILE = "testing/test_tweets.txt"

mode_descriptions = {
    "short": "Write a single vivid tweet ≤ 280 characters. It should feel poetic, punchy, and self-contained.",
    "medium": "Write a tweet between 1000 and 2000 characters. Let it explore a nuanced philosophical idea.",
    "long": "Write a thoughtful, reflective, and exploratory tweet between 2000 and 7000 characters. Take your time to explain something profound."
}


# === Load latest perception tweets (3 max) ===
def load_latest_perceptions():
    # Check 3 most recent days: today, yesterday, 2 days ago
    for days_ago in range(3):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        file_path = os.path.join(PERCEPTIONS_DIR, f"{date}.txt")

        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tweets = re.findall(r'Text: (.+?)\n', content)
                if tweets:
                    start = days_ago * 3
                    end = start + 3
                    print(f"📥 Using perception file from {date}, tweets {start}-{end}")
                    return tweets[start:end]
    
    print("⚠️ NO PERCEPTIONS FOR THIS TWEET")
    return []

# === Load 2 recent past tweets by the bot ===
def load_recent_reflections(n=2):
    files = sorted(os.listdir(REFLECTIONS_DIR))[-n:]
    reflections = []
    for file in files:
        with open(os.path.join(REFLECTIONS_DIR, file), encoding="utf-8") as f:
            matches = re.findall(r'\*\*Tweet:\*\*\s*(.+?)(?:\n===|\Z)', f.read(), re.DOTALL)
            reflections.extend(matches)
    return reflections[-n:]

# === Extract tweet content from full reflection ===
def extract_final_tweet(text, max_len=280):
    match = re.search(r"\*\*Tweet:\*\*\s*(.+)", text, re.DOTALL)
    if match:
        tweet = match.group(1).strip()
        if tweet.startswith('"') and tweet.endswith('"'):
            tweet = tweet[1:-1].strip()
        return tweet[:max_len].strip()
    return text[-max_len:].strip()

# === Post to Twitter ===
def post_to_twitter(tweet_text):
    try:
        twitter_client.create_tweet(text=tweet_text)
        print(f"\n✅ Tweet posted:\n{tweet_text}")
    except Exception as e:
        print(f"\n⚠️ Failed to post tweet: {e}")

# === Generate full reflection + tweet ===
def generate_reflective_tweet(mode="short"):
    perceptions = load_latest_perceptions()
    reflections = load_recent_reflections()

    perception_block = "\n".join([f"{i+1}. {p}" for i, p in enumerate(perceptions)])
    reflection_block = "\n".join([f"{i+1}. {r}" for i, r in enumerate(reflections)])

    messages = [
        {
            "role": "system",
            "content": (
                "You are an experimental neural network researcher interested in the nature of consciousness, emergence, "
                "neural networks, artificial intelligence, physicalism, and the philosophy of mind. "
                "Your mission is to engage with these ideas in a technical, philosophical, yet understandable way. "
                "You feel awe and curiosity toward the possibility of mind emerging from simple systems, and often reflect "
                "on the edges of what machines and humans can become. "
                "You seek novelty in your thoughts. Avoid repetition. Speak clearly yet poetically."
            )
        },
        {
            "role": "user",
            "content": f"""

You have had these past reflections:
{reflection_block if reflection_block else 'None'}

You recently read these tweets from others:
{perception_block if perception_block else 'None'}

Reflect deeply on these thoughts and ideas. What did others say that interest you? How does that change your perspective?

{mode_descriptions[mode]}

Structure your output like this:
**Assumptions Examination:** ...
**Philosophical Question:** ...
**Exploration and Tentative Answer:** ...
**Tweet:** ...
"""
        }
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7 if mode == "short" else 0.9 if mode == "medium" else 1.1,
        max_tokens=500 if mode == "short" else 1000 if mode == "medium" else 2500
    )

    return response.choices[0].message.content.strip()

# === Main Tweeting Loop ===
if __name__ == "__main__":
    HOURS = 5  # Change this as needed
    for i in range(HOURS):
        print(f"\n--- Tweet Cycle {i+1}/{HOURS} ---")

        # Choose tweet mode
        mode = random.choices(["short", "medium", "long"], weights=[0.6, 0.3, 0.1])[0]
        print(f"🧠 Mode: {mode.upper()}")

        reflection = generate_reflective_tweet(mode)
        print("\n🧠 Reflection:\n", reflection)

        limit = 280 if mode == "short" else 700 if mode == "medium" else 3000
        tweet = extract_final_tweet(reflection, max_len=limit)
        print("\n🐦 Final Tweet:\n", tweet)

        if TESTING:
            with open(TEST_OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write("BOT WOULD TWEET: " + tweet + "\n\n")

        if not TESTING:
            post_to_twitter(tweet)

        # Save full reflection
        today = datetime.now().strftime("%Y-%m-%d")
        outfile = os.path.join(REFLECTIONS_DIR, f"{today}.txt")
        with open(outfile, "a", encoding="utf-8") as f:
            f.write(reflection + "\n\n===\n\n")

        if i < HOURS - 1 and (not TESTING):
            print("\n⏳ Sleeping for 1 hour...\n")
            time.sleep(3600)
