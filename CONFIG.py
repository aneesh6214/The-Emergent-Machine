import os

# Testing flag
TESTING = True

# Paths - Base
MEM_DIR = "testing/vector_store" if TESTING else "memory/vector_store"
# Perceptions and reflections directories
PERCEPTIONS_DIR = "testing/perceptions" if TESTING else "memory/perceptions"
REFLECTIONS_DIR = "testing/reflections" if TESTING else "memory/reflections"

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

# Create required directories
os.makedirs(REFLECTIONS_DIR, exist_ok=True)