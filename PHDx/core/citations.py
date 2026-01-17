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


def get_secret(key: str, default: str = None) -> str:
    """
    Get a secret from Streamlit secrets (cloud) or environment variables (local).
    """
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
CACHE_DIR = DATA_DIR / "local_cache"
CITATIONS_CACHE = DATA_DIR / "zotero_cache.json"


# =============================================================================
# MOCK ZOTERO - Synthetic Citation Library
# =============================================================================

class MockZoteroSource:
    """A mock Zotero item with .key attribute for compatibility."""

    def __init__(self, data: dict):
        self.key = data.get("key", "")
        self._data = data

    def __getitem__(self, key):
        return self._data.get(key)

    def get(self, key, default=None):
        return self._data.get(key, default)


class MockZotero:
    """
    Mock Zotero library for when ZOTERO_API_KEY is not available.

    Provides 5 high-quality synthetic academic sources related to
    Digital Sovereignty and Urban Governance for testing purposes.
    """

    # Synthetic academic sources - high-quality references
    MOCK_SOURCES = [
        {
            "key": "ZUBOFF2019",
            "title": "The Age of Surveillance Capitalism: The Fight for a Human Future at the New Frontier of Power",
            "creators": [
                {"creatorType": "author", "firstName": "Shoshana", "lastName": "Zuboff"}
            ],
            "year": "2019",
            "date": "2019",
            "itemType": "book",
            "publisher": "PublicAffairs",
            "place": "New York",
            "abstractNote": "A comprehensive analysis of surveillance capitalism as a new economic order that claims human experience as free raw material for hidden commercial practices of extraction, prediction, and sales. Zuboff argues this represents an unprecedented form of power that threatens democratic norms and individual autonomy.",
            "ISBN": "978-1610395694",
            "tags": ["surveillance capitalism", "digital economy", "privacy", "power", "technology"]
        },
        {
            "key": "FOUCAULT1977",
            "title": "Discipline and Punish: The Birth of the Prison",
            "creators": [
                {"creatorType": "author", "firstName": "Michel", "lastName": "Foucault"}
            ],
            "year": "1977",
            "date": "1977",
            "itemType": "book",
            "publisher": "Penguin Books",
            "place": "London",
            "edition": "1st English",
            "abstractNote": "A foundational text examining the emergence of disciplinary society through the lens of penal institutions. Introduces the concept of the panopticon as a metaphor for modern surveillance and normalisation, arguing that power operates through visibility and the internalisation of disciplinary norms.",
            "ISBN": "978-0140137224",
            "tags": ["panopticon", "discipline", "power", "surveillance", "governance"]
        },
        {
            "key": "KITCHIN2014",
            "title": "The real-time city? Big data and smart urbanism",
            "creators": [
                {"creatorType": "author", "firstName": "Rob", "lastName": "Kitchin"}
            ],
            "year": "2014",
            "date": "2014",
            "itemType": "journalArticle",
            "publicationTitle": "GeoJournal",
            "volume": "79",
            "issue": "1",
            "pages": "1-14",
            "DOI": "10.1007/s10708-013-9516-8",
            "abstractNote": "Critically examines the emergence of smart city initiatives and their reliance on big data analytics for urban governance. Argues that while real-time data offers new possibilities for urban management, it raises significant concerns regarding privacy, surveillance, and technocratic governance models.",
            "tags": ["smart cities", "big data", "urban governance", "surveillance", "real-time analytics"]
        },
        {
            "key": "LYON2007",
            "title": "Surveillance Studies: An Overview",
            "creators": [
                {"creatorType": "author", "firstName": "David", "lastName": "Lyon"}
            ],
            "year": "2007",
            "date": "2007",
            "itemType": "book",
            "publisher": "Polity Press",
            "place": "Cambridge",
            "abstractNote": "A comprehensive introduction to the field of surveillance studies, examining how contemporary societies have become increasingly monitored through technological systems. Lyon explores the social, political, and ethical implications of surveillance across domains including security, consumption, and digital communications.",
            "ISBN": "978-0745635927",
            "tags": ["surveillance studies", "monitoring", "privacy", "security", "society"]
        },
        {
            "key": "COULDRY2019",
            "title": "The Costs of Connection: How Data Is Colonizing Human Life and Appropriating It for Capitalism",
            "creators": [
                {"creatorType": "author", "firstName": "Nick", "lastName": "Couldry"},
                {"creatorType": "author", "firstName": "Ulises A.", "lastName": "Mejias"}
            ],
            "year": "2019",
            "date": "2019",
            "itemType": "book",
            "publisher": "Stanford University Press",
            "place": "Stanford, CA",
            "abstractNote": "Develops the concept of 'data colonialism' to describe how technology corporations extract value from human life through data relations. The authors argue that contemporary data practices represent a new phase of colonialism that naturalises the exploitation of human beings for profit.",
            "ISBN": "978-1503609754",
            "tags": ["data colonialism", "digital sovereignty", "exploitation", "capitalism", "technology"]
        }
    ]

    def __init__(self):
        """Initialize the mock Zotero library."""
        self._items = [MockZoteroSource(src) for src in self.MOCK_SOURCES]
        self._mock_mode_notified = False

    def search(self, query: str, limit: int = 5) -> list[MockZoteroSource]:
        """
        Search the mock library for relevant sources.

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of MockZoteroSource objects with .key attribute
        """
        if not query:
            return self._items[:limit]

        query_lower = query.lower()
        keywords = set(query_lower.split())

        # Score each source by keyword matches
        scored = []
        for item in self._items:
            item_text = f"{item['title']} {item['abstractNote']} {' '.join(item.get('tags', []))}".lower()
            score = sum(1 for kw in keywords if kw in item_text)
            if score > 0 or not query.strip():
                scored.append((score, item))

        # Sort by score and return top results
        scored.sort(key=lambda x: x[0], reverse=True)

        # If no matches, return all sources (they're all relevant to the thesis topic)
        if not scored:
            return self._items[:limit]

        return [item for _, item in scored[:limit]]

    def get_all_items(self) -> list[MockZoteroSource]:
        """Return all mock sources."""
        return self._items

    def num_items(self) -> int:
        """Return number of items in mock library."""
        return len(self._items)


# Flag to track if mock mode toast has been shown this session
_MOCK_MODE_TOAST_SHOWN = False


def _show_mock_mode_toast():
    """Show Streamlit toast notification for Mock Mode (once per session)."""
    global _MOCK_MODE_TOAST_SHOWN
    if not _MOCK_MODE_TOAST_SHOWN:
        try:
            import streamlit as st
            if hasattr(st, 'toast'):
                st.toast("⚠️ Using Synthetic Citation Library", icon="📚")
            _MOCK_MODE_TOAST_SHOWN = True
        except Exception:
            pass  # Not in Streamlit context


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

        If ZOTERO_API_KEY is not available, automatically switches to Mock Mode
        with a synthetic citation library for testing.

        Args:
            user_id: Zotero user ID (from .env ZOTERO_USER_ID)
            library_type: "user" or "group"
            api_key: Zotero API key (from .env ZOTERO_API_KEY)
        """
        self.user_id = user_id or get_secret("ZOTERO_USER_ID")
        self.api_key = api_key or get_secret("ZOTERO_API_KEY")
        self.library_type = library_type

        self.zot = None
        self.connected = False
        self.items_cache = []
        self.last_fetch = None

        # Mock Mode - activated when no API key
        self.mock_mode = False
        self.mock_zotero = None

        # Initialize Anthropic for relevance analysis
        anthropic_key = get_secret("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None

        # Load cached items
        self._load_cache()

        # Check if we should use Mock Mode
        if not self.api_key:
            self._enable_mock_mode()
        elif self.user_id and self.api_key:
            # Attempt real connection
            self._connect()

    def _enable_mock_mode(self):
        """Enable Mock Mode with synthetic citation library."""
        self.mock_mode = True
        self.mock_zotero = MockZotero()
        self.connected = True  # Mark as "connected" for UI purposes

        # Populate cache with mock sources
        self.items_cache = self._convert_mock_to_cache()
        self.last_fetch = datetime.now().isoformat()

        # Show toast notification in Streamlit
        _show_mock_mode_toast()

    def _convert_mock_to_cache(self) -> list[dict]:
        """Convert MockZotero sources to cache format."""
        items = []
        for src in MockZotero.MOCK_SOURCES:
            creators = self._parse_creators(src.get("creators", []))
            items.append({
                "key": src.get("key", ""),
                "title": src.get("title", "Untitled"),
                "creators": creators,
                "authors": creators["formatted"],
                "authors_list": creators["list"],
                "year": src.get("year", ""),
                "date": src.get("date", ""),
                "abstract": src.get("abstractNote", ""),
                "publication": src.get("publicationTitle", ""),
                "publisher": src.get("publisher", ""),
                "place": src.get("place", ""),
                "volume": src.get("volume", ""),
                "issue": src.get("issue", ""),
                "pages": src.get("pages", ""),
                "doi": src.get("DOI", ""),
                "url": src.get("url", ""),
                "isbn": src.get("ISBN", ""),
                "edition": src.get("edition", ""),
                "tags": src.get("tags", []),
                "item_type": src.get("itemType", ""),
                "accessed": src.get("accessDate", "")
            })
        return items

    def _connect(self) -> bool:
        """
        Establish connection to Zotero (pyzotero or direct API).

        API Robustness: Handles 403 Forbidden errors with helpful message.
        """
        self.connection_error = None  # Reset error state

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
                error_str = str(e).lower()
                # Check for 403 Forbidden
                if "403" in error_str or "forbidden" in error_str:
                    self.connection_error = "forbidden"
                    print("=" * 60)
                    print("Invalid Zotero API Key. Please check your PHDx .env file.")
                    print("=" * 60)
                    print("\nTo fix this:")
                    print("  1. Go to https://www.zotero.org/settings/keys")
                    print("  2. Create a new API key with library read access")
                    print("  3. Update ZOTERO_API_KEY in your PHDx/.env file")
                    print("=" * 60)
                else:
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

            # API Robustness: Handle 403 Forbidden specifically
            elif response.status_code == 403:
                self.connection_error = "forbidden"
                self.connected = False
                print("\n" + "=" * 60)
                print("Invalid Zotero API Key. Please check your PHDx .env file.")
                print("=" * 60)
                print("\nTo fix this:")
                print("  1. Go to https://www.zotero.org/settings/keys")
                print("  2. Create a new API key with library read access")
                print("  3. Update ZOTERO_API_KEY in your PHDx/.env file")
                print("=" * 60 + "\n")
                return False

            elif response.status_code == 404:
                self.connection_error = "user_not_found"
                print(f"Zotero user ID not found: {self.user_id}")
                self.connected = False
                return False

            else:
                print(f"Zotero API error: {response.status_code}")
                self.connected = False
                return False

        except requests.exceptions.Timeout:
            self.connection_error = "timeout"
            print("Zotero API connection timed out. Check your internet connection.")
            self.connected = False
            return False

        except requests.exceptions.ConnectionError:
            self.connection_error = "network"
            print("Network error connecting to Zotero. Check your internet connection.")
            self.connected = False
            return False

        except Exception as e:
            self.connection_error = "unknown"
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
            "mock_mode": self.mock_mode,
            "user_id": self.user_id,
            "library_type": self.library_type,
            "has_api_key": bool(self.api_key),
            "pyzotero_available": PYZOTERO_AVAILABLE,
            "using_direct_api": getattr(self, '_use_direct_api', False),
            "cached_items": len(self.items_cache),
            "last_fetch": self.last_fetch,
            "connection_error": getattr(self, 'connection_error', None)
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

    # Check for Mock Mode first
    if status.get("mock_mode"):
        # Show Mock Mode indicator with toast
        st.warning("📚 **Mock Mode Active**")
        st.caption("Using Synthetic Citation Library")

        # Trigger toast notification
        if hasattr(st, 'toast'):
            # Use session state to only show once per session
            if "mock_mode_toast_shown" not in st.session_state:
                st.toast("⚠️ Using Synthetic Citation Library", icon="📚")
                st.session_state.mock_mode_toast_shown = True

    # Connection status - check both pyzotero and direct API
    elif not status["connected"]:
        # API Robustness: Handle 403 Forbidden error specifically
        if status.get("connection_error") == "forbidden":
            st.error("🔒 **Invalid Zotero API Key**")
            st.markdown("Please check your PHDx `.env` file.")
            st.markdown("**To fix this:**")
            st.markdown("1. Go to [Zotero API Keys](https://www.zotero.org/settings/keys)")
            st.markdown("2. Create a new key with library read access")
            st.markdown("3. Update `ZOTERO_API_KEY` in your `.env` file")

        elif not status["user_id"] or not status["has_api_key"]:
            st.warning("Zotero credentials not configured")
            st.markdown("Add to `.env`:")
            st.code("ZOTERO_USER_ID=your_user_id\nZOTERO_API_KEY=your_api_key", language="bash")
            st.markdown("[Get your API key](https://www.zotero.org/settings/keys)")

        elif status.get("connection_error") == "timeout":
            st.error("⏱️ Connection timed out")
            st.caption("Check your internet connection and try again.")

        elif status.get("connection_error") == "network":
            st.error("🌐 Network error")
            st.caption("Unable to reach Zotero servers.")

        else:
            st.error("Connection failed")

        # Show cached items if available
        if status["cached_items"] > 0:
            st.info(f"Using {status['cached_items']} cached items")
        return

    # Connected to real Zotero - show stats
    if not status.get("mock_mode"):
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
