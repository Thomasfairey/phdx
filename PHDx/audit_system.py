#!/usr/bin/env python3
"""
PHDx System Audit - Diagnostic Script

Checks all PHDx components and provides status report with fix instructions.

Usage:
    python audit_system.py
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

# ANSI colors for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_status(name: str, success: bool, details: str = ""):
    """Print a status line."""
    icon = f"{Colors.GREEN}✓{Colors.END}" if success else f"{Colors.RED}✗{Colors.END}"
    status = f"{Colors.GREEN}OK{Colors.END}" if success else f"{Colors.RED}FAIL{Colors.END}"
    print(f"  {icon} {name}: {status}")
    if details:
        print(f"      {Colors.CYAN}{details}{Colors.END}")


def print_fix(instructions: list[str]):
    """Print fix instructions."""
    print(f"\n  {Colors.YELLOW}How to Fix:{Colors.END}")
    for i, instruction in enumerate(instructions, 1):
        print(f"    {i}. {instruction}")


def audit_dna_engine() -> dict:
    """
    Audit the DNA Engine component.

    Checks:
    - /drafts folder exists and contains .docx files
    - author_dna.json exists and is valid
    """
    print_header("DNA ENGINE AUDIT")

    results = {
        "component": "DNA Engine",
        "checks": [],
        "overall": True
    }

    drafts_dir = ROOT_DIR / "drafts"
    dna_path = ROOT_DIR / "data" / "author_dna.json"

    # Check 1: Drafts folder exists
    drafts_exists = drafts_dir.exists() and drafts_dir.is_dir()
    results["checks"].append({"name": "Drafts folder exists", "passed": drafts_exists})
    print_status("Drafts folder", drafts_exists, str(drafts_dir) if drafts_exists else "")

    if not drafts_exists:
        print_fix([
            f"Create the drafts folder: mkdir -p {drafts_dir}",
            "Add your thesis chapter .docx files to this folder"
        ])
        results["overall"] = False

    # Check 2: Drafts folder contains .docx files
    docx_files = list(drafts_dir.glob("*.docx")) if drafts_exists else []
    has_docx = len(docx_files) > 0
    results["checks"].append({"name": "Contains .docx files", "passed": has_docx})
    print_status("Contains .docx files", has_docx, f"{len(docx_files)} files found" if has_docx else "No .docx files")

    if drafts_exists and not has_docx:
        print_fix([
            f"Add .docx draft files to: {drafts_dir}",
            "These should be your thesis chapter drafts for DNA analysis"
        ])
        results["overall"] = False
    elif has_docx:
        for f in docx_files[:3]:
            print(f"        - {f.name}")
        if len(docx_files) > 3:
            print(f"        ... and {len(docx_files) - 3} more")

    # Check 3: author_dna.json exists
    dna_exists = dna_path.exists()
    results["checks"].append({"name": "author_dna.json exists", "passed": dna_exists})
    print_status("author_dna.json", dna_exists, str(dna_path) if dna_exists else "Not generated yet")

    if not dna_exists:
        print_fix([
            "Generate your DNA profile by running:",
            f"  cd {ROOT_DIR} && python core/dna_engine.py",
            "This requires .docx files in the /drafts folder"
        ])
        results["overall"] = False

    # Check 4: author_dna.json is valid JSON with expected structure
    if dna_exists:
        try:
            with open(dna_path, 'r', encoding='utf-8') as f:
                dna_data = json.load(f)

            required_keys = ["metadata", "sentence_complexity", "hedging_analysis"]
            has_structure = all(k in dna_data for k in required_keys)
            results["checks"].append({"name": "DNA profile valid", "passed": has_structure})

            if has_structure:
                meta = dna_data.get("metadata", {})
                print_status("DNA profile valid", True,
                    f"{meta.get('total_word_count', 0):,} words from {len(meta.get('documents_analyzed', []))} documents")
            else:
                print_status("DNA profile valid", False, "Missing required fields")
                print_fix([
                    "Regenerate your DNA profile:",
                    f"  cd {ROOT_DIR} && python core/dna_engine.py"
                ])
                results["overall"] = False

        except json.JSONDecodeError as e:
            results["checks"].append({"name": "DNA profile valid", "passed": False})
            print_status("DNA profile valid", False, f"Invalid JSON: {e}")
            print_fix([
                "Delete the corrupted file and regenerate:",
                f"  rm {dna_path}",
                f"  cd {ROOT_DIR} && python core/dna_engine.py"
            ])
            results["overall"] = False

    return results


def audit_zotero_sentinel() -> dict:
    """
    Audit the Zotero Sentinel component.

    Checks:
    - ZOTERO_USER_ID configured
    - ZOTERO_API_KEY configured
    - Can connect to Zotero API
    - Can retrieve library information
    """
    print_header("ZOTERO SENTINEL AUDIT")

    results = {
        "component": "Zotero Sentinel",
        "checks": [],
        "overall": True
    }

    import requests
    ZOTERO_API_BASE = "https://api.zotero.org"

    user_id = os.getenv("ZOTERO_USER_ID")
    api_key = os.getenv("ZOTERO_API_KEY")

    # Check 1: User ID configured
    has_user_id = bool(user_id)
    results["checks"].append({"name": "ZOTERO_USER_ID configured", "passed": has_user_id})
    print_status("ZOTERO_USER_ID", has_user_id, f"ID: {user_id}" if has_user_id else "Not set")

    if not has_user_id:
        print_fix([
            "Add your Zotero User ID to .env:",
            "  ZOTERO_USER_ID=your_user_id",
            "Find your ID at: https://www.zotero.org/settings/keys",
            "  (shown in URL: zotero.org/users/{USER_ID})"
        ])
        results["overall"] = False

    # Check 2: API Key configured
    has_api_key = bool(api_key)
    results["checks"].append({"name": "ZOTERO_API_KEY configured", "passed": has_api_key})
    print_status("ZOTERO_API_KEY", has_api_key, "Configured" if has_api_key else "Not set")

    if not has_api_key:
        print_fix([
            "Add your Zotero API Key to .env:",
            "  ZOTERO_API_KEY=your_api_key",
            "Create one at: https://www.zotero.org/settings/keys",
            "  (Enable 'Allow library access' permission)"
        ])
        results["overall"] = False

    # Check 3: API Connection
    if has_user_id and has_api_key:
        try:
            headers = {"Zotero-API-Key": api_key}

            # Test connection with a simple request
            url = f"{ZOTERO_API_BASE}/users/{user_id}/items/top?limit=1"
            response = requests.get(url, headers=headers, timeout=10)

            connected = response.status_code == 200
            results["checks"].append({"name": "API connection", "passed": connected})

            if connected:
                total_items = int(response.headers.get('Total-Results', 0))
                print_status("API connection", True, f"Connected successfully")

                # Check 4: Library content
                results["checks"].append({"name": "Library accessible", "passed": True})
                print_status("Library accessible", True, f"{total_items} items in library")

                if total_items == 0:
                    print(f"\n  {Colors.YELLOW}Note: Your Zotero library is empty.{Colors.END}")
                    print(f"    Add references at: https://www.zotero.org/")

                # Get library/user info
                user_url = f"{ZOTERO_API_BASE}/users/{user_id}"
                user_response = requests.get(user_url, headers=headers, timeout=10)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    username = user_data.get("username", "Unknown")
                    print_status("Library owner", True, f"Username: {username}")
                    results["checks"].append({"name": "Library owner", "passed": True})

            else:
                error_msg = f"HTTP {response.status_code}"
                if response.status_code == 403:
                    error_msg = "Invalid API key or insufficient permissions"
                elif response.status_code == 404:
                    error_msg = "User ID not found"

                print_status("API connection", False, error_msg)
                print_fix([
                    "Verify your credentials in .env:",
                    "  - Check ZOTERO_USER_ID is correct",
                    "  - Check ZOTERO_API_KEY is valid and not expired",
                    "Create a new key at: https://www.zotero.org/settings/keys"
                ])
                results["overall"] = False

        except requests.exceptions.Timeout:
            results["checks"].append({"name": "API connection", "passed": False})
            print_status("API connection", False, "Connection timed out")
            print_fix([
                "Check your internet connection",
                "Zotero API may be temporarily unavailable",
                "Try again in a few minutes"
            ])
            results["overall"] = False

        except requests.exceptions.RequestException as e:
            results["checks"].append({"name": "API connection", "passed": False})
            print_status("API connection", False, f"Error: {e}")
            print_fix([
                "Check your internet connection",
                f"Error details: {e}"
            ])
            results["overall"] = False

    return results


def audit_google_bridge() -> dict:
    """
    Audit the Google Bridge component.

    Checks:
    - Google credentials file exists
    - Can authenticate with Google API
    - GOOGLE_DOC_ID configured and accessible
    - GOOGLE_SHEETS_URL configured and accessible
    """
    print_header("GOOGLE BRIDGE AUDIT")

    results = {
        "component": "Google Bridge",
        "checks": [],
        "overall": True
    }

    creds_path = ROOT_DIR / os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    doc_id = os.getenv("GOOGLE_DOC_ID")
    sheets_url = os.getenv("GOOGLE_SHEETS_URL")

    # Check 1: Credentials file exists
    creds_exists = creds_path.exists()
    results["checks"].append({"name": "credentials.json exists", "passed": creds_exists})
    print_status("credentials.json", creds_exists, str(creds_path) if creds_exists else "Not found")

    if not creds_exists:
        print_fix([
            "Download Google Service Account credentials:",
            "  1. Go to: https://console.cloud.google.com/",
            "  2. Create a project (or select existing)",
            "  3. Enable Google Docs API and Google Sheets API",
            "  4. Create Service Account > Keys > Add Key > JSON",
            f"  5. Save as: {creds_path}",
            "  6. Share your Doc/Sheet with the service account email"
        ])
        results["overall"] = False

        # Skip remaining checks if no credentials
        results["checks"].append({"name": "Google API authentication", "passed": False})
        print_status("Google API auth", False, "Skipped - no credentials")
        return results

    # Check 2: Can authenticate
    try:
        from google.oauth2.service_account import Credentials

        scopes = [
            "https://www.googleapis.com/auth/documents.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

        creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
        service_email = creds.service_account_email

        results["checks"].append({"name": "Google API authentication", "passed": True})
        print_status("Google API auth", True, f"Service account: {service_email[:30]}...")

        # Check 3: Google Doc access
        if doc_id:
            try:
                from googleapiclient.discovery import build

                docs_service = build('docs', 'v1', credentials=creds)
                doc = docs_service.documents().get(documentId=doc_id).execute()
                doc_title = doc.get('title', 'Untitled')

                results["checks"].append({"name": "Google Doc accessible", "passed": True})
                print_status("Google Doc", True, f'"{doc_title}"')

            except Exception as e:
                error_str = str(e)
                results["checks"].append({"name": "Google Doc accessible", "passed": False})

                if "404" in error_str:
                    print_status("Google Doc", False, "Document not found")
                    print_fix([
                        "Verify GOOGLE_DOC_ID in .env is correct",
                        f"  Current value: {doc_id}",
                        "Find the ID in your Google Doc URL:",
                        "  docs.google.com/document/d/{DOC_ID}/edit"
                    ])
                elif "403" in error_str or "permission" in error_str.lower():
                    print_status("Google Doc", False, "Permission denied")
                    print_fix([
                        f"Share your Google Doc with the service account:",
                        f"  {service_email}",
                        "Give it 'Viewer' or 'Editor' access"
                    ])
                else:
                    print_status("Google Doc", False, f"Error: {e}")

                results["overall"] = False
        else:
            results["checks"].append({"name": "Google Doc configured", "passed": False})
            print_status("GOOGLE_DOC_ID", False, "Not configured in .env")
            print_fix([
                "Add to .env:",
                "  GOOGLE_DOC_ID=your_document_id",
                "Find the ID in your Google Doc URL:",
                "  docs.google.com/document/d/{DOC_ID}/edit"
            ])
            results["overall"] = False

        # Check 4: Google Sheets access
        if sheets_url:
            try:
                import gspread

                gc = gspread.authorize(creds)
                sheet = gc.open_by_url(sheets_url).sheet1

                # Get first row as sample
                records = sheet.get_all_records()
                row_count = len(records)

                results["checks"].append({"name": "Google Sheet accessible", "passed": True})
                print_status("Google Sheet", True, f'"{sheet.title}" - {row_count} data rows')

                if row_count > 0:
                    # Show sample columns
                    sample_row = records[0]
                    columns = list(sample_row.keys())[:4]
                    print(f"        Sample columns: {', '.join(columns)}")

            except Exception as e:
                error_str = str(e)
                results["checks"].append({"name": "Google Sheet accessible", "passed": False})

                if "404" in error_str:
                    print_status("Google Sheet", False, "Sheet not found")
                elif "403" in error_str or "permission" in error_str.lower():
                    print_status("Google Sheet", False, "Permission denied")
                    print_fix([
                        f"Share your Google Sheet with the service account:",
                        f"  {service_email}",
                        "Give it 'Viewer' or 'Editor' access"
                    ])
                else:
                    print_status("Google Sheet", False, f"Error: {e}")

                results["overall"] = False
        else:
            results["checks"].append({"name": "Google Sheet configured", "passed": False})
            print_status("GOOGLE_SHEETS_URL", False, "Not configured in .env (optional)")
            print(f"      {Colors.YELLOW}This is optional - only needed for data injection{Colors.END}")
            # Don't fail overall for missing sheets

    except ImportError as e:
        missing_lib = str(e).split("'")[-2] if "'" in str(e) else "unknown"
        results["checks"].append({"name": "Google API libraries", "passed": False})
        print_status("Google API libraries", False, f"Missing: {missing_lib}")
        print_fix([
            "Install required libraries:",
            "  pip install google-auth google-auth-oauthlib google-api-python-client gspread"
        ])
        results["overall"] = False

    except Exception as e:
        results["checks"].append({"name": "Google API authentication", "passed": False})
        print_status("Google API auth", False, f"Error: {e}")
        print_fix([
            "Verify credentials.json is a valid Google Service Account key",
            "Re-download from Google Cloud Console if needed"
        ])
        results["overall"] = False

    return results


def audit_red_thread() -> dict:
    """
    Audit the Red Thread Engine component.

    Checks:
    - ChromaDB installed
    - ChromaDB collection initialized
    - Can query the database
    """
    print_header("RED THREAD ENGINE AUDIT")

    results = {
        "component": "Red Thread Engine",
        "checks": [],
        "overall": True
    }

    chroma_dir = ROOT_DIR / "data" / "chroma_db"

    # Check 1: ChromaDB installed
    try:
        import chromadb
        results["checks"].append({"name": "ChromaDB installed", "passed": True})
        print_status("ChromaDB installed", True, f"Version: {chromadb.__version__}")

    except ImportError:
        results["checks"].append({"name": "ChromaDB installed", "passed": False})
        print_status("ChromaDB installed", False, "Not found")
        print_fix([
            "Install ChromaDB:",
            "  pip install chromadb"
        ])
        results["overall"] = False
        return results

    # Check 2: ChromaDB directory exists
    chroma_exists = chroma_dir.exists()
    results["checks"].append({"name": "ChromaDB directory", "passed": chroma_exists})
    print_status("ChromaDB directory", chroma_exists,
                str(chroma_dir) if chroma_exists else "Not initialized")

    # Check 3: Can initialize/connect to ChromaDB
    try:
        from core.red_thread import RedThreadEngine

        engine = RedThreadEngine()
        stats = engine.get_stats()

        total_paragraphs = stats.get("total_paragraphs", 0)
        results["checks"].append({"name": "ChromaDB connection", "passed": True})
        print_status("ChromaDB connection", True, "Connected successfully")

        # Check 4: Collection has data
        has_data = total_paragraphs > 0
        results["checks"].append({"name": "Collection has data", "passed": has_data})
        print_status("Collection data", has_data,
                    f"{total_paragraphs} paragraphs indexed" if has_data else "Empty collection")

        if not has_data:
            print_fix([
                "Index your drafts to populate the Red Thread database:",
                f"  1. Add .docx files to {ROOT_DIR / 'drafts'}",
                "  2. Run the indexer:",
                f"     cd {ROOT_DIR} && python -c \"from core.red_thread import RedThreadEngine; e = RedThreadEngine(); print(e.index_drafts_folder())\"",
                "  Or use the 'Re-index Drafts' button in the UI sidebar"
            ])
            # Don't fail overall for empty collection - might be first run

        # Check 5: Test query capability
        try:
            test_results = engine.find_similar_passages("test query for audit", n_results=1)
            results["checks"].append({"name": "Query capability", "passed": True})
            print_status("Query capability", True, "Queries working")
        except Exception as e:
            results["checks"].append({"name": "Query capability", "passed": False})
            print_status("Query capability", False, f"Error: {e}")
            results["overall"] = False

    except Exception as e:
        results["checks"].append({"name": "ChromaDB connection", "passed": False})
        print_status("ChromaDB connection", False, f"Error: {e}")
        print_fix([
            "Try reinitializing ChromaDB:",
            f"  1. Delete the database: rm -rf {chroma_dir}",
            "  2. Restart the Red Thread Engine",
            "  3. Re-index your drafts"
        ])
        results["overall"] = False

    return results


def print_summary(all_results: list[dict]):
    """Print overall system health summary."""
    print_header("SYSTEM HEALTH SUMMARY")

    total_checks = 0
    passed_checks = 0
    failed_components = []

    for result in all_results:
        component = result["component"]
        is_healthy = result["overall"]

        for check in result["checks"]:
            total_checks += 1
            if check["passed"]:
                passed_checks += 1

        status = f"{Colors.GREEN}HEALTHY{Colors.END}" if is_healthy else f"{Colors.RED}NEEDS ATTENTION{Colors.END}"
        icon = f"{Colors.GREEN}✓{Colors.END}" if is_healthy else f"{Colors.RED}✗{Colors.END}"
        print(f"  {icon} {component}: {status}")

        if not is_healthy:
            failed_components.append(component)

    print(f"\n  {Colors.BOLD}Overall: {passed_checks}/{total_checks} checks passed{Colors.END}")

    if failed_components:
        print(f"\n  {Colors.YELLOW}Components needing attention:{Colors.END}")
        for comp in failed_components:
            print(f"    - {comp}")
        print(f"\n  {Colors.CYAN}Run this script again after making fixes to verify.{Colors.END}")
    else:
        print(f"\n  {Colors.GREEN}{Colors.BOLD}All systems operational!{Colors.END}")

    return len(failed_components) == 0


def main():
    """Run the full system audit."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║           PHDx SYSTEM DIAGNOSTIC AUDIT                ║")
    print("  ║         PhD Thesis Command Center v2.0                ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    print(f"  {Colors.CYAN}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    print(f"  {Colors.CYAN}Root: {ROOT_DIR}{Colors.END}")

    all_results = []

    # Run all audits
    all_results.append(audit_dna_engine())
    all_results.append(audit_zotero_sentinel())
    all_results.append(audit_google_bridge())
    all_results.append(audit_red_thread())

    # Print summary
    all_healthy = print_summary(all_results)

    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.END}\n")

    # Return exit code based on health
    return 0 if all_healthy else 1


if __name__ == "__main__":
    sys.exit(main())
