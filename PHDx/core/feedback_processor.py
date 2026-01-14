"""
Supervisor Feedback Processor - PHDx

Parses supervisor feedback documents (PDF/DOCX/TXT), categorizes feedback
using Claude AI, and maps comments to relevant thesis sections.

Categories:
- Major Structural: Chapter organization, argument flow, missing sections
- Minor/Stylistic: Grammar, clarity, word choice, formatting
- Citations Needed: Missing references, citation format issues
"""

import json
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from enum import Enum

import anthropic
from dotenv import load_dotenv

# Document parsing libraries
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# Import ethics utilities
try:
    from core.ethics_utils import scrub_text, log_ai_usage
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from core.ethics_utils import scrub_text, log_ai_usage
    except ImportError:
        def scrub_text(text):
            return {"scrubbed_text": text, "total_redactions": 0}
        def log_ai_usage(*args, **kwargs):
            pass

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
FEEDBACK_DIR = ROOT_DIR / "feedback"
DRAFTS_DIR = ROOT_DIR / "drafts"
DATA_DIR = ROOT_DIR / "data"
FEEDBACK_CACHE = DATA_DIR / "feedback_analysis.json"


class FeedbackCategory(Enum):
    """Categories for supervisor feedback."""
    MAJOR_STRUCTURAL = "major_structural"
    MINOR_STYLISTIC = "minor_stylistic"
    CITATIONS_NEEDED = "citations_needed"
    GENERAL = "general"


@dataclass
class FeedbackItem:
    """A single piece of categorized feedback."""
    id: str
    text: str
    category: str
    priority: str  # high, medium, low
    chapter: str
    section: str
    target_paragraph: str  # text snippet to highlight
    action_required: str
    resolved: bool = False
    source_file: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackItem":
        return cls(**data)


class FeedbackProcessor:
    """
    Processes supervisor feedback documents and categorizes comments.

    Features:
    - Parses PDF, DOCX, and TXT files
    - Uses Claude to categorize feedback
    - Maps feedback to thesis sections
    - Tracks resolution status
    """

    def __init__(self):
        """Initialize the feedback processor."""
        self.feedback_items: list[FeedbackItem] = []
        self.processed_files: dict[str, str] = {}  # filename -> hash

        # Initialize Claude client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude = anthropic.Anthropic(api_key=api_key) if api_key else None

        # Load existing feedback
        self._load_cache()

    def _load_cache(self):
        """Load cached feedback analysis."""
        if FEEDBACK_CACHE.exists():
            try:
                with open(FEEDBACK_CACHE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.feedback_items = [
                        FeedbackItem.from_dict(item)
                        for item in data.get("items", [])
                    ]
                    self.processed_files = data.get("processed_files", {})
            except (json.JSONDecodeError, IOError):
                self.feedback_items = []

    def _save_cache(self):
        """Save feedback analysis to cache."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(FEEDBACK_CACHE, 'w', encoding='utf-8') as f:
            json.dump({
                "items": [item.to_dict() for item in self.feedback_items],
                "processed_files": self.processed_files,
                "last_updated": datetime.now().isoformat()
            }, f, indent=2)

    def _get_file_hash(self, filepath: Path) -> str:
        """Get hash of file for change detection."""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def _parse_txt(self, filepath: Path) -> str:
        """Parse a text file."""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def _parse_docx(self, filepath: Path) -> str:
        """Parse a DOCX file."""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not installed. Run: pip install python-docx")

        doc = DocxDocument(filepath)
        paragraphs = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)

        # Also extract comments if present
        # Note: python-docx doesn't easily extract comments,
        # so we focus on the main text

        return "\n\n".join(paragraphs)

    def _parse_pdf(self, filepath: Path) -> str:
        """Parse a PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

        doc = fitz.open(filepath)
        text_parts = []

        for page in doc:
            text_parts.append(page.get_text())

        doc.close()
        return "\n\n".join(text_parts)

    def parse_document(self, filepath: Path) -> str:
        """
        Parse a document based on its extension.

        Supports: .txt, .md, .docx, .pdf
        """
        suffix = filepath.suffix.lower()

        if suffix in ['.txt', '.md']:
            return self._parse_txt(filepath)
        elif suffix == '.docx':
            return self._parse_docx(filepath)
        elif suffix == '.pdf':
            return self._parse_pdf(filepath)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def _get_draft_context(self) -> str:
        """Get summary of draft structure for context."""
        context_parts = []

        if not DRAFTS_DIR.exists():
            return "No drafts available."

        for docx_file in DRAFTS_DIR.glob("*.docx"):
            try:
                if DOCX_AVAILABLE:
                    doc = DocxDocument(docx_file)
                    # Get first few paragraphs as context
                    preview = []
                    for para in doc.paragraphs[:10]:
                        if para.text.strip():
                            preview.append(para.text.strip()[:200])

                    context_parts.append(f"**{docx_file.name}**:\n" + "\n".join(preview[:5]))
            except Exception:
                continue

        return "\n\n---\n\n".join(context_parts) if context_parts else "No drafts available."

    def categorize_feedback(self, feedback_text: str, source_file: str = "") -> list[FeedbackItem]:
        """
        Use Claude to categorize feedback into structured items.

        Args:
            feedback_text: Raw text from feedback document
            source_file: Name of the source file

        Returns:
            List of categorized FeedbackItem objects
        """
        if not self.claude:
            # Return uncategorized if no Claude available
            return [FeedbackItem(
                id=hashlib.md5(feedback_text[:100].encode()).hexdigest()[:8],
                text=feedback_text,
                category=FeedbackCategory.GENERAL.value,
                priority="medium",
                chapter="Unknown",
                section="Unknown",
                target_paragraph="",
                action_required="Review feedback",
                source_file=source_file,
                created_at=datetime.now().isoformat()
            )]

        # Get draft context for mapping
        draft_context = self._get_draft_context()

        # Scrub feedback before sending to AI
        scrub_result = scrub_text(feedback_text)
        scrubbed_feedback = scrub_result["scrubbed_text"]

        prompt = f"""You are a PhD thesis feedback analyzer. Parse the supervisor feedback and categorize each distinct comment.

FEEDBACK DOCUMENT:
{scrubbed_feedback[:8000]}

DRAFT CONTEXT (for mapping feedback to sections):
{draft_context[:3000]}

For each distinct piece of feedback, create a JSON object with:
- "text": The feedback comment (verbatim or paraphrased)
- "category": One of "major_structural", "minor_stylistic", "citations_needed", or "general"
  - major_structural: Chapter organization, argument flow, missing sections, theoretical framework issues
  - minor_stylistic: Grammar, clarity, word choice, formatting, sentence structure
  - citations_needed: Missing references, citation format, need for additional sources
  - general: Other feedback that doesn't fit above categories
- "priority": "high", "medium", or "low" based on impact on thesis quality
- "chapter": Best guess at which chapter this applies to (e.g., "Chapter 1", "Literature Review", "Methodology")
- "section": Specific section if identifiable (e.g., "Introduction", "2.3 Theoretical Framework")
- "target_paragraph": A short text snippet (10-20 words) from the draft that this feedback targets, for highlighting
- "action_required": Brief action statement (e.g., "Restructure argument in section 2.3", "Add citation for claim")

Return a JSON array of feedback objects. Be thorough - extract ALL distinct feedback points.

Example output:
[
  {{
    "text": "The transition between sections 2.1 and 2.2 is abrupt",
    "category": "major_structural",
    "priority": "high",
    "chapter": "Chapter 2",
    "section": "2.1-2.2",
    "target_paragraph": "Having established the theoretical basis",
    "action_required": "Add transitional paragraph connecting sections"
  }}
]

Return ONLY valid JSON array, no markdown."""

        # Log AI usage
        log_ai_usage(
            action_type="categorize_feedback",
            data_source="feedback_document",
            prompt=f"Categorizing feedback from: {source_file}",
            was_scrubbed=scrub_result["total_redactions"] > 0,
            redactions_count=scrub_result["total_redactions"]
        )

        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Clean markdown if present
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            items_data = json.loads(response_text)

            feedback_items = []
            for i, item in enumerate(items_data):
                feedback_items.append(FeedbackItem(
                    id=f"{hashlib.md5(source_file.encode()).hexdigest()[:4]}_{i:03d}",
                    text=item.get("text", ""),
                    category=item.get("category", "general"),
                    priority=item.get("priority", "medium"),
                    chapter=item.get("chapter", "Unknown"),
                    section=item.get("section", ""),
                    target_paragraph=item.get("target_paragraph", ""),
                    action_required=item.get("action_required", ""),
                    source_file=source_file,
                    created_at=datetime.now().isoformat()
                ))

            return feedback_items

        except Exception as e:
            print(f"Error categorizing feedback: {e}")
            return [FeedbackItem(
                id=hashlib.md5(feedback_text[:100].encode()).hexdigest()[:8],
                text=feedback_text[:500],
                category=FeedbackCategory.GENERAL.value,
                priority="medium",
                chapter="Unknown",
                section="Unknown",
                target_paragraph="",
                action_required="Review feedback manually",
                source_file=source_file,
                created_at=datetime.now().isoformat()
            )]

    def process_feedback_folder(self, force_reprocess: bool = False) -> dict:
        """
        Process all feedback documents in the /feedback folder.

        Args:
            force_reprocess: If True, reprocess all files even if cached

        Returns:
            Summary of processing results
        """
        if not FEEDBACK_DIR.exists():
            FEEDBACK_DIR.mkdir(parents=True)
            return {"status": "created", "message": "Feedback folder created", "items": 0}

        results = {
            "files_processed": 0,
            "files_skipped": 0,
            "new_items": 0,
            "errors": []
        }

        supported_extensions = {'.txt', '.md', '.docx', '.pdf'}

        for filepath in FEEDBACK_DIR.iterdir():
            if filepath.suffix.lower() not in supported_extensions:
                continue

            if filepath.name.startswith('.'):
                continue

            try:
                # Check if file has changed
                file_hash = self._get_file_hash(filepath)

                if not force_reprocess and filepath.name in self.processed_files:
                    if self.processed_files[filepath.name] == file_hash:
                        results["files_skipped"] += 1
                        continue

                # Parse and categorize
                feedback_text = self.parse_document(filepath)

                if not feedback_text.strip():
                    results["errors"].append(f"{filepath.name}: Empty document")
                    continue

                # Remove old items from this file
                self.feedback_items = [
                    item for item in self.feedback_items
                    if item.source_file != filepath.name
                ]

                # Categorize new feedback
                new_items = self.categorize_feedback(feedback_text, filepath.name)
                self.feedback_items.extend(new_items)

                # Update processed files
                self.processed_files[filepath.name] = file_hash

                results["files_processed"] += 1
                results["new_items"] += len(new_items)

            except Exception as e:
                results["errors"].append(f"{filepath.name}: {str(e)}")

        # Save to cache
        self._save_cache()

        return results

    def get_feedback_by_category(self) -> dict[str, list[FeedbackItem]]:
        """Get feedback items grouped by category."""
        grouped = {
            "major_structural": [],
            "minor_stylistic": [],
            "citations_needed": [],
            "general": []
        }

        for item in self.feedback_items:
            category = item.category
            if category in grouped:
                grouped[category].append(item)
            else:
                grouped["general"].append(item)

        return grouped

    def get_feedback_by_chapter(self) -> dict[str, list[FeedbackItem]]:
        """Get feedback items grouped by chapter."""
        grouped = {}

        for item in self.feedback_items:
            chapter = item.chapter or "Unknown"
            if chapter not in grouped:
                grouped[chapter] = []
            grouped[chapter].append(item)

        return grouped

    def get_unresolved_count(self) -> dict:
        """Get count of unresolved feedback by category."""
        counts = {
            "major_structural": 0,
            "minor_stylistic": 0,
            "citations_needed": 0,
            "general": 0,
            "total": 0
        }

        for item in self.feedback_items:
            if not item.resolved:
                category = item.category if item.category in counts else "general"
                counts[category] += 1
                counts["total"] += 1

        return counts

    def mark_resolved(self, item_id: str, resolved: bool = True) -> bool:
        """Mark a feedback item as resolved/unresolved."""
        for item in self.feedback_items:
            if item.id == item_id:
                item.resolved = resolved
                self._save_cache()
                return True
        return False

    def get_item_by_id(self, item_id: str) -> Optional[FeedbackItem]:
        """Get a specific feedback item by ID."""
        for item in self.feedback_items:
            if item.id == item_id:
                return item
        return None

    def get_stats(self) -> dict:
        """Get processor statistics."""
        by_category = self.get_feedback_by_category()
        unresolved = self.get_unresolved_count()

        return {
            "total_items": len(self.feedback_items),
            "files_processed": len(self.processed_files),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "unresolved": unresolved,
            "resolved": len(self.feedback_items) - unresolved["total"]
        }


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================

def render_feedback_tab(processor: FeedbackProcessor):
    """
    Render the Supervisor Feedback tab in the dashboard.

    Features:
    - Process new feedback button
    - Categorized checklist view
    - Click to highlight functionality
    """
    import streamlit as st

    st.markdown("### Supervisor Feedback")
    st.markdown("*Categorized feedback from your supervisor with actionable checklist*")

    # Process feedback button
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Process Feedback", type="primary", use_container_width=True):
            with st.spinner("Processing feedback documents..."):
                results = processor.process_feedback_folder()

                if results.get("errors"):
                    for err in results["errors"]:
                        st.error(err)

                st.success(f"Processed {results['files_processed']} files, {results['new_items']} items found")
                st.rerun()

    with col2:
        if st.button("Refresh", use_container_width=True):
            results = processor.process_feedback_folder(force_reprocess=True)
            st.rerun()

    with col3:
        stats = processor.get_stats()
        unresolved = stats["unresolved"]["total"]
        total = stats["total_items"]
        resolved = stats["resolved"]

        if total > 0:
            progress = resolved / total
            st.progress(progress, text=f"Progress: {resolved}/{total} resolved ({progress*100:.0f}%)")
        else:
            st.info("No feedback processed yet. Add files to /feedback folder.")

    # Initialize session state for highlighting
    if "highlight_text" not in st.session_state:
        st.session_state.highlight_text = None
    if "highlight_chapter" not in st.session_state:
        st.session_state.highlight_chapter = None

    # Show highlighted text notification
    if st.session_state.highlight_text:
        st.markdown(f"""
        <div style="background: rgba(0, 113, 206, 0.15); border: 1px solid rgba(0, 113, 206, 0.4);
                    border-radius: 8px; padding: 0.75rem; margin: 1rem 0;">
            <strong>Highlighting in Drafting Pane:</strong><br>
            <em>"{st.session_state.highlight_text[:100]}..."</em>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Clear Highlight"):
                st.session_state.highlight_text = None
                st.session_state.highlight_chapter = None
                st.rerun()

    st.markdown("---")

    # Categorized feedback display
    feedback_by_category = processor.get_feedback_by_category()

    # Category tabs
    cat_tabs = st.tabs([
        f"Major Structural ({len(feedback_by_category['major_structural'])})",
        f"Minor/Stylistic ({len(feedback_by_category['minor_stylistic'])})",
        f"Citations Needed ({len(feedback_by_category['citations_needed'])})",
        f"General ({len(feedback_by_category['general'])})"
    ])

    category_keys = ["major_structural", "minor_stylistic", "citations_needed", "general"]
    category_icons = {
        "major_structural": "🏗️",
        "minor_stylistic": "✏️",
        "citations_needed": "📚",
        "general": "📋"
    }
    priority_colors = {
        "high": "#f44336",
        "medium": "#ffc107",
        "low": "#4caf50"
    }

    for tab, cat_key in zip(cat_tabs, category_keys):
        with tab:
            items = feedback_by_category[cat_key]

            if not items:
                st.info(f"No {cat_key.replace('_', ' ')} feedback items.")
                continue

            # Sort by priority (high first)
            priority_order = {"high": 0, "medium": 1, "low": 2}
            items.sort(key=lambda x: (x.resolved, priority_order.get(x.priority, 1)))

            for item in items:
                icon = category_icons.get(cat_key, "📋")
                priority_color = priority_colors.get(item.priority, "#ffc107")

                # Create unique key for checkbox
                checkbox_key = f"fb_{item.id}"

                # Checkbox row
                col1, col2, col3 = st.columns([0.5, 4, 1])

                with col1:
                    resolved = st.checkbox(
                        "",
                        value=item.resolved,
                        key=checkbox_key,
                        label_visibility="collapsed"
                    )

                    # Update if changed
                    if resolved != item.resolved:
                        processor.mark_resolved(item.id, resolved)
                        st.rerun()

                with col2:
                    # Style based on resolved status
                    text_style = "text-decoration: line-through; opacity: 0.6;" if item.resolved else ""

                    st.markdown(f"""
                    <div style="{text_style}">
                        <span style="color: {priority_color}; font-weight: bold;">[{item.priority.upper()}]</span>
                        {icon} <strong>{item.chapter}</strong> - {item.section if item.section else 'General'}
                        <br>
                        <span style="color: rgba(224, 224, 224, 0.9);">{item.text[:150]}{'...' if len(item.text) > 150 else ''}</span>
                        <br>
                        <span style="color: rgba(0, 113, 206, 0.9); font-size: 0.85rem;">
                            Action: {item.action_required}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    # Highlight button
                    if item.target_paragraph and not item.resolved:
                        if st.button("🎯", key=f"hl_{item.id}", help="Highlight in draft"):
                            st.session_state.highlight_text = item.target_paragraph
                            st.session_state.highlight_chapter = item.chapter
                            st.rerun()

                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>",
                           unsafe_allow_html=True)

    # Summary by chapter
    st.markdown("---")
    st.markdown("#### Feedback by Chapter")

    by_chapter = processor.get_feedback_by_chapter()

    if by_chapter:
        for chapter, items in sorted(by_chapter.items()):
            unresolved_count = sum(1 for i in items if not i.resolved)
            total_count = len(items)

            if unresolved_count > 0:
                st.markdown(f"**{chapter}**: {unresolved_count}/{total_count} unresolved")
            else:
                st.markdown(f"**{chapter}**: All {total_count} resolved ✓")
    else:
        st.info("No feedback items to display.")


def get_highlight_text() -> Optional[str]:
    """
    Get the current text to highlight in the drafting pane.

    Call this from the drafting tab to check if text should be highlighted.
    """
    import streamlit as st
    return st.session_state.get("highlight_text")


def get_highlight_chapter() -> Optional[str]:
    """Get the chapter associated with the current highlight."""
    import streamlit as st
    return st.session_state.get("highlight_chapter")


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for testing feedback processor."""
    print("=" * 60)
    print("PHDx Supervisor Feedback Processor")
    print("=" * 60)

    processor = FeedbackProcessor()

    print(f"\nFeedback directory: {FEEDBACK_DIR}")
    print(f"PDF support: {'Yes' if PDF_AVAILABLE else 'No (pip install pymupdf)'}")
    print(f"DOCX support: {'Yes' if DOCX_AVAILABLE else 'No (pip install python-docx)'}")
    print(f"Claude API: {'Configured' if processor.claude else 'Not configured'}")

    # Process feedback folder
    print("\nProcessing feedback folder...")
    results = processor.process_feedback_folder()

    print(f"\nResults:")
    print(f"  Files processed: {results['files_processed']}")
    print(f"  Files skipped: {results['files_skipped']}")
    print(f"  New items: {results['new_items']}")

    if results['errors']:
        print(f"\n  Errors:")
        for err in results['errors']:
            print(f"    - {err}")

    # Show stats
    stats = processor.get_stats()
    print(f"\nFeedback Statistics:")
    print(f"  Total items: {stats['total_items']}")
    print(f"  Resolved: {stats['resolved']}")
    print(f"  Unresolved: {stats['unresolved']['total']}")
    print(f"\n  By category:")
    for cat, count in stats['by_category'].items():
        print(f"    - {cat}: {count}")

    # Show sample items
    if processor.feedback_items:
        print(f"\nSample feedback items:")
        for item in processor.feedback_items[:3]:
            print(f"\n  [{item.priority.upper()}] {item.category}")
            print(f"  Chapter: {item.chapter}")
            print(f"  Text: {item.text[:80]}...")
            print(f"  Action: {item.action_required}")


if __name__ == "__main__":
    main()
