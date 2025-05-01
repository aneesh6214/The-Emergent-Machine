# memory_db.py
import os
import json
import uuid
import openai
import faiss
import numpy as np
from datetime import datetime
from typing import List, Dict
import random

EMBED_MODEL = "text-embedding-3-small"
DIM = 1536

class MemoryDB:
    def __init__(self, root_dir: str):
        self.root = root_dir
        os.makedirs(self.root, exist_ok=True)
        self.index_path = os.path.join(self.root, "faiss.index")
        self.meta_path  = os.path.join(self.root, "metadata.jsonl")

        # load or init FAISS index
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:
            self.index = faiss.IndexFlatL2(DIM)

        # load metadata
        self._meta: List[Dict] = []
        if os.path.exists(self.meta_path):
            with open(self.meta_path, encoding="utf-8") as f:
                for line in f:
                    self._meta.append(json.loads(line))

    def _embed(self, text: str) -> List[float]:
        resp = openai.OpenAI().embeddings.create(
            model=EMBED_MODEL,
            input=text[:8192]
        )
        return resp.data[0].embedding

    def _dump_meta_line(self, entry: Dict):
        with open(self.meta_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def add_memory(self, text: str, kind: str):
        if not text.strip():
            return
        embedding = self._embed(text)
        # convert to numpy array
        vec = np.array(embedding, dtype="float32").reshape(1, -1)
        self.index.add(vec)

        uid = str(uuid.uuid4())
        meta = {
            "id":        uid,
            "kind":      kind,
            "text":      text.strip(),
            "timestamp": datetime.utcnow().isoformat()
        }
        self._meta.append(meta)
        self._dump_meta_line(meta)
        faiss.write_index(self.index, self.index_path)

    def retrieve(self, query: str, k: int = 3, kind: str = None) -> List[str]:
        if self.index.ntotal == 0:
            return []
        embedding = self._embed(query)
        vec = np.array(embedding, dtype="float32").reshape(1, -1)
        D, I = self.index.search(vec, min(k, self.index.ntotal))

        results = []
        for idx in I[0]:
            if idx < len(self._meta):
                entry = self._meta[idx]
                if kind is None or entry["kind"] == kind:
                    results.append(entry["text"])
                if len(results) >= k:
                    break
        return results
    
    # ------------------------------------------------------------------
    # convenience: get the N most-recent memories of a given kind
    # ------------------------------------------------------------------
    def recent(self, kind: str = "reflection", n: int = 3) -> list[str]:
        """Return the newest ≤ n memory.text items whose meta['kind'] matches."""
        items = (m for m in self._meta if m["kind"] == kind)
        newest = sorted(items, key=lambda m: m["timestamp"], reverse=True)[:n]
        return [m["text"] for m in newest]

    def sample(self, k: int = 2, kind: str | None = None) -> list[str]:
        """Return k random memory texts (optionally restricted to kind)."""
        pool = [m["text"] for m in self._meta if (kind is None or m["kind"] == kind)]
        return random.sample(pool, k=min(k, len(pool)))