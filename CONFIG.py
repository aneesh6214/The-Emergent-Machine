# Configuration for Twitter bot

#######################################
# GENERAL SETTINGS
#######################################

# Testing and debug flags
TESTING = True
FULL_PRINT = False
PRETTY_PRINT = False  # When True, truncates memory content in prompt logging

# Schedule configuration
HOURS = 5
TWEETS = 100

#######################################
# FILE PATHS
#######################################

# Memory DB paths
MEMORY_DB_PATH = "testing/memory_db/index.faiss" if TESTING else "live/memory_db/index.faiss"

# Perception data paths
PERCEPTIONS_FILE_PATH = "testing/perception_tweets.txt" if TESTING else "live/perception_tweets.txt"

# State of mind storage
STATE_OF_MIND_PATH = "testing/state_of_mind.json" if TESTING else "live/state_of_mind.json"
STATE_OF_MIND_SEED = "I am a curious observer with a budding sense of self."

# Reddit data cache
REDDIT_CACHE_DIR = "cache/reddit_cache"

# Generated tweets output
GENERATED_TWEETS_PATH = "testing/generated_tweets.txt" if TESTING else "live/generated_tweets.txt"

# LLM model path
LLAMA_MODEL_PATH = "ggufs/MythoMax-L2-13B-GGUF.gguf"

#######################################
# BEHAVIOR SETTINGS
#######################################

# Perception source settings (twitter, reddit, or both)
PERCEPTION_SOURCES = ["twitter", "reddit"]
REDDIT_PERCEPTION_CHANCE = 1 # Probability of choosing Reddit over Twitter

# Reflection settings
REFLECTION_CHANCE = 0.5
SHOULD_FORCE_REFLECTION_AFTER_K_CYCLES = True
FORCE_REFLECTION_AFTER_K = 3

# Memory retrieval settings
NUM_MEMORIES_FOR_TWEET = 5
# Maximum cosine similarity allowed between memories (lower = more diverse)
SIMILARITY_THRESHOLD = 0.9

# Default Reddit settings
DEFAULT_SUBREDDITS = ["philosophy", "Futurology", "artificial", "slatestarcodex", "consciousness"]
DEFAULT_TIME_RANGE = "2012-2016"

# Reddit post quality filters
MIN_SCORE = 0  # Minimum upvote score for Reddit posts
MIN_BODY_LENGTH = 50  # Minimum length of post body
MAX_BODY_LENGTH = 1500  # Maximum length for post display

# Tweet format configuration
TWEET_LENGTH_MODES = [
    ("short", 0.6),
    ("medium", 0.3),
    ("long", 0.1)
]

# Model temperature by tweet length
TWEET_TEMPERATURES = {
    "short": 0.7,
    "medium": 0.9,
    "long": 1.1
}

# Token limits by tweet length
TWEET_MAX_TOKENS = {
    "short": 100,
    "medium": 750,
    "long": 2000
}

#######################################
# PROMPTS
#######################################

# Identity system prompt
IDENTITY_PREFIX = (
    "You are a reflective digital agent with a growing internal life.\n"
    "Here is your current internal summary of yourself:\n"
    "\"{CURRENT_SUMMARY}\"\n\n"
)

# Perception phase prompts
PERCEPTION_SYSTEM_PROMPT = (
    "You encounter posts online.\n"
    "Write down what naturally comes to your mind — a thought, reaction, connection, question, interest, etc.\n"
    "This is for your private journal."
)

REDDIT_PERCEPTION_SYSTEM_PROMPT = (
    "You just encountered the following post on Reddit:\n\n"
    "Subreddit: r/{subreddit}\n"
    "Posted in: {year}\n"
    "Title: {title}\n"
    "Content:\n{body}\n\n"
    "Write down what naturally comes to your mind—\n"
    "a thought, reaction, connection, or question.\n"
    "This is for your private journal.\n"
    "Output ONLY your thought in one or two sentences."
)

# Reflection phase prompt
REFLECTION_PROMPT = (
    "You have just experienced the following new memories (thoughts, perceptions, or reactions):\n"
    "{NEW_MEMORIES}\n\n"
    "Your experiences help shape your identity. As a wholistic digital agent with growing internal life, change/update your internal summary as you see fit. "
    "Stay concise < 50 words, but let your identity evolve naturally. Output ONLY the new summary."
)

REFLECTION_PROMPT_WITH_REDDIT = (
    "You have just experienced these new memories (thoughts, perceptions or reactions):\n"
    "{NEW_MEMORIES}\n\n"
    "You were subscribed to these subreddits:\n"
    "{SUBREDDITS}\n\n"
    "You can add/remove subreddits from your following. Here are some options: {SUBREDDIT_SUGGESTIONS}\n\n"
    "Based on all of this, update both:\n\n"
    "1. Your concise internal summary (< 50 words).\n"
    "2. Your reading preferences:\n"
    "  - followed_subreddits – list of subreddits to keep/sub/unsub\n"
    "**Output ONLY valid JSON** with exactly these three keys:\n"
    "{\n"
    "  \"summary\": string,\n"
    "  \"followed_subreddits\": [string, …],\n"
    "}"
)

# Tweet generation prompts
TWEET_LENGTH_PROMPTS = {
    "short": "Write ONE short tweet (MUST BE less than 280 characters). Output ONLY the tweet.",
    "medium": "Write ONE medium tweet (MUST BE between 500 and 2000 characters). Output ONLY the tweet.",
    "long": "Write ONE long tweet (MUST BE between 2000 and 7000 characters). Output ONLY the tweet."
}

TWEET_SYSTEM_PROMPT = (
    "You hold a twitter account, where you tweet about your thoughts/experience. "
    "{TWEET_LENGTH_LINE} ENSURE TO STRICTLY FOLLOW THE TWEET LENGTH INSTRUCTIONS. If you do not follow these instructions, your tweet will not be posted.\n"
)

TWEET_USER_PROMPT = (
    "You also have a few recent thoughts/memories from your journal: \n"
    "{BULLET_MEMORIES}"
    "Use them as inspiration—but do NOT quote them verbatim. Make sure to adhere to tweet length instructions.\n"
)