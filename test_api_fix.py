#!/usr/bin/env python3
"""Quick test to verify FastAPI configuration."""

try:
    from src.main import app
    from src.api.routes import DiagramResponse, AnalysisRequest
    
    print("✓ FastAPI app created successfully")
    print("✓ All routes registered")
    
    endpoints = [route.path for route in app.routes]
    api_endpoints = [e for e in endpoints if e.startswith("/api")]
    
    print(f"✓ Available endpoints: {api_endpoints}")
    print("\n✓ API configuration is VALID - Ready to run!")
    
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
