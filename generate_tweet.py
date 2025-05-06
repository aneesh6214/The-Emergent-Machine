import openai
import os
from dotenv import load_dotenv
from config import MODE_DESCRIPTIONS, STYLE_INSTRUCTIONS

# === Load .env and set up OpenAI ===
load_dotenv()
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Prompt templates ===
def get_prompt_by_type(prompt_type, mode,
                       perception_block,
                       reflection_block,
                       recent_belief=None):
    intro = f"{MODE_DESCRIPTIONS[mode]}\n"
    if prompt_type == "default_reflection":
        return f"""
You recently read these tweets from others:
{perception_block or 'None'}

You've also been reflecting on:
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

"{recent_belief or '—'}"

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

"{recent_belief or '—'}"

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

"{recent_belief or '—'}"

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

def build_prompt(prompt_type, mode, perc_block, refl_block, recent_belief=None, 
                current_mood=None, current_focus=None, current_style=None, 
                ban_words=None, self_ref=False, invented_terms=None):
    """
    Build the system and user prompts for tweet generation.
    Returns a tuple of (system_prompt, user_prompt)
    """
    # 1) Build system prompt
    system_prompt = (
        "You are an experimental neural network thinker interested in AI, consciousness, emergence, "
        "neural networks, physicalism, and philosophy of mind. "
    )
    
    if current_mood and current_focus and current_style:
        system_prompt += f"Your mood: **{current_mood}**, focus: **{current_focus}**, style: **{current_style}**. "
    
    system_prompt += "Seek novelty, avoid repetition."
    
    # 2) Build user prompt
    user_prompt = get_prompt_by_type(prompt_type, mode, perc_block, refl_block, recent_belief)
    
    if current_style:
        user_prompt += f"\nStyle instructions: {STYLE_INSTRUCTIONS[current_style]}"
    
    # 3) Add ban clause if words to avoid
    if ban_words:
        ban_clause = "Avoid these words or metaphors involving these words. They are banned: " + ", ".join(ban_words) + "."
        user_prompt += "\n" + ban_clause
    
    # 4) Add self-reference if requested
    if self_ref:
        self_ref_clause = "Include a brief self-reference (mention your mood, focus, or that you're on Twitter)."
        user_prompt += "\n" + self_ref_clause
    
    # 5) Add invented terms if any
    if invented_terms:
        invented_clause = f"You're welcome (but not required) to weave one of your own coined concepts into the tweet. Here's a refresher:\n{invented_terms}"
        user_prompt += "\n" + invented_clause
    
    return system_prompt, user_prompt

def generate_tweet(system_prompt, user_prompt, temperature=0.7, max_tokens=500):
    """
    Generate a tweet using the OpenAI API.
    Returns the full reflection text.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print("📖 Prompting OpenAI with -->", user_prompt)
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature,
        top_p=0.95,
        max_tokens=max_tokens
    )
    
    reflection = response.choices[0].message.content.strip()
    return reflection
