from config import (
    TWEET_SYSTEM_PROMPT, 
    TWEET_USER_PROMPT, 
    GENERATED_TWEETS_PATH,
    TWEET_LENGTH_MODES, 
    TWEET_LENGTH_PROMPTS,
    NUM_MEMORIES_FOR_TWEET,
    SIMILARITY_THRESHOLD,
    TWEET_TEMPERATURES,
    TWEET_MAX_TOKENS
)
from state_of_mind import get_identity_summary
from recent_perception import get_recent_perception
from model import call_llm, embed_text
from memory import memory_db
from helpers import cosine_similarity
import os
import random
import numpy as np
import math

def get_diverse_recent_memories(n=NUM_MEMORIES_FOR_TWEET, threshold=SIMILARITY_THRESHOLD):
    """Retrieve a diverse set of recent memories using cosine similarity.
    
    Args:
        n: Number of memories to retrieve
        threshold: Maximum cosine similarity allowed between memories (lower = more diverse)
        
    Returns:
        List of diverse memory texts in chronological order
    """
    entries = memory_db.entries[::-1]  # Reverse for most recent first
    selected = []
    selected_vecs = []
    
    # First pass: Try to get n diverse memories with strict threshold
    for text, vector in entries:
        if not selected:
            selected.append(text)
            selected_vecs.append(vector)
        else:
            # Only add if this memory is sufficiently different from all selected ones
            if all(cosine_similarity(vector, v) < threshold for v in selected_vecs):
                selected.append(text)
                selected_vecs.append(vector)
        
        if len(selected) >= n:
            break
    
    # Second pass: If we don't have enough memories, relax the threshold gradually
    if len(selected) < n and len(entries) >= n:
        print(f"🧠 Only found {len(selected)} diverse memories with threshold {threshold}, relaxing criteria...")
        remaining_slots = n - len(selected)
        relaxed_entries = [entry for entry in entries if entry[0] not in selected]
        
        # For each remaining slot, find the most diverse entry from the remaining pool
        for _ in range(remaining_slots):
            if not relaxed_entries:
                break
                
            # Find the memory that's most different from the current selection
            best_entry = None
            lowest_max_similarity = float('inf')
            
            for text, vector in relaxed_entries:
                if not selected_vecs:  # If we somehow have no vectors yet
                    best_entry = (text, vector)
                    break
                    
                # Calculate max similarity to any existing memory
                max_similarity = max(cosine_similarity(vector, v) for v in selected_vecs)
                
                if max_similarity < lowest_max_similarity:
                    lowest_max_similarity = max_similarity
                    best_entry = (text, vector)
            
            if best_entry:
                text, vector = best_entry
                selected.append(text)
                selected_vecs.append(vector)
                relaxed_entries.remove(best_entry)
    
    # Sort chronologically (most recent last)
    return selected[::-1]

def get_top_memories(query_text, a=0.9, b=0.6, k=5, decay='linear'):
    """Return up to k memories ordered so the highest-scoring one is last."""
    if not memory_db.entries:
        return []

    query_emb = embed_text(query_text)
    total     = len(memory_db.entries)
    scored    = []

    for idx, (text, vec) in enumerate(memory_db.entries):  # oldest → newest
        sim = cosine_similarity(vec, query_emb)            # −1 … 1
        # optional: map to 0…1
        sim = 0.5 * (1 + sim)

        # recency score
        age   = total - idx                                # newest ⇒ total
        if decay == 'exp':
            rec = math.exp(-0.1 * age)                     # exponential
        else:  # linear
            rec = age / total

        score = a * sim + b * rec
        scored.append((score, text))

    top = sorted(scored, key=lambda t: t[0], reverse=True)[:k]
    top_sorted = sorted(top, key=lambda t: t[0])           # best last
    return [text for _, text in top_sorted]

def choose_tweet_length_mode():
    r = random.random()
    cumulative = 0.0
    
    for mode, prob in TWEET_LENGTH_MODES:
        cumulative += prob
        if r < cumulative:
            return mode
            
    return TWEET_LENGTH_MODES[-1][0]  # Fallback to last

def tweet_phase(current_perception=None):
    current_summary = get_identity_summary()
    if current_perception is None:
        current_perception = get_recent_perception()
    if current_perception:
        memories = get_top_memories(current_perception)
    else:
        memories = get_diverse_recent_memories()
    bullet_memories = '\n'.join(f"• {m}" for m in memories)
    
    mode = choose_tweet_length_mode()
    tweet_length_line = TWEET_LENGTH_PROMPTS[mode]
    
    system_prompt = TWEET_SYSTEM_PROMPT.replace("{TWEET_LENGTH_LINE}", tweet_length_line)
    user_prompt = TWEET_USER_PROMPT.replace("{BULLET_MEMORIES}", bullet_memories)
    
    print(f"Selected tweet mode: {mode}")
    
    tweet = call_llm(
        system_prompt=system_prompt, 
        user_prompt=user_prompt, 
        response_type="tweet", 
        temperature=TWEET_TEMPERATURES[mode],
        max_tokens=TWEET_MAX_TOKENS[mode]
    )
    
    # Ensure consistent tweet storage format
    os.makedirs(os.path.dirname(GENERATED_TWEETS_PATH), exist_ok=True)
    with open(GENERATED_TWEETS_PATH, "a", encoding="utf-8") as f:
        # The quotes are explicitly added here to make format consistent
        f.write(f'{mode} tweet --> "{tweet}"\n\n')
        
    return tweet 