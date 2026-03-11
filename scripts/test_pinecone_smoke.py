"""Standalone Pinecone smoke test for 384-dimension vector upsert."""

import sys
from pathlib import Path
from uuid import uuid4

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.vector_store_pinecone import PineconeProvider
from src.modules.vector_store_provider import VectorStoreConfig
from src.utils.config import settings


def main():
    config = VectorStoreConfig(
        backend="pinecone",
        enable_commit_cache=True,
        local_index_path=settings.RAG_INDEX_PATH,
        pinecone_api_key=settings.PINECONE_API_KEY,
        pinecone_index_name=settings.PINECONE_INDEX_NAME,
        pinecone_environment=settings.PINECONE_ENVIRONMENT,
        pinecone_namespace_prefix=settings.PINECONE_NAMESPACE_PREFIX,
    )
    provider = PineconeProvider(config)
    print(f"provider_available={provider.available}")
    print(f"health_check={provider.health_check()}")

    if not provider.health_check():
        raise SystemExit("Pinecone health check failed")

    dummy_id = f"smoke-test-{uuid4()}"
    namespace = provider._namespace("debug/repo", "smoke-test")
    count, success = provider.upsert_chunks(
        repo_id="debug/repo",
        commit_sha="smoke-test",
        chunks=[
            {
                "id": dummy_id,
                "file_path": "debug.py",
                "start_line": 1,
                "end_line": 1,
                "language": "python",
                "chunk_index": 0,
                "code_content": "print('pinecone smoke test')",
            }
        ],
        vectors=[[0.01] * 384],
    )
    print(
        {
            "success": success,
            "count": count,
            "namespace": namespace,
            "index_name": settings.PINECONE_INDEX_NAME,
            "vector_dimension": 384,
            "vector_id": dummy_id,
        }
    )


if __name__ == "__main__":
    main()
