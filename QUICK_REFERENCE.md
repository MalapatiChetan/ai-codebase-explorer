# AI Codebase Explainer - Quick Reference

## 🚀 Quick Start (60 seconds)

```bash
# 1. Setup
cd ai-codebase-explainer
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

# 2. Install
pip install -r requirements.txt

# 3. Run
python -m uvicorn src.main:app --reload

# 4. Test
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/fastapi/fastapi"}'
```

## 📁 Project Structure

```
src/
├── main.py                 # FastAPI app
├── api/routes.py          # HTTP endpoints
├── modules/
│   ├── repo_scanner.py     # Clone & scan
│   ├── framework_detector.py # Detect tech
│   ├── metadata_builder.py  # Structure data
│   └── ai_analyzer.py      # AI analysis
└── utils/
    ├── config.py           # Configuration
    └── constants.py        # Patterns & constants
```

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/analyze` | Analyze a repo |
| GET | `/api/health` | Health check |
| GET | `/api/info` | Service info |
| GET | `/api/docs` | Swagger UI |

## 📊 API Request/Response

### Request
```json
{
  "repo_url": "https://github.com/user/repo",
  "include_ai_analysis": true
}
```

### Response
```json
{
  "status": "success",
  "repository_name": "repo",
  "metadata": {
    "repository": {...},
    "analysis": {...},
    "frameworks": {...},
    "tech_stack": [...],
    "modules": [...]
  },
  "analysis": {
    "status": "success",
    "analysis": {
      "raw_analysis": "..."
    }
  }
}
```

## 🛠️ Configuration

Create `.env` file:
```env
OPENAI_API_KEY=sk-xxx...xxx  # Optional
REPO_CLONE_PATH=./data/repos
DEBUG=false
```

## 🧪 Testing

```bash
# Run all tests
python test_system.py

# Test specific module
python -c "from src.modules.repo_scanner import RepositoryScanner; print('OK')"
```

## 🐳 Docker

```bash
# Build
docker build -t ai-codebase-explainer .

# Run
docker run -p 8000:8000 ai-codebase-explainer

# Or with Compose
docker-compose up
```

## 📚 Key Modules

### RepositoryScanner
```python
from src.modules.repo_scanner import RepositoryScanner

scanner = RepositoryScanner()
repo_path = scanner.clone_repository(url)
metadata = scanner.scan_repository(repo_path)
```

### FrameworkDetector
```python
from src.modules.framework_detector import FrameworkDetector

detector = FrameworkDetector()
frameworks = detector.detect_frameworks(metadata)
language = detector.get_primary_language(metadata)
```

### RepositoryMetadataBuilder
```python
from src.modules.metadata_builder import RepositoryMetadataBuilder

builder = RepositoryMetadataBuilder()
metadata = builder.build_metadata(repo_url)
summary = builder.get_summary(metadata)
```

### AIArchitectureAnalyzer
```python
from src.modules.ai_analyzer import AIArchitectureAnalyzer

analyzer = AIArchitectureAnalyzer()
analysis = analyzer.analyze(metadata)
```

## 🔍 Framework Detection Patterns

Supported frameworks (20+):
- **Frontend**: React, Vue, Angular, Next.js
- **Backend**: FastAPI, Django, Flask, Express, Spring Boot
- **Infrastructure**: Docker, Kubernetes
- **Languages**: Python, JavaScript, TypeScript, Java, Go, Rust

## 🎯 Architecture Patterns Detected

- Microservices (docker-compose.yml)
- Monolithic (has backend + frontend)
- API-First (api directories)
- MVC (controller/model/view)
- Serverless (serverless.yml, lambda)
- Plugin-based (plugin directories)

## 📋 Framework Pattern Format

In `src/utils/constants.py`:
```python
FRAMEWORK_PATTERNS = {
    "Framework": [
        "package.json:framework",  # File content pattern
        "*.extension",             # File extension pattern
        "directory/file",          # File/directory pattern
    ],
    ...
}
```

## 🔐 Security Features

- URL validation (GitHub only)
- Read-only analysis
- No code execution
- No credential storage
- Input validation with Pydantic

## 📈 Performance Tips

```env
# Analyze more files
MAX_ANALYSIS_FILES=200

# Faster AI responses
OPENAI_MAX_TOKENS=1000

# Production workers
# python -m uvicorn src.main:app --workers 4
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `--port 8001` |
| Module not found | Run from project root |
| Git not found | Install Git |
| No OpenAI key | Works with fallback |

## 📖 Documentation

- **README.md** - Overview
- **SETUP.md** - Installation guide
- **ARCHITECTURE.md** - System design
- **PROJECT_SUMMARY.md** - Complete summary
- **test_system.py** - Test suite

## ⚡ Common Commands

```bash
# Development
python -m uvicorn src.main:app --reload

# Production
python -m uvicorn src.main:app --host 0.0.0.0 --workers 4

# Testing
python test_system.py

# Check imports
python -c "from src.main import app; print('OK')"

# View logs
docker-compose logs -f api
```

## 🔄 Data Flow

```
User Input (URL)
    ↓
Repository Scanner (Clone + Scan)
    ↓
Framework Detector (Identify Tech)
    ↓
Metadata Builder (Structure Data)
    ↓
AI Analyzer (Generate Insights)
    ↓
API Response (Return Results)
```

## 💡 Extension Points

1. **Add Framework**: Update FRAMEWORK_PATTERNS
2. **New Analysis**: Extend AI Analyzer
3. **New Endpoint**: Add to routes.py
4. **Custom Detection**: Extend FrameworkDetector

## 🌐 Environment Variables

```env
# AI
OPENAI_API_KEY           # OpenAI API key
OPENAI_MODEL             # Default: gpt-4
OPENAI_TEMPERATURE       # Default: 0.7
OPENAI_MAX_TOKENS        # Default: 2000

# Repo Analysis
REPO_CLONE_PATH          # Default: ./data/repos
MAX_REPO_SIZE_MB         # Default: 500
MAX_ANALYSIS_FILES       # Default: 100

# API
DEBUG                    # Default: false
API_TITLE                # Default: AI Codebase Explainer
API_VERSION              # Default: 0.1.0
```

## 📞 Support Resources

- **Issues**: Check troubleshooting in SETUP.md
- **Architecture**: See ARCHITECTURE.md
- **Usage**: Review USAGE_EXAMPLE.py
- **Tests**: Run test_system.py

---

**Quick Reference Version**: 1.0  
**Last Updated**: March 4, 2026
