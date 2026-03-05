# AI Codebase Explainer - Setup Guide

## Prerequisites

- Python 3.8 or higher
- Git
- pip (Python package manager)
- (Optional) OpenAI API key for AI-powered analysis

## Quick Start (5 minutes)

### 1. Clone/Navigate to Project
```bash
cd ai-codebase-explainer
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key if you have one
# Without it, the system will still work with fallback analysis
```

### 5. Run the Server
```bash
python -m uvicorn src.main:app --reload --port 8000
```

### 6. Test the API
Open your browser or use curl:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/fastapi/fastapi"}'
```

### 7. View Documentation
- Interactive Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## Detailed Setup

### Windows Setup

1. **Install Python**
   ```bash
   # Download from python.org or use Windows Package Manager
   winget install Python.Python.3.11
   ```

2. **Verify Installation**
   ```bash
   python --version
   pip --version
   ```

3. **Create Virtual Environment**
   ```bash
   python -m venv venv
   ```

4. **Activate Virtual Environment**
   ```bash
   venv\Scripts\activate
   # You should see (venv) in your terminal
   ```

5. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Verify Installation**
   ```bash
   python -c "from src.main import app; print('Success!')"
   ```

### macOS/Linux Setup

1. **Install Python (if needed)**
   ```bash
   # Using Homebrew on macOS
   brew install python3.11
   
   # Using apt on Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   ```

3. **Activate Virtual Environment**
   ```bash
   source venv/bin/activate
   # You should see (venv) in your terminal
   ```

4. **Install Dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration (Optional - for AI analysis)
OPENAI_API_KEY=sk-xxx...xxx

# Repository Configuration
REPO_CLONE_PATH=./data/repos
MAX_REPO_SIZE_MB=500
MAX_ANALYSIS_FILES=100

# API Configuration
DEBUG=false

# Model Configuration
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

### Without OpenAI API Key

The system works perfectly fine without an OpenAI API key. It will:
1. Still analyze repository structure
2. Still detect frameworks and languages
3. Generate rule-based architecture analysis
4. Return all results without AI-powered insights

To test this, simply don't add the `OPENAI_API_KEY` to your `.env` file.

---

## Running the Application

### Development Mode (with auto-reload)
```bash
python -m uvicorn src.main:app --reload --port 8000
```

### Production Mode
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Python directly
```bash
python src/main.py
```

---

## Docker Setup

### Build Docker Image
```bash
docker build -t ai-codebase-explainer .
```

### Run Docker Container
```bash
# Without OpenAI key
docker run -p 8000:8000 ai-codebase-explainer

# With OpenAI key
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-xxx \
  ai-codebase-explainer
```

### Using Docker Compose
```bash
# Create .env file with your configuration

# Start service
docker-compose up

# Stop service
docker-compose down

# View logs
docker-compose logs -f api
```

---

## Testing

### Run Test Suite
```bash
python test_system.py
```

This will:
- Test all modules independently
- Verify API models
- Display progress report
- Show system capabilities

### Test Specific Module
```bash
python -c "from src.modules.repo_scanner import RepositoryScanner; \
           print('Repository Scanner: OK')"
```

---

## Troubleshooting

### Issue: "No module named 'src'"
**Solution**: Make sure you're running from the project root directory
```bash
cd ai-codebase-explainer
python -m uvicorn src.main:app --reload
```

### Issue: Port 8000 already in use
**Solution**: Use a different port
```bash
python -m uvicorn src.main:app --reload --port 8001
```

### Issue: Git not found when cloning repositories
**Solution**: Install Git
```bash
# Windows
winget install Git.Git

# macOS
brew install git

# Ubuntu/Debian
sudo apt-get install git
```

### Issue: "OpenAI API key not configured"
**Solution**: This is just a warning. The system still works with fallback analysis.
To enable AI analysis, add your key to `.env`

### Issue: Virtual environment not activating
**Solution for Windows**: 
```bash
# Try this instead
.\venv\Scripts\Activate.ps1
# If still having issues, check ExecutionPolicy:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Invalid JSON in API response
**Solution**: Check that your request is valid
```bash
# Valid request
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/user/repo"}'

# Check JSON with:
python -m json.tool
```

---

## Development Workflow

### Adding a New Feature

1. Create a branch
   ```bash
   git checkout -b feature/new-feature
   ```

2. Modify the relevant module
   ```bash
   # Edit files in src/modules/ or src/api/
   ```

3. Update tests if needed
   ```bash
   # Edit test_system.py or create new test files
   ```

4. Test locally
   ```bash
   python test_system.py
   python -m uvicorn src.main:app --reload
   ```

5. Commit and push
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/new-feature
   ```

### Project Structure for Development
```
ai-codebase-explainer/
├── src/
│   ├── api/
│   │   ├── routes.py           # API endpoint definitions
│   │   └── __init__.py
│   ├── modules/
│   │   ├── repo_scanner.py     # Repository analysis
│   │   ├── framework_detector.py # Technology detection
│   │   ├── metadata_builder.py  # Data structuring
│   │   ├── ai_analyzer.py       # AI integration
│   │   └── __init__.py
│   ├── utils/
│   │   ├── config.py           # Configuration
│   │   ├── constants.py        # Constants
│   │   └── __init__.py
│   ├── main.py                 # FastAPI app entry
│   └── __init__.py
├── data/
│   └── repos/                  # Cloned repositories
├── test_system.py              # Test suite
├── requirements.txt            # Dependencies
├── .env.example                # Configuration template
├── README.md                   # Project documentation
├── SETUP.md                    # This file
├── ARCHITECTURE.md             # Architecture details
├── Dockerfile
└── docker-compose.yml
```

---

## Performance Tips

1. **Increase Max Files for Analysis**
   ```env
   MAX_ANALYSIS_FILES=500  # Default is 100
   ```

2. **Use Multiple Workers in Production**
   ```bash
   python -m uvicorn src.main:app --workers 4
   ```

3. **Configure AI Timeout**
   ```env
   OPENAI_MAX_TOKENS=1500  # Lower for faster responses
   ```

4. **Monitor Repository Cache**
   - Repositories are cloned to `./data/repos/`
   - Clean up old repos to save space
   - Set `REPO_CLONE_PATH` to a faster disk

---

## Security Considerations

1. **API Key Management**
   - Never commit `.env` file with real keys
   - Use environment variables in production
   - Rotate keys periodically

2. **Repository Analysis**
   - The system only performs read-only analysis
   - No code execution
   - No data extraction beyond metadata

3. **CORS Configuration**
   - Currently allows all origins (for development)
   - In production, restrict to trusted domains
   - See `src/main.py` for CORS settings

---

## Next Steps

After setup, you can:

1. **Analyze a Real Repository**
   ```bash
   curl -X POST http://localhost:8000/api/analyze \
     -H "Content-Type: application/json" \
     -d '{"repo_url":"https://github.com/your/repo"}'
   ```

2. **View API Documentation**
   - http://localhost:8000/api/docs

3. **Customize Framework Detection**
   - Edit `src/utils/constants.py`
   - Add new patterns to `FRAMEWORK_PATTERNS`

4. **Extend the System**
   - See ARCHITECTURE.md for extension points
   - Add new modules to `src/modules/`
   - Add new routes to `src/api/routes.py`

---

## Getting Help

- Check the README.md for overview
- See ARCHITECTURE.md for technical details
- Review test_system.py for usage examples
- Check USAGE_EXAMPLE.py for API examples

---

**Setup Version**: 1.0
**Last Updated**: March 4, 2026
