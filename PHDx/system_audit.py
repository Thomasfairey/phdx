#!/usr/bin/env python3
"""
PHDx System Audit v2.0 - Deep Health Check

Comprehensive diagnostic for all PHDx modules with detailed testing
and Markdown status report generation.

Usage:
    python system_audit.py
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
import uuid

# Add project root to path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")


# =============================================================================
# ANSI COLORS
# =============================================================================
class C:
    """Terminal colors."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


# =============================================================================
# REPORT BUILDER
# =============================================================================
class AuditReport:
    """Builds the Markdown status report."""

    def __init__(self):
        self.sections = []
        self.summary = {"passed": 0, "failed": 0, "warnings": 0}

    def add_section(self, name: str, status: str, details: list[str], fix_cmd: Optional[str] = None):
        """Add a section to the report."""
        self.sections.append({
            "name": name,
            "status": status,
            "details": details,
            "fix_cmd": fix_cmd
        })

        if status == "PASSED":
            self.summary["passed"] += 1
        elif status == "FAILED":
            self.summary["failed"] += 1
        else:
            self.summary["warnings"] += 1

    def print_terminal(self):
        """Print the Markdown report to terminal."""
        print(f"\n{C.BOLD}{C.CYAN}")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║              PHDx DEEP HEALTH CHECK REPORT                   ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"{C.END}")

        print(f"{C.DIM}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.END}")
        print(f"{C.DIM}Root: {ROOT_DIR}{C.END}\n")

        # Print each section
        for section in self.sections:
            self._print_section(section)

        # Print summary
        self._print_summary()

    def _print_section(self, section: dict):
        """Print a single section."""
        status = section["status"]
        name = section["name"]

        if status == "PASSED":
            status_icon = f"{C.GREEN}[PASSED]{C.END}"
            header_color = C.GREEN
        elif status == "FAILED":
            status_icon = f"{C.RED}[FAILED]{C.END}"
            header_color = C.RED
        else:
            status_icon = f"{C.YELLOW}[WARNING]{C.END}"
            header_color = C.YELLOW

        print(f"{C.BOLD}{header_color}{'─' * 60}{C.END}")
        print(f"{status_icon} {C.BOLD}{name}{C.END}")
        print(f"{header_color}{'─' * 60}{C.END}")

        for detail in section["details"]:
            print(f"  {detail}")

        if section["fix_cmd"] and status != "PASSED":
            print(f"\n  {C.YELLOW}Fix Command:{C.END}")
            print(f"  {C.CYAN}$ {section['fix_cmd']}{C.END}")

        print()

    def _print_summary(self):
        """Print the summary."""
        total = self.summary["passed"] + self.summary["failed"] + self.summary["warnings"]

        print(f"{C.BOLD}{C.BLUE}{'═' * 60}{C.END}")
        print(f"{C.BOLD}SUMMARY{C.END}")
        print(f"{C.BLUE}{'═' * 60}{C.END}")

        print(f"  {C.GREEN}✓ Passed:   {self.summary['passed']}/{total}{C.END}")
        print(f"  {C.RED}✗ Failed:   {self.summary['failed']}/{total}{C.END}")
        print(f"  {C.YELLOW}⚠ Warnings: {self.summary['warnings']}/{total}{C.END}")

        if self.summary["failed"] == 0 and self.summary["warnings"] == 0:
            print(f"\n  {C.GREEN}{C.BOLD}🎉 All systems operational!{C.END}")
        elif self.summary["failed"] > 0:
            print(f"\n  {C.RED}Some modules need attention. See fix commands above.{C.END}")

        print(f"\n{C.BLUE}{'═' * 60}{C.END}\n")

    def to_markdown(self) -> str:
        """Generate Markdown report string."""
        lines = [
            "# PHDx Deep Health Check Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Root Directory:** `{ROOT_DIR}`",
            "",
            "---",
            ""
        ]

        for section in self.sections:
            status_badge = {
                "PASSED": "✅ **[PASSED]**",
                "FAILED": "❌ **[FAILED]**",
                "WARNING": "⚠️ **[WARNING]**"
            }.get(section["status"], "❓")

            lines.append(f"## {status_badge} {section['name']}")
            lines.append("")

            for detail in section["details"]:
                # Clean ANSI codes for markdown
                clean_detail = re.sub(r'\033\[[0-9;]*m', '', detail)
                lines.append(f"- {clean_detail}")

            if section["fix_cmd"] and section["status"] != "PASSED":
                lines.append("")
                lines.append("**Fix Command:**")
                lines.append(f"```bash")
                lines.append(section["fix_cmd"])
                lines.append("```")

            lines.append("")

        # Summary
        lines.extend([
            "---",
            "",
            "## Summary",
            "",
            f"| Status | Count |",
            f"|--------|-------|",
            f"| ✅ Passed | {self.summary['passed']} |",
            f"| ❌ Failed | {self.summary['failed']} |",
            f"| ⚠️ Warnings | {self.summary['warnings']} |",
            ""
        ])

        return "\n".join(lines)


# =============================================================================
# AUDIT FUNCTIONS
# =============================================================================

def audit_environment(report: AuditReport):
    """
    Environment Check: Verify all required keys in .env
    """
    print(f"{C.CYAN}Checking environment variables...{C.END}")

    details = []
    all_valid = True
    env_path = ROOT_DIR / ".env"

    # Required keys with validation patterns
    required_keys = {
        "ANTHROPIC_API_KEY": {
            "pattern": r"^sk-ant-[a-zA-Z0-9\-_]+$",
            "hint": "Should start with 'sk-ant-'"
        },
        "ZOTERO_USER_ID": {
            "pattern": r"^\d+$",
            "hint": "Should be numeric"
        },
        "ZOTERO_API_KEY": {
            "pattern": r"^[a-zA-Z0-9]+$",
            "hint": "Alphanumeric string"
        }
    }

    # Optional but recommended keys
    optional_keys = {
        "GOOGLE_DOC_ID": {
            "pattern": r"^[a-zA-Z0-9\-_]+$",
            "hint": "Document ID from Google Docs URL"
        },
        "GOOGLE_SHEETS_URL": {
            "pattern": r"^https://docs\.google\.com/spreadsheets",
            "hint": "Full Google Sheets URL"
        },
        "GOOGLE_CREDENTIALS_PATH": {
            "pattern": r".*\.json$",
            "hint": "Path to credentials.json"
        }
    }

    # Check .env file exists
    if not env_path.exists():
        details.append(f"{C.RED}✗ .env file not found{C.END}")
        report.add_section(
            "Environment Variables",
            "FAILED",
            details,
            f"cp {ROOT_DIR}/.env.example {ROOT_DIR}/.env && nano {ROOT_DIR}/.env"
        )
        return

    details.append(f"{C.GREEN}✓ .env file exists{C.END}")

    # Check required keys
    for key, config in required_keys.items():
        value = os.getenv(key)

        if not value:
            details.append(f"{C.RED}✗ {key}: Missing{C.END}")
            all_valid = False
        elif not re.match(config["pattern"], value):
            details.append(f"{C.YELLOW}⚠ {key}: Invalid format ({config['hint']}){C.END}")
            all_valid = False
        else:
            # Mask sensitive values
            masked = value[:8] + "..." + value[-4:] if len(value) > 16 else value[:4] + "..."
            details.append(f"{C.GREEN}✓ {key}: {masked}{C.END}")

    # Check optional keys
    for key, config in optional_keys.items():
        value = os.getenv(key)

        if not value:
            details.append(f"{C.DIM}○ {key}: Not configured (optional){C.END}")
        elif config["pattern"] and not re.match(config["pattern"], value):
            details.append(f"{C.YELLOW}⚠ {key}: Invalid format ({config['hint']}){C.END}")
        else:
            masked = value[:20] + "..." if len(value) > 25 else value
            details.append(f"{C.GREEN}✓ {key}: {masked}{C.END}")

    status = "PASSED" if all_valid else "FAILED"
    fix_cmd = f"nano {ROOT_DIR}/.env  # Add missing keys"

    report.add_section("Environment Variables", status, details, fix_cmd)


def audit_dna_engine(report: AuditReport):
    """
    DNA Engine Test: Load and analyze author_dna.json
    """
    print(f"{C.CYAN}Testing DNA Engine...{C.END}")

    details = []
    dna_path = ROOT_DIR / "data" / "author_dna.json"
    drafts_dir = ROOT_DIR / "drafts"

    # Check drafts folder
    if not drafts_dir.exists():
        details.append(f"{C.RED}✗ Drafts folder missing: {drafts_dir}{C.END}")
        report.add_section(
            "DNA Engine",
            "FAILED",
            details,
            f"mkdir -p {drafts_dir} && echo 'Add .docx files here'"
        )
        return

    docx_files = list(drafts_dir.glob("*.docx"))
    details.append(f"{C.GREEN}✓ Drafts folder exists: {len(docx_files)} .docx files{C.END}")

    # Check DNA profile
    if not dna_path.exists():
        details.append(f"{C.RED}✗ DNA Profile: MISSING{C.END}")
        details.append(f"  Status: author_dna.json not generated")

        fix_cmd = f"cd {ROOT_DIR} && python core/dna_engine.py"
        if len(docx_files) == 0:
            fix_cmd = f"# First add .docx files to {drafts_dir}, then:\ncd {ROOT_DIR} && python core/dna_engine.py"

        report.add_section("DNA Engine", "FAILED", details, fix_cmd)
        return

    # Load and analyze DNA profile
    try:
        with open(dna_path, 'r', encoding='utf-8') as f:
            dna = json.load(f)

        details.append(f"{C.GREEN}✓ DNA Profile: LOADED{C.END}")

        # Generate Linguistic Summary
        meta = dna.get("metadata", {})
        sentence = dna.get("sentence_complexity", {})
        hedging = dna.get("hedging_analysis", {})
        transitions = dna.get("transition_vocabulary", {})

        details.append(f"\n  {C.BOLD}═══ Linguistic Summary ═══{C.END}")
        details.append(f"  📊 Total Words Analyzed: {meta.get('total_word_count', 0):,}")
        details.append(f"  📄 Documents Analyzed: {len(meta.get('documents_analyzed', []))}")
        details.append(f"  📝 Avg Sentence Length: {sentence.get('average_length', 0)} words")
        details.append(f"  🔮 Hedging Density: {hedging.get('hedging_density_per_1000_words', 0)}/1000 words")
        details.append(f"  🔗 Transition Density: {transitions.get('transition_density_per_1000_words', 0)}/1000 words")

        # Top hedging phrases
        top_hedges = list(hedging.get("phrases_found", {}).keys())[:3]
        if top_hedges:
            details.append(f"  💭 Top Hedges: {', '.join(top_hedges)}")

        # Preferred transition categories
        prefs = transitions.get("preferred_categories", [])[:3]
        if prefs:
            details.append(f"  ➡️ Transition Style: {', '.join(prefs)}")

        report.add_section("DNA Engine", "PASSED", details)

    except json.JSONDecodeError as e:
        details.append(f"{C.RED}✗ DNA Profile: CORRUPT{C.END}")
        details.append(f"  Error: {e}")
        report.add_section(
            "DNA Engine",
            "FAILED",
            details,
            f"rm {dna_path} && cd {ROOT_DIR} && python core/dna_engine.py"
        )


def audit_zotero_sentinel(report: AuditReport):
    """
    Zotero Sentinel Test: Connect and fetch library info
    """
    print(f"{C.CYAN}Testing Zotero Sentinel...{C.END}")

    details = []
    import requests

    user_id = os.getenv("ZOTERO_USER_ID")
    api_key = os.getenv("ZOTERO_API_KEY")

    if not user_id or not api_key:
        details.append(f"{C.RED}✗ Credentials: Missing{C.END}")
        report.add_section(
            "Zotero Sentinel",
            "FAILED",
            details,
            "# Add to .env:\nZOTERO_USER_ID=your_id\nZOTERO_API_KEY=your_key\n# Get key at: https://www.zotero.org/settings/keys"
        )
        return

    details.append(f"{C.GREEN}✓ Credentials: Configured{C.END}")

    # Test API connection
    try:
        headers = {"Zotero-API-Key": api_key}

        # Get user info
        user_url = f"https://api.zotero.org/users/{user_id}"
        user_resp = requests.get(user_url, headers=headers, timeout=10)

        if user_resp.status_code == 200:
            user_data = user_resp.json()
            username = user_data.get("username", "Unknown")
            details.append(f"{C.GREEN}✓ Zotero Connection: SUCCESS{C.END}")
            details.append(f"  👤 Library Owner: {username}")

            # Get library stats
            items_url = f"https://api.zotero.org/users/{user_id}/items/top?limit=1"
            items_resp = requests.get(items_url, headers=headers, timeout=10)

            if items_resp.status_code == 200:
                total_items = int(items_resp.headers.get('Total-Results', 0))
                details.append(f"  📚 Library Items: {total_items}")

                if total_items == 0:
                    details.append(f"  {C.YELLOW}⚠ Library is empty - add references at zotero.org{C.END}")

                # Get a sample item title if available
                items = items_resp.json()
                if items:
                    sample_title = items[0].get("data", {}).get("title", "")[:50]
                    if sample_title:
                        details.append(f"  📄 Sample: \"{sample_title}...\"")

            report.add_section("Zotero Sentinel", "PASSED", details)

        elif user_resp.status_code == 403:
            details.append(f"{C.RED}✗ Zotero Connection: FAILED (Invalid API Key){C.END}")
            report.add_section(
                "Zotero Sentinel",
                "FAILED",
                details,
                "# Regenerate API key at:\n# https://www.zotero.org/settings/keys\n# Then update ZOTERO_API_KEY in .env"
            )

        elif user_resp.status_code == 404:
            details.append(f"{C.RED}✗ Zotero Connection: FAILED (User ID not found){C.END}")
            report.add_section(
                "Zotero Sentinel",
                "FAILED",
                details,
                "# Check your ZOTERO_USER_ID in .env\n# Find it at: https://www.zotero.org/settings/keys"
            )

        else:
            details.append(f"{C.RED}✗ Zotero Connection: FAILED (HTTP {user_resp.status_code}){C.END}")
            report.add_section("Zotero Sentinel", "FAILED", details, "# Check internet connection and try again")

    except requests.exceptions.Timeout:
        details.append(f"{C.RED}✗ Zotero Connection: TIMEOUT{C.END}")
        report.add_section("Zotero Sentinel", "FAILED", details, "# Check internet connection")

    except Exception as e:
        details.append(f"{C.RED}✗ Zotero Connection: ERROR - {e}{C.END}")
        report.add_section("Zotero Sentinel", "FAILED", details, "pip install requests")


def audit_red_thread(report: AuditReport):
    """
    Red Thread Test: Initialize ChromaDB, insert and retrieve test data
    """
    print(f"{C.CYAN}Testing Red Thread Engine...{C.END}")

    details = []

    # Check ChromaDB installation
    try:
        import chromadb
        details.append(f"{C.GREEN}✓ ChromaDB: Installed (v{chromadb.__version__}){C.END}")
    except ImportError:
        details.append(f"{C.RED}✗ ChromaDB: Not installed{C.END}")
        report.add_section(
            "Red Thread Engine",
            "FAILED",
            details,
            "pip install chromadb"
        )
        return

    # Test vector database operations
    try:
        # Create temporary test collection
        chroma_path = ROOT_DIR / "data" / "chroma_db"
        client = chromadb.PersistentClient(path=str(chroma_path))

        test_collection_name = f"audit_test_{uuid.uuid4().hex[:8]}"
        collection = client.create_collection(name=test_collection_name)

        details.append(f"{C.GREEN}✓ ChromaDB: Initialized{C.END}")

        # Insert test document
        test_id = "audit_test_001"
        test_claim = "The epistemological foundations of qualitative research necessitate reflexive engagement with positionality."
        test_meta = {"chapter": "Methodology", "type": "research_claim"}

        collection.add(
            documents=[test_claim],
            metadatas=[test_meta],
            ids=[test_id]
        )

        details.append(f"{C.GREEN}✓ Write Test: SUCCESS{C.END}")
        details.append(f"  📝 Inserted: \"{test_claim[:50]}...\"")

        # Retrieve test document
        results = collection.query(
            query_texts=["epistemological foundations qualitative research"],
            n_results=1
        )

        if results and results['documents'] and len(results['documents'][0]) > 0:
            retrieved = results['documents'][0][0]
            similarity = 1 - results['distances'][0][0] if results.get('distances') else 0

            details.append(f"{C.GREEN}✓ Read Test: SUCCESS{C.END}")
            details.append(f"  🔍 Retrieved: \"{retrieved[:50]}...\"")
            details.append(f"  📊 Similarity Score: {similarity:.2%}")
        else:
            details.append(f"{C.YELLOW}⚠ Read Test: No results returned{C.END}")

        # Cleanup test collection
        client.delete_collection(name=test_collection_name)
        details.append(f"{C.GREEN}✓ Cleanup: Test collection removed{C.END}")

        # Check main collection stats
        try:
            main_collection = client.get_collection("thesis_paragraphs")
            count = main_collection.count()
            details.append(f"\n  {C.BOLD}Main Collection:{C.END}")
            details.append(f"  📊 Indexed Paragraphs: {count}")

            if count == 0:
                details.append(f"  {C.YELLOW}⚠ Collection empty - run indexer{C.END}")

        except Exception:
            details.append(f"  {C.DIM}○ Main collection not yet created{C.END}")

        report.add_section("Red Thread Engine", "PASSED", details)

    except Exception as e:
        details.append(f"{C.RED}✗ ChromaDB Test: FAILED{C.END}")
        details.append(f"  Error: {e}")
        report.add_section(
            "Red Thread Engine",
            "FAILED",
            details,
            f"rm -rf {ROOT_DIR}/data/chroma_db && pip install --upgrade chromadb"
        )


def audit_google_bridge(report: AuditReport):
    """
    Google Bridge Test: Authenticate and fetch thesis document title
    """
    print(f"{C.CYAN}Testing Google Bridge...{C.END}")

    details = []

    creds_path = ROOT_DIR / os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    doc_id = os.getenv("GOOGLE_DOC_ID")
    sheets_url = os.getenv("GOOGLE_SHEETS_URL")

    # Check credentials file
    if not creds_path.exists():
        details.append(f"{C.RED}✗ Credentials: {creds_path.name} not found{C.END}")
        report.add_section(
            "Google Bridge",
            "FAILED",
            details,
            """# Setup Google Service Account:
# 1. Go to https://console.cloud.google.com/
# 2. Create project > Enable Docs & Sheets APIs
# 3. Create Service Account > Download JSON key
# 4. Save as credentials.json in PHDx folder
# 5. Share your Doc/Sheet with the service account email"""
        )
        return

    details.append(f"{C.GREEN}✓ Credentials: Found{C.END}")

    # Try to authenticate
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        scopes = [
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        service_email = creds.service_account_email

        details.append(f"{C.GREEN}✓ Authentication: SUCCESS{C.END}")
        details.append(f"  📧 Service Account: {service_email[:40]}...")

        # Test Google Docs
        if doc_id:
            try:
                docs_service = build('docs', 'v1', credentials=creds)
                doc = docs_service.documents().get(documentId=doc_id).execute()
                doc_title = doc.get('title', 'Untitled')

                details.append(f"{C.GREEN}✓ Google Docs: CONNECTED{C.END}")
                details.append(f"  📄 Thesis Document: \"{doc_title}\"")

            except Exception as e:
                error_str = str(e)
                if "404" in error_str:
                    details.append(f"{C.RED}✗ Google Docs: Document not found{C.END}")
                elif "403" in error_str:
                    details.append(f"{C.RED}✗ Google Docs: Permission denied{C.END}")
                    details.append(f"  💡 Share document with: {service_email}")
                else:
                    details.append(f"{C.RED}✗ Google Docs: {e}{C.END}")
        else:
            details.append(f"{C.DIM}○ GOOGLE_DOC_ID: Not configured (optional){C.END}")

        # Test Google Sheets
        if sheets_url:
            try:
                import gspread

                gc = gspread.authorize(creds)
                sheet = gc.open_by_url(sheets_url).sheet1

                sheet_title = sheet.title
                records = sheet.get_all_records()
                row_count = len(records)

                details.append(f"{C.GREEN}✓ Google Sheets: CONNECTED{C.END}")
                details.append(f"  📊 Sheet: \"{sheet_title}\" ({row_count} rows)")

                # Sample first row
                if records:
                    sample_keys = list(records[0].keys())[:3]
                    details.append(f"  📋 Columns: {', '.join(sample_keys)}...")

            except Exception as e:
                error_str = str(e)
                if "403" in error_str:
                    details.append(f"{C.RED}✗ Google Sheets: Permission denied{C.END}")
                    details.append(f"  💡 Share sheet with: {service_email}")
                else:
                    details.append(f"{C.RED}✗ Google Sheets: {e}{C.END}")
        else:
            details.append(f"{C.DIM}○ GOOGLE_SHEETS_URL: Not configured (optional){C.END}")

        # Determine overall status
        has_doc = doc_id and "CONNECTED" in str(details)
        has_sheets = sheets_url and "Sheet:" in str(details)

        if has_doc or has_sheets or (not doc_id and not sheets_url):
            report.add_section("Google Bridge", "PASSED", details)
        else:
            report.add_section(
                "Google Bridge",
                "WARNING",
                details,
                f"# Share your documents with:\n# {service_email}"
            )

    except ImportError as e:
        details.append(f"{C.RED}✗ Missing library: {e}{C.END}")
        report.add_section(
            "Google Bridge",
            "FAILED",
            details,
            "pip install google-auth google-auth-oauthlib google-api-python-client gspread"
        )

    except Exception as e:
        details.append(f"{C.RED}✗ Authentication: FAILED{C.END}")
        details.append(f"  Error: {e}")
        report.add_section(
            "Google Bridge",
            "FAILED",
            details,
            "# Re-download credentials.json from Google Cloud Console"
        )


def audit_feedback_processor(report: AuditReport):
    """
    Feedback Processor Test: Check module and feedback folder
    """
    print(f"{C.CYAN}Testing Feedback Processor...{C.END}")

    details = []
    feedback_dir = ROOT_DIR / "feedback"

    # Check feedback directory
    if not feedback_dir.exists():
        details.append(f"{C.YELLOW}⚠ Feedback folder: Creating...{C.END}")
        feedback_dir.mkdir(parents=True, exist_ok=True)

    details.append(f"{C.GREEN}✓ Feedback folder: {feedback_dir}{C.END}")

    # Count feedback files
    supported = ['.pdf', '.docx', '.txt', '.md']
    feedback_files = [f for f in feedback_dir.iterdir() if f.suffix.lower() in supported]
    details.append(f"  📁 Feedback documents: {len(feedback_files)}")

    # Check module import
    try:
        from core.feedback_processor import FeedbackProcessor

        processor = FeedbackProcessor()
        stats = processor.get_stats()

        details.append(f"{C.GREEN}✓ FeedbackProcessor: Loaded{C.END}")
        details.append(f"  📊 Cached items: {stats['total_items']}")
        details.append(f"  ✅ Resolved: {stats['resolved']}")
        details.append(f"  ⏳ Unresolved: {stats['unresolved']['total']}")

        # Check parsing libraries
        try:
            from docx import Document
            details.append(f"{C.GREEN}✓ DOCX support: Available{C.END}")
        except ImportError:
            details.append(f"{C.YELLOW}⚠ DOCX support: pip install python-docx{C.END}")

        try:
            import fitz
            details.append(f"{C.GREEN}✓ PDF support: Available{C.END}")
        except ImportError:
            details.append(f"{C.YELLOW}⚠ PDF support: pip install pymupdf{C.END}")

        report.add_section("Feedback Processor", "PASSED", details)

    except ImportError as e:
        details.append(f"{C.RED}✗ FeedbackProcessor: Import failed{C.END}")
        details.append(f"  Error: {e}")
        report.add_section(
            "Feedback Processor",
            "FAILED",
            details,
            "pip install python-docx pymupdf"
        )


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the full system audit."""
    print(f"\n{C.BOLD}{C.MAGENTA}")
    print("  ╔═══════════════════════════════════════════════════════════╗")
    print("  ║           PHDx SYSTEM AUDIT v2.0 - DEEP CHECK             ║")
    print("  ║              PhD Thesis Command Center                    ║")
    print("  ╚═══════════════════════════════════════════════════════════╝")
    print(f"{C.END}")

    report = AuditReport()

    # Run all audits
    audit_environment(report)
    audit_dna_engine(report)
    audit_zotero_sentinel(report)
    audit_red_thread(report)
    audit_google_bridge(report)
    audit_feedback_processor(report)

    # Print terminal report
    report.print_terminal()

    # Save Markdown report
    report_path = ROOT_DIR / "data" / "audit_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report.to_markdown())

    print(f"{C.DIM}Markdown report saved to: {report_path}{C.END}\n")

    # Return exit code
    return 0 if report.summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
