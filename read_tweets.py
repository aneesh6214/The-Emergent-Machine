import tweepy
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# === Twitter client (bearer token for read-only access) ===
client = tweepy.Client(bearer_token=os.getenv("TWITTER_BEARER_TOKEN"))

# === Search query ===
SEARCH_QUERY = '(consciousness OR emergence) ("AI" OR "neural networks" OR "mind" OR "sentience") lang:en -is:retweet'
MAX_RESULTS = 10  # Twitter requires minimum of 10 for search_recent_tweets

# === File setup ===
TODAY = datetime.now().strftime("%Y-%m-%d")
PERCEPTION_DIR = "memory/perceptions"
os.makedirs(PERCEPTION_DIR, exist_ok=True)
PERCEPTION_FILE = os.path.join(PERCEPTION_DIR, f"{TODAY}.txt")

def get_relevant_tweets():
    response = client.search_recent_tweets(
        query=SEARCH_QUERY,
        tweet_fields=["created_at", "author_id"],
        expansions=["author_id"],
        max_results=MAX_RESULTS
    )

    user_map = {u["id"]: u["username"] for u in response.includes["users"]} if response.includes else {}
    tweet_data = []

    for tweet in response.data:
        tweet_data.append({
            "username": user_map.get(tweet.author_id, "unknown"),
            "text": tweet.text.strip().replace("\n", " "),
            "timestamp": tweet.created_at.isoformat(),
            "tweet_id": tweet.id
        })

    return tweet_data

def save_to_perception_memory(tweet_data):
    with open(PERCEPTION_FILE, "w", encoding="utf-8") as f:
        for i, tweet in enumerate(tweet_data):
            f.write(f"[Tweet {i+1}]\n")
            f.write(f"Author: @{tweet['username']}\n")
            f.write(f"Text: {tweet['text']}\n")
            f.write(f"Timestamp: {tweet['timestamp']}\n")
            f.write(f"Tweet ID: {tweet['tweet_id']}\n\n")
            f.write(f"[Bot Reflection Prompt Hook]\n")
            f.write("> What ideas or questions does this spark in you?\n")
            f.write("---\n\n")

    print(f"✅ Saved {len(tweet_data)} tweets to {PERCEPTION_FILE}")

if __name__ == "__main__":
    tweet_data = get_relevant_tweets()
    save_to_perception_memory(tweet_data)
