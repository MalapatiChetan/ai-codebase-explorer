#!/usr/bin/env python
"""Comprehensive diagnostic script for /api/query AI fallback issue."""

import sys
import logging

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(name)s: %(message)s')

print("\n" + "="*80)
print("AI QUERY ENDPOINT DIAGNOSIS")
print("="*80)

# Test 1: Configuration State
print("\n[TEST 1] Configuration State")
print("-" * 80)
try:
    from src.utils.config import settings
    
    google_api_key = settings.GOOGLE_API_KEY
    enable_ai_chat = settings.ENABLE_AI_CHAT
    
    print("[OK] Config module imported")
    print(f"  GOOGLE_API_KEY: {'SET' if google_api_key else 'EMPTY'} (length: {len(google_api_key)})")
    print(f"  ENABLE_AI_CHAT: {enable_ai_chat}")
    print(f"  GOOGLE_MODEL: {settings.GOOGLE_MODEL}")
    print(f"  GOOGLE_TEMPERATURE: {settings.GOOGLE_TEMPERATURE}")
    
    # Test the helper methods
    is_ai_usable = settings.is_ai_usable()
    ai_disabled_reason = settings.get_ai_disabled_reason()
    
    print(f"\n  settings.is_ai_usable(): {is_ai_usable}")
    print(f"  settings.get_ai_disabled_reason(): '{ai_disabled_reason}'")
    
except Exception as e:
    print(f"[FAIL] Config error: {e}")
    sys.exit(1)

# Test 2: ArchitectureQueryAnswerer Initialization
print("\n[TEST 2] ArchitectureQueryAnswerer Initialization")
print("-" * 80)
try:
    from src.modules.architecture_query_answerer import ArchitectureQueryAnswerer
    
    print("Creating ArchitectureQueryAnswerer instance...")
    answerer = ArchitectureQueryAnswerer()
    
    print(f"[OK] Answerer created")
    print(f"  answerer.ai_usable: {answerer.ai_usable}")
    print(f"  answerer.client: {'SET' if answerer.client else 'None'}")
    print(f"  answerer.rag_enabled: {answerer.rag_enabled}")
    
    if answerer.ai_usable:
        print(f"  answerer.google_model: {answerer.google_model}")
        print(f"  answerer.google_temperature: {answerer.google_temperature}")
    
except Exception as e:
    print(f"[FAIL] Answerer initialization error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Gemini Client Direct Test
print("\n[TEST 3] Gemini Client Direct Test")
print("-" * 80)
if settings.GOOGLE_API_KEY:
    try:
        from google import genai
        
        print("Attempting to initialize Gemini client directly...")
        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        print(f"[OK] Gemini client initialized")
        
        # Try a simple API call
        print("Testing Gemini API with a simple query...")
        response = client.models.generate_content(
            model=settings.GOOGLE_MODEL,
            contents="Say 'OK' if you receive this.",
            config={"temperature": 0.7, "max_output_tokens": 100}
        )
        print(f"[OK] Gemini API responded: {response.text[:50]}")
        
    except Exception as e:
        print(f"[FAIL] Gemini client error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[SKIP] No GOOGLE_API_KEY - skipping Gemini client test")

# Test 4: Answer Question Logic
print("\n[TEST 4] Answer Question Logic Simulation")
print("-" * 80)
print("Simulating what happens in /api/query endpoint:")
print(f"  1. is_ai_usable() = {answerer.ai_usable}")
print(f"  2. client initialized = {answerer.client is not None}")

if answerer.ai_usable:
    print(f"  -> Should route to: _ai_answer_question()")
    print(f"    Which calls: Gemini API with optional RAG")
else:
    reason = settings.get_ai_disabled_reason()
    print(f"  -> Will route to: _rule_based_answer()")
    print(f"    Reason: {reason}")

# Test 5: Check for Silent Failures
print("\n[TEST 5] Silent Failure Detection")
print("-" * 80)

# Scenario A: ENABLE_AI_CHAT = False
if not settings.ENABLE_AI_CHAT:
    print("[WARN] ENABLE_AI_CHAT = False -> AI will always be disabled")
    print("   Fix: Set ENABLE_AI_CHAT=true in .env")

# Scenario B: Empty GOOGLE_API_KEY
if not settings.GOOGLE_API_KEY:
    print("[WARN] GOOGLE_API_KEY is empty -> AI will be disabled")
    print("   Fix: Set GOOGLE_API_KEY=<your-api-key> in .env")

# Scenario C: Both enabled but client init fails
if settings.is_ai_usable() and answerer.client is None:
    print("[WARN] CRITICAL: AI should be usable but client is None")
    print("   This indicates a silent failure in client initialization")
    print("   Check Gemini API key validity and network connectivity")

# Test 6: Expected vs Actual Behavior
print("\n[TEST 6] Expected vs Actual Behavior")
print("-" * 80)
print("For /api/query to use AI, we need:")
print("  [*] ENABLE_AI_CHAT = true")
print("  [*] GOOGLE_API_KEY = <valid API key>")
print("  [*] settings.is_ai_usable() = True")
print("  [*] answerer.client = initialized")
print("  [*] answerer.ai_usable = True")

print("\nCurrent state:")
print(f"  [{'Y' if settings.ENABLE_AI_CHAT else 'N'}] ENABLE_AI_CHAT = {settings.ENABLE_AI_CHAT}")
print(f"  [{'Y' if settings.GOOGLE_API_KEY else 'N'}] GOOGLE_API_KEY = {'SET' if settings.GOOGLE_API_KEY else 'EMPTY'}")
print(f"  [{'Y' if settings.is_ai_usable() else 'N'}] is_ai_usable() = {settings.is_ai_usable()}")
print(f"  [{'Y' if answerer.client is not None else 'N'}] answerer.client = {type(answerer.client).__name__ if answerer.client else None}")
print(f"  [{'Y' if answerer.ai_usable else 'N'}] answerer.ai_usable = {answerer.ai_usable}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

if answerer.ai_usable and answerer.client:
    print("[OK] AI SHOULD BE ACTIVE for /api/query")
    print("  - Requests will use Gemini API")
    print("  - RAG context will be used if available")
    print("  - Model: " + settings.GOOGLE_MODEL)
else:
    print("[FAIL] AI IS DISABLED for /api/query")
    reason = settings.get_ai_disabled_reason()
    print(f"  Reason: {reason}")
    print("  - Requests will use rule-based answers")
    print("  - To enable AI:")
    print("    1. Set ENABLE_AI_CHAT=true in .env")
    print("    2. Set GOOGLE_API_KEY=<api-key> in .env")
    print("    3. Use valid model: gemini-2.5-flash, gemini-2.5-pro, or gemini-2.0-flash")
    print("    4. Restart the backend")

print("="*80 + "\n")
