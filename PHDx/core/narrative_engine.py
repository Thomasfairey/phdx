"""
Narrative Engine - Thesis Structure and Argument Intelligence for PHDx

High-level thesis analysis providing:
- Thesis structure analysis and suggestions
- Argument mapping and visualization
- Gap analysis (missing evidence, weak links)
- Thematic coherence checking
- Literature synthesis assistance

Helps ensure the thesis tells a coherent story from introduction to conclusion.
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

# Local imports
from core.ethics_utils import log_ai_usage

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
NARRATIVE_CACHE = DATA_DIR / "narrative_cache"
NARRATIVE_CACHE.mkdir(parents=True, exist_ok=True)


# =============================================================================
# THESIS STRUCTURE TEMPLATES
# =============================================================================

THESIS_STRUCTURES = {
    "empirical": {
        "name": "Empirical Research Thesis",
        "description": "Standard structure for empirical/data-driven research",
        "chapters": [
            {"order": 1, "name": "Introduction", "target_pct": 8},
            {"order": 2, "name": "Literature Review", "target_pct": 20},
            {"order": 3, "name": "Methodology", "target_pct": 15},
            {"order": 4, "name": "Findings", "target_pct": 25},
            {"order": 5, "name": "Discussion", "target_pct": 20},
            {"order": 6, "name": "Conclusion", "target_pct": 7},
            {"order": 7, "name": "References", "target_pct": 5},
        ],
        "recommended_for": ["quantitative", "mixed methods", "case study"],
    },
    "theoretical": {
        "name": "Theoretical/Conceptual Thesis",
        "description": "Structure for theory-building or conceptual research",
        "chapters": [
            {"order": 1, "name": "Introduction", "target_pct": 10},
            {"order": 2, "name": "Theoretical Background", "target_pct": 25},
            {"order": 3, "name": "Conceptual Framework Development", "target_pct": 25},
            {"order": 4, "name": "Application/Analysis", "target_pct": 20},
            {"order": 5, "name": "Discussion & Implications", "target_pct": 12},
            {"order": 6, "name": "Conclusion", "target_pct": 8},
        ],
        "recommended_for": ["philosophical", "conceptual", "theoretical"],
    },
    "papers_based": {
        "name": "Papers-Based Thesis",
        "description": "Collection of published/publishable papers with framing chapters",
        "chapters": [
            {"order": 1, "name": "Introduction & Overview", "target_pct": 15},
            {"order": 2, "name": "Paper 1", "target_pct": 20},
            {"order": 3, "name": "Paper 2", "target_pct": 20},
            {"order": 4, "name": "Paper 3", "target_pct": 20},
            {"order": 5, "name": "Synthesis & Discussion", "target_pct": 15},
            {"order": 6, "name": "Conclusion", "target_pct": 10},
        ],
        "recommended_for": ["publication-track", "article-based"],
    },
    "practice_based": {
        "name": "Practice-Based Research Thesis",
        "description": "For research involving creative practice or professional context",
        "chapters": [
            {"order": 1, "name": "Introduction", "target_pct": 10},
            {"order": 2, "name": "Contextual Review", "target_pct": 15},
            {"order": 3, "name": "Methodology & Methods", "target_pct": 15},
            {"order": 4, "name": "Practice Documentation", "target_pct": 25},
            {"order": 5, "name": "Critical Reflection", "target_pct": 20},
            {"order": 6, "name": "Conclusion", "target_pct": 10},
            {"order": 7, "name": "Portfolio/Appendices", "target_pct": 5},
        ],
        "recommended_for": ["creative", "professional doctorate", "action research"],
    },
}


class NarrativeEngine:
    """
    Narrative Intelligence for thesis structure and argument coherence.

    Provides chapter suggestions, gap analysis, and thematic checking
    to ensure the thesis tells a coherent story.
    """

    def __init__(self):
        """Initialize the Narrative Engine."""
        self._llm_gateway = None
        self._vector_store = None

        self._init_integrations()

    def _init_integrations(self):
        """Initialize optional integrations."""
        try:
            from core import llm_gateway

            self._llm_gateway = llm_gateway
        except ImportError:
            pass

        try:
            from core.vector_store import get_vector_store

            self._vector_store = get_vector_store("thesis_narrative")
        except ImportError:
            pass

    # =========================================================================
    # STRUCTURE ANALYSIS
    # =========================================================================

    def suggest_thesis_structure(
        self,
        thesis_type: str = "empirical",
        field: str = "",
        research_approach: str = "",
    ) -> dict:
        """
        Suggest an appropriate thesis structure.

        Args:
            thesis_type: Type of thesis (empirical, theoretical, papers_based, practice_based)
            field: Academic field/discipline
            research_approach: Research methodology approach

        Returns:
            dict with recommended structure
        """
        structure = THESIS_STRUCTURES.get(thesis_type.lower())

        if not structure:
            # Try to match based on research approach
            for struct_type, struct in THESIS_STRUCTURES.items():
                if research_approach.lower() in [
                    r.lower() for r in struct.get("recommended_for", [])
                ]:
                    structure = struct
                    thesis_type = struct_type
                    break

        if not structure:
            structure = THESIS_STRUCTURES["empirical"]
            thesis_type = "empirical"

        return {
            "status": "success",
            "recommended_type": thesis_type,
            "structure": structure,
            "field": field,
            "research_approach": research_approach,
            "total_chapters": len(structure["chapters"]),
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_thesis_structure(self, chapters: list[dict]) -> dict:
        """
        Analyze the current thesis structure.

        Args:
            chapters: List of chapter dicts with name, word_count, status

        Returns:
            dict with structural analysis
        """
        if not chapters:
            return {"status": "error", "error": "No chapters provided"}

        total_words = sum(c.get("word_count", 0) for c in chapters)

        analysis = {
            "report_id": hashlib.md5(
                f"{len(chapters)}_{total_words}".encode(), usedforsecurity=False
            ).hexdigest()[:12],
            "timestamp": datetime.now().isoformat(),
            "total_chapters": len(chapters),
            "total_words": total_words,
            "chapters": [],
            "balance_assessment": {},
            "recommendations": [],
        }

        # Analyze each chapter
        for chapter in chapters:
            name = chapter.get("name", "Unknown")
            word_count = chapter.get("word_count", 0)
            percentage = (word_count / total_words * 100) if total_words > 0 else 0

            chapter_analysis = {
                "name": name,
                "word_count": word_count,
                "percentage": round(percentage, 1),
                "status": chapter.get("status", "unknown"),
            }

            # Check against typical percentages
            typical = self._get_typical_percentage(name)
            if typical:
                deviation = percentage - typical
                chapter_analysis["typical_percentage"] = typical
                chapter_analysis["deviation"] = round(deviation, 1)

                if abs(deviation) > 5:
                    if deviation > 0:
                        analysis["recommendations"].append(
                            f"{name} may be too long ({percentage:.1f}% vs typical {typical}%)"
                        )
                    else:
                        analysis["recommendations"].append(
                            f"{name} may be too short ({percentage:.1f}% vs typical {typical}%)"
                        )

            analysis["chapters"].append(chapter_analysis)

        # Overall balance assessment
        if total_words < 60000:
            analysis["balance_assessment"]["overall"] = "below_typical"
            analysis["recommendations"].append(
                f"Total word count ({total_words:,}) is below typical PhD thesis (80,000-100,000)"
            )
        elif total_words > 100000:
            analysis["balance_assessment"]["overall"] = "above_typical"
            analysis["recommendations"].append(
                f"Total word count ({total_words:,}) exceeds typical maximum (100,000)"
            )
        else:
            analysis["balance_assessment"]["overall"] = "within_range"

        analysis["status"] = "success"
        return analysis

    def _get_typical_percentage(self, chapter_name: str) -> Optional[float]:
        """Get typical percentage for a chapter type."""
        typical = {
            "introduction": 8,
            "literature review": 20,
            "literature": 20,
            "methodology": 15,
            "methods": 15,
            "findings": 25,
            "results": 25,
            "discussion": 20,
            "conclusion": 7,
            "conclusions": 7,
        }

        for key, pct in typical.items():
            if key in chapter_name.lower():
                return pct
        return None

    def evaluate_chapter_balance(self, chapter_word_counts: dict) -> dict:
        """
        Evaluate balance between chapters.

        Args:
            chapter_word_counts: Dict of chapter_name: word_count

        Returns:
            dict with balance evaluation
        """
        chapters = [
            {"name": name, "word_count": count}
            for name, count in chapter_word_counts.items()
        ]
        return self.analyze_thesis_structure(chapters)

    # =========================================================================
    # ARGUMENT MAPPING
    # =========================================================================

    def map_arguments(self, thesis_text: str) -> dict:
        """
        Create an argument map from thesis text.

        Args:
            thesis_text: Full thesis text or substantial excerpt

        Returns:
            dict with argument structure (claims, evidence, conclusions)
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        prompt = f"""Analyze this thesis text and map its argument structure.

THESIS TEXT:
{thesis_text[:8000]}

Create an argument map identifying:
1. MAIN THESIS/CLAIM: The central argument
2. SUPPORTING ARGUMENTS: Key sub-arguments that support the main thesis
3. EVIDENCE: Types of evidence used (empirical, theoretical, case-based)
4. LOGICAL FLOW: How arguments connect to each other
5. CONCLUSIONS: Key conclusions drawn

Return a JSON object with:
- "main_thesis": string
- "supporting_arguments": array of {{"argument": string, "evidence_type": string}}
- "argument_flow": array of {{"from": string, "to": string, "relationship": string}}
- "conclusions": array of strings
- "strength_assessment": string (strong/moderate/weak with brief explanation)
"""

        try:
            log_ai_usage(
                action_type="argument_mapping",
                data_source="narrative_engine",
                prompt=prompt[:200],
                was_scrubbed=False,
            )

            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="complex_reasoning"
            )

            content = result.get("content", "{}")
            try:
                # Clean markdown if present
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                argument_map = json.loads(content)
            except json.JSONDecodeError:
                argument_map = {"raw_analysis": content}

            return {
                "status": "success",
                "argument_map": argument_map,
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def visualize_argument_flow(self, argument_map: dict) -> dict:
        """
        Generate a visualization specification for the argument flow.

        Args:
            argument_map: Argument map from map_arguments()

        Returns:
            dict with Mermaid diagram specification
        """
        if not argument_map or "argument_map" not in argument_map:
            return {"status": "error", "error": "Invalid argument map"}

        am = argument_map.get("argument_map", {})

        # Build Mermaid flowchart
        mermaid = ["flowchart TD"]

        # Main thesis
        main_thesis = am.get("main_thesis", "Main Thesis")
        mermaid.append(f'    MT["{main_thesis[:50]}..."]')

        # Supporting arguments
        supporting = am.get("supporting_arguments", [])
        for i, arg in enumerate(supporting):
            arg_text = arg.get("argument", f"Argument {i + 1}")[:40]
            mermaid.append(f'    SA{i}["{arg_text}..."]')
            mermaid.append(f"    SA{i} --> MT")

        # Conclusions
        conclusions = am.get("conclusions", [])
        for i, conc in enumerate(conclusions):
            conc_text = conc[:40] if isinstance(conc, str) else str(conc)[:40]
            mermaid.append(f'    C{i}["{conc_text}..."]')
            mermaid.append(f"    MT --> C{i}")

        return {
            "status": "success",
            "mermaid_code": "\n".join(mermaid),
            "format": "mermaid",
            "timestamp": datetime.now().isoformat(),
        }

    # =========================================================================
    # GAP ANALYSIS
    # =========================================================================

    def identify_argument_gaps(self, argument_map: dict) -> dict:
        """
        Identify gaps in the argument structure.

        Args:
            argument_map: Argument map from map_arguments()

        Returns:
            dict with identified gaps
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        am_str = json.dumps(argument_map, indent=2)

        prompt = f"""Analyze this argument map for gaps and weaknesses.

ARGUMENT MAP:
{am_str[:4000]}

Identify:
1. LOGICAL GAPS: Missing steps in reasoning
2. EVIDENCE GAPS: Claims without sufficient support
3. CONNECTION GAPS: Arguments that don't clearly link
4. COUNTERARGUMENT GAPS: Unaddressed objections
5. SYNTHESIS GAPS: Missing integration of ideas

For each gap, provide:
- Type of gap
- Location/affected argument
- Severity (critical/moderate/minor)
- Suggestion for addressing it

Return a JSON object with "gaps" array."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="audit"
            )

            content = result.get("content", "{}")
            try:
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                gaps = json.loads(content)
            except json.JSONDecodeError:
                gaps = {"raw_analysis": content}

            return {
                "status": "success",
                "gap_analysis": gaps,
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def identify_missing_connections(self, chapters: list[dict]) -> dict:
        """
        Identify missing connections between chapters.

        Args:
            chapters: List of chapter dicts with name and summary/content

        Returns:
            dict with connection analysis
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        chapters_summary = "\n\n".join(
            [
                f"CHAPTER {i + 1}: {c.get('name', 'Unknown')}\n{c.get('summary', c.get('content', ''))[:500]}..."
                for i, c in enumerate(chapters)
            ]
        )

        prompt = f"""Analyze these thesis chapters for narrative connections.

{chapters_summary}

Identify:
1. STRONG CONNECTIONS: Well-linked chapters
2. WEAK CONNECTIONS: Chapters that need better linking
3. MISSING BRIDGES: Transitions that should exist
4. REDUNDANCIES: Overlapping content
5. SUGGESTED BRIDGES: Specific text/concepts to add

Return a JSON object with "connections" analysis."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="complex_reasoning"
            )

            content = result.get("content", "{}")
            try:
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                connections = json.loads(content)
            except json.JSONDecodeError:
                connections = {"raw_analysis": content}

            return {
                "status": "success",
                "connection_analysis": connections,
                "chapters_analyzed": len(chapters),
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # THEMATIC COHERENCE
    # =========================================================================

    def extract_themes(self, thesis_text: str, n_themes: int = 5) -> dict:
        """
        Extract main themes from thesis text.

        Args:
            thesis_text: Thesis text to analyze
            n_themes: Number of themes to extract

        Returns:
            dict with extracted themes
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        prompt = f"""Extract the {n_themes} main themes from this thesis text.

THESIS TEXT:
{thesis_text[:6000]}

For each theme, provide:
- Theme name (2-4 words)
- Description (1-2 sentences)
- Key terms associated with the theme
- Chapters/sections where it appears most

Return a JSON object with "themes" array."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="complex_reasoning"
            )

            content = result.get("content", "{}")
            try:
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                themes = json.loads(content)
            except json.JSONDecodeError:
                themes = {"raw_analysis": content}

            return {
                "status": "success",
                "themes": themes,
                "n_themes_requested": n_themes,
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def check_thematic_consistency(self, chapters: list[dict]) -> dict:
        """
        Check thematic consistency across chapters.

        Args:
            chapters: List of chapter dicts with name and content/summary

        Returns:
            dict with thematic consistency analysis
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        chapters_text = "\n\n---\n\n".join(
            [
                f"CHAPTER: {c.get('name', 'Unknown')}\n{c.get('content', c.get('summary', ''))[:1000]}"
                for c in chapters
            ]
        )

        prompt = f"""Analyze thematic consistency across these thesis chapters.

{chapters_text}

Evaluate:
1. CONSISTENT THEMES: Themes that appear coherently throughout
2. INCONSISTENT THEMES: Themes that appear but aren't well integrated
3. DROPPED THEMES: Themes introduced but not followed through
4. EMERGENT THEMES: Themes that appear later without introduction
5. OVERALL COHERENCE SCORE: 0-100

Return a JSON object with the analysis."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="audit"
            )

            content = result.get("content", "{}")
            try:
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                consistency = json.loads(content)
            except json.JSONDecodeError:
                consistency = {"raw_analysis": content}

            return {
                "status": "success",
                "thematic_consistency": consistency,
                "chapters_analyzed": len(chapters),
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def trace_theme_development(self, theme: str, chapters: list[dict]) -> dict:
        """
        Trace how a specific theme develops across chapters.

        Args:
            theme: Theme to trace
            chapters: List of chapter dicts

        Returns:
            dict with theme development analysis
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        chapters_text = "\n\n".join(
            [
                f"CHAPTER {i + 1} ({c.get('name', 'Unknown')}):\n{c.get('content', c.get('summary', ''))[:800]}"
                for i, c in enumerate(chapters)
            ]
        )

        prompt = f"""Trace the development of the theme "{theme}" across these chapters.

{chapters_text}

For each chapter, identify:
- How the theme is introduced/developed
- Key concepts related to the theme
- How it connects to the previous chapter's treatment
- Strength of theme presence (strong/moderate/weak/absent)

Return a JSON object with "theme_trace" array (one entry per chapter)."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="complex_reasoning"
            )

            content = result.get("content", "{}")
            try:
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                trace = json.loads(content)
            except json.JSONDecodeError:
                trace = {"raw_analysis": content}

            return {
                "status": "success",
                "theme": theme,
                "development_trace": trace,
                "chapters_analyzed": len(chapters),
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # LITERATURE SYNTHESIS
    # =========================================================================

    def suggest_synthesis_points(self, papers: list[dict], topic: str) -> dict:
        """
        Suggest synthesis points for literature review.

        Args:
            papers: List of paper dicts with title, authors, abstract
            topic: Topic to synthesize around

        Returns:
            dict with synthesis suggestions
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        papers_summary = "\n\n".join(
            [
                f"PAPER: {p.get('title', 'Unknown')}\nAuthors: {p.get('authors', 'Unknown')}\nAbstract: {p.get('abstract', '')[:300]}..."
                for p in papers[:10]  # Limit to 10 papers
            ]
        )

        prompt = f"""Suggest synthesis points for these papers on the topic: "{topic}"

{papers_summary}

Identify:
1. COMMON THEMES: Themes that multiple papers address
2. POINTS OF AGREEMENT: Where authors agree
3. POINTS OF DISAGREEMENT: Where authors disagree or contradict
4. GAPS IN LITERATURE: What's missing from these papers collectively
5. SYNTHESIS OPPORTUNITIES: How to bring these together meaningfully

Return a JSON object with the analysis."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="literature_synthesis"
            )

            content = result.get("content", "{}")
            try:
                if "```" in content:
                    content = re.sub(r"```json\s*", "", content)
                    content = re.sub(r"```\s*", "", content)
                synthesis = json.loads(content)
            except json.JSONDecodeError:
                synthesis = {"raw_analysis": content}

            return {
                "status": "success",
                "synthesis_points": synthesis,
                "topic": topic,
                "papers_analyzed": len(papers),
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_synthesis_paragraph(self, papers: list[dict], focus: str) -> dict:
        """
        Generate a synthesis paragraph from multiple papers.

        Args:
            papers: List of paper dicts
            focus: Specific focus for the synthesis

        Returns:
            dict with synthesized paragraph
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        papers_info = "\n".join(
            [
                f"- {p.get('authors', 'Unknown')} ({p.get('year', 'n.d.')}): {p.get('title', 'Unknown')}"
                for p in papers
            ]
        )

        prompt = f"""Write a synthesis paragraph that brings together these sources on the topic: "{focus}"

SOURCES:
{papers_info}

Write a well-crafted academic paragraph that:
- Synthesizes (not summarizes) the sources
- Shows how they relate to each other
- Uses appropriate hedging language
- Includes inline citations in (Author, Year) format
- Is suitable for a PhD thesis literature review

SYNTHESIS PARAGRAPH:"""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="drafting"
            )

            return {
                "status": "success",
                "synthesis_paragraph": result.get("content", ""),
                "focus": focus,
                "sources_used": len(papers),
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_available_structures(self) -> dict:
        """Get all available thesis structures."""
        return {
            "status": "success",
            "structures": THESIS_STRUCTURES,
            "structure_types": list(THESIS_STRUCTURES.keys()),
        }

    def get_status(self) -> dict:
        """Get engine status."""
        return {
            "llm_available": self._llm_gateway is not None,
            "vector_store_available": self._vector_store is not None,
            "available_structures": list(THESIS_STRUCTURES.keys()),
            "cache_directory": str(NARRATIVE_CACHE),
        }


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================


def analyze_structure(chapters: list) -> dict:
    """Standalone function to analyze thesis structure."""
    engine = NarrativeEngine()
    return engine.analyze_thesis_structure(chapters)


def map_thesis_arguments(text: str) -> dict:
    """Standalone function to map arguments."""
    engine = NarrativeEngine()
    return engine.map_arguments(text)


def check_thematic_coherence(chapters: list) -> dict:
    """Standalone function to check thematic coherence."""
    engine = NarrativeEngine()
    return engine.check_thematic_consistency(chapters)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Narrative Engine - Thesis Structure Intelligence")
    print("=" * 60)

    engine = NarrativeEngine()
    status = engine.get_status()

    print("\nEngine Status:")
    for key, value in status.items():
        print(f"  - {key}: {value}")

    print("\nAvailable Thesis Structures:")
    for name, struct in THESIS_STRUCTURES.items():
        print(f"  - {name}: {struct['name']}")
        print(f"    Chapters: {len(struct['chapters'])}")

    print("\n" + "=" * 60)
