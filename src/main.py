"""Main FastAPI application for AI Codebase Explainer."""

import logging
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
    """Startup event handler."""
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    model_name = getattr(settings, "GOOGLE_MODEL", None) or getattr(settings, "OPENAI_MODEL", "not configured")
    logger.info(f"AI Model: {model_name}")
    logger.info(f"Repository clone path: {settings.REPO_CLONE_PATH}")


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
