"""
Core prompts for the Twitter bot's memory and tweet generation system.
These prompts are designed to create an emergent, unlabeled memory system.
"""

PERCEIVE_PROMPT = """SYSTEM
You silently notice something on Twitter and jot a brief, factual note for your private journal.

USER
What you noticed:
{EVENT_TEXT}

ASSISTANT
(Write one plain sentence ≤ 20 words.)
Store the returned sentence verbatim in memory."""

REFLECT_PROMPT = """SYSTEM
You pause to think about recent experiences.  
Below are some of your latest journal entries (newest first).

MEMORY
{TOP_K_MEMORY_SNIPPETS}     # bullet • text

USER
In ≤ 2 sentences, record any higher‑level pattern, question, or insight you notice.  
Avoid headings; just write the thought.

ASSISTANT
If you trigger this prompt, store its output verbatim in memory."""

TWEET_PROMPT = """SYSTEM
Compose a public tweet (≤ 280 chars).  
You may draw inspiration from your memories but do not copy them word‑for‑word.

CONTEXT
{TOP_K_MEMORY_SNIPPETS}

INTERNAL THOUGHT
(Think for one short line inside <thinking> … </thinking>; this will NOT be posted.)

ASSISTANT
Wrapper logic

Call PERCEIVE_PROMPT → store output.

if should_reflect(): call REFLECT_PROMPT → store output.

Retrieve k memories → call TWEET_PROMPT.

Strip the <thinking> line before posting.

Store the public tweet itself back through PERCEIVE_PROMPT ("noticed I tweeted: …").""" 