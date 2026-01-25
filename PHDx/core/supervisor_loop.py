"""
Supervisor Loop - Feedback Analysis Engine for PHDx

This module watches the /feedback folder for supervisor feedback files,
analyzes them using Claude, and maps feedback to specific sections in
the /drafts folder for targeted revision suggestions.

Folder: PHDx/feedback/
Output: data/supervisor_analysis.json
"""

import json
import re
from datetime import datetime
from pathlib import Path
from hashlib import md5

import anthropic
from docx import Document
from dotenv import load_dotenv

# Import ethics utilities for AI usage logging
try:
    from core.ethics_utils import log_ai_usage, scrub_text
    from core.secrets_utils import get_secret
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.ethics_utils import log_ai_usage, scrub_text
    from core.secrets_utils import get_secret

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
FEEDBACK_DIR = ROOT_DIR / "feedback"
DRAFTS_DIR = ROOT_DIR / "drafts"
DATA_DIR = ROOT_DIR / "data"
ANALYSIS_OUTPUT = DATA_DIR / "supervisor_analysis.json"


class SupervisorLoop:
    """
    Watches /feedback folder and analyzes supervisor comments,
    mapping them to specific thesis sections for targeted edits.
    """

    def __init__(self):
        """Initialize the supervisor loop with Claude client."""
        api_key = get_secret("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=api_key) if api_key else None

        # Ensure directories exist
        FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing analysis if available
        self.analysis_cache = self._load_analysis_cache()

    def _load_analysis_cache(self) -> dict:
        """Load existing analysis from cache file."""
        if ANALYSIS_OUTPUT.exists():
            try:
                with open(ANALYSIS_OUTPUT, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"feedback_items": [], "last_updated": None}
        return {"feedback_items": [], "last_updated": None}

    def _save_analysis_cache(self):
        """Save analysis to cache file."""
        self.analysis_cache["last_updated"] = datetime.now().isoformat()
        with open(ANALYSIS_OUTPUT, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_cache, f, indent=2, ensure_ascii=False)

    def _get_file_hash(self, filepath: Path) -> str:
        """Generate hash for a file to detect changes."""
        with open(filepath, 'rb') as f:
            return md5(f.read(), usedforsecurity=False).hexdigest()

    def _load_drafts_content(self) -> dict:
        """Load all draft content for mapping."""
        drafts = {}

        if not DRAFTS_DIR.exists():
            return drafts

        for docx_file in DRAFTS_DIR.glob("*.docx"):
            try:
                doc = Document(docx_file)
                paragraphs = []

                for i, para in enumerate(doc.paragraphs):
                    if para.text.strip():
                        paragraphs.append({
                            "index": i,
                            "text": para.text.strip(),
                            "word_count": len(para.text.split())
                        })

                drafts[docx_file.stem] = {
                    "filename": docx_file.name,
                    "paragraphs": paragraphs,
                    "total_words": sum(p["word_count"] for p in paragraphs)
                }

            except Exception as e:
                print(f"Error loading {docx_file.name}: {e}")

        return drafts

    def scan_feedback_folder(self) -> list[dict]:
        """
        Scan the /feedback folder for new or updated feedback files.

        Returns:
            List of feedback file info dicts
        """
        feedback_files = []

        if not FEEDBACK_DIR.exists():
            FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
            return feedback_files

        # Support .txt and .md files
        for pattern in ["*.txt", "*.md"]:
            for filepath in FEEDBACK_DIR.glob(pattern):
                file_hash = self._get_file_hash(filepath)

                # Check if already processed
                existing = next(
                    (f for f in self.analysis_cache.get("feedback_items", [])
                     if f.get("filename") == filepath.name),
                    None
                )

                is_new = existing is None
                is_modified = existing and existing.get("file_hash") != file_hash

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                feedback_files.append({
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "file_hash": file_hash,
                    "content": content,
                    "word_count": len(content.split()),
                    "is_new": is_new,
                    "is_modified": is_modified,
                    "needs_analysis": is_new or is_modified,
                    "modified_time": datetime.fromtimestamp(
                        filepath.stat().st_mtime
                    ).isoformat()
                })

        return feedback_files

    def analyze_feedback(self, feedback_text: str, feedback_filename: str) -> dict:
        """
        Analyze supervisor feedback and map to thesis sections.

        Args:
            feedback_text: The raw feedback text
            feedback_filename: Name of the feedback file

        Returns:
            dict: Analysis with mapped suggestions
                {
                    "feedback_id": str,
                    "timestamp": str,
                    "filename": str,
                    "status": "success" | "error",
                    "summary": str,
                    "key_themes": [str],
                    "mapped_suggestions": [
                        {
                            "suggestion_id": str,
                            "feedback_quote": str,
                            "target_chapter": str,
                            "target_section": str,
                            "action_type": "expand" | "revise" | "add" | "remove" | "clarify",
                            "priority": "high" | "medium" | "low",
                            "suggestion_text": str,
                            "theoretical_focus": str | null,
                            "specific_instruction": str
                        }
                    ],
                    "overall_tone": "positive" | "critical" | "mixed" | "neutral",
                    "estimated_revision_scope": "minor" | "moderate" | "major"
                }
        """
        feedback_id = md5(
            f"{feedback_text[:100]}{datetime.now().isoformat()}".encode(),
            usedforsecurity=False
        ).hexdigest()[:10]

        result = {
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat(),
            "filename": feedback_filename,
            "status": "error",
            "summary": "",
            "key_themes": [],
            "mapped_suggestions": [],
            "overall_tone": "neutral",
            "estimated_revision_scope": "moderate"
        }

        if not self.claude_client:
            result["error"] = "ANTHROPIC_API_KEY not configured"
            return result

        if len(feedback_text.strip()) < 20:
            result["error"] = "Feedback too short for analysis"
            return result

        # Load drafts for context
        drafts = self._load_drafts_content()
        drafts_summary = ""

        if drafts:
            drafts_summary = "AVAILABLE THESIS CHAPTERS:\n"
            for chapter_name, chapter_data in drafts.items():
                drafts_summary += f"\n## {chapter_name} ({chapter_data['total_words']} words)\n"
                # Include first few paragraphs as context
                for para in chapter_data['paragraphs'][:3]:
                    drafts_summary += f"  - Para {para['index']}: {para['text'][:100]}...\n"

        # Ethics scrubbing
        scrub_result = scrub_text(feedback_text)
        scrubbed_feedback = scrub_result["scrubbed_text"]
        was_scrubbed = scrub_result["total_redactions"] > 0

        # Build analysis prompt
        prompt = f"""You are an expert PhD thesis advisor assistant. Analyze the following SUPERVISOR FEEDBACK and map each comment to specific thesis sections.

SUPERVISOR FEEDBACK:
{scrubbed_feedback}

{drafts_summary if drafts_summary else "NOTE: No thesis chapters currently loaded."}

Analyze this feedback and return a JSON object with:
1. A summary of the feedback
2. Key themes identified
3. Mapped suggestions - each feedback point mapped to:
   - Which chapter/section it applies to
   - What action is needed (expand, revise, add, remove, clarify)
   - Priority level
   - Specific instruction for the student
   - Any theoretical focus mentioned (e.g., "Bourdieu", "critical theory")

Return ONLY valid JSON in this structure:
{{
    "summary": "<2-3 sentence summary of the feedback>",
    "key_themes": ["<theme1>", "<theme2>", ...],
    "mapped_suggestions": [
        {{
            "suggestion_id": "<unique_id>",
            "feedback_quote": "<exact quote from feedback>",
            "target_chapter": "<chapter name or 'General'>",
            "target_section": "<specific section if identifiable>",
            "action_type": "expand" | "revise" | "add" | "remove" | "clarify",
            "priority": "high" | "medium" | "low",
            "suggestion_text": "<actionable suggestion for the student>",
            "theoretical_focus": "<theorist/framework mentioned or null>",
            "specific_instruction": "<detailed instruction, e.g., 'Add 500 words on Bourdieu's concept of cultural capital'>"
        }}
    ],
    "overall_tone": "positive" | "critical" | "mixed" | "neutral",
    "estimated_revision_scope": "minor" | "moderate" | "major"
}}

Be specific and actionable. If the supervisor mentions specific theorists (Bourdieu, Foucault, etc.), highlight these prominently."""

        # Log AI usage
        log_ai_usage(
            action_type="supervisor_feedback_analysis",
            data_source="feedback_folder",
            prompt=f"Analyzing feedback: {feedback_filename}",
            was_scrubbed=was_scrubbed,
            redactions_count=scrub_result["total_redactions"]
        )

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text.strip()

            # Clean markdown wrapping if present
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            analysis = json.loads(response_text)

            # Populate result
            result["status"] = "success"
            result["summary"] = analysis.get("summary", "")
            result["key_themes"] = analysis.get("key_themes", [])
            result["mapped_suggestions"] = analysis.get("mapped_suggestions", [])
            result["overall_tone"] = analysis.get("overall_tone", "neutral")
            result["estimated_revision_scope"] = analysis.get(
                "estimated_revision_scope", "moderate"
            )

        except json.JSONDecodeError as e:
            result["error"] = f"Failed to parse AI response: {str(e)}"
            result["raw_response"] = response_text if 'response_text' in locals() else None

        except Exception as e:
            result["error"] = f"Analysis failed: {str(e)}"

        return result

    def process_new_feedback(self) -> dict:
        """
        Process all new or modified feedback files.

        Returns:
            dict: Processing report
                {
                    "processed_count": int,
                    "new_files": [str],
                    "modified_files": [str],
                    "errors": [str],
                    "total_suggestions": int
                }
        """
        report = {
            "processed_count": 0,
            "new_files": [],
            "modified_files": [],
            "errors": [],
            "total_suggestions": 0,
            "timestamp": datetime.now().isoformat()
        }

        feedback_files = self.scan_feedback_folder()

        for feedback in feedback_files:
            if not feedback["needs_analysis"]:
                continue

            print(f"Processing feedback: {feedback['filename']}...")

            try:
                analysis = self.analyze_feedback(
                    feedback["content"],
                    feedback["filename"]
                )

                if analysis["status"] == "success":
                    # Update cache
                    existing_idx = next(
                        (i for i, f in enumerate(self.analysis_cache["feedback_items"])
                         if f.get("filename") == feedback["filename"]),
                        None
                    )

                    feedback_entry = {
                        "filename": feedback["filename"],
                        "file_hash": feedback["file_hash"],
                        "modified_time": feedback["modified_time"],
                        "analysis": analysis
                    }

                    if existing_idx is not None:
                        self.analysis_cache["feedback_items"][existing_idx] = feedback_entry
                        report["modified_files"].append(feedback["filename"])
                    else:
                        self.analysis_cache["feedback_items"].append(feedback_entry)
                        report["new_files"].append(feedback["filename"])

                    report["processed_count"] += 1
                    report["total_suggestions"] += len(analysis["mapped_suggestions"])

                else:
                    report["errors"].append(
                        f"{feedback['filename']}: {analysis.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                report["errors"].append(f"{feedback['filename']}: {str(e)}")

        # Save updated cache
        self._save_analysis_cache()

        return report

    def get_latest_suggestions(self, limit: int = 10) -> list[dict]:
        """
        Get the most recent suggestions across all feedback.

        Args:
            limit: Maximum number of suggestions to return

        Returns:
            List of suggestion dicts with source info
        """
        all_suggestions = []

        for feedback_item in self.analysis_cache.get("feedback_items", []):
            analysis = feedback_item.get("analysis", {})
            for suggestion in analysis.get("mapped_suggestions", []):
                all_suggestions.append({
                    **suggestion,
                    "source_file": feedback_item["filename"],
                    "feedback_date": feedback_item.get("modified_time", ""),
                    "overall_tone": analysis.get("overall_tone", "neutral")
                })

        # Sort by priority (high first) and then by date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        all_suggestions.sort(
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 3),
                x.get("feedback_date", "")
            ),
            reverse=False
        )

        return all_suggestions[:limit]

    def get_suggestions_by_chapter(self, chapter_name: str) -> list[dict]:
        """
        Get suggestions filtered by target chapter.

        Args:
            chapter_name: Chapter name to filter by

        Returns:
            List of suggestions for that chapter
        """
        suggestions = self.get_latest_suggestions(limit=100)
        return [
            s for s in suggestions
            if chapter_name.lower() in s.get("target_chapter", "").lower()
            or s.get("target_chapter", "").lower() == "general"
        ]

    def get_feedback_summary(self) -> dict:
        """
        Get a summary of all processed feedback.

        Returns:
            dict: Summary statistics
        """
        feedback_items = self.analysis_cache.get("feedback_items", [])

        if not feedback_items:
            return {
                "total_feedback_files": 0,
                "total_suggestions": 0,
                "by_priority": {"high": 0, "medium": 0, "low": 0},
                "by_action": {},
                "key_themes": [],
                "theoretical_focuses": [],
                "overall_revision_scope": "none",
                "last_updated": None
            }

        all_suggestions = []
        all_themes = []
        theoretical_focuses = []

        for item in feedback_items:
            analysis = item.get("analysis", {})
            all_suggestions.extend(analysis.get("mapped_suggestions", []))
            all_themes.extend(analysis.get("key_themes", []))

            for suggestion in analysis.get("mapped_suggestions", []):
                if suggestion.get("theoretical_focus"):
                    theoretical_focuses.append(suggestion["theoretical_focus"])

        # Count by priority
        by_priority = {"high": 0, "medium": 0, "low": 0}
        by_action = {}

        for s in all_suggestions:
            priority = s.get("priority", "low")
            by_priority[priority] = by_priority.get(priority, 0) + 1

            action = s.get("action_type", "other")
            by_action[action] = by_action.get(action, 0) + 1

        # Deduplicate themes
        unique_themes = list(set(all_themes))[:10]
        unique_theoretical = list(set(theoretical_focuses))

        # Determine overall scope
        if by_priority["high"] >= 3:
            overall_scope = "major"
        elif by_priority["high"] >= 1 or by_priority["medium"] >= 3:
            overall_scope = "moderate"
        else:
            overall_scope = "minor"

        return {
            "total_feedback_files": len(feedback_items),
            "total_suggestions": len(all_suggestions),
            "by_priority": by_priority,
            "by_action": by_action,
            "key_themes": unique_themes,
            "theoretical_focuses": unique_theoretical,
            "overall_revision_scope": overall_scope,
            "last_updated": self.analysis_cache.get("last_updated")
        }

    def get_status(self) -> dict:
        """Get current status of the supervisor loop."""
        feedback_files = self.scan_feedback_folder()

        return {
            "feedback_folder": str(FEEDBACK_DIR),
            "folder_exists": FEEDBACK_DIR.exists(),
            "total_feedback_files": len(feedback_files),
            "pending_analysis": sum(1 for f in feedback_files if f["needs_analysis"]),
            "processed_files": len(self.analysis_cache.get("feedback_items", [])),
            "last_updated": self.analysis_cache.get("last_updated")
        }


# =============================================================================
# STREAMLIT WIDGET FOR SIDEBAR
# =============================================================================

def render_supervisor_notes_widget(supervisor_loop: SupervisorLoop, current_chapter: str = ""):
    """
    Render the Supervisor Notes panel for Streamlit sidebar.

    Args:
        supervisor_loop: SupervisorLoop instance
        current_chapter: Currently selected chapter for filtering
    """
    import streamlit as st

    st.markdown("### 📝 Supervisor Notes")

    status = supervisor_loop.get_status()

    if not status["folder_exists"]:
        st.info(f"Feedback folder created at:\n`{status['feedback_folder']}`")
        st.markdown("Add `.txt` or `.md` feedback files to this folder.")
        return

    if status["total_feedback_files"] == 0:
        st.info("No feedback files found.")
        st.markdown(f"Add feedback to:\n`{status['feedback_folder']}`")
        return

    # Process pending feedback
    if status["pending_analysis"] > 0:
        if st.button(f"🔄 Process {status['pending_analysis']} New Feedback", use_container_width=True):
            with st.spinner("Analyzing feedback..."):
                report = supervisor_loop.process_new_feedback()
                if report["processed_count"] > 0:
                    st.success(f"Processed {report['processed_count']} file(s)")
                if report["errors"]:
                    for err in report["errors"]:
                        st.error(err)
                st.rerun()

    # Get summary
    summary = supervisor_loop.get_feedback_summary()

    if summary["total_suggestions"] == 0:
        st.info("No suggestions yet. Click 'Process' above.")
        return

    # Display summary stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Suggestions", summary["total_suggestions"])
    with col2:
        scope_colors = {"minor": "🟢", "moderate": "🟡", "major": "🔴"}
        scope_icon = scope_colors.get(summary["overall_revision_scope"], "⚪")
        st.metric("Revision Scope", f"{scope_icon} {summary['overall_revision_scope'].title()}")

    # Priority breakdown
    st.markdown("**By Priority:**")
    priorities = summary["by_priority"]
    st.markdown(
        f"🔴 High: **{priorities['high']}** | "
        f"🟡 Medium: **{priorities['medium']}** | "
        f"🟢 Low: **{priorities['low']}**"
    )

    st.markdown("---")

    # Get suggestions (filtered by chapter if applicable)
    if current_chapter and current_chapter != "Free Writing":
        suggestions = supervisor_loop.get_suggestions_by_chapter(current_chapter)
        st.markdown(f"**Suggestions for {current_chapter}:**")
    else:
        suggestions = supervisor_loop.get_latest_suggestions(limit=5)
        st.markdown("**Latest Suggestions:**")

    if not suggestions:
        st.info("No suggestions for this chapter.")
        return

    # Display suggestions
    for i, suggestion in enumerate(suggestions[:5], 1):
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            suggestion.get("priority", "low"), "⚪"
        )
        action_icon = {
            "expand": "📈",
            "revise": "✏️",
            "add": "➕",
            "remove": "➖",
            "clarify": "💡"
        }.get(suggestion.get("action_type", ""), "📌")

        with st.expander(
            f"{priority_icon} {action_icon} {suggestion.get('target_chapter', 'General')}"
        ):
            # Theoretical focus highlight
            if suggestion.get("theoretical_focus"):
                st.markdown(
                    f"**📚 Focus on:** `{suggestion['theoretical_focus']}`"
                )

            st.markdown(f"**Suggestion:** {suggestion.get('suggestion_text', '')}")

            if suggestion.get("specific_instruction"):
                st.markdown(f"**Action:** {suggestion['specific_instruction']}")

            if suggestion.get("feedback_quote"):
                st.caption(f"*\"{suggestion['feedback_quote'][:100]}...\"*")

            st.caption(f"Source: {suggestion.get('source_file', 'unknown')}")

    # Theoretical focuses summary
    if summary["theoretical_focuses"]:
        st.markdown("---")
        st.markdown("**📚 Theoretical Focuses Mentioned:**")
        for theorist in summary["theoretical_focuses"][:5]:
            st.markdown(f"- {theorist}")


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================

def process_feedback() -> dict:
    """
    Standalone function to process all pending feedback.

    Usage:
        from core.supervisor_loop import process_feedback
        report = process_feedback()
    """
    loop = SupervisorLoop()
    return loop.process_new_feedback()


def get_suggestions(chapter: str = "") -> list[dict]:
    """
    Standalone function to get suggestions.

    Usage:
        from core.supervisor_loop import get_suggestions
        suggestions = get_suggestions("Literature Review")
    """
    loop = SupervisorLoop()
    if chapter:
        return loop.get_suggestions_by_chapter(chapter)
    return loop.get_latest_suggestions()


if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Supervisor Loop - Feedback Analysis Engine")
    print("=" * 60)

    loop = SupervisorLoop()

    status = loop.get_status()
    print(f"\nFeedback folder: {status['feedback_folder']}")
    print(f"Total feedback files: {status['total_feedback_files']}")
    print(f"Pending analysis: {status['pending_analysis']}")
    print(f"Processed files: {status['processed_files']}")

    if status["pending_analysis"] > 0:
        print(f"\n[Processing {status['pending_analysis']} new feedback files...]")
        report = loop.process_new_feedback()
        print(f"Processed: {report['processed_count']}")
        print(f"Total suggestions: {report['total_suggestions']}")

        if report["errors"]:
            print("Errors:")
            for err in report["errors"]:
                print(f"  - {err}")

    print("\n" + "=" * 60)
    print("Summary:")
    summary = loop.get_feedback_summary()
    print(f"  Total suggestions: {summary['total_suggestions']}")
    print(f"  Revision scope: {summary['overall_revision_scope']}")
    print(f"  Key themes: {', '.join(summary['key_themes'][:5])}")

    if summary["theoretical_focuses"]:
        print(f"  Theoretical focuses: {', '.join(summary['theoretical_focuses'])}")

    print("=" * 60)
