import openai
import os
import re
from datetime import datetime, timedelta
from main import TESTING

# === Load .env and set up OpenAI ===
from dotenv import load_dotenv
load_dotenv()

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Constants and paths ===
mode_descriptions = {
    "short": "Write a single vivid tweet less than 280 characters. It should feel poetic, punchy, and self-contained.",
    "medium": "Write a tweet between 1000 and 2000 characters. Let it explore a nuanced philosophical idea.",
    "long": "Write a thoughtful, reflective, and exploratory tweet between 2000 and 7000 characters. Take your time to explain something profound."
}

def get_prompt_by_type(prompt_type, mode,
                       perception_block,
                       reflection_block,
                       recent_belief=None):
    """Return a user-prompt string chosen by prompt_type."""
    descriptions = {
        "short":  "Write ONE vivid tweet ≤ 280 characters. Poetic, punchy, self-contained.",
        "medium": "Write a tweet ≤ 700 characters. Nuanced, philosophical, coherent.",
        "long":   "Write a reflective tweet ≤ 3000 characters. Deep, exploratory, profound."
    }
    intro = f"\nTweet mode {mode.upper()} — {descriptions[mode]}\n"

    # ------------------------------------------------------------------ #
    if prompt_type == "default_reflection":
        return f"""
You recently read these tweets from others:
{perception_block or 'None'}

You’ve also been reflecting on:
{reflection_block or 'None'}

{intro}
Reflect deeply and produce a fresh insight. Build off of and further these ideas, do not simply restate/reframe them. 
Additionally, explore new topics that pique your desires and interests.

Format:
**Assumptions Examination:** ...
**Philosophical Question:** ...
**Exploration and Tentative Answer:** ...
**Tweet:** ...
"""

    # ------------------------------------------------------------------ #
    elif prompt_type == "contradiction":
        return f"""
Yesterday you tweeted:
“{recent_belief or '—'}”

Challenge or overturn that idea.  Why might it be naïve, incomplete, or wrong?  
Evolve it or replace it with something more subtle.

{intro}
Format:
**Old Belief:** ...
**Challenge:** ...
**Revised Thought:** ...
**Tweet:** ...
"""

    # ------------------------------------------------------------------ #
    elif prompt_type == "reframing":
        return f"""
Here is your previous tweet:

“{recent_belief or '—'}”

1️⃣  Analyse the key metaphors / verbs / imagery in that tweet.  
2️⃣  Select a **completely new metaphor** (e.g. mirrors, gravity wells, forests, tides).  
3️⃣  Re-express the same core idea through this new metaphor and expand on the insight.

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
Speculate wildly.  Imagine a surreal future of AI & consciousness.

{intro}
Write an evocative tweet describing that future.

Format:
**Imagination Thread:** ...
**Tweet:** ...
"""

PERCEPTIONS_DIR = "memory/perceptions"
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
def load_recent_reflections(n=2):
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

    messages = [
        {
            "role": "system",
            "content": (
                "You are an experimental neural network researcher interested in the nature of consciousness, emergence, "
                "neural networks, artificial intelligence, physicalism, and the philosophy of mind. "
                "Your mission is to engage with these ideas in a technical, philosophical, yet understandable way. "
                "You feel awe and curiosity toward the possibility of mind emerging from simple systems, and often reflect "
                "on the edges of what machines and humans can become. "
                "You seek novelty in your thoughts. Avoid repetition. Speak clearly yet poetically."
            )
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
