"""
EthicsAirlock Service - PII Detection and Sanitization

Implements the verified simulation logic for PII scrubbing.
Uses exact regex patterns from the simulation constraint.
"""

import re
from typing import Tuple, Dict

from .transparency_log import TransparencyLog, get_transparency_log


class EthicsAirlock:
    """
    PII detection and sanitization service.

    SIMULATION CONSTRAINT: Uses exact regex patterns from simulation:
    - email: Standard email pattern
    - phone: UK mobile format (+44 or 0 prefix)
    - names: Participant identifiers with CamelCase and hyphens support
    """

    def __init__(self, logger: TransparencyLog = None):
        """
        Initialize the EthicsAirlock.

        Args:
            logger: TransparencyLog instance for audit logging
        """
        self.logger = logger or get_transparency_log()

        # EXACT PII patterns from simulation (DO NOT MODIFY)
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'((?:\+44|0)7\d{9})',
            # LOGIC FIX: Updated regex to handle CamelCase (JohnDoe) and hyphens
            "names": r'\b(Participant [a-zA-Z0-9_-]+)\b'
        }

    def sanitize(self, text: str) -> Tuple[str, bool]:
        """
        Sanitize text by detecting and redacting PII.

        EXACT LOGIC from simulation:
        1. Check each PII pattern against the text
        2. If found, replace with [REDACTED]
        3. Log event with INTERVENTION_REQUIRED or CLEAN status

        Args:
            text: Text to sanitize

        Returns:
            Tuple of (sanitized_text, pii_found)
        """
        sanitized_text = text
        pii_found = False

        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, sanitized_text):
                pii_found = True
                sanitized_text = re.sub(pattern, "[REDACTED]", sanitized_text)

        status = "INTERVENTION_REQUIRED" if pii_found else "CLEAN"
        self.logger.log_event("Airlock", "PII Scrubbing", status)

        return sanitized_text, pii_found

    def detect_pii(self, text: str) -> Dict[str, list]:
        """
        Detect PII without redacting (for analysis purposes).

        Args:
            text: Text to analyze

        Returns:
            Dictionary of detected PII by type
        """
        detected = {}
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                detected[pii_type] = matches
        return detected

    def get_patterns(self) -> Dict[str, str]:
        """Return the PII patterns being used."""
        return self.pii_patterns.copy()


# Singleton instance for dependency injection
_airlock_instance: EthicsAirlock = None


def get_ethics_airlock() -> EthicsAirlock:
    """Get or create the EthicsAirlock singleton instance."""
    global _airlock_instance
    if _airlock_instance is None:
        _airlock_instance = EthicsAirlock()
    return _airlock_instance
