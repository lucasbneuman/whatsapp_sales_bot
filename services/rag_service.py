"""RAG service for document upload and retrieval."""

import os
from pathlib import Path
from typing import List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.document_loaders import PyMuPDFLoader, TextLoader, UnstructuredWordDocumentLoader
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from utils.logging_config import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations."""

    def __init__(self, openai_api_key: Optional[str] = None, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG service.

        Args:
            openai_api_key: OpenAI API key for embeddings
            persist_directory: Directory to persist ChromaDB data
        """
        if not CHROMADB_AVAILABLE:
            logger.warning("ChromaDB not available. RAG functionality disabled. Install Visual C++ Build Tools and chromadb to enable.")
            self.enabled = False
            return

        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be provided or set in environment")

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key,
        )

        # Initialize ChromaDB
        self.persist_directory = persist_directory
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection_name = "sales_documents"
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection '{self.collection_name}'")
        except:
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info(f"Created new collection '{self.collection_name}'")

        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        self.enabled = True
        logger.info("RAG service initialized")

    async def upload_document(self, file_path: str) -> int:
        """
        Upload and process a single document.

        Args:
            file_path: Path to the document file

        Returns:
            Number of chunks created

        Raises:
            ValueError: If file format is not supported
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path_obj.suffix.lower()

        try:
            # Load document based on file type
            if extension == ".pdf":
                loader = PyMuPDFLoader(file_path)
            elif extension == ".txt":
                loader = TextLoader(file_path)
            elif extension in [".doc", ".docx"]:
                loader = UnstructuredWordDocumentLoader(file_path)
            else:
                raise ValueError(f"Unsupported file format: {extension}")

            logger.info(f"Loading document: {file_path_obj.name}")
            documents = loader.load()

            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Split document into {len(chunks)} chunks")

            # Generate embeddings and store
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.embeddings.embed_query(chunk.page_content)

                # Create unique ID
                doc_id = f"{file_path_obj.stem}_{i}"

                # Add to ChromaDB
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk.page_content],
                    metadatas=[{"source": file_path_obj.name, "chunk_index": i}],
                )

            logger.info(f"Successfully uploaded {len(chunks)} chunks from {file_path_obj.name}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error uploading document {file_path}: {e}")
            raise

    async def upload_documents(self, file_paths: List[str]) -> int:
        """
        Upload multiple documents.

        Args:
            file_paths: List of file paths

        Returns:
            Total number of chunks created
        """
        total_chunks = 0
        for file_path in file_paths:
            try:
                chunks = await self.upload_document(file_path)
                total_chunks += chunks
            except Exception as e:
                logger.error(f"Failed to upload {file_path}: {e}")
                continue

        logger.info(f"Uploaded {len(file_paths)} documents, total {total_chunks} chunks")
        return total_chunks

    async def retrieve_context(self, query: str, k: int = 3) -> str:
        """
        Retrieve relevant context for a query.

        Args:
            query: Search query
            k: Number of top results to retrieve

        Returns:
            Concatenated context from top-k chunks
        """
        if not self.enabled:
            return ""

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
            )

            # Extract and format results
            if results["documents"] and len(results["documents"][0]) > 0:
                contexts = results["documents"][0]
                context_text = "\n\n---\n\n".join(contexts)
                logger.info(f"Retrieved {len(contexts)} relevant chunks for query")
                return context_text
            else:
                logger.info("No relevant context found")
                return ""

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""

    def get_collection_stats(self) -> dict:
        """
        Get statistics about the document collection.

        Returns:
            Dict with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"total_chunks": 0, "collection_name": self.collection_name}

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name)
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise


# Global instance (will be initialized in app.py)
rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get the global RAG service instance."""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service
