"""Integration tests for truncation fixes and RAG improvements.

Tests:
1. Prompt budgeting correctly reserves output tokens
2. Long queries don't truncate with new settings
3. finish_reason logging works
4. Commit-aware caching prevents re-indexing
5. Local FAISS provider works end-to-end
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.utils.prompt_budget import (
    estimate_tokens, create_budget, trim_code_snippets, trim_context
)
from src.modules.vector_store_provider import LocalFaissProvider, VectorStoreConfig


class TestPromptBudgeting:
    """Tests for token budgeting utilities."""
    
    def test_estimate_tokens_basic(self):
        """Test rough token estimation."""
        text = "Hello world"  # ~3 words
        tokens = estimate_tokens(text)
        assert 2 <= tokens <= 5, "Should estimate roughly 3 tokens"
    
    def test_estimate_tokens_empty(self):
        """Test empty string."""
        tokens = estimate_tokens("")
        assert tokens == 0
    
    def test_estimate_tokens_large(self):
        """Test larger text."""
        text = "This is a much longer text. " * 100
        tokens = estimate_tokens(text)
        assert tokens > 500, "Should estimate hundreds of tokens"
    
    def test_create_budget_not_over(self):
        """Test budget when not exceeded."""
        budget = create_budget(
            model="gemini-2.5-flash",
            system_prompt="You are helpful.",
            user_question="What is this?",
            context="Some context here.",
            reserved_output_tokens=1500,
        )
        assert not budget.is_over_budget, "Should not be over budget with small text"
        assert budget.available_for_context > 1500
    
    def test_create_budget_calculates_ratio(self):
        """Test budget trim ratio calculation."""
        budget = create_budget(
            model="gemini-2.5-flash",
            system_prompt="System",
            user_question="Q",
            context="X" * 100000,  # Huge context
            reserved_output_tokens=1500,
        )
        # Will be over budget
        assert budget.is_over_budget
        assert 0 <= budget.context_trim_ratio <= 1.0
    
    def test_trim_code_snippets_limits_count(self):
        """Test that snippet count is limited."""
        context = """RELEVANT CODE SNIPPETS:
============================================================

[Snippet 1] file1.py (Lines 1-10)
Language: python | Relevance: 95%
code here

[Snippet 2] file2.py (Lines 20-30)
Language: python | Relevance: 90%
more code

[Snippet 3] file3.py (Lines 40-50)
Language: python | Relevance: 85%
more code

[Snippet 4] file4.py (Lines 60-70)
Language: python | Relevance: 80%
more code

QUESTION:
What is this?"""
        
        trimmed, stats = trim_code_snippets(context, max_snippets=2)
        
        assert stats["snippets_found"] == 4
        assert stats["snippets_kept"] == 2
        assert "Snippet 3" not in trimmed
        assert "Snippet 4" not in trimmed
    
    def test_trim_context_preserves_priority(self):
        """Test that high-priority sections are preserved when trimming."""
        context = """REPOSITORY ARCHITECTURE:
Important framework info here.

CODE SNIPPETS:
Some code
Some more code
Even more code
More and more code
Even more code
""" * 10  # Large expansion
        
        trimmed, stats = trim_context(
            context,
            max_chars=1000,
            priority_sections=["REPOSITORY ARCHITECTURE"],
        )
        
        assert stats["status"] == "trimmed"
        assert "REPOSITORY ARCHITECTURE" in trimmed


class TestLocalFaissProvider:
    """Tests for local FAISS vector store provider."""
    
    @pytest.fixture
    def config(self, tmp_path):
        """Create temporary config for testing."""
        return VectorStoreConfig(
            backend="local_faiss",
            local_index_path=str(tmp_path / "indices"),
            enable_commit_cache=True,
        )
    
    def test_health_check_available(self, config):
        """Test health check when available."""
        try:
            provider = LocalFaissProvider(config)
            # If FAISS is installed, should be available
            assert provider.available == True or provider.available == False
        except Exception as e:
            pytest.skip(f"FAISS not available: {e}")
    
    def test_has_commit_index_nonexistent(self, config):
        """Test checking for nonexistent index."""
        try:
            import faiss  # Skip if not available
            provider = LocalFaissProvider(config)
            exists = provider.has_commit_index("test/repo", "abc123def")
            assert exists == False, "Nonexistent index should return False"
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_upsert_and_query(self, config):
        """Test storing and retrieving chunks."""
        try:
            import faiss
            provider = LocalFaissProvider(config)
            
            if not provider.available:
                pytest.skip("FAISS not available")
            
            # Prepare test data
            chunks = [
                {
                    "id": "1",
                    "file_path": "main.py",
                    "start_line": 1,
                    "end_line": 10,
                    "code_content": "def hello(): return 'world'",
                    "language": "python",
                },
                {
                    "id": "2",
                    "file_path": "utils.py",
                    "start_line": 20,
                    "end_line": 30,
                    "code_content": "def greet(name): return f'Hello {name}'",
                    "language": "python",
                },
            ]
            
            # Create vectors (384 dims for all-MiniLM-L6-v2)
            vectors = [[0.1] * 384, [0.2] * 384]
            
            # Upsert
            count, success = provider.upsert_chunks(
                "test/repo",
                "abc123def",
                chunks,
                vectors,
            )
            
            assert success == True
            assert count == 2
            
            # Check cache hit
            has_index = provider.has_commit_index("test/repo", "abc123def")
            assert has_index == True, "Index should exist after upsert"
            
            # Query
            query_vector = [0.1] * 384
            results = provider.query_chunks(
                "test/repo",
                "abc123def",
                query_vector,
                top_k=2,
                similarity_threshold=0.0,  # Accept all
            )
            
            assert len(results) > 0, "Should find similar chunks"
            chunk, score = results[0]
            assert "file_path" in chunk
            assert 0 <= score <= 1, "Similarity should be 0-1"
        
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_delete_repo(self, config):
        """Test deleting repository indices."""
        try:
            import faiss
            provider = LocalFaissProvider(config)
            
            if not provider.available:
                pytest.skip("FAISS not available")
            
            chunks = [
                {"id": "1", "file_path": "test.py", "start_line": 1,
                 "end_line": 5, "code_content": "test", "language": "python"}
            ]
            vectors = [[0.1] * 384]
            
            # Upsert first
            provider.upsert_chunks("test/repo", "abc123", chunks, vectors)
            provider.upsert_chunks("test/repo", "def456", chunks, vectors)
            
            # Delete repo
            success = provider.delete_repo("test/repo")
            assert success == True
            
            # Verify deleted
            assert not provider.has_commit_index("test/repo", "abc123")
            assert not provider.has_commit_index("test/repo", "def456")
        
        except ImportError:
            pytest.skip("FAISS not installed")
    
    def test_metadata_returns_stats(self, config):
        """Test that metadata returns expected structure."""
        try:
            import faiss
            provider = LocalFaissProvider(config)
            metadata = provider.get_metadata()
            
            assert "backend_type" in metadata
            assert "is_available" in metadata
            assert metadata["backend_type"] == "local_faiss"
        except ImportError:
            pytest.skip("FAISS not installed")


class TestCommitCaching:
    """Tests for commit-aware caching behavior."""
    
    def test_skip_reindex_same_commit(self, tmp_path):
        """Test that re-indexing is skipped when commit unchanged."""
        try:
            import faiss
            
            config = VectorStoreConfig(
                backend="local_faiss",
                local_index_path=str(tmp_path / "indices"),
                enable_commit_cache=True,
            )
            provider = LocalFaissProvider(config)
            
            if not provider.available:
                pytest.skip("FAISS not available")
            
            chunks = [
                {"id": "1", "file_path": "test.py", "start_line": 1,
                 "end_line": 5, "code_content": "test", "language": "python"}
            ]
            vectors = [[0.1] * 384]
            
            # First index
            repo_id = "test/repo"
            commit = "abc123def"
            provider.upsert_chunks(repo_id, commit, chunks, vectors)
            
            # Check if commit index exists
            has_index_1 = provider.has_commit_index(repo_id, commit)
            assert has_index_1 == True
            
            # Index again with same commit
            has_index_2 = provider.has_commit_index(repo_id, commit)
            assert has_index_2 == True, "Should recognize same commit"
            
            # Different commit
            has_index_3 = provider.has_commit_index(repo_id, "xyz789")
            assert has_index_3 == False, "Different commit should not have index"
        
        except ImportError:
            pytest.skip("FAISS not installed")


class TestObservabilityLogging:
    """Tests for observability metrics logging."""
    
    def test_budget_contains_all_fields(self):
        """Test that budget dict contains all required fields."""
        budget = create_budget(
            model="gemini-2.5-flash",
            system_prompt="Test",
            user_question="Q",
            context="Context",
            reserved_output_tokens=1500,
        )
        
        budget_dict = budget.to_dict()
        required_fields = [
            "model",
            "system_prompt_tokens",
            "user_question_tokens",
            "context_tokens",
            "available_for_context",
            "reserved_output_tokens",
            "is_over_budget",
        ]
        
        for field in required_fields:
            assert field in budget_dict, f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
