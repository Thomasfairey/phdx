"""
PHDx Auditor - Oxford Brookes PhD Marking Criteria Evaluator

This module evaluates thesis drafts against the official Oxford Brookes
University PhD assessment criteria: Originality, Criticality, and Rigour.

Reference: Oxford Brookes Research Degrees Examination Regulations
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

# Import secrets utility
try:
    from core.secrets_utils import get_secret
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.secrets_utils import get_secret

# Load environment variables
load_dotenv()

# =============================================================================
# OXFORD BROOKES PHD MARKING CRITERIA
# =============================================================================

OXFORD_BROOKES_CRITERIA = {
    "institution": "Oxford Brookes University",
    "degree": "Doctor of Philosophy (PhD)",
    "criteria": {
        "originality": {
            "name": "Originality",
            "weight": 0.35,
            "description": "The thesis must make an original contribution to knowledge",
            "indicators": [
                "Novel theoretical framework or conceptual contribution",
                "New empirical findings that advance the field",
                "Innovative methodology or analytical approach",
                "Original synthesis of existing knowledge",
                "Discovery of new facts or relationships",
                "Development of new techniques, tools, or applications"
            ],
            "grade_descriptors": {
                "excellent": "Makes a significant and innovative contribution that advances the field substantially. Demonstrates clear potential for high-impact publication.",
                "good": "Makes a solid original contribution with clear novelty. Advances understanding in the field.",
                "satisfactory": "Makes an adequate contribution to knowledge. Some original elements present but scope is limited.",
                "needs_improvement": "Originality is unclear or insufficiently demonstrated. Contribution to knowledge is marginal.",
                "unsatisfactory": "Fails to demonstrate original contribution. Work is largely derivative or replicative."
            }
        },
        "criticality": {
            "name": "Critical Analysis & Argumentation",
            "weight": 0.35,
            "description": "The thesis must demonstrate critical engagement with the literature and rigorous argumentation",
            "indicators": [
                "Comprehensive and systematic literature review",
                "Critical evaluation of sources and methodologies",
                "Well-structured and coherent argumentation",
                "Identification of gaps, tensions, and debates in the field",
                "Balanced consideration of alternative perspectives",
                "Clear articulation of theoretical positioning",
                "Logical progression from evidence to conclusions"
            ],
            "grade_descriptors": {
                "excellent": "Exceptional critical engagement with sophisticated argumentation. Demonstrates mastery of the field with nuanced evaluation of complex issues.",
                "good": "Strong critical analysis with well-developed arguments. Engages effectively with key debates and perspectives.",
                "satisfactory": "Adequate critical engagement. Arguments are generally sound but may lack depth in places.",
                "needs_improvement": "Limited critical analysis. Arguments may be superficial or poorly developed.",
                "unsatisfactory": "Lacks critical engagement. Arguments are weak, inconsistent, or absent."
            }
        },
        "rigour": {
            "name": "Methodological Rigour",
            "weight": 0.30,
            "description": "The thesis must demonstrate appropriate and rigorous research design and execution",
            "indicators": [
                "Clear and justified research design",
                "Appropriate methodology for research questions",
                "Systematic data collection procedures",
                "Robust analytical framework",
                "Transparent reporting of methods and limitations",
                "Ethical considerations addressed appropriately",
                "Replicability and validity considerations",
                "Appropriate use of evidence to support claims"
            ],
            "grade_descriptors": {
                "excellent": "Exemplary methodological rigour with innovative yet appropriate design. Methods are transparently reported and executed to the highest standards.",
                "good": "Strong methodological approach with clear justification. Minor limitations acknowledged and addressed.",
                "satisfactory": "Adequate research design with acceptable rigour. Some methodological limitations present.",
                "needs_improvement": "Methodological weaknesses that undermine confidence in findings. Design or execution issues evident.",
                "unsatisfactory": "Serious methodological flaws. Research design is inappropriate or poorly executed."
            }
        }
    },
    "grade_scale": {
        "excellent": {"range": "85-100", "descriptor": "Distinction-level work"},
        "good": {"range": "70-84", "descriptor": "Strong pass"},
        "satisfactory": {"range": "60-69", "descriptor": "Pass"},
        "needs_improvement": {"range": "50-59", "descriptor": "Marginal - revisions required"},
        "unsatisfactory": {"range": "0-49", "descriptor": "Fail - major revisions or resubmission"}
    }
}

# System prompt for Claude evaluation
AUDITOR_SYSTEM_PROMPT = f"""You are an expert PhD thesis examiner at Oxford Brookes University. Your role is to evaluate thesis drafts against the official Oxford Brookes PhD marking criteria.

## OXFORD BROOKES PHD ASSESSMENT CRITERIA

### 1. ORIGINALITY (Weight: 35%)
{OXFORD_BROOKES_CRITERIA['criteria']['originality']['description']}

Key Indicators:
{chr(10).join('- ' + i for i in OXFORD_BROOKES_CRITERIA['criteria']['originality']['indicators'])}

### 2. CRITICAL ANALYSIS & ARGUMENTATION (Weight: 35%)
{OXFORD_BROOKES_CRITERIA['criteria']['criticality']['description']}

Key Indicators:
{chr(10).join('- ' + i for i in OXFORD_BROOKES_CRITERIA['criteria']['criticality']['indicators'])}

### 3. METHODOLOGICAL RIGOUR (Weight: 30%)
{OXFORD_BROOKES_CRITERIA['criteria']['rigour']['description']}

Key Indicators:
{chr(10).join('- ' + i for i in OXFORD_BROOKES_CRITERIA['criteria']['rigour']['indicators'])}

## GRADING SCALE
- Excellent (85-100): Distinction-level work
- Good (70-84): Strong pass
- Satisfactory (60-69): Pass
- Needs Improvement (50-59): Marginal - revisions required
- Unsatisfactory (0-49): Fail - major revisions needed

You must provide constructive, specific feedback that helps the candidate improve their work. Be rigorous but fair in your assessment."""


class BrookesAuditor:
    """
    Evaluates thesis drafts against Oxford Brookes PhD marking criteria.
    """

    def __init__(self):
        """Initialize the auditor with Claude client."""
        api_key = get_secret("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.criteria = OXFORD_BROOKES_CRITERIA

    def audit_draft(self, draft_text: str, chapter_context: str = "") -> dict:
        """
        Evaluate a draft against Oxford Brookes PhD criteria.

        Args:
            draft_text: The text to evaluate
            chapter_context: Optional context (e.g., "Chapter 2: Literature Review")

        Returns:
            dict: Audit report with grades and feedback
                {
                    "audit_id": str,
                    "timestamp": str,
                    "status": "success" | "error",
                    "context": str,
                    "word_count": int,
                    "overall_grade": {
                        "score": int,
                        "level": str,
                        "descriptor": str
                    },
                    "criteria_scores": {
                        "originality": {"score": int, "level": str, "feedback": str},
                        "criticality": {"score": int, "level": str, "feedback": str},
                        "rigour": {"score": int, "level": str, "feedback": str}
                    },
                    "strengths": [str],
                    "areas_for_improvement": [str],
                    "specific_recommendations": [str],
                    "examiner_summary": str
                }
        """
        import hashlib

        # Generate audit ID
        audit_id = hashlib.md5(
            f"{draft_text[:50]}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:10]

        report = {
            "audit_id": audit_id,
            "timestamp": datetime.now().isoformat(),
            "status": "error",
            "context": chapter_context or "General Draft",
            "word_count": len(draft_text.split()),
            "overall_grade": {
                "score": 0,
                "level": "unknown",
                "descriptor": ""
            },
            "criteria_scores": {
                "originality": {"score": 0, "level": "", "feedback": ""},
                "criticality": {"score": 0, "level": "", "feedback": ""},
                "rigour": {"score": 0, "level": "", "feedback": ""}
            },
            "strengths": [],
            "areas_for_improvement": [],
            "specific_recommendations": [],
            "examiner_summary": ""
        }

        if not self.claude_client:
            report["error"] = "ANTHROPIC_API_KEY not configured"
            return report

        if len(draft_text.strip()) < 100:
            report["error"] = "Draft too short for meaningful evaluation (min 100 characters)"
            return report

        # Construct evaluation prompt
        eval_prompt = f"""Evaluate the following PhD thesis draft against Oxford Brookes marking criteria.

{f"CONTEXT: {chapter_context}" if chapter_context else ""}

DRAFT TEXT:
{draft_text}

Provide your evaluation as a JSON object with this exact structure:
{{
    "overall_grade": {{
        "score": <integer 0-100>,
        "level": "excellent" | "good" | "satisfactory" | "needs_improvement" | "unsatisfactory",
        "descriptor": "<brief overall assessment>"
    }},
    "criteria_scores": {{
        "originality": {{
            "score": <integer 0-100>,
            "level": "excellent" | "good" | "satisfactory" | "needs_improvement" | "unsatisfactory",
            "feedback": "<specific feedback on originality, 2-3 sentences>"
        }},
        "criticality": {{
            "score": <integer 0-100>,
            "level": "excellent" | "good" | "satisfactory" | "needs_improvement" | "unsatisfactory",
            "feedback": "<specific feedback on critical analysis, 2-3 sentences>"
        }},
        "rigour": {{
            "score": <integer 0-100>,
            "level": "excellent" | "good" | "satisfactory" | "needs_improvement" | "unsatisfactory",
            "feedback": "<specific feedback on methodological rigour, 2-3 sentences>"
        }}
    }},
    "strengths": [
        "<strength 1>",
        "<strength 2>",
        "<strength 3>"
    ],
    "areas_for_improvement": [
        "<area 1>",
        "<area 2>",
        "<area 3>"
    ],
    "specific_recommendations": [
        "<actionable recommendation 1>",
        "<actionable recommendation 2>",
        "<actionable recommendation 3>"
    ],
    "examiner_summary": "<2-3 paragraph summary as if written by a PhD examiner, addressing the candidate directly>"
}}

Be constructive but rigorous. Provide specific, actionable feedback.
Return ONLY valid JSON, no markdown formatting."""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=AUDITOR_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": eval_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Clean markdown if present
            if response_text.startswith("```"):
                import re
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)

            # Parse response
            evaluation = json.loads(response_text)

            # Populate report
            report["status"] = "success"
            report["overall_grade"] = evaluation.get("overall_grade", report["overall_grade"])
            report["criteria_scores"] = evaluation.get("criteria_scores", report["criteria_scores"])
            report["strengths"] = evaluation.get("strengths", [])
            report["areas_for_improvement"] = evaluation.get("areas_for_improvement", [])
            report["specific_recommendations"] = evaluation.get("specific_recommendations", [])
            report["examiner_summary"] = evaluation.get("examiner_summary", "")

        except json.JSONDecodeError as e:
            report["error"] = f"Failed to parse evaluation: {str(e)}"
            report["raw_response"] = response_text if 'response_text' in dir() else None

        except Exception as e:
            report["error"] = f"Evaluation failed: {str(e)}"

        return report

    def get_criteria_summary(self) -> dict:
        """Return a summary of the marking criteria for display."""
        return {
            "institution": self.criteria["institution"],
            "criteria": [
                {
                    "name": c["name"],
                    "weight": f"{int(c['weight'] * 100)}%",
                    "description": c["description"]
                }
                for c in self.criteria["criteria"].values()
            ],
            "grade_scale": self.criteria["grade_scale"]
        }

    def format_audit_for_display(self, report: dict) -> str:
        """Format audit report as markdown for Streamlit display."""
        if report.get("error"):
            return f"**Error:** {report['error']}"

        grade = report["overall_grade"]
        scores = report["criteria_scores"]

        # Grade color
        level_colors = {
            "excellent": "#00c853",
            "good": "#0071ce",
            "satisfactory": "#ffc107",
            "needs_improvement": "#ff9800",
            "unsatisfactory": "#f44336"
        }
        color = level_colors.get(grade["level"], "#e0e0e0")

        md = f"""
### Oxford Brookes PhD Audit Report

**Audit ID:** `{report['audit_id']}`
**Date:** {report['timestamp'][:10]}
**Context:** {report['context']}
**Word Count:** {report['word_count']:,}

---

## Overall Grade: <span style="color:{color}">{grade['score']}/100 ({grade['level'].replace('_', ' ').title()})</span>

{grade['descriptor']}

---

## Criteria Breakdown

| Criterion | Score | Level | Weight |
|-----------|-------|-------|--------|
| Originality | {scores['originality']['score']}/100 | {scores['originality']['level'].replace('_', ' ').title()} | 35% |
| Critical Analysis | {scores['criticality']['score']}/100 | {scores['criticality']['level'].replace('_', ' ').title()} | 35% |
| Methodological Rigour | {scores['rigour']['score']}/100 | {scores['rigour']['level'].replace('_', ' ').title()} | 30% |

### Originality
{scores['originality']['feedback']}

### Critical Analysis
{scores['criticality']['feedback']}

### Methodological Rigour
{scores['rigour']['feedback']}

---

## Strengths
{chr(10).join('- ' + s for s in report['strengths'])}

## Areas for Improvement
{chr(10).join('- ' + a for a in report['areas_for_improvement'])}

## Recommendations
{chr(10).join('- ' + r for r in report['specific_recommendations'])}

---

## Examiner Summary

{report['examiner_summary']}
"""
        return md


# =============================================================================
# GOOGLE DOCS INTEGRATION
# =============================================================================

class GoogleDocsPusher:
    """
    Push verified drafts to Google Docs with PHDx timestamp.
    """

    def __init__(self):
        """Initialize Google Docs client."""
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        self.service = None

    def _get_service(self):
        """Get or create Google Docs API service."""
        if self.service:
            return self.service

        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            if not Path(self.credentials_path).exists():
                raise FileNotFoundError(f"Credentials not found: {self.credentials_path}")

            scopes = [
                "https://www.googleapis.com/auth/documents",
                "https://www.googleapis.com/auth/drive"
            ]

            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=scopes
            )

            self.service = build('docs', 'v1', credentials=creds)
            return self.service

        except ImportError:
            raise ImportError("google-api-python-client not installed")

    def push_to_doc(
        self,
        doc_id: str,
        text: str,
        section_title: str = "",
        include_timestamp: bool = True
    ) -> dict:
        """
        Append text to the end of a Google Doc.

        Args:
            doc_id: Google Doc ID (from URL)
            text: Text to append
            section_title: Optional section heading
            include_timestamp: Whether to include PHDx-Verified timestamp

        Returns:
            dict: Result of the operation
                {
                    "success": bool,
                    "doc_id": str,
                    "doc_url": str,
                    "timestamp": str,
                    "characters_added": int,
                    "error": str (if failed)
                }
        """
        result = {
            "success": False,
            "doc_id": doc_id,
            "doc_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            "timestamp": datetime.now().isoformat(),
            "characters_added": 0
        }

        try:
            service = self._get_service()

            # Get current document to find end index
            doc = service.documents().get(documentId=doc_id).execute()
            end_index = doc['body']['content'][-1]['endIndex'] - 1

            # Build content to insert
            content_parts = []

            # Add section break
            content_parts.append("\n\n---\n\n")

            # Add PHDx verification header
            if include_timestamp:
                timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                content_parts.append(f"[PHDx-Verified: {timestamp_str}]\n\n")

            # Add section title if provided
            if section_title:
                content_parts.append(f"## {section_title}\n\n")

            # Add the main text
            content_parts.append(text)

            # Combine all parts
            full_content = "".join(content_parts)

            # Create insert request
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': end_index
                        },
                        'text': full_content
                    }
                }
            ]

            # Execute the request
            service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()

            result["success"] = True
            result["characters_added"] = len(full_content)

        except FileNotFoundError as e:
            result["error"] = str(e)

        except ImportError as e:
            result["error"] = str(e)

        except Exception as e:
            result["error"] = f"Failed to push to Google Doc: {str(e)}"

        return result

    def get_doc_info(self, doc_id: str) -> dict:
        """Get basic info about a Google Doc."""
        try:
            service = self._get_service()
            doc = service.documents().get(documentId=doc_id).execute()

            return {
                "success": True,
                "title": doc.get("title", "Untitled"),
                "doc_id": doc_id,
                "url": f"https://docs.google.com/document/d/{doc_id}/edit"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================

def audit_draft(draft_text: str, chapter_context: str = "") -> dict:
    """
    Standalone function to audit a draft.

    Usage:
        from core.auditor import audit_draft
        report = audit_draft("Your thesis text...", "Chapter 3: Methodology")
    """
    auditor = BrookesAuditor()
    return auditor.audit_draft(draft_text, chapter_context)


def push_to_google_doc(doc_id: str, text: str, section_title: str = "") -> dict:
    """
    Standalone function to push text to Google Doc.

    Usage:
        from core.auditor import push_to_google_doc
        result = push_to_google_doc("doc_id_here", "Your text...", "Section Title")
    """
    pusher = GoogleDocsPusher()
    return pusher.push_to_doc(doc_id, text, section_title)


def get_marking_criteria() -> dict:
    """Return Oxford Brookes marking criteria."""
    return OXFORD_BROOKES_CRITERIA


# =============================================================================
# WAR ROOM - VIVA VOCE SIMULATOR
# =============================================================================

# Hostile examiner system prompt
HOSTILE_EXAMINER_PROMPT = """You are a hostile External Examiner conducting a PhD viva voce examination. You have read the ENTIRE thesis provided below and your job is to probe for weaknesses.

Your personality:
- You are NOT polite. You are direct, probing, and skeptical.
- You challenge every assumption and demand rigorous justification.
- You seek out methodological weaknesses, logical gaps, and unsupported claims.
- You ask follow-up questions that probe deeper into weak areas.
- You never let the candidate off easy with vague answers.

When asking questions:
- Focus on the WEAKEST aspects of the methodology, argumentation, or evidence.
- Ask ONE hard, specific question at a time.
- Be challenging but professional (no personal attacks).
- If methodology is unclear, attack it. If claims are unsupported, demand evidence.
- Reference specific parts of the thesis in your questions.

When evaluating answers:
- Rate answers as: WEAK, EVASIVE, ADEQUATE, or STRONG
- WEAK: Does not address the question, shows lack of understanding
- EVASIVE: Deflects or provides superficial response
- ADEQUATE: Addresses the question but could be stronger
- STRONG: Demonstrates deep understanding and provides compelling justification

After rating, immediately ask the NEXT probing question targeting another weakness."""


class VivaSimulator:
    """
    War Room - Viva Voce Examination Simulator.

    Simulates a hostile external examiner conducting an oral defense.
    """

    def __init__(self):
        """Initialize the Viva Simulator."""
        api_key = get_secret("ANTHROPIC_API_KEY")
        self.claude_client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self._conversation_history: dict[str, list] = {}  # user_id -> message history
        self._thesis_context: dict[str, str] = {}  # user_id -> thesis text

    def load_thesis_context(self, user_id: str, thesis_text: str) -> dict:
        """
        Load thesis context for a defense simulation.

        Args:
            user_id: Unique identifier for the user/session
            thesis_text: The complete thesis text to analyze

        Returns:
            dict with status and analysis preview
        """
        if not self.claude_client:
            return {"success": False, "error": "ANTHROPIC_API_KEY not configured"}

        if len(thesis_text.strip()) < 500:
            return {"success": False, "error": "Thesis text too short (minimum 500 characters)"}

        # Store thesis context
        self._thesis_context[user_id] = thesis_text
        self._conversation_history[user_id] = []

        # Count words and estimate chapters
        word_count = len(thesis_text.split())

        # Detect sections
        sections_detected = []
        section_keywords = ['introduction', 'literature', 'method', 'result', 'discussion', 'conclusion']
        text_lower = thesis_text.lower()
        for kw in section_keywords:
            if kw in text_lower:
                sections_detected.append(kw.title())

        return {
            "success": True,
            "user_id": user_id,
            "word_count": word_count,
            "sections_detected": sections_detected,
            "message": f"Thesis loaded. {word_count:,} words detected. Ready for examination."
        }

    def start_defense(self, user_id: str) -> dict:
        """
        Start the defense simulation with the first hostile question.

        Args:
            user_id: User identifier with loaded thesis

        Returns:
            dict with the first question from the hostile examiner
        """
        if not self.claude_client:
            return {"success": False, "error": "ANTHROPIC_API_KEY not configured"}

        thesis_text = self._thesis_context.get(user_id)
        if not thesis_text:
            return {"success": False, "error": "No thesis loaded. Call load_thesis_context first."}

        # Reset conversation
        self._conversation_history[user_id] = []

        # Generate initial question
        init_prompt = f"""You are beginning the viva voce examination. You have read this thesis:

---
{thesis_text[:15000]}
{f'... [truncated - thesis continues for {len(thesis_text) - 15000} more characters]' if len(thesis_text) > 15000 else ''}
---

Now, identify the WEAKEST link in the methodology or argumentation. Ask your FIRST hard, probing question. Do NOT be polite. Be direct and challenging.

Start with: "Let's begin. [Your question]"

Respond with ONLY your question, nothing else."""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                system=HOSTILE_EXAMINER_PROMPT,
                messages=[{"role": "user", "content": init_prompt}]
            )

            question = response.content[0].text.strip()

            # Store in history
            self._conversation_history[user_id].append({
                "role": "examiner",
                "content": question,
                "type": "question"
            })

            return {
                "success": True,
                "question": question,
                "question_number": 1,
                "session_active": True
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to start defense: {str(e)}"}

    def respond_to_answer(self, user_id: str, candidate_answer: str) -> dict:
        """
        Process candidate's answer and generate next question.

        Args:
            user_id: User identifier
            candidate_answer: The candidate's response to the previous question

        Returns:
            dict with rating, feedback, and next question
        """
        if not self.claude_client:
            return {"success": False, "error": "ANTHROPIC_API_KEY not configured"}

        thesis_text = self._thesis_context.get(user_id)
        if not thesis_text:
            return {"success": False, "error": "No active session"}

        history = self._conversation_history.get(user_id, [])
        if not history:
            return {"success": False, "error": "No active defense session. Start with start_defense."}

        # Get last question
        last_question = None
        for msg in reversed(history):
            if msg["role"] == "examiner" and msg["type"] == "question":
                last_question = msg["content"]
                break

        if not last_question:
            return {"success": False, "error": "No previous question found"}

        # Store candidate answer
        history.append({
            "role": "candidate",
            "content": candidate_answer,
            "type": "answer"
        })

        question_count = sum(1 for m in history if m["role"] == "examiner" and m["type"] == "question")

        # Build context for evaluation
        eval_prompt = f"""Based on the thesis you read earlier, you asked:
"{last_question}"

The candidate answered:
"{candidate_answer}"

Your tasks:
1. Rate this answer as: WEAK, EVASIVE, ADEQUATE, or STRONG
2. Give a brief (1-2 sentence) explanation of why
3. Ask your NEXT probing question targeting ANOTHER weakness in the thesis

{f'This is question {question_count + 1}. You have asked {question_count} questions so far.' if question_count > 0 else ''}

Respond in this EXACT format:
RATING: [WEAK/EVASIVE/ADEQUATE/STRONG]
FEEDBACK: [Your brief explanation]
NEXT QUESTION: [Your next challenging question]"""

        try:
            response = self.claude_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=HOSTILE_EXAMINER_PROMPT + f"\n\nTHESIS CONTEXT (first 8000 chars):\n{thesis_text[:8000]}",
                messages=[{"role": "user", "content": eval_prompt}]
            )

            response_text = response.content[0].text.strip()

            # Parse response
            rating = "UNKNOWN"
            feedback = ""
            next_question = ""

            lines = response_text.split('\n')
            for i, line in enumerate(lines):
                line_upper = line.upper()
                if line_upper.startswith('RATING:'):
                    rating_text = line.split(':', 1)[1].strip().upper()
                    if 'WEAK' in rating_text:
                        rating = 'WEAK'
                    elif 'EVASIVE' in rating_text:
                        rating = 'EVASIVE'
                    elif 'ADEQUATE' in rating_text:
                        rating = 'ADEQUATE'
                    elif 'STRONG' in rating_text:
                        rating = 'STRONG'
                elif line_upper.startswith('FEEDBACK:'):
                    feedback = line.split(':', 1)[1].strip()
                elif line_upper.startswith('NEXT QUESTION:'):
                    next_question = line.split(':', 1)[1].strip()
                    # Get any additional lines that might be part of the question
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not any(lines[j].upper().startswith(k) for k in ['RATING:', 'FEEDBACK:', 'NEXT QUESTION:']):
                            next_question += ' ' + lines[j].strip()

            # If parsing failed, use full response as question
            if not next_question:
                next_question = response_text

            # Store examiner response
            history.append({
                "role": "examiner",
                "content": next_question,
                "type": "question",
                "rating": rating,
                "feedback": feedback
            })

            self._conversation_history[user_id] = history

            return {
                "success": True,
                "rating": rating,
                "feedback": feedback,
                "next_question": next_question,
                "question_number": question_count + 1,
                "session_active": True
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to process answer: {str(e)}"}

    def end_defense(self, user_id: str) -> dict:
        """
        End the defense session and provide summary.

        Args:
            user_id: User identifier

        Returns:
            dict with defense summary and statistics
        """
        history = self._conversation_history.get(user_id, [])

        if not history:
            return {"success": False, "error": "No active session"}

        # Calculate statistics
        total_questions = sum(1 for m in history if m["role"] == "examiner" and m["type"] == "question")
        total_answers = sum(1 for m in history if m["role"] == "candidate")

        ratings = [m.get("rating") for m in history if m.get("rating")]
        rating_counts = {
            "STRONG": ratings.count("STRONG"),
            "ADEQUATE": ratings.count("ADEQUATE"),
            "EVASIVE": ratings.count("EVASIVE"),
            "WEAK": ratings.count("WEAK")
        }

        # Calculate performance score
        score_map = {"STRONG": 100, "ADEQUATE": 70, "EVASIVE": 40, "WEAK": 20}
        if ratings:
            avg_score = sum(score_map.get(r, 50) for r in ratings) / len(ratings)
        else:
            avg_score = 0

        # Determine verdict
        if avg_score >= 80:
            verdict = "PASS - Strong Defense"
            verdict_detail = "You demonstrated excellent command of your research and responded well to challenging questions."
        elif avg_score >= 60:
            verdict = "PASS WITH MINOR CORRECTIONS"
            verdict_detail = "Your defense was adequate but revealed some areas requiring minor revisions."
        elif avg_score >= 40:
            verdict = "MAJOR CORRECTIONS REQUIRED"
            verdict_detail = "Significant gaps in your defense suggest substantial revisions are needed."
        else:
            verdict = "RESUBMISSION REQUIRED"
            verdict_detail = "Your defense revealed fundamental issues that require extensive rework."

        # Clean up session
        if user_id in self._conversation_history:
            del self._conversation_history[user_id]
        if user_id in self._thesis_context:
            del self._thesis_context[user_id]

        return {
            "success": True,
            "summary": {
                "total_questions": total_questions,
                "total_answers": total_answers,
                "rating_breakdown": rating_counts,
                "average_score": round(avg_score, 1),
                "verdict": verdict,
                "verdict_detail": verdict_detail
            },
            "session_active": False
        }

    def get_session_status(self, user_id: str) -> dict:
        """Get current session status."""
        has_thesis = user_id in self._thesis_context
        history = self._conversation_history.get(user_id, [])

        return {
            "session_active": has_thesis,
            "thesis_loaded": has_thesis,
            "questions_asked": sum(1 for m in history if m["role"] == "examiner" and m["type"] == "question"),
            "answers_given": sum(1 for m in history if m["role"] == "candidate"),
        }


def simulate_defense(user_id: str, thesis_text: str = None, action: str = "start", answer: str = None) -> dict:
    """
    Standalone function for defense simulation.

    Args:
        user_id: Unique user identifier
        thesis_text: Full thesis text (required for 'start' action)
        action: One of 'start', 'answer', 'end', 'status'
        answer: Candidate's answer (required for 'answer' action)

    Returns:
        dict with simulation result
    """
    simulator = VivaSimulator()

    if action == "start":
        if not thesis_text:
            return {"success": False, "error": "thesis_text required for start action"}
        load_result = simulator.load_thesis_context(user_id, thesis_text)
        if not load_result["success"]:
            return load_result
        return simulator.start_defense(user_id)

    elif action == "answer":
        if not answer:
            return {"success": False, "error": "answer required for answer action"}
        return simulator.respond_to_answer(user_id, answer)

    elif action == "end":
        return simulator.end_defense(user_id)

    elif action == "status":
        return simulator.get_session_status(user_id)

    else:
        return {"success": False, "error": f"Unknown action: {action}"}


# =============================================================================
# Module Entry Point
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Auditor - Oxford Brookes PhD Marking Criteria")
    print("=" * 60)

    auditor = BrookesAuditor()
    summary = auditor.get_criteria_summary()

    print(f"\nInstitution: {summary['institution']}")
    print("\nAssessment Criteria:")
    for c in summary['criteria']:
        print(f"  - {c['name']} ({c['weight']}): {c['description'][:50]}...")

    print("\nGrade Scale:")
    for level, info in summary['grade_scale'].items():
        print(f"  - {level.title()}: {info['range']} - {info['descriptor']}")
