"""Validation tests for refactoring fixes."""

import json
import tempfile
import logging
from pathlib import Path
from unittest import mock

import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestFrameworkDetection:
    """Tests for improved framework detection with dependency parsing."""
    
    def test_framework_not_detected_without_dependency(self):
        """Framework should NOT be detected if dependency is missing."""
        from src.modules.framework_detector import FrameworkDetector
        
        detector = FrameworkDetector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create package.json WITHOUT react dependency
            package_json = {
                "name": "test-app",
                "version": "1.0.0",
                "dependencies": {
                    "axios": "^0.21.0"  # No react!
                }
            }
            with open(repo_path / "package.json", "w") as f:
                json.dump(package_json, f)
            
            # Create minimal metadata
            repo_metadata = {
                "files": [],
                "root_files": ["package.json"],
                "languages": {}
            }
            
            # Detect frameworks
            detected = detector.detect_frameworks(repo_path, repo_metadata)
            
            # React should NOT be detected
            assert "React" not in detected, "React should not be detected without react dependency"
            logger.info("✓ Framework not detected without dependency")
    
    def test_framework_detected_with_dependency(self):
        """Framework SHOULD be detected when dependency is present."""
        from src.modules.framework_detector import FrameworkDetector
        
        detector = FrameworkDetector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create package.json WITH react dependency
            package_json = {
                "name": "test-app",
                "version": "1.0.0",
                "dependencies": {
                    "react": "^18.0.0",
                    "axios": "^0.21.0"
                }
            }
            with open(repo_path / "package.json", "w") as f:
                json.dump(package_json, f)
            
            # Create minimal metadata
            repo_metadata = {
                "files": [],
                "root_files": ["package.json"],
                "languages": {}
            }
            
            # Detect frameworks
            detected = detector.detect_frameworks(repo_path, repo_metadata)
            
            # React SHOULD be detected
            assert "React" in detected, "React should be detected when react is in dependencies"
            assert detected["React"]["confidence"] >= 0.7, "Confidence should be high for actual dependency"
            logger.info(f"✓ React detected with confidence {detected['React']['confidence']:.1%}")
    
    def test_python_framework_detection(self):
        """Test Python framework detection from requirements.txt."""
        from src.modules.framework_detector import FrameworkDetector
        
        detector = FrameworkDetector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create requirements.txt with FastAPI
            with open(repo_path / "requirements.txt", "w") as f:
                f.write("fastapi==0.100.0\n")
                f.write("uvicorn==0.24.0\n")
                f.write("numpy==1.24.0\n")
            
            # Create minimal metadata
            repo_metadata = {
                "files": [],
                "root_files": ["requirements.txt"],
                "languages": {}
            }
            
            # Detect frameworks
            detected = detector.detect_frameworks(repo_path, repo_metadata)
            
            # FastAPI should be detected
            assert "FastAPI" in detected, "FastAPI should be detected from requirements.txt"
            assert detected["FastAPI"]["confidence"] >= 0.7
            logger.info(f"✓ FastAPI detected with confidence {detected['FastAPI']['confidence']:.1%}")
    
    def test_devdependencies_parsing(self):
        """Test that devDependencies are also parsed from package.json."""
        from src.modules.framework_detector import FrameworkDetector
        
        detector = FrameworkDetector()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create package.json with Angular in devDependencies
            package_json = {
                "name": "test-app",
                "dependencies": {},
                "devDependencies": {
                    "@angular/core": "^15.0.0"
                }
            }
            with open(repo_path / "package.json", "w") as f:
                json.dump(package_json, f)
            
            # Create minimal metadata
            repo_metadata = {
                "files": [],
                "root_files": ["package.json"],
                "languages": {}
            }
            
            # Detect frameworks
            detected = detector.detect_frameworks(repo_path, repo_metadata)
            
            # Angular should be detected from devDependencies
            assert "Angular" in detected, "Angular should be detected from devDependencies"
            logger.info("✓ DevDependencies parsed correctly")


class TestRAGIndexingControl:
    """Tests for RAG indexing control flags."""
    
    def test_rag_indexing_skipped_when_disabled(self):
        """RAG indexing should skip when ENABLE_RAG_INDEX_ON_ANALYZE is False."""
        from src.modules.metadata_builder import RepositoryMetadataBuilder
        
        builder = RepositoryMetadataBuilder()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create minimum viable repo structure
            (repo_path / "src").mkdir(parents=True)
            (repo_path / "src" / "main.py").write_text("print('test')")
            
            metadata = {
                "repository": {"name": "test-repo", "url": "http://test", "path": str(repo_path)},
                "analysis": {"file_count": 1, "primary_language": "Python", "languages": {}}
            }
            
            # Mock settings where they're actually imported
            with mock.patch("src.utils.config.settings") as mock_settings:
                mock_settings.ENABLE_RAG = True
                mock_settings.ENABLE_RAG_INDEX_ON_ANALYZE = False  # DISABLE indexing on analyze
                mock_settings.GOOGLE_API_KEY = "test-key"
                
                # Call indexing method - should return early
                builder._index_code_for_rag(str(repo_path), metadata)
                
                logger.info("✓ RAG indexing skipped when ENABLE_RAG_INDEX_ON_ANALYZE=False")
    
    def test_rag_indexing_skipped_without_ai_provider(self):
        """RAG indexing should skip when no AI provider (Google API key) is configured."""
        from src.modules.metadata_builder import RepositoryMetadataBuilder
        
        builder = RepositoryMetadataBuilder()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create minimum viable repo structure
            (repo_path / "src").mkdir(parents=True)
            (repo_path / "src" / "main.py").write_text("print('test')")
            
            metadata = {
                "repository": {"name": "test-repo", "url": "http://test", "path": str(repo_path)},
                "analysis": {"file_count": 1, "primary_language": "Python", "languages": {}}
            }
            
            # Mock settings where they're actually imported
            with mock.patch("src.utils.config.settings") as mock_settings:
                mock_settings.ENABLE_RAG = True
                mock_settings.ENABLE_RAG_INDEX_ON_ANALYZE = True  # Enable indexing on analyze
                mock_settings.GOOGLE_API_KEY = ""  # NO API KEY
                
                # Call indexing method - should return early
                builder._index_code_for_rag(str(repo_path), metadata)
                
                logger.info("✓ RAG indexing skipped when no Google API key configured")


class TestQueryContextBuilding:
    """Tests for context construction with corrected data structures."""
    
    def test_languages_dict_handling(self):
        """Test that languages dict is properly converted to list for context."""
        from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
        
        answerer = ArchitectureQueryAnswerer()
        
        # Create metadata with languages as dict (as it is in real data)
        metadata = {
            "repository": {"name": "test-repo", "url": "http://test"},
            "analysis": {
                "primary_language": "Python",
                "file_count": 10,
                "languages": {"py": 8, "js": 2},  # Dict, not list!
                "has_backend": True,
                "has_frontend": False
            },
            "frameworks": {},
            "tech_stack": [],
            "architecture_patterns": [],
            "modules": [],
            "dependencies": {}
        }
        
        # Should not raise an exception
        try:
            context = answerer._construct_context(metadata)
            assert "Python" in context, "Primary language should be in context"
            assert "py" in context or "js" in context, "Languages should be listed"
            logger.info("✓ Languages dict properly converted to list")
        except TypeError as e:
            pytest.fail(f"Context construction failed with dict languages: {e}")
    
    def test_important_files_list_handling(self):
        """Test that important_files list is properly iterated."""
        from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
        
        answerer = ArchitectureQueryAnswerer()
        
        # Create metadata with important_files as list (as it is in real data)
        metadata = {
            "repository": {"name": "test-repo", "url": "http://test"},
            "analysis": {
                "primary_language": "Python",
                "file_count": 10,
                "languages": {"py": 8},
                "has_backend": True,
                "has_frontend": False
            },
            "frameworks": {},
            "tech_stack": [],
            "architecture_patterns": [],
            "modules": [],
            "important_files": ["README.md", "package.json", "Dockerfile"],  # List, not dict!
            "dependencies": {}
        }
        
        # Should not raise an exception
        try:
            context = answerer._construct_context(metadata)
            assert "README.md" in context, "Important files should be in context"
            logger.info("✓ Important files list properly iterated")
        except Exception as e:
            pytest.fail(f"Context construction failed with list important_files: {e}")


class TestQueryPipelineMode:
    """Tests for query pipeline mode selection and logging."""
    
    def test_rag_mode_indicated_in_response(self):
        """Response should include ai_mode indicating which mode was used."""
        from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
        
        answerer = ArchitectureQueryAnswerer()
        
        metadata = {
            "repository": {"name": "test-repo", "url": "http://test"},
            "analysis": {
                "primary_language": "Python",
                "file_count": 10,
                "languages": {"py": 8},
                "has_backend": True,
                "has_frontend": False
            },
            "frameworks": {},
            "tech_stack": [],
            "architecture_patterns": [],
            "modules": [],
            "important_files": [],
            "dependencies": {}
        }
        
        # Test rule-based mode
        response = answerer._rule_based_answer(metadata, "What is this project?")
        
        assert "ai_mode" in response, "Response should include ai_mode field"
        assert "Rule-based fallback" in response["ai_mode"], "Rule-based mode should be indicated"
        assert response["mode"] == "rule-based", "Mode should be 'rule-based'"
        logger.info(f"✓ Rule-based response includes ai_mode: {response['ai_mode']}")


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
