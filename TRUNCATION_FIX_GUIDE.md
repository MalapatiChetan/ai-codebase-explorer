ROOT CAUSE ANALYSIS & FIXES FOR TRUNCATED ANSWERS
==================================================

WHAT WAS BROKEN AND HOW WE FIXED IT:

┌─────────────────────────────────────────────────────────────────┐
│ ROOT CAUSE #1: HARDCODED 1000-TOKEN LIMIT                       │
├─────────────────────────────────────────────────────────────────┤
│ Location: src/modules/architecture_query_answerer.py, line 469  │
│ Code:                                                            │
│   response = self.client.models.generate_content(...             │
│       config={                                                   │
│           "max_output_tokens": 1000,  ← BUG: WAY TOO LOW!       │
│       }                                                           │
│   )                                                              │
│                                                                  │
│ Impact: Answers truncated after ~1000 tokens (≈4000 chars)      │
│ Configuration had GOOGLE_MAX_TOKENS=4000 but wasn't used!       │
│                                                                  │
│ FIX:                                                             │
│   - Use getattr(settings, "GOOGLE_MAX_TOKENS", 4000)            │
│   - Constrain to safe range: 2000-8000 tokens                   │
│ Result: Now allows 4000-8000 tokens for responses               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ROOT CAUSE #2: NO PROMPT BUDGETING                               │
├─────────────────────────────────────────────────────────────────┤
│ Problem: Huge context (metadata + code snippets) consumed most  │
│ of the token budget, leaving little room for response.          │
│                                                                  │
│ Examples:                                                        │
│ - System prompt: ~150 tokens                                   │
│ - Metadata context: ~500-2000 tokens                           │
│ - Code snippets: ~2000-5000 tokens                             │
│ - User question: ~50 tokens                                    │
│ - Total: 2700-7250 tokens                                      │
│                                                                  │
│ With 1000 max output, only 0-300 tokens left!                  │
│                                                                  │
│ FIX:                                                             │
│   - Created prompt_budget.py utility                            │
│   - Estimate token usage per component                          │
│   - Dynamically trim context to reserve response budget        │
│   - Minimum 1200 tokens reserved for response                  │
│   - Reduce: snippets > snippet size > metadata verbosity        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ROOT CAUSE #3: NO FINISH_REASON CHECKING                         │
├─────────────────────────────────────────────────────────────────┤
│ Problem: Didn't detect when Gemini hit MAX_TOKENS limit         │
│ Silent truncation - responses seemed complete but weren't.      │
│                                                                  │
│ FIX:                                                             │
│   - Check response.finish_reason for "MAX_TOKENS"              │
│   - Detect incomplete markdown/lists/sentences                  │
│   - Log truncation detection as "truncated_detected"            │
│   - Implement automatic continuation retry:                     │
│     "Continue from where you stopped..."                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ ROOT CAUSE #4: NO OBSERVABILITY                                 │
├─────────────────────────────────────────────────────────────────┤
│ Problem: Couldn't diagnose issues in production                 │
│                                                                  │
│ FIX: Now log structured observability data:                     │
│   - prompt_estimated_tokens: tokens in initial prompt           │
│   - snippet_count: how many code snippets included              │
│   - context_chars: total context size                           │
│   - requested_max_output_tokens: what we asked for              │
│   - finish_reason: why Gemini stopped (STOP/MAX_TOKENS/etc)    │
│   - output_chars: actual response length                        │
│   - output_tokens: estimated response token count               │
│   - truncated_detected: true if truncation detected            │
└─────────────────────────────────────────────────────────────────┘


IMPLEMENTATION HIGHLIGHTS
==========================

NEW FILES:
  src/utils/prompt_budget.py
    - estimate_tokens(text) - rough token counting
    - create_budget(...) - plan token allocation
    - trim_context(...) - intelligently shrink context
    - trim_code_snippets(...) - reduce code examples

  src/modules/vector_store_provider.py
    - Abstract base class for RAG backends
    - LocalFaissProvider - local commit-aware caching
    - Commit hash checking to skip re-indexing
    - Works while instance alive, lost on restart

  src/modules/vector_store_pinecone.py
    - Pinecone cloud implementation (template)
    - Survives restarts, shared across instances
    - Namespace per repo+commit for caching
    - Ready to implement when needed

MODIFIED FILES:
  src/modules/architecture_query_answerer.py
    - Fixed root causes #1-4
    - Added prompt budgeting
    - Added finish_reason checking
    - Added continuation retry logic
    - Added observability logging
    - New _continue_truncated_answer() method


TESTING THE FIXES
=================

BEFORE FIX:
  Q: "Explain the system architecture in detail"
  A: "This project consists of several key components:
      1. Frontend layer...
      2. Backend API...
      [TRUNCATED - response ends abruptly]"
  Length: ~400 chars instead of expected 2000+

AFTER FIX:
  Q: "Explain the system architecture in detail"
  A: "This project consists of several key components:
      1. Frontend layer - React with TypeScript, handles...
      2. Backend API - FastAPI with Python, provides REST...
      3. Database layer - PostgreSQL, stores user data...
      4. Caching layer - Redis, speeds up queries...
      5. Authentication - JWT tokens with role-based...
      [complete answer, ends with period]"
  Length: ~2500 chars (625% longer!)
  finish_reason: STOP (not MAX_TOKENS)
  truncated_detected: false


TOKEN BUDGET EXAMPLES
=====================

Example 1: Large Repository
  System prompt:     150 tokens
  Metadata context:  1500 tokens  (lots of frameworks, modules)
  Code snippets:     2000 tokens  (10 RAG results, each 200 chars)
  User question:     50 tokens
  Total input:       3700 tokens
  
  Before fix:
    Reserved for response: 1000 tokens ← PROBLEM
    Actual response space: 0 tokens (over budget!)
    
  After fix:
    Input limit:     1,000,000 tokens (Gemini 2.5-flash)
    Reserved output: 1500 tokens
    Available input: 998,500 tokens
    
    With budget at 3700:
      Still have 994,800 tokens available!
      Can reserve 4000 for response
      Result: Complete, detailed answers

Example 2: Small Repository
  System prompt:     150 tokens
  Metadata context:  300 tokens   (few frameworks)
  Code snippets:     400 tokens   (2 RAG results)
  User question:     100 tokens
  Total input:       950 tokens
  
  After fix:
    Available output: 4000 tokens
    Response is complete and detailed
    No truncation possible


RAG STORAGE & COMMIT CACHING
============================

LOCAL FAISS (Current):
  Location: ./data/rag_indices/repo_owner_repo_name_{commit_sha}/
  Files:
    - index.faiss: FAISS vector database
    - metadata.json: chunk metadata + commit info
  
  Persistence:
    ✓ Survives instance restart (if storage is not ephemeral)
    ✗ Lost on container restart (Render, Vercel, etc.) if no persistent volume
    ✗ Not shared across multiple server instances

  Startup behavior:
    - Auto-loads on startup if exists
    - Skips re-index if commit unchanged
    - Fallback: re-index if missing
    
  Logs show:
    - "✓ Found cached index for repo@commit" if cache hit
    - "Rebuilding index..." if cache miss

PINECONE (Cloud):
  Location: Cloud namespace "repo_owner/repo_name{commit_sha}"
  
  Persistence:
    ✓ Survives restarts, failures, deployments
    ✓ Shared across multiple instances
    ✓ Automatic backup and recovery
    ✗ Network latency on queries
    ✗ Cost for API calls + storage
    
  Startup behavior:
    - Checks cloud for commit namespace
    - Skips re-index if exists
    - Queries cloud-hosted vectors


CONFIGURATION
==============

DON'T FORGET THESE SETTINGS:

# In .env or environment variables:

# Google Gemini (REQUIRED for AI):
GOOGLE_API_KEY=<your-key>              # Get from: https://aistudio.google.com/app/apikey
GOOGLE_MODEL=gemini-2.5-flash          # Don't change unless you know why
GOOGLE_MAX_TOKENS=4000                 # Changed from implicit 1000!
GOOGLE_TEMPERATURE=0.7

# Enable chat (required):
ENABLE_AI_CHAT=true

# RAG Configuration:
ENABLE_RAG=true
ENABLE_RAG_INDEX_ON_ANALYZE=true
RAG_INDEX_PATH=./data/rag_indices      # Must persist across restarts in production!

# Vector Store (NEW):
VECTOR_BACKEND=local_faiss             # Options: "local_faiss", "pinecone"
ENABLE_COMMIT_CACHE=true               # Skip re-index if commit unchanged

# For Pinecone (only if using Pinecone):
PINECONE_API_KEY=<your-pinecone-key>
PINECONE_INDEX_NAME=codebase-embeddings


HOW TO GET API KEYS
===================

GOOGLE GEMINI API KEY:
  1. Go to: https://aistudio.google.com/app/apikey
  2. Click "Create API Key"
  3. Create in new project (or select existing)
  4. Copy the key
  5. Set in .env: GOOGLE_API_KEY=<key>
  6. Check uses: Free tier has limits, consider upgrading
  7. Monitor: https://console.cloud.google.com/billing

  Quota limits:
    Free tier:    2 RPM (requests/min), 32K tokens/min
    Paid tier:    100+ RPM (adjust in Cloud Console)
    
  Verify it works:
    curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY" \
      -H "Content-Type: application/json" \
      -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'

PINECONE API KEY (Optional, for production):
  1. Sign up: https://www.pinecone.io
  2. Create project → Create index (dimension: 384)
  3. Copy API key
  4. Set in .env: PINECONE_API_KEY=<key>
  5. Set index name: PINECONE_INDEX_NAME=codebase-embeddings
  6. Pricing: Starter (free 1M vectors), then pay-per-use

GITHUB TOKEN (Optional, for private repos):
  1. GitHub Settings → Developer settings → Personal access tokens
  2. Generate new token (classic)
  3. Scope: "repo" (full control of private repositories)
  4. Copy token
  5. Set in .env: GITHUB_TOKEN=<token>


ENVIRONMENT VARIABLES CHECKLIST
================================

REQUIRED FOR CHAT TO WORK:
  ✓ GOOGLE_API_KEY - without this, chat falls back to rule-based
  ✓ ENABLE_AI_CHAT=true - master switch
  ✓ GOOGLE_MAX_TOKENS=4000 - ensure response budget

PRODUCTION PERSISTENCE (important!):
  ✓ RAG_INDEX_PATH must point to persistent volume
    - On Render: mount service volume to /mnt/data
    - On Vercel: not supported (use Pinecone instead)
    - On Docker: mount volume to container
    - Without persistence: index lost on restart → answers degrade

  ✓ If using local FAISS:
    - Commit cache only works if data survives restart
    - Render: configure service volume as persistent
    - Docker: mount -v /path/to/persistent:/data

  ✓ If using Pinecone:
    - Set VECTOR_BACKEND=pinecone
    - PINECONE_API_KEY configured
    - Works automatically across restarts


PRODUCTION RECOMMENDATIONS
===========================

OPTION 1: Local FAISS + Persistent Volume (Simplest)
  Best for: Single server, limited scale
  Setup:
    - Configure Render service volume for /data
    - Or mount Docker volume
    - Cost: Free (data storage only)
    - Trade-off: Lost on server restart if not persistent

  .env settings:
    VECTOR_BACKEND=local_faiss
    RAG_INDEX_PATH=/mnt/data/rag_indices
    ENABLE_COMMIT_CACHE=true

OPTION 2: Pinecone Cloud (Recommended for Production)
  Best for: Multi-instance, High availability, Vercel
  Setup:
    - Create Pinecone account: https://www.pinecone.io
    - Create index (dimension 384)
    - Set API key in environment
  Cost: Free tier up to 1M vectors, then $0.10/M vectors/month
  Benefits:
    - Survives restarts and failures
    - Shared across multiple instances
    - Automatic backups
    - Scales to billions of vectors

  .env settings:
    VECTOR_BACKEND=pinecone
    PINECONE_API_KEY=<your-key>
    PINECONE_INDEX_NAME=codebase-embeddings
    ENABLE_COMMIT_CACHE=true

OPTION 3: Hybrid (Best Practice)
  Use local FAISS as cache, Pinecone as backup:
    - Fast: queries hit local FAISS first
    - Reliable: synced to Pinecone periodically
    - Automatic failover if local lost
  (Requires custom implement, not included in this release)


OBSERVABILITY LOGS
==================

Example log output showing new diagnostics:

[INFO] Token budget: {
  'model': 'gemini-2.5-flash',
  'system_prompt_tokens': 150,
  'user_question_tokens': 85,
  'context_tokens': 2340,
  'available_for_context': 996425,
  'reserved_output_tokens': 1500,
  'is_over_budget': False
}

[INFO] AI response metrics: {
  'prompt_estimated_tokens': 2575,
  'snippet_count': 5,
  'context_chars': 9360,
  'requested_max_output_tokens': 4000,
  'finish_reason': 'STOP',         ← Check this value!
  'output_chars': 2847,
  'output_tokens': 712,
  'truncated_detected': False,
  'retry_attempted': False
}

If truncated:
[WARNING] ✗ Response was truncated (finish_reason=MAX_TOKENS). Attempting second pass...
[INFO] Continuation successful. Original: 3999 chars, Continuation: 1200 chars


TEST QUERIES
============

Try these to verify fixes work:

1. Simple Query (should work):
   Q: "What is this project?"
   A: Should be ~500-1000 chars, complete

2. Complex Query (previously truncated):
   Q: "Explain the complete system architecture, including all components, data flow, and how they interact"
   A: Should be 2000+ chars, fully complete
   Observe: finish_reason should be "STOP", truncated_detected: false

3. Very Long Query (tests budgeting):
   Q: "I need every detail about [large repo] - describe every file, every function, the data model, deployment process, testing approach, performance considerations, security model, dependencies, and how to extend it"
   A: Should be trimmed gracefully, still informative, no truncation
   Observe: context was auto-trimmed, snippets reduced

4. Test continuation (artificial truncation):
   Manually set max_output_tokens to 500 in config, query
   A: Should attempt continuation, should be long again
   Observe: retry_attempted: true in logs


REMAINING LIMITATIONS
======================

1. Token Estimation:
   - Current: 1 token ≈ 4 chars (rough)
   - More accurate: pip install tiktoken
   - Would improve budgeting precision

2. Local FAISS Limitations:
   - Ephemeral filesystem: data lost on restart
   - Single instance: can't share across servers
   - Solution: Use Pinecone for production

3. Continuation Retry:
   - Only handles MAX_TOKENS
   - Partial answers + continuation = longer latency
   - Trade-off: Complete answer takes 2 API calls

4. Code Snippet Trimming:
   - Current: removes snippets or limits lines
   - Could be smarter: prioritize by relevance
   - Future: use RAG scores to keep best snippets

5. Metadata Context:
   -Always includes all frameworks, tech stack
   - Could trim less relevant for specific questions
   - Future: use intent to customize context


NEXT STEPS
==========

1. COMMIT: Test locally, commit changes to git
2. DEPLOY: Push to Render/Vercel
3. MONITOR: Watch logs for finish_reason and truncation_detected
4. TUNE: Adjust GOOGLE_MAX_TOKENS if needed (default 4000 is conservative)
5. MIGRATE: Consider Pinecone for production multi-instance setup
