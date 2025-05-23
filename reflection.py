import random
import json
from config import (
    REFLECTION_PROMPT, 
    REFLECTION_PROMPT_WITH_REDDIT,
    REFLECTION_CHANCE,
    SHOULD_FORCE_REFLECTION_AFTER_K_CYCLES, 
    FORCE_REFLECTION_AFTER_K,
    PERCEPTION_SOURCES
)
from state_of_mind import (
    get_identity_summary, 
    set_identity_summary,
    get_followed_subreddits,
    update_state_from_json
)
from model import call_llm, embed_text
from helpers import strip_surrounding_quotes, cosine_similarity
from memory import memory_db
from recent_perception import get_recent_perception
import pickle
from reddit_perception import search_reddit_embeddings

last_reflection_index = 0
cycles_since_last_reflection = 0

def should_reflect():
    global cycles_since_last_reflection
    
    if SHOULD_FORCE_REFLECTION_AFTER_K_CYCLES and cycles_since_last_reflection >= FORCE_REFLECTION_AFTER_K:
        print(f"🤔 Forcing reflection after {FORCE_REFLECTION_AFTER_K} cycles without reflection.")
        return True
        
    return random.random() < REFLECTION_CHANCE

def gather_new_memories():
    global last_reflection_index
    
    entries = memory_db.entries
    new_memories = [text for (text, vector) in entries[last_reflection_index:]]
    
    if len(new_memories) < 3:
        return None
        
    last_reflection_index = len(entries)
    return new_memories

def reflection_phase():
    global cycles_since_last_reflection
    
    if not should_reflect():
        cycles_since_last_reflection += 1
        print("Reflection phase skipped (random chance).")
        return None
        
    new_memories = gather_new_memories()
    if not new_memories:
        cycles_since_last_reflection += 1
        print("Reflection phase skipped (not enough new memories).")
        return None

    # Check if we're using Reddit perception
    using_reddit = "reddit" in PERCEPTION_SOURCES
    
    summary = get_identity_summary()
    top_subreddits = search_reddit_embeddings(summary, top_n=3)
    subreddit_suggestions = ", ".join([f"r/{s}" for s in top_subreddits])
    
    if using_reddit:
        # Use the updated prompt format with Reddit preferences
        subreddits = get_followed_subreddits()
        
        # Format the prompt
        user_prompt = REFLECTION_PROMPT_WITH_REDDIT.replace(
            "{NEW_MEMORIES}", '\n'.join(f"• {m}" for m in new_memories)
        ).replace(
            "{SUBREDDITS}", ", ".join([f"r/{s}" for s in subreddits])
        ).replace(
            "{SUBREDDIT_SUGGESTIONS}", subreddit_suggestions
        )
        
        # Get the new state as JSON
        response = call_llm(
            system_prompt="", 
            user_prompt=user_prompt, 
            response_type="reflection",
            store_in_memory=False
        )
        
        # Clean up the response to ensure it's valid JSON
        response = strip_surrounding_quotes(response)
        response = response.strip()
        
        try:
            # Parse the JSON response
            state_dict = json.loads(response)
            
            # Update the state
            update_successful = update_state_from_json(state_dict)
            
            if update_successful:
                print(f"🔄 Updated state with new preferences: {len(state_dict['followed_subreddits'])} subreddits")
            else:
                print("❌ Failed to update state from reflection response")
                
            cycles_since_last_reflection = 0
            return state_dict.get("summary", "")
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing reflection response as JSON: {e}")
            print(f"Response was: {response}")
            cycles_since_last_reflection += 1
            return None
    else:
        # Use the original prompt format without Reddit preferences
        user_prompt = REFLECTION_PROMPT.replace("{NEW_MEMORIES}", '\n'.join(f"• {m}" for m in new_memories))
        
        # Get the new summary
        new_summary = call_llm(
            system_prompt="", 
            user_prompt=user_prompt, 
            response_type="reflection",
            store_in_memory=False
        )
        
        # Update the state
        set_identity_summary(new_summary)
        cycles_since_last_reflection = 0
        
        return new_summary

def reset_reflection_cycle_counter():
    global cycles_since_last_reflection
    cycles_since_last_reflection = 0

def get_cycles_since_last_reflection():
    global cycles_since_last_reflection
    return cycles_since_last_reflection 