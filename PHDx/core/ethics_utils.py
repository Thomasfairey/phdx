"""
Ethics Utilities - Data Anonymization for PHDx

This module provides anonymization functions to strip personally identifiable
information (PII) from text before sending to LLMs, ensuring ethical AI usage.

Uses both regex patterns and spaCy NER for comprehensive anonymization.
"""

import csv
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
AI_USAGE_LOG = DATA_DIR / "ai_usage_log.csv"


# =============================================================================
# REGEX PATTERNS FOR PII DETECTION
# =============================================================================

PII_PATTERNS = {
    "email": re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    ),
    "phone_uk": re.compile(
        r'\+44\s?\d{4}\s?\d{6}|\+44\s?\d{3}\s?\d{3}\s?\d{4}|07\d{3}\s?\d{6}|07\d{3}\s?\d{3}\s?\d{3}'
    ),
    "phone_us": re.compile(
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    ),
    "phone_intl": re.compile(
        r'\b\+[1-9]\d{1,2}[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{2,4}\b'
    ),
    "uk_postcode": re.compile(
        r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',
        re.IGNORECASE
    ),
    "national_insurance": re.compile(
        r'\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b',
        re.IGNORECASE
    ),
    "credit_card": re.compile(
        r'\b(?:\d{4}[\s-]?){3}\d{4}\b'
    ),
    "ip_address": re.compile(
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ),
    "url": re.compile(
        r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*'
    ),
    "date_of_birth": re.compile(
        r'\b(?:DOB|D\.O\.B\.?|Date of Birth)[:\s]*\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b',
        re.IGNORECASE
    ),
    "student_id": re.compile(
        r'\b(?:Student\s*(?:ID|Number)|ID\s*Number)[:\s]*\d{6,10}\b',
        re.IGNORECASE
    )
}

# Replacement tokens
PII_REPLACEMENTS = {
    "email": "[EMAIL_REDACTED]",
    "phone_uk": "[PHONE_REDACTED]",
    "phone_us": "[PHONE_REDACTED]",
    "phone_intl": "[PHONE_REDACTED]",
    "uk_postcode": "[POSTCODE_REDACTED]",
    "national_insurance": "[NI_NUMBER_REDACTED]",
    "credit_card": "[CARD_REDACTED]",
    "ip_address": "[IP_REDACTED]",
    "url": "[URL_REDACTED]",
    "date_of_birth": "[DOB_REDACTED]",
    "student_id": "[STUDENT_ID_REDACTED]"
}


class EthicsScrubber:
    """
    Anonymizes text by removing personally identifiable information.

    Uses regex patterns for structured PII and optionally spaCy NER
    for named entity recognition (names, organizations, locations).
    """

    def __init__(self, use_spacy: bool = True):
        """
        Initialize the ethics scrubber.

        Args:
            use_spacy: Whether to use spaCy for NER-based anonymization
        """
        self.use_spacy = use_spacy
        self.nlp = None
        self._load_spacy()

    def _load_spacy(self):
        """Load spaCy model for NER."""
        if not self.use_spacy:
            return

        try:
            import spacy
            # Try to load the model, download if not available
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Downloading spaCy model...")
                from spacy.cli import download
                download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
        except ImportError:
            print("spaCy not available. Using regex-only anonymization.")
            self.use_spacy = False

    def scrub_regex(self, text: str) -> tuple[str, dict]:
        """
        Remove PII using regex patterns.

        Args:
            text: Input text to scrub

        Returns:
            Tuple of (scrubbed_text, scrub_report)
        """
        scrubbed = text
        report = {
            "method": "regex",
            "items_found": {},
            "total_redactions": 0
        }

        for pii_type, pattern in PII_PATTERNS.items():
            matches = pattern.findall(scrubbed)
            if matches:
                report["items_found"][pii_type] = len(matches)
                report["total_redactions"] += len(matches)
                scrubbed = pattern.sub(PII_REPLACEMENTS[pii_type], scrubbed)

        return scrubbed, report

    def scrub_names_spacy(self, text: str) -> tuple[str, dict]:
        """
        Remove names and entities using spaCy NER.

        Args:
            text: Input text to scrub

        Returns:
            Tuple of (scrubbed_text, scrub_report)
        """
        if not self.nlp:
            return text, {"method": "spacy", "error": "spaCy not loaded"}

        doc = self.nlp(text)
        scrubbed = text
        report = {
            "method": "spacy_ner",
            "entities_found": {},
            "total_redactions": 0
        }

        # Entity types to redact
        redact_types = {
            "PERSON": "[NAME_REDACTED]",
            "ORG": "[ORG_REDACTED]",
            "GPE": "[LOCATION_REDACTED]",  # Geopolitical entity
            "LOC": "[LOCATION_REDACTED]",
            "FAC": "[FACILITY_REDACTED]",
            "NORP": "[GROUP_REDACTED]"  # Nationalities, religious, political groups
        }

        # Sort entities by start position (reverse) to replace from end
        entities = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)

        for ent in entities:
            if ent.label_ in redact_types:
                # Count entities
                if ent.label_ not in report["entities_found"]:
                    report["entities_found"][ent.label_] = 0
                report["entities_found"][ent.label_] += 1
                report["total_redactions"] += 1

                # Replace in text
                replacement = redact_types[ent.label_]
                scrubbed = scrubbed[:ent.start_char] + replacement + scrubbed[ent.end_char:]

        return scrubbed, report

    def scrub(self, text: str, include_names: bool = True) -> dict:
        """
        Full anonymization pipeline.

        Args:
            text: Input text to scrub
            include_names: Whether to use spaCy for name detection

        Returns:
            dict with scrubbed_text, original_length, scrubbed_length, reports
        """
        result = {
            "original_text": text,
            "original_length": len(text),
            "scrubbed_text": text,
            "scrubbed_length": 0,
            "is_clean": True,
            "reports": [],
            "total_redactions": 0,
            "timestamp": datetime.now().isoformat()
        }

        # Step 1: Regex-based scrubbing
        scrubbed, regex_report = self.scrub_regex(text)
        result["reports"].append(regex_report)
        result["total_redactions"] += regex_report["total_redactions"]

        # Step 2: spaCy NER-based scrubbing (optional)
        if include_names and self.use_spacy:
            scrubbed, spacy_report = self.scrub_names_spacy(scrubbed)
            result["reports"].append(spacy_report)
            result["total_redactions"] += spacy_report["total_redactions"]

        result["scrubbed_text"] = scrubbed
        result["scrubbed_length"] = len(scrubbed)
        result["is_clean"] = result["total_redactions"] == 0

        return result

    def quick_scrub(self, text: str) -> str:
        """
        Quick anonymization returning only the scrubbed text.

        Args:
            text: Input text to scrub

        Returns:
            Scrubbed text string
        """
        result = self.scrub(text)
        return result["scrubbed_text"]


# =============================================================================
# AI USAGE LOGGING
# =============================================================================

class AIUsageLedger:
    """
    Logs all AI interactions for audit trail and ethical compliance.

    Tracks: timestamp, action type, data source, prompt used, token estimate
    """

    def __init__(self, log_path: Path = AI_USAGE_LOG):
        """
        Initialize the usage ledger.

        Args:
            log_path: Path to the CSV log file
        """
        self.log_path = log_path
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        """Create log file with headers if it doesn't exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.log_path.exists():
            with open(self.log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "action_type",
                    "data_source",
                    "prompt_preview",
                    "prompt_length",
                    "was_scrubbed",
                    "redactions_count",
                    "model_used",
                    "session_id"
                ])

    def log(
        self,
        action_type: str,
        data_source: str,
        prompt: str,
        was_scrubbed: bool = False,
        redactions_count: int = 0,
        model_used: str = "claude-sonnet-4-20250514",
        session_id: str = ""
    ):
        """
        Log an AI usage event.

        Args:
            action_type: Type of action (e.g., "generate_draft", "audit", "consistency_check")
            data_source: Source of input data (e.g., "user_input", "google_sheets", "drafts_folder")
            prompt: The prompt sent to the AI (will be truncated in log)
            was_scrubbed: Whether the input was ethics-scrubbed
            redactions_count: Number of PII items redacted
            model_used: AI model identifier
            session_id: Optional session identifier
        """
        # Truncate prompt for log (first 200 chars)
        prompt_preview = prompt[:200].replace('\n', ' ').replace(',', ';')
        if len(prompt) > 200:
            prompt_preview += "..."

        with open(self.log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                action_type,
                data_source,
                prompt_preview,
                len(prompt),
                was_scrubbed,
                redactions_count,
                model_used,
                session_id or "default"
            ])

    def get_recent_logs(self, limit: int = 10) -> list[dict]:
        """
        Get recent log entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of log entry dictionaries
        """
        if not self.log_path.exists():
            return []

        entries = []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)

        return entries[-limit:]

    def get_stats(self) -> dict:
        """
        Get usage statistics.

        Returns:
            dict with usage statistics
        """
        if not self.log_path.exists():
            return {"total_calls": 0, "by_action": {}}

        stats = {
            "total_calls": 0,
            "by_action": {},
            "by_source": {},
            "scrubbed_percentage": 0,
            "total_redactions": 0
        }

        scrubbed_count = 0

        with open(self.log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["total_calls"] += 1

                action = row.get("action_type", "unknown")
                stats["by_action"][action] = stats["by_action"].get(action, 0) + 1

                source = row.get("data_source", "unknown")
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

                if row.get("was_scrubbed") == "True":
                    scrubbed_count += 1

                stats["total_redactions"] += int(row.get("redactions_count", 0))

        if stats["total_calls"] > 0:
            stats["scrubbed_percentage"] = round(scrubbed_count / stats["total_calls"] * 100, 1)

        return stats


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

# Global scrubber instance
_scrubber = None

def get_scrubber() -> EthicsScrubber:
    """Get or create the global ethics scrubber instance."""
    global _scrubber
    if _scrubber is None:
        _scrubber = EthicsScrubber(use_spacy=True)
    return _scrubber


# Global ledger instance
_ledger = None

def get_ledger() -> AIUsageLedger:
    """Get or create the global AI usage ledger instance."""
    global _ledger
    if _ledger is None:
        _ledger = AIUsageLedger()
    return _ledger


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def scrub_text(text: str, include_names: bool = True) -> dict:
    """
    Convenience function to scrub text.

    Args:
        text: Text to anonymize
        include_names: Whether to use spaCy NER for names

    Returns:
        Scrub result dict
    """
    return get_scrubber().scrub(text, include_names)


def quick_scrub(text: str) -> str:
    """
    Quick anonymization returning only scrubbed text.

    Args:
        text: Text to anonymize

    Returns:
        Anonymized text string
    """
    return get_scrubber().quick_scrub(text)


def log_ai_usage(
    action_type: str,
    data_source: str,
    prompt: str,
    was_scrubbed: bool = False,
    redactions_count: int = 0
):
    """
    Log an AI usage event.

    Args:
        action_type: Type of action
        data_source: Source of data
        prompt: The prompt used
        was_scrubbed: Whether input was scrubbed
        redactions_count: Number of redactions
    """
    get_ledger().log(
        action_type=action_type,
        data_source=data_source,
        prompt=prompt,
        was_scrubbed=was_scrubbed,
        redactions_count=redactions_count
    )


def get_usage_stats() -> dict:
    """Get AI usage statistics."""
    return get_ledger().get_stats()


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Ethics Utilities - Anonymization & Logging")
    print("=" * 60)

    # Demo text with PII
    demo_text = """
    Dear Dr. John Smith,

    Thank you for your email at j.smith@oxford.ac.uk regarding the research project.
    My phone number is +44 7700 900123 and I live at OX1 2AB.

    Please contact Sarah Johnson at sarah.j@brookes.ac.uk for more details.
    My student ID is 12345678.

    Best regards,
    Thomas Fairey
    """

    print("\n[1] Original Text:")
    print(demo_text)

    print("\n[2] Scrubbing PII...")
    scrubber = EthicsScrubber(use_spacy=True)
    result = scrubber.scrub(demo_text)

    print("\n[3] Scrubbed Text:")
    print(result["scrubbed_text"])

    print("\n[4] Scrub Report:")
    print(f"  Total redactions: {result['total_redactions']}")
    for report in result["reports"]:
        print(f"  Method: {report['method']}")
        if "items_found" in report:
            for item_type, count in report["items_found"].items():
                print(f"    - {item_type}: {count}")
        if "entities_found" in report:
            for ent_type, count in report["entities_found"].items():
                print(f"    - {ent_type}: {count}")

    print("\n[5] Logging demo AI usage...")
    log_ai_usage(
        action_type="demo",
        data_source="cli_test",
        prompt="Demo prompt for testing",
        was_scrubbed=True,
        redactions_count=result["total_redactions"]
    )
    print(f"  Log file: {AI_USAGE_LOG}")

    print("\n" + "=" * 60)
