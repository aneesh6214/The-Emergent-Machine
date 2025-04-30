import tweepy
from dotenv import load_dotenv
import os

load_dotenv()

client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

response = client.create_tweet(text="hello world from GPT-powered consciousness bot 🌌🧠")
print("Tweet posted:", response)