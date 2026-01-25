"""
PHDx Services - Shared Service Locator

Singleton service locator providing unified access to shared components
across all PHDx modules. Lazy initialization ensures resources are only
created when needed.

Usage:
    from core.services import get_services

    services = get_services()
    result = services.llm.generate_content(prompt, task_type)
    scrubbed = services.scrubber.quick_scrub(text)
"""

import json
from pathlib import Path
from typing import Optional
from datetime import datetime


# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DNA_PROFILE_PATH = DATA_DIR / "author_dna.json"


class PHDxServices:
    """
    Singleton service locator for shared PHDx components.

    Provides lazy-loaded access to:
        - LLM Gateway (multi-model routing)
        - Vector Store (ChromaDB/Pinecone)
        - Ethics Scrubber (PII detection)
        - DNA Profile (author voice)
        - Zotero Sentinel (citations)
    """

    _instance: Optional["PHDxServices"] = None

    def __new__(cls) -> "PHDxServices":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Lazy-loaded service instances
        self._llm_gateway = None
        self._vector_store = None
        self._ethics_scrubber = None
        self._dna_profile = None
        self._zotero_sentinel = None
        self._auditor = None
        self._red_thread = None

        self._initialized = True

    # =========================================================================
    # LLM GATEWAY
    # =========================================================================

    @property
    def llm(self):
        """
        Get the LLM gateway for multi-model content generation.

        Returns:
            Module with generate_content(), get_opus_model(), etc.
        """
        if self._llm_gateway is None:
            from core import llm_gateway
            self._llm_gateway = llm_gateway
        return self._llm_gateway

    def generate_content(self, prompt: str, task_type: str, context: str = "", **kwargs) -> dict:
        """Convenience method for LLM content generation."""
        return self.llm.generate_content(prompt, task_type, context, **kwargs)

    # =========================================================================
    # VECTOR STORE
    # =========================================================================

    @property
    def vectors(self):
        """
        Get the vector store for similarity search.

        Returns:
            VectorStoreBase instance (ChromaDB or Pinecone)
        """
        if self._vector_store is None:
            from core.vector_store import get_vector_store
            self._vector_store = get_vector_store()
        return self._vector_store

    def query_similar(self, text: str, n_results: int = 5) -> dict:
        """Convenience method for vector similarity search."""
        return self.vectors.query(text, n_results)

    # =========================================================================
    # ETHICS SCRUBBER
    # =========================================================================

    @property
    def scrubber(self):
        """
        Get the ethics scrubber for PII detection and removal.

        Returns:
            EthicsScrubber instance
        """
        if self._ethics_scrubber is None:
            from core.ethics_utils import get_scrubber
            self._ethics_scrubber = get_scrubber()
        return self._ethics_scrubber

    def scrub_text(self, text: str, include_names: bool = True) -> dict:
        """Convenience method for full PII scrubbing."""
        return self.scrubber.scrub(text, include_names)

    def quick_scrub(self, text: str) -> str:
        """Convenience method for quick PII scrubbing (text only)."""
        return self.scrubber.quick_scrub(text)

    # =========================================================================
    # DNA PROFILE
    # =========================================================================

    @property
    def dna_profile(self) -> Optional[dict]:
        """
        Get the author's DNA profile for voice matching.

        Returns:
            DNA profile dict or None if not available
        """
        if self._dna_profile is None:
            self._dna_profile = self._load_dna_profile()
        return self._dna_profile

    def _load_dna_profile(self) -> Optional[dict]:
        """Load DNA profile from disk."""
        if DNA_PROFILE_PATH.exists():
            try:
                with open(DNA_PROFILE_PATH, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def reload_dna_profile(self) -> Optional[dict]:
        """Force reload of DNA profile from disk."""
        self._dna_profile = self._load_dna_profile()
        return self._dna_profile

    def has_dna_profile(self) -> bool:
        """Check if DNA profile is available."""
        return self.dna_profile is not None

    # =========================================================================
    # ZOTERO SENTINEL
    # =========================================================================

    @property
    def zotero(self):
        """
        Get the Zotero Sentinel for citation management.

        Returns:
            ZoteroSentinel instance
        """
        if self._zotero_sentinel is None:
            from core.citations import ZoteroSentinel
            from core.secrets_utils import get_secret

            user_id = get_secret("ZOTERO_USER_ID")
            api_key = get_secret("ZOTERO_API_KEY")

            self._zotero_sentinel = ZoteroSentinel(
                user_id=user_id,
                api_key=api_key
            )
        return self._zotero_sentinel

    def get_citations(self, context: str, top_n: int = 5) -> list:
        """Convenience method for getting relevant citations."""
        return self.zotero.get_relevant_papers(context, top_n)

    # =========================================================================
    # AUDITOR
    # =========================================================================

    @property
    def auditor(self):
        """
        Get the Brookes Auditor for thesis evaluation.

        Returns:
            BrookesAuditor instance
        """
        if self._auditor is None:
            from core.auditor import BrookesAuditor
            self._auditor = BrookesAuditor()
        return self._auditor

    def audit_draft(self, text: str, chapter_context: str = "") -> dict:
        """Convenience method for draft auditing."""
        return self.auditor.audit_draft(text, chapter_context)

    # =========================================================================
    # RED THREAD ENGINE
    # =========================================================================

    @property
    def red_thread(self):
        """
        Get the Red Thread Engine for consistency checking.

        Returns:
            RedThreadEngine instance
        """
        if self._red_thread is None:
            from core.red_thread import RedThreadEngine
            self._red_thread = RedThreadEngine()
        return self._red_thread

    def check_consistency(self, text: str) -> dict:
        """Convenience method for consistency checking."""
        return self.red_thread.verify_consistency(text)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_status(self) -> dict:
        """
        Get status of all services.

        Returns:
            dict with service availability info
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "services": {
                "llm_gateway": self._llm_gateway is not None,
                "vector_store": self._vector_store is not None,
                "ethics_scrubber": self._ethics_scrubber is not None,
                "dna_profile": self._dna_profile is not None,
                "zotero_sentinel": self._zotero_sentinel is not None,
                "auditor": self._auditor is not None,
                "red_thread": self._red_thread is not None,
            },
            "dna_profile_available": DNA_PROFILE_PATH.exists(),
        }

    def reset(self):
        """Reset all cached service instances."""
        self._llm_gateway = None
        self._vector_store = None
        self._ethics_scrubber = None
        self._dna_profile = None
        self._zotero_sentinel = None
        self._auditor = None
        self._red_thread = None


# =============================================================================
# GLOBAL ACCESSOR
# =============================================================================

_services_instance: Optional[PHDxServices] = None


def get_services() -> PHDxServices:
    """
    Get the global PHDx services instance.

    Returns:
        PHDxServices singleton instance
    """
    global _services_instance
    if _services_instance is None:
        _services_instance = PHDxServices()
    return _services_instance


def reset_services():
    """Reset the global services instance."""
    global _services_instance
    if _services_instance is not None:
        _services_instance.reset()
    _services_instance = None


# =============================================================================
# CLI TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Services - Status Check")
    print("=" * 60)

    services = get_services()
    status = services.get_status()

    print(f"\nTimestamp: {status['timestamp']}")
    print(f"DNA Profile Available: {status['dna_profile_available']}")

    print("\nService Status:")
    for service, loaded in status['services'].items():
        indicator = "+" if loaded else "-"
        print(f"  [{indicator}] {service}")

    print("\n" + "=" * 60)
