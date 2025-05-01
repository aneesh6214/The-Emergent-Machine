import tweepy
import os
from dotenv import load_dotenv
load_dotenv()

client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

try:
    client.create_tweet(text="Checking rate limit.")
except tweepy.TooManyRequests as e:
    reset_time = e.response.headers.get("x-rate-limit-reset")
    import datetime
    reset_datetime = datetime.datetime.fromtimestamp(int(reset_time))
    print(f"Rate limit resets at: {reset_datetime}")
