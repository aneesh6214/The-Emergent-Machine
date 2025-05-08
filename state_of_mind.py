import os
import json
from config import STATE_OF_MIND_PATH, STATE_OF_MIND_SEED

def load_state_of_mind():
    if not os.path.exists(STATE_OF_MIND_PATH):
        state = {"summary": STATE_OF_MIND_SEED}
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