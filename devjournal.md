# Goal
Lets give an LLM the capabilities to post on twitter, along with some initial ideas to explore (consciousness, emergence, and NNs).
What emergent behaviors arise, what enable them? Can we cultivate an emergent personality?
An agentic personality that evolves overtime?

# Entry 1 - Basic Tweet Gen
generate tweets simply from a prompt.
implement rudimentary memory system to make sure model "knows about" its past tweets.
prompt the model to reflect about a topic and generate a tweet
automatically post the tweet
1st night - ran for 7 hours post 1 time every hour

# Entry 2 - Building Diversity (Reading Tweets)
goals for today:
- make tweets more diverse
- allow bot to read tweets

added:
- tweet length mode (short/medium/long)
- reader.py script to pull 10 most recent posts into memory/perceptions/DATE.txt
- bot is fed perceptions (0-3 if DATE = TODAY, 3-6 if DATE = YDAY, 6-9 if DATE = 2DAYAGO)
- pull perceptions if no recent enough perceptions (this was actually added during Entry 3)
- Testing flag (uses info from and generates tweets into testing directory)

todo/ideas:
- prompt rotation (self-reflect prompt, new concept prompt, reconcile conflict)
- core persona/beliefs, can provide a starter "seed" but should be mostly generated from bot
- topics/themes engine/picker
- detect conflicting ideas in reflections and have bot resolve (cognitive dissonance -> emergent behavior?)

# Entry 3 - Thinking Behaviors (Core Tweet Generation)
- quick refactor into main.py + generate_tweet
- added prompt types
- added selector (selects random mood), need to make engine w/weights (with starting seeds)
- added curiosity engine (with starting seeds)
- moods engine
- vocab engine
- tweet style engine
- 20% self reflective tweets

Core tweet gen is mostly done. Most other diversities will come from perception layer.
Quickly added: more random timing in tweets + log (for fine tune later)
About to run a test with core tweet gen.

Next steps: Agent behaviors
- vector search for memory (long term beliefs, associative memory)
- propose new tweet styles/moods/curioisities/vocab
- desire engine (from seed) + spawn goals and subgoals based on desires

# Entry 4 - Long Term Memory
- added use of own coined vocabulary
- added vector DB for reflections
- vector DB memory for perceptions/reflections (and later on, other things)
    - reflections text files are not used in the code at all
    - perceptions text files are loaded into vector DB from text files on vector DB init.

next steps:
further agent behaviors (developing new interests/curiosities/beliefs/ideas)
Something (I dont know what) needs to trigger our bot to write to its moods/curiosity/tweet_styles engines. 
I think to make this meaningful, these curiosities and mood cant be purely random or purely deterministic (like with prompts). With humans, a new curiosity is a function of all of your old curiosities + the environment/triggers + randomness. How can we simulate the same kind of behavior for our LLM, while keeping it somewhat meaningful to humans? The idea is that we should not simply just be prompting the LLM "think" of a new curiosity, it should be somewhat reminiscent of how humans generate curiosities i guess.

# Entry 5 - Refactor
goal: refactor codebase
codebase refactored
memory file made static

# Entry 6 - Dynamic Engines
goal: generate new curiosities and prune old ones. this should be a funtion of bot state + stimuli + stochastics

# Entry 7 - Stepping Back | True Emergence
my oh my this is embarassing
i have written the behaviors too explicitly
we have individual systems built to produce behaviors
rather than arising between interactions within the system
we need to indirectly elicit the emergent behaviors
not explicitly ask for them

