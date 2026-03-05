"""Repository scanning and analysis module."""

import os
import shutil
import time
import stat
from pathlib import Path
from typing import Dict, List, Tuple
from git import Repo
from git.exc import GitCommandError
import logging

from src.utils.config import settings
from src.utils.constants import BACKEND_INDICATORS, FRONTEND_INDICATORS

logger = logging.getLogger(__name__)


class RepositoryScanner:
    """Handles repository cloning and file system analysis."""
    
    def __init__(self):
        """Initialize the scanner."""
        self.clone_path = Path(settings.REPO_CLONE_PATH)
        self.clone_path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def extract_repo_name(repo_url: str) -> str:
        """Extract repository name from URL."""
        # Handle both HTTPS and SSH URLs
        name = repo_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name
    
    def clone_repository(self, repo_url: str) -> Path:
        """
        Clone a GitHub repository locally with safe directory cleanup.
        
        Args:
            repo_url: URL of the GitHub repository
            
        Returns:
            Path to the cloned repository
            
        Raises:
            ValueError: If cloning fails after retries
        """
        repo_name = self.extract_repo_name(repo_url)
        repo_path = self.clone_path / repo_name
        
        # Try to remove existing repository with retry logic
        if repo_path.exists():
            logger.info(f"Existing repository detected at {repo_path}")
            success = self._safe_remove_directory(repo_path)
            if not success:
                logger.warning(f"Failed to remove existing repo, will attempt clone to alternative path")
                # Try cloning to a temporary location first
                temp_path = self.clone_path / f"{repo_name}_temp_{int(time.time())}"
                repo_path = temp_path
        
        try:
            logger.info(f"Cloning repository from {repo_url} to {repo_path}")
            # Use shallow clone (depth=1) to save 90%+ storage on cloud platforms
            # This clones only the latest commit without full history
            # Prevents "Out of memory" errors on Render's 512MB free tier
            Repo.clone_from(
                repo_url, 
                str(repo_path),
                depth=1,              # Only latest commit (90-95% smaller)
                single_branch=True    # Only default branch (faster, less memory)
            )
            logger.info(f"Successfully cloned repository to {repo_path} (shallow clone - storage optimized)")
            return repo_path
        
        except GitCommandError as e:
            logger.error(f"Git command error while cloning: {e}")
            # Try to cleanup if clone failed
            if repo_path.exists():
                try:
                    shutil.rmtree(repo_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up failed clone directory: {cleanup_error}")
            raise ValueError(f"Failed to clone repository: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during cloning: {e}")
            # Try to cleanup if clone failed
            if repo_path.exists():
                try:
                    shutil.rmtree(repo_path)
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up failed clone directory: {cleanup_error}")
            raise ValueError(f"Unexpected error during cloning: {str(e)}")
    
    def _safe_remove_directory(self, directory: Path, max_retries: int = 5) -> bool:
        """
        Safely remove a directory with retry logic for Windows file locks.
        
        Args:
            directory: Path to directory to remove
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successfully removed, False otherwise
        """
        if not directory.exists():
            return True
        
        for attempt in range(max_retries):
            try:
                # Handle readonly files by changing permissions before removal
                self._make_directory_writable(directory)
                shutil.rmtree(directory)
                logger.info(f"Directory removed successfully: {directory}")
                return True
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    wait_time = 0.5 * (attempt + 1)  # Exponential backoff: 0.5s, 1s, 1.5s, etc.
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} to remove {directory} failed. "
                        f"Retrying in {wait_time}s... (Error: {type(e).__name__})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to remove directory after {max_retries} attempts: {directory}")
                    logger.error(f"Last error: {e}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error removing directory {directory}: {e}")
                return False
        
        return False
    
    def _make_directory_writable(self, directory: Path) -> None:
        """
        Recursively change permissions of directory and files to be writable.
        This helps with cleanup of readonly files (especially on Windows).
        
        Args:
            directory: Path to directory
        """
        try:
            for root, dirs, files in os.walk(directory, topdown=False):
                # Fix directory permissions
                for directory_name in dirs:
                    dir_path = Path(root) / directory_name
                    try:
                        os.chmod(dir_path, stat.S_IRWXU)  # rwx for user
                    except Exception:
                        pass  # Skip if we can't change permissions
                
                # Fix file permissions
                for file_name in files:
                    file_path = Path(root) / file_name
                    try:
                        os.chmod(file_path, stat.S_IWRITE)  # write for user
                    except Exception:
                        pass  # Skip if we can't change permissions
            
            # Fix root directory permissions
            try:
                os.chmod(directory, stat.S_IRWXU)
            except Exception:
                pass
        except Exception as e:
            logger.debug(f"Non-critical error making directory writable: {e}")
    
    @staticmethod
    def should_skip_path(path: Path, skip_dirs: List[str]) -> bool:
        """Check if a path should be skipped during analysis."""
        # Check if any skip_dir matches path components
        for part in path.parts:
            if part in skip_dirs or part.startswith("."):
                return True
        return False
    
    def scan_repository(self, repo_path: Path) -> Dict:
        """
        Recursively scan repository structure and collect file metadata.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary containing repository metadata
        """
        metadata = {
            "repo_path": str(repo_path),
            "repo_name": repo_path.name,
            "files": [],
            "directories": [],
            "file_count": 0,
            "languages": {},
            "has_backend": False,
            "has_frontend": False,
            "root_files": [],
        }
        
        try:
            # Scan root directory for important files
            root_important_files = []
            for item in repo_path.iterdir():
                if item.is_file():
                    root_important_files.append(item.name)
            metadata["root_files"] = root_important_files
            
            # Walk through directory tree
            file_count = 0
            for root, dirs, files in os.walk(repo_path):
                root_path = Path(root)
                
                # Filter out directories that should be skipped
                dirs[:] = [
                    d for d in dirs 
                    if not self.should_skip_path(
                        root_path / d, 
                        settings.SKIP_DIRS
                    )
                ]
                
                # Process files
                for file in files:
                    file_path = root_path / file
                    
                    # Skip if too many files
                    if file_count >= settings.MAX_ANALYSIS_FILES:
                        break
                    
                    try:
                        rel_path = file_path.relative_to(repo_path)
                        file_ext = file_path.suffix.lower()
                        
                        file_info = {
                            "path": str(rel_path).replace("\\", "/"),
                            "name": file,
                            "extension": file_ext,
                            "size_bytes": file_path.stat().st_size,
                        }
                        
                        metadata["files"].append(file_info)
                        
                        # Track language
                        if file_ext:
                            lang = file_ext[1:]  # Remove leading dot
                            metadata["languages"][lang] = metadata["languages"].get(lang, 0) + 1
                        
                        file_count += 1
                    except Exception as e:
                        logger.warning(f"Error processing file {file_path}: {e}")
                        continue
                
                if file_count >= settings.MAX_ANALYSIS_FILES:
                    break
            
            metadata["file_count"] = file_count
            
            # Detect backend/frontend indicators
            root_files_str = " ".join(metadata["root_files"]).lower()
            all_paths = " ".join([f["path"].lower() for f in metadata["files"]])
            
            for indicator in BACKEND_INDICATORS:
                if indicator.lower() in root_files_str or indicator.lower() in all_paths:
                    metadata["has_backend"] = True
                    break
            
            for indicator in FRONTEND_INDICATORS:
                if indicator.lower() in root_files_str or indicator.lower() in all_paths:
                    metadata["has_frontend"] = True
                    break
            
            return metadata
        
        except Exception as e:
            logger.error(f"Error scanning repository: {e}")
            raise ValueError(f"Failed to scan repository: {str(e)}")
    
    def get_file_content(self, repo_path: Path, file_rel_path: str, max_lines: int = 50) -> str:
        """
        Get partial content of a file (up to max_lines).
        
        Args:
            repo_path: Path to repository
            file_rel_path: Relative path to file
            max_lines: Maximum lines to read
            
        Returns:
            File content
        """
        try:
            file_path = repo_path / file_rel_path
            if not file_path.exists():
                return ""
            
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[:max_lines]
                return "".join(lines)
        except Exception as e:
            logger.warning(f"Error reading file {file_rel_path}: {e}")
            return ""
    
    def find_files_by_extension(
        self, 
        repo_path: Path, 
        extensions: List[str]
    ) -> List[Dict]:
        """Find all files with specific extensions."""
        results = []
        extensions_lower = [ext.lower() if ext.startswith(".") else "." + ext.lower() 
                           for ext in extensions]
        
        for file_info in self.scan_repository(repo_path)["files"]:
            if file_info["extension"].lower() in extensions_lower:
                results.append(file_info)
        
        return results
