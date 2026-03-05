# Configuration & Credentials Guide

This document explains all the credentials and configuration options available in the AI Codebase Explainer, including new features for diagram generation, GitHub authentication, and database caching.

## Table of Contents

1. [OpenAI API Key](#openai-api-key)
2. [GitHub Personal Access Token](#github-personal-access-token)
3. [Database Configuration](#database-configuration)
4. [Async Processing & Task Queue](#async-processing--task-queue)
5. [Diagram Generation Settings](#diagram-generation-settings)
6. [Environment Setup Instructions](#environment-setup-instructions)

---

## OpenAI API Key

### Purpose
Used for AI-powered architecture analysis. The system generates detailed insights about repository architecture, technology choices, and recommended improvements.

### Is it Required?
**No** - The system works without it, but provides rule-based analysis instead of AI-powered insights.

### How to Obtain
1. Go to [OpenAI Platform](https://platform.openai.com/account/api-keys)
2. Sign in with your OpenAI account (or create one)
3. Navigate to "API keys"
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)
6. **Keep it private** - never commit to git

### Configuration
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4          # or gpt-3.5-turbo for faster/cheaper
OPENAI_TEMPERATURE=0.7      # 0.0-1.0, lower = more deterministic
OPENAI_MAX_TOKENS=2000      # Response length limit
```

### Pricing
- GPT-4: ~$0.03 per 1K input tokens, ~$0.06 per 1K output tokens
- GPT-3.5-turbo: ~$0.0015 per 1K input tokens, ~$0.002 per 1K output tokens

---

## GitHub Personal Access Token

### Purpose
Enables analysis of **private GitHub repositories**. Without it, only public repositories can be analyzed.

### Is it Required?
**No** - Only needed if you want to analyze private repositories.

### How to Obtain

1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a name (e.g., "AI Codebase Explainer")
4. Set expiration (recommended: 30-90 days for security)
5. Select minimal required scopes:
   - `repo` (for private repository access)
   - `read:org` (optional, if analyzing org repositories)
6. Click "Generate token"
7. Copy the token immediately (you won't see it again)
8. **Keep it private** - never commit to git

### Configuration
```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=your_github_username
```

### Permissions Explanation
- **`repo`** - Allows reading private repository code and metadata
- **`read:org`** - Allows accessing organization repositories (optional)
- **No write access granted** - The system only reads, never modifies

### Alternative: OAuth Flow
For production applications, consider implementing OAuth instead of storing tokens. See [GitHub OAuth Documentation](https://docs.github.com/en/apps/oauth-apps).

---

## Database Configuration

### Purpose
Enables **caching of analysis results** to avoid re-analyzing the same repository. Dramatically speeds up repeated analyses.

### Is it Required?
**No** - Without it, every analysis is computed fresh (recommended for development).

### Supported Databases

#### SQLite (Recommended for Development)
Simple file-based database, no setup required.

```env
DATABASE_URL=sqlite:///./analysis_cache.db
ENABLE_CACHING=true
CACHE_TTL_HOURS=24
```

#### PostgreSQL (Recommended for Production)
Robust relational database for production deployments.

1. Install PostgreSQL:
   ```bash
   # macOS
   brew install postgresql

   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib

   # Windows
   # Download from https://www.postgresql.org/download/windows/
   ```

2. Create database:
   ```bash
   createdb ai_codebase_explainer
   
   # Optional: with specific user/password
   createdb -U postgres -W ai_codebase_explainer
   ```

3. Configure connection:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/ai_codebase_explainer
   ENABLE_CACHING=true
   CACHE_TTL_HOURS=24
   ```

#### MySQL/MariaDB
Alternative relational database option.

```env
DATABASE_URL=mysql://user:password@localhost:3306/ai_codebase_explainer
ENABLE_CACHING=true
```

### Configuration Options
```env
# Enable/disable caching globally
ENABLE_CACHING=true|false

# How long to cache results (hours)
CACHE_TTL_HOURS=24  # Cache for 24 hours

# Clear expired caches periodically
# (Automatic with scheduled background tasks)
```

### Benefits
- **Speed**: Instant results for previously analyzed repositories
- **Reduced API calls**: Less load on GitHub and OpenAI APIs
- **Cost savings**: Fewer OpenAI tokens consumed
- **Scalability**: Better performance for repeated analyses

---

## Async Processing & Task Queue

### Purpose
Enables **background processing** of large repositories without blocking API responses. Useful for:
- Large codebases that take 2-5 minutes to analyze
- Webhooks from CI/CD that shouldn't time out
- Batch processing multiple repositories

### Is it Required?
**No** - Current implementation is synchronous (blocks until complete).

### How to Set Up

#### Redis (Recommended)

1. Install Redis:
   ```bash
   # macOS
   brew install redis

   # Ubuntu/Debian
   sudo apt-get install redis-server

   # Docker
   docker run -d -p 6379:6379 redis:latest
   
   # Windows (using WSL or Docker)
   ```

2. Verify it's running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

3. Configure:
   ```env
   ENABLE_ASYNC_PROCESSING=true
   TASK_QUEUE_URL=redis://localhost:6379
   ```

#### RabbitMQ (Alternative)
```env
ENABLE_ASYNC_PROCESSING=true
TASK_QUEUE_URL=amqp://user:password@localhost:5672/
```

### Workflow with Async Processing
```
User submits analysis → API returns job ID immediately
                       ↓
                Background worker analyzes
                       ↓ (when complete)
        User polls API or receives webhook
                       ↓
              Returns final results
```

---

## Diagram Generation Settings

### Purpose
Controls the generation and storage of architecture diagrams.

### Configuration
```env
# Output directory for generated diagrams
DIAGRAM_OUTPUT_PATH=./data/diagrams

# Enable Mermaid diagram generation (lightweight, markdown-friendly)
GENERATE_MERMAID=true

# Enable Graphviz diagram generation (detailed, SVG-compatible)
GENERATE_GRAPHVIZ=true
```

### Diagram Formats

#### Mermaid
- Format: Human-readable Markdown
- Use case: Documentation, GitHub README
- Example:
  ```mermaid
  graph TD
    Frontend --> Backend
    Backend --> Database
  ```

#### Graphviz
- Format: DOT format
- Use case: Advanced visualization, SVG rendering
- Example:
  ```dot
  digraph {
    Frontend -> Backend;
    Backend -> Database;
  }
  ```

#### JSON
- Format: Structured data
- Use case: Programmatic access, integration with other tools
- Always generated

---

## Environment Setup Instructions

### Step 1: Create .env File

```bash
# Copy template
cp .env.example .env

# Edit with your values
# nano .env  # or your preferred editor
```

### Step 2: Set Required Tokens (Optional)

#### For AI Analysis
```bash
# If you want AI-powered insights
echo "OPENAI_API_KEY=sk-xxxxxxxxxxxxx" >> .env
```

#### For Private Repository Access
```bash
# If you need to analyze private repos
echo "GITHUB_TOKEN=ghp_xxxxxxxxxxxxx" >> .env
echo "GITHUB_USERNAME=your_github_username" >> .env
```

#### For Result Caching
```bash
# If you want faster repeated analyses
echo "ENABLE_CACHING=true" >> .env
echo "DATABASE_URL=sqlite:///./analysis_cache.db" >> .env
```

### Step 3: Verify Configuration

```bash
# Test Python can load config
python -c "from src.utils.config import settings; print(f'API: {settings.API_TITLE}')"

# Should output: API: AI Codebase Explainer
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

### Complete .env Example

```env
# ===== OpenAI Configuration =====
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000

# ===== GitHub Authentication =====
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx
GITHUB_USERNAME=my_github_username

# ===== Repository Analysis =====
REPO_CLONE_PATH=./data/repos
MAX_REPO_SIZE_MB=500
MAX_ANALYSIS_FILES=100

# ===== Diagram Generation =====
DIAGRAM_OUTPUT_PATH=./data/diagrams
GENERATE_MERMAID=true
GENERATE_GRAPHVIZ=true

# ===== Database Caching =====
DATABASE_URL=sqlite:///./analysis_cache.db
ENABLE_CACHING=true
CACHE_TTL_HOURS=24

# ===== Async Processing =====
ENABLE_ASYNC_PROCESSING=false
TASK_QUEUE_URL=redis://localhost:6379

# ===== API Configuration =====
DEBUG=false
API_TITLE=AI Codebase Explainer
API_VERSION=0.1.0
```

---

## Security Best Practices

### 1. Never Commit Credentials
```bash
# Add to .gitignore
echo ".env" >> .gitignore
git rm --cached .env  # If already committed
```

### 2. Use Separate Keys per Environment
- Development: Test keys with limited permissions
- Production: Full privileges, rotated regularly
- Staging: Copy of production setup

### 3. Rotate Tokens Regularly
- GitHub PATs: Every 90 days
- OpenAI keys: Every 6 months minimum
- Database passwords: Every 180 days

### 4. Use Environment Variables in CI/CD
```yaml
# GitHub Actions example
- name: Run Analysis
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  run: python -m uvicorn src.main:app
```

### 5. Limit Token Scopes
- Grant **minimum required** permissions
- Never use `admin` scope unless necessary
- Review permissions quarterly

---

## Troubleshooting

### "OpenAI API key not configured"
**Expected behavior** - The system still works with rule-based analysis.

**To enable AI analysis:**
```bash
# Get key from https://platform.openai.com/account/api-keys
export OPENAI_API_KEY=sk-xxxxxxxxxxxxx

# Or add to .env and restart
```

### "Invalid GitHub token"
**Check:**
1. Token hasn't expired (check GitHub settings)
2. Token has `repo` scope selected
3. No typos in token value

**To regenerate:**
- Delete old token in GitHub settings
- Create new token with same scopes

### "Database connection failed"
**For SQLite:**
- Ensure directory exists: `mkdir -p ./data`
- Check write permissions: `ls -la ./data`

**For PostgreSQL:**
- Verify running: `psql -U postgres`
- Check credentials in DATABASE_URL
- Ensure network connectivity

### "Redis connection refused"
**Check Redis is running:**
```bash
# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:latest

# Test connection
redis-cli ping  # Should return: PONG
```

---

## Next Steps

1. **Choose your configuration**: Select which optional features to enable
2. **Obtain credentials**: Get any required API keys and tokens
3. **Set up environment**: Create .env file with your values
4. **Test configuration**: Run the system and verify all features work
5. **Deploy**: Follow production deployment guide

For more information, see [SETUP.md](SETUP.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

---

**Last Updated**: March 4, 2026
**Version**: 2.0 (Updated for Diagram Generation & Advanced Features)
