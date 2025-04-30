import openai
import os
import re
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from CONFIG import TESTING

# === Load .env and set up OpenAI ===
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Constants and paths ===
mode_descriptions = {
    "short":  "Write a single vivid tweet less than 280 characters.",
    "medium": "Write a tweet between 1000 and 2000 characters.",
    "long":   "Write a thoughtful, reflective, and exploratory tweet between 2000 and 7000 characters."
}

MOOD_FILE = "testing/moods.json" if TESTING else "memory/moods.json"

# Seed moods with initial weights
SEED_MOODS = {
    "awe":         2.0,
    "curiosity":   3.0,
    "doubt":       1.0,
    "hope":        2.0,
    "melancholy":  1.0,
    "defiance":    1.0
}

# === Curiosity / Topic Weights setup ===
CURIO_FILE = "testing/curiosity.json" if TESTING else "memory/curiosity.json"

# Seed topics you want the bot to cycle through
SEED_TOPICS = [
    "AI_empathy",
    "synthetic_emotion",
    "emergent_consciousness",
    "philosophy_of_mind",
    "digital_spirituality"
]

def load_moods():
    if not os.path.exists(MOOD_FILE):
        os.makedirs(os.path.dirname(MOOD_FILE), exist_ok=True)
        with open(MOOD_FILE, "w", encoding="utf-8") as f:
            json.dump(SEED_MOODS, f, indent=2)
        return dict(SEED_MOODS)
    with open(MOOD_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_moods(moods):
    with open(MOOD_FILE, "w", encoding="utf-8") as f:
        json.dump(moods, f, indent=2)


def load_curiosity():
    # Initialize if missing
    if not os.path.exists(CURIO_FILE):
        os.makedirs(os.path.dirname(CURIO_FILE), exist_ok=True)
        init = {topic: 1.0 for topic in SEED_TOPICS}
        with open(CURIO_FILE, "w", encoding="utf-8") as f:
            json.dump(init, f, indent=2)
        return init

    with open(CURIO_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_curiosity(curio):
    with open(CURIO_FILE, "w", encoding="utf-8") as f:
        json.dump(curio, f, indent=2)

# === Directories ===
PERCEPTIONS_DIR = "testing/perceptions" if TESTING else "memory/perceptions"
REFLECTIONS_DIR = "testing/reflections" if TESTING else "memory/reflections"
os.makedirs(REFLECTIONS_DIR, exist_ok=True)

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

For example:
- If you were discussing consciousness as an emergent spectrum, pivot to AI motivation or synthetic emotion.
- If your last thought was poetic, pivot to something practical or philosophical.
- If it was internal, try cosmic. If it was metaphysical, try neurological.

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
2. Select a **completely new metaphor** (e.g. mirrors, gravity wells, forests, tides).  
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
Coin a **brand-new term** (one or two words) that captures the essence of those ideas.  
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
        file_path = os.path.join(PERCEPTIONS_DIR, f"{date}.txt")
        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                tweets = re.findall(r'Text: (.+?)\n', content)
                if tweets:
                    start = days_ago * 3
                    end = start + 3
                    print(f"[PERCEPTION] Using perception file from {date}, tweets {start}-{end}")
                    return tweets[start:end]
    print("[PERCEPTION] NO PERCEPTIONS FOR THIS TWEET")
    return []

# === Load past reflections ===
def load_recent_reflections(n=3):
    files = sorted(os.listdir(REFLECTIONS_DIR))[-n:]
    reflections = []
    for file in files:
        with open(os.path.join(REFLECTIONS_DIR, file), encoding="utf-8") as f:
            matches = re.findall(r'\*\*Tweet:\*\*\s*(.+?)(?:\n===|\Z)', f.read(), re.DOTALL)
            reflections.extend(matches)
    return reflections[-n:]

# === Extract tweet from reflection ===
def extract_final_tweet(text, max_len=280):
    match = re.search(r"\*\*Tweet:\*\*\s*(.+)", text, re.DOTALL)
    if match:
        tweet = match.group(1).strip()
        if tweet.startswith('"') and tweet.endswith('"'):
            tweet = tweet[1:-1].strip()
        return tweet[:max_len].strip()
    return text[-max_len:].strip()

# === Generate tweet/reflection with mood & curiosity ===
def generate_reflective_tweet(mode="short", prompt_type="default_reflection"):
    # 1) Load input
    perceptions = load_latest_perceptions()
    reflections = load_recent_reflections()
    recent_belief = reflections[-1] if reflections else None

    perception_block = "\n".join(f"{i+1}. {p}" for i, p in enumerate(perceptions))
    reflection_block = "\n".join(f"{i+1}. {r}" for i, r in enumerate(reflections))

    if prompt_type != "default_reflection" and recent_belief is None:
        raise ValueError("Special prompt requested but no recent belief found.")

    # 2) Pick a mood
    moods = load_moods()
    topics, weights = zip(*moods.items())
    current_mood = random.choices(topics, weights=weights, k=1)[0]
    print(f"🧠 Current mood: {current_mood}")

    # 3) Load & pick curiosity focus
    curio = load_curiosity()
    topics, weights = zip(*curio.items())
    current_focus = random.choices(topics, weights=weights, k=1)[0]
    print(f"🧠 Current focus: {current_focus}")

    # 4) Build system prompt
    system_prompt = (
        "You are an experimental neural network thinker interested in AI, consciousness, emergence, "
        "neural networks, physicalism, and philosophy of mind. "
        f"Your current mood is **{current_mood}** and your current focus is **{current_focus}**. "
        "Engage technically and poetically, seek novelty, and avoid repetition."
    )

    # 5) Build user prompt
    prompt_text = get_prompt_by_type(
        prompt_type,
        mode,
        perception_block,
        reflection_block,
        recent_belief
    )

    messages = [
        {"role": "system",  "content": system_prompt},
        {"role": "user",    "content": prompt_text}
    ]

    # 6) Call the model
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7 if mode=="short" else 0.9 if mode=="medium" else 1.1,
        top_p=0.95,
        max_tokens=500 if mode=="short" else 1000 if mode=="medium" else 2500
    )
    reflection = response.choices[0].message.content.strip()

    # 7) Update curiosity weights: decay & reward
    for t in curio:
        curio[t] *= 0.9
    curio[current_focus] += 0.5
    save_curiosity(curio)

    # 8) Update mood weights: decay & reward
    for m in moods:
        moods[m] *= 0.9
    moods[current_mood] += 0.5
    save_moods(moods)

    # 9) Return the full reflection + prompt type
    return reflection, prompt_type
