"""Tests using deterministic fixtures."""

import csv
from pathlib import Path

import pytest

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCSVFixtures:
    """Tests for CSV file fixtures."""

    def test_empty_csv_has_headers_only(self):
        """Empty CSV should have headers but no data rows."""
        csv_path = FIXTURES_DIR / "empty.csv"
        assert csv_path.exists(), "empty.csv fixture not found"

        with open(csv_path, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 1, "Empty CSV should have exactly 1 row (headers)"
        assert rows[0] == ["id", "name", "value"]

    def test_single_row_csv(self):
        """Single row CSV should have headers and one data row."""
        csv_path = FIXTURES_DIR / "single_row.csv"
        assert csv_path.exists(), "single_row.csv fixture not found"

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["id"] == "1"
        assert rows[0]["name"] == "test"
        assert rows[0]["value"] == "100"

    def test_mixed_types_csv(self):
        """Mixed types CSV should have various data types and edge cases."""
        csv_path = FIXTURES_DIR / "mixed_types.csv"
        assert csv_path.exists(), "mixed_types.csv fixture not found"

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 5
        # Check headers
        assert "id" in rows[0]
        assert "name" in rows[0]
        assert "value" in rows[0]
        assert "active" in rows[0]
        assert "date" in rows[0]

        # Check for NaN value
        assert rows[2]["value"] == "NaN"

        # Check for empty values
        assert rows[3]["value"] == ""
        assert rows[3]["date"] == ""


class TestThesisFixture:
    """Tests for thesis text fixture."""

    def test_thesis_sample_exists(self):
        """Thesis sample fixture should exist."""
        txt_path = FIXTURES_DIR / "thesis_sample.txt"
        assert txt_path.exists(), "thesis_sample.txt fixture not found"

    def test_thesis_sample_has_content(self):
        """Thesis sample should have meaningful content."""
        txt_path = FIXTURES_DIR / "thesis_sample.txt"
        content = txt_path.read_text()

        assert len(content) > 100, "Thesis sample should have substantial content"
        assert "Chapter 1" in content
        assert "thesis" in content.lower()
        assert "research" in content.lower()

    def test_thesis_sample_has_multiple_paragraphs(self):
        """Thesis sample should have multiple paragraphs."""
        txt_path = FIXTURES_DIR / "thesis_sample.txt"
        content = txt_path.read_text()

        # Count paragraphs (double newlines)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        assert len(paragraphs) >= 3, "Should have at least 3 paragraphs"


class TestFixturesIntegrity:
    """Tests to verify all fixtures are present and valid."""

    def test_all_required_fixtures_exist(self):
        """All required fixture files should exist."""
        required_files = [
            "empty.csv",
            "single_row.csv",
            "mixed_types.csv",
            "thesis_sample.txt",
        ]

        for filename in required_files:
            path = FIXTURES_DIR / filename
            assert path.exists(), f"Required fixture {filename} not found"

    def test_fixtures_are_readable(self):
        """All fixtures should be readable."""
        for filepath in FIXTURES_DIR.iterdir():
            if filepath.is_file():
                try:
                    content = filepath.read_text()
                    assert len(content) > 0 or filepath.name == "empty.csv", (
                        f"Fixture {filepath.name} appears empty"
                    )
                except Exception as e:
                    pytest.fail(f"Could not read fixture {filepath.name}: {e}")
