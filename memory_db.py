"""
Simple FAISS-backed vector memory for the Emergent Machine bot.
Keeps an index + a parallel JSONL file with metadata you can inspect.

Directory layout (TESTING toggles the root):

memory/
 └─ vector_store/
     ├─ faiss.index
     └─ metadata.jsonl
"""
import os, json, faiss, uuid, openai
from datetime import datetime
from typing import List, Dict
import numpy as np

EMBED_MODEL = "text-embedding-3-small"     # 1536-dim (cheap)
DIM         = 1536                         # hard-coded for the model

class MemoryDB:
    def __init__(self, root_dir: str):
        """
        root_dir →  e.g. 'memory/vector_store'  (is created if missing)
        """
        self.root          = root_dir
        self.index_path    = os.path.join(root_dir, "faiss.index")
        self.meta_path     = os.path.join(root_dir, "metadata.jsonl")
        os.makedirs(self.root, exist_ok=True)

        # try load index ------------------------------------------------------
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        else:                                    # fresh, empty index
            self.index = faiss.IndexFlatL2(DIM)

        # metadata in memory (list[dict]); each entry’s 'id' aligns
        self._meta : List[Dict] = []
        if os.path.exists(self.meta_path):
            with open(self.meta_path, encoding="utf-8") as f:
                for line in f:
                    self._meta.append(json.loads(line))

    # ---------- helpers ------------------------------------------------------
    def _embed(self, text: str) -> List[float]:
        resp = openai.OpenAI().embeddings.create(
            model=EMBED_MODEL, input=text[:8192])     # trunc safety
        return resp.data[0].embedding

    def _dump_meta_line(self, entry: Dict):
        with open(self.meta_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ---------- public API ----------------------------------------------------
    def add_memory(self, text: str, kind: str):
        if not text.strip():
            return

        # 1) get the embedding list from OpenAI
        emb_list = self._embed(text)  # this is a Python list of floats

        # 2) turn it into a float32 numpy array of shape (1, DIM)
        vec = np.array(emb_list, dtype="float32").reshape(1, -1)

        # 3) add to FAISS
        self.index.add(vec)

        # 4) metadata
        uid = str(uuid.uuid4())
        meta = {
            "id":        uid,
            "kind":      kind,
            "text":      text.strip(),
            "timestamp": datetime.utcnow().isoformat()
        }
        self._meta.append(meta)
        self._dump_meta_line(meta)

        # 5) persist the index
        faiss.write_index(self.index, self.index_path)


    def retrieve(self, query: str, k: int = 3) -> List[str]:
        if self.index.ntotal == 0:
            return []

        # get embedding list, convert to float32 numpy array
        emb_list = self._embed(query)
        vec = np.array(emb_list, dtype="float32").reshape(1, -1)

        D, I  = self.index.search(vec, k)
        results = []
        for idx in I[0]:
            if idx < len(self._meta):
                results.append(self._meta[idx]["text"])
        return results
