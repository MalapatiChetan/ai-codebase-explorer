"""API routes for the codebase explainer."""

import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path as PathParam
from src.modules.metadata_builder import RepositoryMetadataBuilder
from src.modules.ai_analyzer import AIArchitectureAnalyzer
from src.modules.diagram_generator import ArchitectureDiagramGenerator
from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
from src.modules.github_insights import GitHubInsightsService, GitHubInsightsError
from src.utils.repository_registry import get_repository_registry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

# Initialize shared registry
registry = get_repository_registry()

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


class ConversationMessage(BaseModel):
    """Conversation history item passed from the frontend chat."""
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")


class QueryRequest(BaseModel):
    """Request model for architecture Q&A."""
    repository_name: str = Field(..., description="Name of the analyzed repository")
    question: str = Field(..., description="Question about repository architecture")
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list,
        description="Prior chat messages for conversational context",
    )


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


class InsightsResponse(BaseModel):
    """Response model for GitHub repository insights."""
    status: str = Field(..., description="Status of the request")
    repository_name: str = Field(..., description="Repository name")
    insights: Optional[dict] = Field(None, description="GitHub repository insight payload")
    note: Optional[str] = Field(None, description="Additional note about partial or pending data")


class ExplorerResponse(BaseModel):
    """Response model for GitHub user repository explorer."""
    status: str = Field(..., description="Status of the request")
    username: str = Field(..., description="GitHub username")
    repositories: List[dict] = Field(default_factory=list, description="Public repositories for the user")


class UserOverviewResponse(BaseModel):
    """Response model for GitHub user overview."""
    status: str = Field(..., description="Status of the request")
    username: str = Field(..., description="GitHub username")
    overview: dict = Field(..., description="GitHub user overview payload")


class GitHubRepositoryInsightsResponse(BaseModel):
    """Response model for GitHub explorer repository insights."""
    status: str = Field(..., description="Status of the request")
    owner: str = Field(..., description="Repository owner")
    repository_name: str = Field(..., description="Repository name")
    insights: dict = Field(..., description="GitHub repository insights payload")
    note: Optional[str] = Field(None, description="Additional note about partial or pending data")


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
        repo_name = metadata["repository"]["name"]
        logger.info(f"✓ Metadata built for repository: {repo_name}")
        
        response_data = {
            "status": "success",
            "repository_name": repo_name,
            "message": "Repository analysis completed",
            "metadata": metadata
        }
        
        # Generate AI analysis if requested
        if request.include_ai_analysis:
            logger.info("Generating AI analysis...")
            ai_analyzer = AIArchitectureAnalyzer()
            analysis = ai_analyzer.analyze(metadata)
            response_data["analysis"] = analysis
        
        # Prepare diagrams for response (keep in metadata for persistence)
        if request.include_diagrams and "diagrams" in metadata:
            response_data["diagrams"] = metadata["diagrams"]
        
        # Save repository to registry BEFORE returning (ensures persistence before response)
        logger.info(f"Saving metadata to registry for {repo_name}...")
        registry.register(repo_name, metadata)
        logger.info(f"✓ Repository {repo_name} registered and saved to cache")
        
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
        repo_name = request.repository_name
        logger.info(f"Received query for {repo_name}: {request.question}")
        
        # Validate question
        if not request.question.strip():
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty"
            )
        
        # Check if repository has been analyzed
        logger.debug(f"Checking if repository {repo_name} exists in registry...")
        if not registry.exists(repo_name):
            available_repos = registry.list_repositories()
            logger.error(f"Repository '{repo_name}' not found in registry. Available: {available_repos}")
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{repo_name}' has not been analyzed. Please analyze it first using POST /api/analyze. Available repositories: {', '.join(available_repos) if available_repos else 'None'}"
            )
        
        # Get repository metadata
        logger.debug(f"Retrieving metadata for {repo_name}...")
        metadata = registry.get(repo_name)
        if not metadata:
            logger.error(f"Metadata for '{repo_name}' exists in registry but could not be retrieved")
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve metadata for '{repo_name}'. Repository may be partially analyzed."
            )
        
        logger.info(f"✓ Metadata retrieved successfully for {repo_name}")
        
        # Generate answer
        logger.info("Generating architectural answer...")
        answerer = ArchitectureQueryAnswerer()
        history = [
            {"role": message.role, "content": message.content}
            for message in request.conversation_history
            if message.content.strip()
        ]
        result = answerer.answer_question(metadata, request.question, history)
        
        logger.info(f"✓ Query processed successfully (Mode: {result.get('ai_mode', 'Unknown')})")
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


@router.get("/insights/{repo_name}", response_model=InsightsResponse)
async def get_repository_insights(repo_name: str = PathParam(..., description="Repository name")):
    """Fetch GitHub repository insights for an analyzed repository."""
    try:
        if not registry.exists(repo_name):
            raise HTTPException(
                status_code=404,
                detail=f"Repository '{repo_name}' has not been analyzed. Please analyze it first.",
            )

        metadata = registry.get(repo_name)
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve metadata for '{repo_name}'.",
            )

        repo_url = metadata.get("repository", {}).get("url")
        if not repo_url:
            raise HTTPException(
                status_code=400,
                detail=f"Repository URL is missing for '{repo_name}'.",
            )

        service = GitHubInsightsService()
        insights = service.get_repository_insights(repo_url)
        note = None
        if insights.get("commit_activity", {}).get("pending") or insights.get("code_frequency", {}).get("pending"):
            note = "Some GitHub statistics are still being computed by GitHub and may appear later."

        return InsightsResponse(
            status="success",
            repository_name=repo_name,
            insights=insights,
            note=note,
        )
    except HTTPException:
        raise
    except GitHubInsightsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error during insights request: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Insights failed: {exc}")


@router.get("/github/users/{username}/repos", response_model=ExplorerResponse)
async def get_user_repositories(username: str = PathParam(..., description="GitHub username")):
    """Fetch public repositories for a GitHub user."""
    try:
        service = GitHubInsightsService()
        repositories = service.list_user_repositories(username)
        return ExplorerResponse(
            status="success",
            username=username,
            repositories=repositories,
        )
    except GitHubInsightsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error during GitHub explorer request: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"GitHub explorer failed: {exc}")


@router.get("/github/users/{username}/overview", response_model=UserOverviewResponse)
async def get_user_overview(username: str = PathParam(..., description="GitHub username")):
    """Fetch GitHub profile and aggregated repository overview for a user."""
    try:
        service = GitHubInsightsService()
        overview = service.get_user_overview(username)
        return UserOverviewResponse(
            status="success",
            username=username,
            overview=overview,
        )
    except GitHubInsightsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error during GitHub user overview request: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"GitHub user overview failed: {exc}")


@router.get("/github/repos/{owner}/{repo}/insights", response_model=GitHubRepositoryInsightsResponse)
async def get_github_repository_insights(
    owner: str = PathParam(..., description="Repository owner"),
    repo: str = PathParam(..., description="Repository name"),
    username: Optional[str] = Query(default=None, description="Explored GitHub username for contribution context"),
):
    """Fetch GitHub repository insights directly from GitHub without analysis/indexing."""
    try:
        service = GitHubInsightsService()
        insights = service.get_repository_insights_by_name(owner, repo, username)
        note = None
        if insights.get("commit_activity", {}).get("pending") or insights.get("code_frequency", {}).get("pending"):
            note = "Some GitHub statistics are still being computed by GitHub and may appear later."

        return GitHubRepositoryInsightsResponse(
            status="success",
            owner=owner,
            repository_name=repo,
            insights=insights,
            note=note,
        )
    except GitHubInsightsError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error during GitHub repository insights request: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"GitHub repository insights failed: {exc}")

@router.get("/repositories")
async def list_repositories():
    """
    List all registered/cached repositories.
    
    Returns:
        A list of repository names that have been analyzed and are available
    """
    try:
        repos = registry.list_repositories()
        return {
            "status": "success",
            "count": len(repos),
            "repositories": repos
        }
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list repositories: {str(e)}")

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
            "GET /api/insights/{repo_name}": "Retrieve GitHub insights for an analyzed repository",
            "GET /api/github/users/{username}/repos": "List public repositories for a GitHub user",
            "GET /api/repositories": "List all analyzed/cached repositories",
            "GET /api/health": "Health check",
            "GET /api/info": "Service information",
        }
    }
