"""
Auditor Service - Compliance Scoring

Implements the verified simulation logic for weighted scoring.
Uses exact weights: Originality 35%, Criticality 35%, Rigour 30%
"""

from typing import Dict

from .transparency_log import TransparencyLog, get_transparency_log


class Auditor:
    """
    Compliance scoring service using weighted criteria.

    SIMULATION CONSTRAINT: Uses exact weights:
    - Originality: 0.35 (35%)
    - Criticality: 0.35 (35%)
    - Rigour: 0.30 (30%)

    Total must sum to 1.0 (100%)
    """

    def __init__(self, logger: TransparencyLog = None):
        """
        Initialize the Auditor.

        Args:
            logger: TransparencyLog instance for audit logging
        """
        self.logger = logger or get_transparency_log()

        # EXACT weights from simulation (DO NOT MODIFY)
        self.weights = {
            "Originality": 0.35,
            "Criticality": 0.35,
            "Rigour": 0.30
        }

    def evaluate(self, text: str, mock_scores: Dict[str, int]) -> Dict:
        """
        Evaluate text against compliance criteria.

        EXACT LOGIC from simulation:
        total_score = sum(score * weight for each criterion)

        Args:
            text: Text being evaluated (used for context/logging)
            mock_scores: Dictionary of scores per criterion (0-100)
                        Expected keys: Originality, Criticality, Rigour

        Returns:
            Dictionary with total_weighted_score rounded to 2 decimal places
        """
        # Calculate weighted sum (exact formula from simulation)
        total_score = sum(
            mock_scores.get(k, 0) * v
            for k, v in self.weights.items()
        )

        # Log the evaluation
        self.logger.log_event(
            "Auditor",
            "Compliance Scoring",
            f"Score: {total_score}"
        )

        return {
            "total_weighted_score": round(total_score, 2)
        }

    def get_weights(self) -> Dict[str, float]:
        """Return the scoring weights."""
        return self.weights.copy()

    def validate_scores(self, scores: Dict[str, int]) -> bool:
        """
        Validate that scores contain required criteria.

        Args:
            scores: Score dictionary to validate

        Returns:
            True if all required criteria present, False otherwise
        """
        required = set(self.weights.keys())
        provided = set(scores.keys())
        return required.issubset(provided)


# Singleton instance for dependency injection
_auditor_instance: Auditor = None


def get_auditor() -> Auditor:
    """Get or create the Auditor singleton instance."""
    global _auditor_instance
    if _auditor_instance is None:
        _auditor_instance = Auditor()
    return _auditor_instance
