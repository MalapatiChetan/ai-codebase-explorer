QUICK START: API KEY SETUP & CONFIGURATION
===========================================

WHAT YOU NEED (5 MINUTES SETUP)
===============================

1. Google Gemini API Key (REQUIRED for chat)
2. Pinecone API Key (optional, for production)
3. GitHub Token (optional, for private repos)

Minimum to get working: Just #1


STEP 1: GET GOOGLE GEMINI API KEY
==================================

This is the API key that powers chat. Without it, chat falls back to rule-based.

Process (2 minutes):
  1. Go to: https://aistudio.google.com/app/apikey
  2. Sign in with Google account (create if needed)
  3. Click "+ Create API Key"
  4. Choose "Create in new project" or pick existing project
  5. Copy the API key (starts with "AIza...")
  6. Keep this safe! Never commit to git.

Add to your .env file:
  GOOGLE_API_KEY=AIza...your...key...here

Verify it works:
  curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY" \
    -H "Content-Type: application/json" \
    -d '{"contents":[{"parts":[{"text":"test"}]}]}'

Should return: success (not 401 Unauthorized)

Common issues:
  ❌ "PROJECT_DISABLED" → Check https://console.cloud.google.com/
  ❌ "PERMISSION_DENIED" → Key doesn't have Generative Language API access
  ❌ "RESOURCE_EXHAUSTED" → Free tier quota exceeded (100 reqs/min)


STEP 2: CONFIGURE .env FILE
============================

Create file: .env (in project root)

Required settings:
---
# Google Gemini (for AI chat)
GOOGLE_API_KEY=AIza...               # From step 1
GOOGLE_MODEL=gemini-2.5-flash        # Don't change
GOOGLE_MAX_TOKENS=4000               # IMPORTANT! Was 1000 (bug), now 4000
GOOGLE_TEMPERATURE=0.7

# Enable features
ENABLE_AI_CHAT=true
ENABLE_RAG=true
ENABLE_RAG_INDEX_ON_ANALYZE=true

# Storage (must be persistent in production!)
REPO_CLONE_PATH=./data/repos
DIAGRAM_OUTPUT_PATH=./data/diagrams
RAG_INDEX_PATH=./data/rag_indices

# Vector store (new)
VECTOR_BACKEND=local_faiss           # Or "pinecone" if using cloud
ENABLE_COMMIT_CACHE=true

# Debug
DEBUG=false
---

Optional settings for advanced use:
---
# GitHub (only if analyzing private repos)
GITHUB_TOKEN=ghp_...
GITHUB_USERNAME=your-username

# Database (not needed for basic setup)
DATABASE_URL=
ENABLE_CACHING=false

# Async processing (advanced)
ENABLE_ASYNC_PROCESSING=false
---


STEP 3: LOCAL TESTING
=====================

Verify API key works locally:

1. Ensure .env file exists with GOOGLE_API_KEY

2. Start backend:
   cd /path/to/project
   python -m uvicorn src.main:app --reload

3. Test chat endpoint:
   curl -X POST http://localhost:8000/api/query \
     -H "Content-Type: application/json" \
     -d '{
       "repository_name": "fastapi/fastapi",
       "question": "What is this project?"
     }'

Expected response:
  - "status": "success"
  - "answer": "FastAPI is..."
  - "mode": "ai" (not "rule-based")
  - "ai_mode": "RAG + Gemini" or just "Gemini"

If "rule-based": API key not working, check logs for:
  "AI disabled: GOOGLE_API_KEY not configured"


STEP 4: PRODUCTION DEPLOYMENT (Render)
========================================

On Render.com:

1. Add environment variables:
   Dashboard → Service → Environment
   
   Name: GOOGLE_API_KEY
   Value: AIza...your...key...
   
   (Add each variable from .env)

2. Configure persistent storage for RAG indices:
   Dashboard → Service → Disks
   
   Create disk:
   - Name: data
   - Mount path: /mnt/data
   - Size: 5GB (adjust as needed)
   
   Then set in environment:
   - RAG_INDEX_PATH=/mnt/data/rag_indices

3. Redeploy:
   git push (triggers redeploy)

4. Verify:
   Logs → Look for:
   "✓ AI (Gemini) enabled. Model: gemini-2.5-flash"
   "✓ Directory ready: /mnt/data/rag_indices"


STEP 5: MONITOR USAGE
====================

Google Gemini API:
  Dashboard: https://console.cloud.google.com/
  
  Left sidebar → APIs & Services → Dashboard
  → Generative Language API
  → Monitor tab shows: requests, tokens used, failures
  
  Quotas:
    Free tier: 2 requests/min, 32K tokens/min limit
    Paid: 100+ requests/min (upgrade in Cloud Console)
  
  If you hit quota:
    1. Increase in Google Cloud Console
    2. Or cache more aggressively (reduce RAG_TOP_K)
    3. Or deploy to multiple regions

Monitor in logs for:
  ✓ finish_reason: STOP (complete) vs MAX_TOKENS (truncated)
  ✓ output_tokens: should be decent length, not 0
  ✓ truncated_detected: should be false


STEP 6: ADVANCED - PINECONE (Production Scale)
===============================================

Skip this if using local FAISS. Only needed if:
  - Multiple server instances
  - Very high traffic
  - Vercel deployment
  - Want guaranteed uptime

Setup (10 minutes):

1. Create Pinecone account:
   https://www.pinecone.io → Sign up

2. Create index:
   → Indexes → + Create Index
   Name: codebase-embeddings
   Dimension: 384
   Metric: cosine
   Environment: starter (free)
   → Create

3. Get API key:
   → API Keys → Copy key

4. Add to .env:
   VECTOR_BACKEND=pinecone
   PINECONE_API_KEY=pcak_...your...key...
   PINECONE_INDEX_NAME=codebase-embeddings

5. Test:
   python -c "from src.modules.vector_store_pinecone import PineconeProvider; p = PineconeProvider(...); print(p.health_check())"

Benefits:
  ✓ Survives restarts and deployments
  ✓ Shared across multiple instances
  ✓ Automatic backups
  ✓ No setup needed on server

Costs:
  Free: Up to 1M vectors
  Paid: $25/month + $0.10 per million vectors


TROUBLESHOOTING
===============

Problem: Chat returns "rule-based" answers (not AI)
Solution:
  1. Check logs for: "AI disabled: ..."
  2. Verify GOOGLE_API_KEY is in .env
  3. Verify it's not an empty string
  4. Check: echo $GOOGLE_API_KEY (should print key)
  5. If on Render: restart service after adding env var

Problem: "PERMISSION_DENIED" error in logs
Solution:
  1. API key might be wrong
  2. Get new key from https://aistudio.google.com/app/apikey
  3. Ensure Generative Language API is enabled in Cloud Console

Problem: "RESOURCE_EXHAUSTED" (quota exceeded)
Solution:
  1. Free tier: 2 reqs/min, too low for production
  2. Go to https://console.cloud.google.com/billing
  3. Enable billing
  4. Increase quota under APIs & Services

Problem: Answers still truncate after fix
Solution:
  1. Check logs for "finish_reason": might be something else
  2. Increase GOOGLE_MAX_TOKENS from 4000 to 6000 or 8000
  3. Or reduce RAG_TOP_K from 5 to 3 (less code context)
  4. Check if Gemini quota reached

Problem: RAG index not persisting (Render)
Solution:
  1. Create persistent disk (see Step 4)
  2. Mount to /mnt/data
  3. Set RAG_INDEX_PATH=/mnt/data/rag_indices
  4. Restart service


QUICK REFERENCE - COMPLETE .env
================================

Copy this template, fill in your keys:

```
# ===== REQUIRED =====
GOOGLE_API_KEY=AIza_YOUR_KEY_HERE

# ===== IMPORTANT =====
GOOGLE_MODEL=gemini-2.5-flash
GOOGLE_MAX_TOKENS=4000
GOOGLE_TEMPERATURE=0.7

# ===== FEATURE FLAGS =====
ENABLE_AI_CHAT=true
ENABLE_RAG=true
ENABLE_RAG_INDEX_ON_ANALYZE=true
DEBUG=false

# ===== STORAGE PATHS =====
REPO_CLONE_PATH=./data/repos
DIAGRAM_OUTPUT_PATH=./data/diagrams
RAG_INDEX_PATH=./data/rag_indices

# ===== VECTOR STORE =====
VECTOR_BACKEND=local_faiss
ENABLE_COMMIT_CACHE=true

# ===== OPTIONAL =====
# For private GitHub repos:
GITHUB_TOKEN=
GITHUB_USERNAME=

# For Pinecone (cloud embeddings):
PINECONE_API_KEY=
PINECONE_INDEX_NAME=codebase-embeddings

# Advanced:
DATABASE_URL=
ENABLE_CACHING=false
ENABLE_ASYNC_PROCESSING=false
```


VALIDATION CHECKLIST
====================

Before deploying to production:

[ ] GOOGLE_API_KEY is valid (tested with curl)
[ ] GOOGLE_MAX_TOKENS is set to 4000 or higher
[ ] ENABLE_AI_CHAT=true
[ ] ENABLE_RAG=true
[ ] RAG_INDEX_PATH points to persistent storage
[ ] Tested locally: chat works and gives full answers
[ ] Tested on production: responses complete
[ ] Checked logs show finish_reason: STOP (not MAX_TOKENS)
[ ] Verified truncated_detected: false in logs

If using Pinecone:
[ ] VECTOR_BACKEND=pinecone
[ ] PINECONE_API_KEY is configured
[ ] PINECONE_INDEX_NAME exists and has dimension 384
[ ] Tested health_check passes


GETTING HELP
============

If things don't work:

1. Check logs:
   Render: Dashboard → Logs
   Local: Terminal output (can see full errors)

2. Search for error in logs:
   "GOOGLE" → check API key setup
   "truncated" → truncation issue (check GOOGLE_MAX_TOKENS)
   "RAG" → search issue (indices missing)
   "permission" → API key wrong

3. Verify setup:
   python -c "import os; print(os.getenv('GOOGLE_API_KEY', 'NOT FOUND'))"

4. Test specific functionality:
   Test chat endpoint (see Step 3)
   Test RAG indexing (analyze a repo, check /data/rag_indices)
   Test Gemini directly (curl test above)
