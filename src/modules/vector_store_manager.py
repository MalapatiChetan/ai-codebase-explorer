"""Vector store manager with backend selection and fallback logic."""

import logging
from typing import List, Tuple, Dict, Any

from src.modules.vector_store_provider import (
    LocalFaissProvider,
    VectorStoreConfig,
)
from src.utils.config import settings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manage the active vector backend and fallback behavior."""

    def __init__(self):
        self.config = VectorStoreConfig(
            backend=settings.VECTOR_BACKEND,
            enable_commit_cache=settings.ENABLE_COMMIT_CACHE,
            local_index_path=settings.RAG_INDEX_PATH,
            pinecone_api_key=settings.PINECONE_API_KEY,
            pinecone_index_name=settings.PINECONE_INDEX_NAME,
            pinecone_environment=settings.PINECONE_ENVIRONMENT,
            pinecone_namespace_prefix=settings.PINECONE_NAMESPACE_PREFIX,
        )

        self.primary_provider = None
        self.fallback_provider = None
        self.active_provider = None
        self.backend_stats = {
            "primary_backend": settings.VECTOR_BACKEND,
            "fallback_backend": "local_faiss",
            "is_using_fallback": False,
            "total_operations": 0,
            "fallback_triggers": 0,
        }

        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize the configured backend and optional FAISS fallback."""
        if settings.VECTOR_BACKEND == "pinecone":
            try:
                from src.modules.vector_store_pinecone import PineconeProvider

                self.primary_provider = PineconeProvider(self.config)
                if self.primary_provider.health_check():
                    self.active_provider = self.primary_provider
                    logger.debug("Using Pinecone as primary vector store")
                else:
                    logger.warning("Pinecone health check failed, falling back if possible")
            except Exception as exc:
                logger.warning(f"Failed to initialize Pinecone: {exc}. Falling back if possible.")
        else:
            self.primary_provider = LocalFaissProvider(self.config)
            self.active_provider = self.primary_provider
            logger.debug("Using Local FAISS as vector store")

        if settings.VECTOR_BACKEND != "local_faiss":
            self.fallback_provider = LocalFaissProvider(self.config)
            if self.fallback_provider.health_check():
                if self.active_provider is None:
                    self.active_provider = self.fallback_provider
                    self.backend_stats["is_using_fallback"] = True
                logger.debug("Local FAISS available as fallback")
            else:
                logger.warning("Local FAISS fallback is not available")

    def _execute_with_fallback(self, operation_name: str, operation_func, *args, **kwargs):
        """Run an operation on the active provider, then fallback if needed."""
        self.backend_stats["total_operations"] += 1

        if self.active_provider is None:
            raise RuntimeError("No active vector store provider is available")

        try:
            return operation_func(self.active_provider, *args, **kwargs)
        except Exception as exc:
            logger.error(f"{operation_name} failed on {self.config.backend}: {exc}")

            if self.fallback_provider and self.active_provider is not self.fallback_provider:
                logger.warning("Attempting fallback to Local FAISS")
                self.backend_stats["fallback_triggers"] += 1
                self.backend_stats["is_using_fallback"] = True
                self.active_provider = self.fallback_provider
                return operation_func(self.fallback_provider, *args, **kwargs)

            raise

    def has_commit_index(self, repo_id: str, commit_sha: str) -> bool:
        """Check whether the repo+commit index already exists."""
        try:
            logger.debug(
                f"Checking namespace in vector backend={self.config.backend} "
                f"repo={repo_id} commit_sha={commit_sha}"
            )
            return self._execute_with_fallback(
                "has_commit_index",
                lambda provider: provider.has_commit_index(repo_id, commit_sha),
            )
        except Exception as exc:
            logger.error(f"Failed to check commit index: {exc}")
            return False

    def upsert_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        chunks: List[Dict[str, Any]],
        vectors: List[List[float]],
    ) -> Tuple[int, bool]:
        """Store chunk embeddings in the active backend."""
        try:
            count, success = self._execute_with_fallback(
                "upsert_chunks",
                lambda provider: provider.upsert_chunks(repo_id, commit_sha, chunks, vectors),
            )

            if success and self.active_provider:
                logger.debug(
                    f"Upserted {count} chunks for {repo_id}@{commit_sha} "
                    f"via {self.active_provider.__class__.__name__}"
                )

            return count, success
        except Exception as exc:
            logger.error(f"Failed to upsert chunks: {exc}")
            return 0, False

    def query_chunks(
        self,
        repo_id: str,
        commit_sha: str,
        query_vector: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> Tuple[List[Tuple[Dict[str, Any], float]], Dict[str, Any]]:
        """Query the active backend and return observability metadata."""
        try:
            results = self._execute_with_fallback(
                "query_chunks",
                lambda provider: provider.query_chunks(
                    repo_id,
                    commit_sha,
                    query_vector,
                    top_k,
                    similarity_threshold,
                ),
            )
            return results, {
                "retrieval_backend": self.active_provider.__class__.__name__ if self.active_provider else None,
                "repo_id": repo_id,
                "commit_sha": commit_sha,
                "results_count": len(results),
                "top_k_requested": top_k,
                "is_fallback": self.backend_stats["is_using_fallback"],
                "status": "success",
            }
        except Exception as exc:
            logger.error(f"Failed to query chunks: {exc}")
            return [], {"status": "error", "error": str(exc), "retrieval_backend": None}

    def delete_repo(self, repo_id: str) -> bool:
        """Delete a repository from the active backend."""
        try:
            success = self._execute_with_fallback(
                "delete_repo",
                lambda provider: provider.delete_repo(repo_id),
            )
            if success:
                logger.info(f"Deleted embeddings for {repo_id}")
            return success
        except Exception as exc:
            logger.error(f"Failed to delete repo: {exc}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return manager and backend metadata."""
        try:
            primary_metadata = self.primary_provider.get_metadata() if self.primary_provider else {}
            fallback_metadata = self.fallback_provider.get_metadata() if self.fallback_provider else {}
        except Exception as exc:
            logger.warning(f"Could not get backend metadata: {exc}")
            primary_metadata = {}
            fallback_metadata = {}

        return {
            **self.backend_stats,
            "primary_backend_meta": primary_metadata,
            "fallback_backend_meta": fallback_metadata,
            "active_provider": self.active_provider.__class__.__name__ if self.active_provider else None,
        }

    def health_check(self) -> bool:
        """Return whether at least one backend is currently usable."""
        if self.active_provider is None:
            return False
        try:
            return self.active_provider.health_check()
        except Exception as exc:
            logger.warning(f"Vector store health check failed: {exc}")
            return False


_manager = None


def get_vector_store_manager() -> VectorStoreManager:
    """Return the shared vector store manager instance."""
    global _manager
    if _manager is None:
        _manager = VectorStoreManager()
    return _manager
