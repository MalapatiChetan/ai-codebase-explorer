"""Example usage of the AI Codebase Explainer system."""

import json
from src.modules.metadata_builder import RepositoryMetadataBuilder
from src.modules.ai_analyzer import AIArchitectureAnalyzer


def analyze_repository_example():
    """Example of how to use the system programmatically."""
    
    # This is how you would use the system programmatically
    # (Note: This requires having a real GitHub URL)
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         AI Codebase Explainer - Usage Example               ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Method 1: Using the REST API (Recommended)
    ═══════════════════════════════════════════════════════════════
    
    1. Start the server:
       python -m uvicorn src.main:app --reload
    
    2. Send an analysis request:
       curl -X POST http://localhost:8000/api/analyze \\
         -H "Content-Type: application/json" \\
         -d '{
           "repo_url": "https://github.com/fastapi/fastapi",
           "include_ai_analysis": true
         }'
    
    3. Get the response:
       {
         "status": "success",
         "repository_name": "fastapi",
         "message": "Repository analysis completed",
         "metadata": {
           "repository": { ... },
           "analysis": { ... },
           "frameworks": { ... },
           "tech_stack": [ ... ],
           "modules": [ ... ],
           ...
         },
         "analysis": {
           "status": "success",
           "analysis": {
             "raw_analysis": "...",
             ...
           }
         }
       }
    
    ═══════════════════════════════════════════════════════════════
    
    Method 2: Using the Library Programmatically
    ═══════════════════════════════════════════════════════════════
    
    from src.modules.metadata_builder import RepositoryMetadataBuilder
    from src.modules.ai_analyzer import AIArchitectureAnalyzer
    
    # Build metadata
    builder = RepositoryMetadataBuilder()
    metadata = builder.build_metadata("https://github.com/user/repo")
    
    # Generate AI analysis
    analyzer = AIArchitectureAnalyzer()
    analysis = analyzer.analyze(metadata)
    
    # Use the results
    print(metadata['repository']['name'])
    print(metadata['tech_stack'])
    print(analysis['analysis']['raw_analysis'])
    
    ═══════════════════════════════════════════════════════════════
    
    API Endpoints
    ═══════════════════════════════════════════════════════════════
    
    POST /api/analyze
      Analyze a GitHub repository
      Request: { "repo_url": string, "include_ai_analysis": bool }
      Response: Complete analysis with metadata and AI insights
    
    GET /api/health
      Health check endpoint
      Response: { "status": "healthy", ... }
    
    GET /api/info
      Service information
      Response: { "service": "...", "version": "...", ... }
    
    GET /docs
      Interactive API documentation (Swagger UI)
    
    GET /redoc
      API documentation (ReDoc)
    
    ═══════════════════════════════════════════════════════════════
    
    Example API Response Structure
    ═════════════════════════════════════════════════════════════════
    
    {
      "status": "success",
      "repository_name": "fastapi",
      "message": "Repository analysis completed",
      "metadata": {
        "repository": {
          "url": "https://github.com/fastapi/fastapi",
          "name": "fastapi",
          "path": "./data/repos/fastapi"
        },
        "analysis": {
          "file_count": 75,
          "primary_language": "Python",
          "languages": {
            "py": 65,
            "md": 8,
            "yaml": 2
          },
          "has_backend": true,
          "has_frontend": false
        },
        "frameworks": {
          "FastAPI": { "confidence": 0.95 },
          "Pydantic": { "confidence": 0.85 }
        },
        "tech_stack": ["Python", "FastAPI", "Pydantic"],
        "architecture_patterns": ["API-First"],
        "modules": [
          {
            "name": "fastapi",
            "type": "Backend Logic",
            "file_count": 45,
            "extensions": [".py"]
          },
          ...
        ],
        "important_files": [
          "README.md",
          "pyproject.toml",
          "requirements.txt"
        ]
      },
      "analysis": {
        "status": "success",
        "analysis": {
          "raw_analysis": "...",
          "system_overview": "...",
          ...
        }
      }
    }
    
    ═════════════════════════════════════════════════════════════════
    
    Configuration
    ═════════════════════════════════════════════════════════════════
    
    Create a .env file with:
    
    OPENAI_API_KEY=sk-xxx...xxx  (optional, for AI analysis)
    REPO_CLONE_PATH=./data/repos
    DEBUG=false
    
    ═════════════════════════════════════════════════════════════════
    """)


if __name__ == "__main__":
    analyze_repository_example()
