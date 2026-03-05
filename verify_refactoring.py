#!/usr/bin/env python3
"""
Final verification of the Mermaid diagram refactoring.
Tests all main components are working correctly.
"""

import sys
import tempfile
from pathlib import Path

def verify_imports():
    """Verify all modules can be imported."""
    try:
        from src.modules.diagram_generator import (
            ArchitectureDiagramGenerator,
            sanitize_node_id,
            validate_mermaid_diagram,
        )
        from src.api.routes import DiagramResponse
        from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
        print("PASS: All required modules imported successfully")
        return True
    except ImportError as e:
        print(f"FAIL: Import error - {e}")
        return False


def verify_diagram_generation():
    """Verify basic diagram generation works."""
    try:
        from src.modules.diagram_generator import ArchitectureDiagramGenerator
        
        mock_metadata = {
            'repository': {'name': 'test-repo', 'url': 'https://github.com/test/repo'},
            'analysis': {'has_frontend': True, 'has_backend': True, 'has_docker': False},
            'frameworks': {'React': {'confidence': 0.95}, 'FastAPI': {'confidence': 0.90}},
            'modules': [{'name': 'API', 'type': 'Backend Module', 'file_count': 10}],
            'dependencies': {'sqlalchemy': '1.4'},
        }
        
        generator = ArchitectureDiagramGenerator()
        diagrams = generator.generate_diagrams(mock_metadata)
        
        if not diagrams.get('mermaid'):
            print("FAIL: No Mermaid diagram generated")
            return False
        
        mermaid_code = diagrams['mermaid']
        
        # Verify key components
        checks = [
            ("Has graph declaration", "graph TD" in mermaid_code),
            ("Has node definitions", "[" in mermaid_code),
            ("Has connections", "-->" in mermaid_code),
            ("Has style definitions", "classDef" in mermaid_code),
            ("Has class assignments", "class " in mermaid_code),
        ]
        
        all_passed = True
        for check_name, result in checks:
            status = "PASS" if result else "FAIL"
            print(f"  {status}: {check_name}")
            all_passed = all_passed and result
        
        if all_passed:
            print("PASS: Diagram generation verified")
        else:
            print("FAIL: Diagram generation has issues")
        
        return all_passed
    
    except Exception as e:
        print(f"FAIL: Diagram generation error - {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_node_sanitization():
    """Verify node ID sanitization works correctly."""
    try:
        from src.modules.diagram_generator import sanitize_node_id
        
        test_cases = [
            ("FastAPI Backend", "FastAPI_Backend", True),
            ("Next.js Frontend", "Nextjs_Frontend", True),
            ("PostgreSQL Database", "PostgreSQL_Database", True),
            ("Normal Name", "Normal_Name", True),
        ]
        
        all_passed = True
        for label, expected, should_pass in test_cases:
            result = sanitize_node_id(label)
            passed = result == expected
            if should_pass and not passed:
                print(f"  FAIL: sanitize_node_id('{label}') = '{result}' (expected '{expected}')")
                all_passed = False
        
        if all_passed:
            print("PASS: Node ID sanitization verified")
        else:
            print("FAIL: Node ID sanitization has issues")
        
        return all_passed
    
    except Exception as e:
        print(f"FAIL: Sanitization error - {e}")
        return False


def verify_validation():
    """Verify diagram validation works."""
    try:
        from src.modules.diagram_generator import validate_mermaid_diagram
        
        valid_diagram = """graph TD
    a[Node A]
    b[Node B]
    a --> b
    classDef default fill:white
    class a default"""
        
        is_valid, errors = validate_mermaid_diagram(valid_diagram)
        
        if is_valid:
            print("PASS: Diagram validation verified")
            return True
        else:
            print(f"FAIL: Valid diagram failed validation - {errors}")
            return False
    
    except Exception as e:
        print(f"FAIL: Validation error - {e}")
        return False


def main():
    """Run all verifications."""
    print("=" * 70)
    print("MERMAID REFACTORING - FINAL VERIFICATION")
    print("=" * 70)
    print()
    
    tests = [
        ("Module Imports", verify_imports),
        ("Node Sanitization", verify_node_sanitization),
        ("Diagram Validation", verify_validation),
        ("Diagram Generation", verify_diagram_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n[Testing: {test_name}]")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL: {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} verifications passed")
    print("=" * 70)
    
    if passed == total:
        print("\nSUCCESS: Mermaid diagram refactoring is complete and validated!")
        return 0
    else:
        print(f"\nFAILURE: {total - passed} verification(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
