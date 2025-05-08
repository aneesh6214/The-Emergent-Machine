# memory.py
# Manages the FAISS vector database for the bot's memory

import faiss
import numpy as np
import os
from config import TESTING, MEMORY_DB_PATH
from datetime import datetime
import json

class MemoryDB:
    def __init__(self, dim=1536, db_path=MEMORY_DB_PATH):
        self.dim = dim
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        self.jsonl_path = os.path.join(db_dir, "log.jsonl")
        self.index = faiss.IndexFlatL2(dim)
        self.entries = []  # Store (text, vector) pairs for now
        if os.path.exists(self.db_path):
            self.load()

    def add(self, text, vector, response_type="unknown"):
        print(f"🧠 Adding to memory...")
        timestamp = datetime.utcnow().isoformat()
        metadata = {
            "response_type": response_type,
            "response": text,
            "timestamp": timestamp
        }
        self.index.add(np.array([vector]).astype('float32'))
        self.entries.append((text, vector))
        self.save()
        # Log metadata to jsonl file
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata) + "\n")

    def save(self):
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        faiss.write_index(self.index, self.db_path)

    def load(self):
        self.index = faiss.read_index(self.db_path)

    def search(self, vector, k=5):
        D, I = self.index.search(np.array([vector]).astype('float32'), k)
        return [(self.entries[i][0], D[0][j]) for j, i in enumerate(I[0]) if i < len(self.entries)]

# Singleton instance
memory_db = MemoryDB() 