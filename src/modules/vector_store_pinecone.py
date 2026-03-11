"""Pinecone vector store provider for commit-aware code embeddings."""

import logging
from typing import Any, Dict, List, Tuple

from src.modules.vector_store_provider import VectorStoreConfig, VectorStoreProvider

logger = logging.getLogger(__name__)


class PineconeProvider(VectorStoreProvider):
    """Store repo embeddings in Pinecone namespaces keyed by repo+commit."""

    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self.pc = None
        self.index = None
        self.available = False

        try:
            from pinecone import Pinecone

            if not config.pinecone_api_key:
                logger.warning("PINECONE_API_KEY is not configured. Pinecone backend is unavailable.")
                return

            self.pc = Pinecone(api_key=config.pinecone_api_key)
            self.index = self.pc.Index(config.pinecone_index_name)
            self.available = True
            logger.debug(f"Connected to Pinecone index '{config.pinecone_index_name}'")
        except ImportError:
            logger.warning("Pinecone package is not installed. Install with 'pip install pinecone'.")
        except Exception as exc:
            logger.error(f"Failed to initialize Pinecone: {exc}")

    def _namespace(self, repo_id: str, commit_sha: str) -> str:
        prefix = self.config.pinecone_namespace_prefix.strip("/")
        base = f"{repo_id}/{commit_sha}"
        return f"{prefix}/{base}" if prefix else base

    @staticmethod
    def _stats_namespaces(stats: Any) -> Dict[str, Any]:
        if isinstance(stats, dict):
            return stats.get("namespaces", {}) or {}
        return getattr(stats, "namespaces", {}) or {}

    @staticmethod
    def _stats_total_vectors(stats: Any) -> int:
        if isinstance(stats, dict):
            return stats.get("total_vector_count", 0)
        return getattr(stats, "total_vector_count", 0) or 0

    @staticmethod
    def _result_matches(results: Any) -> List[Any]:
        if isinstance(results, dict):
            return results.get("matches", []) or []
        return getattr(results, "matches", []) or []

    def health_check(self) -> bool:
        if not self.available or self.index is None:
            return False

        try:
            self.index.describe_index_stats()
            return True
        except Exception as exc:
            logger.error(f"Pinecone health check failed: {exc}")
            return False

    def has_commit_index(self, repo_id: str, commit_sha: str) -> bool:
        if not self.available or self.index is None:
            return False

        try:
            namespace = self._namespace(repo_id, commit_sha)
            stats = self.index.describe_index_stats()
            exists = namespace in self._stats_namespaces(stats)
            if exists:
                logger.info(f"Existing Pinecone namespace found for {repo_id}@{commit_sha}")
            return exists
        except Exception as exc:
            logger.error(f"Failed to check Pinecone namespace for {repo_id}@{commit_sha}: {exc}")
            return False

    def upsert_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> Tuple[int, bool]:
        if not self.available or self.index is None:
            return 0, False

        try:
            namespace = self._namespace(repo_id, commit_sha)
            payload = []
            vector_dim = 0
            batch_size = 100

            for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                vector_id = chunk.get("id") or f"{repo_id}:{commit_sha}:{chunk.get('file_path', '')}:{idx}"
                vector_dim = len(vector) if hasattr(vector, "__len__") else vector_dim
                payload.append(
                    {
                        "id": vector_id,
                        "values": [float(value) for value in vector],
                        "metadata": {
                            "repo_id": repo_id,
                            "commit_sha": commit_sha,
                            "file_path": chunk.get("file_path", ""),
                            "start_line": chunk.get("start_line", 0),
                            "end_line": chunk.get("end_line", 0),
                            "language": chunk.get("language", ""),
                            "chunk_index": chunk.get("chunk_index", 0),
                            "code_content": chunk.get("code_content", ""),
                        },
                    }
                )

            logger.info(
                "[STEP 7] Uploading vectors to Pinecone | "
                f"index={self.config.pinecone_index_name} namespace={namespace} "
                f"vectors={len(payload)} vector_dim={vector_dim} batch_size={batch_size}"
            )
            uploaded = 0
            for start in range(0, len(payload), batch_size):
                batch = payload[start:start + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                uploaded += len(batch)
                logger.debug(
                    f"Pinecone upsert batch success | namespace={namespace} "
                    f"batch_start={start} batch_count={len(batch)} uploaded_total={uploaded}"
                )
            logger.info(
                "Pinecone upsert completed | "
                f"namespace={namespace} vectors_uploaded={uploaded}"
            )
            return uploaded, True
        except Exception as exc:
            logger.error(
                "Pinecone upsert failed | "
                f"namespace={self._namespace(repo_id, commit_sha)} error={exc}"
            )
            logger.error(f"Failed to upsert chunks to Pinecone: {exc}")
            return 0, False

    def query_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        query_vector: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not self.available or self.index is None:
            return []

        try:
            namespace = self._namespace(repo_id, commit_sha)
            response = self.index.query(
                vector=list(query_vector),
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
            )

            results = []
            for match in self._result_matches(response):
                if isinstance(match, dict):
                    score = match.get("score", 0)
                    metadata = match.get("metadata", {}) or {}
                    match_id = match.get("id", "")
                else:
                    score = getattr(match, "score", 0)
                    metadata = getattr(match, "metadata", {}) or {}
                    match_id = getattr(match, "id", "")

                if score < similarity_threshold:
                    continue

                results.append(
                    (
                        {
                            "id": match_id,
                            "file_path": metadata.get("file_path", ""),
                            "start_line": metadata.get("start_line", 0),
                            "end_line": metadata.get("end_line", 0),
                            "language": metadata.get("language", ""),
                            "chunk_index": metadata.get("chunk_index", 0),
                            "code_content": metadata.get("code_content", ""),
                        },
                        score,
                    )
                )

            logger.debug(f"Pinecone query returned {len(results)} results for {repo_id}@{commit_sha}")
            return results
        except Exception as exc:
            logger.error(f"Pinecone query failed: {exc}")
            return []

    def delete_repo(self, repo_id: str) -> bool:
        if not self.available or self.index is None:
            return False

        try:
            prefix = self._namespace(repo_id, "")
            stats = self.index.describe_index_stats()
            deleted = 0

            for namespace in self._stats_namespaces(stats):
                if namespace.startswith(prefix):
                    self.index.delete(delete_all=True, namespace=namespace)
                    deleted += 1

            logger.info(f"Deleted {deleted} Pinecone namespaces for {repo_id}")
            return True
        except Exception as exc:
            logger.error(f"Failed to delete repo from Pinecone: {exc}")
            return False

    def get_metadata(self) -> Dict[str, Any]:
        if not self.available or self.index is None:
            return {
                "backend_type": "pinecone",
                "is_available": False,
                "index_name": self.config.pinecone_index_name,
            }

        try:
            stats = self.index.describe_index_stats()
            return {
                "backend_type": "pinecone",
                "is_available": True,
                "index_name": self.config.pinecone_index_name,
                "total_namespaces": len(self._stats_namespaces(stats)),
                "total_vectors": self._stats_total_vectors(stats),
                "dimension": self.config.pinecone_dimension,
                "commit_cache_enabled": self.config.enable_commit_cache,
                "namespace_prefix": self.config.pinecone_namespace_prefix,
            }
        except Exception as exc:
            return {
                "backend_type": "pinecone",
                "is_available": False,
                "error": str(exc),
            }
