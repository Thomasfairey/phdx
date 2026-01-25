"""
Writing Desk API Router.

Endpoints for AI-assisted thesis writing:
- Chapter outline generation
- Draft generation with streaming
- Gap analysis
- Counter-argument generation
- Citation suggestions
"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class OutlineRequest(BaseModel):
    """Request to generate a chapter outline."""
    chapter_type: str = Field(..., description="Type of chapter: introduction, literature_review, methodology, findings, discussion, conclusion")
    thesis_title: str = Field(..., min_length=10, max_length=500)
    research_questions: List[str] = Field(default_factory=list)
    key_themes: List[str] = Field(default_factory=list)


class OutlineSection(BaseModel):
    """A section in the outline."""
    title: str
    purpose: str
    target_words: int
    key_points: List[str] = []


class OutlineResponse(BaseModel):
    """Generated chapter outline."""
    success: bool
    chapter_title: str = ""
    chapter_type: str = ""
    target_words: int = 0
    sections: List[OutlineSection] = []
    error: Optional[str] = None


class DraftRequest(BaseModel):
    """Request to generate a draft."""
    prompt: str = Field(..., min_length=10, max_length=10000)
    section_type: str = Field(default="general")
    tone: str = Field(default="academic")
    target_words: int = Field(default=500, ge=100, le=5000)
    use_dna: bool = Field(default=True, description="Use DNA voice matching")
    existing_text: Optional[str] = None
    notes: Optional[str] = None


class DraftResponse(BaseModel):
    """Generated draft response."""
    success: bool
    draft: str = ""
    word_count: int = 0
    model_used: str = ""
    dna_applied: bool = False
    error: Optional[str] = None


class GapAnalysisRequest(BaseModel):
    """Request for gap analysis."""
    draft_text: str = Field(..., min_length=100, max_length=100000)
    chapter_type: str = Field(default="general")


class GapAnalysisResponse(BaseModel):
    """Gap analysis results."""
    success: bool
    missing_evidence: List[str] = []
    logical_gaps: List[str] = []
    unsupported_assertions: List[str] = []
    weak_connections: List[str] = []
    suggestions: List[str] = []
    priority_actions: List[str] = []
    error: Optional[str] = None


class CounterArgumentRequest(BaseModel):
    """Request for counter-arguments."""
    argument_text: str = Field(..., min_length=50, max_length=10000)


class CounterArgument(BaseModel):
    """A counter-argument."""
    argument: str
    strength: str = "medium"
    response_strategy: str = ""


class CounterArgumentResponse(BaseModel):
    """Counter-argument response."""
    success: bool
    counter_arguments: List[CounterArgument] = []
    error: Optional[str] = None


class CitationSuggestionRequest(BaseModel):
    """Request for citation suggestions."""
    context_text: str = Field(..., min_length=50, max_length=10000)
    num_suggestions: int = Field(default=5, ge=1, le=20)


class CitationSuggestion(BaseModel):
    """A citation suggestion."""
    title: str
    authors: str
    year: str
    relevance: str = ""
    inline_citation: str = ""


class CitationSuggestionResponse(BaseModel):
    """Citation suggestion response."""
    success: bool
    suggestions: List[CitationSuggestion] = []
    error: Optional[str] = None


class TemplateResponse(BaseModel):
    """Chapter template response."""
    chapter_type: str
    target_words: int
    sections: List[str]
    key_elements: List[str] = []


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/templates/{chapter_type}", response_model=TemplateResponse)
async def get_chapter_template(chapter_type: str):
    """Get template for a specific chapter type."""
    try:
        from core.writing_desk import CHAPTER_TEMPLATES

        template = CHAPTER_TEMPLATES.get(chapter_type)
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown chapter type: {chapter_type}. Valid types: {list(CHAPTER_TEMPLATES.keys())}"
            )

        return TemplateResponse(
            chapter_type=chapter_type,
            target_words=template.get("target_words", 0),
            sections=template.get("sections", []),
            key_elements=template.get("key_elements", [])
        )
    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")


@router.get("/templates")
async def list_templates():
    """List all available chapter templates."""
    try:
        from core.writing_desk import CHAPTER_TEMPLATES

        templates = []
        for name, template in CHAPTER_TEMPLATES.items():
            templates.append({
                "name": name,
                "display_name": name.replace("_", " ").title(),
                "target_words": template.get("target_words", 0),
                "section_count": len(template.get("sections", []))
            })

        return {"templates": templates}
    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")


@router.post("/outline/generate", response_model=OutlineResponse)
async def generate_outline(request: OutlineRequest):
    """Generate a chapter outline."""
    try:
        from core.writing_desk import WritingDesk

        desk = WritingDesk()
        result = desk.build_outline(
            chapter_type=request.chapter_type,
            thesis_context={
                "thesis_title": request.thesis_title,
                "research_questions": request.research_questions,
                "key_themes": request.key_themes
            }
        )

        if result.get("error"):
            return OutlineResponse(success=False, error=result["error"])

        sections = [
            OutlineSection(
                title=s.get("title", ""),
                purpose=s.get("purpose", ""),
                target_words=s.get("target_words", 0),
                key_points=s.get("key_points", [])
            )
            for s in result.get("sections", [])
        ]

        return OutlineResponse(
            success=True,
            chapter_title=result.get("chapter_title", ""),
            chapter_type=request.chapter_type,
            target_words=result.get("target_words", 0),
            sections=sections
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")
    except Exception as e:
        return OutlineResponse(success=False, error=str(e))


@router.post("/draft/generate", response_model=DraftResponse)
async def generate_draft(request: DraftRequest):
    """Generate a draft section."""
    try:
        from core.writing_desk import WritingDesk

        desk = WritingDesk()

        section_context = {
            "type": request.section_type,
            "tone": request.tone,
            "target_words": request.target_words,
            "existing_text": request.existing_text,
            "notes": request.notes
        }

        result = desk.generate_draft(
            prompt=request.prompt,
            section_context=section_context,
            use_dna=request.use_dna
        )

        if result.get("error"):
            return DraftResponse(success=False, error=result["error"])

        draft = result.get("draft", "")
        return DraftResponse(
            success=True,
            draft=draft,
            word_count=len(draft.split()),
            model_used=result.get("model_used", ""),
            dna_applied=result.get("dna_applied", False)
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")
    except Exception as e:
        return DraftResponse(success=False, error=str(e))


@router.post("/draft/stream")
async def generate_draft_stream(request: DraftRequest):
    """Generate a draft with streaming response."""
    try:
        from core.writing_desk import WritingDesk

        desk = WritingDesk()

        async def stream_generator():
            """Generate draft chunks."""
            # For now, generate full draft and chunk it
            # TODO: Implement true streaming when LLM gateway supports it
            section_context = {
                "type": request.section_type,
                "tone": request.tone,
                "target_words": request.target_words,
            }

            result = desk.generate_draft(
                prompt=request.prompt,
                section_context=section_context,
                use_dna=request.use_dna
            )

            draft = result.get("draft", "")

            # Simulate streaming by yielding chunks
            chunk_size = 50  # characters
            for i in range(0, len(draft), chunk_size):
                chunk = draft[i:i + chunk_size]
                yield f"data: {chunk}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream"
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")


@router.post("/draft/analyze-gaps", response_model=GapAnalysisResponse)
async def analyze_gaps(request: GapAnalysisRequest):
    """Analyze a draft for gaps and weaknesses."""
    try:
        from core.writing_desk import WritingDesk

        desk = WritingDesk()
        result = desk.identify_gaps(request.draft_text, request.chapter_type)

        if result.get("error"):
            return GapAnalysisResponse(success=False, error=result["error"])

        return GapAnalysisResponse(
            success=True,
            missing_evidence=result.get("missing_evidence", []),
            logical_gaps=result.get("logical_gaps", []),
            unsupported_assertions=result.get("unsupported_assertions", []),
            weak_connections=result.get("weak_connections", []),
            suggestions=result.get("suggestions", []),
            priority_actions=result.get("priority_actions", [])
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")
    except Exception as e:
        return GapAnalysisResponse(success=False, error=str(e))


@router.post("/draft/counter-arguments", response_model=CounterArgumentResponse)
async def generate_counter_arguments(request: CounterArgumentRequest):
    """Generate counter-arguments for an argument."""
    try:
        from core.writing_desk import WritingDesk

        desk = WritingDesk()
        result = desk.generate_counter_arguments(request.argument_text)

        if result.get("error"):
            return CounterArgumentResponse(success=False, error=result["error"])

        counter_args = [
            CounterArgument(
                argument=ca.get("argument", ""),
                strength=ca.get("strength", "medium"),
                response_strategy=ca.get("response_strategy", "")
            )
            for ca in result.get("counter_arguments", [])
        ]

        return CounterArgumentResponse(
            success=True,
            counter_arguments=counter_args
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Writing Desk module not available")
    except Exception as e:
        return CounterArgumentResponse(success=False, error=str(e))


@router.post("/citations/suggest", response_model=CitationSuggestionResponse)
async def suggest_citations(request: CitationSuggestionRequest):
    """Get citation suggestions from Zotero library."""
    try:
        from core.services import get_services

        services = get_services()
        citations = services.get_citations(request.context_text, request.num_suggestions)

        suggestions = []
        for cit in citations:
            creators = cit.get("creators", [])
            authors = ", ".join([c.get("lastName", "") for c in creators[:3]])
            if len(creators) > 3:
                authors += " et al."

            year = cit.get("date", "n.d.")[:4] if cit.get("date") else "n.d."

            suggestions.append(CitationSuggestion(
                title=cit.get("title", "Untitled"),
                authors=authors,
                year=year,
                relevance=cit.get("relevance", ""),
                inline_citation=f"({authors}, {year})"
            ))

        return CitationSuggestionResponse(
            success=True,
            suggestions=suggestions
        )

    except Exception as e:
        return CitationSuggestionResponse(success=False, error=str(e))


@router.get("/context")
async def get_writing_context():
    """Get current writing context and available integrations."""
    try:
        from core.services import get_services

        services = get_services()

        return {
            "dna_profile_available": services.has_dna_profile(),
            "zotero_available": True,  # Check if configured
            "services_status": services.get_status()
        }

    except Exception as e:
        return {"error": str(e)}
