"""Tests for the Interactive Repository Architecture Q&A feature."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
from src.utils.repository_registry import RepositoryRegistry


class TestArchitectureQueryAnswerer:
    """Test the ArchitectureQueryAnswerer module."""
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample repository metadata for testing."""
        return {
            "repository": {
                "name": "fastapi",
                "url": "https://github.com/tiangolo/fastapi",
                "path": "/tmp/fastapi"
            },
            "analysis": {
                "file_count": 150,
                "primary_language": "Python",
                "languages": ["Python", "Markdown", "YAML"],
                "has_backend": True,
                "has_frontend": False
            },
            "frameworks": {
                "FastAPI": {"confidence": 0.95},
                "Pydantic": {"confidence": 0.90},
                "Starlette": {"confidence": 0.85}
            },
            "tech_stack": ["Python", "FastAPI", "Uvicorn", "Pydantic"],
            "architecture_patterns": ["API-First", "Microservices"],
            "modules": [
                {
                    "name": "main",
                    "type": "module",
                    "file_count": 25,
                    "extensions": [".py"]
                },
                {
                    "name": "routers",
                    "type": "module",
                    "file_count": 15,
                    "extensions": [".py"]
                },
                {
                    "name": "models",
                    "type": "module",
                    "file_count": 20,
                    "extensions": [".py"]
                }
            ],
            "important_files": {
                "main": ["main.py"],
                "config": ["config.py"],
                "requirements": ["requirements.txt", "pyproject.toml"]
            },
            "dependencies": {
                "production": {"fastapi": "0.104.0", "uvicorn": "0.24.0"},
                "development": {"pytest": "7.4.0", "black": "23.10.0"}
            },
            "root_files": ["README.md", "LICENSE", "setup.py"]
        }
    
    def test_initialization_with_api_key(self):
        """Test initialization when OpenAI API key is available."""
        with patch("src.modules.architecture_query_answerer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key-123"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.OPENAI_TEMPERATURE = 0.7
            mock_settings.OPENAI_MAX_TOKENS = 1000
            
            with patch("src.modules.architecture_query_answerer.OpenAI"):
                answerer = ArchitectureQueryAnswerer()
                assert answerer.client is not None
    
    def test_initialization_without_api_key(self):
        """Test initialization when OpenAI API key is not available."""
        with patch("src.modules.architecture_query_answerer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            answerer = ArchitectureQueryAnswerer()
            assert answerer.client is None
    
    def test_answer_question_with_invalid_input(self, sample_metadata):
        """Test error handling for invalid question input."""
        answerer = ArchitectureQueryAnswerer()
        
        with pytest.raises(ValueError) as exc_info:
            answerer.answer_question(sample_metadata, "")
        
        assert "non-empty string" in str(exc_info.value)
    
    def test_construct_context(self, sample_metadata):
        """Test context construction from metadata."""
        answerer = ArchitectureQueryAnswerer()
        context = answerer._construct_context(sample_metadata)
        
        # Verify context includes key information
        assert "fastapi" in context.lower()
        assert "fastapi" in context.lower()  # Framework
        assert "python" in context.lower()  # Language
        assert "150" in context  # File count
        assert "main" in context  # Module name
    
    def test_build_query_prompt(self, sample_metadata):
        """Test prompt building for queries."""
        answerer = ArchitectureQueryAnswerer()
        context = answerer._construct_context(sample_metadata)
        question = "What is the architecture of this project?"
        
        prompt = answerer._build_query_prompt(context, question)
        
        assert question in prompt
        assert context in prompt
        assert "REPOSITORY CONTEXT" in prompt
        assert "QUESTION" in prompt
    
    def test_rule_based_answer_without_api(self, sample_metadata):
        """Test rule-based answering when AI is unavailable."""
        with patch("src.modules.architecture_query_answerer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            answerer = ArchitectureQueryAnswerer()
            result = answerer.answer_question(sample_metadata, "What is this project?")
            
            assert result["status"] == "success"
            assert result["mode"] == "rule-based"
            assert "fastapi" in result["answer"].lower()
            assert result["question"] == "What is this project?"
    
    def test_answer_what_is_project(self, sample_metadata):
        """Test 'What is?' question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_what_is_project(sample_metadata)
        
        assert "fastapi" in answer.lower()
        assert "backend service" in answer.lower() or "python" in answer.lower()
        assert "150 files" in answer
    
    def test_answer_how_structured(self, sample_metadata):
        """Test 'How is it structured?' question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_how_structured(sample_metadata)
        
        assert "component" in answer.lower() or "module" in answer.lower()
        assert "main" in answer
        assert "API-First" in answer or "Microservices" in answer
    
    def test_answer_tech_stack(self, sample_metadata):
        """Test technology stack question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_tech_stack(sample_metadata)
        
        assert "fastapi" in answer.lower()
        assert "python" in answer.lower()
        assert "Pydantic" in answer
    
    def test_answer_frameworks(self, sample_metadata):
        """Test framework detection question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_frameworks(sample_metadata)
        
        assert "FastAPI" in answer
        assert "95%" in answer or "0.95" in answer
    
    def test_answer_components(self, sample_metadata):
        """Test component listing question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_components(sample_metadata)
        
        assert "main" in answer.lower()
        assert "routers" in answer.lower()
        assert "25 files" in answer or "15 files" in answer
    
    def test_answer_backend_info(self, sample_metadata):
        """Test backend information question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_backend_info(sample_metadata)
        
        assert "backend" in answer.lower()
        assert "fastapi" in answer.lower()
    
    def test_answer_dependencies(self, sample_metadata):
        """Test dependency information question handling."""
        answerer = ArchitectureQueryAnswerer()
        
        answer = answerer._answer_dependencies(sample_metadata)
        
        assert "2 packages" in answer  # 2 production deps
        assert "fastapi" in answer.lower()
    
    def test_pattern_matching_what_is(self, sample_metadata):
        """Test pattern matching for 'what is' questions."""
        answerer = ArchitectureQueryAnswerer()
        
        result = answerer._rule_based_answer(sample_metadata, "What is this repository?")
        
        assert "fastapi" in result["answer"].lower()
    
    def test_pattern_matching_how_structured(self, sample_metadata):
        """Test pattern matching for 'how is it' questions."""
        answerer = ArchitectureQueryAnswerer()
        
        result = answerer._rule_based_answer(sample_metadata, "How is this project structured?")
        
        assert "component" in result["answer"].lower() or "module" in result["answer"].lower()
    
    def test_pattern_matching_technology(self, sample_metadata):
        """Test pattern matching for technology questions."""
        answerer = ArchitectureQueryAnswerer()
        
        result = answerer._rule_based_answer(sample_metadata, "What technology stack is used?")
        
        assert "fastapi" in result["answer"].lower() or "python" in result["answer"].lower()
    
    def test_pattern_matching_architecture(self, sample_metadata):
        """Test pattern matching for architecture questions."""
        answerer = ArchitectureQueryAnswerer()
        
        result = answerer._rule_based_answer(sample_metadata, "What is the architecture pattern?")
        
        assert "api" in result["answer"].lower() or "microservices" in result["answer"].lower()
    
    def test_general_query_fallback(self, sample_metadata):
        """Test fallback for unmatched question patterns."""
        answerer = ArchitectureQueryAnswerer()
        
        result = answerer._rule_based_answer(sample_metadata, "Tell me something random")
        
        assert "fastapi" in result["answer"].lower()
        assert "python" in result["answer"].lower()


class TestRepositoryRegistry:
    """Test the RepositoryRegistry module."""
    
    def test_register_and_get_repository(self, tmp_path):
        """Test registering and retrieving repository metadata."""
        registry = RepositoryRegistry(cache_dir=str(tmp_path))
        
        metadata = {
            "repository": {"name": "test-repo", "url": "https://github.com/test/repo"},
            "analysis": {"file_count": 50}
        }
        
        registry.register("test-repo", metadata)
        retrieved = registry.get("test-repo")
        
        assert retrieved is not None
        assert retrieved["repository"]["name"] == "test-repo"
        assert retrieved["analysis"]["file_count"] == 50
    
    def test_repository_exists(self, tmp_path):
        """Test checking repository existence."""
        registry = RepositoryRegistry(cache_dir=str(tmp_path))
        
        assert not registry.exists("nonexistent-repo")
        
        metadata = {"repository": {"name": "test-repo"}}
        registry.register("test-repo", metadata)
        
        assert registry.exists("test-repo")
    
    def test_list_repositories(self, tmp_path):
        """Test listing all registered repositories."""
        registry = RepositoryRegistry(cache_dir=str(tmp_path))
        
        repos = [
            {"repository": {"name": "repo1"}},
            {"repository": {"name": "repo2"}},
            {"repository": {"name": "repo3"}}
        ]
        
        for i, metadata in enumerate(repos, 1):
            registry.register(f"repo{i}", metadata)
        
        repo_list = registry.list_repositories()
        
        assert len(repo_list) == 3
        assert "repo1" in repo_list
        assert "repo2" in repo_list
        assert "repo3" in repo_list
    
    def test_persistence_across_instances(self, tmp_path):
        """Test that metadata persists across registry instances."""
        cache_dir = str(tmp_path)
        
        # Register in first instance
        registry1 = RepositoryRegistry(cache_dir=cache_dir)
        metadata = {"repository": {"name": "test-repo"}, "data": "value1"}
        registry1.register("test-repo", metadata)
        
        # Retrieve in new instance
        registry2 = RepositoryRegistry(cache_dir=cache_dir)
        retrieved = registry2.get("test-repo")
        
        assert retrieved is not None
        assert retrieved["data"] == "value1"
    
    def test_get_nonexistent_repository(self, tmp_path):
        """Test getting nonexistent repository."""
        registry = RepositoryRegistry(cache_dir=str(tmp_path))
        
        result = registry.get("nonexistent")
        
        assert result is None


class TestQueryIntegration:
    """Integration tests for the Q&A system."""
    
    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata."""
        return {
            "repository": {
                "name": "example-project",
                "url": "https://github.com/example/project"
            },
            "analysis": {
                "file_count": 100,
                "primary_language": "Python",
                "languages": ["Python"],
                "has_backend": True,
                "has_frontend": False
            },
            "frameworks": {"Flask": {"confidence": 0.9}},
            "tech_stack": ["Python", "Flask"],
            "architecture_patterns": ["MVC"],
            "modules": [{"name": "app", "type": "module", "file_count": 30, "extensions": [".py"]}],
            "important_files": {"main": ["app.py"]},
            "dependencies": {"production": {"flask": "2.0.0"}},
            "root_files": ["README.md"]
        }
    
    def test_query_flow_without_ai(self, sample_metadata, tmp_path):
        """Test full Q&A flow without OpenAI."""
        with patch("src.modules.architecture_query_answerer.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            registry = RepositoryRegistry(cache_dir=str(tmp_path))
            registry.register("example-project", sample_metadata)
            
            answerer = ArchitectureQueryAnswerer()
            result = answerer.answer_question(sample_metadata, "What frameworks are used?")
            
            assert result["status"] == "success"
            assert result["mode"] == "rule-based"
            assert "Flask" in result["answer"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
