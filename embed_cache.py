# embed_cache.py
# Script to embed subreddit names for semantic similarity search.

import os
import pickle
import time
from model import embed_text

# File paths
INPUT_FILENAME = "cache/reddit_cache/subreddit_names.txt"
OUTPUT_FILENAME = "cache/reddit_cache/embedded_subreddit_index.pkl"

# Batch size for processing
BATCH_SIZE = 200


def load_subreddit_names():
    """Load subreddit names from the text file and return a list of names."""
    with open(INPUT_FILENAME, "r") as f:
        names = [line.strip() for line in f if line.strip()]
    return names


def build_embeddings(subreddit_names):
    """Build embeddings for a list of subreddit names using batch processing."""
    embeddings_dict = {}
    total = len(subreddit_names)
    last_checkpoint_time = time.time()
    next_checkpoint = 5000
    for i in range(0, total, BATCH_SIZE):
        batch = subreddit_names[i:i+BATCH_SIZE]
        # Compute embeddings for each subreddit in the batch
        embeddings = [embed_text(name) for name in batch]
        for name, embedding in zip(batch, embeddings):
            embeddings_dict[name] = embedding
        #print(f"Processed {min(i+BATCH_SIZE, total)}/{total} subreddits.")

        if len(embeddings_dict) >= next_checkpoint:
            current_time = time.time()
            elapsed = current_time - last_checkpoint_time
            print(f"Checkpoint reached: {len(embeddings_dict)} embeddings processed. Time since last checkpoint: {elapsed:.2f} seconds.")
            save_embeddings(embeddings_dict)
            last_checkpoint_time = current_time
            next_checkpoint += 5000
    return embeddings_dict


def save_embeddings(embeddings_dict):
    """Save the embeddings dictionary to a pickle file. Ensure the directory exists."""
    directory = os.path.dirname(OUTPUT_FILENAME)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(OUTPUT_FILENAME, "wb") as f:
        pickle.dump(embeddings_dict, f)
    print(f"Embeddings saved to {OUTPUT_FILENAME}")


def main():
    start_time = time.time()
    # Load subreddit names
    names = load_subreddit_names()
    print(f"Loaded {len(names)} subreddit names from {INPUT_FILENAME}.")

    # Build embeddings
    embeddings = build_embeddings(names)
   
    # Save embeddings
    save_embeddings(embeddings)

    elapsed = (time.time() - start_time)/60
    print(f"Done in {elapsed:.2f} minutes.")


if __name__ == "__main__":
    main() 