"""
FeedbackProcessor Service - Traffic Light Categorization

Implements the verified simulation logic for feedback categorization.
Uses exact keyword matching: blocker -> RED, consider -> AMBER, typo -> GREEN
"""

from typing import Dict, List


class FeedbackProcessor:
    """
    Feedback categorization service using traffic light system.

    SIMULATION CONSTRAINT: Uses exact keyword matching:
    - "blocker" (case-insensitive) -> RED
    - "consider" (case-insensitive) -> AMBER
    - "typo" (case-insensitive) -> GREEN
    """

    def process(self, text: str) -> Dict[str, List[str]]:
        """
        Process and categorize feedback text.

        EXACT LOGIC from simulation:
        1. Split text by newlines
        2. For each line:
           - If "blocker" in line (case-insensitive) -> RED
           - Elif "consider" in line (case-insensitive) -> AMBER
           - Elif "typo" in line (case-insensitive) -> GREEN

        Args:
            text: Feedback text with items separated by newlines

        Returns:
            Dictionary with RED, AMBER, GREEN lists
        """
        categories = {
            "RED": [],
            "AMBER": [],
            "GREEN": []
        }

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            line_lower = line.lower()

            # Exact matching logic from simulation (order matters!)
            if "blocker" in line_lower:
                categories["RED"].append(line)
            elif "consider" in line_lower:
                categories["AMBER"].append(line)
            elif "typo" in line_lower:
                categories["GREEN"].append(line)

        return categories

    def count_by_category(self, categories: Dict[str, List[str]]) -> Dict[str, int]:
        """
        Count items in each category.

        Args:
            categories: Categorized feedback dictionary

        Returns:
            Dictionary with counts per category
        """
        return {
            category: len(items)
            for category, items in categories.items()
        }

    def get_priority_items(self, categories: Dict[str, List[str]]) -> List[str]:
        """
        Get items that need immediate attention (RED category).

        Args:
            categories: Categorized feedback dictionary

        Returns:
            List of RED (blocker) items
        """
        return categories.get("RED", [])


# Singleton instance for dependency injection
_processor_instance: FeedbackProcessor = None


def get_feedback_processor() -> FeedbackProcessor:
    """Get or create the FeedbackProcessor singleton instance."""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = FeedbackProcessor()
    return _processor_instance
