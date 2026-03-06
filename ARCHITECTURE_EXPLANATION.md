# System Architecture & Workflow - Complete Explanation

## High-Level Overview

```
USER INTERACTION
    ↓
[Frontend] → Click Analyze Button with GitHub URL
    ↓
[Backend API] → POST /api/analyze
    ↓
[Clone & Analyze] → Clone repo, scan files, detect tech
    ↓
[Storage] → Save to local/cloud, store metadata
    ↓
[Index & Embed] → Create RAG embeddings for search
    ↓
[Response] → Return analysis + diagrams
    ↓
[Chat] → User asks questions via POST /api/query
    ↓
[Answer] → Retrieve from registry, use RAG + AI
```

---

## 1. REPOSITORY CLONING & STORAGE

### Question: Does it clone every time, or store locally?

**Answer: BOTH - but in a specific way**

```
First Analysis of: https://github.com/org/repo1
    ↓
Repository CLONED to: /tmp/ai-explainer/repos/repo1/
(On Render cloud)
or ./data/repos/repo1/ (local machine)
    ↓
Stored as a FULL GIT CLONE (shallow depth=1)
    ↓
Metadata SAVED to: ./metadata_cache/repo1.json
    ↓
Second Analysis (user clicks Analyze again)
    ↓
Repository DELETED and RE-CLONED from GitHub
(NOT reused from disk)
```

**Key Point: The repository IS stored on disk, but it's DELETED every time, not updated.**

### Storage Locations

```
Local Development:
├── ./data/repos/
│   ├── repo1/          ← Actual cloned code
│   ├── repo2/
│   └── smart-parking-lot/
├── ./data/diagrams/
│   ├── repo1/          ← Generated diagrams
│   ├── repo2/
│   └── smart-parking-lot/
├── ./data/rag_indices/
│   ├── repo1/          ← Vector embeddings for search
│   ├── repo2/
│   └── smart-parking-lot/
└── ./metadata_cache/
    ├── repo1.json      ← Metadata snapshot
    ├── repo2.json
    └── smart-parking-lot.json

Cloud (Render):
├── /tmp/ai-explainer/repos/         ← Same structure
├── /tmp/ai-explainer/diagrams/
├── /tmp/ai-explainer/rag_indices/
└── ./metadata_cache/                 ← Persisted (not ephemeral)
```

### File Sizes
- **Repository clone**: 10-50 MB (shallow, depth=1, single-branch)
- **Metadata cache**: 10-200 KB per repo (JSON)
- **RAG indices**: 1-5 MB per repo (embeddings)
- **Diagrams**: 10-50 KB per repo (Mermaid + JSON)

---

## 2. UPDATING REPOSITORIES - IS IT UP-TO-DATE?

### Question: How does the system determine if stored repo is current?

**Answer: IT DOESN'T - It just re-clones**

```
Current Strategy (SIMPLE but INEFFICIENT):
    
User clicks Analyze (first time)
├─ Check if /tmp/ai-explainer/repos/repo1/ exists?
│  └─ NO → Clone fresh from GitHub
│
User clicks Analyze again (second time)
├─ Check if /tmp/ai-explainer/repos/repo1/ exists?
│  └─ YES → DELETE IT COMPLETELY
│  └─ Clone fresh from GitHub again
│
Result: Always analyzing the latest commit ✓
Problem: Always re-downloads (inefficient) ✗
```

**There is NO caching logic that says:**
- "Check if local repo is older than 1 hour"
- "Pull latest commits instead of re-cloning"
- "Compare GitHub HEAD with local HEAD"

### Why This Design?

**Simplicity over efficiency:**
- Guarantees always analyzing latest code
- Avoids merge conflicts, stale data
- Works reliably in cloud (ephemeral storage)
- Backward compatible with old behavior

**Cost:**
- Every analysis re-downloads the entire repository
- Slower analysis (45+ seconds for large repos)
- Higher bandwidth usage
- More disk I/O

---

## 3. WHAT HAPPENS ON RE-ANALYSIS

```
FIRST ANALYSIS (smart-parking-lot)
────────────────────────────────────

User enters: https://github.com/smartparkingiot/smart-parking-lot
Click Analyze

1. clone_repository()
   ├─ Check: /tmp/ai-explainer/repos/smart-parking-lot/ exists?
   │  └─ NO (first time)
   └─ Clone from GitHub (depth=1, ~2 sec)

2. scan_repository()
   └─ Walk file tree, extract code structure

3. detect_frameworks()
   └─ Look for package.json, requirements.txt, etc.

4. analyze_dependencies()
   └─ Parse import statements

5. diagram_generator()
   └─ Create Mermaid diagrams

6. index_code_for_rag()
   └─ Extract code chunks, generate embeddings
   └─ Store in /tmp/ai-explainer/rag_indices/smart-parking-lot/

7. registry.register("smart-parking-lot", metadata)
   └─ Save metadata to ./metadata_cache/smart-parking-lot.json
   └─ Keep in memory: in-memory_cache["smart-parking-lot"]

Result: Metadata + diagrams returned to frontend
Chat becomes AVAILABLE


SECOND ANALYSIS (smart-parking-lot again - SAME REPO)
──────────────────────────────────────────────────────

User enters: https://github.com/smartparkingiot/smart-parking-lot
Click Analyze AGAIN

1. clone_repository()
   ├─ Check: /tmp/ai-explainer/repos/smart-parking-lot/ exists?
   │  └─ YES (exists from before)
   ├─ Delete it COMPLETELY (with aggressive cleanup)
   └─ Clone fresh from GitHub (depth=1, ~2 sec)

2-7. Same process (scan, detect, diagram, index, register)

Result: Re-analyzed, metadata updated, chat works again


ANALYZING DIFFERENT REPO (flask after smart-parking-lot)
─────────────────────────────────────────────────────────

User enters: https://github.com/pallets/flask
Click Analyze

1. clone_repository()
   ├─ Check: /tmp/ai-explainer/repos/flask/ exists?
   │  └─ NO (different repo)
   └─ Clone from GitHub

2-7. Same process

In-Memory State:
  in_memory_cache = {
    "smart-parking-lot": {...},  ← From earlier analysis
    "flask": {...}                ← Just registered
  }

Metadata Cache on Disk:
  ./metadata_cache/
  ├── smart-parking-lot.json  ← Persists
  └── flask.json              ← New
```

**Key Insight: Each analysis ALWAYS re-clones, never updates**

---

## 4. WHY DOES IT STILL SHOW "ANALYZING" WHEN REPO IS ALREADY STORED?

The "analyzing" state includes MORE than just cloning:

```
Timeline of "Analyzing" (total: 10-15 seconds)
─────────────────────────────────────────────────

Click Analyze (fork starts in background)
    ↓
[2 sec]  Clone repository (depth=1, shallow clone)
    ↓
[1 sec]  Scan repository structure (walk files, count LOC)
    ↓
[0.5 sec] Detect frameworks (look for patterns)
    ↓
[1 sec]  Analyze dependencies (parse imports)
    ↓
[1 sec]  Generate diagrams (Mermaid + JSON)
    ↓
[5-10 sec] Index code for RAG (extract chunks, generate embeddings)
         ← MOST TIME HERE! sentence-transformers is slow
    ↓
[0.5 sec] Register in metadata cache
    ↓
ANALYSIS COMPLETE ✓

The "analyzing" message doesn't turn off until ALL steps complete
Even if the repo is stored, you still wait for RAG indexing
```

**Why slow?**
- `sentence-transformers` model encoding (10 seconds first time, ~5-10 sec every time)
- FAISS vector indexing
- Diagram generation
- Each step must complete sequentially

**ON DEPLOYMENT (Render):**
- Pulling sentence-transformers model: ~30 seconds first time
- Then all future analyses: ~5-10 seconds for embeddings alone

---

## 5. METADATA STORAGE & REGISTRY SYSTEM

### What Gets Stored?

```
./metadata_cache/smart-parking-lot.json
────────────────────────────────────────

{
  "repository": {
    "url": "https://github.com/smartparkingiot/smart-parking-lot",
    "name": "smart-parking-lot",
    "path": "/tmp/ai-explainer/repos/smart-parking-lot"
  },
  "analysis": {
    "file_count": 156,
    "primary_language": "Python",
    "languages": ["Python", "JavaScript", "HTML"],
    "has_backend": true,
    "has_frontend": true
  },
  "frameworks": {
    "Flask": { "confidence": 0.95 },
    "React": { "confidence": 0.85 }
  },
  "tech_stack": ["Python", "Flask", "React", "JavaScript", "PostgreSQL"],
  "modules": [...],
  "dependencies": [...],
  "root_files": [...],
  "important_files": [...],
  "diagrams": {
    "mermaid": "graph TD ...",
    "json": {...}
  }
}
```

**Current Problems with this:**

1. **No Timestamp**: Can't tell when it was analyzed
2. **No Git Info**: Doesn't store GitHub commit hash
3. **Stale Data**: If repo updated on GitHub, cache still old
4. **No TTL**: Cache lives forever

---

## 6. WHY DOESN'T CHAT WORK IN DEPLOYMENT?

This is the CORE PROBLEM you're experiencing.

### Local (Works ✓)

```
Local Machine Workflow:
──────────────────────

1. Analyze repo
   └─ Metadata saved to: ./metadata_cache/repo.json
   └─ In-memory registry loads it
   └─ RAG index saved locally

2. Click Chat
   └─ Frontend sends: POST /api/query
      {
        "repository_name": "smart-parking-lot",
        "question": "What does this do?"
      }
   
3. Backend /api/query endpoint
   ├─ Check: registry.exists("smart-parking-lot")?
   │  └─ YES (in memory from step 1)
   ├─ Get metadata: registry.get("smart-parking-lot")
   │  └─ Returns full metadata
   ├─ Load RAG: RAGVectorStore("smart-parking-lot").load_index()
   │  └─ Loads from: ./data/rag_indices/smart-parking-lot/
   │  └─ ✓ FILE EXISTS (was created during analysis)
   └─ Answer question using metadata + RAG

Result: Chat works perfectly ✓
```

### Cloud (Render) - BROKEN ✗

```
Cloud/Render Workflow:
──────────────────────

1. Analyze repo
   └─ BACKEND DIES or RESTARTS after analysis
   
2. Click Chat (NEW request)
   └─ Frontend sends: POST /api/query
   
3. Backend /api/query endpoint
   
   NEW Python process starts (app restarts)
   ├─ registry = RepositoryRegistry() [EMPTY!]
   ├─ Tries to load from ./metadata_cache/repo.json
   │  └─ ✓ FOUND (persisted to disk)
   │  └─ Metadata loaded back to memory
   ├─ Tries to talk to chat feature
   │  
   └─ Checks: registry.exists("smart-parking-lot")?
      └─ Need to verify repo name matches!
      └─ CRITICAL BUG: Repo name may have temp path! ❌
      
4. Tries to load RAG index
   └─ RAGVectorStore("smart-parking-lot").load_index()
   └─ Looks for: /tmp/ai-explainer/rag_indices/smart-parking-lot/
   └─ FILE DOESN'T EXIST (Render /tmp is ephemeral = cleaned on restart!)
   └─ ✗ FAILS - Returns empty RAG

Result: Chat returns answer without code context ✗
        Or fails completely if metadata wasn't saved correctly
```

### Why RAG Index Fails on Render

```
Render Ephemeral Storage
────────────────────────

When analysis runs:
  /tmp/ai-explainer/rag_indices/smart-parking-lot/
  ├─ index.faiss       (1-5 MB)
  ├─ chunks.pkl        (binary data)
  └─ metadata.json

Service lives: ✓ Until analysis completes
After response sent: ✓ Still there

USER WAITS
...

Service gets idle/restarts: ✗ /tmp gets WIPED
(Render free tier restarts services)

Next request (chat):
  Browser: "Can you answer about smart-parking-lot?"
  Render: New Python process starts
  Loads metadata: ✓ From ./metadata_cache/ (persisted)
  Loads RAG index: ✗ From /tmp/ (DELETED!)
  
Result: Chat falls back to rule-based (no code context)
```

---

## 7. CHAT FEATURE DETAILED FLOW

### How Chat is Supposed to Work

```
User Question:
  "What technologies does this use?"

Frontend:
  POST /api/query
  {
    "repository_name": "smart-parking-lot",
    "question": "What technologies does this use?"
  }

Backend:
  
  1. ArchitectureQueryAnswerer()
     ├─ Check if AI is available
     │  └─ settings.is_ai_usable()
     │  └─ Needs GOOGLE_API_KEY + ENABLE_AI_CHAT
     
  2. Load metadata from registry
     └─ registry.get("smart-parking-lot")
     └─ Has: frameworks, dependencies, tech_stack
     
  3. Try to load RAG
     └─ _init_rag_for_repo("smart-parking-lot")
     └─ RAGVectorStore("smart-parking-lot").load_index()
     └─ If successful: used_rag = True
     └─ If fails: used_rag = False (fallback)
     
  4. Detect question intent
     └─ "technologies" → TECH_STACK intent
     
  5. Answer based on metadata
     ├─ With RAG+AI: "Based on code analysis: ..."
     ├─ With AI only: "This repository uses: ..."
     └─ Rule-based: "Detected frameworks: ..."
     
  6. Return response
     {
       "status": "success",
       "answer": "This repository uses Flask for backend...",
       "used_rag": true/false,
       "ai_mode": "Gemini" or "Rule-based"
     }
```

### Why Chat Fails on Render

```
Scenario: User analyzes repo, then chats
──────────────────────────────────────────

1. Analysis completes
   └─ Metadata saved: ./metadata_cache/smart-parking-lot.json ✓
   └─ RAG index saved: /tmp/ai-explainer/rag_indices/smart-parking-lot/ ✓
   └─ Response sent to frontend (analysis complete dialog)

2. Service memory state
   In-memory registry has: "smart-parking-lot" → metadata

3. ~30 seconds pass
   User reads analysis, then clicks chat

4. Chat request arrives
   └─ NEW HTTP REQUEST
   └─ Render might restart Python app (free tier)
   └─ OR connection routed to different container

5. New Python process initializes
   ├─ Load Flask app
   ├─ Create new RepositoryRegistry() [EMPTY]
   ├─ Try POST /api/query
   │  └─ registry.exists("smart-parking-lot")?
   │  └─ NO (memory was cleared)
   │  
   ├─ Load from disk: ./metadata_cache/smart-parking-lot.json
   │  └─ YES, this loads back
   │  
   ├─ Try RAGVectorStore("smart-parking-lot").load_index()
   │  └─ Look for /tmp/ai-explainer/rag_indices/smart-parking-lot/
   │  └─ NO ✗ /tmp was wiped
   │  
   └─ Fallback to rule-based (no AI + no code context)

Result: Chat sometimes works (if process stays alive) ✓
        Chat fails if process restarts (Render free tier) ✗
        Chat loses RAG context on Render (no AI code search) ✗
```

---

## 8. CURRENT ARCHITECTURE ISSUES

### Issue 1: Repository Name Mismatch (ALREADY FIXED)
- ✅ Clone returns (path, repo_name) tuple now
- ✅ Metadata registered with canonical name
- ⚠️  Chat still might not find it if registry empties

### Issue 2: No Smart Caching
- ❌ Always re-clones (inefficient)
- ❌ No way to use "cached" version
- ❌ Every analysis is full re-download

### Issue 3: RAG Index Not Persisted
- ❌ Stored in /tmp (ephemeral on Render)
- ❌ Lost on service restart
- ❌ Chat can't use RAG (falls back to rules)

### Issue 4: In-Memory Registry Gets Cleared
- ❌ Service restart = lost memory
- ⚠️  Metadata loads from disk, but RAG doesn't
- ❌ Chat is incomplete without RAG

### Issue 5: No Git Freshness Check
- ❌ Can't tell if local repo is stale
- ❌ No way to do smart "update" instead of "re-clone"
- ❌ Always analyzing same commit if clicked twice quickly

---

## 9. STEP-BY-STEP: What Happens With "hybrid-feed-system"

```
FIRST ANALYSIS
──────────────

User enters: https://github.com/YOU/hybrid-feed-system
Click Analyze

Backend:
  1. clone_repository()
     ├─ repo_name = "hybrid-feed-system"
     ├─ Clone to: /tmp/ai-explainer/repos/hybrid-feed-system/
     └─ ✓ Success
  
  2. scan_repository()
     ├─ Read from: /tmp/ai-explainer/repos/hybrid-feed-system/
     └─ Extract structure
  
  3-5. Detect frameworks, dependencies, diagrams
  
  6. index_code_for_rag()
     ├─ Extract code chunks
     ├─ Generate embeddings: ~10 seconds ⏳
     └─ Save to: /tmp/ai-explainer/rag_indices/hybrid-feed-system/
  
  7. registry.register("hybrid-feed-system", metadata)
     └─ Save to: ./metadata_cache/hybrid-feed-system.json
     └─ Keep in memory: registry["hybrid-feed-system"]

Frontend: "Analyzing..." dialog disappears ✓
Response: Metadata + diagrams returned
Chat: Available ✓


USER CLICKS CHAT
────────────────

Frontend sends:
  POST /api/query
  {
    "repository_name": "hybrid-feed-system",
    "question": "What's the tech stack?"
  }

Backend (same Python process still running):
  1. registry.exists("hybrid-feed-system")?
     └─ YES ✓ (in memory from analysis)
  
  2. registry.get("hybrid-feed-system")
     └─ Returns metadata
  
  3. _init_rag_for_repo("hybrid-feed-system")
     └─ RAGVectorStore("hybrid-feed-system").load_index()
     └─ Loads from: /tmp/ai-explainer/rag_indices/hybrid-feed-system/
     └─ ✓ FILES EXIST (just created 30 seconds ago)
  
  4. Answer question
     ├─ Detect intent: TECH_STACK
     ├─ Use RAG to find relevant code
     ├─ Use Gemini AI to explain
     └─ Return formatted answer

Chat: Works perfectly ✓


[RENDER RESTARTS or ~30min idle]


USER CLICKS CHAT AGAIN
─────────────────────

Python app restarts (new process)

Frontend sends SAME request:
  POST /api/query
  {
    "repository_name": "hybrid-feed-system",
    "question": "Can you explain the..." 
  }

Backend (NEW Python process):
  1. registry = RepositoryRegistry() [EMPTY]
  
  2. registry.exists("hybrid-feed-system")?
     └─ In-memory: NO ✗
     └─ Check disk: ./metadata_cache/hybrid-feed-system.json
     └─ YES ✓ LOADS FROM DISK

  3. registry.get("hybrid-feed-system")
     └─ Returns metadata ✓

  4. _init_rag_for_repo("hybrid-feed-system")
     └─ RAGVectorStore("hybrid-feed-system").load_index()
     └─ Looks for: /tmp/ai-explainer/rag_indices/hybrid-feed-system/
     └─ ✗ NOT FOUND (Render wiped /tmp on restart)
     └─ Returns None (RAG unavailable)

  5. Answer question
     ├─ Can't use RAG (no embeddings)
     ├─ Use Gemini with metadata only (limited)
     └─ Return answer without code context (weaker)

Chat: Partially works ⚠️ (no code context)
```

---

## SUMMARY TABLE

| Aspect | Local | Render (Current) | Status |
|--------|-------|------------------|--------|
| Repository storage | `./data/repos/` | `/tmp/.../repos/` | ✓ Works |
| Metadata caching | `./metadata_cache/` | `./metadata_cache/` | ✓ Persists |
| Re-clone on analyze | Always deletes old | Always deletes old | ✓ Consistent |
| Fresh commit check | None | None | ❌ Always old |
| RAG index location | `./data/rag_indices/` | `/tmp/.../rag_indices/` | ❌ Ephemeral |
| Chat after analysis | Works ✓ | Works first time ✓ | ⚠️ Fails after restart |
| Chat with RAG | Works ✓ | Works ✓ | ❌ Lost on restart |
| Repository name | Canonical | Canonical (fixed) | ✓ Fixed |

---

## KEY TAKEAWAYS

1. **Repos ARE stored, but NOT re-used**
   - Stored in `/tmp/` (cloud) or `./data/` (local)
   - Always deleted and re-cloned (not updated)
   - No smart caching or freshness checks

2. **Chat works when in-memory registry is alive**
   - Dies on service restart (Render)  
   - Metadata reloads, but RAG index doesn't (ephemeral /tmp)

3. **Chat needs persistent RAG storage**
   - Currently: `/tmp/` (lost on restart)
   - Should be: `./data/` (persisted)
   - Or: external vector DB (like Pinecone)

4. **Analyze keeps showing progress for RAG indexing**
   - 5-10 seconds for embeddings (sentence-transformers)
   - Happens EVERY analyze (not cached)
   - Can't Skip or avoid this

5. **Why deployment chat fails**
   - Render clears `/tmp` on service restart
   - Chat tries to load RAG from missing `/tmp` directory
   - Falls back to metadata-only answers
   - No code context = weaker AI answers
