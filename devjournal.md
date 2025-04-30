# Goal
Lets give an LLM the capabilities to post on twitter, along with some initial ideas to explore (consciousness, emergence, and NNs).
What emergent behaviors arise, what enable them? Can we cultivate an emergent personality?
An agentic personality that evolves overtime?

# Entry 1 - Core Tweet Gen
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
- Testing flag (uses info from and generates tweets into testing directory)

todo/ideas:
- prompt rotation (self-reflect prompt, new concept prompt, reconcile conflict)
- core persona/beliefs, can provide a starter "seed" but should be mostly generated from bot
- topics/themes engine/picker
- detect conflicting ideas in reflections and have bot resolve (cognitive dissonance -> emergent behavior?)

# Entry 3 - Thinking Behaviors 