"""
Citations Manager - Zotero Integration for PHDx

Connects to Zotero library and provides intelligent paper recommendations
based on the current drafting context.
"""

import json
import os
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv
from pyzotero import zotero

# Load environment variables
load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "local_cache"


class ZoteroSentinel:
    """
    Intelligent citation assistant that monitors drafting context
    and suggests relevant papers from Zotero library.
    """

    def __init__(
        self,
        library_id: Optional[str] = None,
        library_type: str = "user",
        api_key: Optional[str] = None
    ):
        """
        Initialize Zotero connection.

        Args:
            library_id: Zotero library ID (from .env or parameter)
            library_type: "user" or "group"
            api_key: Zotero API key (from .env or parameter)
        """
        self.library_id = library_id or os.getenv("ZOTERO_LIBRARY_ID")
        self.api_key = api_key or os.getenv("ZOTERO_API_KEY")
        self.library_type = library_type

        self.zot = None
        self.connected = False
        self.items_cache = []

        # Initialize Anthropic for relevance analysis
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None

        # Attempt connection if credentials available
        if self.library_id and self.api_key:
            self._connect()

    def _connect(self) -> bool:
        """Establish connection to Zotero."""
        try:
            self.zot = zotero.Zotero(
                self.library_id,
                self.library_type,
                self.api_key
            )
            # Test connection
            self.zot.num_items()
            self.connected = True
            return True
        except Exception as e:
            print(f"Zotero connection failed: {e}")
            self.connected = False
            return False

    def get_connection_status(self) -> dict:
        """Get current connection status."""
        return {
            "connected": self.connected,
            "library_id": self.library_id,
            "library_type": self.library_type,
            "has_api_key": bool(self.api_key)
        }

    def fetch_all_items(self, item_type: str = "journalArticle") -> list[dict]:
        """
        Fetch all items from Zotero library.

        Args:
            item_type: Filter by item type (journalArticle, book, etc.)

        Returns:
            List of simplified item dictionaries
        """
        if not self.connected:
            return []

        try:
            # Fetch items (Zotero API handles pagination)
            raw_items = self.zot.everything(self.zot.items(itemType=item_type))

            items = []
            for item in raw_items:
                data = item.get("data", {})
                items.append({
                    "key": data.get("key", ""),
                    "title": data.get("title", "Untitled"),
                    "authors": self._format_authors(data.get("creators", [])),
                    "year": data.get("date", "")[:4] if data.get("date") else "",
                    "abstract": data.get("abstractNote", ""),
                    "publication": data.get("publicationTitle", ""),
                    "doi": data.get("DOI", ""),
                    "tags": [t.get("tag", "") for t in data.get("tags", [])],
                    "item_type": data.get("itemType", "")
                })

            self.items_cache = items
            return items

        except Exception as e:
            print(f"Error fetching items: {e}")
            return []

    def _format_authors(self, creators: list) -> str:
        """Format creator list into author string."""
        authors = []
        for c in creators:
            if c.get("creatorType") == "author":
                if c.get("name"):
                    authors.append(c["name"])
                else:
                    authors.append(f"{c.get('lastName', '')}, {c.get('firstName', '')}")
        return "; ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")

    def search_library(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search Zotero library for items matching query.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching items
        """
        if not self.connected:
            return []

        try:
            results = self.zot.items(q=query, limit=limit)

            items = []
            for item in results:
                data = item.get("data", {})
                items.append({
                    "key": data.get("key", ""),
                    "title": data.get("title", "Untitled"),
                    "authors": self._format_authors(data.get("creators", [])),
                    "year": data.get("date", "")[:4] if data.get("date") else "",
                    "abstract": data.get("abstractNote", "")[:300] + "..." if len(data.get("abstractNote", "")) > 300 else data.get("abstractNote", ""),
                    "publication": data.get("publicationTitle", "")
                })

            return items

        except Exception as e:
            print(f"Search error: {e}")
            return []

    def get_relevant_papers(
        self,
        drafting_context: str,
        chapter_topic: str = "",
        top_n: int = 5
    ) -> list[dict]:
        """
        Get the most relevant papers for the current drafting context.

        Uses Claude to analyze relevance between the drafting context
        and papers in the Zotero library.

        Args:
            drafting_context: Current text being drafted
            chapter_topic: Optional chapter/section topic for context
            top_n: Number of papers to return

        Returns:
            List of relevant papers with relevance scores
        """
        # Ensure we have cached items
        if not self.items_cache:
            self.fetch_all_items()

        if not self.items_cache:
            return []

        # If no Claude, fall back to keyword search
        if not self.claude_client:
            # Simple keyword extraction and search
            keywords = drafting_context.split()[:5]
            return self.search_library(" ".join(keywords), limit=top_n)

        # Prepare papers summary for Claude
        papers_summary = "\n".join([
            f"[{i}] {p['title']} ({p['year']}) - {p['authors']}\n    Abstract: {p['abstract'][:200]}..."
            for i, p in enumerate(self.items_cache[:50])  # Limit to avoid token overflow
        ])

        prompt = f"""Analyze the following DRAFTING CONTEXT from a PhD thesis and identify the most relevant papers from the LIBRARY.

DRAFTING CONTEXT:
{drafting_context}

{f"CHAPTER/SECTION: {chapter_topic}" if chapter_topic else ""}

LIBRARY (first 50 papers):
{papers_summary}

Return a JSON array of the {top_n} most relevant papers, ranked by relevance. Each entry should have:
- "index": The paper index number from the list
- "relevance_score": 0.0 to 1.0
- "reason": Brief explanation of why this paper is relevant

Respond with ONLY valid JSON."""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            result = json.loads(response.content[0].text)

            # Map back to actual papers
            relevant_papers = []
            for r in result[:top_n]:
                idx = r.get("index", 0)
                if 0 <= idx < len(self.items_cache):
                    paper = self.items_cache[idx].copy()
                    paper["relevance_score"] = r.get("relevance_score", 0)
                    paper["relevance_reason"] = r.get("reason", "")
                    relevant_papers.append(paper)

            return relevant_papers

        except Exception as e:
            print(f"Relevance analysis error: {e}")
            # Fall back to simple search
            return self.search_library(drafting_context[:100], limit=top_n)

    def format_citation(self, item: dict, style: str = "APA") -> str:
        """
        Format a citation in the specified style.

        Args:
            item: Paper dictionary
            style: Citation style (APA, Harvard, Chicago, etc.)

        Returns:
            Formatted citation string
        """
        authors = item.get("authors", "Unknown")
        year = item.get("year", "n.d.")
        title = item.get("title", "Untitled")
        publication = item.get("publication", "")

        if style.upper() == "APA":
            return f"{authors} ({year}). {title}. {publication}."
        elif style.upper() == "HARVARD":
            return f"{authors} ({year}) '{title}', {publication}."
        else:
            return f"{authors} ({year}). {title}. {publication}."

    def get_library_stats(self) -> dict:
        """Get statistics about the Zotero library."""
        if not self.connected:
            return {"error": "Not connected"}

        try:
            return {
                "total_items": self.zot.num_items(),
                "cached_items": len(self.items_cache),
                "library_id": self.library_id
            }
        except Exception as e:
            return {"error": str(e)}


# Streamlit widget for sidebar integration
def render_sentinel_widget(sentinel: ZoteroSentinel, drafting_context: str, chapter: str = ""):
    """
    Render the Zotero Sentinel widget for Streamlit sidebar.

    This function is called from the dashboard to display relevant papers.
    """
    import streamlit as st

    st.markdown("### 📚 Citation Sentinel")

    status = sentinel.get_connection_status()

    if not status["connected"]:
        st.warning("Zotero not connected")
        st.markdown("Add to `.env`:")
        st.code("ZOTERO_LIBRARY_ID=your_id\nZOTERO_API_KEY=your_key")
        return

    st.markdown(f"**Library:** {status['library_id']}")

    if drafting_context and len(drafting_context) > 50:
        with st.spinner("Finding relevant papers..."):
            papers = sentinel.get_relevant_papers(drafting_context, chapter, top_n=5)

        if papers:
            st.markdown("**Top Relevant Papers:**")
            for i, paper in enumerate(papers, 1):
                with st.expander(f"{i}. {paper['title'][:50]}..."):
                    st.markdown(f"**{paper['title']}**")
                    st.markdown(f"*{paper['authors']}* ({paper['year']})")
                    if paper.get("relevance_reason"):
                        st.markdown(f"📎 {paper['relevance_reason']}")
                    st.markdown(f"`{sentinel.format_citation(paper)}`")
        else:
            st.info("No relevant papers found")
    else:
        st.info("Start writing to see relevant papers")


def main():
    """CLI for Zotero Sentinel."""
    print("=" * 60)
    print("PHDx Zotero Sentinel - Citation Intelligence")
    print("=" * 60)

    sentinel = ZoteroSentinel()

    status = sentinel.get_connection_status()
    print(f"\nConnection status: {'✓ Connected' if status['connected'] else '✗ Not connected'}")

    if status['connected']:
        stats = sentinel.get_library_stats()
        print(f"Library items: {stats.get('total_items', 'unknown')}")

        print("\nFetching library items...")
        items = sentinel.fetch_all_items()
        print(f"Cached {len(items)} items")

        if items:
            print("\nSample papers:")
            for item in items[:3]:
                print(f"  - {item['title'][:60]}... ({item['year']})")
    else:
        print("\nTo connect, set environment variables:")
        print("  ZOTERO_LIBRARY_ID=your_library_id")
        print("  ZOTERO_API_KEY=your_api_key")


if __name__ == "__main__":
    main()
