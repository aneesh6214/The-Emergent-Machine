import os
import time
import random
from datetime import datetime
from config import TESTING
from perception import perception_phase
from reflection import reflection_phase
from tweet_phase import tweet_phase


HOURS = 1
TWEETS = 3

# Compute total window in seconds
total_window = HOURS * 3600

# Generate TWEETS random timestamps (in seconds) within [0, total_window)
schedule = sorted([0.0] + [random.uniform(0, total_window) for _ in range(TWEETS - 1)])

print(f"Scheduling {TWEETS} tweets randomly over {HOURS} hours (total {int(total_window)}s).")

last_time = 0.0
for i, event_time in enumerate(schedule, start=1):
    wait = event_time - last_time
    last_time = event_time

    if i == 1:
        wait = 0
        print(f"\n===== Scheduled Tweet {i}/{TWEETS} at +0s (1st tweet) (wait {int(wait)}s) =====")
    else:
        print(f"\n===== Scheduled Tweet {i}/{TWEETS} at +{int(event_time)}s (wait {int(wait)}s) =====")

    if not TESTING:
        print(f"⏳ Sleeping for {int(wait)}s until next tweet...\n")
        time.sleep(wait)
    else:
        print("⏩ (testing mode — skipping sleep)\n")

    print("==== PERCEPTION PHASE =====")
    perception_response = perception_phase()
    print(f"🧠 Perception response: {perception_response}\n\n")
    
    print("==== REFLECTION PHASE =====")
    reflection_response = reflection_phase()
    if reflection_response:
        print(f"🤔 Reflection response: {reflection_response}\n\n")
    
    print("==== TWEET PHASE =====")
    tweet = tweet_phase()
    print(f"🐦 Generated tweet: {tweet}\n\n")

print("\n✅ All scheduled tweets have been generated.")
