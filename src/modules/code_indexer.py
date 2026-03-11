"""Code indexing module for RAG-based architecture analysis."""

import logging
import re
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import json

from src.utils.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata."""
    file_path: str
    start_line: int
    end_line: int
    code_content: str
    language: str
    chunk_index: int = 0
    
    def __repr__(self):
        """String representation."""
        return f"CodeChunk({self.file_path}:{self.start_line}-{self.end_line})"
    
    def to_dict(self):
        """Convert to dictionary."""
        return asdict(self)


class CodeIndexer:
    """Indexes source code files from a repository."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """Initialize the code indexer.
        
        Args:
            chunk_size: Size of code chunks in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP
        self.skip_dirs = set(settings.SKIP_DIRS)
        self.supported_extensions = {
            ext.lower() for ext in getattr(settings, "RAG_INDEXED_FILE_TYPES", [])
        }
        self.excluded_files = {
            name.lower() for name in getattr(settings, "RAG_EXCLUDED_FILES", [])
        }
        self.last_index_stats: Dict[str, int] = {
            "files_scanned": 0,
            "chunks_created": 0,
        }
    
    def index_repository(self, repo_path: str) -> List[CodeChunk]:
        """
        Index all source files in a repository.
        
        Args:
            repo_path: Path to the repository directory
            
        Returns:
            List of CodeChunk objects
        """
        logger.debug(f"Starting code indexing for {repo_path}")
        
        repo_path_obj = Path(repo_path)
        if not repo_path_obj.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            return []
        
        chunks = []
        file_count = 0
        
        # Recursively scan for source files
        try:
            for source_file in repo_path_obj.rglob("*"):
                # Skip directories
                if source_file.is_dir():
                    continue
                
                # Skip files in excluded directories
                if self._should_skip(source_file, repo_path_obj):
                    continue
                
                # Check if file extension is supported
                if source_file.suffix.lower() not in self.supported_extensions:
                    continue

                if source_file.name.lower() in self.excluded_files:
                    continue

                if source_file.name.endswith((".min.js", ".min.css")):
                    continue
                
                # Index the file
                try:
                    file_chunks = self._index_file(source_file, repo_path_obj)
                    chunks.extend(file_chunks)
                    file_count += 1
                    
                    if file_count % 50 == 0:
                        logger.debug(f"Indexed {file_count} files, {len(chunks)} chunks created")
                
                except Exception as e:
                    logger.warning(f"Failed to index file {source_file}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error during repository indexing: {e}")
            import traceback
            traceback.print_exc()
        
        self.last_index_stats = {
            "files_scanned": file_count,
            "chunks_created": len(chunks),
        }
        logger.info(
            f"Source scan summary | "
            f"files_scanned={file_count} chunks_created={len(chunks)}"
        )
        return chunks
    
    def _should_skip(self, path: Path, repo_root: Path) -> bool:
        """Check if a path should be skipped.
        
        Args:
            path: Path to check
            repo_root: Root directory of the repository
            
        Returns:
            True if path should be skipped
        """
        try:
            relative_path = path.relative_to(repo_root)
        except ValueError:
            return True
        
        # Check if any parent directory should be skipped
        for part in relative_path.parts:
            if part in self.skip_dirs:
                return True
            # Skip hidden directories/files
            if part.startswith(".") and part not in {".github", ".gitignore"}:
                return True
        if path.name.lower() in self.excluded_files:
            return True
        
        return False
    
    def _index_file(self, file_path: Path, repo_root: Path) -> List[CodeChunk]:
        """
        Index a single source file.
        
        Args:
            file_path: Path to the source file
            repo_root: Root directory of the repository
            
        Returns:
            List of CodeChunk objects
        """
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return []
        
        # Get relative path
        try:
            relative_path = file_path.relative_to(repo_root)
        except ValueError:
            relative_path = file_path
        
        # Determine language from extension
        language = self._get_language(file_path)
        
        # Split into chunks
        chunks = self._create_chunks(
            str(relative_path),
            content,
            language
        )
        
        return chunks
    
    def _create_chunks(self, file_path: str, content: str, language: str) -> List[CodeChunk]:
        """
        Split file content into chunks.
        
        Args:
            file_path: Path to the file (relative)
            content: File content
            language: Programming language
            
        Returns:
            List of CodeChunk objects
        """
        lines = content.split("\n")
        chunks = []
        chunk_index = 0
        
        start_line = 1
        current_chunk = []
        current_char_count = 0
        
        for line_idx, line in enumerate(lines):
            line_with_newline = line + "\n"
            current_chunk.append(line_with_newline)
            current_char_count += len(line_with_newline)
            
            # Create chunk when size exceeded or at end of file
            if current_char_count >= self.chunk_size or line_idx == len(lines) - 1:
                code_content = "".join(current_chunk).rstrip()
                
                if code_content.strip():  # Only add non-empty chunks
                    chunk = CodeChunk(
                        file_path=file_path,
                        start_line=start_line,
                        end_line=line_idx + 1,
                        code_content=code_content,
                        language=language,
                        chunk_index=chunk_index,
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                
                # Prepare for next chunk with overlap
                if line_idx < len(lines) - 1:
                    # Calculate overlap in terms of lines
                    overlap_lines = max(1, int(self.chunk_overlap / 50))  # Rough estimate
                    start_idx = max(0, len(current_chunk) - overlap_lines)
                    
                    current_chunk = current_chunk[start_idx:]
                    current_char_count = sum(len(l) for l in current_chunk)
                    start_line = line_idx + 1 - (len(current_chunk) - 1)
                else:
                    current_chunk = []
                    current_char_count = 0
        
        return chunks
    
    def _get_language(self, file_path: Path) -> str:
        """Get programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name
        """
        extension = file_path.suffix.lower()
        
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",
            ".java": "java",
            ".go": "go",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php",
            ".scala": "scala",
            ".kotlin": "kotlin",
            ".rs": "rust",
            ".swift": "swift",
            ".m": "objective-c",
            ".mm": "objective-cpp",
            ".sql": "sql",
            ".sh": "shell",
            ".bash": "bash",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".json": "json",
            ".xml": "xml",
            ".html": "html",
            ".css": "css",
            ".scss": "scss",
        }
        
        return language_map.get(extension, "text")
    
    def save_chunks_metadata(self, chunks: List[CodeChunk], output_file: str) -> bool:
        """
        Save chunk metadata to file for persistence.
        
        Args:
            chunks: List of code chunks
            output_file: Path to save metadata
            
        Returns:
            True if successful
        """
        try:
            metadata = [chunk.to_dict() for chunk in chunks]
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.debug(f"Saved metadata for {len(chunks)} chunks to {output_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save chunks metadata: {e}")
            return False
    
    def load_chunks_metadata(self, input_file: str) -> List[CodeChunk]:
        """
        Load chunk metadata from file.
        
        Args:
            input_file: Path to load metadata from
            
        Returns:
            List of CodeChunk objects
        """
        try:
            input_path = Path(input_file)
            
            if not input_path.exists():
                logger.debug(f"Chunks metadata file not found: {input_file}")
                return []
            
            with open(input_path, "r") as f:
                metadata = json.load(f)
            
            chunks = [CodeChunk(**chunk_data) for chunk_data in metadata]
            logger.debug(f"Loaded {len(chunks)} chunks from {input_file}")
            return chunks
        
        except Exception as e:
            logger.error(f"Failed to load chunks metadata: {e}")
            return []
