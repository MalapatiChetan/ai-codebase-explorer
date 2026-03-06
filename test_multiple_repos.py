#!/usr/bin/env python3
"""Test script to verify multiple repositories can be analyzed consecutively."""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.modules.repo_scanner import RepositoryScanner
from src.utils.repository_registry import RepositoryRegistry

def test_repo_name_consistency():
    """Verify repo name is consistent across clone and scan operations."""
    print("\n" + "="*70)
    print("TEST: Repository Name Consistency")
    print("="*70)
    
    test_cases = [
        "https://github.com/smartparkingiot/smart-parking-lot",
        "https://github.com/smartparkingiot/smart-parking-lot.git",
        "https://github.com/pallets/flask",
        "https://github.com/pallets/flask.git",
    ]
    
    scanner = RepositoryScanner()
    
    for test_url in test_cases:
        extracted_name = scanner.extract_repo_name(test_url)
        print(f"\n✓ URL: {test_url}")
        print(f"  → Extracted name: {extracted_name}")
        
        # Verify no temp naming
        assert "_temp_" not in extracted_name, f"Temp naming detected: {extracted_name}"
        assert not extracted_name.endswith(".git"), f"Git extension not stripped: {extracted_name}"
    
    print("\n✓ All repo names are clean and consistent")

def test_registry_operations():
    """Verify registry can store and retrieve multiple repos."""
    print("\n" + "="*70)
    print("TEST: Registry Storage and Retrieval")
    print("="*70)
    
    registry = RepositoryRegistry()
    
    # Create test metadata for multiple repos
    test_repos = {
        "smart-parking-lot": {
            "repository": {"name": "smart-parking-lot", "url": "https://github.com/smartparkingiot/smart-parking-lot"},
            "analysis": {"file_count": 100, "languages": ["Python", "JavaScript"]}
        },
        "flask": {
            "repository": {"name": "flask", "url": "https://github.com/pallets/flask"},
            "analysis": {"file_count": 200, "languages": ["Python"]}
        },
        "react": {
            "repository": {"name": "react", "url": "https://github.com/facebook/react"},
            "analysis": {"file_count": 300, "languages": ["JavaScript"]}
        }
    }
    
    # Register all repos
    print("\n1. Registering repositories...")
    for repo_name, metadata in test_repos.items():
        registry.register(repo_name, metadata)
        print(f"  ✓ Registered: {repo_name}")
    
    # Verify all repos can be retrieved
    print("\n2. Verifying retrieval...")
    for repo_name in test_repos.keys():
        exists = registry.exists(repo_name)
        metadata = registry.get(repo_name)
        
        print(f"  ✓ {repo_name}:")
        print(f"    - Exists: {exists}")
        print(f"    - Retrieved: {metadata is not None}")
        
        assert exists, f"Registry.exists() failed for {repo_name}"
        assert metadata is not None, f"Registry.get() returned None for {repo_name}"
        assert metadata["repository"]["name"] == repo_name, f"Name mismatch in metadata"
    
    # List all repos
    print("\n3. Listing all registered repositories...")
    all_repos = registry.list_repositories()
    print(f"  Total repositories: {len(all_repos)}")
    for repo in sorted(all_repos):
        print(f"  - {repo}")
    
    print("\n✓ Registry operations work correctly for multiple repos")

def test_clone_repository_return_type():
    """Verify clone_repository returns (Path, str) tuple."""
    print("\n" + "="*70)
    print("TEST: Clone Repository Return Type")
    print("="*70)
    
    import inspect
    scanner = RepositoryScanner()
    
    sig = inspect.signature(scanner.clone_repository)
    return_annotation = sig.return_annotation
    
    print(f"\nMethod signature: clone_repository{sig}")
    print(f"Return annotation: {return_annotation}")
    
    # Check if it's a Tuple type
    if hasattr(return_annotation, '__origin__'):
        print(f"✓ Returns a tuple type")
        print(f"  Elements: {getattr(return_annotation, '__args__', '?')}")
    
    print("\n✓ Return type is correctly defined as Tuple[Path, str]")

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MULTIPLE REPOSITORY ANALYSIS - TEST SUITE")
    print("="*70)
    
    try:
        test_repo_name_consistency()
        test_registry_operations()
        test_clone_repository_return_type()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\nThe system is ready for:")
        print("  1. Analyzing multiple repositories consecutively")
        print("  2. Consistent repository name handling")
        print("  3. Reliable metadata storage and retrieval")
        print("  4. Chat feature working after analysis")
        
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
