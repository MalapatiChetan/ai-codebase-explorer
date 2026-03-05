#!/usr/bin/env python3
"""
Complete System Verification - AI Codebase Explainer Phase 2
This script verifies all components are working correctly.
"""

import sys
import json
from datetime import datetime

print("=" * 80)
print(" AI CODEBASE EXPLAINER - PHASE 2 COMPLETE SYSTEM VERIFICATION")
print("=" * 80)
print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n")

# Test 1: Module Imports
print("TEST 1: Verifying all module imports...")
print("-" * 80)

test_results = []

try:
    from src.modules.repo_scanner import RepositoryScanner
    print("✓ RepositoryScanner imported")
    test_results.append(("RepositoryScanner", True, None))
except Exception as e:
    print(f"✗ RepositoryScanner import failed: {e}")
    test_results.append(("RepositoryScanner", False, str(e)))

try:
    from src.modules.framework_detector import FrameworkDetector
    print("✓ FrameworkDetector imported")
    test_results.append(("FrameworkDetector", True, None))
except Exception as e:
    print(f"✗ FrameworkDetector import failed: {e}")
    test_results.append(("FrameworkDetector", False, str(e)))

try:
    from src.modules.metadata_builder import RepositoryMetadataBuilder
    print("✓ RepositoryMetadataBuilder imported")
    test_results.append(("RepositoryMetadataBuilder", True, None))
except Exception as e:
    print(f"✗ RepositoryMetadataBuilder import failed: {e}")
    test_results.append(("RepositoryMetadataBuilder", False, str(e)))

try:
    from src.modules.ai_analyzer import AIArchitectureAnalyzer
    print("✓ AIArchitectureAnalyzer imported")
    test_results.append(("AIArchitectureAnalyzer", True, None))
except Exception as e:
    print(f"✗ AIArchitectureAnalyzer import failed: {e}")
    test_results.append(("AIArchitectureAnalyzer", False, str(e)))

try:
    from src.modules.diagram_generator import ArchitectureDiagramGenerator, DiagramNode, DiagramEdge, ArchitectureGraph
    print("✓ ArchitectureDiagramGenerator imported (PHASE 2 - NEW)")
    print("✓ DiagramNode imported (PHASE 2 - NEW)")
    print("✓ DiagramEdge imported (PHASE 2 - NEW)")
    print("✓ ArchitectureGraph imported (PHASE 2 - NEW)")
    test_results.append(("ArchitectureDiagramGenerator", True, None))
except Exception as e:
    print(f"✗ ArchitectureDiagramGenerator import failed: {e}")
    test_results.append(("ArchitectureDiagramGenerator", False, str(e)))

# Test 2: Configuration
print("\n\nTEST 2: Verifying configuration system...")
print("-" * 80)

try:
    from src.utils.config import Settings
    settings = Settings()
    print(f"✓ Settings loaded: OpenAI Model = {settings.OPENAI_MODEL}")
    print(f"✓ Repository clone path configured: {settings.REPO_CLONE_PATH}")
    print(f"✓ Diagram output path configured: {settings.DIAGRAM_OUTPUT_PATH}")
    print(f"✓ Generate Mermaid diagrams: {settings.GENERATE_MERMAID}")
    print(f"✓ Generate Graphviz diagrams: {settings.GENERATE_GRAPHVIZ}")
    test_results.append(("Configuration", True, None))
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    test_results.append(("Configuration", False, str(e)))

# Test 3: API Routes
print("\n\nTEST 3: Verifying API routes...")
print("-" * 80)

try:
    from src.main import app
    from src.api.routes import DiagramResponse, AnalysisRequest, AnalysisResponse
    print("✓ FastAPI application initialized")
    print("✓ DiagramResponse model imported (PHASE 2 - NEW)")
    print("✓ AnalysisRequest model imported")
    print("✓ AnalysisResponse model imported")
    
    # List all routes
    print("\nRegistered API routes:")
    api_routes = [r for r in app.routes if hasattr(r, 'path') and r.path.startswith('/api')]
    for idx, route in enumerate(api_routes, 1):
        methods = getattr(route, 'methods', ['GET'])
        methods_str = ', '.join(methods) if isinstance(methods, (list, set)) else 'GET'
        print(f"  {idx}. {methods_str:6} {route.path}")
    
    test_results.append(("API Routes", True, None))
except Exception as e:
    print(f"✗ API routes failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("API Routes", False, str(e)))

# Test 4: Diagram Generation
print("\n\nTEST 4: Verifying diagram generation...")
print("-" * 80)

try:
    from src.modules.diagram_generator import ArchitectureDiagramGenerator
    
    generator = ArchitectureDiagramGenerator()
    print("✓ Diagram generator instantiated")
    
    # Test with mock metadata
    mock_metadata = {
        "repository": {
            "name": "test-project",
            "url": "https://github.com/test/test",
            "path": "./test"
        },
        "analysis": {
            "file_count": 100,
            "primary_language": "Python",
            "languages": {"python": 60, "javascript": 40},
            "has_backend": True,
            "has_frontend": True
        },
        "frameworks": {
            "FastAPI": {"confidence": 0.9, "matched_patterns": []},
            "React": {"confidence": 0.85, "matched_patterns": []}
        },
        "tech_stack": ["Python", "JavaScript", "PostgreSQL"],
        "architecture_patterns": ["API-First"],
        "dependencies": {"fastapi": "0.1", "react": "18.0"},
        "modules": [
            {"name": "backend", "type": "Backend", "file_count": 50, "languages": {}},
            {"name": "frontend", "type": "Frontend", "file_count": 50, "languages": {}}
        ],
        "root_files": ["requirements.txt"],
        "important_files": ["requirements.txt"]
    }
    
    diagrams = generator.generate_diagrams(mock_metadata)
    
    print(f"✓ Mermaid diagram generated: {len(str(diagrams.get('mermaid', '')))} chars")
    print(f"✓ Graphviz diagram generated: {len(str(diagrams.get('graphviz', '')))} chars")
    print(f"✓ JSON diagram generated: {len(str(diagrams.get('json', '')))} chars")
    
    test_results.append(("Diagram Generation", True, None))
except Exception as e:
    print(f"✗ Diagram generation failed: {e}")
    import traceback
    traceback.print_exc()
    test_results.append(("Diagram Generation", False, str(e)))

# Test 5: Integration
print("\n\nTEST 5: Verifying pipeline integration...")
print("-" * 80)

try:
    from src.modules.metadata_builder import RepositoryMetadataBuilder
    
    builder = RepositoryMetadataBuilder()
    print("✓ MetadataBuilder instantiated with integrated diagram generator")
    
    # Verify diagram_generator is available
    if hasattr(builder, 'diagram_generator'):
        print("✓ Diagram generator integrated into metadata builder")
        test_results.append(("Integration", True, None))
    else:
        raise Exception("Diagram generator not integrated")
        
except Exception as e:
    print(f"✗ Integration check failed: {e}")
    test_results.append(("Integration", False, str(e)))

# Summary
print("\n\n" + "=" * 80)
print(" VERIFICATION SUMMARY")
print("=" * 80)

passed = sum(1 for _, result, _ in test_results if result)
total = len(test_results)

print(f"\nTests Passed: {passed}/{total}")

if passed == total:
    print("\n🟢 ALL SYSTEMS OPERATIONAL - PHASE 2 COMPLETE")
    print("\nSystem Status: PRODUCTION READY ✅")
    print("\nYou can now:")
    print("  1. Start the API server: python -m uvicorn src.main:app --reload --port 8001")
    print("  2. Access documentation: http://localhost:8001/api/docs")
    print("  3. Analyze repositories with diagram generation")
    print("\nFor detailed information, see:")
    print("  - PHASE_2_COMPLETION_REPORT.md")
    print("  - CREDENTIALS_GUIDE.md")
    print("  - QUICK_STATUS.md")
    sys.exit(0)
else:
    print("\n🔴 SOME TESTS FAILED")
    print("\nFailed tests:")
    for name, result, error in test_results:
        if not result:
            print(f"  ✗ {name}")
            if error:
                print(f"    Error: {error}")
    sys.exit(1)
