"""Reset local indexing state and Pinecone namespaces."""

import os
import stat
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.vector_store_pinecone import PineconeProvider
from src.modules.vector_store_provider import VectorStoreConfig
from src.utils.config import settings
from src.utils.logging_utils import configure_library_log_levels


def remove_and_recreate(path: Path) -> None:
    if path.exists():
        def onerror(func, target, exc_info):
            try:
                os.chmod(target, stat.S_IWRITE | stat.S_IREAD)
                func(target)
            except Exception:
                raise

        shutil.rmtree(path, onerror=onerror)
    path.mkdir(parents=True, exist_ok=True)


def clear_local_state() -> None:
    local_paths = [
        Path(settings.REPO_CLONE_PATH),
        Path(settings.DIAGRAM_OUTPUT_PATH),
        Path(settings.RAG_INDEX_PATH),
        PROJECT_ROOT / "metadata_cache",
    ]

    print("[RESET] Clearing local repositories, diagrams, metadata cache, and index artifacts")
    for path in local_paths:
        remove_and_recreate(path)
        print(f"[RESET] Local path cleared: {path}")


def clear_pinecone() -> None:
    print("[RESET] Clearing Pinecone namespaces")
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
    if not provider.health_check():
        raise SystemExit("Pinecone health check failed during reset")

    stats = provider.index.describe_index_stats()
    namespaces = provider._stats_namespaces(stats)
    print(f"[RESET] Namespaces found: {list(namespaces.keys())}")
    for namespace in namespaces:
        provider.index.delete(delete_all=True, namespace=namespace)
        print(f"[RESET] Deleted Pinecone namespace: {namespace}")


def main() -> None:
    configure_library_log_levels()
    clear_local_state()
    clear_pinecone()
    print("[RESET] Indexing environment reset complete")


if __name__ == "__main__":
    main()
