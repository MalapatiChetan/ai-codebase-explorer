"""Pinecone vector store provider for cloud-hosted embeddings.

IMPLEMENTATION GUIDE:
1. Install: pip install pinecone-client
2. Create account: https://www.pinecone.io
3. Create index with dimension 384 (for all-MiniLM-L6-v2)
4. Set environment variables:
   - PINECONE_API_KEY=...
   - PINECONE_INDEX_NAME=...
5. Set in .env: VECTOR_BACKEND=pinecone

BENEFITS vs Local FAISS:
✓ Survives container restarts (Render, Vercel, etc.)
✓ Shared embeddings across multiple server instances
✓ Automatic backup and recovery
✓ Supports clustering for faster search
✗ Added latency (network calls)
✗ Cost per API calls and storage

COMMIT-AWARE CACHING:
Metadata stored as vector namespace + metadata:
- Namespace: "repo_id/commit_sha"
- Each chunk stored with metadata including commit_sha
- Query only within specific commit namespace
- Skip re-index if commit_sha unchanged
"""

import logging
from typing import List, Tuple, Optional, Dict, Any

from src.modules.vector_store_provider import VectorStoreProvider, VectorStoreConfig

logger = logging.getLogger(__name__)


class PineconeProvider(VectorStoreProvider):
    """Pinecone cloud vector store with commit-aware caching.
    
    Architecture:
    - Index: single Pinecone index for all repos
    - Namespace per repo+commit: "owner/repo_name{commit_sha}"
    - Each vector ID includes file path for deduplication
    """
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self.pc = None
        self.index = None
        self.available = False
        
        try:
            from pinecone import Pinecone
            
            if not config.pinecone_api_key:
                logger.warning("⚠ PINECONE_API_KEY not configured. Pinecone backend unavailable.")
                return
            
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=config.pinecone_api_key)
            self.index = self.pc.Index(config.pinecone_index_name)
            self.available = True
            logger.info(f"✓ Pinecone connected to index '{config.pinecone_index_name}'")
        
        except ImportError:
            logger.warning("⚠ Pinecone not installed. Install: pip install pinecone-client")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone: {e}")
    
    def health_check(self) -> bool:
        """Check if Pinecone is available and index exists."""
        if not self.available or not self.index:
            return False
        
        try:
            stats = self.index.describe_index_stats()
            logger.debug(f"Pinecone index stats: {stats}")
            return True
        except Exception as e:
            logger.error(f"Pinecone health check failed: {e}")
            return False
    
    def has_commit_index(self, repo_id: str, commit_sha: str) -> bool:
        """Check if embeddings exist for repo+commit in Pinecone.
        
        Uses namespace to distinguish commits, so we check if any vectors
        exist in that namespace.
        """
        if not self.available or not self.index:
            return False
        
        try:
            namespace = f"{repo_id}/{commit_sha}"
            stats = self.index.describe_index_stats()
            
            # Check if namespace exists
            namespaces = stats.get("namespaces", {})
            exists = namespace in namespaces
            
            if exists:
                logger.info(f"✓ Found cached index for {repo_id}@{commit_sha} in Pinecone")
            return exists
        
        except Exception as e:
            logger.error(f"Error checking Pinecone index: {e}")
            return False
    
    def upsert_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> Tuple[int, bool]:
        """Store chunks and embeddings in Pinecone with commit metadata."""
        if not self.available or not self.index:
            return 0, False
        
        try:
            namespace = f"{repo_id}/{commit_sha}"
            
            # Prepare vectors for Pinecone with metadata
            # Pinecone vector format: (id, values, metadata)
            vectors_to_upsert = []
            
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                vector_id = f"{chunk.get('file_path', '')}:{chunk.get('id', i)}"
                metadata = {
                    "file_path": chunk.get("file_path", ""),
                    "start_line": chunk.get("start_line", 0),
                    "end_line": chunk.get("end_line", 0),
                    "language": chunk.get("language", ""),
                    "code_preview": chunk.get("code_content", "")[:200],  # First 200 chars
                    "commit_sha": commit_sha,
                    "repo_id": repo_id,
                }
                vectors_to_upsert.append((vector_id, vector, metadata))
            
            # Batch upsert to Pinecone
            self.index.upsert(vectors_to_upsert, namespace=namespace)
            
            logger.info(f"✓ Upserted {len(chunks)} chunks to Pinecone for {repo_id}@{commit_sha}")
            return len(chunks), True
        
        except Exception as e:
            logger.error(f"Failed to upsert chunks to Pinecone: {e}")
            return 0, False
    
    def query_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        query_vector: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Search for relevant chunks in Pinecone."""
        if not self.available or not self.index:
            return []
        
        try:
            namespace = f"{repo_id}/{commit_sha}"
            
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
            )
            
            # Convert Pinecone results to our format
            chunks_results = []
            for match in results.get("matches", []):
                score = match.get("score", 0)
                
                if score >= similarity_threshold:
                    # Reconstruct chunk from metadata
                    metadata = match.get("metadata", {})
                    chunk = {
                        "id": match.get("id", ""),
                        "file_path": metadata.get("file_path", ""),
                        "start_line": metadata.get("start_line", 0),
                        "end_line": metadata.get("end_line", 0),
                        "language": metadata.get("language", ""),
                        "code_content": metadata.get("code_preview", ""),
                    }
                    chunks_results.append((chunk, score))
            
            logger.debug(f"Pinecone query returned {len(chunks_results)} results for {repo_id}@{commit_sha}")
            return chunks_results
        
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []
    
    def delete_repo(self, repo_id: str) -> bool:
        """Delete all embeddings for a repository from Pinecone.
        
        This deletes all namespaces matching the repo_id pattern.
        """
        if not self.available or not self.index:
            return False
        
        try:
            stats = self.index.describe_index_stats()
            namespaces = stats.get("namespaces", {})
            
            deleted_count = 0
            for namespace in namespaces:
                if namespace.startswith(f"{repo_id}/"):
                    # Delete all vectors in namespace
                    self.index.delete(delete_all=True, namespace=namespace)
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} commit namespaces for {repo_id} from Pinecone")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete repo from Pinecone: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get Pinecone metadata and statistics."""
        try:
            stats = self.index.describe_index_stats()
            
            total_namespaces = len(stats.get("namespaces", {}))
            total_vectors = stats.get("total_vector_count", 0)
            
            return {
                "backend_type": "pinecone",
                "is_available": self.available,
                "index_name": self.config.pinecone_index_name,
                "total_namespaces": total_namespaces,
                "total_vectors": total_vectors,
                "dimension": self.config.pinecone_dimension,
                "commit_cache_enabled": self.config.enable_commit_cache,
            }
        except Exception as e:
            return {
                "backend_type": "pinecone",
                "is_available": False,
                "error": str(e),
            }
