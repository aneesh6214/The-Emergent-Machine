import re
import random
import json
from datetime import datetime
import os

from config import TESTING, LOG_FILE
from generate_tweet import build_prompt, generate_tweet
from utils import extract_final_tweet
from memory_db import memory
from perception_loader import load_latest_perceptions
from reflection_loader import get_recent_tweets, save_reflection, recent_reflections

from engines import mood_engine, curiosity_engine, style_engine, vocabulary_engine

# Prompt types for tweet generation
ALT_PROMPT_TYPES = ["pivot", "reframe", "invent_concept", "dream"]

def choose_prompt_type(defaults_since_special, next_special_in, has_history=True):
    """
    Choose a prompt type based on the current sequence position.
    We generally follow a pattern of several default prompts followed by a special one.
    """
    if not has_history:
        return "default_reflection", defaults_since_special + 1, next_special_in
    
    elif defaults_since_special < next_special_in:
        return "default_reflection", defaults_since_special + 1, next_special_in
    
    else:
        special_type = random.choice(ALT_PROMPT_TYPES)
        return special_type, 0, random.randint(1, 2)


def extract_concept_from_reflection(reflection):
    """
    If using an 'invent_concept' prompt, extract the concept name and definition
    from the reflection to add to the vocabulary.
    """
    name_m = re.search(r"\*\*Concept Name:\*\*\s*(.+)", reflection)
    def_m = re.search(r"\*\*Definition:\*\*\s*(.+)", reflection)
    
    if name_m and def_m:
        term = name_m.group(1).strip()
        definition = def_m.group(1).strip()
        return term, definition
    
    return None, None


def log_tweet_generation(log_entry):
    """Log the tweet generation to a JSONL file for future analysis/training."""
    if not TESTING:
        with open(LOG_FILE, "a", encoding="utf-8") as logf:
            logf.write(json.dumps(log_entry) + "\n")


def generate_reflective_tweet(mode="short", prompt_type="default_reflection"):
    """
    Main function to generate a reflective tweet. This orchestrates the process:
    1. Load perceptions and recent reflections
    2. Select mood, curiosity focus, and style
    3. Build the prompt
    4. Generate the tweet
    5. Update the memory and engines
    6. Return the reflection and tweet
    """
    # 1) Load inputs from memory/perception
    print("🧠 Loading perceptions and reflections...")
    perceptions = load_latest_perceptions()
    reflections = recent_reflections(memory, n=3)
    recent_belief = reflections[-1] if reflections else None
    
    if prompt_type != "default_reflection" and recent_belief is None:
        raise ValueError("No prior belief for special prompt")

    # 2) Select mood, curiosity focus, and style
    current_mood = mood_engine.process_mood()
    current_focus = curiosity_engine.process_curiosity()
    current_style = style_engine.process_style()
    
    # 3) Semantic recall from unified memory
    query = current_focus.replace("_", " ")
    refl_snips = memory.retrieve(query, k=2, kind="reflection")
    perc_snips = memory.retrieve(query, k=2, kind="perception")
    if not perc_snips:
        perc_snips = memory.sample(k=2, kind="perception")
    
    # Format for prompt
    refl_block = "\n".join(f"• {t[:500]}…" for t in refl_snips) or "None"
    perc_block = "\n".join(f"• {t[:500]}…" for t in perc_snips) or "None"
    
    # 4) Build ban-list and self-reference flag
    recent_tw = get_recent_tweets(20)
    ban_words = vocabulary_engine.build_banlist(recent_tw, k=6)
    
    # Decide if we should self-reference
    self_ref = random.random() < 0.20
    
    # Get invented terms for potential use
    invented_terms = vocabulary_engine.build_invented_terms_snippet(max_terms=1)
    
    # 5) Build the prompt
    prompt_args = {
        'prompt_type': prompt_type,
        'mode': mode,
        'perc_block': perc_block,
        'refl_block': refl_block,
        'recent_belief': recent_belief,
        'current_mood': current_mood,
        'current_focus': current_focus,
        'current_style': current_style, 
        'ban_words': ban_words,
        'self_ref': self_ref,
        'invented_terms': invented_terms
    }
    print("📖 Building the prompt with args: ", prompt_args)
    
    system_prompt, user_prompt = build_prompt(**prompt_args)
    
    # 6) Call LLM to generate tweet
    temperature = 0.7 if mode == "short" else 0.9 if mode == "medium" else 1.1
    max_tokens = 500 if mode == "short" else 1000 if mode == "medium" else 2500
    
    reflection = generate_tweet(system_prompt, user_prompt, temperature, max_tokens)
    
    # 7) Extract final tweet
    limit = 280 if mode == "short" else 3000 if mode == "medium" else 7000
    tweet = extract_final_tweet(reflection, max_len=limit)
    
    # 8) Update memory
    memory.add_memory(reflection, kind="reflection")
    
    # 9) Update vocabulary if concept invented
    if prompt_type == "invent_concept":
        term, definition = extract_concept_from_reflection(reflection)
        if term and definition:
            vocabulary_engine.add_invented_term(term, definition)
    
    # 10) Save reflection to file
    today = datetime.now().strftime("%Y-%m-%d")
    save_reflection(reflection, today)
    
    # 11) Log for fine-tuning
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "mode": mode,
        "prompt_type": prompt_type,
        "mood": current_mood,
        "focus": current_focus,
        "style": current_style,
        "user_prompt": user_prompt,
        "system_prompt": system_prompt,
        "reflection_text": reflection,
        "final_tweet": tweet,
        "perceptions": perceptions,
        "recent_beliefs": reflections,
        "ban_words": ban_words,
        "self_reference": self_ref
    }
    log_tweet_generation(log_entry)
    
    return reflection, tweet, prompt_type 