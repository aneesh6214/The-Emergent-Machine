import random
from utils import load_json, save_json
from config import CURIO_FILE, SEED_TOPICS

def load_curiosity():
    """Load curiosity weights or initialize with seed data."""
    return load_json(CURIO_FILE, {t: 1.0 for t in SEED_TOPICS})

def save_curiosity(curio):
    """Save curiosity weights to file."""
    save_json(CURIO_FILE, curio)

def get_current_focus():
    """Select a curiosity focus based on weighted probabilities."""
    curio = load_curiosity()
    c_topics, c_weights = zip(*curio.items())
    current_focus = random.choices(c_topics, weights=c_weights, k=1)[0]
    return current_focus

def update_curiosity_weights(curio, current_focus, decay_factor=0.9, boost=0.5):
    """
    Update curiosity weights:
    - All curiosities decay by the decay_factor
    - The current focus gets boosted
    """
    for t in curio:
        curio[t] *= decay_factor
    curio[current_focus] += boost
    return curio

def process_curiosity(current_focus=None):
    """
    Process curiosity selection and weight updates.
    If current_focus is None, select one based on weights.
    Returns the selected focus.
    """
    curio = load_curiosity()
    
    if current_focus is None:
        c_topics, c_weights = zip(*curio.items())
        current_focus = random.choices(c_topics, weights=c_weights, k=1)[0]
    
    # Update weights
    curio = update_curiosity_weights(curio, current_focus)
    save_curiosity(curio)
    
    return current_focus

def add_new_curiosity(topic, initial_weight=1.0):
    """Add a new curiosity topic with an initial weight."""
    curio = load_curiosity()
    if topic not in curio:
        curio[topic] = initial_weight
        save_curiosity(curio)
        return True
    return False 