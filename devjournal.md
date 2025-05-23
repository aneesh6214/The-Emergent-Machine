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

# Entry 7 - Stepping Back, Refactoring for True Emergence
my oh my this is embarassing
i have written the behaviors too explicitly
we have individual systems built to produce behaviors
rather than arising between interactions within the system
we need to indirectly elicit the emergent behaviors
not explicitly ask for them

code has been split into two branches 
master (to be modified)
v0-engine-arch (legacy, not to be modified)

at some point switch from twitter api to twint
https://github.com/twintproject/twint

todo:
    tear out engines
    unify vector store
    change core tweet gen

# Entry 8 (master) - Deleting Engines & Unifying Memory
New Arch:
    Perceive - Every tweet the bot writes to its memory system about what it percieved
    Reflect stage - Every N tweets or when a "novelty score" of new perceptions > τ • 20 % probability on each loop ⇒ avoids determinism
    Plan/Tweet stage - The bot tweets based on its state/memories

STATUS:
- no more engines
- new tweet gen arch/cycle [Percieve -> (Chance) Reflect -> Tweet]

perceptions will need to be changed. bot is very stagnant. there are no systems which would trigger drift
without being elicited from the environment.

## NEXT STEPS
change perception:
- track bots following & approximate a home page feed from that
- use SNScrape (or something else) to scrape from twitter (not API)

agent behaviors:
- switch to mistral (or some local model), follow MCP
- give bot agent abilites (search hashtags, follow people, reply, etc.)

long term/non-immediate:
- memory analysis (clustering) to prove/identify emergent behaviors
- memory scoring (importance/novelty)
- goals/motivations?

# Entry 9 - Fresh Start
Starting from the beginning
- vector DB set up
- perception phase set up 
- model call abstracted into model.py
- reflect phase set up (modifies state_of_mind context)
- tweet gen set up

percept -> reflect -> tweet
overarching "state of mind" context
model writes to state of mind during reflection
top k memories ("diverse" retrieval) added at all prompts
tweet 3 variable lengths (short, medium, long)
temp varies by mode (short=0.7, medium=0.9, long=1.1)

todo:
switch to local llm & mcp
agent behaviors (state of mind)
other perception sources (books, etc.)
fine tune persona
adaptive ?
make way i can talk to it and it remembers
how does openai memory work so good?

# Entry 10 - Switch to Local LLM
https://huggingface.co/TheBloke/MythoMax-L2-13B-GGUF

Switched to Mixtral 8xB (MythoMax Q5_M_K)
tried out mcp with mcp client, added lag- not very practical

better to go with a light wrapper around the llm
can implement our own modular context wrapper/system
leave room for agent "actions"

also cleaned code. quick summary:
main.py (sets up timing/calles each phase)
perception.py (gets tweets FROM FILE & prompts perception)
reflection.py (gets k memories & prompts reflection)
tweet_phase.py (select tweet length & prompt tweet, writes to tweet file)
memory.py (singleton db interface)
model.py (LLM interface & calls write to memory)