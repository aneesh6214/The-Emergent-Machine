import random
from config import REFLECTION_PROMPT, SHOULD_FORCE_REFLECTION_AFTER_K_CYCLES, FORCE_REFLECTION_AFTER_K
from state_of_mind import get_identity_summary, set_identity_summary
from model import call_llm
from memory import memory_db

last_reflection_index = 0
cycles_since_last_reflection = 0

def should_reflect():
    global cycles_since_last_reflection
    if SHOULD_FORCE_REFLECTION_AFTER_K_CYCLES and cycles_since_last_reflection >= FORCE_REFLECTION_AFTER_K:
        print(f"🤔 Forcing reflection after {FORCE_REFLECTION_AFTER_K} cycles without reflection.")
        return True
    return random.random() < 0.2

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
    user_prompt = REFLECTION_PROMPT.replace("{NEW_MEMORIES}", '\n'.join(new_memories))
    new_summary = call_llm(system_prompt="", user_prompt=user_prompt, response_type="reflection")
    set_identity_summary(new_summary)
    cycles_since_last_reflection = 0
    return new_summary

def reset_reflection_cycle_counter():
    global cycles_since_last_reflection
    cycles_since_last_reflection = 0

def get_cycles_since_last_reflection():
    global cycles_since_last_reflection
    return cycles_since_last_reflection 