"""
Red Thread Engine - Logical Continuity Checker for PHDx

Uses vector embeddings to index thesis drafts and detect potential logical
contradictions, terminology shifts, and inconsistencies in new writing.

Supports:
  - ChromaDB (local development)
  - Pinecone (cloud deployment on Streamlit Cloud)

Primary Functions:
  - index_existing_chapters(): Index all .docx files from /drafts
  - verify_consistency(): Check new text against 30k+ word corpus
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from docx import Document
from dotenv import load_dotenv

# Import vector store abstraction
from core.vector_store import get_vector_store, VectorStoreBase
from core.secrets_utils import get_secret

# Load environment variables
load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DRAFTS_DIR = ROOT_DIR / "drafts"
DATA_DIR = ROOT_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"

# Collection names
COLLECTION_NAME = "thesis_paragraphs"
CHAPTERS_COLLECTION = "thesis_chapters"


class RedThreadEngine:
    """
    Engine for maintaining logical continuity across thesis drafts.

    Uses vector embeddings to find semantically similar passages and
    Claude to analyze potential contradictions.

    Automatically uses Pinecone (cloud) if PINECONE_API_KEY is set,
    otherwise falls back to ChromaDB (local).
    """

    def __init__(self, use_local: bool = False):
        """
        Initialize the Red Thread Engine.

        Args:
            use_local: Force use of local ChromaDB even if Pinecone is configured
        """
        # Initialize vector store (auto-selects Pinecone or ChromaDB)
        if use_local:
            from core.vector_store import ChromaVectorStore
            self.vector_store = ChromaVectorStore(COLLECTION_NAME)
        else:
            self.vector_store = get_vector_store(COLLECTION_NAME)

        self.backend = self.vector_store.backend

        # Initialize Anthropic client if API key available
        api_key = get_secret("ANTHROPIC_API_KEY")
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

            # Upsert to vector store (update if exists, insert if not)
            self.vector_store.upsert(
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
            "files": [],
            "waiting_for_content": False
        }

        if not drafts_dir.exists():
            print(f"Drafts directory not found: {drafts_dir}")
            drafts_dir.mkdir(parents=True, exist_ok=True)
            stats["waiting_for_content"] = True
            return stats

        docx_files = list(drafts_dir.glob("*.docx"))

        # Empty Directory Grace - friendly message instead of error
        if not docx_files:
            print("\n" + "=" * 60)
            print("Waiting for your first 30k words...")
            print("=" * 60)
            print("\nThe Red Thread Engine needs thesis content to check for")
            print("logical contradictions and maintain argument consistency.")
            print("\nTo get started:")
            print("  1. Add your thesis chapter drafts (.docx) to the /drafts folder")
            print("  2. Re-run indexing to build your semantic corpus")
            print(f"\nDrafts folder: {drafts_dir}")
            print("=" * 60 + "\n")
            stats["waiting_for_content"] = True
            return stats

        for docx_file in docx_files:
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
        if self.vector_store.count() == 0:
            return []

        results = self.vector_store.query(
            query_text=text,
            n_results=min(n_results, self.vector_store.count())
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
        stats = self.vector_store.get_stats()
        stats["total_paragraphs"] = self.vector_store.count()
        return stats

    def clear_index(self):
        """Clear all indexed content."""
        self.vector_store.delete_all()

    # =========================================================================
    # PRIMARY API FUNCTIONS
    # =========================================================================

    def index_existing_chapters(self, drafts_dir: Path = DRAFTS_DIR) -> dict:
        """
        Index all .docx files from /drafts folder into ChromaDB vector store.

        This function reads all thesis chapter files, extracts paragraphs,
        generates embeddings, and stores them for semantic search.

        Args:
            drafts_dir: Path to drafts folder (default: PHDx/drafts/)

        Returns:
            dict: Indexing report with statistics
                {
                    "success": bool,
                    "timestamp": str,
                    "total_files": int,
                    "total_paragraphs": int,
                    "total_words": int,
                    "chapters": [
                        {"filename": str, "paragraphs": int, "words": int}
                    ],
                    "storage_path": str
                }
        """
        report = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "total_paragraphs": 0,
            "total_words": 0,
            "chapters": [],
            "storage_path": str(CHROMA_DIR)
        }

        # Ensure directories exist
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        if not drafts_dir.exists():
            drafts_dir.mkdir(parents=True, exist_ok=True)
            report["error"] = f"Created empty drafts directory at {drafts_dir}"
            return report

        # Find all .docx files
        docx_files = list(drafts_dir.glob("*.docx"))

        if not docx_files:
            report["error"] = "No .docx files found in drafts folder"
            return report

        print(f"\n{'='*60}")
        print("PHDx Red Thread Engine - Indexing Chapters")
        print(f"{'='*60}")
        print(f"Source: {drafts_dir}")
        print(f"Storage: {CHROMA_DIR}")
        print(f"Files found: {len(docx_files)}")
        print("-" * 60)

        for docx_file in docx_files:
            try:
                # Read document
                doc = Document(docx_file)
                full_text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])

                # Extract paragraphs
                paragraphs = self._extract_paragraphs(full_text, min_words=15)

                if not paragraphs:
                    print(f"  ⚠ {docx_file.name}: No paragraphs extracted")
                    continue

                # Calculate word count
                word_count = sum(len(p.split()) for p in paragraphs)

                # Create unique IDs with chapter prefix
                chapter_name = docx_file.stem
                ids = [f"{chapter_name}_para_{i}" for i in range(len(paragraphs))]

                # Rich metadata for each paragraph
                metadatas = [
                    {
                        "source_file": docx_file.name,
                        "chapter": chapter_name,
                        "paragraph_index": i,
                        "word_count": len(p.split()),
                        "char_count": len(p),
                        "indexed_at": datetime.now().isoformat()
                    }
                    for i, p in enumerate(paragraphs)
                ]

                # Upsert to vector store (update if exists)
                self.vector_store.upsert(
                    ids=ids,
                    documents=paragraphs,
                    metadatas=metadatas
                )

                # Update report
                report["total_files"] += 1
                report["total_paragraphs"] += len(paragraphs)
                report["total_words"] += word_count
                report["chapters"].append({
                    "filename": docx_file.name,
                    "chapter": chapter_name,
                    "paragraphs": len(paragraphs),
                    "words": word_count
                })

                print(f"  ✓ {docx_file.name}: {len(paragraphs)} paragraphs, {word_count:,} words")

            except Exception as e:
                print(f"  ✗ {docx_file.name}: Error - {e}")
                report["chapters"].append({
                    "filename": docx_file.name,
                    "error": str(e)
                })

        report["success"] = report["total_paragraphs"] > 0

        print("-" * 60)
        print(f"Total: {report['total_paragraphs']} paragraphs, {report['total_words']:,} words")
        print(f"{'='*60}\n")

        return report

    def verify_consistency(self, new_draft_text: str) -> dict:
        """
        Verify consistency of new draft text against existing 30k+ word corpus.

        This function:
        1. Searches the vector store for semantically related sections
        2. Uses Claude to identify contradictions or terminology shifts
        3. Returns a detailed Consistency Report JSON

        Args:
            new_draft_text: The new text to verify against existing corpus

        Returns:
            dict: Consistency Report
                {
                    "report_id": str,
                    "timestamp": str,
                    "status": "consistent" | "issues_found" | "error",
                    "overall_score": float (0-100),
                    "new_text_preview": str,
                    "corpus_stats": {
                        "total_indexed": int,
                        "sections_analyzed": int
                    },
                    "related_sections": [
                        {
                            "text": str,
                            "source": str,
                            "similarity": float
                        }
                    ],
                    "issues": [
                        {
                            "type": "contradiction" | "terminology_shift" | "inconsistency",
                            "severity": "high" | "medium" | "low",
                            "description": str,
                            "new_text_claim": str,
                            "existing_claim": str,
                            "source_file": str,
                            "recommendation": str
                        }
                    ],
                    "terminology_analysis": {
                        "key_terms_new": [str],
                        "potential_shifts": [str]
                    },
                    "summary": str
                }
        """
        import hashlib

        # Generate report ID
        report_id = hashlib.md5(
            f"{new_draft_text[:100]}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        report = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "overall_score": 0,
            "new_text_preview": new_draft_text[:200] + "..." if len(new_draft_text) > 200 else new_draft_text,
            "corpus_stats": {
                "total_indexed": self.vector_store.count(),
                "sections_analyzed": 0
            },
            "related_sections": [],
            "issues": [],
            "terminology_analysis": {
                "key_terms_new": [],
                "potential_shifts": []
            },
            "summary": ""
        }

        # Check if we have indexed content
        if self.vector_store.count() == 0:
            report["status"] = "error"
            report["summary"] = "No indexed content. Run index_existing_chapters() first."
            return report

        # Check for Claude API
        if not self.claude_client:
            report["status"] = "error"
            report["summary"] = "ANTHROPIC_API_KEY not configured. Cannot perform AI analysis."
            return report

        # Find semantically related sections (top 10)
        try:
            results = self.vector_store.query(
                query_text=new_draft_text,
                n_results=min(10, self.vector_store.count())
            )

            related_sections = []
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                similarity = round(1 / (1 + dist), 3)
                related_sections.append({
                    "text": doc[:500] + "..." if len(doc) > 500 else doc,
                    "full_text": doc,
                    "source": meta.get("source_file", "unknown"),
                    "chapter": meta.get("chapter", "unknown"),
                    "paragraph_index": meta.get("paragraph_index", 0),
                    "similarity": similarity
                })

            report["related_sections"] = [
                {"text": s["text"], "source": s["source"], "similarity": s["similarity"]}
                for s in related_sections
            ]
            report["corpus_stats"]["sections_analyzed"] = len(related_sections)

        except Exception as e:
            report["status"] = "error"
            report["summary"] = f"Vector search failed: {str(e)}"
            return report

        # Prepare context for Claude analysis
        context_for_claude = "\n\n---\n\n".join([
            f"[SOURCE: {s['source']}, Chapter: {s['chapter']}, Similarity: {s['similarity']}]\n{s['full_text']}"
            for s in related_sections[:7]  # Top 7 most relevant
        ])

        # Claude prompt for deep consistency analysis
        analysis_prompt = f"""You are an academic consistency analyzer for a PhD thesis. Analyze the NEW DRAFT TEXT against EXISTING THESIS SECTIONS.

Your task:
1. Identify any logical CONTRADICTIONS (claims that conflict)
2. Detect TERMINOLOGY SHIFTS (same concept, different terms)
3. Find INCONSISTENCIES (methodology, findings, or argumentation conflicts)
4. Extract KEY TERMS from the new text
5. Provide an overall consistency score (0-100)

NEW DRAFT TEXT:
{new_draft_text}

EXISTING THESIS SECTIONS (from ~30,000 word corpus):
{context_for_claude}

Respond with a JSON object (no markdown, just raw JSON):
{{
    "overall_score": <0-100 integer>,
    "issues": [
        {{
            "type": "contradiction" | "terminology_shift" | "inconsistency",
            "severity": "high" | "medium" | "low",
            "description": "<clear explanation>",
            "new_text_claim": "<quote from new text>",
            "existing_claim": "<quote from existing text>",
            "source_file": "<filename>",
            "recommendation": "<how to resolve>"
        }}
    ],
    "terminology_analysis": {{
        "key_terms_new": ["<term1>", "<term2>", ...],
        "potential_shifts": ["<term used differently>", ...]
    }},
    "summary": "<2-3 sentence summary of consistency status>"
}}

If the text is fully consistent, return an empty issues array and score of 100.
Return ONLY valid JSON."""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": analysis_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Clean potential markdown wrapping
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            # Parse Claude's response
            analysis = json.loads(response_text)

            # Populate report
            report["overall_score"] = analysis.get("overall_score", 0)
            report["issues"] = analysis.get("issues", [])
            report["terminology_analysis"] = analysis.get("terminology_analysis", {
                "key_terms_new": [],
                "potential_shifts": []
            })
            report["summary"] = analysis.get("summary", "Analysis complete.")

            # Determine status
            if not report["issues"]:
                report["status"] = "consistent"
            else:
                high_severity = any(i.get("severity") == "high" for i in report["issues"])
                report["status"] = "issues_found"
                if high_severity:
                    report["status"] = "critical_issues"

        except json.JSONDecodeError as e:
            report["status"] = "error"
            report["summary"] = f"Failed to parse AI response: {str(e)}"
            report["raw_response"] = response_text if 'response_text' in dir() else None

        except Exception as e:
            report["status"] = "error"
            report["summary"] = f"Analysis failed: {str(e)}"

        return report

    def get_consistency_report_for_ui(self, new_draft_text: str) -> dict:
        """
        Wrapper for verify_consistency that formats output for Streamlit UI.

        Returns a simplified report optimized for display.
        Includes thematic threshold warning when similarity < 50%.
        """
        full_report = self.verify_consistency(new_draft_text)

        # Calculate average similarity from related sections
        related_sections = full_report.get("related_sections", [])
        avg_similarity = 0
        if related_sections:
            avg_similarity = sum(s.get("similarity", 0) for s in related_sections) / len(related_sections)
            avg_similarity = round(avg_similarity * 100, 1)  # Convert to percentage

        # Thematic Threshold Warning - trigger when similarity < 50%
        low_consistency_warning = None
        if avg_similarity < 50 and related_sections:
            low_consistency_warning = {
                "triggered": True,
                "message": "Low Argument Consistency detected. Check Chapter 2 for contradictions.",
                "avg_similarity": avg_similarity,
                "recommendation": "Your new text may be diverging from your thesis argument. Review your Literature Review chapter to ensure conceptual alignment."
            }

        # Create UI-friendly version
        ui_report = {
            "status": full_report["status"],
            "score": full_report["overall_score"],
            "score_label": self._score_to_label(full_report["overall_score"]),
            "summary": full_report["summary"],
            "issue_count": len(full_report["issues"]),
            "issues_by_severity": {
                "high": [i for i in full_report["issues"] if i.get("severity") == "high"],
                "medium": [i for i in full_report["issues"] if i.get("severity") == "medium"],
                "low": [i for i in full_report["issues"] if i.get("severity") == "low"]
            },
            "key_terms": full_report["terminology_analysis"].get("key_terms_new", []),
            "terminology_warnings": full_report["terminology_analysis"].get("potential_shifts", []),
            "related_count": len(full_report["related_sections"]),
            "avg_similarity_percent": avg_similarity,
            "low_consistency_warning": low_consistency_warning,
            "full_report": full_report  # Include full report for detailed view
        }

        return ui_report

    def _score_to_label(self, score: int) -> str:
        """Convert numeric score to human-readable label."""
        if score >= 95:
            return "Excellent"
        elif score >= 85:
            return "Good"
        elif score >= 70:
            return "Fair"
        elif score >= 50:
            return "Needs Review"
        else:
            return "Critical Issues"


# =============================================================================
# STANDALONE FUNCTIONS (for direct import)
# =============================================================================

def index_existing_chapters(drafts_dir: Path = DRAFTS_DIR) -> dict:
    """
    Standalone function to index all chapters from /drafts folder.

    Usage:
        from core.red_thread import index_existing_chapters
        report = index_existing_chapters()
    """
    engine = RedThreadEngine()
    return engine.index_existing_chapters(drafts_dir)


def verify_consistency(new_draft_text: str) -> dict:
    """
    Standalone function to verify consistency of new text.

    Usage:
        from core.red_thread import verify_consistency
        report = verify_consistency("Your new paragraph here...")

    Returns:
        Consistency Report JSON
    """
    engine = RedThreadEngine()
    return engine.verify_consistency(new_draft_text)


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
