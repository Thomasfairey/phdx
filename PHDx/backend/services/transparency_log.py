"""
TransparencyLog Service - Audit Logging

Implements the verified simulation logic for audit logging.
Uses a class-level list to simulate a persistent database
that survives across different user sessions.
"""

import logging
from datetime import datetime
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransparencyLog:
    """
    Audit logging service for PHDx transparency compliance.

    SIMULATION CONSTRAINT: Uses a class-level list to simulate a
    persistent database that survives across different user sessions.
    """

    # Class-level persistent storage (as per simulation spec)
    _persistent_db: List[Dict] = []

    def log_event(self, module: str, action: str, status: str) -> Dict:
        """
        Log an audit event.

        Args:
            module: Name of the module generating the event
            action: Description of the action being performed
            status: Status/outcome of the action

        Returns:
            The created log entry
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "action": action,
            "status": status
        }
        TransparencyLog._persistent_db.append(entry)
        logger.info(f"AUDIT LOG: [{module}] {action} - {status}")
        return entry

    def get_logs(self) -> List[Dict]:
        """
        Retrieve all audit logs.

        Returns:
            List of all log entries
        """
        return TransparencyLog._persistent_db

    def clear_logs(self) -> None:
        """Clear all logs (useful for testing)."""
        TransparencyLog._persistent_db.clear()

    def get_logs_by_module(self, module: str) -> List[Dict]:
        """
        Get logs filtered by module name.

        Args:
            module: Module name to filter by

        Returns:
            List of matching log entries
        """
        return [
            log for log in TransparencyLog._persistent_db
            if log["module"] == module
        ]

    def get_logs_by_status(self, status: str) -> List[Dict]:
        """
        Get logs filtered by status.

        Args:
            status: Status to filter by

        Returns:
            List of matching log entries
        """
        return [
            log for log in TransparencyLog._persistent_db
            if log["status"] == status
        ]


# Singleton instance for dependency injection
_transparency_log_instance: TransparencyLog = None


def get_transparency_log() -> TransparencyLog:
    """Get or create the TransparencyLog singleton instance."""
    global _transparency_log_instance
    if _transparency_log_instance is None:
        _transparency_log_instance = TransparencyLog()
    return _transparency_log_instance
