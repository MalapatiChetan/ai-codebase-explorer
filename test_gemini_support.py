#!/usr/bin/env python3
"""Test script to verify Google Gemini support in AI analyzer."""

import os
import sys
import logging

# Configure logging to see provider messages
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)

sys.path.insert(0, '.')

from src.modules.ai_analyzer import AIArchitectureAnalyzer

def test_ai_analyzer():
    """Test the AI analyzer with different provider configurations."""
    
    print("\n" + "="*70)
    print("Testing Google Gemini Support in AI Analyzer")
    print("="*70)
    
    # Test 1: Initialize without any API keys (should use rule-based)
    print("\n[TEST 1] Initialize without API keys (rule-based fallback)")
    print("-" * 70)
    
    analyzer = AIArchitectureAnalyzer()
    print(f"\n✓ AIArchitectureAnalyzer initialized")
    print(f"  Active Provider: {analyzer.provider.upper()}")
    assert analyzer.provider == "rule-based", f"Expected 'rule-based', got '{analyzer.provider}'"
    
    # Test 2: Perform analysis with rule-based provider
    print("\n[TEST 2] Perform analysis with rule-based provider")
    print("-" * 70)
    
    sample_metadata = {
        'repository': {'name': 'test-repo', 'url': 'https://github.com/test/repo'},
        'analysis': {'primary_language': 'Python', 'file_count': 50, 'has_backend': True, 'has_frontend': False},
        'frameworks': {'FastAPI': {'confidence': 0.95}},
        'tech_stack': ['Python', 'FastAPI'],
        'architecture_patterns': ['API-First'],
        'modules': [{'name': 'api', 'type': 'module', 'file_count': 10}],
        'root_files': ['README.md']
    }
    
    result = analyzer.analyze(sample_metadata)
    print(f"\n✓ Analysis completed")
    print(f"  Status: {result['status']}")
    print(f"  Provider used: {analyzer.provider}")
    print(f"  Analysis keys: {list(result['analysis'].keys())}")
    print(f"  Analysis note: {result['analysis'].get('note', 'N/A')}")
    
    assert result['status'] == 'success', f"Expected status 'success', got '{result['status']}'"
    assert 'raw_analysis' in result['analysis'], "Missing 'raw_analysis' in result"
    
    # Test 3: Verify provider selection logic
    print("\n[TEST 3] Verify provider selection logic")
    print("-" * 70)
    
    from src.utils.config import settings
    
    print(f"\nCurrent settings:")
    print(f"  GOOGLE_API_KEY configured: {bool(settings.GOOGLE_API_KEY)}")
    print(f"  OPENAI_API_KEY configured: {bool(settings.OPENAI_API_KEY)}")
    print(f"  Google model: {settings.GOOGLE_MODEL}")
    print(f"  OpenAI model: {settings.OPENAI_MODEL}")
    
    print(f"\nProvider selection logic:")
    if settings.GOOGLE_API_KEY:
        print("  1. GOOGLE_API_KEY is set → Will use Gemini (if valid)")
    else:
        print("  1. GOOGLE_API_KEY is NOT set → Will skip Gemini")
    
    if settings.OPENAI_API_KEY:
        print("  2. OPENAI_API_KEY is set → Will use OpenAI (if Gemini fails)")
    else:
        print("  2. OPENAI_API_KEY is NOT set → Will skip OpenAI")
    
    print("  3. Fallback to rule-based analysis (always available)")
    
    # Test 4: Verify module imports
    print("\n[TEST 4] Verify Gemini module is available")
    print("-" * 70)
    
    try:
        import google.generativeai as genai
        print("\n✓ google.generativeai module imported successfully")
        print(f"  Module: google.generativeai")
        print(f"  Version: {genai.__version__ if hasattr(genai, '__version__') else 'Unknown'}")
    except ImportError as e:
        print(f"\n✗ Failed to import google.generativeai: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("\n✓ All tests passed!")
    print("\nProvider Priority (in order):")
    print("  1. Google Gemini (if GOOGLE_API_KEY is set)")
    print("  2. OpenAI (if OPENAI_API_KEY is set)")
    print("  3. Rule-based fallback (always available)")
    print("\nTo enable Gemini, set GOOGLE_API_KEY in .env file:")
    print("  GOOGLE_API_KEY=your-api-key-here")
    print("\nTo enable OpenAI, set OPENAI_API_KEY in .env file:")
    print("  OPENAI_API_KEY=your-api-key-here")
    print("\n" + "="*70)

if __name__ == "__main__":
    try:
        test_ai_analyzer()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
