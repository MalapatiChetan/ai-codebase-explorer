# AI Codebase Explainer - Architecture Documentation

## System Overview

The AI Codebase Explainer is a comprehensive system for analyzing GitHub repositories and generating developer-friendly architecture documentation. It combines repository scanning, framework detection, and AI-powered analysis to provide deep insights into any public GitHub project.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    User/Client Layer                         │
│                    (REST API / UI)                           │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              API Routes (routes.py)                  │   │
│  │ • POST /api/analyze - Main analysis endpoint        │   │
│  │ • GET /api/health - Health check                    │   │
│  │ • GET /api/info - Service information               │   │
│  └────────────────┬─────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                 Analysis Pipeline                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  1. Repository Scanner Module (repo_scanner.py)     │   │
│  │  ├─ Clone GitHub repositories                       │   │
│  │  ├─ Scan file structure recursively                 │   │
│  │  ├─ Collect file metadata                           │   │
│  │  └─ Detect file extensions and languages            │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  2. Framework Detector Module (framework_detector)  │   │
│  │  ├─ Pattern-based framework detection               │   │
│  │  ├─ Confidence scoring                              │   │
│  │  ├─ Primary language identification                 │   │
│  │  ├─ Architecture pattern detection                  │   │
│  │  └─ Dependency file parsing                         │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  3. Metadata Builder Module (metadata_builder.py)   │   │
│  │  ├─ Combine scanner and detector results            │   │
│  │  ├─ Module identification and classification        │   │
│  │  ├─ Tech stack compilation                          │   │
│  │  └─ Important file extraction                       │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  4. AI Analyzer Module (ai_analyzer.py)             │   │
│  │  ├─ OpenAI integration (pluggable)                  │   │
│  │  ├─ Analysis prompt generation                      │   │
│  │  ├─ Response parsing and structuring                │   │
│  │  └─ Fallback rule-based analysis                    │   │
│  └─────────────────┬───────────────────────────────────┘   │
│                    │                                         │
│  ┌─────────────────▼───────────────────────────────────┐   │
│  │  Result Compilation & Return                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Module Architecture

### 1. Repository Scanner (`src/modules/repo_scanner.py`)

**Responsibility**: Clone repositories and scan file structure

**Key Methods**:
- `extract_repo_name(repo_url)` - Parse repository name from GitHub URL
- `clone_repository(repo_url)` - Clone a repository using GitPython
- `scan_repository(repo_path)` - Recursively scan directory structure
- `should_skip_path(path, skip_dirs)` - Filter out unwanted directories
- `get_file_content(repo_path, file_rel_path)` - Read file contents

**Features**:
- Handles both HTTPS and SSH GitHub URLs
- Smart directory filtering (skips .git, node_modules, __pycache__)
- Collects file metadata (path, extension, size)
- Language detection from file extensions
- Backend/Frontend indicator detection
- Configurable analysis depth (max files)

**Data Output**:
```python
{
    "repo_path": "/path/to/repo",
    "repo_name": "project-name",
    "files": [
        {"path": "src/main.py", "name": "main.py", "extension": ".py", "size_bytes": 1024},
        ...
    ],
    "file_count": 50,
    "languages": {"py": 30, "js": 15, "json": 5},
    "has_backend": True,
    "has_frontend": True,
    "root_files": ["README.md", "package.json", ...]
}
```

### 2. Framework Detector (`src/modules/framework_detector.py`)

**Responsibility**: Detect frameworks, languages, and technology stack

**Key Methods**:
- `detect_frameworks(repo_metadata)` - Identify frameworks with confidence scores
- `get_primary_language(repo_metadata)` - Determine main language
- `detect_architecture_patterns(repo_metadata)` - Identify architectural styles
- `get_tech_stack(detected_frameworks, primary_language)` - Build technology list
- `analyze_dependencies(repo_path, repo_metadata)` - Parse dependency files
- `get_service_count_estimate(repo_metadata)` - Estimate number of services

**Detection Strategy**:
- Pattern-based matching against framework signatures
- Confidence scoring (0.0 to 1.0)
- Multiple indicators per framework
- Support for 20+ frameworks (React, Vue, Angular, FastAPI, Django, etc.)

**Detected Patterns**:
- File presence (e.g., "package.json" → Node.js/React)
- File extensions (e.g., ".jsx" → React)
- File content patterns (e.g., "package.json:react" in dependencies)
- Architecture indicators (docker-compose.yml → microservices)

**Data Output**:
```python
{
    "React": {"confidence": 0.85, "matched_patterns": ["package.json:react", "*.jsx"]},
    "FastAPI": {"confidence": 0.80, "matched_patterns": ["requirements.txt:fastapi"]},
    ...
}
```

### 3. Metadata Builder (`src/modules/metadata_builder.py`)

**Responsibility**: Orchestrate analysis and structure all findings

**Key Methods**:
- `build_metadata(repo_url)` - Main orchestration method
- `_identify_modules(scan_metadata)` - Identify top-level components
- `_determine_module_type(dir_name, extensions)` - Classify module types
- `_extract_important_files(scan_metadata)` - Find key config/doc files
- `get_summary(metadata)` - Generate quick overview

**Module Classification**:
- Backend Service (api/, backend/, service/)
- Frontend (ui/, frontend/, components/)
- Configuration (config/, settings/)
- Tests (test/, specs/)
- Documentation (docs/)
- Build/Tools (tools/, build/, scripts/)
- Based on file extensions (.py = Backend, .jsx = Frontend)

**Data Output**:
```python
{
    "repository": {"url": "...", "name": "...", "path": "..."},
    "analysis": {
        "file_count": 100,
        "primary_language": "Python",
        "languages": {...},
        "has_backend": True,
        "has_frontend": True
    },
    "frameworks": {...},
    "tech_stack": ["Python", "FastAPI", "React"],
    "architecture_patterns": ["API-First", "Monolithic"],
    "dependencies": {...},
    "modules": [
        {"name": "src", "type": "Backend Logic", "file_count": 45, "extensions": [".py"]},
        ...
    ],
    "root_files": [...],
    "important_files": [...]
}
```

### 4. AI Analyzer (`src/modules/ai_analyzer.py`)

**Responsibility**: Generate high-level architecture insights

**Key Methods**:
- `analyze(metadata)` - Main analysis method
- `_build_analysis_prompt(metadata)` - Generate comprehensive analysis prompt
- `_parse_analysis_response(response_text, metadata)` - Structure response
- `_generate_fallback_analysis(metadata)` - Rule-based fallback

**Features**:
- OpenAI integration (models: gpt-4, gpt-3.5-turbo configurable)
- Structured prompt engineering
- Response section parsing
- Smart fallback when API unavailable
- Configuration via environment variables

**Analysis Sections**:
1. **System Overview** - High-level project description
2. **Core Components** - Main modules and responsibilities
3. **Architecture Pattern** - Identified architectural style
4. **Data Flow** - How data moves through system
5. **Technology Assessment** - Framework and tool evaluation
6. **Key Observations** - Interesting architectural decisions
7. **Suggested Improvements** - Potential enhancements

**Data Output**:
```python
{
    "status": "success",
    "analysis": {
        "raw_analysis": "Full analysis text...",
        "system_overview": "...",
        "core_components": "...",
        "architecture_pattern": "...",
        "data_flow": "...",
        ...
    }
}
```

## API Layer

### Route Handler (`src/api/routes.py`)

**Endpoints**:

#### POST /api/analyze
- **Purpose**: Analyze a GitHub repository
- **Request Body**:
  ```json
  {
    "repo_url": "https://github.com/user/repo",
    "include_ai_analysis": true
  }
  ```
- **Response**: Complete metadata and AI analysis
- **Error Handling**: 
  - 400: Invalid GitHub URL
  - 500: Analysis failure

#### GET /api/health
- **Purpose**: Health check
- **Response**: Status and service info

#### GET /api/info
- **Purpose**: Service information
- **Response**: Version, description, endpoints

### Main Application (`src/main.py`)

**Features**:
- FastAPI application setup
- CORS middleware configuration
- Router registration
- Startup/shutdown event handlers
- Custom OpenAPI schema
- Logging configuration
- Error handling

## Data Flow

```
User submits GitHub URL
        ↓
API validates URL
        ↓
Repository Scanner
├─ Clone repo
├─ Scan file structure
├─ Collect metadata
└─ Detect languages
        ↓
Framework Detector
├─ Pattern matching
├─ Score frameworks
├─ Detect patterns
└─ Parse dependencies
        ↓
Metadata Builder
├─ Orchestrate results
├─ Identify modules
├─ Compile tech stack
└─ Structure data
        ↓
AI Analyzer
├─ (OpenAI call if configured)
├─ Or fallback to rules
└─ Structure response
        ↓
API Response
└─ Return complete analysis
```

## Configuration

### Environment Variables (`src/utils/config.py`)

- `OPENAI_API_KEY` - OpenAI API key (optional)
- `OPENAI_MODEL` - Default: "gpt-4"
- `OPENAI_TEMPERATURE` - Default: 0.7
- `OPENAI_MAX_TOKENS` - Default: 2000
- `REPO_CLONE_PATH` - Default: "./data/repos"
- `MAX_REPO_SIZE_MB` - Default: 500
- `MAX_ANALYSIS_FILES` - Default: 100
- `SKIP_DIRS` - Directories to skip during scanning

### Constants (`src/utils/constants.py`)

- `FRAMEWORK_PATTERNS` - Framework detection patterns
- `FILE_IMPORTANCE` - File importance weights
- `BACKEND_INDICATORS` - Backend component markers
- `FRONTEND_INDICATORS` - Frontend component markers

## Design Patterns

### 1. **Pluggable Architecture**
- AI analyzer can work with or without OpenAI
- Framework detection is pattern-based (easy to extend)
- Modular design allows easy feature addition

### 2. **Single Responsibility Principle**
- Each module has one clear purpose
- Scanner scans, detector detects, builder builds, analyzer analyzes
- API layer handles only HTTP concerns

### 3. **Data Pipeline Pattern**
- Each step feeds into the next
- Results are accumulated in metadata
- Clear handoffs between components

### 4. **Fallback Strategy**
- AI analysis has fallback to rule-based
- Graceful degradation when API unavailable
- System remains functional without OpenAI

### 5. **Configuration Management**
- Environment-based configuration
- Pydantic settings for validation
- Easy customization

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | FastAPI |
| **Server** | Uvicorn (ASGI) |
| **Repository Management** | GitPython |
| **Data Validation** | Pydantic |
| **Configuration** | Python-dotenv |
| **AI** | OpenAI API |
| **Language** | Python 3.8+ |

## Performance Considerations

1. **File Analysis**
   - Limited to 100 files by default (configurable)
   - Skips large directories (.git, node_modules)
   - Efficient relative path calculation

2. **Memory**
   - Streaming file reads (not loading entire repos)
   - Limited file exploration depth
   - Summary-based metadata storage

3. **Network**
   - Asynchronous request handling
   - Configurable AI request sizes
   - Efficient GitHub cloning

## Security Considerations

1. **Input Validation**
   - URL validation (GitHub URLs only)
   - Pydantic model validation for requests
   - Path traversal prevention

2. **Repository Handling**
   - Local cloning in isolated directory
   - Read-only analysis
   - No credential storage

3. **API Security**
   - CORS configuration
   - Error handling (no info leakage)
   - Environment variable for secrets

## Extensibility

### Adding Framework Detection
1. Add patterns to `FRAMEWORK_PATTERNS` in constants
2. Pattern format: `{"Framework Name": ["pattern1", "pattern2", ...]}`

### Adding File Analysis
1. Extend `scan_repository()` in repo_scanner
2. Add new metadata fields
3. Update metadata builder

### Adding Architecture Patterns
1. Extend `detect_architecture_patterns()` in framework_detector
2. Add detection logic
3. Update analysis prompt

### Custom AI Analysis
1. Extend AI analyzer with new prompt templates
2. Add section parsing
3. Implement custom fallback logic

## Deployment Options

### Local Development
```bash
python -m uvicorn src.main:app --reload
```

### Docker
```bash
docker build -t ai-codebase-explainer .
docker run -p 8000:8000 ai-codebase-explainer
```

### Docker Compose
```bash
docker-compose up
```

### Cloud Deployment
- AWS ECS, Lambda, or EC2
- Google Cloud Run
- Azure Container Instances
- Heroku (with custom buildpack)

## Testing Strategy

- Unit tests for each module
- Integration tests for pipeline
- Integration with real repositories
- Performance benchmarking

## Future Enhancements

1. **Advanced Analysis**
   - Code complexity metrics
   - Performance bottleneck detection
   - Security vulnerability scanning
   - Dependency version analysis

2. **Visualization**
   - Architecture diagrams
   - Component dependency graphs
   - Tech stack visualization

3. **Persistence**
   - Database caching
   - Results history
   - Repository tracking

4. **Automation**
   - Scheduled analysis
   - CI/CD integration
   - Webhook support

5. **UI**
   - Web dashboard
   - Real-time analysis
   - Comparison tools

---

**Architecture Version**: 1.0
**Last Updated**: March 4, 2026
**Status**: Production Ready
