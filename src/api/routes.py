"""API routes for the codebase explainer."""

import logging
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path as PathParam
from src.modules.metadata_builder import RepositoryMetadataBuilder
from src.modules.ai_analyzer import AIArchitectureAnalyzer
from src.modules.diagram_generator import ArchitectureDiagramGenerator
from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
from src.utils.repository_registry import RepositoryRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize registry
registry = RepositoryRegistry()

# Request/Response models
class AnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_url: str = Field(..., description="GitHub repository URL")
    include_ai_analysis: bool = Field(default=True, description="Include AI analysis")
    include_diagrams: bool = Field(default=True, description="Include architecture diagrams")


class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    status: str = Field(..., description="Status of the analysis")
    repository_name: str = Field(..., description="Name of the repository")
    message: Optional[str] = Field(None, description="Status message")
    metadata: Optional[dict] = Field(None, description="Repository metadata")
    analysis: Optional[dict] = Field(None, description="AI analysis")
    diagrams: Optional[dict] = Field(None, description="Architecture diagrams")


class DiagramResponse(BaseModel):
    """Response model for diagram retrieval."""
    status: str = Field(..., description="Status of the request")
    repository_name: str = Field(..., description="Name of the repository")
    format: str = Field(..., description="Diagram format (mermaid, graphviz, json)")
    diagram: Optional[str] = Field(None, description="Diagram content (plain format, no markdown)")


class QueryRequest(BaseModel):
    """Request model for architecture Q&A."""
    repository_name: str = Field(..., description="Name of the analyzed repository")
    question: str = Field(..., description="Question about repository architecture")


class QueryResponse(BaseModel):
    """Response model for Q&A queries."""
    status: str = Field(..., description="Status of the query")
    repository: str = Field(..., description="Repository name")
    question: str = Field(..., description="The asked question")
    answer: str = Field(..., description="Answer to the question")
    mode: str = Field(..., description="Answer mode: 'ai' or 'rule-based'")
    ai_mode: str = Field(..., description="Specific AI mode: 'Gemini', 'RAG + Gemini', or 'Rule-based'")
    used_rag: bool = Field(..., description="Whether RAG was used to retrieve code context")
    intent: Optional[str] = Field(None, description="Detected question intent")
    note: Optional[str] = Field(None, description="Additional notes about the answer")


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_repository(request: AnalysisRequest):
    """
    Analyze a GitHub repository and generate architecture explanation.
    
    Args:
        request: AnalysisRequest with repo_url
        
    Returns:
        AnalysisResponse with metadata, AI analysis, and diagrams
    """
    try:
        logger.info(f"Received analysis request for: {request.repo_url}")
        
        # Validate URL
        if not request.repo_url.startswith("https://github.com/"):
            raise HTTPException(
                status_code=400,
                detail="Invalid GitHub URL. Must start with https://github.com/"
            )
        
        # Build metadata (includes diagram generation)
        logger.info("Building repository metadata...")
        metadata_builder = RepositoryMetadataBuilder()
        metadata = metadata_builder.build_metadata(request.repo_url)
        
        response_data = {
            "status": "success",
            "repository_name": metadata["repository"]["name"],
            "message": "Repository analysis completed",
            "metadata": metadata
        }
        
        # Generate AI analysis if requested
        if request.include_ai_analysis:
            logger.info("Generating AI analysis...")
            ai_analyzer = AIArchitectureAnalyzer()
            analysis = ai_analyzer.analyze(metadata)
            response_data["analysis"] = analysis
        
        # Include diagrams if available and requested
        if request.include_diagrams and "diagrams" in metadata:
            response_data["diagrams"] = metadata.pop("diagrams")
        
        # Register the analyzed repository
        registry.register(metadata["repository"]["name"], metadata)
        
        logger.info("Analysis request completed successfully")
        return AnalysisResponse(**response_data)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/diagrams/{repo_name}", response_model=DiagramResponse)
async def get_diagram(
    repo_name: str = PathParam(..., description="Repository name"),
    format: str = Query("mermaid", description="Diagram format: mermaid, graphviz, or json")
):
    """
    Retrieve a previously generated architecture diagram.
    
    Args:
        repo_name: Name of the repository (e.g., 'fastapi')
        format: Diagram format ('mermaid', 'graphviz', or 'json')
        
    Returns:
        DiagramResponse with the requested diagram
    """
    try:
        if format not in ["mermaid", "graphviz", "json"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Must be 'mermaid', 'graphviz', or 'json'"
            )
        
        logger.info(f"Retrieving {format} diagram for {repo_name}")
        diagram_generator = ArchitectureDiagramGenerator()
        diagram_content = diagram_generator.get_stored_diagram(repo_name, format)
        
        return DiagramResponse(
            status="success",
            repository_name=repo_name,
            format=format,
            diagram=diagram_content
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Diagram not found for repository '{repo_name}'. Please analyze it first."
        )
    except Exception as e:
        logger.error(f"Error retrieving diagram: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_repository_architecture(request: QueryRequest):
    """
    Ask a question about repository architecture.
    
    Args:
        request: QueryRequest with repository_name and question
        
    Returns:
        QueryResponse with answer and metadata
    """
    try:
        logger.info(f"Received query for {request.repository_name}: {request.question}")
        
        # Validate question
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Check if repository has been analyzed
        if not registry.exists(request.repository_name):
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{request.repository_name}' has not been analyzed. Please analyze it first using POST /api/analyze"
            )
        
        # Get repository metadata
        metadata = registry.get(request.repository_name)
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve metadata for '{request.repository_name}'"
            )
        
        # Generate answer
        logger.info("Generating architectural answer...")
        answerer = ArchitectureQueryAnswerer()
        result = answerer.answer_question(metadata, request.question)
        
        logger.info("Query processed successfully")
        return QueryResponse(
            status=result["status"],
            repository=result["repository"],
            question=result["question"],
            answer=result["answer"],
            mode=result["mode"],
            ai_mode=result.get("ai_mode", "Unknown"),
            used_rag=result.get("used_rag", False),
            intent=result.get("intent"),
            note=result.get("note")
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Codebase Explainer",
        "version": "0.1.0"
    }


@router.get("/info")
async def get_info():
    """Get information about the service."""
    return {
        "service": "AI Codebase Explainer",
        "version": "0.2.0",
        "description": "Analyze GitHub repositories and generate architecture documentation with Q&A",
        "endpoints": {
            "POST /api/analyze": "Analyze a GitHub repository",
            "GET /api/diagrams/{repo_name}": "Retrieve architecture diagram for a repository",
            "POST /api/query": "Ask questions about repository architecture",
            "GET /api/health": "Health check",
            "GET /api/info": "Service information",
        }
    }
