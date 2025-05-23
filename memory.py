# memory.py
# Manages the FAISS vector database for the bot's memory

import faiss
import numpy as np
import os
import json
from datetime import datetime
from config import MEMORY_DB_PATH

class MemoryDB:
    def __init__(self, dim=1536, db_path=MEMORY_DB_PATH):
        self.dim = dim
        self.db_path = db_path
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        self.jsonl_path = os.path.join(db_dir, "log.jsonl")
        self.index: faiss.IndexFlatL2 | None = None
        self.entries = []  # Store (text, vector) pairs
        
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
        
        vec_np = np.array([vector]).astype("float32")
        if self.index is None or self.index.d != vec_np.shape[1]:
            self.index = faiss.IndexFlatL2(vec_np.shape[1])
            
        self.index.add(vec_np)
        self.entries.append((text, vector))
        self.save()
        
        # Log metadata to jsonl file
        with open(self.jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata) + "\n")

    def save(self):
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)
        
        if self.index is not None:
            faiss.write_index(self.index, self.db_path)

    def load(self):
        self.index = faiss.read_index(self.db_path)

    def search(self, vector, k=5):
        if self.index is None:
            return []
            
        D, I = self.index.search(np.array([vector]).astype("float32"), k)
        
        return [
            (self.entries[i][0], float(D[0][j]))
            for j, i in enumerate(I[0])
            if i < len(self.entries)
        ]

# Singleton instance
memory_db = MemoryDB() 