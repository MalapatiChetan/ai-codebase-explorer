"""Module metadata builder - structures all collected information."""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from src.modules.repo_scanner import RepositoryScanner
from src.modules.framework_detector import FrameworkDetector
from src.modules.diagram_generator import ArchitectureDiagramGenerator
from src.modules.code_indexer import CodeIndexer
from src.modules.vector_store_manager import get_vector_store_manager
from src.utils.repository_registry import get_repository_registry
from src.utils.config import settings
from src.utils.logging_utils import configure_library_log_levels, log_step

logger = logging.getLogger(__name__)


class RepositoryMetadataBuilder:
    """Builds comprehensive repository metadata from scan and detection results."""
    
    def __init__(self):
        """Initialize the metadata builder."""
        self.scanner = RepositoryScanner()
        self.detector = FrameworkDetector()
        self.diagram_generator = ArchitectureDiagramGenerator()
        self.code_indexer = CodeIndexer()
    
    def build_metadata(self, repo_url: str) -> Dict:
        """
        Build complete repository metadata.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Comprehensive repository metadata dictionary
        """
        configure_library_log_levels()
        logger.info(f"Starting analysis for {repo_url}")
        
        try:
            repo_name = self.scanner.extract_repo_name(repo_url)
            cached_metadata = self._get_cached_metadata_if_current(repo_url, repo_name)
            if cached_metadata:
                log_step(logger, 8, f"Indexing completed via cache for {repo_name}")
                return cached_metadata

            log_step(logger, 3, f"Cloning repository {repo_name}")
            repo_path, repo_name = self.scanner.clone_repository(repo_url)
            logger.info(f"Repository ready at {repo_path}")
            
            # Step 1b: Capture git information for smart caching
            git_commit = "unknown"
            git_commit_short = "unknown"
            git_branch = "unknown"
            try:
                from git import Repo as GitRepo
                git_repo = GitRepo(str(repo_path))
                git_commit = git_repo.head.commit.hexsha
                git_commit_short = git_commit[:8]
                git_branch = git_repo.active_branch.name
                logger.info(f"Resolved commit={git_commit_short} branch={git_branch}")
            except Exception as e:
                logger.debug(f"Could not extract git info: {e}")
            
            log_step(logger, 4, f"Scanning repository structure for {repo_name}")
            scan_metadata = self.scanner.scan_repository(repo_path)
            
            logger.info(
                f"Repository scan summary | files={scan_metadata['file_count']} "
                f"backend={scan_metadata['has_backend']} frontend={scan_metadata['has_frontend']}"
            )
            logger.info("Detecting frameworks and architecture metadata")
            detected_frameworks = self.detector.detect_frameworks(repo_path, scan_metadata)
            
            # Step 4: Get primary language
            primary_language = self.detector.get_primary_language(scan_metadata)
            
            # Step 5: Detect architecture patterns
            patterns = self.detector.detect_architecture_patterns(scan_metadata)
            
            # Step 6: Build tech stack
            tech_stack = self.detector.get_tech_stack(detected_frameworks, primary_language)
            
            # Step 7: Analyze dependencies
            dependencies = self.detector.analyze_dependencies(repo_path, scan_metadata)
            
            # Step 8: Structure module organization
            modules = self._identify_modules(scan_metadata)
            
            # Step 9: Compile initial metadata (needed for diagram generation)
            metadata = {
                "repository": {
                    "url": repo_url,
                    "name": repo_name,  # Use the canonical repo_name from URL extraction, not folder path
                    "path": str(repo_path),
                    "git_commit": git_commit,
                    "git_commit_short": git_commit_short,
                    "git_branch": git_branch,
                },
                "analysis": {
                    "file_count": scan_metadata["file_count"],
                    "primary_language": primary_language,
                    "languages": scan_metadata["languages"],
                    "has_backend": scan_metadata["has_backend"],
                    "has_frontend": scan_metadata["has_frontend"],
                },
                "frameworks": {
                    framework: {
                        "confidence": info["confidence"],
                        "matched_patterns": info["matched_patterns"],
                    }
                    for framework, info in detected_frameworks.items()
                    if info["confidence"] >= 0.2
                },
                "tech_stack": tech_stack,
                "architecture_patterns": patterns,
                "dependencies": dependencies,
                "modules": modules,
                "root_files": scan_metadata["root_files"],
                "important_files": self._extract_important_files(scan_metadata),
            }
            
            logger.info("Generating architecture diagrams")
            try:
                diagrams = self.diagram_generator.generate_diagrams(metadata)
                metadata["diagrams"] = diagrams
            except Exception as e:
                logger.warning(f"Failed to generate diagrams: {e}")
                metadata["diagrams"] = {"error": str(e)}
            
            logger.info("Preparing semantic index")
            try:
                self._index_code_for_rag(repo_path, metadata)
                log_step(logger, 8, f"Indexing completed for {repo_name}")
            except Exception as e:
                logger.warning(f"Failed to index code: {e}")

            # Persist metadata so repeated analyze runs can return cached results
            get_repository_registry().register(repo_name, metadata)
            
            logger.info("Metadata building completed successfully")
            return metadata
        
        except Exception as e:
            logger.error(f"Error building metadata: {e}")
            raise
    
    def _identify_modules(self, scan_metadata: Dict) -> List[Dict]:
        """
        Identify top-level modules/components in the repository.
        
        Args:
            scan_metadata: Repository scan metadata
            
        Returns:
            List of identified modules
        """
        modules = []
        seen_dirs = set()
        
        # Group files by top-level directories
        dir_tree = {}
        
        for file_info in scan_metadata.get("files", []):
            path_parts = file_info["path"].split("/")
            
            # Skip hidden and single-file roots
            if path_parts[0].startswith("."):
                continue
            
            if len(path_parts) > 1:
                top_dir = path_parts[0]
                if top_dir not in dir_tree:
                    dir_tree[top_dir] = {"files": 0, "extensions": set()}
                
                dir_tree[top_dir]["files"] += 1
                ext = file_info["extension"]
                if ext:
                    dir_tree[top_dir]["extensions"].add(ext)
        
        # Create module entries
        for dir_name, info in sorted(dir_tree.items()):
            if info["files"] > 0:
                module_type = self._determine_module_type(dir_name, info["extensions"])
                modules.append({
                    "name": dir_name,
                    "type": module_type,
                    "file_count": info["files"],
                    "extensions": list(info["extensions"])
                })
        
        return modules[:10]  # Return top 10 modules
    
    def _determine_module_type(self, dir_name: str, extensions: set) -> str:
        """Determine the type of a module based on name and content."""
        name_lower = dir_name.lower()
        
        # Backend indicators
        if any(x in name_lower for x in ["api", "backend", "server", "service", "handler"]):
            return "Backend Service"
        
        # Frontend indicators
        if any(x in name_lower for x in ["ui", "frontend", "components", "pages", "app"]):
            return "Frontend"
        
        # Config indicators
        if any(x in name_lower for x in ["config", "settings", "env", "scripts"]):
            return "Configuration"
        
        # Test indicators
        if any(x in name_lower for x in ["test", "tests", "spec", "specs"]):
            return "Tests"
        
        # Documentation
        if any(x in name_lower for x in ["docs", "documentation", "doc"]):
            return "Documentation"
        
        # Tool/Build indicators
        if any(x in name_lower for x in ["tools", "build", "scripts", "bin"]):
            return "Build/Tools"
        
        # Check file extensions
        if ".py" in extensions or ".java" in extensions or ".go" in extensions:
            return "Backend Logic"
        elif ".js" in extensions or ".jsx" in extensions or ".tsx" in extensions or ".ts" in extensions:
            return "Frontend/App Logic"
        elif ".css" in extensions or ".scss" in extensions:
            return "Styles"
        
        return "Module"
    
    def _extract_important_files(self, scan_metadata: Dict) -> List[str]:
        """Extract important files from the scan metadata."""
        important = []
        root_files = scan_metadata.get("root_files", [])
        
        # Known important files
        important_names = [
            "README.md", "README.txt", "README",
            "package.json", "pom.xml", "setup.py",
            "requirements.txt", "Dockerfile", "docker-compose.yml",
            "Makefile", ".github", "docker-compose.yaml",
        ]
        
        for file in root_files:
            for important_name in important_names:
                if file.lower() == important_name.lower():
                    important.append(file)
                    break
        
        return important
    
    def get_summary(self, metadata: Dict) -> Dict:
        """
        Get a summary view of the metadata.
        
        Args:
            metadata: Full repository metadata
            
        Returns:
            Summary dictionary
        """
        return {
            "repository_name": metadata["repository"]["name"],
            "primary_language": metadata["analysis"]["primary_language"],
            "frameworks": list(metadata["frameworks"].keys()),
            "tech_stack": metadata["tech_stack"],
            "architecture_patterns": metadata["architecture_patterns"],
            "has_backend": metadata["analysis"]["has_backend"],
            "has_frontend": metadata["analysis"]["has_frontend"],
            "file_count": metadata["analysis"]["file_count"],
            "modules": metadata["modules"],
        }
    
    def _get_commit_sha(self, repo_path: str) -> Optional[str]:
        """Get the current commit SHA from the repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Commit SHA or None if not available
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.debug(f"Could not get commit SHA: {e}")
        
        return None

    def _get_cached_metadata_if_current(self, repo_url: str, repo_name: str) -> Optional[Dict]:
        """Return cached metadata if repo commit and vector index are already current."""
        registry = get_repository_registry()
        cached_metadata = registry.get(repo_name)
        if not cached_metadata:
            logger.info(f"Analyze cache miss for {repo_name}: no cached metadata found")
            return None

        cached_repo = cached_metadata.get("repository", {})
        cached_commit = cached_repo.get("git_commit")
        cached_url = cached_repo.get("url")
        if not cached_commit or cached_url != repo_url:
            logger.info(
                f"Analyze cache miss for {repo_name}: cached metadata missing commit or URL mismatch"
            )
            return None

        repo_path = Path(settings.REPO_CLONE_PATH) / repo_name
        log_step(logger, 1, f"Checking latest GitHub commit for {repo_name}")
        remote_commit = self.scanner.get_latest_remote_commit(repo_url)
        local_commit = self.scanner.get_local_commit(repo_path) if repo_path.exists() else None
        logger.info(
            "Commit comparison | "
            f"repo={repo_name} remote_commit={remote_commit or 'unavailable'} "
            f"local_commit={local_commit or 'unavailable'} cached_commit={cached_commit}"
        )

        current_commit = remote_commit or local_commit
        if current_commit != cached_commit:
            logger.info(
                f"Analyze cache miss for {repo_name}: commit changed "
                f"(current={current_commit or 'unavailable'}, cached={cached_commit})"
            )
            return None

        if settings.ENABLE_RAG and settings.ENABLE_RAG_INDEX_ON_ANALYZE:
            vector_store = get_vector_store_manager()
            log_step(logger, 2, f"Checking Pinecone namespace for {repo_name}@{cached_commit[:8]}")
            has_namespace = vector_store.health_check() and vector_store.has_commit_index(repo_name, cached_commit)
            logger.info(
                "Namespace lookup | "
                f"repo={repo_name} commit_sha={cached_commit} exists={has_namespace}"
            )
            if not has_namespace:
                logger.info(
                    f"Cached metadata found for {repo_name}, but vector index is missing for commit {cached_commit[:8]}"
                )
                return None

        logger.info(
            f"Analyze cache hit for {repo_name} | commit_sha={cached_commit} "
            f"remote_commit={remote_commit or 'unavailable'} local_commit={local_commit or 'unavailable'}"
        )
        logger.info(f"Skipping clone, scan, chunking, embeddings, and upsert for {repo_name}")
        return cached_metadata
    
    def _index_code_for_rag(self, repo_path: str, metadata: Dict) -> None:
        """
        Index code using RAG system for semantic search.
        
        This method respects configuration flags:
        - ENABLE_RAG: Master switch, must be True
        - ENABLE_RAG_INDEX_ON_ANALYZE: If False, skip indexing during analysis
                                        (indexing happens on-demand when query requires it)
        - GOOGLE_API_KEY: If not configured, skip indexing (no AI provider to use RAG)
        
        Args:
            repo_path: Path to the repository
            metadata: Repository metadata with repository name
        """
        from src.utils.config import settings
        
        if not settings.ENABLE_RAG:
            logger.debug("RAG system disabled in configuration")
            return
        
        if not settings.ENABLE_RAG_INDEX_ON_ANALYZE:
            logger.debug("RAG indexing on analyze disabled - will index on-demand when query requires it")
            return
        
        # Skip indexing if no AI provider configured
        if not settings.GOOGLE_API_KEY:
            logger.debug("No Google API key configured - skipping RAG indexing (system will use rule-based answers)")
            return
        
        try:
            repo_name = metadata["repository"]["name"]
            logger.info(f"Indexing code for {repo_name} from {repo_path}")
            
            # Get current commit SHA for commit-aware caching
            commit_sha = self._get_commit_sha(repo_path)
            if commit_sha:
                logger.info(f"Commit resolved for indexing | commit_sha={commit_sha}")

            vector_store = get_vector_store_manager()
            if commit_sha and vector_store.health_check():
                log_step(logger, 2, f"Checking Pinecone namespace for {repo_name}@{commit_sha[:8]}")
                if vector_store.has_commit_index(repo_name, commit_sha):
                    logger.info(f"Code index already exists for {repo_name}, skipping indexing")
                    return
            
            # Import RAG on-demand to avoid slow initialization at startup
            from src.modules.rag_vector_store import RAGVectorStore
            
            # Initialize RAG vector store with commit tracking
            rag_store = RAGVectorStore(repo_name, commit_sha=commit_sha)
            
            if not rag_store.is_available():
                logger.warning("RAG system not available (missing dependencies)")
                return
            
            log_step(logger, 4, f"Scanning source files for {repo_name}")
            chunks = self.code_indexer.index_repository(repo_path)
            scan_stats = getattr(self.code_indexer, "last_index_stats", {})
            log_step(
                logger,
                5,
                f"Generating code chunks | files_scanned={scan_stats.get('files_scanned', 0)} "
                f"chunks_generated={scan_stats.get('chunks_created', len(chunks))}",
            )
            logger.info(
                "Chunking summary | "
                f"files_scanned={scan_stats.get('files_scanned', 0)} "
                f"chunks_created={scan_stats.get('chunks_created', len(chunks))}"
            )
            
            if not chunks:
                logger.warning("No code chunks to index")
                return
            
            log_step(logger, 6, f"Creating embeddings with {settings.RAG_EMBEDDING_MODEL}")
            success, observability = rag_store.index_chunks(chunks)
            logger.info(f"Embedding/index summary | {observability}")
            
            if success:
                vectors_uploaded = observability.get("chunk_count", len(chunks))
                log_step(
                    logger,
                    7,
                    f"Uploading vectors to Pinecone completed | embeddings_created={observability.get('embeddings_generated', len(chunks))} "
                    f"vectors_uploaded={vectors_uploaded}",
                )
                logger.info(f"Successfully indexed {len(chunks)} code chunks for {repo_name}")
                logger.debug(f"Indexing observability: {observability}")
            else:
                logger.error(f"Failed to index code chunks: {observability.get('status', 'unknown error')}")
        
        except Exception as e:
            logger.error(f"Error during code indexing: {e}")
            import traceback
            traceback.print_exc()
