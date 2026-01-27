"""
PHDx Transparency Module - AI Usage Declaration

Tracks all AI-assisted operations for academic transparency and compliance
with Oxford Brookes University AI usage policies.

Generates exportable declarations for thesis submission.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import io

from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
TRANSPARENCY_LOG = DATA_DIR / "transparency_log.json"
AI_DECLARATION_DIR = DATA_DIR / "declarations"


class AITaskType(Enum):
    """Types of AI-assisted tasks."""

    DRAFT_GENERATION = "draft_generation"
    STYLE_CHECK = "style_check"
    FEEDBACK_SUGGESTION = "feedback_suggestion"
    REVISION_ACCEPTED = "revision_accepted"
    CITATION_ASSIST = "citation_assist"
    STRUCTURE_ADVICE = "structure_advice"
    DNA_ANALYSIS = "dna_analysis"
    COMPLEXITY_CHECK = "complexity_check"
    PII_SCRUB = "pii_scrub"
    OTHER = "other"


@dataclass
class AIUsageEntry:
    """A single AI usage log entry."""

    id: str
    timestamp: str
    task_type: str
    task_description: str
    input_word_count: int
    output_word_count: int
    ai_contribution_percent: float
    chapter: str
    section: str
    model_used: str
    accepted: bool = True
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AIUsageEntry":
        return cls(**data)


class TransparencyLog:
    """
    Tracks all AI-assisted operations for academic transparency.

    Features:
    - Logs every AI interaction with metadata
    - Calculates AI contribution percentages
    - Generates exportable declarations
    - Supports Oxford Brookes AI policy compliance
    """

    def __init__(self):
        """Initialize the transparency log."""
        self.entries: list[AIUsageEntry] = []
        self.metadata: dict = {
            "thesis_title": "",
            "author_name": "",
            "student_id": "",
            "supervisor": "",
            "start_date": "",
            "target_words": 80000,
        }
        self._load()

    def _load(self):
        """Load existing transparency log."""
        if TRANSPARENCY_LOG.exists():
            try:
                with open(TRANSPARENCY_LOG, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.entries = [
                        AIUsageEntry.from_dict(e) for e in data.get("entries", [])
                    ]
                    self.metadata = data.get("metadata", self.metadata)
            except (json.JSONDecodeError, IOError):
                self.entries = []

    def _save(self):
        """Save transparency log."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(TRANSPARENCY_LOG, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "entries": [e.to_dict() for e in self.entries],
                    "metadata": self.metadata,
                    "last_updated": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

    def _generate_id(self) -> str:
        """Generate unique entry ID."""
        import hashlib

        timestamp = datetime.now().isoformat()
        return hashlib.md5(
            f"{timestamp}{len(self.entries)}".encode(), usedforsecurity=False
        ).hexdigest()[:12]

    def _calculate_ai_contribution(
        self, input_text: str, output_text: str, task_type: str
    ) -> float:
        """
        Calculate the AI contribution percentage for a task.

        The calculation considers:
        - Ratio of AI-generated text to input text
        - Type of task (some tasks have inherently higher AI involvement)
        - Whether output was accepted as-is or modified

        Returns:
            Percentage (0-100) representing AI contribution
        """
        input_words = len(input_text.split()) if input_text else 0
        output_words = len(output_text.split()) if output_text else 0

        # Base contribution by task type
        base_contribution = {
            AITaskType.DRAFT_GENERATION.value: 70,
            AITaskType.STYLE_CHECK.value: 10,
            AITaskType.FEEDBACK_SUGGESTION.value: 40,
            AITaskType.REVISION_ACCEPTED.value: 60,
            AITaskType.CITATION_ASSIST.value: 20,
            AITaskType.STRUCTURE_ADVICE.value: 30,
            AITaskType.DNA_ANALYSIS.value: 5,
            AITaskType.COMPLEXITY_CHECK.value: 5,
            AITaskType.PII_SCRUB.value: 5,
            AITaskType.OTHER.value: 25,
        }.get(task_type, 25)

        # Adjust based on output/input ratio
        if input_words > 0 and output_words > 0:
            ratio = output_words / input_words
            if ratio > 2:  # AI generated significantly more
                base_contribution = min(base_contribution * 1.3, 95)
            elif ratio < 0.5:  # AI condensed/edited
                base_contribution = base_contribution * 0.8

        return round(base_contribution, 1)

    def log_draft_generation(
        self,
        input_text: str,
        output_text: str,
        chapter: str = "",
        section: str = "",
        model: str = "claude-sonnet-4",
        notes: str = "",
    ) -> AIUsageEntry:
        """Log a draft generation event."""
        entry = AIUsageEntry(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            task_type=AITaskType.DRAFT_GENERATION.value,
            task_description="AI-assisted draft generation",
            input_word_count=len(input_text.split()) if input_text else 0,
            output_word_count=len(output_text.split()) if output_text else 0,
            ai_contribution_percent=self._calculate_ai_contribution(
                input_text, output_text, AITaskType.DRAFT_GENERATION.value
            ),
            chapter=chapter,
            section=section,
            model_used=model,
            notes=notes,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def log_feedback_suggestion(
        self,
        feedback_text: str,
        suggested_revision: str,
        accepted: bool = False,
        chapter: str = "",
        section: str = "",
        model: str = "claude-sonnet-4",
    ) -> AIUsageEntry:
        """Log a feedback suggestion generation."""
        task_type = (
            AITaskType.REVISION_ACCEPTED.value
            if accepted
            else AITaskType.FEEDBACK_SUGGESTION.value
        )

        entry = AIUsageEntry(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            task_type=task_type,
            task_description="Supervisor feedback revision suggestion"
            + (" (accepted)" if accepted else ""),
            input_word_count=len(feedback_text.split()) if feedback_text else 0,
            output_word_count=len(suggested_revision.split())
            if suggested_revision
            else 0,
            ai_contribution_percent=self._calculate_ai_contribution(
                feedback_text, suggested_revision, task_type
            ),
            chapter=chapter,
            section=section,
            model_used=model,
            accepted=accepted,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def log_style_check(
        self,
        text: str,
        suggestions: str,
        chapter: str = "",
        model: str = "claude-sonnet-4",
    ) -> AIUsageEntry:
        """Log a style check operation."""
        entry = AIUsageEntry(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            task_type=AITaskType.STYLE_CHECK.value,
            task_description="Writing style analysis against DNA profile",
            input_word_count=len(text.split()) if text else 0,
            output_word_count=len(suggestions.split()) if suggestions else 0,
            ai_contribution_percent=self._calculate_ai_contribution(
                text, suggestions, AITaskType.STYLE_CHECK.value
            ),
            chapter=chapter,
            section="",
            model_used=model,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def log_citation_assist(
        self, query: str, citations_found: int, chapter: str = ""
    ) -> AIUsageEntry:
        """Log a citation assistance operation."""
        entry = AIUsageEntry(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            task_type=AITaskType.CITATION_ASSIST.value,
            task_description=f"Citation search and formatting ({citations_found} results)",
            input_word_count=len(query.split()) if query else 0,
            output_word_count=citations_found * 20,  # Estimate
            ai_contribution_percent=20,  # Fixed low contribution
            chapter=chapter,
            section="",
            model_used="zotero-api",
        )
        self.entries.append(entry)
        self._save()
        return entry

    def log_generic(
        self,
        task_type: str,
        description: str,
        input_text: str = "",
        output_text: str = "",
        chapter: str = "",
        section: str = "",
        model: str = "claude-sonnet-4",
    ) -> AIUsageEntry:
        """Log a generic AI operation."""
        entry = AIUsageEntry(
            id=self._generate_id(),
            timestamp=datetime.now().isoformat(),
            task_type=task_type,
            task_description=description,
            input_word_count=len(input_text.split()) if input_text else 0,
            output_word_count=len(output_text.split()) if output_text else 0,
            ai_contribution_percent=self._calculate_ai_contribution(
                input_text, output_text, task_type
            ),
            chapter=chapter,
            section=section,
            model_used=model,
        )
        self.entries.append(entry)
        self._save()
        return entry

    def get_summary_stats(self) -> dict:
        """Get summary statistics for AI usage."""
        if not self.entries:
            return {
                "total_entries": 0,
                "total_ai_words": 0,
                "avg_contribution": 0,
                "by_task_type": {},
                "by_chapter": {},
                "date_range": {"start": None, "end": None},
            }

        total_ai_words = sum(e.output_word_count for e in self.entries)
        avg_contribution = sum(e.ai_contribution_percent for e in self.entries) / len(
            self.entries
        )

        # Group by task type
        by_task = {}
        for e in self.entries:
            if e.task_type not in by_task:
                by_task[e.task_type] = {"count": 0, "words": 0}
            by_task[e.task_type]["count"] += 1
            by_task[e.task_type]["words"] += e.output_word_count

        # Group by chapter
        by_chapter = {}
        for e in self.entries:
            ch = e.chapter or "General"
            if ch not in by_chapter:
                by_chapter[ch] = {"count": 0, "words": 0, "avg_contribution": 0}
            by_chapter[ch]["count"] += 1
            by_chapter[ch]["words"] += e.output_word_count

        # Calculate average contribution per chapter
        for ch in by_chapter:
            ch_entries = [e for e in self.entries if (e.chapter or "General") == ch]
            by_chapter[ch]["avg_contribution"] = (
                sum(e.ai_contribution_percent for e in ch_entries) / len(ch_entries)
                if ch_entries
                else 0
            )

        # Date range
        timestamps = [e.timestamp for e in self.entries]
        timestamps.sort()

        return {
            "total_entries": len(self.entries),
            "total_ai_words": total_ai_words,
            "avg_contribution": round(avg_contribution, 1),
            "by_task_type": by_task,
            "by_chapter": by_chapter,
            "date_range": {
                "start": timestamps[0] if timestamps else None,
                "end": timestamps[-1] if timestamps else None,
            },
        }

    def update_metadata(self, **kwargs):
        """Update thesis metadata."""
        self.metadata.update(kwargs)
        self._save()

    def export_to_csv(self) -> str:
        """Export log to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Date",
                "Task Type",
                "Description",
                "Chapter",
                "Section",
                "Input Words",
                "Output Words",
                "AI Contribution %",
                "Model",
                "Accepted",
            ]
        )

        # Data
        for e in self.entries:
            writer.writerow(
                [
                    e.timestamp[:10],
                    e.task_type,
                    e.task_description,
                    e.chapter,
                    e.section,
                    e.input_word_count,
                    e.output_word_count,
                    e.ai_contribution_percent,
                    e.model_used,
                    "Yes" if e.accepted else "No",
                ]
            )

        return output.getvalue()

    def generate_brookes_declaration(self, final_word_count: int = 50000) -> str:
        """
        Generate the Oxford Brookes AI Declaration document.

        This produces a formatted declaration suitable for thesis submission,
        documenting how AI was used as a 'Critical Research Co-Pilot'.

        Args:
            final_word_count: Total words in final thesis

        Returns:
            Formatted markdown text for the declaration
        """
        stats = self.get_summary_stats()
        meta = self.metadata

        # Calculate overall AI involvement
        total_ai_words = stats["total_ai_words"]
        ai_percentage = (
            (total_ai_words / final_word_count * 100) if final_word_count > 0 else 0
        )
        weighted_contribution = stats["avg_contribution"]

        # Date range
        start_date = stats["date_range"]["start"]
        end_date = stats["date_range"]["end"]
        if start_date:
            start_date = start_date[:10]
        if end_date:
            end_date = end_date[:10]

        declaration = f"""
# Declaration of AI Usage in Academic Research

## Oxford Brookes University
### PhD Thesis AI Transparency Statement

---

## Thesis Information

| Field | Value |
|-------|-------|
| **Thesis Title** | {meta.get("thesis_title", "[Not specified]")} |
| **Author** | {meta.get("author_name", "[Not specified]")} |
| **Student ID** | {meta.get("student_id", "[Not specified]")} |
| **Supervisor** | {meta.get("supervisor", "[Not specified]")} |
| **Final Word Count** | {final_word_count:,} |
| **Declaration Date** | {datetime.now().strftime("%d %B %Y")} |

---

## Executive Summary

This declaration documents the use of artificial intelligence tools during the research and writing of this doctoral thesis. In accordance with Oxford Brookes University's Academic Integrity Policy and the evolving standards for AI transparency in academic research, this document provides a comprehensive account of all AI-assisted operations.

**PHDx (PhD Thesis Command Center)** was employed as a **Critical Research Co-Pilot** to enhance productivity while maintaining academic integrity. The AI tools were used to support, not replace, original scholarly work.

---

## AI Usage Overview

| Metric | Value |
|--------|-------|
| **Total AI-Assisted Operations** | {stats["total_entries"]} |
| **AI-Assisted Word Count** | {total_ai_words:,} words |
| **Percentage of Final Thesis** | {ai_percentage:.1f}% |
| **Average AI Contribution per Task** | {weighted_contribution:.1f}% |
| **Usage Period** | {start_date or "N/A"} to {end_date or "N/A"} |

---

## AI Tools Employed

### Primary Tool: PHDx - PhD Thesis Command Center

PHDx is a custom research assistant built on the Claude AI platform (Anthropic). It was used for the following purposes:

"""
        # Add task type breakdown
        if stats["by_task_type"]:
            declaration += "### Usage by Task Type\n\n"
            declaration += (
                "| Task Type | Operations | Words Processed | Description |\n"
            )
            declaration += (
                "|-----------|------------|-----------------|-------------|\n"
            )

            task_descriptions = {
                "draft_generation": "AI-assisted paragraph drafting with author voice matching",
                "style_check": "Writing style analysis against personal linguistic DNA",
                "feedback_suggestion": "Revision suggestions based on supervisor feedback",
                "revision_accepted": "Accepted AI-suggested revisions",
                "citation_assist": "Citation search and Harvard formatting",
                "structure_advice": "Chapter and section structure recommendations",
                "dna_analysis": "Linguistic fingerprint extraction from writing samples",
                "complexity_check": "Flesch-Kincaid readability analysis",
                "pii_scrub": "Personal data anonymization before AI processing",
                "other": "Miscellaneous AI assistance",
            }

            for task_type, data in stats["by_task_type"].items():
                desc = task_descriptions.get(task_type, "AI assistance")
                declaration += f"| {task_type.replace('_', ' ').title()} | {data['count']} | {data['words']:,} | {desc} |\n"

        # Add chapter breakdown
        if stats["by_chapter"]:
            declaration += "\n### Usage by Chapter\n\n"
            declaration += "| Chapter | Operations | Words | Avg. AI Contribution |\n"
            declaration += "|---------|------------|-------|---------------------|\n"

            for chapter, data in sorted(stats["by_chapter"].items()):
                declaration += f"| {chapter} | {data['count']} | {data['words']:,} | {data['avg_contribution']:.1f}% |\n"

        declaration += f"""

---

## Nature of AI Contribution

### What AI Did:

1. **Draft Assistance**: Generated initial paragraph drafts based on outlined arguments, which were subsequently reviewed, edited, and validated by the author.

2. **Style Consistency**: Analyzed writing samples to create a "linguistic DNA" profile, ensuring AI suggestions matched the author's established voice.

3. **Revision Support**: Provided revision suggestions in response to supervisor feedback, which were critically evaluated before acceptance.

4. **Citation Formatting**: Assisted with Harvard citation formatting per Oxford Brookes "Cite Them Right" guidelines.

5. **Readability Analysis**: Monitored Flesch-Kincaid Grade Level to maintain doctoral-level complexity (14-16).

### What AI Did NOT Do:

- Generate research questions or hypotheses
- Conduct primary research or data collection
- Make theoretical or methodological decisions
- Draw conclusions from research findings
- Determine the structure or argument of the thesis
- Write without subsequent human review and editing

---

## Academic Integrity Statement

I hereby declare that:

1. All AI-generated content was critically reviewed, edited, and validated before inclusion.
2. The intellectual contribution, theoretical framework, and original arguments are entirely my own.
3. AI was used as a tool to enhance productivity, not to substitute for scholarly thinking.
4. This declaration accurately represents all AI usage during thesis preparation.
5. I understand and have complied with Oxford Brookes University's Academic Integrity Policy.

---

## Signatures

**Author**: _________________________________ Date: _____________

**Supervisor**: _________________________________ Date: _____________

---

*This declaration was generated by PHDx Transparency Module v1.0*
*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

        return declaration

    def export_declaration_pdf(self, final_word_count: int = 50000) -> bytes:
        """
        Export the Brookes AI Declaration as a PDF.

        Requires: fpdf2 library (pip install fpdf2)

        Returns:
            PDF file as bytes
        """
        try:
            from fpdf import FPDF

            self.generate_brookes_declaration(
                final_word_count
            )  # Generate but not used in PDF
            stats = self.get_summary_stats()
            meta = self.metadata

            # Create PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Title
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(
                0,
                15,
                "Declaration of AI Usage in Academic Research",
                ln=True,
                align="C",
            )

            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, "Oxford Brookes University", ln=True, align="C")

            pdf.set_font("Helvetica", "I", 12)
            pdf.cell(0, 8, "PhD Thesis AI Transparency Statement", ln=True, align="C")

            pdf.ln(10)

            # Thesis Information
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Thesis Information", ln=True)
            pdf.set_draw_color(0, 113, 206)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_font("Helvetica", "", 10)
            info_items = [
                ("Thesis Title", meta.get("thesis_title", "[Not specified]")),
                ("Author", meta.get("author_name", "[Not specified]")),
                ("Student ID", meta.get("student_id", "[Not specified]")),
                ("Supervisor", meta.get("supervisor", "[Not specified]")),
                ("Final Word Count", f"{final_word_count:,}"),
                ("Declaration Date", datetime.now().strftime("%d %B %Y")),
            ]

            for label, value in info_items:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(50, 6, f"{label}:", ln=False)
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, str(value), ln=True)

            pdf.ln(10)

            # AI Usage Overview
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "AI Usage Overview", ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            total_ai_words = stats["total_ai_words"]
            ai_percentage = (
                (total_ai_words / final_word_count * 100) if final_word_count > 0 else 0
            )

            pdf.set_font("Helvetica", "", 10)
            overview_items = [
                ("Total AI-Assisted Operations", str(stats["total_entries"])),
                ("AI-Assisted Word Count", f"{total_ai_words:,} words"),
                ("Percentage of Final Thesis", f"{ai_percentage:.1f}%"),
                (
                    "Average AI Contribution per Task",
                    f"{stats['avg_contribution']:.1f}%",
                ),
            ]

            for label, value in overview_items:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(70, 6, f"{label}:", ln=False)
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 6, value, ln=True)

            pdf.ln(10)

            # Usage by Task Type
            if stats["by_task_type"]:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(0, 8, "Usage by Task Type", ln=True)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(5)

                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(60, 6, "Task Type", border=1)
                pdf.cell(30, 6, "Operations", border=1, align="C")
                pdf.cell(40, 6, "Words", border=1, align="C")
                pdf.ln()

                pdf.set_font("Helvetica", "", 9)
                for task_type, data in stats["by_task_type"].items():
                    pdf.cell(60, 6, task_type.replace("_", " ").title(), border=1)
                    pdf.cell(30, 6, str(data["count"]), border=1, align="C")
                    pdf.cell(40, 6, f"{data['words']:,}", border=1, align="C")
                    pdf.ln()

            pdf.ln(10)

            # Academic Integrity Statement
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Academic Integrity Statement", ln=True)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_font("Helvetica", "", 10)
            statement = (
                "I hereby declare that all AI-generated content was critically reviewed, "
                "edited, and validated before inclusion. The intellectual contribution, "
                "theoretical framework, and original arguments are entirely my own. "
                "AI was used as a tool to enhance productivity, not to substitute for "
                "scholarly thinking."
            )
            pdf.multi_cell(0, 5, statement)

            pdf.ln(15)

            # Signatures
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(
                0,
                8,
                "Author Signature: ___________________________ Date: ___________",
                ln=True,
            )
            pdf.ln(5)
            pdf.cell(
                0,
                8,
                "Supervisor Signature: ________________________ Date: ___________",
                ln=True,
            )

            pdf.ln(15)
            pdf.set_font("Helvetica", "I", 8)
            pdf.cell(
                0,
                5,
                f"Generated by PHDx Transparency Module - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ln=True,
                align="C",
            )

            return pdf.output()

        except ImportError:
            # Fallback: return markdown as text
            return self.generate_brookes_declaration(final_word_count).encode("utf-8")


# =============================================================================
# STREAMLIT UI COMPONENTS
# =============================================================================


def render_transparency_widget(log: TransparencyLog):
    """Render transparency summary widget for sidebar."""
    import streamlit as st

    st.markdown("### 📜 AI Transparency")

    stats = log.get_summary_stats()

    if stats["total_entries"] == 0:
        st.info("No AI operations logged yet")
        return

    col1, col2 = st.columns(2)
    with col1:
        st.metric("AI Operations", stats["total_entries"])
    with col2:
        st.metric("Avg Contribution", f"{stats['avg_contribution']:.0f}%")


def render_declaration_export(log: TransparencyLog):
    """Render the declaration export section for Progress tab."""
    import streamlit as st

    st.markdown("### 📜 AI Transparency Declaration")
    st.markdown("*Export your AI usage declaration for Oxford Brookes submission*")

    # Metadata form
    with st.expander("Thesis Metadata", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(
                "Thesis Title",
                value=log.metadata.get("thesis_title", ""),
                key="meta_title",
            )
            author = st.text_input(
                "Author Name",
                value=log.metadata.get("author_name", ""),
                key="meta_author",
            )

        with col2:
            student_id = st.text_input(
                "Student ID", value=log.metadata.get("student_id", ""), key="meta_id"
            )
            supervisor = st.text_input(
                "Supervisor",
                value=log.metadata.get("supervisor", ""),
                key="meta_supervisor",
            )

        if st.button("Save Metadata"):
            log.update_metadata(
                thesis_title=title,
                author_name=author,
                student_id=student_id,
                supervisor=supervisor,
            )
            st.success("Metadata saved!")

    # Usage summary
    stats = log.get_summary_stats()

    st.markdown("#### Usage Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
        <div style="text-align: center; padding: 0.5rem; background: rgba(0, 113, 206, 0.15);
                    border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #0071ce;">
                {stats["total_entries"]}
            </div>
            <div style="font-size: 0.75rem; color: rgba(224, 224, 224, 0.7);">Operations</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div style="text-align: center; padding: 0.5rem; background: rgba(76, 175, 80, 0.15);
                    border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #4caf50;">
                {stats["total_ai_words"]:,}
            </div>
            <div style="font-size: 0.75rem; color: rgba(224, 224, 224, 0.7);">AI Words</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div style="text-align: center; padding: 0.5rem; background: rgba(255, 193, 7, 0.15);
                    border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #ffc107;">
                {stats["avg_contribution"]:.0f}%
            </div>
            <div style="font-size: 0.75rem; color: rgba(224, 224, 224, 0.7);">Avg Contribution</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        task_count = len(stats.get("by_task_type", {}))
        st.markdown(
            f"""
        <div style="text-align: center; padding: 0.5rem; background: rgba(156, 39, 176, 0.15);
                    border-radius: 8px;">
            <div style="font-size: 1.5rem; font-weight: bold; color: #9c27b0;">
                {task_count}
            </div>
            <div style="font-size: 0.75rem; color: rgba(224, 224, 224, 0.7);">Task Types</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Export section
    st.markdown("#### Export Declaration")

    final_words = st.number_input(
        "Final Thesis Word Count",
        min_value=1000,
        max_value=200000,
        value=50000,
        step=1000,
        help="Enter your final thesis word count for percentage calculations",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📄 Export Brookes AI Declaration", type="primary", use_container_width=True
        ):
            try:
                pdf_bytes = log.export_declaration_pdf(final_words)

                # Save to file
                AI_DECLARATION_DIR.mkdir(parents=True, exist_ok=True)
                filename = (
                    f"ai_declaration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                )
                filepath = AI_DECLARATION_DIR / filename

                with open(filepath, "wb") as f:
                    f.write(pdf_bytes)

                st.success(f"Declaration saved to: {filepath}")

                # Download button
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                )

            except Exception as e:
                st.error(f"Error generating PDF: {e}")
                st.info("Falling back to Markdown export...")

                md_text = log.generate_brookes_declaration(final_words)
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=md_text,
                    file_name="ai_declaration.md",
                    mime="text/markdown",
                )

    with col2:
        if st.button("📊 Export CSV Log", use_container_width=True):
            csv_data = log.export_to_csv()
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"ai_usage_log_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    with col3:
        if st.button("👁️ Preview Declaration", use_container_width=True):
            with st.expander("Declaration Preview", expanded=True):
                md_text = log.generate_brookes_declaration(final_words)
                st.markdown(md_text)


# =============================================================================
# CLI
# =============================================================================


def main():
    """CLI for testing transparency module."""
    print("=" * 60)
    print("PHDx Transparency Module")
    print("=" * 60)

    log = TransparencyLog()

    # Add sample entries for testing
    if not log.entries:
        print("\nAdding sample entries for demonstration...")

        log.log_draft_generation(
            input_text="Write about the theoretical framework for digital sovereignty",
            output_text="The theoretical framework underpinning this research draws upon multiple disciplinary perspectives. "
            * 10,
            chapter="Chapter 2",
            section="2.3 Theoretical Framework",
        )

        log.log_feedback_suggestion(
            feedback_text="The transition between sections is abrupt",
            suggested_revision="Furthermore, having established the conceptual foundations, it becomes necessary to consider...",
            accepted=True,
            chapter="Chapter 2",
        )

        log.log_style_check(
            text="This research examines the various aspects of governance." * 5,
            suggestions="Consider using more hedging language",
            chapter="Chapter 1",
        )

    # Show stats
    stats = log.get_summary_stats()
    print("\nTransparency Log Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Total AI words: {stats['total_ai_words']}")
    print(f"  Average contribution: {stats['avg_contribution']:.1f}%")

    if stats["by_task_type"]:
        print("\n  By task type:")
        for task, data in stats["by_task_type"].items():
            print(f"    - {task}: {data['count']} ops, {data['words']} words")

    # Generate declaration
    print("\nGenerating Brookes AI Declaration...")
    declaration = log.generate_brookes_declaration(50000)
    print(declaration[:1000] + "...")
    print(f"\n[Full declaration: {len(declaration)} characters]")


if __name__ == "__main__":
    main()
