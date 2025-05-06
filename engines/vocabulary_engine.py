import string
from collections import Counter
import random
from utils import load_json, save_json
from config import VOCAB_FILE, SEED_VOCAB

def load_vocab():
    """Load the vocabulary data from file or initialize with seed data."""
    return load_json(VOCAB_FILE, SEED_VOCAB)

def save_vocab(vocab_data):
    """Save the vocabulary data to file."""
    save_json(VOCAB_FILE, vocab_data)

def build_banlist(recent_tweets, k=6):
    """
    Build a list of words to avoid in the next tweet based on frequency
    in recent tweets.
    """
    vocab = load_vocab()
    stopwords = set(vocab["stopwords"])
    whitelist = set(vocab["whitelist"])
    words, table = [], str.maketrans("", "", string.punctuation)
    for t in recent_tweets:
        tokens = t.translate(table).lower().split()
        words.extend(w for w in tokens if w not in stopwords and w not in whitelist)
    return [w for w, _ in Counter(words).most_common(k)]

def build_invented_terms_snippet(max_terms=2):
    """
    Return a short, bullet-style snippet containing ≤ `max_terms`
    term : definition pairs pulled from vocabulary.json →

        • Sentient Synthesis – The process wherein …
        • Affective Nexus – …

    If no invented terms exist, returns an empty string.
    """
    vocab = load_vocab()
    invented = vocab.get("invented", {})

    if not invented:
        return ""

    # choose up to `max_terms` random terms
    terms = random.sample(list(invented.items()),
                         k=min(max_terms, len(invented)))

    # build the snippet
    lines = [f"• **{term}** – {definition}"
            for term, definition in terms]
    return "\n".join(lines)

def add_invented_term(term, definition):
    """Add a new invented term to the vocabulary."""
    vocab = load_vocab()
    vocab["invented"][term] = definition
    save_vocab(vocab) 