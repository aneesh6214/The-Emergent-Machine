from config import TWEET_SYSTEM_PROMPT, TWEET_USER_PROMPT, GENERATED_TWEETS_PATH, TWEET_LENGTH_MODES, TWEET_LENGTH_PROMPTS
from state_of_mind import get_identity_summary
from model import call_llm
from memory import memory_db
import os
import random
import numpy as np

NUM_MEMORIES_FOR_TWEET = 5
SIMILARITY_THRESHOLD = 0.92

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
        return 0.0
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def get_diverse_recent_memories(n=NUM_MEMORIES_FOR_TWEET, threshold=SIMILARITY_THRESHOLD):
    # Get the n most recent, diverse memories
    entries = memory_db.entries[::-1]  # reverse for most recent first
    selected = []
    selected_vecs = []
    for text, vector in entries:
        if not selected:
            selected.append(text)
            selected_vecs.append(vector)
        else:
            if all(cosine_similarity(vector, v) < threshold for v in selected_vecs):
                selected.append(text)
                selected_vecs.append(vector)
        if len(selected) >= n:
            break
    return selected[::-1]  # return in chronological order

def choose_tweet_length_mode():
    r = random.random()
    cumulative = 0.0
    for mode, prob in TWEET_LENGTH_MODES:
        cumulative += prob
        if r < cumulative:
            return mode
    return TWEET_LENGTH_MODES[-1][0]  # fallback to last

def tweet_phase():
    current_summary = get_identity_summary()
    memories = get_diverse_recent_memories()
    bullet_memories = '\n'.join(f"• {m}" for m in memories)
    mode = choose_tweet_length_mode()
    tweet_length_line = TWEET_LENGTH_PROMPTS[mode]
    system_prompt = TWEET_SYSTEM_PROMPT.replace("{CURRENT_SUMMARY}", current_summary).replace("{TWEET_LENGTH_LINE}", tweet_length_line)
    user_prompt = TWEET_USER_PROMPT.replace("{BULLET_MEMORIES}", bullet_memories)
    print(f"Selected tweet mode: {mode}")
    temperature = 0.9 if mode == "medium" else 1.1 if mode == "long" else 0.7
    max_tokens = 750 if mode == "medium" else 2000 if mode == "long" else 100
    tweet = call_llm(system_prompt=system_prompt, user_prompt=user_prompt, response_type="tweet", temperature=temperature)
    # Write tweet to file
    os.makedirs(os.path.dirname(GENERATED_TWEETS_PATH), exist_ok=True)
    with open(GENERATED_TWEETS_PATH, "a", encoding="utf-8") as f:
        f.write(mode + " tweet --> " + tweet + "\n\n")
    return tweet 