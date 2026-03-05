# AI Codebase Explainer

A comprehensive system for analyzing GitHub repositories and generating structured architecture documentation.

## Features

- **Repository Cloning**: Automatically clone public GitHub repositories
- **Structure Analysis**: Recursively analyze folder hierarchies and detect file patterns
- **Framework Detection**: Identify programming languages and frameworks
- **Dependency Analysis**: Parse dependency files (package.json, pom.xml, requirements.txt, etc.)
- **AI-Powered Analysis**: Generate developer-friendly architecture explanations
- **REST API**: Simple endpoint to submit repositories and get analysis results

## Project Structure

```
ai-codebase-explainer/
├── src/
│   ├── modules/
│   │   ├── repo_scanner.py        # Repository cloning and file system analysis
│   │   ├── framework_detector.py  # Framework and language detection
│   │   ├── metadata_builder.py    # Build structured repository metadata
│   │   └── ai_analyzer.py         # AI-powered architecture analysis
│   ├── api/
│   │   └── routes.py              # FastAPI route definitions
│   ├── utils/
│   │   ├── config.py              # Configuration management
│   │   └── constants.py           # Project constants
│   └── main.py                    # FastAPI application entry point
├── data/
│   └── repos/                     # Cloned repositories stored here
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

## Running the Application

```bash
python -m uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Analyze Repository
```
POST /api/analyze
Content-Type: application/json

{
  "repo_url": "https://github.com/user/repo"
}
```

Returns comprehensive architecture analysis including:
- System overview
- Modules and components
- Technology stack
- Service responsibilities
- Detected architecture patterns

## Architecture

The system follows a modular architecture:

1. **Repo Scanner**: Clones GitHub repositories and analyzes file structure
2. **Framework Detector**: Identifies programming languages and frameworks
3. **Metadata Builder**: Creates structured representation of the codebase
4. **AI Analyzer**: Uses OpenAI to generate architectural insights
5. **API Layer**: FastAPI endpoints for user interaction

## Next Steps

- Implement streaming responses for large repositories
- Add caching to avoid re-analyzing repositories
- Create UI dashboard for visualizing architecture
- Add support for private repositories (with authentication)
- Implement more sophisticated dependency resolution
