"""
DNAEngine Service - Linguistic Fingerprint Analysis

Implements the verified simulation logic for writing style analysis.
Uses exact variance formula from the simulation constraint.
"""

from typing import Dict

from .transparency_log import TransparencyLog, get_transparency_log


class DNAEngine:
    """
    Writing style analysis service using sentence variance.

    SIMULATION CONSTRAINT: Uses exact variance formula:
    variance = sum((x - mean)^2 for x in lengths) / len(lengths)

    Style match is determined by comparing variance to baseline - 5.0
    """

    def __init__(self, logger: TransparencyLog = None):
        """
        Initialize the DNAEngine.

        Args:
            logger: TransparencyLog instance for audit logging
        """
        self.logger = logger or get_transparency_log()
        self.author_baseline_variance = 15.0

    def analyze_style(self, text: str, baseline_variance: float = None) -> Dict[str, float]:
        """
        Analyze writing style by calculating sentence length variance.

        EXACT LOGIC from simulation:
        1. Split text by periods into sentences
        2. Count words per sentence (excluding empty)
        3. Calculate mean sentence length
        4. Calculate variance: sum((x - mean)^2) / n
        5. Compare to baseline - 5.0 threshold

        Args:
            text: Text to analyze
            baseline_variance: Optional custom baseline (defaults to 15.0)

        Returns:
            Dictionary with variance, style_match, and status
        """
        if baseline_variance is not None:
            self.author_baseline_variance = baseline_variance

        # Split by periods (exact simulation logic)
        sentences = text.split('.')

        # Get word counts for non-empty sentences
        lengths = [len(s.split()) for s in sentences if s.strip()]

        # Handle edge case: no valid sentences
        if not lengths:
            return {"variance": 0, "style_match": False, "status": "FAIL"}

        # Calculate mean (exact formula)
        mean = sum(lengths) / len(lengths)

        # Calculate variance (exact formula from simulation)
        variance = sum((x - mean) ** 2 for x in lengths) / len(lengths)

        # Determine style match (exact threshold from simulation)
        is_consistent_style = variance >= (self.author_baseline_variance - 5.0)

        # Log the analysis
        status = "MATCH" if is_consistent_style else "ANOMALY_DETECTED"
        self.logger.log_event("DNA_Engine", "Style Analysis", status)

        return {
            "variance": variance,
            "style_match": is_consistent_style,
            "status": status
        }

    def set_baseline(self, variance: float) -> None:
        """
        Update the author baseline variance.

        Args:
            variance: New baseline variance value
        """
        self.author_baseline_variance = variance

    def get_baseline(self) -> float:
        """Get the current baseline variance."""
        return self.author_baseline_variance


# Singleton instance for dependency injection
_dna_engine_instance: DNAEngine = None


def get_dna_engine() -> DNAEngine:
    """Get or create the DNAEngine singleton instance."""
    global _dna_engine_instance
    if _dna_engine_instance is None:
        _dna_engine_instance = DNAEngine()
    return _dna_engine_instance
