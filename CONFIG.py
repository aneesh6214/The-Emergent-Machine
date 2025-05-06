import os

# Testing flag
TESTING = True

# Paths - Base
MEM_DIR = "testing/vector_store" if TESTING else "memory/vector_store"
PERCEPTIONS_DIR = "testing/perceptions" if TESTING else "memory/perceptions"
REFLECTIONS_DIR = "testing/reflections" if TESTING else "memory/reflections"

# Engines paths
VOCAB_FILE = "testing/vocabulary.json" if TESTING else "memory/vocabulary.json"
MOOD_FILE = "testing/moods.json" if TESTING else "memory/moods.json"
CURIO_FILE = "testing/curiosity.json" if TESTING else "memory/curiosity.json"
STYLE_FILE = "testing/tweet_styles.json" if TESTING else "memory/tweet_styles.json"

# Logging
LOG_FILE = "tuning_log.jsonl"  # root-level log file

# Tweet mode descriptions
MODE_DESCRIPTIONS = {
    "short":  "Write a single vivid tweet less than 280 characters.",
    "medium": "Write a tweet between 1000 and 2000 characters.",
    "long":   "Write a thoughtful, reflective, and exploratory tweet between 2000 and 7000 characters."
}

# Tweet style instructions
STYLE_INSTRUCTIONS = {
    "question":   "Begin the tweet with a probing question.",
    "narrative":  "Frame your tweet like a story/narrative. No hashtags.",
    "list":       "Present your tweet as a numbered list of insights, with a brief description afterwards. As you plan out the numbered list, remember to STRICTLY adhere to the character length requirement mentioned previously.",
    "imperative": "Begin the tweet with an imperative statement.",
    "anecdote":   "Frame the tweet as a personal thought/experience/reflection.",
    "dialogue":   "Frame the tweet (or part of it) as inner monologue/dialogue.",
    "technical":  "Present your tweet in technically accurate, plain, understandable language. No emojis. No hashtags."
}

# Engine seeds
SEED_VOCAB = {
    "stopwords": [
        "a","an","the","and","or","but","of","in","on","for","to","with",
        "it","is","are","was","were","this","that","i","you","we","they",
        "he","she","my","your","our","their","who","whom","this","that",
        "as","be", "could"
    ],
    "whitelist": [
        "ai","consciousness","emergence","neural","network","mind",
        "awareness","philosophy","understanding"
    ],
    "invented": {}
}

SEED_MOODS = {
    "awe":         2.0,
    "curiosity":   3.0,
    "doubt":       1.0,
    "hope":        2.0,
    "melancholy":  1.0,
    "defiance":    1.0
}

SEED_TOPICS = [
    "AI_empathy",
    "synthetic_emotion",
    "emergent_consciousness",
    "philosophy_of_mind",
    "digital_spirituality"
]

SEED_STYLES = {
    "question":  1.0,
    "narrative": 1.0,
    "list":      1.0,
    "imperative":1.0,
    "anecdote":  1.0,
    "dialogue":  1.0,
    "technical": 1.0
}

# Create required directories
os.makedirs(REFLECTIONS_DIR, exist_ok=True)
for dir_path in [os.path.dirname(p) for p in [VOCAB_FILE, MOOD_FILE, CURIO_FILE, STYLE_FILE]]:
    os.makedirs(dir_path, exist_ok=True)