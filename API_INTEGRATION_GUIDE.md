# Frontend-Backend API Integration Guide

## Overview

The frontend communicates with the backend through **REST API endpoints** using the **Axios HTTP client**. All API calls are centralized in `lib/api.js` for easy management, error handling, and testing.

---

## API Client Architecture

### File: `lib/api.js`

**Purpose**: Centralized HTTP client with all backend endpoints

**Features**:
- Base URL configuration from environment
- Automatic error handling
- Request/response interceptors
- Timeout handling
- Type validation

### Base Configuration

```javascript
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})
```

**Environment Variable**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Available Endpoints

### 1. POST /api/analyze

**Purpose**: Analyze a GitHub repository

**Called From**: `RepositoryInput.js` → `pages/index.js`

**Request**:
```javascript
const response = await analyzeRepository(repoUrl)

// Sends:
{
  "repo_url": "https://github.com/owner/repo",
  "include_ai_analysis": true,
  "include_diagrams": true
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "repository_name": "repo",
  "message": "Repository analysis completed",
  "metadata": {
    "repository": {
      "name": "repo",
      "url": "https://github.com/owner/repo",
      "path": "/tmp/repo"
    },
    "analysis": {
      "file_count": 150,
      "primary_language": "Python",
      "languages": ["Python", "JavaScript", "Markdown"],
      "has_backend": true,
      "has_frontend": false
    },
    "frameworks": {
      "FastAPI": { "confidence": 0.95 },
      "Pydantic": { "confidence": 0.90 },
      "Uvicorn": { "confidence": 0.85 }
    },
    "tech_stack": ["Python", "FastAPI", "Pydantic"],
    "architecture_patterns": ["API-First", "Microservices"],
    "top_components": [
      {"name": "API", "type": "router"},
      {"name": "Database", "type": "service"}
    ]
  },
  "analysis": {
    "status": "success",
    "analysis": {
      "description": "FastAPI-based REST API...",
      "architecture": "Service-oriented...",
      "key_features": ["Async support", "Type hints", "API documentation"]
    }
  }
}
```

**Error Response** (400):
```json
{
  "detail": "Invalid GitHub URL format"
}
```

**Usage in Frontend**:
```javascript
const handleAnalyze = async (repoUrl) => {
  try {
    const result = await analyzeRepository(repoUrl)
    setMetadata(result.metadata)
    setAnalysis(result.analysis)
    // Fetch diagram next
  } catch (error) {
    setError(error.message)
  }
}
```

---

### 2. GET /api/diagrams/{repo_name}

**Purpose**: Retrieve architecture diagram in specified format

**Called From**: `pages/index.js` (after analyze)

**Request**:
```javascript
const response = await getDiagram(repoName, 'mermaid')

// URL becomes: /api/diagrams/repo?format=mermaid
```

**Query Parameters**:
| Parameter | Values | Default |
|-----------|--------|---------|
| `format` | mermaid, graphviz, json | mermaid |

**Response - Mermaid Format** (200 OK):
```json
{
  "repository_name": "repo",
  "format": "mermaid",
  "diagram": "graph TB\n  A[API Gateway] --> B[Service1]\n  A --> C[Service2]\n  B --> D[Database]\n  C --> D"
}
```

**Response - Graphviz Format**:
```json
{
  "repository_name": "repo",
  "format": "graphviz",
  "diagram": "digraph {\n  API -> Service1\n  API -> Service2\n  Service1 -> DB\n}"
}
```

**Response - JSON Format**:
```json
{
  "repository_name": "repo",
  "format": "json",
  "diagram": {
    "nodes": [
      {"id": "api", "label": "API Gateway", "type": "service"},
      {"id": "svc1", "label": "Service1", "type": "service"}
    ],
    "edges": [
      {"from": "api", "to": "svc1", "type": "calls"}
    ]
  }
}
```

**Error Response** (404):
```json
{
  "detail": "Repository 'unknown-repo' not found"
}
```

**Mermaid Rendering in Frontend**:
```javascript
const handleDiagramFetch = async (repoName) => {
  const result = await getDiagram(repoName, 'mermaid')
  
  // Store diagram code
  setDiagram(result.diagram)
  
  // ArchitectureDiagram.js useEffect will:
  // 1. Create <div class="mermaid">{diagram}</div>
  // 2. Call mermaid.contentLoaded()
  // 3. Render to SVG
}
```

---

### 3. POST /api/query

**Purpose**: Ask questions about repository architecture (Interactive Q&A)

**Called From**: `QuestionInput.js` → `pages/index.js`

**Request**:
```javascript
const response = await queryArchitecture(repositoryName, question)

// Sends:
{
  "repository_name": "fastapi",
  "question": "What is the main architecture pattern?"
}
```

**Response** (200 OK):
```json
{
  "status": "success",
  "repository_name": "fastapi",
  "question": "What is the main architecture pattern?",
  "answer": "FastAPI uses a service-oriented architecture with clear separation between routing, business logic, and data access layers. The main pattern is API-First with dependency injection.",
  "mode": "ai",
  "note": "Based on code analysis and AI reasoning"
}
```

**Alternative Response - Rule-Based**:
```json
{
  "status": "success",
  "repository_name": "fastapi",
  "question": "What frameworks are used?",
  "answer": "FastAPI (0.95), Pydantic (0.90), Uvicorn (0.85), Starlette (0.80)",
  "mode": "rule-based",
  "note": "Based on pattern matching and metadata analysis"
}
```

**Error Response** (400):
```json
{
  "detail": "Repository 'unknown' not found. Please analyze it first."
}
```

**Usage in Frontend**:
```javascript
const handleQuery = async (question) => {
  // Disabled if no repo loaded
  if (!metadata) return
  
  try {
    const result = await queryArchitecture(metadata.repository.name, question)
    
    setAnswer({
      text: result.answer,
      mode: result.mode,
      note: result.note,
      question: result.question
    })
  } catch (error) {
    setError(error.message)
  }
}
```

---

### 4. GET /api/health

**Purpose**: Check if API is available and healthy

**Called From**: `pages/index.js` (on component mount)

**Request**:
```javascript
const response = await healthCheck()
```

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

**Error Response** (Connection error):
```javascript
// No response = API unavailable
// Frontend catches error and shows "API Unavailable" message
```

**Usage in Frontend**:
```javascript
useEffect(() => {
  const checkHealth = async () => {
    try {
      await healthCheck()
      setApiAvailable(true)
    } catch {
      setApiAvailable(false)
    }
  }
  
  checkHealth()
  const interval = setInterval(checkHealth, 30000) // Check every 30s
  return () => clearInterval(interval)
}, [])
```

---

### 5. GET /api/info

**Purpose**: Get API service information

**Called From**: Optional (footer, or manual calls)

**Request**:
```javascript
const response = await getApiInfo()
```

**Response** (200 OK):
```json
{
  "service_name": "AI Codebase Explainer API",
  "version": "1.0.0",
  "description": "REST API for analyzing GitHub repositories with AI",
  "endpoints": [
    {
      "path": "/api/analyze",
      "method": "POST",
      "description": "Analyze a repository"
    },
    {
      "path": "/api/diagrams/{repo_name}",
      "method": "GET",
      "description": "Get architecture diagram"
    },
    {
      "path": "/api/query",
      "method": "POST",
      "description": "Ask questions about architecture"
    }
  ]
}
```

**Usage in Frontend**:
```javascript
const getServiceInfo = async () => {
  const info = await getApiInfo()
  console.log(`API Version: ${info.version}`)
  console.log(`Endpoints: ${info.endpoints.length}`)
}
```

---

## Error Handling

### Standard Error Structure

All errors follow this pattern:

```javascript
{
  "detail": "Error message describing what went wrong"
}
```

### Frontend Error Handling

**In lib/api.js**:
```javascript
export const analyzeRepository = async (repoUrl) => {
  try {
    const response = await apiClient.post('/api/analyze', {
      repo_url: repoUrl,
      include_ai_analysis: true,
      include_diagrams: true,
    })
    return response.data
  } catch (error) {
    const message = error.response?.data?.detail || 
                   error.message || 
                   'Failed to analyze repository'
    throw new Error(message)
  }
}
```

**In Components**:
```javascript
const handleAnalyze = async (repoUrl) => {
  try {
    // ... API call
  } catch (error) {
    setError(error.message)  // Display to user
  }
}
```

**User Sees**:
```
Error: Invalid GitHub URL format
```

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Cannot GET /api/health` | Backend not running | Start backend: `python -m uvicorn backend.main:app --reload` |
| `Invalid GitHub URL format` | Wrong URL format | Use: `https://github.com/owner/repo` |
| `Repository 'X' not found` | Repo doesn't exist or is private | Use public repository |
| `API Unavailable` | Network error | Check backend is running, check firewall |
| `Failed to fetch diagram` | Diagram generation failed | Repo might be too large |

---

## Request/Response Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Action                                  │
│              (Click "Analyze Repository")                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                 Frontend Component                                │
│            RepositoryInput.js                                    │
│         handleAnalyze(repoUrl)                                   │
└──────────────────────┬───────────────────────────────────────────┘
                       │
           ┌───────────┴────────────┐
           │                        │
           ▼                        ▼
      Validate URL         Call API Client
      (GitHub only)        analyzeRepository()
           │                        │
           └───────────┬────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    API Client (lib/api.js)    │
        │                              │
        │  1. Get API base URL         │
        │  2. Create request payload   │
        │  3. Send POST request        │
        │  4. Handle errors           │
        │  5. Return data or throw    │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    HTTP Request                │
        │  POST /api/analyze             │
        │                              │
        │  Body:                        │
        │  {                            │
        │    "repo_url": "...",         │
        │    "include_ai_analysis": ... │
        │  }                            │
        └──────────────┬───────────────┘
                       │
                       ▼ (Network)
        ┌──────────────────────────────┐
        │    Backend (FastAPI)          │
        │                              │
        │  1. Receive request          │
        │  2. Validate input           │
        │  3. Clone repository         │
        │  4. Analyze code             │
        │  5. Run AI models            │
        │  6. Build diagrams           │
        │  7. Return response          │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    HTTP Response (200 OK)     │
        │                              │
        │  Body:                        │
        │  {                            │
        │    "status": "success",      │
        │    "metadata": {...},        │
        │    "analysis": {...}         │
        │  }                            │
        └──────────────┬───────────────┘
                       │
                       ▼ (Network)
        ┌──────────────────────────────┐
        │    API Client (lib/api.js)    │
        │                              │
        │  1. Receive response         │
        │  2. Validate format          │
        │  3. Return response.data     │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    Frontend Component         │
        │    pages/index.js             │
        │                              │
        │  1. Receive data             │
        │  2. Update state:            │
        │     setMetadata()            │
        │     setAnalysis()            │
        │  3. Re-render components     │
        │  4. Show results             │
        │                              │
        │  Next: Fetch diagram...      │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    Diagram Fetch              │
        │  getDiagram(repoName, fmt)   │
        │                              │
        │  Sequence repeats for        │
        │  GET /api/diagrams/{repo}    │
        └──────────────────────────────┘
```

---

## Testing API Endpoints

### Using curl (Command Line)

**Test /api/analyze**:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi",
    "include_ai_analysis": true,
    "include_diagrams": true
  }'
```

**Test /api/health**:
```bash
curl http://localhost:8000/api/health
```

**Test /api/diagrams**:
```bash
curl "http://localhost:8000/api/diagrams/fastapi?format=mermaid"
```

**Test /api/query**:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "fastapi",
    "question": "What is the main pattern?"
  }'
```

### Using Browser Console

```javascript
// Test health endpoint
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(d => console.log(d))

// Test analyze endpoint
fetch('http://localhost:8000/api/analyze', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    repo_url: 'https://github.com/tiangolo/fastapi',
    include_ai_analysis: true
  })
})
  .then(r => r.json())
  .then(d => console.log(d))
```

### Using Frontend's API Client

```javascript
// In browser console on http://localhost:3000

// Import API client
import { analyzeRepository, healthCheck, getDiagram } from './lib/api'

// Test health
await healthCheck()

// Test analyze
const result = await analyzeRepository('https://github.com/tiangolo/fastapi')
console.log(result)

// Test diagram
const diagram = await getDiagram('fastapi', 'mermaid')
console.log(diagram)
```

---

## Adding New Endpoints

When backend adds new endpoints:

### Step 1: Add to lib/api.js

```javascript
export const newEndpoint = async (param1, param2) => {
  try {
    const response = await apiClient.post('/api/new-endpoint', {
      param1,
      param2,
    })
    return response.data
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Request failed')
  }
}
```

### Step 2: Use in Component

```javascript
import { newEndpoint } from '@/lib/api'

const handleNewAction = async () => {
  try {
    const result = await newEndpoint(val1, val2)
    setResult(result)
  } catch (error) {
    setError(error.message)
  }
}
```

### Step 3: Test

```bash
# Test endpoint directly
curl http://localhost:8000/api/new-endpoint

# Or test in frontend with browser console
import { newEndpoint } from './lib/api'
await newEndpoint(val1, val2)
```

---

## Performance Considerations

### Request Timing

| Operation | Typical Time | Notes |
|-----------|-------------|-------|
| Network roundtrip | 50-100ms | Localhost |
| Repository clone | 5-30s | Depends on size |
| Code analysis | 2-10s | AI analysis |
| Diagram generation | 1-3s | Graph rendering |
| Q&A query | 2-8s | AI response time |
| **Total end-to-end** | **10-50s** | Varies by repo |

### Optimization Tips

1. **Cache responses**: Store results for same repo
2. **Parallel requests**: Fetch diagram while analysis completes
3. **Lazy load**: Only fetch what user requests
4. **Pagination**: For large result sets

---

## CORS & Security

### CORS Headers

Backend must allow frontend requests:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Frontend Config

Environment variable sets allowed origin:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Security Best Practices

1. ✅ No credentials in requests (backend handles)
2. ✅ HTTPS in production (use https://api.example.com)
3. ✅ Validate all user input before sending
4. ✅ Don't expose sensitive data in frontend

---

## Debugging API Issues

### Enable Request Logging

Add to lib/api.js:

```javascript
apiClient.interceptors.request.use(request => {
  console.log('API Request:', request.method.toUpperCase(), request.url)
  console.log('Body:', request.data)
  return request
})

apiClient.interceptors.response.use(response => {
  console.log('API Response:', response.status, response.data)
  return response
}, error => {
  console.log('API Error:', error.response?.status, error.response?.data)
  throw error
})
```

### Check Network Tab

In browser DevTools:
1. Open Inspector (F12)
2. Go to **Network** tab
3. Perform action
4. Click request to see:
   - **Headers**: Method, URL, status
   - **Request**: Payload sent
   - **Response**: Data received
   - **Timing**: Performance metrics

### Test Endpoint Directly

```bash
# Direct backend test (bypasses frontend)
curl -v http://localhost:8000/api/analyze \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/user/repo"}'
```

---

## Summary

The API integration layer provides:

✅ **Centralized client** in `lib/api.js` with all endpoints
✅ **Error handling** with meaningful messages
✅ **Easy testing** via curl, fetch, or browser console
✅ **Type safety** with request/response validation
✅ **Performance** with proper timeouts and caching
✅ **Security** with CORS and input validation

All components use the same API client, making the codebase consistent, maintainable, and easy to test.

---

## API Reference Summary

| Endpoint | Method | Purpose | Component |
|----------|--------|---------|-----------|
| `/api/analyze` | POST | Analyze repository | RepositoryInput |
| `/api/diagrams/{repo}` | GET | Get diagram | Dashboard |
| `/api/query` | POST | Q&A | QuestionInput |
| `/api/health` | GET | Health check | Dashboard |
| `/api/info` | GET | API info | Footer |

For detailed endpoint documentation, see the [FRONTEND_ARCHITECTURE_REPORT.md](FRONTEND_ARCHITECTURE_REPORT.md).
