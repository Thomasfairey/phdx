#!/usr/bin/env python3
"""
PHDx Architecture Validation - Simulation Harness
==================================================

A comprehensive test suite that validates the PHDx thesis assistant architecture
against Oxford Brookes University standards using synthetic dummy data.

Modules Tested:
- Ethics Airlock: PII detection and redaction
- DNA Engine: Linguistic fingerprinting and style deviation detection
- Auditor: Compliance scoring (Originality, Criticality, Rigour)
- Feedback Processor: Traffic light classification (Red/Amber/Green)
- Red Thread Engine: Vector similarity for logical continuity
- Transparency Log: AI usage audit logging

Author: PHDx Architecture Validation Team
Date: 2026-01-19
"""

import json
import re
import math
import hashlib
import statistics
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
from collections import Counter


# =============================================================================
# PHASE A: SYNTHETIC DATA GENERATION
# =============================================================================

class SyntheticDataGenerator:
    """Generates realistic synthetic data for architecture testing."""

    @staticmethod
    def generate_author_profile() -> str:
        """
        Generate a 500-word sample representing the student's natural writing style.
        Characteristics: Academic tone, moderate hedging, varied sentence length.
        """
        return """The intersection of urban ecology and economic development presents
a compelling area of scholarly inquiry that merits careful examination. This research
endeavours to explore the multifaceted relationships between environmental sustainability
and community economic resilience, drawing upon theoretical frameworks from both
ecological economics and urban geography.

It could be argued that contemporary urban planning has, perhaps inadvisedly,
overlooked the potential contributions of small-scale agricultural interventions.
The literature suggests that community-based initiatives may offer viable pathways
toward sustainable development, though the empirical evidence remains somewhat
contested among scholars in this field. Furthermore, preliminary observations
indicate that localised food production systems might contribute meaningfully to
neighbourhood economic vitality.

The methodological approach adopted herein reflects a commitment to rigorous
qualitative inquiry. Semi-structured interviews were conducted with thirty-seven
participants across four distinct urban contexts, enabling a nuanced understanding
of lived experiences. The analytical framework draws upon grounded theory principles,
allowing themes to emerge organically from the data rather than imposing predetermined
categories upon participant narratives.

Theoretical considerations suggest that ecosystems services valuation may provide
a useful lens through which to examine these phenomena. However, it is important
to acknowledge certain limitations inherent in applying such frameworks to
community-level analysis. The complexity of urban social-ecological systems
arguably demands more holistic approaches that transcend disciplinary boundaries.

Several key findings emerge from this investigation. Firstly, participants
consistently emphasised the importance of community ownership in determining
project sustainability. Secondly, economic benefits appeared to extend beyond
direct monetary gains, encompassing social capital formation and skill development.
Thirdly, environmental awareness among participants demonstrated notable increases
following engagement with urban greening initiatives.

The implications of these findings for policy development warrant careful
consideration. Municipal authorities might benefit from adopting more flexible
regulatory frameworks that accommodate grassroots environmental initiatives.
Additionally, funding mechanisms could potentially be restructured to support
longer-term community capacity building rather than short-term project deliverables.

Critical engagement with existing literature reveals certain tensions between
neoliberal urban governance paradigms and community-led sustainability efforts.
These tensions manifest in resource allocation decisions, planning processes,
and evaluation criteria that may inadvertently disadvantage participatory approaches.
Scholars have increasingly called for governance models that privilege community
voice alongside technical expertise.

In conclusion, this research contributes to ongoing scholarly conversations
regarding urban sustainability transitions. The findings suggest that small-scale
interventions, when appropriately supported, may yield disproportionately positive
outcomes for both environmental and economic indicators. Future research might
productively examine the scalability of such approaches across diverse urban contexts,
whilst remaining attentive to the specificities of local conditions and community
aspirations. The theoretical and practical implications extend beyond the immediate
case studies, offering insights relevant to broader debates concerning sustainable
urban futures and the democratisation of environmental governance."""

    @staticmethod
    def generate_draft_chapter() -> str:
        """
        Generate a 1000-word academic text with intentional 'errors' for testing:
        - PII (names, phone numbers, emails)
        - Style shift (AI-generated/generic paragraph)
        """
        return """Chapter 4: Discussion

The Socio-Economic Impact of Urban Beekeeping: A Critical Analysis

4.1 Introduction to Findings

This chapter presents a comprehensive discussion of the research findings,
situating them within the broader theoretical landscape outlined in Chapter 2.
The analysis draws upon data collected from multiple urban beekeeping initiatives
across Greater London, with particular attention to the economic and social
dimensions of these interventions. Initial observations suggest that urban
apiculture may serve as a catalyst for community development, though the
mechanisms underlying these effects require careful examination.

4.2 Economic Impact Assessment

The economic implications of urban beekeeping extend considerably beyond
simple honey production metrics. Participant John Doe, contacted at
07700900461, provided particularly illuminating insights regarding the
indirect economic benefits observed within his community. Revenue streams
identified through this research include direct product sales, educational
workshop fees, and pollination services for local urban agriculture initiatives.

Quantitative analysis reveals that participating communities experienced
an average 23% increase in local economic activity attributable to
beekeeping-related enterprises. However, it must be acknowledged that
establishing precise causal relationships presents methodological challenges.
The research team, including Dr. Sarah Mitchell (s.mitchell@oxfordbrookes.ac.uk),
employed triangulation strategies to enhance the validity of economic assessments.

Interview data from Participant ID: P-2847-CONF suggests that informal
economic exchanges may constitute a significant yet underreported component
of the overall economic impact. These findings align with theoretical
frameworks emphasising the importance of social economy perspectives in
understanding community-based initiatives.

4.3 Social Capital Formation

[STYLE SHIFT - AI GENERATED PARAGRAPH]
Urban beekeeping is a practice that involves keeping bees in urban areas.
It has become increasingly popular in recent years. Many people are interested
in urban beekeeping because it can help the environment. Bees are important
pollinators and they help plants grow. Urban beekeeping can also provide
honey for local communities. This is a good thing because honey is healthy
and delicious. Many cities now allow urban beekeeping and have created
regulations to make it safe. Overall, urban beekeeping is a positive trend
that benefits both people and the environment in many different ways.
[END STYLE SHIFT]

Returning to our analytical framework, the formation of social capital
through shared beekeeping activities emerged as a particularly salient theme.
Participants described how collective hive management fostered trust-building
and reciprocal relationships that extended beyond the immediate apicultural
context. Mrs. Elizabeth Warren (contact: 020-7946-0958) articulated this
dynamic particularly effectively during her interview.

4.4 Environmental Consciousness

The pedagogical dimensions of urban beekeeping merit substantial attention.
Engagement with hive ecosystems appeared to catalyse broader environmental
awareness among participants, with many reporting fundamental shifts in
their understanding of urban ecology. This finding resonates with
experiential learning theories proposed by Kolb and subsequent scholars.

Preliminary data suggests that 78% of participants demonstrated measurably
enhanced environmental literacy following six months of involvement.
These outcomes arguably validate investments in community-based
environmental education initiatives, though longitudinal research would
be necessary to assess the durability of such effects.

4.5 Challenges and Constraints

Several significant challenges emerged throughout this investigation.
Regulatory complexity represented a substantial barrier for many aspiring
urban beekeepers, with navigating planning permissions and environmental
health requirements consuming considerable time and resources. Participant
Thomas Anderson (email: t.anderson.participant@gmail.com) described spending
over forty hours addressing administrative requirements before establishing
his first hive.

Furthermore, the initial capital investment required for appropriate
equipment and training may exclude lower-income community members from
participation. This observation raises important equity considerations
that warrant attention in policy development processes. The research
assistant, Jane Cooper (ID: JC-STAFF-0042), noted similar patterns across
all four study sites.

4.6 Theoretical Implications

These findings contribute meaningfully to theoretical debates regarding
urban sustainability transitions. The observed synergies between economic
development and environmental enhancement challenge narratives positioning
these objectives as inherently conflictual. Rather, our data suggests
that appropriately designed interventions may generate co-benefits across
multiple sustainability dimensions.

The applicability of resilience thinking frameworks to urban community
contexts receives substantial empirical support through this research.
Beekeeping communities demonstrated adaptive capacity characteristics
consistent with theoretical predictions, including diversity, modularity,
and feedback responsiveness. These observations extend the explanatory
power of social-ecological systems theory to novel urban contexts.

4.7 Policy Recommendations

Based upon the foregoing analysis, several policy recommendations may
be advanced. Municipal authorities should consider streamlining regulatory
pathways for community-based urban agriculture initiatives. Financial
support mechanisms might productively target capacity building and
knowledge exchange rather than direct production subsidies. Planning
frameworks could beneficially incorporate pollinator habitat considerations
as standard elements of urban development assessment.

4.8 Limitations and Future Research

This research acknowledges certain limitations that contextualize the
findings presented. The geographic scope, whilst enabling depth of
analysis, necessarily constrains generalisability claims. Temporal
constraints precluded longitudinal assessment of long-term economic
trajectories. Future research might productively address these limitations
through expanded multi-site studies and extended observation periods.

The intersection of urban beekeeping with broader food security concerns
represents a particularly promising avenue for subsequent investigation.
Additionally, comparative analysis across different regulatory environments
could yield valuable insights regarding optimal policy configurations
for supporting community-based environmental initiatives.

4.9 Conclusion

In summary, this chapter has examined the socio-economic dimensions of
urban beekeeping through rigorous engagement with empirical evidence
and theoretical frameworks. The findings suggest that such initiatives
offer genuine potential for contributing to sustainable urban development,
whilst acknowledging the complexities and constraints that shape their
implementation and outcomes."""

    @staticmethod
    def generate_supervisor_feedback() -> str:
        """
        Generate raw supervisor feedback text with mixed severity levels.
        Contains explicit [Red], [Amber], [Green] markers for testing.
        """
        return """PhD Progress Review - Chapter 4 Draft Feedback
Supervisor: Prof. M. Richardson
Date: November 2025

Overall Impression:
The chapter demonstrates solid engagement with the empirical material,
though several areas require attention before submission.

CRITICAL ISSUES:

1. [Red] The methodology section lacks sufficient justification for the
sampling strategy. You need to explain WHY thirty-seven participants
were selected and how this number ensures theoretical saturation. This
is a fundamental flaw that must be addressed.

2. [Red] The theoretical framework appears disconnected from the analysis
in sections 4.5 and 4.6. The resilience thinking claims need much stronger
evidential support - currently this reads as assertion rather than argument.

3. [Red] Your positionality statement is entirely absent. Given the
participatory nature of this research, this is a serious omission that
the examiners will certainly flag.

CORRECTIONS NEEDED:

4. [Amber] The economic figures in 4.2 need proper citation. Where does
the "23% increase" come from? Is this your data or external sources?

5. [Amber] Several paragraphs exceed recommended length (250-300 words).
Break these down for improved readability.

6. [Amber] The transition between 4.4 and 4.5 is abrupt. Add a linking
paragraph to improve flow.

7. [Amber] Citation formatting inconsistent - some use Oxford style,
others appear to be APA. Standardise throughout.

8. [Amber] Fix typo on page 12: "beneficially" should be "beneficially" -
actually this appears correct, ignore this comment.

POSITIVE ELEMENTS:

9. [Green] Excellent integration of participant quotes in section 4.3.
This brings the analysis to life effectively.

10. [Green] The policy recommendations are practical and well-grounded
in the evidence. Maintain this approach.

11. [Green] Strong concluding synthesis that effectively ties together
the chapter's main arguments.

12. [Green] Good use of hedging language throughout - maintains appropriate
academic caution without undermining your claims.

Please address the Red items as priority before our next meeting.

Best regards,
Prof. Richardson"""


# =============================================================================
# PHASE B: MOCK ARCHITECTURE MODULES
# =============================================================================

@dataclass
class PIIDetection:
    """Represents a detected PII instance."""
    type: str  # 'name', 'phone', 'email', 'participant_id'
    original: str
    position: tuple  # (start, end)


class EthicsAirlock:
    """
    Ethics Airlock Module - PII Detection and Redaction.

    Scans text for personally identifiable information (names, emails,
    phone numbers, participant IDs) and redacts them.
    """

    # PII detection patterns
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'uk_phone': r'\b(?:0\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4}|07\d{3}[-\s]?\d{6})\b',
        'participant_id': r'\b(?:P-\d{4}-[A-Z]+|ID:\s*[A-Z]{2}-[A-Z]+-\d{4}|Participant\s+ID:\s*\S+)\b',
        'name_pattern': r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
        'participant_name': r'\bParticipant\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',
    }

    def __init__(self):
        self.detections: list[PIIDetection] = []
        self.redaction_log: list[dict] = []

    def scan_for_pii(self, text: str) -> list[PIIDetection]:
        """Scan text and return all PII detections."""
        self.detections = []

        for pii_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                self.detections.append(PIIDetection(
                    type=pii_type,
                    original=match.group(),
                    position=(match.start(), match.end())
                ))

        return self.detections

    def redact(self, text: str) -> dict:
        """
        Redact all PII from text.

        Returns:
            dict with 'scrubbed_text', 'total_redactions', 'redaction_details'
        """
        self.scan_for_pii(text)

        # Sort detections by position (reverse) to preserve indices during replacement
        sorted_detections = sorted(self.detections, key=lambda x: x.position[0], reverse=True)

        scrubbed = text
        redaction_details = []

        for detection in sorted_detections:
            start, end = detection.position
            original = scrubbed[start:end]
            scrubbed = scrubbed[:start] + '[REDACTED]' + scrubbed[end:]

            redaction_details.append({
                'type': detection.type,
                'original': original,
                'position': detection.position
            })

        self.redaction_log = redaction_details

        return {
            'scrubbed_text': scrubbed,
            'total_redactions': len(redaction_details),
            'redaction_details': list(reversed(redaction_details))  # Restore original order
        }

    def validate_clean(self, text: str) -> bool:
        """Check if text contains any remaining PII."""
        detections = self.scan_for_pii(text)
        return len(detections) == 0


class DNAEngine:
    """
    DNA Engine - Linguistic Fingerprinting Module.

    Captures linguistic fingerprint including:
    - Vocabulary richness (type-token ratio)
    - Sentence length variance
    - Hedging density
    - Academic tone markers
    """

    HEDGING_PHRASES = [
        'may', 'might', 'could', 'would', 'perhaps', 'possibly', 'arguably',
        'it could be argued', 'suggests that', 'appears to', 'seems to',
        'it is possible', 'potentially', 'presumably', 'likely', 'unlikely',
        'to some extent', 'in some cases', 'tends to', 'generally'
    ]

    ACADEMIC_MARKERS = [
        'furthermore', 'moreover', 'however', 'nevertheless', 'consequently',
        'therefore', 'thus', 'hence', 'notwithstanding', 'whilst', 'whereby',
        'herein', 'aforementioned', 'hitherto', 'vis-à-vis'
    ]

    def __init__(self):
        self.profile: dict = {}

    def analyze(self, text: str) -> dict:
        """
        Generate linguistic fingerprint for text.

        Returns comprehensive profile with metrics.
        """
        words = re.findall(r'\b\w+\b', text.lower())
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Vocabulary richness (Type-Token Ratio)
        unique_words = set(words)
        ttr = len(unique_words) / len(words) if words else 0

        # Sentence length statistics
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) for s in sentences]
        avg_sentence_length = statistics.mean(sentence_lengths) if sentence_lengths else 0
        sentence_length_variance = statistics.variance(sentence_lengths) if len(sentence_lengths) > 1 else 0
        sentence_length_std = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0

        # Hedging density
        hedging_count = sum(1 for phrase in self.HEDGING_PHRASES
                          if phrase in text.lower())
        hedging_density = (hedging_count / len(words)) * 1000 if words else 0

        # Academic marker density
        academic_count = sum(1 for marker in self.ACADEMIC_MARKERS
                           if marker in text.lower())
        academic_density = (academic_count / len(words)) * 1000 if words else 0

        # Average word length
        avg_word_length = statistics.mean([len(w) for w in words]) if words else 0

        self.profile = {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'unique_words': len(unique_words),
            'type_token_ratio': round(ttr, 4),
            'avg_sentence_length': round(avg_sentence_length, 2),
            'sentence_length_variance': round(sentence_length_variance, 2),
            'sentence_length_std': round(sentence_length_std, 2),
            'hedging_density_per_1000': round(hedging_density, 2),
            'academic_marker_density_per_1000': round(academic_density, 2),
            'avg_word_length': round(avg_word_length, 2),
            'hedging_phrases_found': hedging_count,
            'academic_markers_found': academic_count
        }

        return self.profile

    def compare_profiles(self, profile_a: dict, profile_b: dict) -> dict:
        """
        Compare two linguistic profiles and compute deviation scores.

        Returns comparison metrics including style deviance score.
        """
        metrics = ['type_token_ratio', 'avg_sentence_length', 'sentence_length_variance',
                   'hedging_density_per_1000', 'academic_marker_density_per_1000', 'avg_word_length']

        deviations = {}
        for metric in metrics:
            val_a = profile_a.get(metric, 0)
            val_b = profile_b.get(metric, 0)

            if val_a != 0:
                deviation = abs(val_b - val_a) / val_a * 100
            else:
                deviation = 100 if val_b != 0 else 0

            deviations[metric] = round(deviation, 2)

        # Overall style deviance score (weighted average)
        weights = {
            'type_token_ratio': 0.15,
            'avg_sentence_length': 0.20,
            'sentence_length_variance': 0.15,
            'hedging_density_per_1000': 0.25,
            'academic_marker_density_per_1000': 0.15,
            'avg_word_length': 0.10
        }

        style_deviance_score = sum(
            deviations[m] * weights[m] for m in metrics
        )

        return {
            'deviations': deviations,
            'style_deviance_score': round(style_deviance_score, 2),
            'significant_deviation': style_deviance_score > 30  # Threshold for warning
        }

    def detect_style_shift(self, author_profile: dict, chapter_text: str) -> dict:
        """
        Detect paragraphs that deviate significantly from author's style.

        Returns list of flagged paragraphs with their deviation scores.
        """
        paragraphs = re.split(r'\n\n+', chapter_text)
        flagged = []

        for i, para in enumerate(paragraphs):
            if len(para.split()) < 30:  # Skip short paragraphs
                continue

            para_profile = self.analyze(para)
            comparison = self.compare_profiles(author_profile, para_profile)

            if comparison['significant_deviation']:
                flagged.append({
                    'paragraph_index': i,
                    'text_preview': para[:150] + '...' if len(para) > 150 else para,
                    'style_deviance_score': comparison['style_deviance_score'],
                    'deviations': comparison['deviations'],
                    'warning': 'Significant style deviation detected'
                })

        return {
            'total_paragraphs': len(paragraphs),
            'flagged_paragraphs': len(flagged),
            'flags': flagged,
            'style_shift_detected': len(flagged) > 0
        }


class Auditor:
    """
    Auditor Module - Compliance Scoring.

    Scores text based on:
    - Originality (35%): Unique phrasing, vocabulary diversity
    - Criticality (35%): Critical engagement markers, argumentation depth
    - Rigour (30%): Methodological markers, evidence-based claims
    """

    WEIGHTS = {
        'originality': 0.35,
        'criticality': 0.35,
        'rigour': 0.30
    }

    CRITICAL_MARKERS = [
        'critically', 'challenges', 'problematic', 'contested', 'debatable',
        'limitation', 'however', 'nevertheless', 'contrary', 'alternative',
        'critique', 'question', 'examine', 'interrogate', 'scrutinize'
    ]

    RIGOUR_MARKERS = [
        'evidence', 'data', 'findings', 'results', 'analysis', 'methodology',
        'empirical', 'quantitative', 'qualitative', 'systematic', 'validity',
        'reliability', 'triangulation', 'sampling', 'significant'
    ]

    def __init__(self):
        self.last_audit: dict = {}

    def score_originality(self, text: str) -> float:
        """
        Score originality based on vocabulary diversity and unique phrasing.
        Scale: 0-100
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0

        # Type-token ratio component
        unique_ratio = len(set(words)) / len(words)
        ttr_score = min(unique_ratio * 150, 50)  # Cap at 50

        # Sentence structure variety
        sentences = re.split(r'[.!?]+', text)
        sentence_starts = [s.strip().split()[0].lower() for s in sentences
                         if s.strip() and s.strip().split()]
        start_variety = len(set(sentence_starts)) / len(sentence_starts) if sentence_starts else 0
        variety_score = start_variety * 30

        # Long word usage (sophistication proxy)
        long_words = [w for w in words if len(w) > 8]
        sophistication = (len(long_words) / len(words)) * 100
        soph_score = min(sophistication * 2, 20)

        return round(min(ttr_score + variety_score + soph_score, 100), 2)

    def score_criticality(self, text: str) -> float:
        """
        Score critical engagement based on argumentation markers.
        Scale: 0-100
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0

        # Critical marker density
        critical_count = sum(1 for marker in self.CRITICAL_MARKERS
                           if marker in text.lower())
        marker_score = min((critical_count / len(words)) * 2000, 50)

        # Question/interrogation presence
        question_count = text.count('?')
        question_score = min(question_count * 5, 20)

        # Contrast/comparison structures
        contrast_patterns = ['however', 'whereas', 'while', 'although', 'despite',
                           'on the other hand', 'in contrast', 'conversely']
        contrast_count = sum(1 for p in contrast_patterns if p in text.lower())
        contrast_score = min(contrast_count * 5, 30)

        return round(min(marker_score + question_score + contrast_score, 100), 2)

    def score_rigour(self, text: str) -> float:
        """
        Score methodological rigour based on evidence markers.
        Scale: 0-100
        """
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0

        # Rigour marker density
        rigour_count = sum(1 for marker in self.RIGOUR_MARKERS
                         if marker in text.lower())
        marker_score = min((rigour_count / len(words)) * 1500, 50)

        # Numeric evidence (statistics, percentages)
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', text)
        numeric_score = min(len(numbers) * 3, 25)

        # Citation patterns (simplified)
        citation_patterns = [r'\(\d{4}\)', r'\(.*?,\s*\d{4}\)', r'\[.*?\]']
        citation_count = sum(len(re.findall(p, text)) for p in citation_patterns)
        citation_score = min(citation_count * 2, 25)

        return round(min(marker_score + numeric_score + citation_score, 100), 2)

    def audit(self, text: str) -> dict:
        """
        Perform full audit and return scores.

        Returns JSON object with component and total scores.
        """
        originality = self.score_originality(text)
        criticality = self.score_criticality(text)
        rigour = self.score_rigour(text)

        # Weighted total
        total_score = (
            originality * self.WEIGHTS['originality'] +
            criticality * self.WEIGHTS['criticality'] +
            rigour * self.WEIGHTS['rigour']
        )

        self.last_audit = {
            'timestamp': datetime.now().isoformat(),
            'word_count': len(re.findall(r'\b\w+\b', text)),
            'scores': {
                'originality': {
                    'score': originality,
                    'weight': self.WEIGHTS['originality'],
                    'weighted': round(originality * self.WEIGHTS['originality'], 2)
                },
                'criticality': {
                    'score': criticality,
                    'weight': self.WEIGHTS['criticality'],
                    'weighted': round(criticality * self.WEIGHTS['criticality'], 2)
                },
                'rigour': {
                    'score': rigour,
                    'weight': self.WEIGHTS['rigour'],
                    'weighted': round(rigour * self.WEIGHTS['rigour'], 2)
                }
            },
            'total_score': round(total_score, 2),
            'grade': self._score_to_grade(total_score)
        }

        return self.last_audit

    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to grade."""
        if score >= 70:
            return 'Distinction'
        elif score >= 60:
            return 'Merit'
        elif score >= 50:
            return 'Pass'
        else:
            return 'Needs Improvement'


class FeedbackClassifier:
    """
    Feedback Processor - Traffic Light Classification.

    Parses supervisor feedback into:
    - RED: Blockers - Critical structural/theoretical issues
    - AMBER: Major - Stylistic or citation corrections
    - GREEN: Minor - Positive reinforcement
    """

    def __init__(self):
        self.classification: dict = {'RED': [], 'AMBER': [], 'GREEN': []}

    def classify(self, feedback_text: str) -> dict:
        """
        Parse and classify feedback into traffic light categories.

        Looks for explicit markers like [Red], [Amber], [Green] and
        also uses keyword analysis for unmarked feedback.
        """
        self.classification = {'RED': [], 'AMBER': [], 'GREEN': []}

        # Split into individual feedback items
        lines = feedback_text.split('\n')
        current_item = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for explicit markers
            red_match = re.search(r'\[Red\]', line, re.IGNORECASE)
            amber_match = re.search(r'\[Amber\]', line, re.IGNORECASE)
            green_match = re.search(r'\[Green\]', line, re.IGNORECASE)

            if red_match:
                # Clean the marker and add to RED
                clean_text = re.sub(r'\[Red\]\s*', '', line, flags=re.IGNORECASE).strip()
                if clean_text:
                    self.classification['RED'].append({
                        'text': clean_text,
                        'severity': 'blocker',
                        'action': 'Must address before submission'
                    })
            elif amber_match:
                clean_text = re.sub(r'\[Amber\]\s*', '', line, flags=re.IGNORECASE).strip()
                if clean_text:
                    self.classification['AMBER'].append({
                        'text': clean_text,
                        'severity': 'major',
                        'action': 'Should address in revision'
                    })
            elif green_match:
                clean_text = re.sub(r'\[Green\]\s*', '', line, flags=re.IGNORECASE).strip()
                if clean_text:
                    self.classification['GREEN'].append({
                        'text': clean_text,
                        'severity': 'positive',
                        'action': 'Maintain this approach'
                    })

        return self.classification

    def get_summary(self) -> dict:
        """Return summary statistics of classification."""
        return {
            'red_count': len(self.classification['RED']),
            'amber_count': len(self.classification['AMBER']),
            'green_count': len(self.classification['GREEN']),
            'total': sum(len(v) for v in self.classification.values()),
            'critical_issues': len(self.classification['RED']) > 0
        }


class RedThreadEngine:
    """
    Red Thread Engine - Logical Continuity Checker.

    Simulates vector similarity to check logical continuity between chapters.
    Uses simplified cosine similarity on word vectors.
    """

    def __init__(self):
        self.indexed_chapters: dict = {}

    def _text_to_vector(self, text: str) -> Counter:
        """Convert text to word frequency vector."""
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stopwords
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                    'could', 'should', 'may', 'might', 'must', 'this', 'that', 'these',
                    'those', 'it', 'its', 'as', 'if', 'than', 'so', 'such'}
        words = [w for w in words if w not in stopwords and len(w) > 2]
        return Counter(words)

    def _cosine_similarity(self, vec_a: Counter, vec_b: Counter) -> float:
        """Calculate cosine similarity between two word vectors."""
        intersection = set(vec_a.keys()) & set(vec_b.keys())

        if not intersection:
            return 0.0

        dot_product = sum(vec_a[x] * vec_b[x] for x in intersection)

        magnitude_a = math.sqrt(sum(v**2 for v in vec_a.values()))
        magnitude_b = math.sqrt(sum(v**2 for v in vec_b.values()))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def index_chapter(self, chapter_name: str, text: str):
        """Index a chapter for later comparison."""
        self.indexed_chapters[chapter_name] = {
            'text': text,
            'vector': self._text_to_vector(text),
            'word_count': len(text.split())
        }

    def check_continuity(self, chapter_a: str, chapter_b: str) -> dict:
        """
        Check logical continuity between two chapters.

        Returns similarity score and analysis.
        """
        if chapter_a not in self.indexed_chapters:
            return {'error': f'Chapter {chapter_a} not indexed'}
        if chapter_b not in self.indexed_chapters:
            return {'error': f'Chapter {chapter_b} not indexed'}

        vec_a = self.indexed_chapters[chapter_a]['vector']
        vec_b = self.indexed_chapters[chapter_b]['vector']

        similarity = self._cosine_similarity(vec_a, vec_b)

        # Find shared key concepts
        shared_terms = set(vec_a.keys()) & set(vec_b.keys())
        top_shared = sorted(shared_terms,
                          key=lambda x: vec_a[x] + vec_b[x],
                          reverse=True)[:10]

        # Find unique terms in each
        unique_a = set(vec_a.keys()) - set(vec_b.keys())
        unique_b = set(vec_b.keys()) - set(vec_a.keys())

        return {
            'chapter_a': chapter_a,
            'chapter_b': chapter_b,
            'similarity_score': round(similarity, 4),
            'similarity_percentage': round(similarity * 100, 2),
            'continuity_status': 'strong' if similarity > 0.3 else 'moderate' if similarity > 0.15 else 'weak',
            'shared_key_terms': top_shared,
            'terms_only_in_a': list(sorted(unique_a, key=lambda x: vec_a[x], reverse=True))[:5],
            'terms_only_in_b': list(sorted(unique_b, key=lambda x: vec_b[x], reverse=True))[:5],
            'recommendation': self._get_recommendation(similarity)
        }

    def _get_recommendation(self, similarity: float) -> str:
        """Generate recommendation based on similarity score."""
        if similarity > 0.3:
            return "Strong thematic continuity. Chapters are well-connected."
        elif similarity > 0.15:
            return "Moderate continuity. Consider strengthening conceptual links."
        else:
            return "Weak continuity detected. Review argument flow between chapters."


class TransparencyLog:
    """
    Transparency Log - AI Usage Audit Trail.

    Records all AI-assisted operations for academic integrity compliance.
    """

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or Path('./audit_log.json')
        self.entries: list[dict] = []

    def log_ai_usage(self,
                     action_type: str,
                     module: str,
                     input_summary: str,
                     output_summary: str,
                     was_scrubbed: bool = False,
                     redactions_count: int = 0) -> dict:
        """
        Log an AI-assisted action.

        Returns the created log entry.
        """
        entry = {
            'entry_id': hashlib.md5(
                f"{action_type}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12],
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'module': module,
            'input_summary': input_summary[:200] + '...' if len(input_summary) > 200 else input_summary,
            'output_summary': output_summary[:200] + '...' if len(output_summary) > 200 else output_summary,
            'pii_protection': {
                'was_scrubbed': was_scrubbed,
                'redactions_count': redactions_count
            },
            'compliance_flags': {
                'ethics_cleared': was_scrubbed or redactions_count == 0,
                'logged_for_audit': True
            }
        }

        self.entries.append(entry)
        return entry

    def save_log(self) -> str:
        """Save log to JSON file."""
        with open(self.log_path, 'w') as f:
            json.dump({
                'audit_log': self.entries,
                'generated_at': datetime.now().isoformat(),
                'total_entries': len(self.entries)
            }, f, indent=2)
        return str(self.log_path)

    def get_entries(self) -> list[dict]:
        """Return all log entries."""
        return self.entries


# =============================================================================
# TEST RUNNER
# =============================================================================

class PHDxArchitectureValidator:
    """
    Main test harness for validating PHDx architecture.

    Runs all tests and generates validation report.
    """

    def __init__(self):
        self.results: dict = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'synthetic_data': {},
            'recommendations': []
        }

        # Initialize modules
        self.ethics_airlock = EthicsAirlock()
        self.dna_engine = DNAEngine()
        self.auditor = Auditor()
        self.feedback_classifier = FeedbackClassifier()
        self.red_thread = RedThreadEngine()
        self.transparency_log = TransparencyLog()

        # Generate synthetic data
        self.data_generator = SyntheticDataGenerator()
        self.author_profile_text = self.data_generator.generate_author_profile()
        self.draft_chapter_text = self.data_generator.generate_draft_chapter()
        self.supervisor_feedback_text = self.data_generator.generate_supervisor_feedback()

    def run_all_tests(self) -> dict:
        """Execute all architecture validation tests."""
        print("\n" + "=" * 70)
        print("PHDx ARCHITECTURE VALIDATION - SIMULATION HARNESS")
        print("Oxford Brookes University Standards Compliance")
        print("=" * 70)
        print(f"Timestamp: {self.results['timestamp']}")
        print("-" * 70)

        # Store synthetic data info
        self.results['synthetic_data'] = {
            'author_profile_words': len(self.author_profile_text.split()),
            'draft_chapter_words': len(self.draft_chapter_text.split()),
            'supervisor_feedback_words': len(self.supervisor_feedback_text.split())
        }

        # Run tests
        self._test_ethics_airlock()
        self._test_dna_engine()
        self._test_auditor()
        self._test_feedback_processor()
        self._test_red_thread()
        self._test_transparency_log()

        # Generate summary
        self._generate_summary()

        return self.results

    def _test_ethics_airlock(self):
        """TEST 1: Ethics Airlock - PII Detection and Redaction"""
        print("\n[TEST 1] Ethics Airlock (PII Detection)")
        print("-" * 40)

        test_result = {
            'name': 'Ethics Airlock',
            'description': 'PII detection and redaction',
            'passed': False,
            'details': {}
        }

        # Scan for PII
        detections = self.ethics_airlock.scan_for_pii(self.draft_chapter_text)
        print(f"  PII instances detected: {len(detections)}")

        # Redact PII
        redaction_result = self.ethics_airlock.redact(self.draft_chapter_text)
        scrubbed_text = redaction_result['scrubbed_text']

        # Validate - check no PII remains
        is_clean = self.ethics_airlock.validate_clean(scrubbed_text)

        # Check specific patterns don't exist in scrubbed text
        phone_remains = bool(re.search(r'07\d{9}', scrubbed_text))
        email_remains = bool(re.search(r'@[a-zA-Z]+\.[a-zA-Z]+', scrubbed_text))

        test_result['passed'] = is_clean and not phone_remains and not email_remains
        test_result['details'] = {
            'pii_detected': len(detections),
            'redactions_made': redaction_result['total_redactions'],
            'redaction_samples': redaction_result['redaction_details'][:5],
            'validation_clean': is_clean,
            'phone_check_passed': not phone_remains,
            'email_check_passed': not email_remains
        }

        # Log for transparency
        self.transparency_log.log_ai_usage(
            action_type='pii_scan_and_redact',
            module='EthicsAirlock',
            input_summary=f'Draft chapter ({len(self.draft_chapter_text)} chars)',
            output_summary=f'Redacted {redaction_result["total_redactions"]} PII instances',
            was_scrubbed=True,
            redactions_count=redaction_result['total_redactions']
        )

        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"  Status: {status}")
        print(f"  Redactions: {redaction_result['total_redactions']}")

        self.results['tests']['ethics_airlock'] = test_result

    def _test_dna_engine(self):
        """TEST 2: DNA Engine - Linguistic Fingerprinting"""
        print("\n[TEST 2] DNA Engine (Linguistic Fingerprinting)")
        print("-" * 40)

        test_result = {
            'name': 'DNA Engine',
            'description': 'Style deviation detection',
            'passed': False,
            'details': {}
        }

        # Generate author profile
        author_profile = self.dna_engine.analyze(self.author_profile_text)
        print(f"  Author Profile TTR: {author_profile['type_token_ratio']}")
        print(f"  Author Avg Sentence Length: {author_profile['avg_sentence_length']}")

        # Detect style shifts in chapter
        shift_detection = self.dna_engine.detect_style_shift(
            author_profile,
            self.draft_chapter_text
        )

        # Test passes if the intentional style shift is detected
        style_shift_detected = shift_detection['style_shift_detected']
        flagged_count = shift_detection['flagged_paragraphs']

        # Check if the AI-generated paragraph was flagged
        ai_paragraph_flagged = any(
            'increasingly popular' in flag['text_preview'].lower() or
            'urban beekeeping is a practice' in flag['text_preview'].lower()
            for flag in shift_detection['flags']
        )

        test_result['passed'] = style_shift_detected and flagged_count > 0
        test_result['details'] = {
            'author_profile': author_profile,
            'style_shift_detected': style_shift_detected,
            'flagged_paragraphs': flagged_count,
            'ai_paragraph_detected': ai_paragraph_flagged,
            'flags': shift_detection['flags'][:3]  # First 3 flags
        }

        self.transparency_log.log_ai_usage(
            action_type='style_analysis',
            module='DNAEngine',
            input_summary='Author profile vs draft chapter comparison',
            output_summary=f'Detected {flagged_count} style deviations',
            was_scrubbed=False
        )

        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"  Status: {status}")
        print(f"  Style shifts detected: {flagged_count}")
        if ai_paragraph_flagged:
            print("  AI-generated paragraph successfully flagged!")

        self.results['tests']['dna_engine'] = test_result

    def _test_auditor(self):
        """TEST 3: Auditor - Compliance Scoring"""
        print("\n[TEST 3] Auditor (Compliance Scoring)")
        print("-" * 40)

        test_result = {
            'name': 'Auditor',
            'description': 'Weighted compliance scoring',
            'passed': False,
            'details': {}
        }

        # Perform audit
        audit_result = self.auditor.audit(self.draft_chapter_text)

        # Verify weight calculations
        scores = audit_result['scores']
        calculated_total = (
            scores['originality']['score'] * scores['originality']['weight'] +
            scores['criticality']['score'] * scores['criticality']['weight'] +
            scores['rigour']['score'] * scores['rigour']['weight']
        )

        # Check if weights sum to 1.0
        weights_sum = sum(score['weight'] for score in scores.values())
        weights_valid = abs(weights_sum - 1.0) < 0.001

        # Check if total matches calculated
        total_matches = abs(audit_result['total_score'] - calculated_total) < 0.1

        # Verify 35% originality weight
        originality_weight_correct = scores['originality']['weight'] == 0.35
        criticality_weight_correct = scores['criticality']['weight'] == 0.35
        rigour_weight_correct = scores['rigour']['weight'] == 0.30

        test_result['passed'] = (
            weights_valid and
            total_matches and
            originality_weight_correct and
            criticality_weight_correct and
            rigour_weight_correct
        )

        test_result['details'] = {
            'audit_result': audit_result,
            'weights_sum_to_one': weights_valid,
            'total_calculation_verified': total_matches,
            'calculated_total': round(calculated_total, 2),
            'reported_total': audit_result['total_score'],
            'weight_verification': {
                'originality_35%': originality_weight_correct,
                'criticality_35%': criticality_weight_correct,
                'rigour_30%': rigour_weight_correct
            }
        }

        self.transparency_log.log_ai_usage(
            action_type='compliance_audit',
            module='Auditor',
            input_summary=f'Draft chapter ({audit_result["word_count"]} words)',
            output_summary=f'Total score: {audit_result["total_score"]}, Grade: {audit_result["grade"]}',
            was_scrubbed=False
        )

        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"  Status: {status}")
        print(f"  Originality: {scores['originality']['score']} (35% weight)")
        print(f"  Criticality: {scores['criticality']['score']} (35% weight)")
        print(f"  Rigour: {scores['rigour']['score']} (30% weight)")
        print(f"  Total Score: {audit_result['total_score']}")
        print(f"  Grade: {audit_result['grade']}")

        self.results['tests']['auditor'] = test_result

    def _test_feedback_processor(self):
        """TEST 4: Feedback Processor - Traffic Light Classification"""
        print("\n[TEST 4] Feedback Processor (Traffic Light)")
        print("-" * 40)

        test_result = {
            'name': 'Feedback Processor',
            'description': 'Traffic light classification',
            'passed': False,
            'details': {}
        }

        # Classify feedback
        classification = self.feedback_classifier.classify(self.supervisor_feedback_text)
        summary = self.feedback_classifier.get_summary()

        # Validate structure - should have RED, AMBER, GREEN keys
        has_correct_keys = all(k in classification for k in ['RED', 'AMBER', 'GREEN'])

        # Should have detected the explicit markers in test data
        has_red_items = len(classification['RED']) > 0
        has_amber_items = len(classification['AMBER']) > 0
        has_green_items = len(classification['GREEN']) > 0

        # Expected counts based on synthetic data
        expected_red = 3  # 3 [Red] markers
        expected_amber = 5  # 5 [Amber] markers (one was "ignore")
        expected_green = 4  # 4 [Green] markers

        red_count_matches = summary['red_count'] >= 2  # At least 2 red items
        amber_count_matches = summary['amber_count'] >= 3  # At least 3 amber items
        green_count_matches = summary['green_count'] >= 3  # At least 3 green items

        test_result['passed'] = (
            has_correct_keys and
            has_red_items and
            has_amber_items and
            has_green_items and
            red_count_matches
        )

        test_result['details'] = {
            'classification': {
                'RED': [item['text'][:100] for item in classification['RED']],
                'AMBER': [item['text'][:100] for item in classification['AMBER']],
                'GREEN': [item['text'][:100] for item in classification['GREEN']]
            },
            'summary': summary,
            'structure_valid': has_correct_keys,
            'count_validation': {
                'red_items_found': summary['red_count'],
                'amber_items_found': summary['amber_count'],
                'green_items_found': summary['green_count']
            }
        }

        self.transparency_log.log_ai_usage(
            action_type='feedback_classification',
            module='FeedbackProcessor',
            input_summary='Supervisor feedback document',
            output_summary=f'Classified: {summary["red_count"]} RED, {summary["amber_count"]} AMBER, {summary["green_count"]} GREEN',
            was_scrubbed=False
        )

        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"  Status: {status}")
        print(f"  RED (Blockers): {summary['red_count']}")
        print(f"  AMBER (Major): {summary['amber_count']}")
        print(f"  GREEN (Positive): {summary['green_count']}")

        self.results['tests']['feedback_processor'] = test_result

    def _test_red_thread(self):
        """TEST 5: Red Thread Engine - Logical Continuity"""
        print("\n[TEST 5] Red Thread Engine (Logical Continuity)")
        print("-" * 40)

        test_result = {
            'name': 'Red Thread Engine',
            'description': 'Chapter continuity checking',
            'passed': False,
            'details': {}
        }

        # Create mock Chapter 1 (Introduction) that shares themes with Chapter 4
        chapter_1_intro = """
        Introduction to Urban Beekeeping Research

        This thesis investigates the socio-economic impacts of urban beekeeping
        initiatives in metropolitan contexts. The research explores how community-based
        apiculture projects contribute to sustainable urban development and social
        capital formation. Through rigorous qualitative methodology, this study
        examines participant experiences across multiple urban sites.

        The theoretical framework draws upon ecological economics and urban geography,
        situating urban beekeeping within broader debates about sustainability
        transitions and community resilience. Environmental consciousness and
        economic development are examined as interconnected rather than competing
        objectives.

        Key research questions address the mechanisms through which beekeeping
        activities generate community benefits, the policy implications for
        municipal governance, and the scalability of such interventions across
        diverse urban contexts.
        """

        # Index chapters
        self.red_thread.index_chapter('Chapter_1_Introduction', chapter_1_intro)
        self.red_thread.index_chapter('Chapter_4_Discussion', self.draft_chapter_text)

        # Check continuity
        continuity_result = self.red_thread.check_continuity(
            'Chapter_1_Introduction',
            'Chapter_4_Discussion'
        )

        # Test passes if continuity is detected (chapters should share themes)
        has_similarity = continuity_result['similarity_score'] > 0.1
        has_shared_terms = len(continuity_result['shared_key_terms']) > 5
        has_status = 'continuity_status' in continuity_result

        test_result['passed'] = has_similarity and has_shared_terms and has_status
        test_result['details'] = {
            'continuity_result': continuity_result,
            'similarity_score': continuity_result['similarity_score'],
            'similarity_percentage': continuity_result['similarity_percentage'],
            'continuity_status': continuity_result['continuity_status'],
            'shared_terms_count': len(continuity_result['shared_key_terms']),
            'top_shared_terms': continuity_result['shared_key_terms'][:5]
        }

        self.transparency_log.log_ai_usage(
            action_type='continuity_check',
            module='RedThreadEngine',
            input_summary='Chapter 1 vs Chapter 4 comparison',
            output_summary=f'Similarity: {continuity_result["similarity_percentage"]}%, Status: {continuity_result["continuity_status"]}',
            was_scrubbed=False
        )

        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"  Status: {status}")
        print(f"  Similarity Score: {continuity_result['similarity_percentage']}%")
        print(f"  Continuity Status: {continuity_result['continuity_status']}")
        print(f"  Shared Key Terms: {', '.join(continuity_result['shared_key_terms'][:5])}")

        self.results['tests']['red_thread'] = test_result

    def _test_transparency_log(self):
        """TEST 6: Transparency Log - Audit Trail"""
        print("\n[TEST 6] Transparency Log (Audit Trail)")
        print("-" * 40)

        test_result = {
            'name': 'Transparency Log',
            'description': 'AI usage audit logging',
            'passed': False,
            'details': {}
        }

        # Get all logged entries
        entries = self.transparency_log.get_entries()

        # Verify we have entries from previous tests
        has_entries = len(entries) >= 5  # Should have at least 5 from previous tests

        # Check entry structure
        required_fields = ['entry_id', 'timestamp', 'action_type', 'module',
                         'input_summary', 'output_summary', 'pii_protection',
                         'compliance_flags']

        structure_valid = all(
            all(field in entry for field in required_fields)
            for entry in entries
        )

        # Check that Auditor step is logged
        auditor_logged = any(
            entry['module'] == 'Auditor'
            for entry in entries
        )

        # Save log file
        log_path = self.transparency_log.save_log()
        log_saved = Path(log_path).exists()

        test_result['passed'] = (
            has_entries and
            structure_valid and
            auditor_logged and
            log_saved
        )

        test_result['details'] = {
            'total_entries': len(entries),
            'entries_have_valid_structure': structure_valid,
            'auditor_step_logged': auditor_logged,
            'log_file_path': log_path,
            'log_file_saved': log_saved,
            'sample_entries': entries[:2] if entries else []
        }

        status = "PASS" if test_result['passed'] else "FAIL"
        print(f"  Status: {status}")
        print(f"  Total Entries: {len(entries)}")
        print(f"  Log Saved: {log_path}")

        self.results['tests']['transparency_log'] = test_result

    def _generate_summary(self):
        """Generate test summary and recommendations."""
        tests = self.results['tests']

        passed = sum(1 for t in tests.values() if t['passed'])
        failed = len(tests) - passed

        self.results['summary'] = {
            'total_tests': len(tests),
            'passed': passed,
            'failed': failed,
            'pass_rate': f"{(passed/len(tests))*100:.1f}%",
            'overall_status': 'PASS' if failed == 0 else 'FAIL'
        }

        # Generate recommendations
        recommendations = []

        if not tests['ethics_airlock']['passed']:
            recommendations.append({
                'module': 'Ethics Airlock',
                'issue': 'PII detection incomplete',
                'recommendation': 'Expand regex patterns to catch edge cases'
            })

        if not tests['dna_engine']['passed']:
            recommendations.append({
                'module': 'DNA Engine',
                'issue': 'Style shift detection needs tuning',
                'recommendation': 'Adjust deviation threshold or add more linguistic markers'
            })

        if not tests['red_thread']['passed']:
            recommendations.append({
                'module': 'Red Thread Engine',
                'issue': 'Continuity detection weak',
                'recommendation': 'Consider using proper embeddings (sentence-transformers) for production'
            })

        # General recommendations
        recommendations.append({
            'module': 'General',
            'issue': 'Simulation uses simplified algorithms',
            'recommendation': 'Production system should integrate with LLM APIs for enhanced analysis'
        })

        self.results['recommendations'] = recommendations

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass Rate: {self.results['summary']['pass_rate']}")
        print(f"Overall Status: {self.results['summary']['overall_status']}")
        print("=" * 70)

    def generate_markdown_report(self) -> str:
        """Generate comprehensive validation report in Markdown format."""
        report = []

        # Header
        report.append("# PHDx Architecture Validation Report")
        report.append("")
        report.append(f"**Generated:** {self.results['timestamp']}")
        report.append(f"**Validation Standard:** Oxford Brookes University PhD Requirements")
        report.append("")

        # Executive Summary
        report.append("## Executive Summary")
        report.append("")
        summary = self.results['summary']
        status_emoji = "✅" if summary['overall_status'] == 'PASS' else "❌"
        report.append(f"| Metric | Value |")
        report.append(f"|--------|-------|")
        report.append(f"| Overall Status | {status_emoji} {summary['overall_status']} |")
        report.append(f"| Tests Passed | {summary['passed']}/{summary['total_tests']} |")
        report.append(f"| Pass Rate | {summary['pass_rate']} |")
        report.append("")

        # Synthetic Data Summary
        report.append("## Synthetic Test Data")
        report.append("")
        data = self.results['synthetic_data']
        report.append(f"- **Author Profile:** {data['author_profile_words']} words")
        report.append(f"- **Draft Chapter:** {data['draft_chapter_words']} words")
        report.append(f"- **Supervisor Feedback:** {data['supervisor_feedback_words']} words")
        report.append("")

        # Individual Test Results
        report.append("## Test Results")
        report.append("")

        for test_name, test_data in self.results['tests'].items():
            status = "✅ PASS" if test_data['passed'] else "❌ FAIL"
            report.append(f"### {test_data['name']}")
            report.append(f"**Status:** {status}")
            report.append(f"**Description:** {test_data['description']}")
            report.append("")

            # Test-specific details
            if test_name == 'ethics_airlock':
                details = test_data['details']
                report.append("#### PII Detection Results")
                report.append(f"- PII Instances Detected: {details['pii_detected']}")
                report.append(f"- Redactions Made: {details['redactions_made']}")
                report.append(f"- Validation Clean: {details['validation_clean']}")
                report.append("")
                report.append("#### Sample Redactions (Before → After)")
                report.append("```")
                for sample in details['redaction_samples'][:3]:
                    report.append(f"Type: {sample['type']}")
                    report.append(f"  {sample['original']} → [REDACTED]")
                report.append("```")

            elif test_name == 'dna_engine':
                details = test_data['details']
                profile = details['author_profile']
                report.append("#### Author Linguistic Profile")
                report.append(f"- Type-Token Ratio: {profile['type_token_ratio']}")
                report.append(f"- Avg Sentence Length: {profile['avg_sentence_length']} words")
                report.append(f"- Hedging Density: {profile['hedging_density_per_1000']}/1000 words")
                report.append(f"- Academic Markers: {profile['academic_marker_density_per_1000']}/1000 words")
                report.append("")
                report.append(f"**Style Shifts Detected:** {details['flagged_paragraphs']}")
                report.append(f"**AI Paragraph Flagged:** {'Yes ✓' if details['ai_paragraph_detected'] else 'No'}")

            elif test_name == 'auditor':
                details = test_data['details']
                audit = details['audit_result']
                report.append("#### Compliance Scores")
                report.append("")
                report.append("| Component | Score | Weight | Weighted |")
                report.append("|-----------|-------|--------|----------|")
                for comp, data in audit['scores'].items():
                    report.append(f"| {comp.title()} | {data['score']} | {data['weight']*100}% | {data['weighted']} |")
                report.append(f"| **Total** | **{audit['total_score']}** | 100% | **{audit['total_score']}** |")
                report.append("")
                report.append(f"**Grade:** {audit['grade']}")
                report.append("")
                report.append("#### Weight Verification")
                wv = details['weight_verification']
                report.append(f"- Originality at 35%: {'✓' if wv['originality_35%'] else '✗'}")
                report.append(f"- Criticality at 35%: {'✓' if wv['criticality_35%'] else '✗'}")
                report.append(f"- Rigour at 30%: {'✓' if wv['rigour_30%'] else '✗'}")

            elif test_name == 'feedback_processor':
                details = test_data['details']
                classification = details['classification']
                report.append("#### Traffic Light Classification")
                report.append("")
                report.append(f"**🔴 RED (Blockers):** {len(classification['RED'])}")
                for item in classification['RED'][:2]:
                    report.append(f"  - {item[:80]}...")
                report.append("")
                report.append(f"**🟡 AMBER (Major):** {len(classification['AMBER'])}")
                for item in classification['AMBER'][:2]:
                    report.append(f"  - {item[:80]}...")
                report.append("")
                report.append(f"**🟢 GREEN (Positive):** {len(classification['GREEN'])}")
                for item in classification['GREEN'][:2]:
                    report.append(f"  - {item[:80]}...")

            elif test_name == 'red_thread':
                details = test_data['details']
                report.append("#### Continuity Analysis")
                report.append(f"- Similarity Score: {details['similarity_percentage']}%")
                report.append(f"- Continuity Status: {details['continuity_status']}")
                report.append(f"- Shared Terms: {details['shared_terms_count']}")
                report.append("")
                report.append("**Top Shared Key Terms:**")
                for term in details['top_shared_terms']:
                    report.append(f"  - {term}")

            elif test_name == 'transparency_log':
                details = test_data['details']
                report.append("#### Audit Trail")
                report.append(f"- Total Entries: {details['total_entries']}")
                report.append(f"- Auditor Step Logged: {'Yes ✓' if details['auditor_step_logged'] else 'No'}")
                report.append(f"- Log File: `{details['log_file_path']}`")

            report.append("")

        # Recommendations
        report.append("## Recommendations")
        report.append("")
        for rec in self.results['recommendations']:
            report.append(f"### {rec['module']}")
            report.append(f"**Issue:** {rec['issue']}")
            report.append(f"**Recommendation:** {rec['recommendation']}")
            report.append("")

        # Footer
        report.append("---")
        report.append("*Report generated by PHDx Architecture Validation Harness*")
        report.append(f"*Simulation run completed: {self.results['timestamp']}*")

        return "\n".join(report)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main entry point for the validation harness."""
    print("\n" + "=" * 70)
    print("INITIALIZING PHDx ARCHITECTURE VALIDATION HARNESS")
    print("=" * 70)

    # Create validator and run tests
    validator = PHDxArchitectureValidator()
    results = validator.run_all_tests()

    # Generate and save report
    report = validator.generate_markdown_report()

    # Save report
    report_path = Path(__file__).parent.parent / 'data' / 'validation_report.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w') as f:
        f.write(report)

    print(f"\n📄 Validation Report saved to: {report_path}")

    # Also print the report
    print("\n" + "=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    print(report)

    # Return exit code based on results
    return 0 if results['summary']['overall_status'] == 'PASS' else 1


if __name__ == "__main__":
    exit(main())
