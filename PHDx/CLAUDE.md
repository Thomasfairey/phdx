# PHDx - PhD Thesis Orchestrator

## Project Overview

PHDx is a PhD Thesis Command Center designed to assist doctoral candidates in managing, drafting, and refining their thesis work. Built to align with **Oxford Brookes University** standards and guidelines.

## Purpose

This orchestrator serves as an intelligent companion throughout the PhD thesis journey, providing:

- **Linguistic Consistency**: Maintains author voice and academic tone across all chapters
- **Structural Guidance**: Ensures adherence to Oxford Brookes thesis formatting requirements
- **Draft Management**: Centralizes all thesis drafts and revisions
- **AI-Assisted Writing**: Leverages Claude for intelligent feedback and suggestions

## Architecture

```
PHDx/
├── core/               # Core functionality and engines
│   └── dna_engine.py   # Linguistic fingerprint analyzer
├── ui/                 # User interface components
│   └── dashboard.py    # Streamlit-based command center
├── data/               # Data storage
│   ├── local_cache/    # Cached processing results
│   └── author_dna.json # Author's linguistic profile
├── drafts/             # Thesis draft documents (.docx)
├── .claude/            # Claude Code configuration
│   └── rules/          # Custom rules and guidelines
├── .env                # Environment variables (API keys)
├── requirements.txt    # Python dependencies
└── CLAUDE.md           # This file
```

## Oxford Brookes Standards

This tool is configured to support Oxford Brookes University PhD thesis requirements:

### Formatting Requirements
- A4 paper size
- 1.5 or double line spacing for main text
- Minimum margins: 40mm (left/binding edge), 20mm (other edges)
- Font size: 11-12pt for main text
- Page numbers in consistent position

### Structure Guidelines
- Title page with prescribed information
- Abstract (max 300 words)
- Table of contents
- List of figures/tables (if applicable)
- Main chapters
- References (consistent citation style)
- Appendices (if applicable)

### Word Count
- Typically 80,000-100,000 words (field-dependent)
- Excludes bibliography and appendices

## Core Components

### DNA Engine (`core/dna_engine.py`)

Analyzes the author's writing style to create a linguistic fingerprint:

- **Sentence Complexity**: Average sentence length and structure patterns
- **Hedging Frequency**: Academic hedging language (e.g., "suggests", "arguably", "potentially")
- **Transition Vocabulary**: Characteristic linking words and phrases
- **Voice Consistency**: First/third person usage patterns

### Dashboard (`ui/dashboard.py`)

Streamlit-based interface providing:

- Data source management (Google Drive, local files)
- Drafting pane with AI assistance
- Progress tracking
- Style consistency checks

## Environment Variables

Required in `.env`:

```
ANTHROPIC_API_KEY=your_api_key_here
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

## Usage

```bash
# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Run the dashboard
streamlit run ui/dashboard.py
```

## Development Phases

- [x] **Phase 1**: Foundation - Core structure, DNA engine, basic UI
- [ ] **Phase 2**: Integration - Google Drive sync, document management
- [ ] **Phase 3**: Intelligence - Advanced AI features, style matching
- [ ] **Phase 4**: Polish - Oxford Brookes templates, export features

## Contributing

This is a personal PhD thesis management tool. Configuration and customization should be done through the `.claude/rules/` directory.
