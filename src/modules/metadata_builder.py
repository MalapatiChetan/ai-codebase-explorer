"""Module metadata builder - structures all collected information."""

import logging
from pathlib import Path
from typing import Dict, List
from src.modules.repo_scanner import RepositoryScanner
from src.modules.framework_detector import FrameworkDetector
from src.modules.diagram_generator import ArchitectureDiagramGenerator
from src.modules.code_indexer import CodeIndexer

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
        logger.info(f"Building metadata for {repo_url}")
        
        try:
            # Step 1: Clone repository
            logger.info("Step 1: Cloning repository...")
            repo_path, repo_name = self.scanner.clone_repository(repo_url)
            logger.info(f"Repository cloned as: {repo_name}")
            
            # Step 2: Scan repository structure
            logger.info("Step 2: Scanning repository structure...")
            scan_metadata = self.scanner.scan_repository(repo_path)
            
            # Step 3: Detect frameworks
            logger.info("Step 3: Detecting frameworks...")
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
            
            # Step 10: Generate architecture diagrams
            logger.info("Step 10: Generating architecture diagrams...")
            try:
                diagrams = self.diagram_generator.generate_diagrams(metadata)
                metadata["diagrams"] = diagrams
            except Exception as e:
                logger.warning(f"Failed to generate diagrams: {e}")
                metadata["diagrams"] = {"error": str(e)}
            
            # Step 11: Index code for RAG system
            logger.info("Step 11: Indexing code for semantic search...")
            try:
                self._index_code_for_rag(repo_path, metadata)
                logger.info("Code indexing completed")
            except Exception as e:
                logger.warning(f"Failed to index code: {e}")
            
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
            logger.info(f"Starting code indexing for RAG system: {repo_name}")
            
            # Import RAG on-demand to avoid slow initialization at startup
            from src.modules.rag_vector_store import RAGVectorStore
            
            # Initialize RAG vector store
            rag_store = RAGVectorStore(repo_name)
            
            if not rag_store.is_available():
                logger.warning("RAG system not available (missing dependencies)")
                return
            
            # Check if index already exists
            if rag_store.load_index():
                logger.info(f"Code index already exists for {repo_name}, skipping indexing")
                return
            
            # Index code
            logger.info(f"Indexing code from {repo_path}")
            chunks = self.code_indexer.index_repository(repo_path)
            
            if not chunks:
                logger.warning("No code chunks to index")
                return
            
            # Build vector index
            success = rag_store.index_chunks(chunks)
            
            if success:
                logger.info(f"Successfully indexed {len(chunks)} code chunks for {repo_name}")
            else:
                logger.error("Failed to index code chunks")
        
        except Exception as e:
            logger.error(f"Error during code indexing: {e}")
            import traceback
            traceback.print_exc()
