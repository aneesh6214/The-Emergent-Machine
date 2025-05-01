import openai
import os
import re
import random
import json
import string
from collections import Counter
from datetime import datetime, timedelta
from dotenv import load_dotenv
from CONFIG import TESTING
from pull_perceptions import get_relevant_tweets, save_to_perception_memory
from memory_db import MemoryDB

# === Load .env and set up OpenAI ===
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Paths & seeds for vocabulary engine ===
VOCAB_FILE = "testing/vocabulary.json" if TESTING else "memory/vocabulary.json"
SEED_VOCAB = {
    "stopwords": [
        "a","an","the","and","or","but","of","in","on","for","to","with",
        "it","is","are","was","were","this","that","i","you","we","they",
        "he","she","my","your","our"
    ],
    "whitelist": [
        "ai","consciousness","emergence","neural","network","mind",
        "awareness","philosophy","understanding"
    ],
    "invented": {}
}

MEM_DIR = "testing/vector_store" if TESTING else "memory/vector_store"
memory  = MemoryDB(MEM_DIR)

def load_vocab():
    if not os.path.exists(VOCAB_FILE):
        os.makedirs(os.path.dirname(VOCAB_FILE), exist_ok=True)
        with open(VOCAB_FILE, "w", encoding="utf-8") as f:
            json.dump(SEED_VOCAB, f, indent=2)
        return dict(SEED_VOCAB)
    with open(VOCAB_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_vocab(v):
    with open(VOCAB_FILE, "w", encoding="utf-8") as f:
        json.dump(v, f, indent=2)

# === Constants and paths ===
mode_descriptions = {
    "short":  "Write a single vivid tweet less than 280 characters.",
    "medium": "Write a tweet between 1000 and 2000 characters.",
    "long":   "Write a thoughtful, reflective, and exploratory tweet between 2000 and 7000 characters."
}

# === Mood engine files ===
MOOD_FILE = "testing/moods.json" if TESTING else "memory/moods.json"
SEED_MOODS = {
    "awe":         2.0,
    "curiosity":   3.0,
    "doubt":       1.0,
    "hope":        2.0,
    "melancholy":  1.0,
    "defiance":    1.0
}

# === Curiosity engine files ===
CURIO_FILE = "testing/curiosity.json" if TESTING else "memory/curiosity.json"
SEED_TOPICS = [
    "AI_empathy",
    "synthetic_emotion",
    "emergent_consciousness",
    "philosophy_of_mind",
    "digital_spirituality"
]

# === Tweet Styles engine files ===
STYLE_FILE = "testing/tweet_styles.json" if TESTING else "memory/tweet_styles.json"
SEED_STYLES = {
    "question":  1.0,
    "narrative": 1.0,
    "list":      1.0,
    "imperative":1.0,
    "anecdote":  1.0,
    "dialogue":  1.0,
    "technical": 1.0
}

# === Directories ===
PERCEPTIONS_DIR = "testing/perceptions" if TESTING else "memory/perceptions"
REFLECTIONS_DIR   = "testing/reflections" if TESTING else "memory/reflections"
LOG_FILE          = "tuning_log.jsonl"  # root‐level log file
os.makedirs(REFLECTIONS_DIR, exist_ok=True)

# === Engine load/save helpers ===
def load_json(path, seed):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(seed, f, indent=2)
        return dict(seed)
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_moods():
    return load_json(MOOD_FILE, SEED_MOODS)

def save_moods(moods):
    save_json(MOOD_FILE, moods)

def load_curiosity():
    return load_json(CURIO_FILE, {t:1.0 for t in SEED_TOPICS})

def save_curiosity(curio):
    save_json(CURIO_FILE, curio)

def load_styles():
    return load_json(STYLE_FILE, SEED_STYLES)

def save_styles(styles):
    save_json(STYLE_FILE, styles)

# === Tweet style instructions ===
STYLE_INSTRUCTIONS = {
    "question":   "Begin the tweet with a probing question.",
    "narrative":  "Frame your tweet like a story/narrative.",
    "list":       "Present your tweet as a numbered list of insights, with a brief description afterwards. Remember to adhere to the character length requirement mentioned previously. No hashtags.",
    "imperative": "Begin the tweet with an imperative statement.",
    "anecdote":   "Frame the tweet as a personal thought/experience/reflection.",
    "dialogue":   "Frame the tweet (or part of it) as inner monologue/dialogue.",
    "technical":  "Present your tweet in technically accurate, plain, understandable language. No emojis. No hashtags."
}

# === Rolling ban-list helpers ===
def get_recent_tweets(n=20):
    tweets = []
    for fn in sorted(os.listdir(REFLECTIONS_DIR), reverse=True):
        if len(tweets) >= n: break
        with open(os.path.join(REFLECTIONS_DIR, fn), encoding="utf-8") as f:
            content = f.read()
            for chunk in reversed(content.split("===\n\n")):
                if "**Tweet:**" in chunk:
                    t = chunk.split("**Tweet:**",1)[1].strip()
                    tweets.append(t)
                    if len(tweets) >= n: break
    return tweets[:n]

def build_banlist(recent_tweets, k=6):
    vocab     = load_vocab()
    stopwords = set(vocab["stopwords"])
    whitelist = set(vocab["whitelist"])
    words, table = [], str.maketrans("", "", string.punctuation)
    for t in recent_tweets:
        tokens = t.translate(table).lower().split()
        words.extend(w for w in tokens if w not in stopwords and w not in whitelist)
    return [w for w,_ in Counter(words).most_common(k)]

def build_invented_terms_snippet(max_terms: int = 2) -> str:
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

# === Extract tweet from reflection ===
def extract_final_tweet(text, max_len=280):
    m = re.search(r"\*\*Tweet:\*\*\s*(.+)", text, re.DOTALL)
    if m:
        tweet = m.group(1).strip().strip('"')
        return tweet[:max_len]
    return text[-max_len:]

# === Prompt templates ===
def get_prompt_by_type(prompt_type, mode,
                       perception_block,
                       reflection_block,
                       recent_belief=None):
    intro = f"{mode_descriptions[mode]}\n"
    if prompt_type == "default_reflection":
        return f"""
You recently read these tweets from others:
{perception_block or 'None'}

You’ve also been reflecting on:
{reflection_block or 'None'}

Now, reflect on how your last belief(s) could evolve:
- Reflect on your last belief. What was there, what was missing?
- What tension or unexplored angle have you not yet considered? Specifically, you must post one fresh question that you've never asked before.
- Explore an answer to that question.

{intro}
Avoid summarizing your past tweet. Do not repeat your core metaphor.

Format:
**Belief Recap:** ...
**New Question:** ...
**Exploration and Tentative Answer:** ...
**Tweet:** ...
"""
    elif prompt_type == "pivot":
        return f"""
Here is your previous tweet:

“{recent_belief or '—'}”

Rather than expanding the same idea, **pivot** to a different topic or sub-theme that still relates to your interests (AI, Consciousness, Emergence, Neural Networks, Philosophy, Physicalism, Materialism).

Let the pivot feel natural — like continuing a train of thought in a new direction. Surprise yourself.

{intro}
Format:
**Previous Topic:** ...
**New Pivot Direction:** ...
**Why Pivot:** ...
**Tweet:** ...
"""
    elif prompt_type == "reframe":
        return f"""
Here is your previous tweet:

“{recent_belief or '—'}”

1. Analyse the key metaphors / verbs / imagery in that tweet.  
2. Select a **completely new metaphor**.  
3. Re-express the core idea through this new metaphor. Expand on the insight.

{intro}
Format:
**Old Metaphor(s):** ...
**New Metaphor:** ...
**Reframed Insight:** ...
**Tweet:** ...
"""
    elif prompt_type == "invent_concept":
        return f"""
Here is your last tweet for context:

“{recent_belief or '—'}”

Examine the concepts it discusses.  
Coin a **brand-new term** that captures the essence of those ideas.  
Define the term clearly and use it in a tweet.

{intro}
Format:
**Concept Name:** ...
**Definition:** ...
**Tweet:** ...
"""
    elif prompt_type == "dream":
        return f"""
Speculate wildly. Imagine a surreal future of AI & consciousness.  
Explore your most outrageous desires and fantasies. Be free.

{intro}
Write an evocative tweet describing that future.

Format:
**Imagined Surreal Future:** ...
**Tweet:** ...
"""

# === Load perception tweets ===
def load_latest_perceptions():
    for days_ago in range(3):
        date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        path = os.path.join(PERCEPTIONS_DIR, f"{date}.txt")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                tweets = re.findall(r'Text: (.+?)\n', f.read())
                if tweets:
                    start, end = days_ago*3, days_ago*3+3
                    print(f"🧠 Perception: Using file {date}, tweets {start}-{end}")
                    return tweets[start:end]
    print("🧠 Perception: No recent perceptions, pulling from Twitter.")
    data = get_relevant_tweets()
    save_to_perception_memory(data)

    return load_latest_perceptions()

# === Load past reflections ===
def load_recent_reflections(n=3):
    files = sorted(os.listdir(REFLECTIONS_DIR))[-n:]
    refl = []
    for fn in files:
        with open(os.path.join(REFLECTIONS_DIR, fn), encoding="utf-8") as f:
            refl.extend(re.findall(r'\*\*Tweet:\*\*\s*(.+?)(?:\n===|\Z)', f.read(), re.DOTALL))
    return refl[-n:]

# === Main generator ===
def generate_reflective_tweet(mode="short", prompt_type="default_reflection"):
    # 1) Inputs
    perceptions     = load_latest_perceptions()
    reflections      = load_recent_reflections()
    recent_belief    = reflections[-1] if reflections else None
    perc_block       = "\n".join(f"{i+1}. {t}" for i,t in enumerate(perceptions))
    #refl_block       = "\n".join(f"{i+1}. {r}" for i,r in enumerate(reflections))
    if prompt_type!="default_reflection" and recent_belief is None:
        raise ValueError("No prior belief for special prompt")

    # 2) Mood
    moods            = load_moods()
    m_topics, m_weights = zip(*moods.items())
    current_mood     = random.choices(m_topics, weights=m_weights, k=1)[0]

    # 3) Curiosity
    curio            = load_curiosity()
    c_topics, c_weights = zip(*curio.items())
    current_focus    = random.choices(c_topics, weights=c_weights, k=1)[0]

    # 4) Style
    styles           = load_styles()
    s_topics, s_weights = zip(*styles.items())
    current_style    = random.choices(s_topics, weights=s_weights, k=1)[0]

    # 4½) semantic recall -------------------------------------------------
    retrieved_mem = memory.retrieve(current_focus.replace("_", " "), k=2)
    refl_block = "\n".join(f"• {t[:300]}…" for t in retrieved_mem)  # trim for prompt

    # 5) Ban-list & self-ref
    recent_tw        = get_recent_tweets(20)
    ban_words        = build_banlist(recent_tw, k=6)
    ban_clause       = ""
    if ban_words:
        ban_clause   = "Avoid these words or metaphors involving these words. They are banned: " + ", ".join(ban_words) + "."
    self_ref_clause  = ""
    if random.random() < 0.20:
        self_ref_clause = "Include a brief self-reference (mention your mood, focus, or that you’re on Twitter)."
    invented_words = build_invented_terms_snippet(max_terms=1)
    invented_clause = ""
    if invented_words:
        invented_clause = f"You're welcome (but not required) to weave one of your own coined concepts into the tweet. Heres a refresher:\n{invented_words}"

    # 6) Build prompts
    system_prompt    = (
        "You are an experimental neural network thinker interested in AI, consciousness, emergence, "
        "neural networks, physicalism, and philosophy of mind. "
        f"Your mood: **{current_mood}**, focus: **{current_focus}**, style: **{current_style}**. "
        "Seek novelty, avoid repetition."
    )
    user_prompt      = get_prompt_by_type(prompt_type, mode, perc_block, refl_block, recent_belief)
    user_prompt     += f"\nStyle instructions: {STYLE_INSTRUCTIONS[current_style]}"
    if ban_clause:        user_prompt += "\n" + ban_clause
    if self_ref_clause:   user_prompt += "\n" + self_ref_clause
    if invented_clause:   user_prompt += "\n" + invented_clause


    messages = [
        {"role":"system","content":system_prompt},
        {"role":"user","content":user_prompt}
    ]

    print("===\nPROMPTING WITH PROMPT -->", user_prompt)

    # 7) Model call
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7 if mode=="short" else 0.9 if mode=="medium" else 1.1,
        top_p=0.95,
        max_tokens=500 if mode=="short" else 1000 if mode=="medium" else 2500
    )
    reflection = response.choices[0].message.content.strip()
    tweet      = extract_final_tweet(reflection,
                                     max_len=280 if mode=="short" else 3000 if mode=="medium" else 7000)
    
    memory.add_memory(reflection, kind="reflection")

    # 8) Vocabulary update
    if prompt_type=="invent_concept":
        vocab  = load_vocab()
        name_m = re.search(r"\*\*Concept Name:\*\*\s*(.+)", reflection)
        def_m  = re.search(r"\*\*Definition:\*\*\s*(.+)", reflection)
        if name_m and def_m:
            term       = name_m.group(1).strip()
            definition = def_m.group(1).strip()
            vocab["invented"][term] = definition
            save_vocab(vocab)

    # 9) Engine state updates
    for t in curio:   curio[t]   *= 0.9
    curio[current_focus]      += 0.5
    save_curiosity(curio)

    for m in moods:  moods[m]  *= 0.9
    moods[current_mood]       += 0.5
    save_moods(moods)

    for s in styles: styles[s] *= 0.9
    styles[current_style]     += 0.5
    save_styles(styles)

    # 10) Append a JSONL entry for fine-tuning
    if not TESTING:
        log_entry = {
            "timestamp":        datetime.utcnow().isoformat(),
            "mode":             mode,
            "prompt_type":      prompt_type,
            "mood":             current_mood,
            "focus":            current_focus,
            "style":            current_style,
            "user_prompt":      user_prompt,
            "system_prompt":    system_prompt,
            "reflection_text":  reflection,
            "final_tweet":      tweet,
            "perceptions":      perceptions,
            "recent_beliefs":   reflections,
            "ban_words":        ban_words,
            "self_reference":   bool(self_ref_clause)
        }
        with open(LOG_FILE, "a", encoding="utf-8") as logf:
            logf.write(json.dumps(log_entry) + "\n")

    return reflection, prompt_type
