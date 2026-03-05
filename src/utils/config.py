"""Configuration management for AI Codebase Explainer."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings.
    
    Configuration sources (in precedence order):
    1. Environment variables (e.g., export GOOGLE_API_KEY=...)
    2. .env file in current working directory
    3. Class defaults (defined below)
    
    For boolean values in .env files, use: true, false, 1, 0 (case-sensitive)
    """
    
    # API Configuration
    API_TITLE: str = "AI Codebase Explainer"
    API_VERSION: str = "0.1.0"
    DEBUG: bool = False  # Use 'true'/'false' or '1'/'0' in .env (case-sensitive)
    
    # Google Gemini Configuration (via google-genai SDK)
    # Primary AI provider: Gemini API
    GOOGLE_API_KEY: str = ""  # Get from: https://aistudio.google.com/app/apikey
    GOOGLE_MODEL: str = "gemini-2.5-flash"  # Valid models: gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash, or gemini-flash-latest
    GOOGLE_TEMPERATURE: float = 0.7
    GOOGLE_MAX_TOKENS: int = 4000
    
    # Optional legacy support: if GOOGLE_API_KEY not set but OPENAI_API_KEY is,
    # you can manually map it. This is intentionally not automatic to avoid confusion.
    # OPENAI_API_KEY: str = ""  # Not used - Gemini is primary provider
    
    # AI Chat Configuration
    ENABLE_AI_CHAT: bool = True  # Master switch: disable to force rule-based answers
    
    # Repository Configuration
    REPO_CLONE_PATH: str = "./data/repos"
    MAX_REPO_SIZE_MB: int = 500
    MAX_ANALYSIS_FILES: int = 100
    
    # GitHub Configuration (for private repositories - optional)
    GITHUB_TOKEN: str = ""  # Personal Access Token for private repos
    GITHUB_USERNAME: str = ""  # GitHub username if using authentication
    
    # Diagram Generation Configuration
    DIAGRAM_OUTPUT_PATH: str = "./data/diagrams"
    GENERATE_MERMAID: bool = True
    GENERATE_GRAPHVIZ: bool = True
    
    # Database Configuration (for caching - optional)
    DATABASE_URL: str = ""  # e.g., "sqlite:///./analysis_cache.db"
    ENABLE_CACHING: bool = False
    CACHE_TTL_HOURS: int = 24
    
    # Async Processing Configuration
    ENABLE_ASYNC_PROCESSING: bool = False
    TASK_QUEUE_URL: str = ""  # e.g., "redis://localhost:6379"
    
    # RAG (Retrieval-Augmented Generation) Configuration
    ENABLE_RAG: bool = True
    ENABLE_RAG_INDEX_ON_ANALYZE: bool = False  # Only index when query requires it, not during analysis
    RAG_INDEX_PATH: str = "./data/rag_indices"
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # Lightweight, fast model
    RAG_CHUNK_SIZE: int = 500  # Code chunk size in characters
    RAG_CHUNK_OVERLAP: int = 100  # Overlap between chunks
    RAG_TOP_K: int = 5  # Number of chunks to retrieve for context
    RAG_SIMILARITY_THRESHOLD: float = 0.3  # Minimum similarity score
    
    # Analysis Configuration
    SKIP_DIRS: list = [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".env",
        ".idea",
        ".vscode",
        "dist",
        "build",
        ".gradle",
        "target",
        ".next",
        "vendor",
        "deps",
        "lib",
        "pkg",
        ".bundle",
        ".pytest_cache",
        ".mypy_cache",
        "site-packages",
        "bin",
        "obj",
    ]
    
    IMPORTANT_FILES: list = [
        "README.md",
        "README.txt",
        "package.json",
        "pom.xml",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "setup.py",
        "pyproject.toml",
        "Gemfile",
        "go.mod",
        "Cargo.toml",
        ".github",
    ]
    
    class Config:
        """Pydantic configuration.
        
        case_sensitive = True means environment variable names must match exactly:
          Good:  GOOGLE_API_KEY, ENABLE_AI_CHAT
          Bad:   google_api_key, enable_ai_chat (won't be recognized)
        
        env_file = ".env" loads from .env in current working directory.
        Extra env vars not in Settings are silently ignored (safe for Docker/K8s).
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True  # Variable names must match exactly
    
    def is_ai_usable(self) -> bool:
        """Check if AI chat is actually usable (enabled and has API key).
        
        Returns:
            True if ENABLE_AI_CHAT=True AND GOOGLE_API_KEY is set and non-empty
            False otherwise
        """
        return self.ENABLE_AI_CHAT and bool(self.GOOGLE_API_KEY)
    
    def get_ai_disabled_reason(self) -> str:
        """Get reason why AI might not be usable. Returns empty string if AI is usable.
        
        Returns:
            Non-empty string if AI is disabled/unavailable, empty string if usable.
            Useful for logging and user-facing error messages.
        """
        if not self.ENABLE_AI_CHAT:
            return "AI chat disabled in configuration (ENABLE_AI_CHAT=False)"
        if not self.GOOGLE_API_KEY:
            return "Google API key not configured (GOOGLE_API_KEY empty or missing from .env)"
        return ""  # AI is usable, return empty string
    
    def validate_at_startup(self) -> None:
        """Validate critical configuration at startup. Logs warnings but doesn't crash.
        
        Use this in main.py to log configuration issues before running the server.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Check AI configuration
        if not self.is_ai_usable():
            reason = self.get_ai_disabled_reason()
            logger.warning(f"⚠ AI not usable: {reason}")
            logger.warning("  → System will use rule-based answers only")
        else:
            logger.info("✓ AI (Gemini) configured and ready")
        
        # Check repository paths
        repo_path = Path(self.REPO_CLONE_PATH)
        if not repo_path.exists():
            logger.warning(f"⚠ Repository clone path doesn't exist: {self.REPO_CLONE_PATH}")
        
        # Check diagram output path
        diagram_path = Path(self.DIAGRAM_OUTPUT_PATH)
        if not diagram_path.exists():
            logger.warning(f"⚠ Diagram output path doesn't exist: {self.DIAGRAM_OUTPUT_PATH}")
        
        # Check RAG configuration
        if self.ENABLE_RAG:
            rag_path = Path(self.RAG_INDEX_PATH)
            if not rag_path.exists():
                logger.warning(f"⚠ RAG index path doesn't exist: {self.RAG_INDEX_PATH}")
            if not self.GOOGLE_API_KEY:
                logger.warning("⚠ RAG enabled but no GOOGLE_API_KEY; RAG won't be used")


# Create settings instance
settings = Settings()

# Note: Directory creation moved to main.py startup event for cloud compatibility
# Cloud platforms (Render, Vercel) may have ephemeral /tmp that's only available at runtime

# Optional: Call validate_at_startup() from main.py
# Example in main.py:
#   from src.utils.config import settings
#   settings.validate_at_startup()
