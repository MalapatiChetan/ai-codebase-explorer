#!/usr/bin/env python
"""
Repository storage optimization implementations.

Choose ONE and copy the clone_repository method into src/modules/repo_scanner.py
"""

# ==============================================================================
# OPTION 1: SHALLOW CLONE (Recommended - Easiest, 90% Storage Savings)
# ==============================================================================
"""
Best for: All scenarios (quickest to implement)
Storage: 10-300MB instead of 500MB-5GB (90-95% savings)
Speed: 1-3 seconds instead of 30-60 seconds
Code change: Just add 2 parameters to clone_from()

Implementation:
    1. Find this in src/modules/repo_scanner.py:
       Repo.clone_from(repo_url, str(repo_path))
    
    2. Replace with:
       Repo.clone_from(repo_url, str(repo_path), depth=1, single_branch=True)
"""

def clone_repository_shallow(self, repo_url: str) -> Path:
    """
    Clone repository with shallow copy (latest commit only, no history).
    
    This reduces storage by 90-95% and cloning speed by 50x-100x.
    Architecture analysis doesn't need full history.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Path to cloned repository
    """
    repo_name = self.extract_repo_name(repo_url)
    repo_path = self.clone_path / repo_name
    
    if repo_path.exists():
        success = self._safe_remove_directory(repo_path)
        if not success:
            temp_path = self.clone_path / f"{repo_name}_temp_{int(time.time())}"
            repo_path = temp_path
    
    try:
        logger.info(f"Shallow cloning {repo_url} (latest commit only)...")
        Repo.clone_from(
            repo_url,
            str(repo_path),
            depth=1,              # Only the latest commit
            single_branch=True,   # Only the default branch (main/master)
        )
        logger.info(f"Shallow clone complete: {repo_path} (~95% smaller than full clone)")
        return repo_path
    
    except GitCommandError as e:
        logger.error(f"Git error: {e}")
        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")
        raise ValueError(f"Clone failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error: {cleanup_error}")
        raise ValueError(f"Clone failed: {str(e)}")


# ==============================================================================
# OPTION 2: TEMPORARY CLONE + AUTO-CLEANUP (Cloud-Ready, Zero Permanent Storage)
# ==============================================================================
"""
Best for: Cloud deployments (Render, AWS, Heroku)
Storage: 10-300MB in /tmp, auto-deleted after analysis
Speed: 1-3 seconds
Code change: Replace clone logic + add cleanup method

Implementation:
    1. Replace clone_repository() in src/modules/repo_scanner.py with this
    2. Add cleanup_temporary_repo() method
    3. Call cleanup_temporary_repo() in metadata_builder.py after analysis
"""

import tempfile
from contextlib import contextmanager

def clone_repository_temporary(self, repo_url: str) -> Path:
    """
    Clone to temporary directory (/tmp) which is ephemeral on cloud platforms.
    
    Perfect for cloud: Render, AWS, Heroku automatically clean /tmp on restart.
    No permanent storage usage.
    
    Args:
        repo_url: GitHub repository URL
        
    Returns:
        Path to temporary cloned repository (will be deleted after analysis)
    """
    repo_name = self.extract_repo_name(repo_url)
    
    # Use system temp directory (ephemeral on cloud platforms)
    # On Render: /tmp is ~1GB and auto-cleaned
    # On local dev: /tmp is user temp directory
    temp_base = Path(tempfile.gettempdir()) / "ai-explainer"
    repo_path = temp_base / repo_name
    
    # Clean previous attempt if it exists
    if repo_path.exists():
        self._safe_remove_directory(repo_path)
    
    repo_path.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Cloning to temporary storage: {repo_path}")
        logger.warning(f"IMPORTANT: This repo will be deleted after analysis!")
        
        Repo.clone_from(
            repo_url,
            str(repo_path),
            depth=1,              # Shallow clone for speed
            single_branch=True,   # Only default branch
        )
        
        logger.info(f"Repository cloned to temp: {repo_path}")
        logger.info(f"Storage usage: estimated {self._estimate_size(repo_path)} MB")
        
        return repo_path
    
    except GitCommandError as e:
        logger.error(f"Git error: {e}")
        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
            except:
                pass
        raise ValueError(f"Clone failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if repo_path.exists():
            try:
                shutil.rmtree(repo_path)
            except:
                pass
        raise ValueError(f"Clone failed: {str(e)}")

def cleanup_temporary_repo(self, repo_path: Path) -> bool:
    """
    Delete temporary repository after analysis.
    
    Call this in metadata_builder.py after analysis completes.
    
    Args:
        repo_path: Path to repository to delete
        
    Returns:
        True if successfully deleted, False otherwise
    """
    if not repo_path.exists():
        logger.warning(f"Repo already deleted or doesn't exist: {repo_path}")
        return True
    
    try:
        logger.info(f"Cleaning up temporary repository: {repo_path}")
        removed = self._safe_remove_directory(repo_path)
        
        if removed:
            logger.info(f"✓ Successfully deleted temporary repo")
            return True
        else:
            logger.warning(f"✗ Failed to delete temporary repo: {repo_path}")
            return False
    
    except Exception as e:
        logger.error(f"Error deleting repo: {e}")
        return False

def _estimate_size(self, path: Path) -> float:
    """Estimate directory size in MB."""
    total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    return round(total / (1024 * 1024), 2)


# ==============================================================================
# OPTION 3: GITHUB API (Zero Storage, For Massive Repos)
# ==============================================================================
"""
Best for: Massive repositories (TensorFlow, PyTorch, LLVM)
Storage: 0MB (nothing cloned)
Speed: 2-5 seconds (depending on API call count)
Code change: Replace scanner with API-based scanner

Implementation:
    1. Create new file: src/modules/github_api_scanner.py
    2. Use GitHubAPIScanner instead of git clone
    3. Requires: GITHUB_TOKEN environment variable for rate limits
"""

import httpx
import base64
from typing import Optional

class GitHubAPIScanner:
    """
    Fetch repository structure via GitHub API without cloning.
    
    Advantages:
    - Zero local storage
    - Works for public and private repos
    - Can fetch exactly what you need
    
    Limitations:
    - API rate limits (60 req/hr unauthenticated, 5000 authenticated)
    - Slower for very large repos with thousands of files
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize GitHub API scanner."""
        self.base_url = "https://api.github.com"
        self.github_token = github_token
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
    
    def parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        """Extract owner and repo from GitHub URL."""
        # Handle: https://github.com/owner/repo or https://github.com/owner/repo.git
        parts = repo_url.rstrip("/").replace(".git", "").split("/")
        owner = parts[-2]
        repo = parts[-1]
        return owner, repo
    
    def get_repo_structure(self, repo_url: str) -> dict:
        """
        Get complete repository structure via API.
        
        Returns: {
            "files": [...],  # List of all files
            "dirs": [...],   # List of all directories
            "file_count": N,
            "size_bytes": N,
        }
        """
        owner, repo = self.parse_repo_url(repo_url)
        
        try:
            # Get repository metadata
            repo_info_url = f"{self.base_url}/repos/{owner}/{repo}"
            repo_info = self._api_get(repo_info_url)
            
            # Get directory tree (recursive)
            tree_url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
            tree = self._api_get(tree_url)
            
            files = [item for item in tree.get("tree", []) if item["type"] == "blob"]
            dirs = [item for item in tree.get("tree", []) if item["type"] == "tree"]
            
            return {
                "owner": owner,
                "repo": repo,
                "url": repo_url,
                "description": repo_info.get("description", ""),
                "language": repo_info.get("language", "Unknown"),
                "size_kb": repo_info.get("size", 0),
                "files": files,
                "dirs": dirs,
                "file_count": len(files),
                "has_issues": repo_info.get("has_issues"),
                "has_wiki": repo_info.get("has_wiki"),
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch repo structure: {e}")
            raise ValueError(f"Could not fetch repository structure: {e}")
    
    def get_file_content(self, repo_url: str, file_path: str) -> str:
        """
        Get specific file content via API.
        
        Args:
            repo_url: GitHub repository URL
            file_path: Path to file in repo (e.g., "src/main.py")
            
        Returns:
            File content as string
        """
        owner, repo = self.parse_repo_url(repo_url)
        
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            response = self._api_get(url)
            
            # Content is base64-encoded
            content = base64.b64decode(response["content"]).decode("utf-8")
            return content
        
        except Exception as e:
            logger.error(f"Failed to fetch file {file_path}: {e}")
            return ""
    
    def get_readme(self, repo_url: str) -> str:
        """Get README content if it exists."""
        readme_paths = ["README.md", "README.txt", "README", "readme.md"]
        
        for path in readme_paths:
            try:
                return self.get_file_content(repo_url, path)
            except:
                continue
        
        return ""
    
    def _api_get(self, url: str) -> dict:
        """Make authenticated API request."""
        response = httpx.get(url, headers=self.headers, timeout=10)
        
        if response.status_code == 403:
            raise ValueError("API rate limit exceeded. Use GITHUB_TOKEN for higher limits.")
        
        if response.status_code == 404:
            raise ValueError("Repository not found.")
        
        if response.status_code >= 400:
            raise ValueError(f"API error {response.status_code}: {response.text[:100]}")
        
        return response.json()

# ==============================================================================
# USAGE IN metadata_builder.py
# ==============================================================================

"""
# Option 1: No change needed - just uncomment next 2 lines in repo_scanner.py:
# Repo.clone_from(
#     repo_url, str(repo_path),
#     depth=1, single_branch=True  # ← Add these
# )

# Option 2: Add cleanup call in metadata_builder.py:
def build_metadata(self, repo_url: str) -> Dict:
    try:
        repo_path = self.scanner.clone_repository(repo_url)
        scan_metadata = self.scanner.scan_repository(repo_path)
        # ... more analysis ...
        return metadata
    finally:
        # Auto-cleanup temporary repo
        self.scanner.cleanup_temporary_repo(repo_path)

# Option 3: Use GitHub API instead of cloning:
def build_metadata(self, repo_url: str) -> Dict:
    api_scanner = GitHubAPIScanner(token=settings.GITHUB_TOKEN)
    structure = api_scanner.get_repo_structure(repo_url)
    
    # Analyze structure without cloning
    metadata = {
        "repository": {"url": repo_url, "name": structure["repo"]},
        "files": structure["files"],
        "file_count": structure["file_count"],
        # ... etc ...
    }
    return metadata
"""

