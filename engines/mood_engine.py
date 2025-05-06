import random
from utils import load_json, save_json
from config import MOOD_FILE, SEED_MOODS

def load_moods():
    """Load mood weights from file or initialize with seed data."""
    return load_json(MOOD_FILE, SEED_MOODS)

def save_moods(moods):
    """Save mood weights to file."""
    save_json(MOOD_FILE, moods)

def get_current_mood():
    """Select a mood based on weighted probabilities."""
    moods = load_moods()
    m_topics, m_weights = zip(*moods.items())
    current_mood = random.choices(m_topics, weights=m_weights, k=1)[0]
    return current_mood

def update_mood_weights(moods, current_mood, decay_factor=0.9, boost=0.5):
    """
    Update mood weights:
    - All moods decay by the decay_factor
    - The current mood gets boosted
    """
    for m in moods:
        moods[m] *= decay_factor
    moods[current_mood] += boost
    return moods

def process_mood(current_mood=None):
    """
    Process mood selection and weight updates.
    If current_mood is None, select one based on weights.
    Returns the selected mood.
    """
    moods = load_moods()
    
    if current_mood is None:
        m_topics, m_weights = zip(*moods.items())
        current_mood = random.choices(m_topics, weights=m_weights, k=1)[0]
    
    # Update weights
    moods = update_mood_weights(moods, current_mood)
    save_moods(moods)
    
    return current_mood 