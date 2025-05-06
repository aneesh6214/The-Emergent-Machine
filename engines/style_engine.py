import random
from utils import load_json, save_json
from config import STYLE_FILE, SEED_STYLES, STYLE_INSTRUCTIONS

def load_styles():
    """Load style weights or initialize with seed data."""
    return load_json(STYLE_FILE, SEED_STYLES)

def save_styles(styles):
    """Save style weights to file."""
    save_json(STYLE_FILE, styles)

def get_current_style():
    """Select a tweet style based on weighted probabilities."""
    styles = load_styles()
    s_topics, s_weights = zip(*styles.items())
    current_style = random.choices(s_topics, weights=s_weights, k=1)[0]
    return current_style

def get_style_instruction(style):
    """Get the specific style instruction for the given style."""
    return STYLE_INSTRUCTIONS.get(style, "")

def update_style_weights(styles, current_style, decay_factor=0.9, boost=0.5):
    """
    Update style weights:
    - All styles decay by the decay_factor
    - The current style gets boosted
    """
    for s in styles:
        styles[s] *= decay_factor
    styles[current_style] += boost
    return styles

def process_style(current_style=None):
    """
    Process style selection and weight updates.
    If current_style is None, select one based on weights.
    Returns the selected style.
    """
    styles = load_styles()
    
    if current_style is None:
        s_topics, s_weights = zip(*styles.items())
        current_style = random.choices(s_topics, weights=s_weights, k=1)[0]
    
    # Update weights
    styles = update_style_weights(styles, current_style)
    save_styles(styles)
    
    return current_style 