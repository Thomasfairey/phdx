"""
Unit Tests for PHDx Production Backend Services

These tests verify that the production code implements the EXACT
logic from the simulation constraint. Each test is derived from
the simulation requirements.
"""

import unittest
from ..services.transparency_log import TransparencyLog
from ..services.ethics_airlock import EthicsAirlock
from ..services.dna_engine import DNAEngine
from ..services.auditor import Auditor
from ..services.feedback_processor import FeedbackProcessor


class TestTransparencyLog(unittest.TestCase):
    """Tests for TransparencyLog service."""

    def setUp(self):
        """Set up fresh logger for each test."""
        self.logger = TransparencyLog()
        self.logger.clear_logs()

    def tearDown(self):
        """Clean up after each test."""
        self.logger.clear_logs()

    def test_log_event_creates_entry(self):
        """Test that log_event creates a properly structured entry."""
        entry = self.logger.log_event("TestModule", "TestAction", "SUCCESS")

        self.assertEqual(entry["module"], "TestModule")
        self.assertEqual(entry["action"], "TestAction")
        self.assertEqual(entry["status"], "SUCCESS")
        self.assertIn("timestamp", entry)

    def test_persistent_db_survives_instances(self):
        """SIMULATION CONSTRAINT: Class-level list survives across instances."""
        logger1 = TransparencyLog()
        logger1.clear_logs()
        logger1.log_event("Module1", "Action1", "Status1")

        logger2 = TransparencyLog()
        logs = logger2.get_logs()

        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["module"], "Module1")

    def test_get_logs_returns_all_entries(self):
        """Test that get_logs returns all logged entries."""
        self.logger.log_event("Module1", "Action1", "Status1")
        self.logger.log_event("Module2", "Action2", "Status2")

        logs = self.logger.get_logs()
        self.assertEqual(len(logs), 2)

    def test_filter_by_module(self):
        """Test filtering logs by module name."""
        self.logger.log_event("Airlock", "Action1", "Status1")
        self.logger.log_event("DNA_Engine", "Action2", "Status2")
        self.logger.log_event("Airlock", "Action3", "Status3")

        airlock_logs = self.logger.get_logs_by_module("Airlock")
        self.assertEqual(len(airlock_logs), 2)


class TestEthicsAirlock(unittest.TestCase):
    """Tests for EthicsAirlock service."""

    def setUp(self):
        """Set up airlock for testing."""
        self.logger = TransparencyLog()
        self.logger.clear_logs()
        self.airlock = EthicsAirlock(self.logger)

    def tearDown(self):
        """Clean up after each test."""
        self.logger.clear_logs()

    def test_email_detection_and_redaction(self):
        """SIMULATION CONSTRAINT: Email regex pattern."""
        text = "Contact john.doe@example.com for more info"
        sanitized, pii_found = self.airlock.sanitize(text)

        self.assertTrue(pii_found)
        self.assertNotIn("john.doe@example.com", sanitized)
        self.assertIn("[REDACTED]", sanitized)

    def test_uk_phone_detection_and_redaction(self):
        """SIMULATION CONSTRAINT: UK phone regex ((?:\\+44|0)7\\d{9})."""
        # Test +44 format
        text1 = "Call +447123456789"
        sanitized1, pii_found1 = self.airlock.sanitize(text1)
        self.assertTrue(pii_found1)
        self.assertIn("[REDACTED]", sanitized1)

        # Test 07 format
        text2 = "Call 07123456789"
        sanitized2, pii_found2 = self.airlock.sanitize(text2)
        self.assertTrue(pii_found2)
        self.assertIn("[REDACTED]", sanitized2)

    def test_participant_name_detection(self):
        """SIMULATION CONSTRAINT: Participant name regex with CamelCase and hyphens."""
        # Standard format
        text1 = "Interview with Participant ABC123"
        sanitized1, pii_found1 = self.airlock.sanitize(text1)
        self.assertTrue(pii_found1)

        # CamelCase support (LOGIC FIX from simulation)
        text2 = "Interview with Participant JohnDoe"
        sanitized2, pii_found2 = self.airlock.sanitize(text2)
        self.assertTrue(pii_found2)

        # Hyphen support (LOGIC FIX from simulation)
        text3 = "Interview with Participant John-Doe"
        sanitized3, pii_found3 = self.airlock.sanitize(text3)
        self.assertTrue(pii_found3)

    def test_clean_text_status(self):
        """SIMULATION CONSTRAINT: CLEAN status when no PII found."""
        text = "This is clean text with no personal information"
        sanitized, pii_found = self.airlock.sanitize(text)

        self.assertFalse(pii_found)
        self.assertEqual(sanitized, text)

        # Check audit log
        logs = self.logger.get_logs()
        self.assertEqual(logs[-1]["status"], "CLEAN")

    def test_intervention_required_status(self):
        """SIMULATION CONSTRAINT: INTERVENTION_REQUIRED when PII found."""
        text = "Email: test@test.com"
        self.airlock.sanitize(text)

        logs = self.logger.get_logs()
        self.assertEqual(logs[-1]["status"], "INTERVENTION_REQUIRED")


class TestDNAEngine(unittest.TestCase):
    """Tests for DNAEngine service."""

    def setUp(self):
        """Set up engine for testing."""
        self.logger = TransparencyLog()
        self.logger.clear_logs()
        self.engine = DNAEngine(self.logger)

    def tearDown(self):
        """Clean up after each test."""
        self.logger.clear_logs()

    def test_variance_calculation(self):
        """SIMULATION CONSTRAINT: variance = sum((x - mean)^2) / n."""
        # Sentences with 3 and 5 words: mean=4, variance=((3-4)^2 + (5-4)^2)/2 = 1
        text = "Three word sentence. Here are five words now."
        result = self.engine.analyze_style(text)

        # Calculate expected: lengths = [3, 5], mean = 4, variance = 1.0
        self.assertAlmostEqual(result["variance"], 1.0, places=2)

    def test_style_match_threshold(self):
        """SIMULATION CONSTRAINT: match when variance >= baseline - 5.0."""
        # Set baseline to 15.0 (default), threshold is 10.0
        self.engine.set_baseline(15.0)

        # Create text with variance >= 10.0
        # Sentences: 2 words, 20 words -> variance should be high
        text = "Short sentence. " + "Word " * 19 + "end."
        result = self.engine.analyze_style(text)

        if result["variance"] >= 10.0:
            self.assertTrue(result["style_match"])
            self.assertEqual(result["status"], "MATCH")
        else:
            self.assertFalse(result["style_match"])
            self.assertEqual(result["status"], "ANOMALY_DETECTED")

    def test_empty_text_handling(self):
        """SIMULATION CONSTRAINT: Return FAIL status for empty/invalid text."""
        result = self.engine.analyze_style("")
        self.assertEqual(result["variance"], 0)
        self.assertEqual(result["status"], "FAIL")

    def test_baseline_default(self):
        """Test default baseline variance is 15.0."""
        self.assertEqual(self.engine.get_baseline(), 15.0)


class TestAuditor(unittest.TestCase):
    """Tests for Auditor service."""

    def setUp(self):
        """Set up auditor for testing."""
        self.logger = TransparencyLog()
        self.logger.clear_logs()
        self.auditor = Auditor(self.logger)

    def tearDown(self):
        """Clean up after each test."""
        self.logger.clear_logs()

    def test_weights_match_simulation(self):
        """SIMULATION CONSTRAINT: Exact weights."""
        weights = self.auditor.get_weights()
        self.assertEqual(weights["Originality"], 0.35)
        self.assertEqual(weights["Criticality"], 0.35)
        self.assertEqual(weights["Rigour"], 0.30)

    def test_weighted_score_calculation(self):
        """SIMULATION CONSTRAINT: sum(score * weight) rounded to 2 decimals."""
        scores = {
            "Originality": 80,
            "Criticality": 70,
            "Rigour": 90
        }

        # Expected: 80*0.35 + 70*0.35 + 90*0.30 = 28 + 24.5 + 27 = 79.5
        result = self.auditor.evaluate("Test text", scores)
        self.assertEqual(result["total_weighted_score"], 79.5)

    def test_perfect_score(self):
        """Test perfect scores result in 100."""
        scores = {
            "Originality": 100,
            "Criticality": 100,
            "Rigour": 100
        }

        # Expected: 100*0.35 + 100*0.35 + 100*0.30 = 100
        result = self.auditor.evaluate("Test text", scores)
        self.assertEqual(result["total_weighted_score"], 100.0)

    def test_zero_score(self):
        """Test zero scores result in 0."""
        scores = {
            "Originality": 0,
            "Criticality": 0,
            "Rigour": 0
        }

        result = self.auditor.evaluate("Test text", scores)
        self.assertEqual(result["total_weighted_score"], 0.0)

    def test_partial_scores_default_to_zero(self):
        """Test missing scores default to 0."""
        scores = {"Originality": 100}  # Missing Criticality and Rigour

        # Expected: 100*0.35 + 0*0.35 + 0*0.30 = 35.0
        result = self.auditor.evaluate("Test text", scores)
        self.assertEqual(result["total_weighted_score"], 35.0)


class TestFeedbackProcessor(unittest.TestCase):
    """Tests for FeedbackProcessor service."""

    def setUp(self):
        """Set up processor for testing."""
        self.processor = FeedbackProcessor()

    def test_blocker_goes_to_red(self):
        """SIMULATION CONSTRAINT: 'blocker' -> RED."""
        text = "This is a blocker issue"
        result = self.processor.process(text)
        self.assertEqual(len(result["RED"]), 1)
        self.assertIn("This is a blocker issue", result["RED"])

    def test_consider_goes_to_amber(self):
        """SIMULATION CONSTRAINT: 'consider' -> AMBER."""
        text = "You should consider this change"
        result = self.processor.process(text)
        self.assertEqual(len(result["AMBER"]), 1)
        self.assertIn("You should consider this change", result["AMBER"])

    def test_typo_goes_to_green(self):
        """SIMULATION CONSTRAINT: 'typo' -> GREEN."""
        text = "There is a typo here"
        result = self.processor.process(text)
        self.assertEqual(len(result["GREEN"]), 1)
        self.assertIn("There is a typo here", result["GREEN"])

    def test_case_insensitive_matching(self):
        """SIMULATION CONSTRAINT: Keywords are case-insensitive."""
        text = "BLOCKER issue\nConsider THIS\nTYPO found"
        result = self.processor.process(text)

        self.assertEqual(len(result["RED"]), 1)
        self.assertEqual(len(result["AMBER"]), 1)
        self.assertEqual(len(result["GREEN"]), 1)

    def test_multiline_processing(self):
        """Test that newlines separate items."""
        text = """This is a blocker
Consider revising
Found a typo
Another blocker here"""

        result = self.processor.process(text)

        self.assertEqual(len(result["RED"]), 2)
        self.assertEqual(len(result["AMBER"]), 1)
        self.assertEqual(len(result["GREEN"]), 1)

    def test_uncategorized_lines_ignored(self):
        """Test that lines without keywords are not categorized."""
        text = "This is just feedback\nNo special keywords here"
        result = self.processor.process(text)

        self.assertEqual(len(result["RED"]), 0)
        self.assertEqual(len(result["AMBER"]), 0)
        self.assertEqual(len(result["GREEN"]), 0)

    def test_empty_categories_by_default(self):
        """Test that empty text returns empty categories."""
        result = self.processor.process("")

        self.assertEqual(result["RED"], [])
        self.assertEqual(result["AMBER"], [])
        self.assertEqual(result["GREEN"], [])


if __name__ == "__main__":
    unittest.main()
