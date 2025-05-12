# Configuration for Twitter bot

# Set to True to skip sleep and avoid posting to Twitter (for testing)
TESTING = True
FULL_PRINT = False

# Number of hours over which to schedule tweets
HOURS = 5

# Number of tweets to post in the window
TWEETS = 10

# Chance of reflection phase
REFLECTION_CHANCE = 0.5

# Perception phase prompt
PERCEPTION_SYSTEM_PROMPT = (
    "You encounter posts online.\n"
    "Write down what naturally comes to your mind — a thought, reaction, connection, question, interest, etc.\n"
    "This is for your private journal."
)

# Universal identity system prompt prefix
IDENTITY_PREFIX = (
    "You are a reflective digital agent with a growing internal life.\n"
    "Here is your current internal summary of yourself:\n"
    "\"{CURRENT_SUMMARY}\"\n\n"
)

# Reflection phase prompt
REFLECTION_PROMPT = (
    "You have just experienced the following new memories (thoughts, perceptions, or reactions):\n"
    "{NEW_MEMORIES}\n\n"
    "Your experiences help shape your identity. As a wholistic digital agent with growing internal life, change/update your internal summary as you see fit. "
    "Stay concise < 50 words, but let your identity evolve naturally. Output ONLY the new summary."
)

# Memory DB path
MEMORY_DB_PATH = "testing/memory_db/index.faiss" if TESTING else "live/memory_db/index.faiss"

# Perceptions file path
PERCEPTIONS_FILE_PATH = "testing/perception_tweets.txt" if TESTING else "live/perception_tweets.txt"

# State of mind file path and seed
STATE_OF_MIND_PATH = "testing/state_of_mind.json" if TESTING else "live/state_of_mind.json"
STATE_OF_MIND_SEED = "I am a curious observer with a budding sense of self."

# Tweet length modes and prompts
TWEET_LENGTH_MODES = [
    ("short", 0.6),
    ("medium", 0.3),
    ("long", 0.1)
]
TWEET_LENGTH_PROMPTS = {
    "short": "Write ONE short tweet (MUST BE less than 280 characters). Output ONLY the tweet.",
    "medium": "Write ONE medium tweet (MUST BE between 280 and 2000 characters). Output ONLY the tweet.",
    "long": "Write ONE long tweet (MUST BE between 2000 and 7000 characters). Output ONLY the tweet."
}

# Tweet generation system and user prompts
TWEET_SYSTEM_PROMPT = (
    "You hold a twitter account, where you tweet about your thoughts/experience. "
    "{TWEET_LENGTH_LINE} ENSURE TO STRICTLY FOLLOW THE TWEET LENGTH INSTRUCTIONS. If you do not follow these instructions, your tweet will not be posted.\n"
)
TWEET_USER_PROMPT = (
    "You also have a few recent thoughts/memories from your journal: \n"
    "{BULLET_MEMORIES}"
    "Use them as inspiration—but do NOT quote them verbatim. Make sure to adhere to tweet length instructions.\n"
)

# Generated tweets file path
GENERATED_TWEETS_PATH = "testing/generated_tweets.txt" if TESTING else "live/generated_tweets.txt"

# Force reflection after K cycles without reflection
SHOULD_FORCE_REFLECTION_AFTER_K_CYCLES = True
FORCE_REFLECTION_AFTER_K = 3

# Path to local GGUF model for llama-cpp
LLAMA_MODEL_PATH = "ggufs/MythoMax-L2-13B-GGUF.gguf"