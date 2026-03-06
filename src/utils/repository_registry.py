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
        Register an analyzed repository and save to disk immediately.
        
        Args:
            repo_name: Repository name or identifier
            metadata: Repository metadata dictionary
        """
        logger.info(f"Registering repository: {repo_name}")
        
        # Store in memory
        self.repositories[repo_name] = metadata
        logger.debug(f"Repository {repo_name} stored in memory cache")
        
        # Save to disk immediately
        self._save_metadata(repo_name, metadata)
        logger.info(f"✓ Repository {repo_name} registered and persisted to disk")
    
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
        """Save metadata to disk with comprehensive error handling and logging."""
        try:
            metadata_file = self.cache_dir / f"{repo_name}.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"✓ Metadata persisted to disk: {metadata_file}")
        except TypeError as e:
            logger.error(f"✗ JSON serialization error while saving metadata for {repo_name}: {e}")
            logger.error(f"  This usually means metadata contains non-serializable objects")
        except IOError as e:
            logger.error(f"✗ File I/O error while saving metadata for {repo_name}: {e}")
            logger.error(f"  Check permissions for {self.cache_dir}")
        except Exception as e:
            logger.error(f"✗ Unexpected error while saving metadata for {repo_name}: {type(e).__name__}: {e}")
    
    def _load_metadata(self, repo_name: str) -> Optional[Dict]:
        """Load metadata from disk with comprehensive error handling and logging."""
        try:
            metadata_file = self.cache_dir / f"{repo_name}.json"
            if not metadata_file.exists():
                logger.debug(f"Metadata file does not exist: {metadata_file}")
                return None
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            logger.debug(f"✓ Loaded metadata from disk: {metadata_file}")
            return metadata
        except json.JSONDecodeError as e:
            logger.error(f"✗ Invalid JSON in metadata file for {repo_name}: {e}")
            logger.error(f"  File may be corrupted. Consider re-analyzing the repository.")
        except IOError as e:
            logger.error(f"✗ File I/O error while loading metadata for {repo_name}: {e}")
        except Exception as e:
            logger.error(f"✗ Unexpected error while loading metadata for {repo_name}: {type(e).__name__}: {e}")
        
        return None
    
    def _metadata_file_exists(self, repo_name: str) -> bool:
        """Check if metadata file exists on disk."""
        return (self.cache_dir / f"{repo_name}.json").exists()
    
    def auto_load_from_cache(self) -> int:
        """
        Auto-load all repository metadata files from the cache directory.
        Called on application startup to restore previously analyzed repositories.
        This ensures metadata persistence across server restarts and deployments.
        
        Returns:
            Number of repositories successfully loaded
        """
        if not self.cache_dir.exists():
            logger.info("No cached repositories found (cache directory doesn't exist)")
            return 0
        
        loaded_count = 0
        failed_count = 0
        
        try:
            cached_files = list(self.cache_dir.glob("*.json"))
            logger.info(f"Found {len(cached_files)} metadata file(s) in cache directory")
            
            for metadata_file in cached_files:
                try:
                    repo_name = metadata_file.stem
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    self.repositories[repo_name] = metadata
                    loaded_count += 1
                    logger.debug(f"✓ Auto-loaded repository from cache: {repo_name}")
                except json.JSONDecodeError as e:
                    failed_count += 1
                    logger.warning(f"✗ Skip - Invalid JSON in {metadata_file.name}: {e}. Consider re-analyzing.")
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"✗ Skip - Failed to load {metadata_file.name}: {type(e).__name__}: {e}")
            
            if loaded_count > 0:
                logger.info(f"✓ Auto-loaded {loaded_count} repository(ies) from cache")
            if failed_count > 0:
                logger.warning(f"⚠ {failed_count} metadata file(s) could not be loaded (may be corrupted)")
            if loaded_count == 0 and len(cached_files) == 0:
                logger.info("No cached repositories found to auto-load")
        except Exception as e:
            logger.error(f"Error during auto-load from cache: {type(e).__name__}: {e}")
        
        return loaded_count
