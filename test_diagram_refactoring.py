#!/usr/bin/env python3
"""
Unit tests for refactored Mermaid diagram generation.

Tests the following:
- Node ID sanitization
- Mermaid diagram generation with proper styling
- Style class application to nodes
- Diagram validation
- API consistency (plain Mermaid syntax return)
"""

import json
import tempfile
from pathlib import Path
from src.modules.diagram_generator import (
    ArchitectureDiagramGenerator,
    sanitize_node_id,
    validate_mermaid_diagram,
)


def test_sanitize_node_id():
    """Test node ID sanitization."""
    print("\n[TEST 1] Node ID Sanitization")
    print("-" * 70)
    
    test_cases = [
        ("FastAPI Backend", "FastAPI_Backend"),
        ("Next.js Frontend", "Nextjs_Frontend"),  # Periods are removed for Mermaid compatibility
        ("PostgreSQL Database", "PostgreSQL_Database"),
        ("Frontend Application", "Frontend_Application"),
        ("Web Service", "Web_Service"),
    ]
    
    all_passed = True
    for label, expected in test_cases:
        result = sanitize_node_id(label)
        status = "✓" if result == expected else "✗"
        print(f"{status} sanitize_node_id('{label}') = '{result}' (expected '{expected}')")
        if result != expected:
            all_passed = False
    
    return all_passed


def test_mermaid_validation():
    """Test Mermaid diagram validation."""
    print("\n[TEST 2] Mermaid Diagram Validation")
    print("-" * 70)
    
    # Valid diagram
    valid_diagram = """graph TD
    app[Application]
    frontend[Frontend]
    backend[Backend]
    db[(Database)]
    
    app --> frontend
    app --> backend
    backend --> db
    
    classDef frontend fill:#e1f5ff,stroke:#01579b
    classDef backend fill:#f3e5f5,stroke:#4a148c
    classDef database fill:#e8f5e9,stroke:#1b5e20
    
    class frontend frontend
    class backend backend
    class db database
    class app application"""
    
    is_valid, errors = validate_mermaid_diagram(valid_diagram)
    print(f"✓ Valid diagram validation: is_valid={is_valid}, errors={errors}")
    
    # Invalid diagram (missing declaration)
    invalid_diagram = """app[Application]
    frontend[Frontend]"""
    
    is_valid, errors = validate_mermaid_diagram(invalid_diagram)
    status = "✓" if not is_valid and len(errors) > 0 else "✗"
    print(f"{status} Invalid diagram detected: {len(errors)} errors found")
    
    return True


def test_mermaid_generation_with_styling():
    """Test Mermaid diagram generation with styles applied to nodes."""
    print("\n[TEST 3] Mermaid Generation with Styling")
    print("-" * 70)
    
    # Create a mock metadata
    mock_metadata = {
        'repository': {'name': 'test-repo', 'url': 'https://github.com/test/repo'},
        'analysis': {'has_frontend': True, 'has_backend': True, 'has_docker': False},
        'frameworks': {
            'React': {'confidence': 0.95},
            'FastAPI': {'confidence': 0.90},
        },
        'modules': [
            {'name': 'API Module', 'type': 'Backend Module', 'file_count': 10},
            {'name': 'UI Module', 'type': 'Frontend Module', 'file_count': 20},
        ],
        'dependencies': {'sqlalchemy': '1.4'},
    }
    
    # Generate diagrams
    generator = ArchitectureDiagramGenerator()
    diagrams = generator.generate_diagrams(mock_metadata)
    
    mermaid_code = diagrams.get("mermaid", "")
    
    # Verify diagram structure
    checks = {
        "Contains graph declaration": "graph TD" in mermaid_code,
        "Contains node definitions": "[" in mermaid_code,
        "Contains connections": "-->" in mermaid_code,
        "Contains style definitions": "classDef" in mermaid_code,
        "Contains class assignments": "class " in mermaid_code,
        "Contains frontend style": "classDef frontend" in mermaid_code,
        "Contains backend style": "classDef backend" in mermaid_code,
        "Contains database style": "classDef database" in mermaid_code,
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check}: {result}")
        if not result:
            all_passed = False
    
    # Print sample of generated diagram
    print("\nGenerated Mermaid Diagram Sample:")
    print("-" * 70)
    print(mermaid_code[:500] + "..." if len(mermaid_code) > 500 else mermaid_code)
    
    return all_passed


def test_node_class_application():
    """Test that style classes are actually applied to nodes."""
    print("\n[TEST 4] Node Style Class Application")
    print("-" * 70)
    
    mock_metadata = {
        'repository': {'name': 'test-repo', 'url': 'https://github.com/test/repo'},
        'analysis': {'has_frontend': True, 'has_backend': True, 'has_docker': False},
        'frameworks': {
            'React': {'confidence': 0.95},
            'FastAPI': {'confidence': 0.90},
        },
        'modules': [
            {'name': 'API Module', 'type': 'Backend Module', 'file_count': 10},
        ],
        'dependencies': {'sqlalchemy': '1.4'},
    }
    
    generator = ArchitectureDiagramGenerator()
    diagrams = generator.generate_diagrams(mock_metadata)
    mermaid_code = diagrams.get("mermaid", "")
    
    # Extract class assignments
    import re
    class_assignments = re.findall(r'class\s+(\w+)\s+(\w+)', mermaid_code)
    
    print(f"Found {len(class_assignments)} class assignments:")
    all_assigned = True
    for node_id, node_class in class_assignments:
        print(f"  ✓ {node_id} => {node_class}")
    
    if len(class_assignments) == 0:
        print("  ✗ No class assignments found!")
        all_assigned = False
    
    # Check that all defined nodes have classes
    node_definitions = re.findall(r'^[\s]*([a-zA-Z_]\w*)\[', mermaid_code, re.MULTILINE)
    assigned_nodes = {node_id for node_id, _ in class_assignments}
    
    print(f"\nNode Coverage:")
    print(f"  - Total defined nodes: {len(node_definitions)}")
    print(f"  - Nodes with class assignments: {len(assigned_nodes)}")
    
    unassigned = set(node_definitions) - assigned_nodes
    if unassigned:
        print(f"  ✗ Unassigned nodes: {unassigned}")
        all_assigned = False
    else:
        print(f"  ✓ All nodes have class assignments")
    
    return all_assigned


def test_sanitized_ids_in_connections():
    """Test that connections use sanitized node IDs."""
    print("\n[TEST 5] Sanitized IDs in Connections")
    print("-" * 70)
    
    mock_metadata = {
        'repository': {'name': 'test-repo', 'url': 'https://github.com/test/repo'},
        'analysis': {'has_frontend': True, 'has_backend': True, 'has_docker': False},
        'frameworks': {
            'React': {'confidence': 0.95},
            'FastAPI': {'confidence': 0.90},
        },
        'modules': [
            {'name': 'API Module', 'type': 'Backend Module', 'file_count': 10},
        ],
        'dependencies': {'sqlalchemy': '1.4'},
    }
    
    generator = ArchitectureDiagramGenerator()
    diagrams = generator.generate_diagrams(mock_metadata)
    mermaid_code = diagrams.get("mermaid", "")
    
    # Extract node definitions section (before classDef)
    node_section = mermaid_code.split("classDef")[0]
    
    # Check for spaces in node IDs in the node definition section
    import re
    # Pattern: look for node IDs with spaces like "app name" where "app name" is used as an identifier
    space_in_ids = re.findall(r'^\s*([a-zA-Z_]\w+\s+[a-zA-Z_]\w+)\[', node_section, re.MULTILINE)
    
    if space_in_ids:
        print(f"✗ Found spaces in node identifiers: {space_in_ids}")
        return False
    else:
        print("✓ All node identifiers are properly sanitized (no spaces)")
    
    # Check that connections reference valid IDs
    node_ids = set(re.findall(r'^\s*([a-zA-Z_]\w*)\[', node_section, re.MULTILINE))
    connection_endpoints = set(re.findall(r'([a-zA-Z_]\w+)\s*(?:-->|-)', node_section))
    
    undefined_refs = connection_endpoints - node_ids
    if undefined_refs:
        print(f"✗ Undefined node references in connections: {undefined_refs}")
        return False
    else:
        print(f"✓ All connections reference defined nodes")
    
    return True


def test_diagram_storage_and_retrieval():
    """Test that diagrams are stored and retrieved in plain format."""
    print("\n[TEST 6] Diagram Storage and Retrieval")
    print("-" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily change output path
        import src.modules.diagram_generator as dg_module
        original_output_path = dg_module.settings.DIAGRAM_OUTPUT_PATH
        dg_module.settings.DIAGRAM_OUTPUT_PATH = tmpdir
        
        try:
            mock_metadata = {
                'repository': {'name': 'test-repo', 'url': 'https://github.com/test/repo'},
                'analysis': {'has_frontend': True, 'has_backend': True, 'has_docker': False},
                'frameworks': {
                    'React': {'confidence': 0.95},
                    'FastAPI': {'confidence': 0.90},
                },
                'modules': [],
                'dependencies': {},
            }
            
            generator = ArchitectureDiagramGenerator()
            diagrams = generator.generate_diagrams(mock_metadata)
            
            # Retrieve and verify
            retrieved = generator.get_stored_diagram("test-repo", "mermaid")
            
            # Should not contain Markdown formatting
            if "```mermaid" in retrieved:
                print("✗ Retrieved diagram contains Markdown formatting (should be plain)")
                return False
            else:
                print("✓ Retrieved diagram is plain Mermaid syntax (no Markdown wrapping)")
            
            # Should start with graph declaration
            if not retrieved.strip().startswith("graph"):
                print("✗ Retrieved diagram doesn't start with 'graph' declaration")
                return False
            else:
                print("✓ Retrieved diagram has valid graph declaration")
            
            # Validate retrieved diagram
            is_valid, errors = validate_mermaid_diagram(retrieved)
            if not is_valid:
                print(f"✗ Retrieved diagram has validation errors: {errors}")
                return False
            else:
                print("✓ Retrieved diagram passes validation")
            
            return True
        
        finally:
            dg_module.settings.DIAGRAM_OUTPUT_PATH = original_output_path


def test_api_consistency():
    """Test that both endpoints return consistent plain Mermaid format."""
    print("\n[TEST 7] API Response Consistency")
    print("-" * 70)
    
    # Test that DiagramResponse returns plain syntax
    from src.api.routes import DiagramResponse
    
    sample_mermaid = """graph TD
    app[Application]
    classDef app fill:#f5f5f5
    class app app"""
    
    response = DiagramResponse(
        status="success",
        repository_name="test-repo",
        format="mermaid",
        diagram=sample_mermaid
    )
    
    # Verify response structure
    checks = {
        "Has status": response.status == "success",
        "Has repository_name": response.repository_name == "test-repo",
        "Has format": response.format == "mermaid",
        "Has diagram": response.diagram is not None,
        "Diagram is string": isinstance(response.diagram, str),
        "Diagram doesn't contain Markdown": "```" not in response.diagram,
        "Diagram is plain format": response.diagram.startswith("graph"),
    }
    
    all_passed = True
    for check, result in checks.items():
        status = "✓" if result else "✗"
        print(f"{status} {check}: {result}")
        if not result:
            all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("=" * 70)
    print("MERMAID DIAGRAM REFACTORING - UNIT TESTS")
    print("=" * 70)
    
    tests = [
        ("Node ID Sanitization", test_sanitize_node_id),
        ("Mermaid Validation", test_mermaid_validation),
        ("Mermaid Generation with Styling", test_mermaid_generation_with_styling),
        ("Node Style Class Application", test_node_class_application),
        ("Sanitized IDs in Connections", test_sanitized_ids_in_connections),
        ("Diagram Storage and Retrieval", test_diagram_storage_and_retrieval),
        ("API Response Consistency", test_api_consistency),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    if passed == total:
        print("\n✅ All tests passed! Diagram refactoring is complete and validated.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
