import os
import json
from config import STATE_OF_MIND_PATH, STATE_OF_MIND_SEED, DEFAULT_SUBREDDITS, DEFAULT_TIME_RANGE

def load_state_of_mind():
    if not os.path.exists(STATE_OF_MIND_PATH):
        state = {
            "summary": STATE_OF_MIND_SEED,
            "followed_subreddits": DEFAULT_SUBREDDITS,
        }
        save_state_of_mind(state)
        return state
        
    with open(STATE_OF_MIND_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state_of_mind(state):
    os.makedirs(os.path.dirname(STATE_OF_MIND_PATH), exist_ok=True)
    
    with open(STATE_OF_MIND_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def get_identity_summary():
    state = load_state_of_mind()
    return state.get("summary", "")

def set_identity_summary(new_summary):
    state = load_state_of_mind()
    state["summary"] = new_summary
    save_state_of_mind(state)
    
def get_followed_subreddits():
    state = load_state_of_mind()
    return state.get("followed_subreddits", DEFAULT_SUBREDDITS)

def update_state_from_json(json_state):
    """Update the entire state from a JSON object (typically from reflection)"""
    try:
        # Parse the JSON if it's a string
        if isinstance(json_state, str):
            state_dict = json.loads(json_state)
        else:
            state_dict = json_state
            
        # Validate required keys
        required_keys = ["summary", "followed_subreddits"]
        for key in required_keys:
            if key not in state_dict:
                raise ValueError(f"Missing required key in state: {key}")
        
        # Validate types
        if not isinstance(state_dict["summary"], str):
            raise ValueError("Summary must be a string")
        if not isinstance(state_dict["followed_subreddits"], list):
            raise ValueError("followed_subreddits must be a list")
            
        # Save the updated state
        save_state_of_mind(state_dict)
        return True
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error updating state from JSON: {e}")
        return False 