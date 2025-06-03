"""Memory storage for agent interactions."""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions


class MemoryStore:
    """Simple memory store with JSON persistence and optional vector search."""
    
    def __init__(self, 
                 json_file: str = "memories.json",
                 use_vector_store: bool = True,
                 vector_db_path: str = "./chroma_db"):
        self.json_file = Path(json_file)
        self.use_vector_store = use_vector_store
        self.memories: List[Dict[str, Any]] = []
        
        # Load existing memories
        if self.json_file.exists():
            with open(self.json_file, 'r') as f:
                self.memories = json.load(f)
                
        # Initialize vector store if requested
        if self.use_vector_store:
            self.chroma_client = chromadb.PersistentClient(path=vector_db_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name="twitter_memories",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            )
            
            # Add existing memories to vector store if it's empty
            if self.collection.count() == 0 and self.memories:
                self._rebuild_vector_store()
                
    def _rebuild_vector_store(self):
        """Rebuild vector store from JSON memories."""
        if not self.use_vector_store or not self.memories:
            return
            
        documents = []
        metadatas = []
        ids = []
        
        for i, memory in enumerate(self.memories):
            doc = f"{memory.get('summary', '')} {memory.get('action', {}).get('reasoning', '')}"
            documents.append(doc)
            metadatas.append({
                "timestamp": memory.get('timestamp', ''),
                "url": memory.get('perception', {}).get('url', ''),
                "action_type": memory.get('action', {}).get('action_type', '')
            })
            ids.append(f"memory_{i}")
            
            # Commit in chunks of 150 to avoid exceeding batch limits
            if len(documents) >= 150:
                self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
                documents, metadatas, ids = [], [], []
        
        # Add any remaining items
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        
    async def add(self, memory: Dict[str, Any]):
        """Add a new memory to the store."""
        # Add timestamp
        memory['timestamp'] = datetime.now().isoformat()
        
        # Append to memories list
        self.memories.append(memory)
        
        # Save to JSON
        with open(self.json_file, 'w') as f:
            json.dump(self.memories, f, indent=2)
            
        # Add to vector store
        if self.use_vector_store:
            doc = f"{memory.get('summary', '')} {memory.get('action', {}).get('reasoning', '')}"
            self.collection.add(
                documents=[doc],
                metadatas=[{
                    "timestamp": memory['timestamp'],
                    "url": memory.get('perception', {}).get('url', ''),
                    "action_type": memory.get('action', {}).get('action_type', '')
                }],
                ids=[f"memory_{len(self.memories) - 1}"]
            )
            
    async def search(self, query: str, n_results: int = 5) -> List[str]:
        """Search for relevant memories using vector similarity."""
        if not self.use_vector_store:
            # Simple text search fallback
            results = []
            query_lower = query.lower()
            
            for memory in reversed(self.memories[-20:]):  # Search last 20 memories
                summary = memory.get('summary', '').lower()
                reasoning = memory.get('action', {}).get('reasoning', '').lower()
                
                if query_lower in summary or query_lower in reasoning:
                    results.append(memory['summary'])
                    
                if len(results) >= n_results:
                    break
                    
            return results
            
        # Vector search
        search_results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Extract memory summaries from IDs
        summaries = []
        if search_results['ids']:
            for id_str in search_results['ids'][0]:
                idx = int(id_str.split('_')[1])
                if idx < len(self.memories):
                    summaries.append(self.memories[idx]['summary'])
                    
        return summaries
        
    async def get_recent(self, n: int = 10) -> List[str]:
        """Get the most recent memory summaries."""
        recent_memories = self.memories[-n:] if len(self.memories) > n else self.memories
        return [m.get('summary', '') for m in recent_memories]
        
    async def get_all(self) -> List[Dict[str, Any]]:
        """Get all memories."""
        return self.memories
        
    def clear(self):
        """Clear all memories (use with caution)."""
        self.memories = []
        
        # Clear JSON file
        with open(self.json_file, 'w') as f:
            json.dump([], f)
            
        # Clear vector store
        if self.use_vector_store:
            self.chroma_client.delete_collection("twitter_memories")
            self.collection = self.chroma_client.create_collection(
                name="twitter_memories",
                embedding_function=embedding_functions.DefaultEmbeddingFunction()
            ) 