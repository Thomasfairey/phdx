"""
Writing Desk - AI-Assisted Drafting Workspace for PHDx

Advanced writing workspace for thesis chapter drafting with:
- Chapter outline builder with templates
- AI-assisted drafting with DNA profile voice matching
- Real-time gap identification
- Counter-argument generation
- Inline citation suggestions
- Direct Google Docs sync

Integrates with DNA engine for voice consistency and Zotero for citations.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Local imports
from core.secrets_utils import get_secret
from core.ethics_utils import scrub_text, log_ai_usage

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
OUTLINES_DIR = DATA_DIR / "outlines"
OUTLINES_DIR.mkdir(parents=True, exist_ok=True)
DNA_PROFILE_PATH = DATA_DIR / "author_dna.json"


# =============================================================================
# CHAPTER TEMPLATES
# =============================================================================

CHAPTER_TEMPLATES = {
    "introduction": {
        "title": "Introduction",
        "description": "Sets the stage for your research",
        "sections": [
            {
                "title": "Research Context",
                "guidance": "Establish the broader context and significance of your research area",
                "target_words": 500
            },
            {
                "title": "Problem Statement",
                "guidance": "Clearly articulate the research problem or gap you are addressing",
                "target_words": 300
            },
            {
                "title": "Research Questions/Objectives",
                "guidance": "State your main research questions or objectives",
                "target_words": 200
            },
            {
                "title": "Contribution and Significance",
                "guidance": "Explain the expected contribution and significance of your research",
                "target_words": 300
            },
            {
                "title": "Thesis Structure",
                "guidance": "Provide an overview of how the thesis is organized",
                "target_words": 300
            }
        ],
        "target_words": 2000
    },
    "literature_review": {
        "title": "Literature Review",
        "description": "Critical analysis of existing research",
        "sections": [
            {
                "title": "Introduction to the Literature",
                "guidance": "Overview of the literature landscape and your review approach",
                "target_words": 400
            },
            {
                "title": "Theoretical Framework",
                "guidance": "Key theories and concepts underpinning your research",
                "target_words": 1500
            },
            {
                "title": "Thematic Analysis",
                "guidance": "Organized discussion of themes/topics in the literature",
                "target_words": 3000
            },
            {
                "title": "Research Gaps",
                "guidance": "Identify gaps, limitations, and areas for further research",
                "target_words": 500
            },
            {
                "title": "Chapter Summary",
                "guidance": "Synthesize key findings and link to your research",
                "target_words": 300
            }
        ],
        "target_words": 8000
    },
    "methodology": {
        "title": "Methodology",
        "description": "Research design and methods",
        "sections": [
            {
                "title": "Research Philosophy",
                "guidance": "Ontological and epistemological positioning",
                "target_words": 500
            },
            {
                "title": "Research Design",
                "guidance": "Overall approach (qualitative, quantitative, mixed methods)",
                "target_words": 600
            },
            {
                "title": "Data Collection",
                "guidance": "Methods, sampling, and procedures for gathering data",
                "target_words": 800
            },
            {
                "title": "Data Analysis",
                "guidance": "Analytical framework and techniques",
                "target_words": 600
            },
            {
                "title": "Ethical Considerations",
                "guidance": "Ethical approval, consent, data protection",
                "target_words": 400
            },
            {
                "title": "Limitations",
                "guidance": "Methodological limitations and mitigation strategies",
                "target_words": 300
            }
        ],
        "target_words": 4000
    },
    "findings": {
        "title": "Findings",
        "description": "Presentation of research results",
        "sections": [
            {
                "title": "Introduction",
                "guidance": "Overview of findings structure",
                "target_words": 200
            },
            {
                "title": "Theme/Finding 1",
                "guidance": "First major finding with supporting evidence",
                "target_words": 1500
            },
            {
                "title": "Theme/Finding 2",
                "guidance": "Second major finding with supporting evidence",
                "target_words": 1500
            },
            {
                "title": "Theme/Finding 3",
                "guidance": "Third major finding with supporting evidence",
                "target_words": 1500
            },
            {
                "title": "Summary of Findings",
                "guidance": "Synthesis of key findings",
                "target_words": 400
            }
        ],
        "target_words": 6000
    },
    "discussion": {
        "title": "Discussion",
        "description": "Interpretation and implications",
        "sections": [
            {
                "title": "Introduction",
                "guidance": "Recap of research aims and key findings",
                "target_words": 300
            },
            {
                "title": "Interpretation of Findings",
                "guidance": "What do the findings mean in context?",
                "target_words": 2000
            },
            {
                "title": "Relation to Existing Literature",
                "guidance": "How findings relate to previous research",
                "target_words": 1500
            },
            {
                "title": "Theoretical Implications",
                "guidance": "Contribution to theory development",
                "target_words": 800
            },
            {
                "title": "Practical Implications",
                "guidance": "Implications for practice and policy",
                "target_words": 800
            }
        ],
        "target_words": 6000
    },
    "conclusion": {
        "title": "Conclusion",
        "description": "Summary and future directions",
        "sections": [
            {
                "title": "Summary of the Research",
                "guidance": "Brief overview of what was done and found",
                "target_words": 400
            },
            {
                "title": "Key Contributions",
                "guidance": "Main contributions to knowledge",
                "target_words": 500
            },
            {
                "title": "Limitations",
                "guidance": "Acknowledgement of research limitations",
                "target_words": 300
            },
            {
                "title": "Recommendations for Future Research",
                "guidance": "Directions for future investigation",
                "target_words": 400
            },
            {
                "title": "Concluding Remarks",
                "guidance": "Final reflections",
                "target_words": 200
            }
        ],
        "target_words": 2000
    }
}


class WritingDesk:
    """
    Advanced writing workspace for thesis chapter drafting.

    Integrates DNA profile, red thread checking, and citation suggestions
    to provide comprehensive AI-assisted writing support.
    """

    def __init__(self):
        """Initialize the Writing Desk with integrations."""
        self._dna_profile = None
        self._llm_gateway = None
        self._zotero = None
        self._red_thread = None

        # Load DNA profile if available
        self._load_dna_profile()

        # Initialize integrations
        self._init_integrations()

    def _load_dna_profile(self):
        """Load author's DNA profile for voice matching."""
        if DNA_PROFILE_PATH.exists():
            try:
                with open(DNA_PROFILE_PATH, 'r') as f:
                    self._dna_profile = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._dna_profile = None

    def _init_integrations(self):
        """Initialize optional integrations."""
        # LLM Gateway
        try:
            from core import llm_gateway
            self._llm_gateway = llm_gateway
        except ImportError:
            pass

        # Zotero Sentinel
        try:
            from core.citations import ZoteroSentinel
            self._zotero = ZoteroSentinel()
        except ImportError:
            pass

        # Red Thread Engine
        try:
            from core.red_thread import RedThreadEngine
            self._red_thread = RedThreadEngine()
        except ImportError:
            pass

    # =========================================================================
    # OUTLINE MANAGEMENT
    # =========================================================================

    def get_chapter_template(self, chapter_type: str) -> dict:
        """
        Get a chapter template.

        Args:
            chapter_type: Type of chapter (introduction, literature_review, etc.)

        Returns:
            Template dict with sections and guidance
        """
        template = CHAPTER_TEMPLATES.get(chapter_type.lower())
        if template:
            return {
                "status": "success",
                "template": template,
                "chapter_type": chapter_type
            }
        return {
            "status": "error",
            "error": f"Unknown chapter type: {chapter_type}",
            "available_types": list(CHAPTER_TEMPLATES.keys())
        }

    def create_outline(
        self,
        chapter_type: str,
        thesis_topic: str,
        custom_sections: list = None
    ) -> dict:
        """
        Create a chapter outline based on template and topic.

        Args:
            chapter_type: Type of chapter
            thesis_topic: Overall thesis topic for context
            custom_sections: Optional list of custom section titles

        Returns:
            Outline dict with AI-generated section descriptions
        """
        template = CHAPTER_TEMPLATES.get(chapter_type.lower())
        if not template:
            return {
                "status": "error",
                "error": f"Unknown chapter type: {chapter_type}"
            }

        outline_id = hashlib.md5(
            f"{chapter_type}_{thesis_topic}_{datetime.now().isoformat()}".encode(),
            usedforsecurity=False
        ).hexdigest()[:12]

        outline = {
            "outline_id": outline_id,
            "chapter_type": chapter_type,
            "title": template["title"],
            "thesis_topic": thesis_topic,
            "created_at": datetime.now().isoformat(),
            "target_words": template["target_words"],
            "sections": []
        }

        # Use template sections or custom
        sections_to_use = custom_sections if custom_sections else [
            s["title"] for s in template["sections"]
        ]

        for i, section_title in enumerate(sections_to_use):
            # Find matching template section for guidance
            template_section = next(
                (s for s in template["sections"] if s["title"] == section_title),
                {"guidance": "Write content for this section", "target_words": 500}
            )

            outline["sections"].append({
                "order": i + 1,
                "title": section_title,
                "guidance": template_section.get("guidance", ""),
                "target_words": template_section.get("target_words", 500),
                "content": "",
                "word_count": 0,
                "status": "not_started"
            })

        # Save outline
        outline_path = OUTLINES_DIR / f"outline_{outline_id}.json"
        with open(outline_path, 'w') as f:
            json.dump(outline, f, indent=2)

        return {
            "status": "success",
            "outline": outline,
            "saved_to": str(outline_path)
        }

    def expand_section(
        self,
        section_title: str,
        section_guidance: str,
        thesis_context: str,
        existing_content: str = ""
    ) -> dict:
        """
        Expand an outline section into a draft paragraph.

        Args:
            section_title: Title of the section
            section_guidance: Guidance for what to include
            thesis_context: Overall thesis context
            existing_content: Any existing content to expand from

        Returns:
            dict with expanded content
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        # Build prompt with DNA profile context
        dna_context = ""
        if self._dna_profile:
            dna_context = self._format_dna_for_prompt()

        prompt = f"""You are a PhD thesis writing assistant. Expand the following section into academic prose.

THESIS CONTEXT: {thesis_context}

SECTION: {section_title}
GUIDANCE: {section_guidance}

{f"EXISTING CONTENT TO EXPAND: {existing_content}" if existing_content else ""}

{dna_context}

Write 2-3 paragraphs of thesis-ready academic prose for this section.
Use formal academic language with appropriate hedging.
Include placeholder citations where evidence would strengthen the argument (use format: [CITATION NEEDED]).
"""

        try:
            log_ai_usage(
                action_type="section_expansion",
                data_source="writing_desk",
                prompt=prompt[:200],
                was_scrubbed=False
            )

            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="drafting"
            )

            return {
                "status": "success",
                "content": result.get("content", ""),
                "section_title": section_title,
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # AI-ASSISTED DRAFTING
    # =========================================================================

    def generate_draft(
        self,
        prompt: str,
        section_context: dict = None,
        use_dna: bool = True
    ) -> dict:
        """
        Generate a draft with AI assistance and DNA voice matching.

        Args:
            prompt: Writing prompt or instruction
            section_context: Optional context (chapter, section, existing text)
            use_dna: Whether to apply DNA profile for voice matching

        Returns:
            dict with generated draft
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        # Build system prompt with DNA profile
        system_prompt = "You are a PhD thesis writing assistant. Write in formal academic prose."

        if use_dna and self._dna_profile:
            dna_instructions = self._format_dna_for_prompt()
            system_prompt += f"\n\n{dna_instructions}"

        # Add section context
        context_text = ""
        if section_context:
            context_text = f"""
Chapter: {section_context.get('chapter', 'Unknown')}
Section: {section_context.get('section', 'Unknown')}
Previous text: {section_context.get('existing_text', '')[:1000]}
"""

        try:
            log_ai_usage(
                action_type="draft_generation",
                data_source="writing_desk",
                prompt=prompt[:200],
                was_scrubbed=False
            )

            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="drafting",
                context_text=context_text,
                system_prompt=system_prompt
            )

            draft = result.get("content", "")

            # Check consistency if red thread available
            consistency_check = None
            if self._red_thread and len(draft) > 100:
                try:
                    consistency_check = self._red_thread.verify_consistency(draft)
                except Exception:
                    pass

            return {
                "status": "success",
                "draft": draft,
                "word_count": len(draft.split()),
                "model_used": result.get("model_used", "unknown"),
                "dna_applied": use_dna and self._dna_profile is not None,
                "consistency_check": consistency_check,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def continue_draft(
        self,
        existing_text: str,
        direction: str = "forward",
        target_words: int = 200
    ) -> dict:
        """
        Continue writing from existing text.

        Args:
            existing_text: Text to continue from
            direction: "forward" (continue) or "expand" (elaborate)
            target_words: Approximate words to generate

        Returns:
            dict with continuation
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        if direction == "forward":
            prompt = f"""Continue this academic text naturally for approximately {target_words} words.
Maintain the same voice, tone, and argument flow.

TEXT TO CONTINUE:
{existing_text[-2000:]}

CONTINUATION:"""
        else:  # expand
            prompt = f"""Expand and elaborate on this academic text, adding depth and detail.
Add approximately {target_words} words while maintaining coherence.

TEXT TO EXPAND:
{existing_text[-2000:]}

EXPANDED VERSION:"""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="drafting"
            )

            return {
                "status": "success",
                "continuation": result.get("content", ""),
                "direction": direction,
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def rewrite_section(
        self,
        text: str,
        instruction: str
    ) -> dict:
        """
        Rewrite a section based on specific instructions.

        Args:
            text: Text to rewrite
            instruction: Rewriting instruction (e.g., "make more formal", "simplify")

        Returns:
            dict with rewritten text
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        prompt = f"""Rewrite this academic text according to the instruction below.
Maintain the core meaning and arguments while implementing the requested changes.

INSTRUCTION: {instruction}

ORIGINAL TEXT:
{text}

REWRITTEN TEXT:"""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="rewrite"
            )

            return {
                "status": "success",
                "original": text,
                "rewritten": result.get("content", ""),
                "instruction": instruction,
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # VOICE CONSISTENCY
    # =========================================================================

    def _format_dna_for_prompt(self) -> str:
        """Format DNA profile as instructions for the LLM."""
        if not self._dna_profile:
            return ""

        instructions = ["AUTHOR VOICE PROFILE - Match these characteristics:"]

        # Sentence complexity
        if "sentence_complexity" in self._dna_profile:
            sc = self._dna_profile["sentence_complexity"]
            avg_len = sc.get("average_length", 20)
            instructions.append(f"- Average sentence length: {avg_len} words")

        # Hedging patterns
        if "hedging_analysis" in self._dna_profile:
            ha = self._dna_profile["hedging_analysis"]
            freq = ha.get("hedging_frequency", 0)
            if freq > 0.05:
                instructions.append("- Use frequent hedging language (suggests, may, potentially)")
            elif freq > 0.02:
                instructions.append("- Use moderate hedging language")

        # Transition vocabulary
        if "transition_vocabulary" in self._dna_profile:
            tv = self._dna_profile["transition_vocabulary"]
            common = tv.get("most_common", [])[:5]
            if common:
                instructions.append(f"- Preferred transitions: {', '.join(common)}")

        # Claude deep analysis insights
        if "claude_deep_analysis" in self._dna_profile:
            cda = self._dna_profile["claude_deep_analysis"]
            if "distinctive_features" in cda:
                features = cda["distinctive_features"][:3]
                instructions.append(f"- Distinctive features: {', '.join(features)}")

        return "\n".join(instructions)

    def check_voice_consistency(self, draft: str) -> dict:
        """
        Check if draft matches author's DNA profile.

        Args:
            draft: Draft text to check

        Returns:
            dict with consistency analysis
        """
        if not self._dna_profile:
            return {
                "status": "error",
                "error": "No DNA profile available. Run DNA analysis first."
            }

        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        dna_summary = json.dumps({
            k: v for k, v in self._dna_profile.items()
            if k in ["sentence_complexity", "hedging_analysis", "transition_vocabulary"]
        }, indent=2)

        prompt = f"""Analyze this draft for voice consistency with the author's profile.

AUTHOR DNA PROFILE:
{dna_summary}

DRAFT TO ANALYZE:
{draft[:3000]}

Provide a JSON response with:
1. "consistency_score": 0-100
2. "matching_features": list of features that match
3. "deviating_features": list of features that deviate
4. "recommendations": list of specific improvements

Respond with ONLY valid JSON."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="audit"
            )

            # Parse JSON response
            content = result.get("content", "{}")
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                analysis = {"raw_analysis": content}

            return {
                "status": "success",
                "analysis": analysis,
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def apply_dna_profile(self, draft: str) -> dict:
        """
        Transform draft to match author's voice profile.

        Args:
            draft: Draft text to transform

        Returns:
            dict with transformed text
        """
        if not self._dna_profile or not self._llm_gateway:
            return {"status": "error", "error": "DNA profile or LLM not available"}

        dna_instructions = self._format_dna_for_prompt()

        prompt = f"""Transform this draft to match the author's voice profile while preserving meaning.

{dna_instructions}

DRAFT TO TRANSFORM:
{draft}

TRANSFORMED TEXT (matching author's voice):"""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="rewrite"
            )

            return {
                "status": "success",
                "original": draft,
                "transformed": result.get("content", ""),
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # ARGUMENT DEVELOPMENT
    # =========================================================================

    def identify_gaps(
        self,
        draft: str,
        section_type: str = ""
    ) -> dict:
        """
        Identify gaps in the argument or narrative.

        Args:
            draft: Draft text to analyze
            section_type: Type of section for context

        Returns:
            dict with identified gaps and suggestions
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        prompt = f"""Analyze this PhD thesis draft for gaps and weaknesses.

{f"SECTION TYPE: {section_type}" if section_type else ""}

DRAFT:
{draft[:4000]}

Identify:
1. Missing evidence or support for claims
2. Logical gaps in the argument
3. Unsupported assertions
4. Areas needing more depth
5. Missing connections to theory/literature

For each gap, provide:
- Location (which part of the text)
- Type of gap
- Suggestion for addressing it

Respond with a JSON object containing "gaps" array."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="audit"
            )

            content = result.get("content", "{}")
            try:
                gaps = json.loads(content)
            except json.JSONDecodeError:
                gaps = {"raw_analysis": content}

            return {
                "status": "success",
                "gaps": gaps,
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_counterarguments(self, argument: str) -> dict:
        """
        Generate counterarguments for stronger academic writing.

        Args:
            argument: The argument to counter

        Returns:
            dict with counterarguments
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        prompt = f"""Generate counterarguments for this thesis argument.

ARGUMENT:
{argument}

Provide:
1. 3 potential counterarguments a critical reader might raise
2. For each counterargument, suggest a response/rebuttal
3. Consider theoretical, methodological, and empirical objections

Respond with a JSON object containing "counterarguments" array."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="complex_reasoning"
            )

            content = result.get("content", "{}")
            try:
                counters = json.loads(content)
            except json.JSONDecodeError:
                counters = {"raw_analysis": content}

            return {
                "status": "success",
                "counterarguments": counters,
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def strengthen_argument(self, paragraph: str) -> dict:
        """
        Suggest ways to strengthen an argument.

        Args:
            paragraph: Paragraph to strengthen

        Returns:
            dict with strengthening suggestions and rewrite
        """
        if not self._llm_gateway:
            return {"status": "error", "error": "LLM gateway not available"}

        prompt = f"""Analyze and strengthen this academic argument.

ORIGINAL PARAGRAPH:
{paragraph}

Provide:
1. Analysis of current argument strength
2. Specific suggestions for improvement
3. A strengthened rewrite of the paragraph

Respond with a JSON object containing "analysis", "suggestions", and "strengthened_text"."""

        try:
            result = self._llm_gateway.generate_content(
                prompt=prompt,
                task_type="complex_reasoning"
            )

            content = result.get("content", "{}")
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                analysis = {"strengthened_text": content}

            return {
                "status": "success",
                "original": paragraph,
                "analysis": analysis,
                "model_used": result.get("model_used", "unknown")
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # CITATION INTEGRATION
    # =========================================================================

    def suggest_citations_inline(self, paragraph: str, top_n: int = 3) -> dict:
        """
        Suggest citations for a paragraph from Zotero library.

        Args:
            paragraph: Paragraph needing citations
            top_n: Number of suggestions to return

        Returns:
            dict with citation suggestions
        """
        if not self._zotero:
            return {"status": "error", "error": "Zotero not available"}

        try:
            papers = self._zotero.get_relevant_papers(paragraph, top_n=top_n)

            suggestions = []
            for paper in papers:
                suggestions.append({
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", ""),
                    "year": paper.get("year", ""),
                    "inline_citation": self._zotero.format_inline_citation(paper),
                    "full_reference": self._zotero.format_as_brookes_harvard(paper),
                    "relevance_score": paper.get("relevance_score", 0),
                    "relevance_reason": paper.get("relevance_reason", "")
                })

            return {
                "status": "success",
                "suggestions": suggestions,
                "paragraph_preview": paragraph[:200] + "..."
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def get_writing_context(self) -> dict:
        """Get current writing context and status."""
        return {
            "dna_profile_loaded": self._dna_profile is not None,
            "llm_available": self._llm_gateway is not None,
            "zotero_available": self._zotero is not None,
            "red_thread_available": self._red_thread is not None,
            "available_templates": list(CHAPTER_TEMPLATES.keys()),
            "outlines_directory": str(OUTLINES_DIR)
        }

    def has_dna_profile(self) -> bool:
        """Check if DNA profile is available."""
        return self._dna_profile is not None


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================

def get_chapter_templates() -> dict:
    """Get all available chapter templates."""
    return CHAPTER_TEMPLATES


def create_chapter_outline(chapter_type: str, topic: str) -> dict:
    """Standalone function to create a chapter outline."""
    desk = WritingDesk()
    return desk.create_outline(chapter_type, topic)


def generate_section_draft(section: str, context: str) -> dict:
    """Standalone function to generate section draft."""
    desk = WritingDesk()
    return desk.expand_section(section, "Write content for this section", context)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Writing Desk - AI-Assisted Drafting")
    print("=" * 60)

    desk = WritingDesk()
    context = desk.get_writing_context()

    print("\nWriting Context:")
    for key, value in context.items():
        print(f"  - {key}: {value}")

    print("\nAvailable Chapter Templates:")
    for name, template in CHAPTER_TEMPLATES.items():
        print(f"  - {name}: {template['title']} (~{template['target_words']} words)")

    print("\n" + "=" * 60)
