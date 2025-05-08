# perception.py
# Handles the perception phase: reading a tweet and prompting the LLM

import os
from config import PERCEPTION_SYSTEM_PROMPT, PERCEPTIONS_FILE_PATH
from model import call_llm

# Keep track of the current position in the perceptions file
perception_pointer = 0

def parse_tweet_block(lines):
    author = None
    text = None
    for line in lines:
        if line.startswith('Author:'):
            author = line[len('Author:'):].strip()
        elif line.startswith('Text:'):
            text = line[len('Text:'):].strip()
    if author and text:
        return f"@{author}\n{text}"
    return None

def read_one_perception():
    global perception_pointer
    file_path = PERCEPTIONS_FILE_PATH
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # Find all tweet blocks
    tweet_blocks = []
    current_block = []
    for line in lines:
        line = line.strip()
        if line == '[Tweet]':
            current_block = []  # Start a new block
        elif line == '---':
            if current_block:
                tweet_blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)
    if current_block:
        tweet_blocks.append(current_block)
    # Get the next tweet block
    if perception_pointer < len(tweet_blocks):
        tweet = parse_tweet_block(tweet_blocks[perception_pointer])
        perception_pointer += 1
        return tweet
    return None

def perception_phase():
    tweet = read_one_perception()
    if not tweet:
        print("No perception tweet found.")
        return None
    response = call_llm(system_prompt=PERCEPTION_SYSTEM_PROMPT, user_prompt=tweet, response_type="perception")
    return response 