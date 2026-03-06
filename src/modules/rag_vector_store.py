"""Vector database and embedding module for RAG system."""

import logging
import json
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

from src.modules.code_indexer import CodeChunk
from src.utils.config import settings

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not installed. RAG will be disabled.")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("faiss not installed. Vector database will be disabled.")


class EmbeddingGenerator:
    """Generates embeddings for code chunks using sentence-transformers."""
    
    def __init__(self, model_name: str = None):
        """Initialize the embedding generator.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        self.model_name = model_name or settings.RAG_EMBEDDING_MODEL
        self.model = None
        self.embedding_dim = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                # Get embedding dimension from model
                test_embedding = self.model.encode("test")
                self.embedding_dim = test_embedding.shape[0]
                logger.info(f"Embedding model loaded. Dimension: {self.embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                self.model = None
    
    def is_available(self) -> bool:
        """Check if embedding generation is available."""
        return self.model is not None and SENTENCE_TRANSFORMERS_AVAILABLE
    
    def embed_chunk(self, chunk: CodeChunk) -> Optional[np.ndarray]:
        """Generate embedding for a code chunk.
        
        Args:
            chunk: CodeChunk to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.is_available():
            return None
        
        try:
            # Combine file path and code for richer embedding
            text = f"File: {chunk.file_path}\n{chunk.code_content}"
            embedding = self.model.encode(text)
            return embedding
        
        except Exception as e:
            logger.warning(f"Failed to embed chunk {chunk}: {e}")
            return None
    
    def embed_chunks(self, chunks: List[CodeChunk]) -> List[np.ndarray]:
        """Generate embeddings for multiple code chunks using batch processing.
        
        Args:
            chunks: List of CodeChunk objects
            
        Returns:
            List of embedding vectors
        """
        if not self.is_available():
            return []
        
        if not chunks:
            return []
        
        batch_size = getattr(settings, "RAG_BATCH_SIZE", 50)
        embeddings = []
        
        # Process chunks in batches for better performance
        total = len(chunks)
        for batch_start in range(0, total, batch_size):
            batch_end = min(batch_start + batch_size, total)
            batch_chunks = chunks[batch_start:batch_end]
            
            logger.debug(f"Embedding batch {batch_start//batch_size + 1}/{(total + batch_size - 1)//batch_size} ({batch_start}-{batch_end}/{total})")
            
            # Prepare batch texts
            batch_texts = []
            for chunk in batch_chunks:
                text = f"File: {chunk.file_path}\n{chunk.code_content}"
                batch_texts.append(text)
            
            # Batch encode all texts at once
            try:
                batch_embeddings = self.model.encode(batch_texts)
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.warning(f"Failed to embed batch: {e}")
                # Fallback to one-by-one
                for chunk in batch_chunks:
                    embedding = self.embed_chunk(chunk)
                    if embedding is not None:
                        embeddings.append(embedding)
                    else:
                        embeddings.append(np.zeros(self.embedding_dim))
        
        return embeddings
            else:
                # Use zero vector if embedding fails
                embeddings.append(np.zeros(self.embedding_dim))
        
        return embeddings
    
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for arbitrary text (e.g., user query).
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if not self.is_available():
            return None
        
        try:
            embedding = self.model.encode(text)
            return embedding
        except Exception as e:
            logger.warning(f"Failed to embed text: {e}")
            return None


class VectorDatabase:
    """Vector database using FAISS for efficient similarity search."""
    
    def __init__(self, embedding_dim: int):
        """Initialize the vector database.
        
        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.index = None
        self.chunks = []
        self.chunk_ids = []
        
        if FAISS_AVAILABLE:
            try:
                # Create FAISS index (L2 distance)
                self.index = faiss.IndexFlatL2(embedding_dim)
                logger.info(f"Created FAISS index with dimension {embedding_dim}")
            except Exception as e:
                logger.error(f"Failed to create FAISS index: {e}")
                self.index = None
    
    def is_available(self) -> bool:
        """Check if vector database is available."""
        return self.index is not None and FAISS_AVAILABLE
    
    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[np.ndarray]) -> int:
        """Add code chunks and their embeddings to the database.
        
        Args:
            chunks: List of CodeChunk objects
            embeddings: List of embedding vectors
            
        Returns:
            Number of chunks added
        """
        if not self.is_available() or len(chunks) == 0:
            return 0
        
        if len(chunks) != len(embeddings):
            logger.error(f"Number of chunks ({len(chunks)}) doesn't match embeddings ({len(embeddings)})")
            return 0
        
        try:
            # Convert embeddings to numpy array
            embeddings_array = np.array(embeddings).astype("float32")
            
            # Add to FAISS index
            self.index.add(embeddings_array)
            
            # Store chunks for reference
            self.chunks.extend(chunks)
            self.chunk_ids.extend(range(len(self.chunk_ids), len(self.chunk_ids) + len(chunks)))
            
            logger.info(f"Added {len(chunks)} chunks to vector database")
            return len(chunks)
        
        except Exception as e:
            logger.error(f"Failed to add chunks to database: {e}")
            return 0
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[CodeChunk, float]]:
        """Search for similar code chunks.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of (CodeChunk, distance) tuples
        """
        if not self.is_available() or len(self.chunks) == 0:
            return []
        
        if query_embedding is None:
            return []
        
        try:
            # Reshape query for FAISS
            query = np.array([query_embedding]).astype("float32")
            
            # Search
            distances, indices = self.index.search(query, min(k, len(self.chunks)))
            
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0 and idx < len(self.chunks):
                    chunk = self.chunks[int(idx)]
                    # Convert L2 distance to similarity score (higher is better)
                    similarity = 1.0 / (1.0 + float(dist))
                    results.append((chunk, similarity))
            
            return results
        
        except Exception as e:
            logger.error(f"Failed to search vector database: {e}")
            return []
    
    def save(self, directory: str) -> bool:
        """Save the vector database to disk.
        
        Args:
            directory: Directory to save to
            
        Returns:
            True if successful
        """
        if not self.is_available():
            return False
        
        try:
            dir_path = Path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            index_file = dir_path / "index.faiss"
            faiss.write_index(self.index, str(index_file))
            
            # Save chunks metadata
            chunks_file = dir_path / "chunks.json"
            chunks_data = [chunk.to_dict() for chunk in self.chunks]
            with open(chunks_file, "w") as f:
                json.dump(chunks_data, f, indent=2)
            
            logger.info(f"Saved vector database to {directory}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save vector database: {e}")
            return False
    
    def load(self, directory: str) -> bool:
        """Load a vector database from disk.
        
        Args:
            directory: Directory to load from
            
        Returns:
            True if successful
        """
        if not FAISS_AVAILABLE:
            return False
        
        try:
            dir_path = Path(directory)
            
            # Load FAISS index
            index_file = dir_path / "index.faiss"
            if not index_file.exists():
                logger.debug(f"No FAISS index found at {index_file}")
                return False
            
            self.index = faiss.read_index(str(index_file))
            
            # Load chunks metadata
            chunks_file = dir_path / "chunks.json"
            if chunks_file.exists():
                with open(chunks_file, "r") as f:
                    chunks_data = json.load(f)
                self.chunks = [CodeChunk(**chunk_data) for chunk_data in chunks_data]
            
            logger.info(f"Loaded vector database from {directory}")
            logger.info(f"Loaded {len(self.chunks)} chunks from index")
            return True
        
        except Exception as e:
            logger.error(f"Failed to load vector database: {e}")
            return False


class RAGVectorStore:
    """Complete vector storage system for RAG."""
    
    def __init__(self, repo_name: str):
        """Initialize the RAG vector store.
        
        Args:
            repo_name: Name of the repository
        """
        self.repo_name = repo_name
        self.embedding_gen = EmbeddingGenerator()
        
        # Create database with appropriate dimension
        if self.embedding_gen.is_available():
            self.vector_db = VectorDatabase(self.embedding_gen.embedding_dim)
        else:
            self.vector_db = VectorDatabase(384)  # Default dimension for all-MiniLM-L6-v2
        
        self.index_dir = Path(settings.RAG_INDEX_PATH) / repo_name.replace("/", "_")
    
    def is_available(self) -> bool:
        """Check if RAG system is available."""
        return settings.ENABLE_RAG and self.embedding_gen.is_available() and self.vector_db.is_available()
    
    def index_chunks(self, chunks: List[CodeChunk]) -> bool:
        """Index code chunks.
        
        Args:
            chunks: List of code chunks to index
            
        Returns:
            True if successful
        """
        if not self.is_available():
            logger.warning("RAG system not available")
            return False
        
        logger.info(f"Indexing {len(chunks)} code chunks for {self.repo_name}")
        
        try:
            # Generate embeddings
            embeddings = self.embedding_gen.embed_chunks(chunks)
            
            if len(embeddings) != len(chunks):
                logger.error(f"Embedding count mismatch: {len(embeddings)} vs {len(chunks)}")
                return False
            
            # Add to vector database
            added = self.vector_db.add_chunks(chunks, embeddings)
            
            # Save to disk
            self.vector_db.save(str(self.index_dir))
            
            logger.info(f"Successfully indexed {added} chunks")
            return True
        
        except Exception as e:
            logger.error(f"Failed to index chunks: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_index(self) -> bool:
        """Load existing index from disk.
        
        Args:
            Returns:
                True if index was loaded
        """
        if not self.is_available():
            return False
        
        if not self.index_dir.exists():
            logger.debug(f"No index found for {self.repo_name}")
            return False
        
        return self.vector_db.load(str(self.index_dir))
    
    def search(self, query: str, k: int = None) -> List[Tuple[CodeChunk, float]]:
        """Search for relevant code chunks.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of (CodeChunk, similarity_score) tuples
        """
        if not self.is_available():
            return []
        
        k = k or settings.RAG_TOP_K
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_gen.embed_text(query)
            
            if query_embedding is None:
                return []
            
            # Search vector database
            results = self.vector_db.search(query_embedding, k=k)
            
            # Filter by similarity threshold
            filtered_results = [
                (chunk, score) for chunk, score in results
                if score >= settings.RAG_SIMILARITY_THRESHOLD
            ]
            
            logger.debug(f"Search returned {len(filtered_results)} results (threshold: {settings.RAG_SIMILARITY_THRESHOLD})")
            return filtered_results
        
        except Exception as e:
            logger.error(f"Failed to search vector database: {e}")
            return []
