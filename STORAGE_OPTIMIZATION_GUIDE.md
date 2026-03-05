# Repository Storage Optimization Guide

## Current Approach (Storage-Heavy)

```python
# Current: Clones full repo with entire history
Repo.clone_from(repo_url, str(repo_path))
# Size: Full repository (~100MB-1GB+ for large repos)
```

**Problem**: Large repos like `tensorflow` (5GB+) or `pytorch` (2GB+) eat up storage quickly.

---

## ✅ Recommended Alternatives

### Option 1: **Shallow Clone** (RECOMMENDED - 90% Storage Savings)

Clone only the latest commit without history.

```python
# Shallow clone: depth=1 (latest snapshot only)
Repo.clone_from(repo_url, str(repo_path), depth=1, single_branch=True)

# Storage reduction:
# FastAPI (full)     ~200MB  →  shallow: ~10MB  (95% saving)
# React (full)       ~500MB  →  shallow: ~20MB  (96% saving)  
# TensorFlow (full)  ~5GB    →  shallow: ~300MB (94% saving)
```

**Pros**:
- ✅ 90-95% storage savings
- ✅ Fast to clone (1-2 sec vs 30+ sec)
- ✅ Code analysis works identically
- ✅ No API rate limits

**Cons**:
- ❌ Can't access commit history (rarely needed for architecture analysis)
- ❌ Git blame/blame features won't work

---

### Option 2: **GitHub API (Zero Local Storage)**

Don't clone at all - fetch files on-demand via GitHub API.

```python
import httpx
import base64
from pathlib import Path

class GitHubAPIScanner:
    """Fetch repository structure without cloning."""
    
    def __init__(self, token: str = ""):
        self.base_url = "https://api.github.com/repos"
        self.session = httpx.AsyncClient()
        self.headers = {}
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    async def get_repo_structure(self, owner: str, repo: str) -> Dict:
        """Get repo structure without cloning."""
        # Get tree (directory structure)
        url = f"{self.base_url}/{owner}/{repo}/git/trees/HEAD?recursive=1"
        response = await self.session.get(url, headers=self.headers)
        tree = response.json()["tree"]
        
        return {
            "files": [item for item in tree if item["type"] == "blob"],
            "dirs": [item for item in tree if item["type"] == "tree"],
        }
    
    async def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Get specific file content without cloning."""
        url = f"{self.base_url}/{owner}/{repo}/contents/{path}"
        response = await self.session.get(url, headers=self.headers)
        data = response.json()
        
        # File content is base64-encoded
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content
```

**Pros**:
- ✅ Zero local storage (no repo directory)
- ✅ Instant analysis (no clone wait time)
- ✅ Works for private repos with token
- ✅ Can fetch exactly what you need

**Cons**:
- ❌ API rate limits (60 req/hr unauthenticated, 5000 authenticated)
- ❌ Large repos might need many API calls
- ❌ Slower for massive codebases (lots of files = lots of calls)
- ❌ Need GitHub token for private repos

---

### Option 3: **Temporary Cloning + Auto-Delete**

Clone to ephemeral storage and delete after analysis.

```python
import tempfile
import shutil
from pathlib import Path
from git import Repo

class TemporaryRepositoryScanner:
    """Clone to temporary storage and auto-cleanup."""
    
    def clone_temporary(self, repo_url: str) -> Path:
        """Clone to /tmp, auto-deletes after context exit."""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        
        # Use system temp directory (ephemeral on cloud)
        temp_dir = Path(tempfile.gettempdir()) / "repos" / repo_name
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Shallow clone for speed
        Repo.clone_from(repo_url, str(temp_dir), depth=1, single_branch=True)
        return temp_dir
    
    def analyze_with_cleanup(self, repo_url: str):
        """Context manager for auto-cleanup."""
        repo_path = self.clone_temporary(repo_url)
        try:
            # Analyze the repo
            scan = analyze_repo(repo_path)
            return scan
        finally:
            # Auto-delete after analysis
            shutil.rmtree(repo_path, ignore_errors=True)
```

**Usage**:
```python
scanner = TemporaryRepositoryScanner()
metadata = scanner.analyze_with_cleanup("https://github.com/fastapi/fastapi")
# Repo is automatically deleted after analysis!
```

**Pros**:
- ✅ Automatic cleanup (no storage left behind)
- ✅ Good for cloud environments (Render, AWS, etc.)
- ✅ Can use shallow clone for speed
- ✅ Temporary storage is fast

**Cons**:
- ⚠️ Data lost after analysis (can't re-analyze without re-cloning)
- ⚠️ /tmp might be small on some systems

---

### Option 4: **Sparse Checkout** (Clone Specific Directories Only)

Clone only the files you need.

```python
from git import Repo
from git.repo.fun import is_git_dir

def sparse_clone(repo_url: str, target_path: Path, patterns: list[str]):
    """
    Clone only specific files/directories.
    
    patterns: ["src/", "README*", "*.json"]
    """
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize sparse checkout
    repo = Repo.init(target_path)
    repo.remotes.add("origin", repo_url)
    
    # Configure sparse checkout
    git_dir = target_path / ".git"
    sparse_file = git_dir / "info" / "sparse-checkout"
    sparse_file.parent.mkdir(exist_ok=True)
    
    with open(sparse_file, "w") as f:
        for pattern in patterns:
            f.write(f"{pattern}\n")
    
    # Pull with sparse checkout
    repo.remotes.origin.fetch(depth=1)
    repo.heads.main.checkout()
```

**Example**:
```python
sparse_clone(
    "https://github.com/fastapi/fastapi",
    Path("./data/repos/fastapi"),
    patterns=[
        "fastapi/",        # Only source code
        "README.md",       # And readme
        "pyproject.toml",  # And dependencies
    ]
)
```

**Pros**:
- ✅ Moderate storage savings (50-80%)
- ✅ Focuses on code you actually need
- ✅ Still has file history (unlike shallow clone)

**Cons**:
- ⚠️ More complex setup
- ⚠️ Sparse checkout support varies by Git version

---

## 📊 Storage Comparison

| Strategy | Size | Speed | Setup | Cloud-Ready |
|----------|------|-------|-------|-------------|
| **Full Clone** | 500MB-5GB | 30-60s | Simple | ❌ |
| **Shallow Clone** | 10-300MB | 1-3s | 1 line | ✅ |
| **GitHub API** | ~0MB | 5-10s | Medium | ✅✅ |
| **Temp Clone** | 10-300MB | 1-3s | Medium | ✅✅ |
| **Sparse Clone** | 50-200MB | 5-10s | Complex | ✅ |

---

## 🎯 Recommendation by Use Case

### **Development/Testing → Use Shallow Clone**
```python
Repo.clone_from(repo_url, str(repo_path), depth=1, single_branch=True)
```
- Fast to clone
- Small storage
- Easy implementation

### **Production Cloud (Render) → Use Temp Clone + Auto-Delete**
```python
# Clone to /tmp, auto-delete after analysis
temp_dir = Path(tempfile.gettempdir()) / repo_name
Repo.clone_from(repo_url, str(temp_dir), depth=1, single_branch=True)
# ... analyze ...
shutil.rmtree(temp_dir)  # Cleanup
```
- Clean ephemeral storage
- No permanent disk usage
- Perfect for Render's 30s startup limits

### **Massive Repos (TensorFlow, PyTorch) → Use GitHub API**
```python
# Don't clone at all - fetch on-demand
files = await github_api.get_repo_structure(owner, repo)
content = await github_api.get_file_content(owner, repo, filepath)
```
- Zero storage
- Only fetch what you need

---

## Implementation: Update `repo_scanner.py`

Here are the key changes:

```python
# OPTION A: Shallow Clone (Recommended - 1 line change)
def clone_repository(self, repo_url: str) -> Path:
    repo_name = self.extract_repo_name(repo_url)
    repo_path = self.clone_path / repo_name
    
    # Add depth=1 and single_branch=True
    Repo.clone_from(
        repo_url, 
        str(repo_path),
        depth=1,              # ← Only latest commit
        single_branch=True    # ← Only main branch
    )
    return repo_path


# OPTION B: Temporary Clone (Best for Cloud)
def clone_repository(self, repo_url: str) -> Path:
    import tempfile
    
    repo_name = self.extract_repo_name(repo_url)
    
    # Use /tmp for ephemeral storage on cloud
    temp_base = Path(tempfile.gettempdir()) / "ai-explainer-repos"
    repo_path = temp_base / repo_name
    
    repo_path.mkdir(parents=True, exist_ok=True)
    
    Repo.clone_from(
        repo_url,
        str(repo_path),
        depth=1,
        single_branch=True
    )
    return repo_path

# Add cleanup method
def cleanup_temporary_repo(self, repo_path: Path) -> bool:
    """Delete temporary repo after analysis."""
    try:
        shutil.rmtree(repo_path)
        logger.info(f"Cleaned up temporary repo: {repo_path}")
        return True
    except Exception as e:
        logger.warning(f"Failed to cleanup {repo_path}: {e}")
        return False
```

---

## 🚀 Implementation Priority

**Easy Win (5 min)**: Add `depth=1, single_branch=True` to clone
- 90% storage savings
- No other changes needed
- Works with current code

**Medium (30 min)**: Temp clone + auto-cleanup
- Best for cloud (Render, AWS)
- Zero permanent storage
- Requires metadata_builder updates

**Advanced (2 hours)**: GitHub API integration
- Zero local storage
- Handles massive repos
- Requires new API module

---

## Questions & Answers

**Q: Will shallow clone break code analysis?**
A: No - you only need the latest code to analyze architecture. History isn't used.

**Q: What about monorepos with multiple subdirectories?**
A: All strategies work fine - shallow clone still gets entire structure.

**Q: Can I re-analyze the same repo?**
A: Shallow clone ✅ (re-clone is fast)
Temp clone ❌ (deleted after)
GitHub API ✅ (always available)

**Q: Will GitHub API work for private repos?**
A: Yes - if you provide a GitHub token in `GITHUB_TOKEN` env var.

**Q: What's the best for Render.com?**
A: Temp clone + auto-cleanup (Option 3)
- No persistent storage needed
- Ephemeral /tmp is perfect for their model

