# perception.py
# Handles the perception phase: reading a tweet and prompting the LLM

import os
import random
from config import (
    PERCEPTION_SYSTEM_PROMPT, 
    PERCEPTIONS_FILE_PATH,
    PERCEPTION_SOURCES,
    REDDIT_PERCEPTION_CHANCE
)
from model import call_llm

# Import conditionally to handle when datasets package is not installed
try:
    from reddit_perception import reddit_perception_phase
    REDDIT_AVAILABLE = True
except (ImportError, Exception) as e:
    print(f"⚠️ Reddit perception not available: {e}")
    REDDIT_AVAILABLE = False

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
    
    with open(PERCEPTIONS_FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
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
    
    if perception_pointer < len(tweet_blocks):
        tweet = parse_tweet_block(tweet_blocks[perception_pointer])
        perception_pointer += 1
        return tweet
    
    return None

def twitter_perception_phase():
    """Run the Twitter perception phase"""
    tweet = read_one_perception()
    
    if not tweet:
        print("❌ No perception tweet found.")
        return None
        
    response = call_llm(
        system_prompt=PERCEPTION_SYSTEM_PROMPT, 
        user_prompt=tweet, 
        response_type="twitter_perception"
    )
    
    return response

def choose_perception_source():
    """Choose which perception source to use (Twitter or Reddit)"""
    available_sources = list(PERCEPTION_SOURCES)
    
    # Remove Reddit if not available
    if "reddit" in available_sources and not REDDIT_AVAILABLE:
        available_sources.remove("reddit")
    
    # If no sources available, return None
    if not available_sources:
        return None
    
    # If only one source available, use that
    if len(available_sources) == 1:
        return available_sources[0]
    
    # If both Twitter and Reddit are available, use probability to choose
    if "twitter" in available_sources and "reddit" in available_sources:
        return "reddit" if random.random() < REDDIT_PERCEPTION_CHANCE else "twitter"
    
    # Default to first available source
    return available_sources[0]

def perception_phase():
    """Run the perception phase, choosing between Twitter and Reddit sources"""
    source = choose_perception_source()
    
    if source == "reddit" and REDDIT_AVAILABLE:
        print("🔄 Using Reddit for perception")
        try:
            reddit_result = reddit_perception_phase()
            if reddit_result:
                return reddit_result
            print("❌ Reddit perception failed, falling back to Twitter")
        except Exception as e:
            print(f"❌ Error in Reddit perception: {e}")
            print("📱 Falling back to Twitter perception")
        # If we get here, Reddit perception failed, fall back to Twitter
        source = "twitter"
        
    if source == "twitter":
        print("🔄 Using Twitter for perception")
        return twitter_perception_phase()
    else:
        print("❌ No perception source available")
        return None 