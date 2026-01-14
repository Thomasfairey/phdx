"""
Vector Store Abstraction for PHDx

Provides a unified interface for vector storage that works with:
- ChromaDB (local development)
- Pinecone (cloud deployment on Streamlit Cloud)

Automatically selects the appropriate backend based on environment variables.
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from abc import ABC, abstractmethod

from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"


class VectorStoreBase(ABC):
    """Abstract base class for vector stores."""

    @abstractmethod
    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> int:
        """Insert or update documents."""
        pass

    @abstractmethod
    def query(self, query_text: str, n_results: int = 5) -> dict:
        """Query for similar documents."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return number of documents in store."""
        pass

    @abstractmethod
    def delete_all(self) -> None:
        """Clear all documents."""
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """Get store statistics."""
        pass


class ChromaVectorStore(VectorStoreBase):
    """Local ChromaDB vector store for development."""

    def __init__(self, collection_name: str = "thesis_paragraphs"):
        import chromadb
        from chromadb.utils import embedding_functions

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
            metadata={"description": "PHDx thesis paragraphs"}
        )
        self.backend = "chromadb"

    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> int:
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(ids)

    def query(self, query_text: str, n_results: int = 5) -> dict:
        if self.collection.count() == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        return self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

    def count(self) -> int:
        return self.collection.count()

    def delete_all(self) -> None:
        # Delete and recreate collection
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name="thesis_paragraphs",
            embedding_function=self.embedding_fn
        )

    def get_stats(self) -> dict:
        return {
            "backend": "chromadb",
            "total_documents": self.collection.count(),
            "storage_path": str(CHROMA_DIR),
            "collection_name": self.collection.name
        }


class PineconeVectorStore(VectorStoreBase):
    """
    Pinecone cloud vector store for production deployment.

    Requires:
        PINECONE_API_KEY: Your Pinecone API key
        PINECONE_INDEX: Index name (default: phdx-thesis)
    """

    def __init__(self, index_name: str = None):
        from pinecone import Pinecone, ServerlessSpec
        from sentence_transformers import SentenceTransformer

        self.api_key = os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY not set in environment")

        self.index_name = index_name or os.getenv("PINECONE_INDEX", "phdx-thesis")
        self.backend = "pinecone"

        # Initialize Pinecone
        self.pc = Pinecone(api_key=self.api_key)

        # Create index if it doesn't exist
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            print(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # all-MiniLM-L6-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )

        self.index = self.pc.Index(self.index_name)

        # Initialize embedding model (same as ChromaDB default)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')

        # Local metadata cache (Pinecone doesn't store full text)
        self._metadata_cache = {}
        self._document_cache = {}

    def _generate_id(self, text: str, index: int) -> str:
        """Generate a consistent ID for a document."""
        return hashlib.md5(f"{text[:100]}_{index}".encode()).hexdigest()[:16]

    def upsert(self, ids: list[str], documents: list[str], metadatas: list[dict]) -> int:
        # Generate embeddings
        embeddings = self.encoder.encode(documents).tolist()

        # Prepare vectors for Pinecone
        vectors = []
        for i, (doc_id, doc, meta, emb) in enumerate(zip(ids, documents, metadatas, embeddings)):
            # Store document text in metadata (Pinecone metadata has size limits)
            # Truncate long documents for metadata storage
            meta_with_text = {
                **meta,
                "text_preview": doc[:500] if len(doc) > 500 else doc,
                "text_hash": hashlib.md5(doc.encode()).hexdigest()
            }

            vectors.append({
                "id": doc_id,
                "values": emb,
                "metadata": meta_with_text
            })

            # Cache full document locally
            self._document_cache[doc_id] = doc
            self._metadata_cache[doc_id] = meta

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)

        return len(vectors)

    def query(self, query_text: str, n_results: int = 5) -> dict:
        # Generate query embedding
        query_embedding = self.encoder.encode([query_text])[0].tolist()

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=n_results,
            include_metadata=True
        )

        # Format results to match ChromaDB output format
        documents = []
        metadatas = []
        distances = []

        for match in results.matches:
            doc_id = match.id

            # Get full document from cache or use preview
            if doc_id in self._document_cache:
                documents.append(self._document_cache[doc_id])
            else:
                documents.append(match.metadata.get("text_preview", ""))

            # Get metadata
            meta = {k: v for k, v in match.metadata.items()
                    if k not in ["text_preview", "text_hash"]}
            metadatas.append(meta)

            # Convert similarity score to distance (for compatibility)
            # Pinecone returns similarity (0-1), ChromaDB uses distance
            distances.append(1 - match.score)

        return {
            "documents": [documents],
            "metadatas": [metadatas],
            "distances": [distances]
        }

    def count(self) -> int:
        stats = self.index.describe_index_stats()
        return stats.total_vector_count

    def delete_all(self) -> None:
        self.index.delete(delete_all=True)
        self._document_cache.clear()
        self._metadata_cache.clear()

    def get_stats(self) -> dict:
        stats = self.index.describe_index_stats()
        return {
            "backend": "pinecone",
            "total_documents": stats.total_vector_count,
            "index_name": self.index_name,
            "dimension": stats.dimension,
            "namespaces": dict(stats.namespaces) if stats.namespaces else {}
        }


def get_vector_store(collection_name: str = "thesis_paragraphs") -> VectorStoreBase:
    """
    Factory function to get the appropriate vector store.

    Returns Pinecone if PINECONE_API_KEY is set, otherwise ChromaDB.

    Usage:
        from core.vector_store import get_vector_store
        store = get_vector_store()
        store.upsert(ids, documents, metadatas)
        results = store.query("search text")
    """
    pinecone_key = os.getenv("PINECONE_API_KEY")

    if pinecone_key:
        try:
            print("Using Pinecone vector store (cloud mode)")
            return PineconeVectorStore()
        except Exception as e:
            print(f"Pinecone initialization failed: {e}")
            print("Falling back to ChromaDB")
            return ChromaVectorStore(collection_name)
    else:
        print("Using ChromaDB vector store (local mode)")
        return ChromaVectorStore(collection_name)


# =============================================================================
# CLI for testing
# =============================================================================

def main():
    """Test vector store functionality."""
    print("=" * 60)
    print("PHDx Vector Store Test")
    print("=" * 60)

    store = get_vector_store()
    print(f"\nBackend: {store.backend}")
    print(f"Stats: {store.get_stats()}")

    # Test upsert
    test_docs = [
        "The proliferation of digital surveillance in urban environments.",
        "Foucault's panopticon provides a framework for understanding modern surveillance.",
        "Smart city initiatives rely heavily on data analytics for governance."
    ]
    test_ids = [f"test_{i}" for i in range(len(test_docs))]
    test_meta = [{"source": "test", "index": i} for i in range(len(test_docs))]

    print("\nUpserting test documents...")
    store.upsert(test_ids, test_docs, test_meta)
    print(f"Document count: {store.count()}")

    # Test query
    print("\nQuerying for 'surveillance capitalism'...")
    results = store.query("surveillance capitalism", n_results=2)

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        similarity = 1 / (1 + dist)
        print(f"\n  [{i+1}] Similarity: {similarity:.3f}")
        print(f"      {doc[:80]}...")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
