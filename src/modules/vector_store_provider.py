"""Abstract vector store interface for pluggable RAG backends.

Supports multiple implementations:
- LocalFaissProvider: Local FAISS with commit hash caching
- PineconeProvider: Cloud-hosted Pinecone (future)
- RedisProvider: Redis-backed vector store (future)

All providers implement commit-aware caching to avoid re-indexing.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreConfig:
    """Configuration for vector store backend."""
    backend: str  # "local_faiss", "pinecone", "redis"
    enable_commit_cache: bool = True  # Skip re-index if commit unchanged
    
    # Local FAISS config
    local_index_path: str = "./data/rag_indices"
    
    # Pinecone config
    pinecone_api_key: str = ""
    pinecone_index_name: str = "codebase-embeddings"
    pinecone_dimension: int = 384  # For all-MiniLM-L6-v2
    pinecone_environment: str = "us-east-1-aws"
    pinecone_namespace_prefix: str = ""
    
    # Shared config
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384


class VectorStoreProvider(ABC):
    """Abstract base class for vector store providers."""
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available and healthy.
        
        Returns:
            True if provider is ready to use
        """
        pass
    
    @abstractmethod
    def has_commit_index(self, repo_id: str, commit_sha: str) -> bool:
        """Check if embeddings exist for repo+commit combination.
        
        Args:
            repo_id: Repository identifier (e.g., "fastapi/fastapi")
            commit_sha: Git commit SHA (full or short)
            
        Returns:
            True if index exists and is up-to-date
        """
        pass
    
    @abstractmethod
    def upsert_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> Tuple[int, bool]:
        """Store chunks and their embeddings.
        
        Args:
            repo_id: Repository identifier
            commit_sha: Commit SHA this index is for
            chunks: List of chunk metadata dicts with keys:
                - id: unique ID
                - file_path: path in repo
                - start_line: start line number
                - end_line: end line number
                - code_content: actual code
                - language: programming language
            vectors: Embedding vectors (must match chunks length)
            
        Returns:
            Tuple of (num_upserted, success)
        """
        pass
    
    @abstractmethod
    def query_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        query_vector: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for relevant chunks.
        
        Args:
            repo_id: Repository identifier
            commit_sha: Commit to search within
            query_vector: Query embedding vector
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of (chunk_metadata, similarity_score) tuples,
            ordered by similarity (highest first)
        """
        pass
    
    @abstractmethod
    def delete_repo(self, repo_id: str) -> bool:
        """Delete all embeddings for a repository.
        
        Args:
            repo_id: Repository identifier
            
        Returns:
            True if deletion successful
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get provider metadata and stats.
        
        Returns:
            Dict with stats like:
            - backend_type: provider type
            - is_available: whether provider is ready
            - repos_indexed: number of repos
            - total_chunks: total chunks stored
            - last_error: last error if any
        """
        pass


class LocalFaissProvider(VectorStoreProvider):
    """Local FAISS vector store with commit-aware caching.
    
    Stores indices in: {index_path}/repo_name{commit_sha}/
    Metadata in: {index_path}/repo_name{commit_sha}/metadata.json
    
    This allows multiple commits of same repo to have separate indices,
    preventing re-indexing when commit hasn't changed.
    """
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self.index_path = config.local_index_path
        self.enable_commit_cache = config.enable_commit_cache
        try:
            import faiss
            import numpy as np
            self.faiss = faiss
            self.np = np
            self.available = True
            logger.debug("FAISS available for local vector storage")
        except ImportError:
            self.available = False
            logger.warning("⚠ FAISS not installed. Local vector store unavailable. Install: pip install faiss-cpu")
        
        self._indices_cache = {}  # In-memory cache of loaded indices
    
    def health_check(self) -> bool:
        """Check if local FAISS is available."""
        return self.available
    
    def has_commit_index(self, repo_id: str, commit_sha: str) -> bool:
        """Check if commit index exists locally."""
        if not self.enable_commit_cache or not self.available:
            return False
        
        try:
            from pathlib import Path
            index_dir = Path(self.index_path) / f"{repo_id}_{commit_sha}"
            index_file = index_dir / "index.faiss"
            metadata_file = index_dir / "metadata.json"
            exists = index_file.exists() and metadata_file.exists()
            if exists:
                logger.info(f"✓ Found cached index for {repo_id}@{commit_sha}")
            return exists
        except Exception as e:
            logger.error(f"Error checking index: {e}")
            return False
    
    def upsert_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> Tuple[int, bool]:
        """Store chunks with commit hash for future cache hits."""
        if not self.available:
            return 0, False
        
        try:
            import json
            from pathlib import Path
            
            # Create index directory with commit hash
            index_dir = Path(self.index_path) / f"{repo_id}_{commit_sha}"
            index_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert vectors to numpy array
            vector_array = self.np.array(vectors, dtype=self.np.float32)
            
            # Create FAISS index
            dimension = vector_array.shape[1]
            index = self.faiss.IndexFlatL2(dimension)
            index.add(vector_array)
            
            # Save index
            self.faiss.write_index(index, str(index_dir / "index.faiss"))
            
            # Save metadata
            metadata = {
                "repo_id": repo_id,
                "commit_sha": commit_sha,
                "chunk_count": len(chunks),
                "chunks": chunks,
            }
            with open(index_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✓ Stored {len(chunks)} chunks for {repo_id}@{commit_sha}")
            return len(chunks), True
        
        except Exception as e:
            logger.error(f"Failed to upsert chunks: {e}")
            return 0, False
    
    def query_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        query_vector: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search local FAISS index."""
        if not self.available:
            return []
        
        try:
            import json
            from pathlib import Path
            
            index_dir = Path(self.index_path) / f"{repo_id}_{commit_sha}"
            index_file = index_dir / "index.faiss"
            metadata_file = index_dir / "metadata.json"
            
            if not index_file.exists() or not metadata_file.exists():
                logger.warning(f"Index not found for {repo_id}@{commit_sha}")
                return []
            
            # Load index
            index = self.faiss.read_index(str(index_file))
            
            # Load metadata
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            chunks = metadata.get("chunks", [])
            
            # Search
            query_array = self.np.array([query_vector], dtype=self.np.float32)
            distances, indices = index.search(query_array, min(top_k, len(chunks)))
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                idx = int(idx)
                if idx >= 0 and idx < len(chunks):
                    # FAISS uses L2 distance; convert to similarity (0-1)
                    similarity = 1 / (1 + float(dist))  # Inverse of L2 distance
                    if similarity >= similarity_threshold:
                        results.append((chunks[idx], similarity))
            
            logger.debug(f"Query returned {len(results)} results for {repo_id}@{commit_sha}")
            return results
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    def delete_repo(self, repo_id: str) -> bool:
        """Delete all indices for a repo."""
        if not self.available:
            return False
        
        try:
            import shutil
            from pathlib import Path
            
            index_path = Path(self.index_path)
            deleted_count = 0
            
            # Find and delete all indices matching repo_id*
            for item in index_path.glob(f"{repo_id}_*"):
                shutil.rmtree(item)
                deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} indices for {repo_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete repo: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get local FAISS metadata."""
        try:
            import json
            from pathlib import Path
            
            index_path = Path(self.index_path)
            repos_indexed = set()
            total_chunks = 0
            
            if index_path.exists():
                for metadata_file in index_path.glob("*/metadata.json"):
                    try:
                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)
                            repos_indexed.add(metadata.get("repo_id", "unknown"))
                            total_chunks += metadata.get("chunk_count", 0)
                    except:
                        pass
            
            return {
                "backend_type": "local_faiss",
                "is_available": self.available,
                "repos_indexed": len(repos_indexed),
                "total_chunks": total_chunks,
                "index_path": str(self.index_path),
                "commit_cache_enabled": self.enable_commit_cache,
            }
        except Exception as e:
            return {
                "backend_type": "local_faiss",
                "is_available": False,
                "error": str(e),
            }
