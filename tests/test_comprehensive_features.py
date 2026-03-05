"""Comprehensive tests for integrated system features and improvements."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer, QueryIntent, IntentMatch
from src.modules.diagram_generator import ArchitectureDiagramGenerator, validate_mermaid_diagram
from src.utils.config import settings
from src.api.routes import QueryResponse


class TestConfigurationHelpers:
    """Test configuration helper methods for AI usability."""
    
    def test_is_ai_usable_with_api_key_and_enabled(self):
        """When API key exists and ENABLE_AI_CHAT=True, AI should be usable."""
        with patch.object(settings, 'GOOGLE_API_KEY', 'test-key'):
            with patch.object(settings, 'ENABLE_AI_CHAT', True):
                assert settings.is_ai_usable() is True
    
    def test_is_ai_usable_with_api_key_but_disabled(self):
        """When ENABLE_AI_CHAT=False, AI should NOT be usable even with key."""
        with patch.object(settings, 'GOOGLE_API_KEY', 'test-key'):
            with patch.object(settings, 'ENABLE_AI_CHAT', False):
                assert settings.is_ai_usable() is False
    
    def test_is_ai_usable_without_api_key(self):
        """When API key missing, AI should NOT be usable."""
        with patch.object(settings, 'GOOGLE_API_KEY', ''):
            with patch.object(settings, 'ENABLE_AI_CHAT', True):
                assert settings.is_ai_usable() is False
    
    def test_get_ai_disabled_reason_when_config_disabled(self):
        """Returns appropriate message when AI disabled in config."""
        with patch.object(settings, 'ENABLE_AI_CHAT', False):
            with patch.object(settings, 'GOOGLE_API_KEY', 'test-key'):
                reason = settings.get_ai_disabled_reason()
                assert 'disabled' in reason.lower() or 'config' in reason.lower()
    
    def test_get_ai_disabled_reason_when_no_api_key(self):
        """Returns appropriate message when API key missing."""
        with patch.object(settings, 'GOOGLE_API_KEY', ''):
            with patch.object(settings, 'ENABLE_AI_CHAT', True):
                reason = settings.get_ai_disabled_reason()
                assert 'api' in reason.lower() or 'key' in reason.lower()


class TestIntentDetection:
    """Test intent detection in query answerer."""
    
    def setup_method(self):
        """Setup answerer for each test."""
        self.answerer = ArchitectureQueryAnswerer()
    
    def test_detect_project_overview_intent(self):
        """Should detect project overview questions."""
        questions = [
            "What is this project?",
            "What does this project do?",
            "Tell me about this repository"
        ]
        
        for question in questions:
            intent = self.answerer._detect_intent(question)
            assert intent.intent == QueryIntent.PROJECT_OVERVIEW
            assert intent.confidence >= 0.9
    
    def test_detect_architecture_intent(self):
        """Should detect architecture questions."""
        questions = [
            "How is it structured?",
            "What is the architecture?",
            "Show me a diagram"
        ]
        
        for question in questions:
            intent = self.answerer._detect_intent(question)
            assert intent.intent == QueryIntent.ARCHITECTURE
            assert intent.confidence >= 0.9
    
    def test_detect_tech_stack_intent(self):
        """Should detect technology/framework questions."""
        questions = [
            "What technologies are used?",
            "What's the tech stack?",
            "What frameworks?"
        ]
        
        for question in questions:
            intent = self.answerer._detect_intent(question)
            assert intent.intent == QueryIntent.TECH_STACK
            assert intent.confidence >= 0.9
    
    def test_detect_components_intent(self):
        """Should detect component/module questions."""
        questions = [
            "What are the components?",
            "What modules exist?",
            "What are the parts?"
        ]
        
        for question in questions:
            intent = self.answerer._detect_intent(question)
            assert intent.intent == QueryIntent.COMPONENTS
    
    def test_detect_data_flow_intent(self):
        """Should detect data flow questions."""
        questions = [
            "How does data flow?",
            "What is the request-response cycle?",
            "How does data move through the system?"
        ]
        
        for question in questions:
            intent = self.answerer._detect_intent(question)
            assert intent.intent == QueryIntent.DATA_FLOW
    
    def test_detect_deployment_intent(self):
        """Should detect deployment questions."""
        questions = [
            "How is it deployed?",
            "What about production?",
            "How do we scale this?"
        ]
        
        for question in questions:
            intent = self.answerer._detect_intent(question)
            assert intent.intent == QueryIntent.DEPLOYMENT
    
    def test_default_to_general_intent(self):
        """Should default to general intent for non-matching questions."""
        question = "This is a random question that doesn't match patterns"
        intent = self.answerer._detect_intent(question)
        assert intent.intent == QueryIntent.GENERAL
        assert intent.confidence <= 0.5


class TestRuleBasedAnswering:
    """Test rule-based answer generation for all intents."""
    
    def setup_method(self):
        """Setup answerer and metadata for each test."""
        self.answerer = ArchitectureQueryAnswerer()
        self.metadata = self._create_test_metadata()
    
    def _create_test_metadata(self):
        """Create realistic test metadata."""
        return {
            "repository": {
                "name": "test-project",
                "url": "https://github.com/test/project",
                "path": "/tmp/test-project"
            },
            "analysis": {
                "file_count": 150,
                "primary_language": "Python",
                "languages": {"python": 100, "javascript": 30, "yaml": 20},
                "has_backend": True,
                "has_frontend": True
            },
            "frameworks": {
                "Django": {"confidence": 0.95, "matched_patterns": ["models.py", "settings.py"]},
                "React": {"confidence": 0.90, "matched_patterns": ["components/", "hooks/"]}
            },
            "tech_stack": ["Django", "React", "PostgreSQL", "Redis"],
            "architecture_patterns": ["MVC", "REST API"],
            "dependencies": {
                "production": {"django": "4.0", "react": "18.0"},
                "development": {"pytest": "7.0", "black": "22.0"}
            },
            "modules": [
                {"name": "backend", "type": "Backend Service", "file_count": 60, "extensions": [".py"]},
                {"name": "frontend", "type": "Frontend", "file_count": 40, "extensions": [".js", ".jsx"]},
                {"name": "api", "type": "API Handler", "file_count": 20, "extensions": [".py"]}
            ],
            "root_files": ["README.md", "Dockerfile", "docker-compose.yml"],
            "important_files": ["README.md", "package.json", "requirements.txt"]
        }
    
    def test_answer_project_overview(self):
        """Should generate coherent project overview."""
        intent = IntentMatch(QueryIntent.PROJECT_OVERVIEW, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "What is this?")
        
        assert answer  # Non-empty
        assert "test-project" in answer
        assert "full-stack" in answer.lower() or "web" in answer.lower()
    
    def test_answer_architecture(self):
        """Should describe architecture clearly."""
        intent = IntentMatch(QueryIntent.ARCHITECTURE, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "How is it structured?")
        
        assert answer
        assert "backend" in answer.lower() or "component" in answer.lower()
    
    def test_answer_tech_stack(self):
        """Should list technologies and frameworks."""
        intent = IntentMatch(QueryIntent.TECH_STACK, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "What tech?")
        
        assert answer
        assert "Django" in answer or "Python" in answer  # Should mention detected tech
    
    def test_answer_components(self):
        """Should list components and modules."""
        intent = IntentMatch(QueryIntent.COMPONENTS, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "What are components?")
        
        assert answer
        assert "backend" in answer.lower() or "module" in answer.lower()
    
    def test_answer_data_flow(self):
        """Should explain data flow clearly."""
        intent = IntentMatch(QueryIntent.DATA_FLOW, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "How does data flow?")
        
        assert answer
        assert "frontend" in answer.lower() or "backend" in answer.lower() or "request" in answer.lower()
    
    def test_answer_deployment(self):
        """Should describe deployment."""
        intent = IntentMatch(QueryIntent.DEPLOYMENT, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "How to deploy?")
        
        assert answer
        # Should mention deployment-related concepts
        assert any(term in answer.lower() for term in ["deploy", "docker", "backend", "frontend"])
    
    def test_answer_dependencies(self):
        """Should list dependencies."""
        intent = IntentMatch(QueryIntent.DEPENDENCIES, 1.0)
        answer = self.answerer._answer_by_intent(intent.intent, self.metadata, "What depends?")
        
        assert answer
        assert "production" in answer.lower() or "dependency" in answer.lower() or "django" in answer.lower()


class TestAIDisabledMode:
    """Test system behavior when AI is disabled."""
    
    def setup_method(self):
        """Setup for tests."""
        self.metadata = self._create_test_metadata()
    
    def _create_test_metadata(self):
        """Create test metadata."""
        return {
            "repository": {"name": "test-repo", "url": "https://github.com/test/repo", "path": "/tmp/test"},
            "analysis": {"file_count": 100, "primary_language": "Python", "languages": {}, "has_backend": True, "has_frontend": False},
            "frameworks": {}, "tech_stack": [], "architecture_patterns": [],
            "dependencies": {}, "modules": [], "root_files": [], "important_files": []
        }
    
    @patch('src.modules.architecture_query_answerer.settings.is_ai_usable')
    def test_ai_disabled_returns_rule_based_mode(self, mock_usable):
        """When AI disabled, should return rule-based mode."""
        mock_usable.return_value = False
        
        answerer = ArchitectureQueryAnswerer()
        result = answerer.answer_question(self.metadata, "What is this?")
        
        assert result["mode"] == "rule-based"
        assert "rule-based" in result["ai_mode"].lower()
    
    @patch('src.modules.architecture_query_answerer.settings.is_ai_usable')
    @patch('src.modules.architecture_query_answerer.settings.get_ai_disabled_reason')
    def test_ai_disabled_provides_reason(self, mock_reason, mock_usable):
        """Should include reason why AI is disabled."""
        mock_usable.return_value = False
        mock_reason.return_value = "AI chat disabled in configuration"
        
        answerer = ArchitectureQueryAnswerer()
        result = answerer.answer_question(self.metadata, "What is this?")
        
        assert "disabled" in result["ai_mode"].lower() or "configuration" in result["ai_mode"].lower()
    
    @patch('src.modules.architecture_query_answerer.settings.is_ai_usable')
    def test_ai_disabled_includes_response_fields(self, mock_usable):
        """Should include all required response fields in rule-based mode."""
        mock_usable.return_value = False
        
        answerer = ArchitectureQueryAnswerer()
        result = answerer.answer_question(self.metadata, "What is this?")
        
        # Verify response structure
        assert "mode" in result
        assert "ai_mode" in result
        assert "used_rag" in result
        assert "intent" in result
        assert "status" in result
        assert "answer" in result


class TestDiagramGeneration:
    """Test architecture diagram generation."""
    
    def setup_method(self):
        """Setup generator and metadata for each test."""
        self.generator = ArchitectureDiagramGenerator()
        self.metadata = self._create_test_metadata()
    
    def _create_test_metadata(self):
        """Create realistic test metadata for diagrams."""
        return {
            "repository": {
                "name": "test-project",
                "url": "https://github.com/test/project",
                "path": "/tmp/test",
                "root_files": ["README.md", "Dockerfile"]
            },
            "analysis": {
                "file_count": 200,
                "primary_language": "Python",
                "languages": {"python": 120, "javascript": 80},
                "has_backend": True,
                "has_frontend": True
            },
            "frameworks": {
                "FastAPI": {"confidence": 0.95, "matched_patterns": ["main.py"]},
                "React": {"confidence": 0.90, "matched_patterns": ["App.jsx"]},
                "PostgreSQL": {"confidence": 0.85, "matched_patterns": ["models"]},
                "Docker": {"confidence": 0.80, "matched_patterns": ["Dockerfile"]}
            },
            "tech_stack": ["FastAPI", "React", "PostgreSQL", "Redis"],
            "architecture_patterns": ["REST", "MVC"],
            "dependencies": {
                "production": {"fastapi": "0.100", "sqlalchemy": "2.0", "pydantic": "2.0"},
                "development": {"pytest": "7.0"}
            },
            "modules": [
                {"name": "services", "type": "Backend Service", "file_count": 60, "extensions": [".py"]},
                {"name": "handlers", "type": "API Handler", "file_count": 40, "extensions": [".py"]},
                {"name": "components", "type": "Frontend", "file_count": 80, "extensions": [".jsx"]},
            ],
            "root_files": ["Dockerfile", "docker-compose.yml"],
            "important_files": ["README.md"]
        }
    
    def test_diagram_generation_succeeds(self):
        """Should generate diagram without errors."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        
        assert diagrams is not None
        assert "mermaid" in diagrams
        assert diagrams["mermaid"] is not None
    
    def test_mermaid_diagram_is_valid(self):
        """Generated Mermaid should be syntactically valid."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        mermaid_code = diagrams["mermaid"]
        
        is_valid, errors = validate_mermaid_diagram(mermaid_code)
        if not is_valid:
            print(f"Validation errors: {errors}")
        assert is_valid or len(errors) == 0 or all(e is None for e in errors)
    
    def test_mermaid_includes_frontend_node(self):
        """Diagram should include frontend layer when detected."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        mermaid_code = diagrams["mermaid"]
        
        assert "client" in mermaid_code or "frontend" in mermaid_code.lower() or "Client" in mermaid_code
    
    def test_mermaid_includes_backend_node(self):
        """Diagram should include backend/services when detected."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        mermaid_code = diagrams["mermaid"]
        
        assert "backend" in mermaid_code.lower() or "service" in mermaid_code.lower() or "Service" in mermaid_code
    
    def test_mermaid_includes_database_node(self):
        """Diagram should include database when indicators present."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        mermaid_code = diagrams["mermaid"]
        
        assert "database" in mermaid_code.lower() or "Database" in mermaid_code
    
    def test_mermaid_includes_style_classes(self):
        """Diagram should have style class definitions."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        mermaid_code = diagrams["mermaid"]
        
        assert "classDef" in mermaid_code
        # Should have color definitions for different node types
        assert "fill:" in mermaid_code
    
    def test_mermaid_diagram_plain_format(self):
        """Mermaid should be returned in plain format (not Markdown-wrapped)."""
        diagrams = self.generator.generate_diagrams(self.metadata)
        mermaid_code = diagrams["mermaid"]
        
        # Should start with 'graph' directive, not with markdown code block
        assert mermaid_code.strip().startswith("graph")
        assert "```mermaid" not in mermaid_code
        assert "```" not in mermaid_code


class TestAPIResponseFormat:
    """Test API response format includes all required fields."""
    
    def test_query_response_model_has_ai_mode_field(self):
        """QueryResponse should have ai_mode field."""
        response = QueryResponse(
            status="success",
            repository="test",
            question="test",
            answer="test",
            mode="ai",
            ai_mode="Gemini",
            used_rag=False,
            intent="project_overview",
            note="test note"
        )
        
        assert response.ai_mode == "Gemini"
    
    def test_query_response_model_has_used_rag_field(self):
        """QueryResponse should have used_rag field."""
        response = QueryResponse(
            status="success",
            repository="test",
            question="test",
            answer="test",
            mode="ai",
            ai_mode="RAG + Gemini",
            used_rag=True,
            intent="data_flow",
            note="test"
        )
        
        assert response.used_rag is True
    
    def test_query_response_model_has_intent_field(self):
        """QueryResponse should have intent field."""
        response = QueryResponse(
            status="success",
            repository="test",
            question="test",
            answer="test",
            mode="rule-based",
            ai_mode="Rule-based",
            used_rag=False,
            intent="architecture",
            note="test"
        )
        
        assert response.intent == "architecture"


class TestMetadataBuilderRAGFlag:
    """Test that ENABLE_RAG_INDEX_ON_ANALYZE flag is respected."""
    
    @patch('src.modules.metadata_builder.settings.ENABLE_RAG', True)
    @patch('src.modules.metadata_builder.settings.ENABLE_RAG_INDEX_ON_ANALYZE', False)
    @patch('src.modules.metadata_builder.settings.GOOGLE_API_KEY', '')
    def test_index_skipped_when_flag_false(self, mock_key, mock_index_on_analyze, mock_enable_rag):
        """Should skip RAG indexing when ENABLE_RAG_INDEX_ON_ANALYZE=False."""
        from src.modules.metadata_builder import RepositoryMetadataBuilder
        
        builder = RepositoryMetadataBuilder()
        metadata = {"repository": {"name": "test"}}
        
        # This should not raise an error, and indexing should be skipped
        result = builder._index_code_for_rag("/tmp/test", metadata)
        
        # Function should return without doing anything
        assert result is None
    
    @patch('src.modules.metadata_builder.settings.ENABLE_RAG', False)
    def test_index_skipped_when_rag_disabled(self, mock_enable_rag):
        """Should skip RAG indexing when RAG system disabled."""
        from src.modules.metadata_builder import RepositoryMetadataBuilder
        
        builder = RepositoryMetadataBuilder()
        metadata = {"repository": {"name": "test"}}
        
        result = builder._index_code_for_rag("/tmp/test", metadata)
        
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
