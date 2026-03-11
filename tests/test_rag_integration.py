"""Integration tests for RAG vector store with commit-aware caching."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.modules.rag_vector_store import RAGVectorStore, EmbeddingGenerator
from src.modules.code_indexer import CodeChunk
from src.utils.config import settings


class TestRAGVectorStoreIntegration:
    """Test RAG vector store integration with observability."""
    
    @pytest.fixture
    def mock_embedding_gen(self):
        """Create a mock embedding generator."""
        gen = Mock(spec=EmbeddingGenerator)
        gen.is_available.return_value = True
        gen.embedding_dim = 384
        gen.embed_chunks.return_value = [np.random.randn(384) for _ in range(3)]
        gen.embed_text.return_value = np.random.randn(384)
        return gen
    
    @pytest.fixture
    def mock_vector_store_manager(self):
        """Create a mock vector store manager."""
        manager = Mock()
        manager.health_check.return_value = True
        manager.has_commit_index.return_value = False
        manager.upsert_chunks.return_value = (3, True)
        manager.query_chunks.return_value = (
            [
                ({"file_path": "test.py", "code_content": "x = 1", "start_line": 1, "end_line": 1, "language": "python"}, 0.95),
                ({"file_path": "test2.py", "code_content": "y = 2", "start_line": 1, "end_line": 1, "language": "python"}, 0.85),
            ],
            {"provider": "faiss", "results_count": 2, "status": "success"}
        )
        return manager
    
    @pytest.fixture
    def sample_chunks(self):
        """Create sample code chunks for testing."""
        return [
            CodeChunk("test.py", 1, 10, "x = 1", "python"),
            CodeChunk("test.py", 11, 20, "y = 2", "python"),
            CodeChunk("test2.py", 1, 5, "def foo():\n    pass", "python"),
        ]
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    def test_rag_store_initialization_with_commit(self, mock_get_manager, mock_vector_store_manager):
        """Test RAGVectorStore initialization with commit SHA."""
        mock_get_manager.return_value = mock_vector_store_manager
        
        # Create store with commit SHA
        store = RAGVectorStore("fastapi/fastapi", commit_sha="abc123def456")
        
        assert store.repo_name == "fastapi/fastapi"
        assert store.commit_sha == "abc123def456"
        assert store.is_available()
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    def test_rag_store_initialization_without_commit(self, mock_get_manager, mock_vector_store_manager):
        """Test RAGVectorStore initialization without commit SHA."""
        mock_get_manager.return_value = mock_vector_store_manager
        
        # Create store without commit SHA
        store = RAGVectorStore("fastapi/fastapi")
        
        assert store.repo_name == "fastapi/fastapi"
        assert store.commit_sha is None
        assert store.is_available()
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    @patch('src.modules.rag_vector_store.EmbeddingGenerator')
    def test_index_chunks_returns_observability(self, mock_emb_class, mock_get_manager, 
                                                 mock_vector_store_manager, mock_embedding_gen, sample_chunks):
        """Test that index_chunks returns tuple with observability metadata."""
        mock_get_manager.return_value = mock_vector_store_manager
        mock_emb_class.return_value = mock_embedding_gen
        
        store = RAGVectorStore("fastapi/fastapi", commit_sha="abc123")
        success, observability = store.index_chunks(sample_chunks)
        
        # Verify return format
        assert isinstance(success, bool)
        assert isinstance(observability, dict)
        assert success is True
        
        # Verify observability content
        assert "status" in observability
        assert "repo" in observability
        assert "chunk_count" in observability
        assert observability["repo"] == "fastapi/fastapi"
        assert observability["chunk_count"] == 3
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    @patch('src.modules.rag_vector_store.EmbeddingGenerator')
    def test_index_chunks_with_commit_cache_hit(self, mock_emb_class, mock_get_manager,
                                                  mock_vector_store_manager, mock_embedding_gen, sample_chunks):
        """Test that commit cache hit skips indexing."""
        mock_get_manager.return_value = mock_vector_store_manager
        mock_emb_class.return_value = mock_embedding_gen
        
        # Setup: existing commit index
        with patch('src.utils.config.settings') as mock_settings:
            mock_settings.ENABLE_COMMIT_CACHE = True
            mock_settings.ENABLE_RAG = True
            mock_settings.RAG_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
            mock_settings.RAG_INDEX_PATH = "/tmp/rag"
            mock_settings.RAG_BATCH_SIZE = 50
            
            mock_vector_store_manager.has_commit_index.return_value = True  # Cache hit
            
            store = RAGVectorStore("fastapi/fastapi", commit_sha="abc123")
            success, observability = store.index_chunks(sample_chunks)
            
            # Should return cached result
            assert success is True
            assert observability["status"] == "cached"
            assert observability["cache_hit"] is True
            
            # Verify upsert was not called (because of cache hit)
            mock_vector_store_manager.upsert_chunks.assert_not_called()
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    @patch('src.modules.rag_vector_store.EmbeddingGenerator')
    def test_search_returns_observability(self, mock_emb_class, mock_get_manager,
                                           mock_vector_store_manager, mock_embedding_gen):
        """Test that search returns tuple with observability metadata."""
        mock_get_manager.return_value = mock_vector_store_manager
        mock_emb_class.return_value = mock_embedding_gen
        
        store = RAGVectorStore("fastapi/fastapi", commit_sha="abc123")
        results, observability = store.search("How do I use this?", k=5)
        
        # Verify return format
        assert isinstance(results, list)
        assert isinstance(observability, dict)
        
        # Verify results are CodeChuncks with scores
        assert len(results) == 2  # mock returns 2 results
        for chunk, score in results:
            assert hasattr(chunk, 'file_path')
            assert hasattr(chunk, 'code_content')
            assert isinstance(score, float)
            assert 0 <= score <= 1
        
        # Verify observability content
        assert "status" in observability
        assert observability["status"] == "success"
        assert observability["query_results_count"] == 2
        assert "query_text_length" in observability
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    @patch('src.modules.rag_vector_store.EmbeddingGenerator')
    def test_search_with_unavailable_system(self, mock_emb_class, mock_get_manager,
                                             mock_vector_store_manager, mock_embedding_gen):
        """Test search when RAG system is unavailable."""
        mock_get_manager.return_value = None
        
        with patch('src.utils.config.settings') as mock_settings:
            mock_settings.ENABLE_RAG = False
            
            store = RAGVectorStore("fastapi/fastapi")
            results, observability = store.search("test query")
            
            # Should return empty with unavailable status
            assert results == []
            assert observability["status"] == "unavailable"


class TestCommitAwareCaching:
    """Test commit-aware caching behavior."""

    @pytest.fixture
    def mock_vector_store_manager(self):
        """Create a mock vector store manager."""
        manager = Mock()
        manager.health_check.return_value = True
        manager.has_commit_index.return_value = False
        manager.upsert_chunks.return_value = (2, True)
        return manager
    
    @patch('src.modules.rag_vector_store.get_vector_store_manager')
    @patch('src.modules.rag_vector_store.EmbeddingGenerator')
    def test_different_commits_create_separate_indices(self, mock_emb_class, mock_get_manager,
                                                        mock_vector_store_manager):
        """Test that different commits are indexed separately."""
        mock_get_manager.return_value = mock_vector_store_manager
        mock_embedding_gen = Mock(spec=EmbeddingGenerator)
        mock_embedding_gen.is_available.return_value = True
        mock_embedding_gen.embedding_dim = 384
        mock_embedding_gen.embed_chunks.return_value = [np.random.randn(384) for _ in range(2)]
        mock_emb_class.return_value = mock_embedding_gen
        
        chunks = [
            CodeChunk("test.py", 1, 10, "x = 1", "python"),
            CodeChunk("test.py", 11, 20, "y = 2", "python"),
        ]
        
        # Index with commit 1
        store1 = RAGVectorStore("repo/test", commit_sha="commit1")
        store1.index_chunks(chunks)
        
        # Index with commit 2
        store2 = RAGVectorStore("repo/test", commit_sha="commit2")
        store2.index_chunks(chunks)
        
        # Verify manager was called with different commits
        calls = mock_vector_store_manager.upsert_chunks.call_args_list
        assert len(calls) == 2
        assert calls[0][1]["commit_sha"] == "commit1"
        assert calls[1][1]["commit_sha"] == "commit2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
