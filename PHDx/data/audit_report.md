# PHDx Deep Health Check Report

**Generated:** 2026-01-14 11:07:53
**Root Directory:** `/home/user/phd/PHDx`

---

## ❌ **[FAILED]** Environment Variables

- ✓ .env file exists
- ✗ ANTHROPIC_API_KEY: Missing
- ✓ ZOTERO_USER_ID: 1935...
- ✓ ZOTERO_API_KEY: CSlydjmL...ApAE
- ○ GOOGLE_DOC_ID: Not configured (optional)
- ○ GOOGLE_SHEETS_URL: Not configured (optional)
- ✓ GOOGLE_CREDENTIALS_PATH: credentials.json

**Fix Command:**
```bash
nano /home/user/phd/PHDx/.env  # Add missing keys
```

## ❌ **[FAILED]** DNA Engine

- ✓ Drafts folder exists: 0 .docx files
- ✗ DNA Profile: MISSING
-   Status: author_dna.json not generated

**Fix Command:**
```bash
# First add .docx files to /home/user/phd/PHDx/drafts, then:
cd /home/user/phd/PHDx && python core/dna_engine.py
```

## ❌ **[FAILED]** Zotero Sentinel

- ✓ Credentials: Configured
- ✗ Zotero Connection: FAILED (User ID not found)

**Fix Command:**
```bash
# Check your ZOTERO_USER_ID in .env
# Find it at: https://www.zotero.org/settings/keys
```

## ❌ **[FAILED]** Red Thread Engine

- ✓ ChromaDB: Installed (v1.4.0)
- ✗ ChromaDB Test: FAILED
-   Error: Validation error: name: Expected a name containing 3-512 characters from [a-zA-Z0-9._-], starting and ending with a character in [a-zA-Z0-9]. Got: _audit_test_c58bf791

**Fix Command:**
```bash
rm -rf /home/user/phd/PHDx/data/chroma_db && pip install --upgrade chromadb
```

## ❌ **[FAILED]** Google Bridge

- ✗ Credentials: credentials.json not found

**Fix Command:**
```bash
# Setup Google Service Account:
# 1. Go to https://console.cloud.google.com/
# 2. Create project > Enable Docs & Sheets APIs
# 3. Create Service Account > Download JSON key
# 4. Save as credentials.json in PHDx folder
# 5. Share your Doc/Sheet with the service account email
```

## ✅ **[PASSED]** Feedback Processor

- ✓ Feedback folder: /home/user/phd/PHDx/feedback
-   📁 Feedback documents: 0
- ✓ FeedbackProcessor: Loaded
-   📊 Cached items: 0
-   ✅ Resolved: 0
-   ⏳ Unresolved: 0
- ✓ DOCX support: Available
- ⚠ PDF support: pip install pymupdf

---

## Summary

| Status | Count |
|--------|-------|
| ✅ Passed | 1 |
| ❌ Failed | 5 |
| ⚠️ Warnings | 0 |
