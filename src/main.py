"""Main FastAPI application for AI Codebase Explainer."""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.utils.config import settings
from src.api import routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="A system for analyzing GitHub repositories and generating architecture documentation",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler - initialize application."""
    try:
        logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
        
        # Log configuration
        model_name = settings.GOOGLE_MODEL or "not configured"
        logger.info(f"AI Model: {model_name}")
        logger.info(f"AI Enabled: {settings.is_ai_usable()}")
        logger.info(f"Repository clone path: {settings.REPO_CLONE_PATH}")
        logger.info(f"Diagram output path: {settings.DIAGRAM_OUTPUT_PATH}")
        logger.info(f"RAG enabled: {settings.ENABLE_RAG}")
        
        # Ensure required directories exist (cloud-safe)
        # Use /tmp for cloud platforms, ./data for local development
        paths_to_create = [
            settings.REPO_CLONE_PATH,
            settings.DIAGRAM_OUTPUT_PATH,
            settings.RAG_INDEX_PATH,
        ]
        
        for path_str in paths_to_create:
            if not path_str:
                continue
            try:
                path = Path(path_str)
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✓ Directory ready: {path}")
            except PermissionError:
                logger.warning(f"⚠ Permission denied creating {path_str} - using as-is")
            except Exception as e:
                logger.warning(f"⚠ Could not create {path_str}: {e}")
        
        # Validate AI configuration if enabled
        if settings.ENABLE_AI_CHAT:
            if not settings.is_ai_usable():
                reason = settings.get_ai_disabled_reason()
                logger.warning(f"⚠ AI unavailable: {reason}")
            else:
                logger.info("✓ AI (Gemini) is ready")
        
        logger.info("✓ Application startup COMPLETE - Server ready for requests")
    except Exception as e:
        logger.error(f"✗ FATAL ERROR during startup: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info(f"Shutting down {settings.API_TITLE}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AI Codebase Explainer",
        "version": settings.API_VERSION,
        "docs": "/api/docs",
        "health": "/api/health",
        "info": "/api/info"
    }


def custom_openapi():
    """Customize OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="AI-powered repository analysis and architecture documentation system",
        routes=app.routes,
    )
    
    openapi_schema["info"]["x-logo"] = {
        "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting AI Codebase Explainer API...")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
