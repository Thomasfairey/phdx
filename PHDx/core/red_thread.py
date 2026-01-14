"""
Red Thread Engine - Logical Continuity Checker for PHDx

Uses ChromaDB to index thesis drafts and detect potential logical
contradictions or inconsistencies in new writing.
"""

import json
import os
import re
from pathlib import Path
from typing import Optional

import anthropic
import chromadb
from chromadb.utils import embedding_functions
from docx import Document
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DRAFTS_DIR = ROOT_DIR / "drafts"
DATA_DIR = ROOT_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"

# Collection name
COLLECTION_NAME = "thesis_paragraphs"


class RedThreadEngine:
    """
    Engine for maintaining logical continuity across thesis drafts.

    Uses vector embeddings to find semantically similar passages and
    Claude to analyze potential contradictions.
    """

    def __init__(self):
        """Initialize the Red Thread Engine with ChromaDB."""
        # Ensure directories exist
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn,
            metadata={"description": "Thesis paragraphs for continuity checking"}
        )

        # Initialize Anthropic client if API key available
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def _extract_paragraphs(self, text: str, min_words: int = 20) -> list[str]:
        """
        Extract meaningful paragraphs from text.

        Args:
            text: Raw text content
            min_words: Minimum words for a paragraph to be included

        Returns:
            List of paragraph strings
        """
        # Split by double newlines or paragraph breaks
        paragraphs = re.split(r'\n\s*\n', text)

        # Filter and clean
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para.split()) >= min_words:
                cleaned.append(para)

        return cleaned

    def index_document(self, filepath: Path) -> int:
        """
        Index a single .docx document into ChromaDB.

        Args:
            filepath: Path to the .docx file

        Returns:
            Number of paragraphs indexed
        """
        try:
            doc = Document(filepath)
            full_text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            paragraphs = self._extract_paragraphs(full_text)

            if not paragraphs:
                return 0

            # Create unique IDs based on file and paragraph index
            ids = [f"{filepath.stem}_{i}" for i in range(len(paragraphs))]

            # Metadata for each paragraph
            metadatas = [
                {
                    "source_file": filepath.name,
                    "paragraph_index": i,
                    "word_count": len(p.split())
                }
                for i, p in enumerate(paragraphs)
            ]

            # Upsert to collection (update if exists, insert if not)
            self.collection.upsert(
                ids=ids,
                documents=paragraphs,
                metadatas=metadatas
            )

            return len(paragraphs)

        except Exception as e:
            print(f"Error indexing {filepath.name}: {e}")
            return 0

    def index_drafts_folder(self, drafts_dir: Path = DRAFTS_DIR) -> dict:
        """
        Index all .docx files in the drafts folder.

        Returns:
            Dict with indexing statistics
        """
        stats = {
            "files_processed": 0,
            "paragraphs_indexed": 0,
            "files": []
        }

        if not drafts_dir.exists():
            print(f"Drafts directory not found: {drafts_dir}")
            return stats

        for docx_file in drafts_dir.glob("*.docx"):
            count = self.index_document(docx_file)
            stats["files_processed"] += 1
            stats["paragraphs_indexed"] += count
            stats["files"].append({
                "name": docx_file.name,
                "paragraphs": count
            })
            print(f"Indexed {docx_file.name}: {count} paragraphs")

        return stats

    def find_similar_passages(
        self,
        text: str,
        n_results: int = 5,
        threshold: float = 0.7
    ) -> list[dict]:
        """
        Find passages in the index similar to the given text.

        Args:
            text: Text to compare against
            n_results: Maximum number of results to return
            threshold: Minimum similarity score (0-1, higher = more similar)

        Returns:
            List of similar passages with metadata and scores
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[text],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )

        similar = []
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # Convert distance to similarity (ChromaDB uses L2 distance by default)
            # Lower distance = more similar
            similarity = 1 / (1 + dist)

            if similarity >= threshold:
                similar.append({
                    "text": doc,
                    "source_file": meta["source_file"],
                    "paragraph_index": meta["paragraph_index"],
                    "similarity": round(similarity, 3),
                    "distance": round(dist, 3)
                })

        return similar

    def check_continuity(self, new_text: str) -> list[dict]:
        """
        Check a new paragraph for potential logical contradictions
        against the indexed thesis content.

        Args:
            new_text: The new paragraph to check

        Returns:
            List of potential contradictions with explanations
        """
        # Find similar passages
        similar_passages = self.find_similar_passages(new_text, n_results=10, threshold=0.3)

        if not similar_passages:
            return [{
                "status": "no_context",
                "message": "No similar passages found in index. Consider indexing your drafts first."
            }]

        if not self.claude_client:
            return [{
                "status": "no_api_key",
                "message": "ANTHROPIC_API_KEY not set. Cannot perform contradiction analysis.",
                "similar_passages": similar_passages[:5]
            }]

        # Prepare context for Claude
        context_texts = "\n\n---\n\n".join([
            f"[From {p['source_file']}, similarity: {p['similarity']}]\n{p['text']}"
            for p in similar_passages[:5]
        ])

        prompt = f"""Analyze the following NEW PARAGRAPH against EXISTING PASSAGES from a PhD thesis.
Identify any potential logical contradictions, inconsistencies, or conflicts in claims, methodology, or findings.

NEW PARAGRAPH:
{new_text}

EXISTING PASSAGES FROM THESIS:
{context_texts}

Respond with a JSON array of potential issues. Each issue should have:
- "type": "contradiction" | "inconsistency" | "tension" | "none"
- "severity": "high" | "medium" | "low"
- "new_claim": The claim in the new paragraph
- "existing_claim": The conflicting claim from existing text
- "source_file": Which file contains the conflict
- "explanation": Brief explanation of the issue
- "suggestion": How to resolve it

If there are no issues, return: [{{"type": "none", "message": "No contradictions detected"}}]

Respond with ONLY valid JSON, no additional text."""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            # Parse JSON response
            try:
                contradictions = json.loads(response_text)
                return contradictions
            except json.JSONDecodeError:
                return [{
                    "status": "parse_error",
                    "raw_response": response_text
                }]

        except Exception as e:
            return [{
                "status": "error",
                "message": str(e)
            }]

    def get_stats(self) -> dict:
        """Get statistics about the current index."""
        return {
            "total_paragraphs": self.collection.count(),
            "collection_name": COLLECTION_NAME,
            "storage_path": str(CHROMA_DIR)
        }

    def clear_index(self):
        """Clear all indexed content."""
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self.embedding_fn
        )


def main():
    """CLI for Red Thread Engine."""
    print("=" * 60)
    print("PHDx Red Thread Engine - Logical Continuity Checker")
    print("=" * 60)

    engine = RedThreadEngine()

    # Index drafts
    print("\n[1] Indexing drafts folder...")
    stats = engine.index_drafts_folder()
    print(f"Indexed {stats['paragraphs_indexed']} paragraphs from {stats['files_processed']} files")

    # Show stats
    print("\n[2] Current index stats:")
    index_stats = engine.get_stats()
    print(f"  Total paragraphs: {index_stats['total_paragraphs']}")
    print(f"  Storage: {index_stats['storage_path']}")

    # Demo check if we have content
    if index_stats['total_paragraphs'] > 0:
        print("\n[3] Ready for continuity checks!")
        print("Use: engine.check_continuity('Your new paragraph here...')")
    else:
        print("\n[3] No content indexed. Add .docx files to drafts/ folder.")


if __name__ == "__main__":
    main()
