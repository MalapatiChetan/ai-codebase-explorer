# Q&A API Quick Reference

## Endpoint

```
POST /api/query
```

## Request Format

```json
{
  "repository_name": "string - name of analyzed repository",
  "question": "string - your question about the repository"
}
```

## Response Format

```json
{
  "status": "success|error",
  "repository": "repository name",
  "question": "your question",
  "answer": "detailed answer",
  "mode": "ai|rule-based",
  "note": "optional additional note"
}
```

## Usage Examples

### 1. Analyze Repository
**First, analyze the repository:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/tiangolo/fastapi"
  }'
```

### 2. Ask Questions

#### Question: What is this project?
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "fastapi",
    "question": "What is this project?"
  }'
```

Response:
```json
{
  "status": "success",
  "repository": "fastapi",
  "question": "What is this project?",
  "answer": "fastapi is a backend service built with Python. It appears to use FastAPI. The repository contains 150 files across multiple modules.",
  "mode": "rule-based"
}
```

#### Question: How is it structured?
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "fastapi",
    "question": "How is this project structured?"
  }'
```

Response:
```json
{
  "status": "success",
  "repository": "fastapi",
  "question": "How is this project structured?",
  "answer": "The fastapi project is organized into several key components:\n\n1. **main** (module): Contains 25 files\n2. **routers** (module): Contains 15 files\n3. **models** (module): Contains 20 files\n\nArchitectural patterns identified: API-First, Microservices",
  "mode": "rule-based"
}
```

#### Question: What technologies are used?
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "fastapi",
    "question": "What technologies are used?"
  }'
```

Response:
```json
{
  "status": "success",
  "repository": "fastapi",
  "question": "What technologies are used?",
  "answer": "**Technology Stack for fastapi:**\n\nCore Technologies: Python, FastAPI, Uvicorn, Pydantic\n\nFrameworks (by confidence):\n- FastAPI: 95%\n- Pydantic: 90%\n- Starlette: 85%\n\nPrimary Language: Python",
  "mode": "rule-based"
}
```

#### Question: What are the main components?
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "repository_name": "fastapi",
    "question": "What are the main components?"
  }'
```

## Question Categories

The system recognizes and answers these types of questions:

| Category | Example Questions | Info |
|----------|-------------------|------|
| **Project Overview** | "What is this?", "What does it do?" | Project type, purpose |
| **Architecture** | "How is it structured?", "Architecture pattern?" | System design, patterns |
| **Technology** | "What tech stack?", "Technologies used?" | Frameworks, tools, languages |
| **Frameworks** | "What frameworks?", "Which libraries?" | Detected frameworks |
| **Components** | "What are components?", "Modules?" | System components/layers |
| **Frontend** | "Has UI?", "Frontend?" | Frontend information |
| **Backend** | "Has backend?", "API?" | Backend information |
| **Dependencies** | "What dependencies?", "Packages?" | Library/package info |

## Error Responses

### Repository Not Found
```json
{
  "status": "error",
  "detail": "Repository 'unknown-repo' has not been analyzed. Please analyze it first using POST /api/analyze"
}
```

### Empty Question
```json
{
  "status": "error",
  "detail": "Question cannot be empty"
}
```

### Server Error
```json
{
  "status": "error",
  "detail": "Query failed: [error details]"
}
```

## Python SDK Example

```python
import requests

# Configure
API_BASE = "http://localhost:8000"
REPO_NAME = "fastapi"

# Ask a question
response = requests.post(
    f"{API_BASE}/api/query",
    json={
        "repository_name": REPO_NAME,
        "question": "What is the architecture of this project?"
    }
)

# Parse response
data = response.json()
if response.status_code == 200:
    print(f"Answer: {data['answer']}")
    print(f"Mode: {data['mode']}")
else:
    print(f"Error: {data['detail']}")
```

## JavaScript/Node.js Example

```javascript
// Query the API
async function askAboutRepository(repoName, question) {
  const response = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_name: repoName,
      question: question
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    console.log(`Q: ${data.question}`);
    console.log(`A: ${data.answer}`);
    console.log(`Mode: ${data.mode}`);
  } else {
    console.error(`Error: ${data.detail}`);
  }
}

// Usage
askAboutRepository('fastapi', 'What is the main purpose of this project?');
```

## API Response Modes

### AI Mode (requires OpenAI API key)
```json
{
  "mode": "ai",
  "answer": "FastAPI is a modern, fast web framework for building APIs with Python..."
}
```

### Rule-Based Mode (always available)
```json
{
  "mode": "rule-based",
  "answer": "fastapi is a backend service built with Python...",
  "note": "This answer was generated using pattern matching. For AI-powered insights, configure an OpenAI API key."
}
```

## Tips

1. **Analyze First**: Always run `/api/analyze` before querying
2. **Use Exact Names**: Repository names are case-sensitive
3. **Natural Language**: Questions can be informal and natural
4. **AI Quality**: For best results, set OPENAI_API_KEY environment variable
5. **Fallback Happens**: System automatically falls back to rule-based if AI fails
6. **No Limits**: Ask as many questions as you want

## Configuration

```bash
# Enable AI mode (optional)
export OPENAI_API_KEY="sk-..."

# Set model (optional)
export OPENAI_MODEL="gpt-4"

# Set cache location (optional)
export METADATA_CACHE_DIR="./metadata_cache"
```

## Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | success | Question answered successfully |
| 400 | error | Bad request (empty question, malformed JSON) |
| 404 | error | Repository not found or not analyzed |
| 500 | error | Server error during query processing |

## Performance

- **Rule-based answers**: <200ms
- **AI answers**: 2-10 seconds (network dependent)
- **Registry lookups**: <1ms (in-memory)

## Limits

- **Question length**: None (but longer questions may timeout)
- **Answer length**: Max 1000 tokens (AI mode)
- **Repositories**: Unlimited
- **Queries**: Unlimited (rate-limited by your API server)

## Support

For issues or questions:
1. Check repository is analyzed with `/api/analyze`
2. Verify repository name matches
3. Check error message for details
4. Enable logging for debugging
