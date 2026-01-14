"""
Citations Manager - Zotero Sentinel for PHDx

Connects to Zotero library and provides intelligent paper recommendations
based on the current drafting context. Formats citations in Oxford Brookes
'Cite Them Right' Harvard style.

Reference: Pears, R. and Shields, G. (2022) Cite them right: the essential
referencing guide. 12th edn. London: Bloomsbury Academic.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

# Attempt to import pyzotero (may fail due to legacy dependency issues)
try:
    from pyzotero import zotero
    PYZOTERO_AVAILABLE = True
except ImportError:
    PYZOTERO_AVAILABLE = False
    zotero = None

# Direct API fallback using requests
import requests
ZOTERO_API_BASE = "https://api.zotero.org"

# Import ethics utilities for AI usage logging
try:
    from core.ethics_utils import log_ai_usage
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from core.ethics_utils import log_ai_usage
    except ImportError:
        def log_ai_usage(*args, **kwargs):
            pass

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "local_cache"
CITATIONS_CACHE = DATA_DIR / "zotero_cache.json"


class ZoteroSentinel:
    """
    Intelligent citation assistant that monitors drafting context
    and suggests relevant papers from Zotero library.

    Features:
    - Connects to user's Zotero library via API
    - Searches library based on draft content
    - Recommends top 5 relevant papers
    - Formats citations in Oxford Brookes Harvard style
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        library_type: str = "user",
        api_key: Optional[str] = None
    ):
        """
        Initialize Zotero connection.

        Args:
            user_id: Zotero user ID (from .env ZOTERO_USER_ID)
            library_type: "user" or "group"
            api_key: Zotero API key (from .env ZOTERO_API_KEY)
        """
        self.user_id = user_id or os.getenv("ZOTERO_USER_ID")
        self.api_key = api_key or os.getenv("ZOTERO_API_KEY")
        self.library_type = library_type

        self.zot = None
        self.connected = False
        self.items_cache = []
        self.last_fetch = None

        # Initialize Anthropic for relevance analysis
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None

        # Load cached items
        self._load_cache()

        # Attempt connection if credentials available
        if self.user_id and self.api_key:
            self._connect()

    def _connect(self) -> bool:
        """Establish connection to Zotero (pyzotero or direct API)."""
        # Try pyzotero first if available
        if PYZOTERO_AVAILABLE:
            try:
                self.zot = zotero.Zotero(
                    self.user_id,
                    self.library_type,
                    self.api_key
                )
                self.zot.num_items()
                self.connected = True
                self._use_direct_api = False
                return True
            except Exception as e:
                print(f"pyzotero connection failed: {e}")

        # Fall back to direct API
        try:
            headers = {"Zotero-API-Key": self.api_key}
            url = f"{ZOTERO_API_BASE}/users/{self.user_id}/items/top?limit=1"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                self.connected = True
                self._use_direct_api = True
                return True
            else:
                print(f"Zotero API error: {response.status_code}")
                self.connected = False
                return False
        except Exception as e:
            print(f"Zotero direct API connection failed: {e}")
            self.connected = False
            return False

    def _load_cache(self):
        """Load cached items from disk."""
        if CITATIONS_CACHE.exists():
            try:
                with open(CITATIONS_CACHE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.items_cache = cache_data.get("items", [])
                    self.last_fetch = cache_data.get("last_fetch")
            except (json.JSONDecodeError, IOError):
                self.items_cache = []

    def _save_cache(self):
        """Save items to cache file."""
        CITATIONS_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(CITATIONS_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "items": self.items_cache,
                "last_fetch": datetime.now().isoformat(),
                "user_id": self.user_id
            }, f, indent=2)

    def get_connection_status(self) -> dict:
        """Get current connection status."""
        return {
            "connected": self.connected,
            "user_id": self.user_id,
            "library_type": self.library_type,
            "has_api_key": bool(self.api_key),
            "pyzotero_available": PYZOTERO_AVAILABLE,
            "using_direct_api": getattr(self, '_use_direct_api', False),
            "cached_items": len(self.items_cache),
            "last_fetch": self.last_fetch
        }

    def _parse_creators(self, creators: list) -> dict:
        """
        Parse creator list into structured author data.

        Returns:
            dict with 'authors' list and 'formatted' string
        """
        authors = []
        for c in creators:
            if c.get("creatorType") in ["author", "editor"]:
                author = {
                    "firstName": c.get("firstName", ""),
                    "lastName": c.get("lastName", ""),
                    "name": c.get("name", ""),
                    "type": c.get("creatorType", "author")
                }
                if author["name"]:
                    # Single name field (organization)
                    author["display"] = author["name"]
                else:
                    author["display"] = f"{author['lastName']}, {author['firstName'][0]}." if author['firstName'] else author['lastName']
                authors.append(author)

        return {
            "list": authors,
            "count": len(authors),
            "formatted": self._format_authors_harvard(authors)
        }

    def _format_authors_harvard(self, authors: list) -> str:
        """
        Format authors list according to Oxford Brookes Harvard style.

        Rules (Cite Them Right):
        - 1 author: Surname, Initial.
        - 2 authors: Surname, I. and Surname, I.
        - 3 authors: Surname, I., Surname, I. and Surname, I.
        - 4+ authors: Surname, I. et al.
        """
        if not authors:
            return "Unknown"

        if len(authors) == 1:
            return authors[0]["display"]
        elif len(authors) == 2:
            return f"{authors[0]['display']} and {authors[1]['display']}"
        elif len(authors) == 3:
            return f"{authors[0]['display']}, {authors[1]['display']} and {authors[2]['display']}"
        else:
            return f"{authors[0]['display']} et al."

    def _fetch_via_direct_api(self, limit: int = 100) -> list[dict]:
        """Fetch items using direct Zotero API calls."""
        items = []
        headers = {"Zotero-API-Key": self.api_key}
        start = 0

        while True:
            url = f"{ZOTERO_API_BASE}/users/{self.user_id}/items?start={start}&limit={limit}"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                break

            batch = response.json()
            if not batch:
                break

            items.extend(batch)
            start += limit

            # Check if we got all items
            total = int(response.headers.get('Total-Results', 0))
            if start >= total:
                break

        return items

    def fetch_all_items(self, force_refresh: bool = False) -> list[dict]:
        """
        Fetch all items from Zotero library.

        Args:
            force_refresh: Force refresh from API even if cache exists

        Returns:
            List of simplified item dictionaries
        """
        # Use cache if available and not forcing refresh
        if not force_refresh and self.items_cache:
            return self.items_cache

        if not self.connected:
            return self.items_cache  # Return cached items if any

        try:
            # Fetch items via pyzotero or direct API
            if getattr(self, '_use_direct_api', False) or not PYZOTERO_AVAILABLE:
                raw_items = self._fetch_via_direct_api()
            else:
                raw_items = self.zot.everything(self.zot.items())

            items = []
            for item in raw_items:
                data = item.get("data", {})
                item_type = data.get("itemType", "")

                # Skip attachments and notes
                if item_type in ["attachment", "note"]:
                    continue

                creators = self._parse_creators(data.get("creators", []))

                # Extract year from date
                date_str = data.get("date", "")
                year = ""
                if date_str:
                    # Try to extract year from various date formats
                    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
                    if year_match:
                        year = year_match.group()

                items.append({
                    "key": data.get("key", ""),
                    "title": data.get("title", "Untitled"),
                    "creators": creators,
                    "authors": creators["formatted"],
                    "authors_list": creators["list"],
                    "year": year,
                    "date": date_str,
                    "abstract": data.get("abstractNote", ""),
                    "publication": data.get("publicationTitle", data.get("bookTitle", "")),
                    "publisher": data.get("publisher", ""),
                    "place": data.get("place", ""),
                    "volume": data.get("volume", ""),
                    "issue": data.get("issue", ""),
                    "pages": data.get("pages", ""),
                    "doi": data.get("DOI", ""),
                    "url": data.get("url", ""),
                    "isbn": data.get("ISBN", ""),
                    "edition": data.get("edition", ""),
                    "tags": [t.get("tag", "") for t in data.get("tags", [])],
                    "item_type": item_type,
                    "accessed": data.get("accessDate", "")
                })

            self.items_cache = items
            self._save_cache()
            return items

        except Exception as e:
            print(f"Error fetching items: {e}")
            return self.items_cache  # Return cached items on error

    def search_library(self, query: str, limit: int = 5) -> list[dict]:
        """
        Search Zotero library for top relevant papers based on a query.

        This searches both the Zotero API and locally cached items
        to find the most relevant matches.

        Args:
            query: Search query (e.g., a draft paragraph)
            limit: Maximum results to return (default: 5)

        Returns:
            List of top matching items with relevance info
        """
        if not query or len(query.strip()) < 10:
            return []

        results = []

        # Strategy 1: API search if connected
        if self.connected:
            try:
                search_terms = self._extract_key_terms(query)

                # Use direct API or pyzotero based on connection type
                if getattr(self, '_use_direct_api', False) or not PYZOTERO_AVAILABLE:
                    # Direct API search
                    headers = {"Zotero-API-Key": self.api_key}
                    url = f"{ZOTERO_API_BASE}/users/{self.user_id}/items?q={search_terms}&limit={limit * 2}"
                    response = requests.get(url, headers=headers, timeout=30)
                    if response.status_code == 200:
                        api_results = response.json()
                    else:
                        api_results = []
                else:
                    # pyzotero search
                    api_results = self.zot.items(q=search_terms, limit=limit * 2)

                for item in api_results:
                    data = item.get("data", {})
                    if data.get("itemType") in ["attachment", "note"]:
                        continue

                    creators = self._parse_creators(data.get("creators", []))
                    year_match = re.search(r'\b(19|20)\d{2}\b', data.get("date", ""))

                    results.append({
                        "key": data.get("key", ""),
                        "title": data.get("title", "Untitled"),
                        "authors": creators["formatted"],
                        "authors_list": creators["list"],
                        "year": year_match.group() if year_match else "",
                        "abstract": data.get("abstractNote", ""),
                        "publication": data.get("publicationTitle", ""),
                        "item_type": data.get("itemType", ""),
                        "relevance_source": "api_search"
                    })
            except Exception as e:
                print(f"API search error: {e}")

        # Strategy 2: Local cache search with keyword matching
        if self.items_cache:
            query_lower = query.lower()
            keywords = set(re.findall(r'\b\w{4,}\b', query_lower))

            for item in self.items_cache:
                # Skip if already in results
                if any(r["key"] == item["key"] for r in results):
                    continue

                # Calculate relevance score based on keyword matches
                item_text = f"{item['title']} {item['abstract']} {' '.join(item.get('tags', []))}".lower()
                matches = sum(1 for kw in keywords if kw in item_text)

                if matches > 0:
                    item_copy = item.copy()
                    item_copy["relevance_score"] = matches / len(keywords) if keywords else 0
                    item_copy["relevance_source"] = "cache_search"
                    results.append(item_copy)

        # Sort by relevance and return top results
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        return results[:limit]

    def _extract_key_terms(self, text: str) -> str:
        """Extract key search terms from text."""
        # Remove common words and keep significant terms
        stopwords = {
            'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were',
            'been', 'being', 'have', 'has', 'had', 'does', 'did', 'will',
            'would', 'could', 'should', 'from', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
            'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'only', 'own', 'same', 'than', 'too', 'very', 'can', 'just', 'also'
        }

        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        key_terms = [w for w in words if w not in stopwords]

        # Return top 5 unique terms
        seen = set()
        unique_terms = []
        for term in key_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
                if len(unique_terms) >= 5:
                    break

        return " ".join(unique_terms)

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
            List of relevant papers with relevance scores and reasons
        """
        # Ensure we have items to search
        if not self.items_cache:
            self.fetch_all_items()

        if not self.items_cache:
            return []

        # If no Claude, fall back to keyword search
        if not self.claude_client:
            return self.search_library(drafting_context, limit=top_n)

        # Prepare papers summary for Claude (limit to prevent token overflow)
        papers_for_analysis = self.items_cache[:50]
        papers_summary = "\n".join([
            f"[{i}] {p['title']} ({p['year']}) by {p['authors']}\n    Abstract: {p['abstract'][:150]}..."
            for i, p in enumerate(papers_for_analysis)
            if p.get('title')
        ])

        prompt = f"""You are a PhD research assistant. Analyze the DRAFTING CONTEXT and identify the most relevant papers from the LIBRARY for citation.

DRAFTING CONTEXT:
{drafting_context[:1000]}

{f"CHAPTER/SECTION: {chapter_topic}" if chapter_topic else ""}

LIBRARY ({len(papers_for_analysis)} papers):
{papers_summary}

Return a JSON array of the {top_n} most relevant papers for citing in this context.
Each entry must have:
- "index": The paper index number [0-{len(papers_for_analysis)-1}]
- "relevance_score": 0.0 to 1.0 (1.0 = highly relevant)
- "reason": Brief explanation (1 sentence) of why this paper supports the argument

Consider:
- Theoretical frameworks mentioned
- Methodology relevance
- Conceptual alignment
- Direct citations that would strengthen the argument

Respond with ONLY valid JSON array, no markdown."""

        # Log AI usage
        log_ai_usage(
            action_type="citation_relevance",
            data_source="zotero_library",
            prompt=f"Finding relevant papers for: {drafting_context[:100]}...",
            was_scrubbed=False,
            redactions_count=0
        )

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Clean markdown if present
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            result = json.loads(response_text)

            # Map back to actual papers
            relevant_papers = []
            for r in result[:top_n]:
                idx = r.get("index", 0)
                if 0 <= idx < len(papers_for_analysis):
                    paper = papers_for_analysis[idx].copy()
                    paper["relevance_score"] = r.get("relevance_score", 0)
                    paper["relevance_reason"] = r.get("reason", "")
                    relevant_papers.append(paper)

            return relevant_papers

        except Exception as e:
            print(f"Relevance analysis error: {e}")
            # Fall back to simple search
            return self.search_library(drafting_context, limit=top_n)

    def format_as_brookes_harvard(self, item: dict) -> str:
        """
        Format a citation in Oxford Brookes 'Cite Them Right' Harvard style.

        Reference: Pears, R. and Shields, G. (2022) Cite them right. 12th edn.

        Formats supported:
        - Journal articles: Author(s) (Year) 'Title', Journal, Volume(Issue), pp. X-Y.
        - Books: Author(s) (Year) Title. Edition. Place: Publisher.
        - Book chapters: Author(s) (Year) 'Chapter title', in Editor (ed.) Book title. Place: Publisher, pp. X-Y.
        - Websites: Author/Org (Year) Title. Available at: URL (Accessed: Date).

        Args:
            item: Paper dictionary from Zotero

        Returns:
            Formatted citation string
        """
        item_type = item.get("item_type", "journalArticle")
        authors = item.get("authors", "Unknown")
        year = item.get("year", "n.d.")
        title = item.get("title", "Untitled")

        if item_type == "journalArticle":
            # Journal article format
            publication = item.get("publication", "")
            volume = item.get("volume", "")
            issue = item.get("issue", "")
            pages = item.get("pages", "")
            doi = item.get("doi", "")

            citation = f"{authors} ({year}) '{title}'"

            if publication:
                citation += f", {publication}"

            if volume:
                citation += f", {volume}"
                if issue:
                    citation += f"({issue})"

            if pages:
                citation += f", pp. {pages}"

            citation += "."

            if doi:
                citation += f" doi: {doi}."

            return citation

        elif item_type == "book":
            # Book format
            publisher = item.get("publisher", "")
            place = item.get("place", "")
            edition = item.get("edition", "")

            citation = f"{authors} ({year}) {title}"

            if edition:
                citation += f". {edition} edn"

            citation += "."

            if place and publisher:
                citation += f" {place}: {publisher}."
            elif publisher:
                citation += f" {publisher}."

            return citation

        elif item_type == "bookSection":
            # Book chapter format
            book_title = item.get("publication", "")
            publisher = item.get("publisher", "")
            place = item.get("place", "")
            pages = item.get("pages", "")

            citation = f"{authors} ({year}) '{title}'"

            if book_title:
                citation += f", in {book_title}"

            citation += "."

            if place and publisher:
                citation += f" {place}: {publisher}"

            if pages:
                citation += f", pp. {pages}"

            citation += "."
            return citation

        elif item_type in ["webpage", "website", "blogPost"]:
            # Website format
            url = item.get("url", "")
            accessed = item.get("accessed", "")

            citation = f"{authors} ({year}) {title}."

            if url:
                citation += f" Available at: {url}"

            if accessed:
                # Format access date
                try:
                    acc_date = datetime.fromisoformat(accessed.replace('Z', '+00:00'))
                    citation += f" (Accessed: {acc_date.strftime('%d %B %Y')})"
                except (ValueError, AttributeError):
                    citation += f" (Accessed: {accessed})"

            citation += "."
            return citation

        else:
            # Default format
            publication = item.get("publication", "")
            citation = f"{authors} ({year}) '{title}'"
            if publication:
                citation += f", {publication}"
            citation += "."
            return citation

    def format_inline_citation(self, item: dict) -> str:
        """
        Format an inline citation for insertion into text.

        Oxford Brookes Harvard style: (Author, Year) or (Author and Author, Year)

        Args:
            item: Paper dictionary

        Returns:
            Inline citation string, e.g., "(Bourdieu, 1984)"
        """
        authors_list = item.get("authors_list", [])
        year = item.get("year", "n.d.")

        if not authors_list:
            authors_display = item.get("authors", "Unknown")
            # Extract first surname
            if "," in authors_display:
                authors_display = authors_display.split(",")[0]
            elif " " in authors_display:
                authors_display = authors_display.split()[-1]
        elif len(authors_list) == 1:
            authors_display = authors_list[0].get("lastName", authors_list[0].get("display", "Unknown"))
        elif len(authors_list) == 2:
            authors_display = f"{authors_list[0].get('lastName', '')} and {authors_list[1].get('lastName', '')}"
        else:
            authors_display = f"{authors_list[0].get('lastName', '')} et al."

        return f"({authors_display}, {year})"

    def get_library_stats(self) -> dict:
        """Get statistics about the Zotero library."""
        stats = {
            "connected": self.connected,
            "cached_items": len(self.items_cache),
            "last_fetch": self.last_fetch
        }

        if self.connected:
            try:
                stats["total_items"] = self.zot.num_items()
            except Exception as e:
                stats["error"] = str(e)

        # Count by type
        type_counts = {}
        for item in self.items_cache:
            itype = item.get("item_type", "unknown")
            type_counts[itype] = type_counts.get(itype, 0) + 1
        stats["by_type"] = type_counts

        return stats


# =============================================================================
# STREAMLIT WIDGET FOR SIDEBAR
# =============================================================================

def render_sentinel_widget(
    sentinel: ZoteroSentinel,
    drafting_context: str,
    chapter: str = ""
):
    """
    Render the Zotero Sentinel widget for Streamlit sidebar.

    Features:
    - Connection status display
    - Relevant paper recommendations
    - Insert Citation button
    - Full reference display

    Args:
        sentinel: ZoteroSentinel instance
        drafting_context: Current text in drafting pane
        chapter: Current chapter being worked on
    """
    import streamlit as st

    st.markdown("### 📚 Zotero Sentinel")

    status = sentinel.get_connection_status()

    # Connection status - check both pyzotero and direct API
    if not status["connected"]:
        if not status["user_id"] or not status["has_api_key"]:
            st.warning("Zotero credentials not configured")
            st.markdown("Add to `.env`:")
            st.code("ZOTERO_USER_ID=your_user_id\nZOTERO_API_KEY=your_api_key", language="bash")
            st.markdown("[Get your API key](https://www.zotero.org/settings/keys)")
        else:
            st.error("Connection failed")

        # Show cached items if available
        if status["cached_items"] > 0:
            st.info(f"Using {status['cached_items']} cached items")
        return

    # Connected - show stats
    api_mode = "Direct API" if status.get("using_direct_api") else "pyzotero"
    st.success(f"✓ Connected via {api_mode}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Library Items", status.get("cached_items", 0))
    with col2:
        if st.button("🔄 Refresh", key="zotero_refresh"):
            with st.spinner("Fetching library..."):
                sentinel.fetch_all_items(force_refresh=True)
                st.rerun()

    st.markdown("---")

    # Initialize session state for citations
    if "pending_citation" not in st.session_state:
        st.session_state.pending_citation = None
    if "citation_history" not in st.session_state:
        st.session_state.citation_history = []

    # Show pending citation for insertion
    if st.session_state.pending_citation:
        st.success("**Citation ready to insert:**")
        st.code(st.session_state.pending_citation["inline"], language=None)
        st.caption(st.session_state.pending_citation["full"])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy", key="copy_citation", use_container_width=True):
                # Note: Streamlit doesn't have native clipboard, user copies from code block
                st.info("Copy from box above")
        with col2:
            if st.button("✓ Done", key="clear_citation", use_container_width=True):
                st.session_state.pending_citation = None
                st.rerun()

        st.markdown("---")

    # Relevant papers based on drafting context
    if drafting_context and len(drafting_context) > 50:
        st.markdown("**Relevant Papers:**")

        # Check if we need to refresh recommendations
        context_key = f"sentinel_context_{hash(drafting_context[:200])}"
        if context_key not in st.session_state:
            with st.spinner("Finding relevant papers..."):
                papers = sentinel.get_relevant_papers(
                    drafting_context,
                    chapter,
                    top_n=5
                )
                st.session_state[context_key] = papers
        else:
            papers = st.session_state[context_key]

        if papers:
            for i, paper in enumerate(papers):
                with st.expander(
                    f"📄 {paper['title'][:45]}..." if len(paper['title']) > 45 else f"📄 {paper['title']}"
                ):
                    st.markdown(f"**{paper['title']}**")
                    st.markdown(f"*{paper['authors']}* ({paper['year']})")

                    if paper.get("relevance_reason"):
                        st.info(f"💡 {paper['relevance_reason']}")

                    # Show inline citation
                    inline = sentinel.format_inline_citation(paper)
                    st.markdown(f"**Cite as:** `{inline}`")

                    # Full reference
                    full_ref = sentinel.format_as_brookes_harvard(paper)
                    st.caption(f"**Full reference:** {full_ref}")

                    # Insert Citation button
                    if st.button(
                        f"📎 Insert Citation",
                        key=f"insert_cite_{i}_{paper['key']}",
                        use_container_width=True
                    ):
                        st.session_state.pending_citation = {
                            "inline": inline,
                            "full": full_ref,
                            "paper": paper
                        }
                        # Add to history
                        if inline not in [h["inline"] for h in st.session_state.citation_history]:
                            st.session_state.citation_history.append({
                                "inline": inline,
                                "full": full_ref,
                                "title": paper["title"]
                            })
                        st.rerun()
        else:
            st.info("No matching papers found")

        # Manual search
        st.markdown("---")
        search_query = st.text_input(
            "Search library",
            placeholder="e.g., Bourdieu cultural capital",
            key="zotero_search"
        )

        if search_query:
            search_results = sentinel.search_library(search_query, limit=5)
            if search_results:
                st.markdown(f"**Results for '{search_query}':**")
                for j, result in enumerate(search_results):
                    inline = sentinel.format_inline_citation(result)
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"• {result['title'][:40]}... ({result['year']})")
                    with col2:
                        if st.button("📎", key=f"search_cite_{j}"):
                            st.session_state.pending_citation = {
                                "inline": inline,
                                "full": sentinel.format_as_brookes_harvard(result),
                                "paper": result
                            }
                            st.rerun()
            else:
                st.info("No results found")
    else:
        st.info("Start writing to see relevant papers")

    # Citation history
    if st.session_state.citation_history:
        st.markdown("---")
        st.markdown("**Recent Citations:**")
        for hist in st.session_state.citation_history[-3:]:
            st.caption(f"`{hist['inline']}` - {hist['title'][:30]}...")


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================

def search_library(query: str, limit: int = 5) -> list[dict]:
    """
    Standalone function to search Zotero library.

    Usage:
        from core.citations import search_library
        results = search_library("Bourdieu cultural capital")
    """
    sentinel = ZoteroSentinel()
    return sentinel.search_library(query, limit)


def format_as_brookes_harvard(item: dict) -> str:
    """
    Standalone function to format a citation in Oxford Brookes Harvard style.

    Usage:
        from core.citations import format_as_brookes_harvard
        citation = format_as_brookes_harvard(paper_dict)
    """
    sentinel = ZoteroSentinel()
    return sentinel.format_as_brookes_harvard(item)


def get_inline_citation(item: dict) -> str:
    """
    Standalone function to get inline citation.

    Usage:
        from core.citations import get_inline_citation
        cite = get_inline_citation(paper_dict)  # Returns "(Author, Year)"
    """
    sentinel = ZoteroSentinel()
    return sentinel.format_inline_citation(item)


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for Zotero Sentinel."""
    print("=" * 60)
    print("PHDx Zotero Sentinel - Citation Intelligence")
    print("=" * 60)

    sentinel = ZoteroSentinel()

    status = sentinel.get_connection_status()
    print(f"\nConnection: {'Connected' if status['connected'] else 'Not connected'}")
    print(f"User ID: {status['user_id'] or 'Not set'}")
    print(f"API Key: {'Configured' if status['has_api_key'] else 'Not set'}")
    print(f"Cached items: {status['cached_items']}")

    if status['connected']:
        stats = sentinel.get_library_stats()
        print(f"\nLibrary items: {stats.get('total_items', 'unknown')}")

        print("\nFetching library items...")
        items = sentinel.fetch_all_items(force_refresh=True)
        print(f"Fetched {len(items)} items")

        if items:
            print("\nSample papers (Harvard format):")
            for item in items[:3]:
                print(f"\n  {sentinel.format_as_brookes_harvard(item)}")
                print(f"  Cite as: {sentinel.format_inline_citation(item)}")

            # Test search
            print("\n" + "-" * 40)
            print("Testing search_library('theory')...")
            results = sentinel.search_library("theory", limit=3)
            for r in results:
                print(f"  - {r['title'][:50]}...")
    else:
        print("\nTo connect, set in .env:")
        print("  ZOTERO_USER_ID=your_user_id")
        print("  ZOTERO_API_KEY=your_api_key")
        print("\nGet your API key at: https://www.zotero.org/settings/keys")


if __name__ == "__main__":
    main()
