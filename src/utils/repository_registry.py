"""Repository metadata cache and registry."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class RepositoryRegistry:
    """Simple in-memory registry of analyzed repositories with optional persistence."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the repository registry.
        
        Args:
            cache_dir: Optional directory path for persistent storage of metadata
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path(__file__).parent.parent.parent / "metadata_cache"
        self.repositories: Dict[str, Dict] = {}
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Metadata cache directory ready: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Could not create cache directory: {e}")
    
    def register(self, repo_name: str, metadata: Dict) -> None:
        """
        Register an analyzed repository.
        
        Args:
            repo_name: Repository name or identifier
            metadata: Repository metadata dictionary
        """
        self.repositories[repo_name] = metadata
        self._save_metadata(repo_name, metadata)
        logger.info(f"Registered repository: {repo_name}")
    
    def get(self, repo_name: str) -> Optional[Dict]:
        """
        Get metadata for a registered repository.
        
        Args:
            repo_name: Repository name or identifier
            
        Returns:
            Metadata dictionary if found, None otherwise
        """
        # Check in-memory cache first
        if repo_name in self.repositories:
            return self.repositories[repo_name]
        
        # Try to load from disk
        metadata = self._load_metadata(repo_name)
        if metadata:
            self.repositories[repo_name] = metadata
            return metadata
        
        return None
    
    def exists(self, repo_name: str) -> bool:
        """Check if a repository has been analyzed."""
        return repo_name in self.repositories or self._metadata_file_exists(repo_name)
    
    def list_repositories(self) -> list:
        """Get list of all registered repositories."""
        repos = set(self.repositories.keys())
        
        # Also check cached files
        if self.cache_dir.exists():
            for file in self.cache_dir.glob("*.json"):
                repo_name = file.stem
                repos.add(repo_name)
        
        return sorted(list(repos))
    
    def _save_metadata(self, repo_name: str, metadata: Dict) -> None:
        """Save metadata to disk."""
        try:
            metadata_file = self.cache_dir / f"{repo_name}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.debug(f"Saved metadata for {repo_name}")
        except Exception as e:
            logger.warning(f"Could not save metadata for {repo_name}: {e}")
    
    def _load_metadata(self, repo_name: str) -> Optional[Dict]:
        """Load metadata from disk."""
        try:
            metadata_file = self.cache_dir / f"{repo_name}.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load metadata for {repo_name}: {e}")
        
        return None
    
    def _metadata_file_exists(self, repo_name: str) -> bool:
        """Check if metadata file exists on disk."""
        return (self.cache_dir / f"{repo_name}.json").exists()
