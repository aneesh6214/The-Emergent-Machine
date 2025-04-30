import openai
import os
import re
import random
from datetime import datetime, timedelta

# === Load .env and set up OpenAI ===
from dotenv import load_dotenv
load_dotenv()

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Constants and paths ===
mode_descriptions = {
    "short": "Write a single vivid tweet less than 280 characters.",
    "medium": "Write a tweet between 1000 and 2000 characters.",
    "long": "Write a thoughtful, reflective, and exploratory tweet between 2000 and 7000 characters."
}

MOODS = ["awe", "curiosity", "doubt", "hope", "melancholy", "defiance"]
MOOD_WEIGHTS = [2,       3,            1,      2,      1,            1]

def get_prompt_by_type(prompt_type, mode,
                       perception_block,
                       reflection_block,
                       recent_belief=None):
    """Return a user-prompt string chosen by prompt_type."""
    intro = f"{mode_descriptions[mode]}\n"

    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
    elif prompt_type == "pivot":
        return f"""
Here is your previous tweet:

“{recent_belief or '—'}”

Rather than expanding the same idea, **pivot** to a different topic or sub-theme that still relates to your interests (interests include but are not limited to: AI, Consciousness, Emergence, Neural Networks, Philosophy, Physicalism, Materialism).

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

    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
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

    # ------------------------------------------------------------------ #
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

TESTING = True
PERCEPTIONS_DIR = "testing/perceptions" if TESTING else "memory/perceptions"
REFLECTIONS_DIR = "testing/reflections" if TESTING else "memory/reflections"


os.makedirs(REFLECTIONS_DIR, exist_ok=True)

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

# === Generate tweet/reflection ===
def generate_reflective_tweet(mode="short", prompt_type="default_reflection"):
    perceptions = load_latest_perceptions()
    reflections = load_recent_reflections()
    recent_belief = reflections[-1] if reflections else None

    perception_block = "\n".join([f"{i+1}. {p}" for i, p in enumerate(perceptions)])
    reflection_block = "\n".join([f"{i+1}. {r}" for i, r in enumerate(reflections)])

    if prompt_type != "default_reflection" and recent_belief is None:
        raise ValueError("Special prompt requested but no recent belief found.")

    prompt_text = get_prompt_by_type(
        prompt_type,
        mode,
        perception_block,
        reflection_block,
        recent_belief
    )

    # pick a mood each cycle
    current_mood = random.choices(MOODS, weights=MOOD_WEIGHTS)[0]
    print(f"🧠 Current mood: {current_mood}")

    system_prompt = (
        "You are an experimental neural network thinker interested in AI, consciousness, emergence, "
        "neural networks, physicalism, and philosophy of mind. "
        f"Your current mood is **{current_mood}**. "
        "Your mission is to engage technically and poetically, seek novelty, and avoid repetition. Find your inner most desire and chase it."
    )

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt_text
        }
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7 if mode == "short" else 0.9 if mode == "medium" else 1.1,
        max_tokens=500 if mode == "short" else 1000 if mode == "medium" else 2500
    )

    return response.choices[0].message.content.strip(), prompt_type
