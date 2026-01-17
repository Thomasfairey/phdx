# PHDx Deep Health Check Report

**Generated:** 2026-01-14 11:35:24
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

## ✅ **[PASSED]** DNA Engine

- ✓ Drafts folder exists: 3 .docx files
- ✓ DNA Profile: LOADED
- 
  ═══ Linguistic Summary ═══
-   📊 Total Words Analyzed: 1,507
-   📄 Documents Analyzed: 3
-   📝 Avg Sentence Length: 19.29 words
-   🔮 Hedging Density: 7.96/1000 words
-   🔗 Transition Density: 8.63/1000 words
-   💭 Top Hedges: arguably, potentially, may
-   ➡️ Transition Style: contrast, emphasis, addition

## ❌ **[FAILED]** Zotero Sentinel

- ✓ Credentials: Configured
- ✗ Zotero Connection: FAILED (User ID not found)

**Fix Command:**
```bash
# Check your ZOTERO_USER_ID in .env
# Find it at: https://www.zotero.org/settings/keys
```

## ✅ **[PASSED]** Red Thread Engine

- ✓ ChromaDB: Installed (v1.4.0)
- ✓ ChromaDB: Initialized
- ✓ Write Test: SUCCESS
-   📝 Inserted: "The epistemological foundations of qualitative res..."
- ✓ Read Test: SUCCESS
-   🔍 Retrieved: "The epistemological foundations of qualitative res..."
-   📊 Similarity Score: 44.96%
- ✓ Cleanup: Test collection removed
- 
  Main Collection:
-   📊 Indexed Paragraphs: 0
-   ⚠ Collection empty - run indexer

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
| ✅ Passed | 3 |
| ❌ Failed | 3 |
| ⚠️ Warnings | 0 |
