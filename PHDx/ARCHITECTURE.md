# PHDx Technical & Feature Architecture

> **Version**: 1.0
> **Last Updated**: January 2026
> **Status**: Living Document

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Technology Stack](#3-technology-stack)
4. [Core Architecture](#4-core-architecture)
5. [Feature Modules](#5-feature-modules)
6. [Data Architecture](#6-data-architecture)
7. [API Specification](#7-api-specification)
8. [Frontend Architecture](#8-frontend-architecture)
9. [Security & Privacy](#9-security--privacy)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Integration Points](#11-integration-points)
12. [Development Roadmap](#12-development-roadmap)

---

## 1. Executive Summary

### 1.1 What is PHDx?

PHDx is an **AI-powered PhD Thesis Command Center** designed specifically for doctoral candidates to manage, draft, and refine their thesis work in compliance with **Oxford Brookes University** standards. It serves as an intelligent assistant that maintains writing consistency, processes supervisor feedback, and ensures academic integrity throughout the thesis writing process.

### 1.2 Core Value Propositions

| Feature | Description |
|---------|-------------|
| **Linguistic Fingerprinting** | Analyzes and maintains author's unique writing style ("DNA") across all chapters |
| **Multi-Model AI Routing** | Intelligently routes tasks to Claude, GPT-4, or Gemini based on task requirements |
| **Supervisor Feedback Loop** | Processes feedback using Traffic Light System (Red/Amber/Green) for prioritization |
| **Academic Compliance** | Evaluates thesis against Oxford Brookes PhD marking criteria |
| **Citation Management** | Integrates with Zotero for "Cite Them Right" formatting standards |
| **Privacy-First Design** | Scrubs PII from all text before sending to external AI services |
| **Vector-Based Continuity** | Detects logical contradictions across long thesis documents |

### 1.3 Target Users

- PhD candidates at Oxford Brookes University
- Doctoral researchers requiring academic writing assistance
- Students managing complex, multi-chapter thesis documents

---

## 2. System Overview

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                 │
├─────────────────────────────┬───────────────────────────────────────────────┤
│    Streamlit Dashboard      │           Next.js Web Client                  │
│    (Interactive UI)         │           (Modern SPA)                        │
│    Port: 8501               │           Port: 3000                          │
└─────────────┬───────────────┴───────────────────┬───────────────────────────┘
              │                                   │
              └─────────────────┬─────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│                     FastAPI Server (Port: 8000)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Endpoints: /health | /status | /generate | /files | /auth | /sync  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM GATEWAY LAYER                                   │
│                    (Intelligent Model Routing)                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐                   │
│  │   Claude API  │  │  OpenAI API   │  │  Gemini API   │                   │
│  │  (Anthropic)  │  │   (GPT-4o)    │  │   (Google)    │                   │
│  │  [Drafting]   │  │  [Auditing]   │  │ [Large Ctx]   │                   │
│  └───────────────┘  └───────────────┘  └───────────────┘                   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CORE ENGINE LAYER                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ DNA Engine  │ │  Auditor    │ │  Feedback   │ │ Red Thread  │           │
│  │ (Style)     │ │  (Criteria) │ │  Processor  │ │  (Logic)    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  Airlock    │ │  Citations  │ │   Ethics    │ │Transparency │           │
│  │ (Google)    │ │  (Zotero)   │ │  (Privacy)  │ │  (Logging)  │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                          │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐       │
│  │   Vector Store    │  │   File Storage    │  │  External APIs    │       │
│  │ ChromaDB/Pinecone │  │ drafts/ feedback/ │  │ Google Drive/Docs │       │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Project Directory Structure

```
/home/user/phdx/
├── PHDx/                          # Main application directory
│   ├── api/                       # FastAPI backend service
│   │   └── server.py              # RESTful API endpoints
│   ├── core/                      # Core business logic (~7,400 lines)
│   │   ├── dna_engine.py          # Linguistic fingerprint analyzer
│   │   ├── auditor.py             # Oxford Brookes criteria evaluator
│   │   ├── citations.py           # Zotero citation management
│   │   ├── feedback_processor.py  # Supervisor feedback analysis
│   │   ├── supervisor_loop.py     # Feedback mapping engine
│   │   ├── red_thread.py          # Logical continuity checker
│   │   ├── llm_gateway.py         # Multi-model routing system
│   │   ├── airlock.py             # Google OAuth + Drive integration
│   │   ├── vector_store.py        # ChromaDB/Pinecone abstraction
│   │   ├── ethics_utils.py        # PII anonymization
│   │   ├── transparency.py        # AI usage logging
│   │   └── secrets_utils.py       # Secret management
│   ├── ui/                        # Streamlit UI components
│   │   ├── dashboard.py           # Main Streamlit application
│   │   └── styles.py              # UI styling utilities
│   ├── web_client/                # Next.js frontend (v14)
│   │   ├── app/                   # Next.js app router
│   │   ├── components/            # React components
│   │   └── package.json           # Node dependencies
│   ├── data/                      # Generated data storage
│   ├── drafts/                    # Thesis chapter documents
│   ├── feedback/                  # Supervisor feedback documents
│   ├── tests/                     # Unit tests
│   ├── config/                    # Configuration files
│   ├── Dockerfile                 # Production container
│   ├── docker-compose.yml         # Local development
│   ├── requirements.txt           # Python dependencies
│   ├── app.py                     # Streamlit entry point
│   └── run_server.py              # FastAPI development server
├── railway.json                   # Railway.app deployment
└── Dockerfile.railway             # FastAPI backend container
```

---

## 3. Technology Stack

### 3.1 Backend Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Runtime** | Python | 3.11 | Core application runtime |
| **Web Framework** | FastAPI | Latest | RESTful API service |
| **UI Framework** | Streamlit | Latest | Interactive dashboard |
| **LLM - Primary** | Anthropic Claude | sonnet-4-20250514 | Prose drafting & generation |
| **LLM - Secondary** | OpenAI GPT-4o | Latest | Auditing & logic checking |
| **LLM - Extended** | Google Gemini | Latest | Large context window tasks |
| **Vector DB - Local** | ChromaDB | Latest | Local development embeddings |
| **Vector DB - Cloud** | Pinecone | Latest | Production embeddings |
| **Embeddings** | sentence-transformers | Latest | Text vectorization |
| **NLP** | spaCy | Latest | Named Entity Recognition |
| **Document Processing** | python-docx, pypdf | Latest | DOCX/PDF parsing |

### 3.2 Frontend Technologies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Framework** | Next.js | 14.0.4 | React-based SPA |
| **Language** | TypeScript | 5.x | Type-safe JavaScript |
| **UI Library** | React | 18.x | Component framework |
| **Styling** | TailwindCSS | 3.3.0 | Utility-first CSS |
| **Icons** | Lucide React | Latest | Icon library |

### 3.3 Infrastructure & DevOps

| Category | Technology | Purpose |
|----------|------------|---------|
| **Containerization** | Docker | Application packaging |
| **Orchestration** | Docker Compose | Local multi-container setup |
| **Cloud Platform** | Railway.app | Production deployment |
| **Reverse Proxy** | Traefik v2.10 | HTTPS & load balancing |
| **SSL/TLS** | Let's Encrypt | Certificate automation |
| **Version Control** | Git | Source code management |

### 3.4 External Integrations

| Service | Purpose | Authentication |
|---------|---------|----------------|
| **Google Drive/Docs** | Document storage & editing | OAuth 2.0 |
| **Zotero** | Citation management | API Key |
| **Anthropic API** | Claude AI access | API Key |
| **OpenAI API** | GPT-4 access | API Key |
| **Pinecone** | Vector database | API Key |

---

## 4. Core Architecture

### 4.1 Request Flow Architecture

```
User Request
     │
     ▼
┌────────────────────┐
│   UI Layer         │  (Streamlit/Next.js)
│   - Input capture  │
│   - Validation     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   API Gateway      │  (FastAPI)
│   - Authentication │
│   - Rate limiting  │
│   - Request routing│
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   Ethics Layer     │  (ethics_utils.py)
│   - PII detection  │
│   - Anonymization  │
│   - Content filter │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   LLM Gateway      │  (llm_gateway.py)
│   - Token counting │
│   - Model selection│
│   - Request routing│
└─────────┬──────────┘
          │
          ├─────────────────────┬─────────────────────┐
          ▼                     ▼                     ▼
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│  Claude API    │   │  OpenAI API    │   │  Gemini API    │
│  (Drafting)    │   │  (Auditing)    │   │  (Large Ctx)   │
└────────────────┘   └────────────────┘   └────────────────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                                ▼
┌────────────────────┐
│ Transparency Layer │  (transparency.py)
│   - Usage logging  │
│   - Audit trail    │
│   - AI declaration │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   Response Layer   │
│   - Formatting     │
│   - Error handling │
│   - Client return  │
└────────────────────┘
```

### 4.2 Multi-Model Routing Logic

The LLM Gateway implements intelligent model selection based on:

```python
# Routing Decision Tree
def select_model(task_type: str, token_count: int) -> str:

    # Rule 1: Heavy Lift (>30k tokens) → Gemini
    if token_count > 30_000:
        return "gemini"

    # Rule 2: Drafting tasks → Claude
    if task_type in ["draft", "prose", "generate", "write"]:
        return "claude"

    # Rule 3: Analysis tasks → GPT-4
    if task_type in ["audit", "analyze", "critique", "logic"]:
        return "gpt-4"

    # Default: Claude for general tasks
    return "claude"
```

**Model Specializations:**

| Model | Best For | Token Limit | Strengths |
|-------|----------|-------------|-----------|
| **Claude** | Prose generation, creative writing | ~200k | Natural language flow, style consistency |
| **GPT-4** | Logical analysis, auditing, critique | ~128k | Structured reasoning, accuracy |
| **Gemini** | Large document processing | ~1M+ | Extended context window |

### 4.3 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE MODULES                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────┐     writes to      ┌─────────────┐
│ DNA Engine  │ ─────────────────▶ │ author_dna  │
│             │                    │   .json     │
└──────┬──────┘                    └─────────────┘
       │ style reference
       ▼
┌─────────────┐     evaluates      ┌─────────────┐
│  Auditor    │ ─────────────────▶ │ audit_      │
│             │                    │ report.md   │
└──────┬──────┘                    └─────────────┘
       │ criteria scoring
       ▼
┌─────────────┐     indexes        ┌─────────────┐
│ Red Thread  │ ─────────────────▶ │Vector Store │
│  Engine     │                    │ChromaDB/    │
└──────┬──────┘                    │Pinecone     │
       │ continuity check          └─────────────┘
       ▼
┌─────────────┐     processes      ┌─────────────┐
│  Feedback   │ ─────────────────▶ │  feedback/  │
│  Processor  │◀──────────────────│  documents  │
└──────┬──────┘     watches        └─────────────┘
       │ maps to drafts
       ▼
┌─────────────┐     syncs          ┌─────────────┐
│  Airlock    │ ◀────────────────▶ │Google Drive │
│  (OAuth)    │                    │   / Docs    │
└─────────────┘                    └─────────────┘
```

---

## 5. Feature Modules

### 5.1 DNA Engine (Linguistic Fingerprinting)

**Purpose:** Analyzes and captures the author's unique writing style to maintain consistency across thesis chapters.

**File:** `core/dna_engine.py`

**Metrics Captured:**

| Metric | Description | Example Output |
|--------|-------------|----------------|
| **Sentence Complexity** | Average length, distribution analysis | `avg_length: 21.32 words` |
| **Hedging Analysis** | Academic hedging phrase frequency | `"arguably": 6, "potentially": 3` |
| **Transition Vocabulary** | Categorized connector words | `contrast: 15, addition: 12` |
| **Deep Analysis** | AI-powered voice/tone analysis | `formal, analytical, cautious` |

**Analysis Categories:**

```
Transition Types:
├── Addition      (furthermore, moreover, additionally)
├── Contrast      (however, nevertheless, conversely)
├── Cause-Effect  (therefore, consequently, thus)
├── Sequence      (firstly, subsequently, finally)
├── Emphasis      (indeed, notably, significantly)
├── Example       (for instance, specifically, such as)
└── Conclusion    (in summary, ultimately, overall)
```

**Output Schema:**
```json
{
  "metadata": {
    "documents_analyzed": ["chapter1.docx", "chapter2.docx"],
    "total_word_count": 4099,
    "analysis_version": "1.0"
  },
  "sentence_complexity": {
    "average_length": 21.32,
    "total_sentences": 192,
    "length_distribution": {
      "short (1-10 words)": 21,
      "medium (11-20 words)": 65,
      "long (21-30 words)": 83,
      "very_long (31+ words)": 23
    }
  },
  "hedging_analysis": {
    "phrases_found": {...},
    "hedging_density_per_1000_words": 9.76
  },
  "transition_vocabulary": {
    "by_category": {...},
    "preferred_categories": ["contrast", "addition"]
  },
  "claude_deep_analysis": {
    "voice": "formal academic",
    "tone": "analytical",
    "argumentation_style": "evidence-based"
  }
}
```

---

### 5.2 Auditor Module (Academic Compliance)

**Purpose:** Evaluates thesis content against Oxford Brookes University PhD marking criteria.

**File:** `core/auditor.py`

**Marking Criteria Framework:**

| Criterion | Weight | Key Indicators |
|-----------|--------|----------------|
| **Originality** | 35% | Novel contribution, methodology innovation, synthesis |
| **Criticality** | 35% | Critical analysis, literature engagement, argumentation |
| **Rigour** | 30% | Research design, methodology soundness, evidence quality |

**Grade Descriptors:**

| Grade | Description | Score Range |
|-------|-------------|-------------|
| Excellent | Outstanding achievement | 70-100 |
| Good | Clear competence | 60-69 |
| Satisfactory | Meets requirements | 50-59 |
| Borderline | Requires improvement | 40-49 |
| Unsatisfactory | Does not meet standards | 0-39 |

**Output Format:**
```markdown
# Thesis Audit Report

## Overall Assessment
Grade: Good (65/100)

## Criterion Breakdown

### Originality (35%)
Score: 68/100
- Novel methodology identified
- Synthesis requires strengthening
- Recommendations: [...]

### Criticality (35%)
Score: 62/100
- Literature engagement adequate
- Argumentation needs more depth
- Recommendations: [...]

### Rigour (30%)
Score: 65/100
- Research design sound
- Evidence well-documented
- Recommendations: [...]
```

---

### 5.3 Feedback Processor (Supervisor Integration)

**Purpose:** Processes supervisor feedback and categorizes it using a Traffic Light System for prioritization.

**File:** `core/feedback_processor.py`

**Traffic Light System:**

| Color | Meaning | Priority | Action Required |
|-------|---------|----------|-----------------|
| **Red** | Critical structural/theoretical issues | High | Immediate revision |
| **Amber** | Stylistic or citation corrections | Medium | Review and address |
| **Green** | Positive reinforcement | Low | Maintain approach |

**Feedback Categories:**

```
Categories:
├── major_structural    → Red light
├── theoretical         → Red light
├── minor_stylistic     → Amber light
├── citation_format     → Amber light
├── positive_feedback   → Green light
└── clarification       → Amber light
```

**Data Model:**
```python
@dataclass
class FeedbackItem:
    id: str                    # Unique identifier
    text: str                  # Feedback content
    category: str              # Classification
    traffic_light: str         # red | amber | green
    priority: str              # high | medium | low
    chapter: str               # Target chapter
    section: str               # Target section
    target_paragraph: str      # Specific location
    action_required: str       # Required response
    resolved: bool = False     # Resolution status
```

---

### 5.4 Supervisor Loop (Feedback Watch)

**Purpose:** Monitors the `/feedback` directory for new supervisor feedback and automatically processes it.

**File:** `core/supervisor_loop.py`

**Workflow:**

```
┌────────────────────┐
│  Watch /feedback/  │
│     directory      │
└─────────┬──────────┘
          │ New file detected
          ▼
┌────────────────────┐
│  Calculate file    │
│     hash (MD5)     │
└─────────┬──────────┘
          │ Check cache
          ▼
┌────────────────────┐
│  Parse document    │
│  (PDF/DOCX/TXT)    │
└─────────┬──────────┘
          │ Extract text
          ▼
┌────────────────────┐
│  Send to Claude    │
│  for analysis      │
└─────────┬──────────┘
          │ Structured output
          ▼
┌────────────────────┐
│  Map to drafts     │
│  in /drafts/       │
└─────────┬──────────┘
          │ Generate suggestions
          ▼
┌────────────────────┐
│  Store in cache    │
│  with file hash    │
└────────────────────┘
```

**Features:**
- File change detection via MD5 hashing
- Incremental processing (only new/changed files)
- Automatic draft mapping
- Revision suggestion generation

---

### 5.5 Red Thread Engine (Logical Continuity)

**Purpose:** Ensures logical consistency across thesis chapters by detecting contradictions and maintaining argumentative coherence.

**File:** `core/red_thread.py`

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    RED THREAD ENGINE                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   DOCX      │────▶│  Paragraph  │────▶│  Embedding  │   │
│  │   Parser    │     │  Extractor  │     │  Generator  │   │
│  └─────────────┘     └─────────────┘     └──────┬──────┘   │
│                                                  │          │
│                                                  ▼          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              VECTOR STORE                            │   │
│  │  ┌───────────────┐  ┌───────────────┐              │   │
│  │  │   ChromaDB    │  │   Pinecone    │              │   │
│  │  │   (Local)     │  │   (Cloud)     │              │   │
│  │  └───────────────┘  └───────────────┘              │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         SIMILARITY SEARCH ENGINE                     │   │
│  │  - Find semantically similar passages               │   │
│  │  - Detect potential contradictions                  │   │
│  │  - Track argumentative threads                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Capabilities:**
- Index all `.docx` files from `/drafts`
- Vector embeddings via sentence-transformers
- Semantic similarity search
- Contradiction detection across chapters
- Automatic backend selection (ChromaDB vs Pinecone)

---

### 5.6 Airlock Module (Google Integration)

**Purpose:** Manages Google Drive and Google Docs integration for document storage and synchronization.

**File:** `core/airlock.py`

**Supported Operations:**

| Operation | Description |
|-----------|-------------|
| `authenticate()` | OAuth 2.0 flow with Google |
| `list_recent_docs()` | Fetch recent Docs and Sheets |
| `load_google_doc(id)` | Extract full text from Google Doc |
| `upload_local_file()` | Upload .docx/.pdf/.txt to Drive |
| `sync_to_doc()` | Push content back to Google Docs |

**Authentication Flow:**

```
User
  │
  │ Clicks "Connect Google"
  ▼
┌────────────────────┐
│  OAuth 2.0 Flow    │
│  (Web redirect)    │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Google Auth       │
│  Consent Screen    │
└─────────┬──────────┘
          │ Authorization code
          ▼
┌────────────────────┐
│  Token Exchange    │
│  (credentials)     │
└─────────┬──────────┘
          │ Access + Refresh token
          ▼
┌────────────────────┐
│  Store in          │
│  config/token.json │
└────────────────────┘
```

---

### 5.7 Citations Module (Zotero Integration)

**Purpose:** Manages academic citations via Zotero integration with Oxford Brookes "Cite Them Right" formatting.

**File:** `core/citations.py`

**Features:**
- Connect to Zotero library via API
- Fetch citation metadata
- Format citations per Oxford Brookes standards
- Generate mock/synthetic sources for testing
- Support multiple citation styles

**Integration:**
```python
# Example usage
from core.citations import ZoteroClient

client = ZoteroClient(user_id, api_key)
citations = client.get_library_items()
formatted = client.format_cite_them_right(citation)
```

---

### 5.8 Ethics & Privacy Module

**Purpose:** Ensures privacy compliance by anonymizing PII before sending content to external AI services.

**File:** `core/ethics_utils.py`

**PII Detection & Scrubbing:**

| PII Type | Pattern | Replacement |
|----------|---------|-------------|
| Email addresses | `*@*.*` | `[EMAIL]` |
| Phone numbers | UK/US formats | `[PHONE]` |
| Postcodes | UK format | `[POSTCODE]` |
| NI Numbers | UK format | `[NI_NUMBER]` |
| Credit cards | 16-digit | `[CREDIT_CARD]` |
| IP addresses | IPv4/IPv6 | `[IP_ADDRESS]` |
| URLs | http(s):// | `[URL]` |
| Dates of birth | Various formats | `[DOB]` |
| Student IDs | University format | `[STUDENT_ID]` |

**Processing Pipeline:**
```
Input Text
    │
    ▼
┌────────────────────┐
│  Regex Detection   │ ← Pattern matching
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  spaCy NER         │ ← Entity recognition
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Token Replacement │ ← Anonymization
└─────────┬──────────┘
          │
          ▼
Scrubbed Text → LLM API
```

---

### 5.9 Transparency Module (AI Usage Logging)

**Purpose:** Maintains comprehensive logs of all AI interactions for academic integrity and Oxford Brookes compliance.

**File:** `core/transparency.py`

**Logged Information:**

| Field | Description |
|-------|-------------|
| `id` | Unique usage identifier |
| `timestamp` | ISO 8601 timestamp |
| `task_type` | Classification of AI task |
| `task_description` | Human-readable description |
| `input_word_count` | Words sent to AI |
| `output_word_count` | Words received from AI |
| `ai_contribution_percent` | Calculated contribution % |
| `chapter` | Target thesis chapter |
| `section` | Target section |
| `model_used` | AI model identifier |
| `accepted` | Whether output was used |

**Task Types:**
- `draft_generation`
- `style_check`
- `feedback_suggestion`
- `citation_format`
- `logic_analysis`
- `grammar_correction`

---

## 6. Data Architecture

### 6.1 Data Flow Diagram

```
                    EXTERNAL DATA SOURCES
┌───────────────────────────────────────────────────────────┐
│  Google Drive  │  Zotero Library  │  Supervisor PDFs      │
└───────┬────────┴────────┬─────────┴──────────┬────────────┘
        │                 │                    │
        ▼                 ▼                    ▼
┌───────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                         │
│  Airlock Parser  │  Citation Client  │  Feedback Parser   │
└───────┬────────────────────────────────────────┬──────────┘
        │                                        │
        ▼                                        ▼
┌───────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                        │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Ethics    │  │   DNA       │  │   Auditor   │       │
│  │   Scrubber  │  │   Engine    │  │   Module    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
└───────┬────────────────────────────────────────┬──────────┘
        │                                        │
        ▼                                        ▼
┌───────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                           │
│                                                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  /drafts/   │  │   /data/    │  │  /feedback/ │       │
│  │   .docx     │  │  author_dna │  │   processed │       │
│  │   files     │  │  audit_rpt  │  │   feedback  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              VECTOR DATABASE                         │ │
│  │  ChromaDB (local) ←→ Pinecone (cloud)               │ │
│  │  - Paragraph embeddings                              │ │
│  │  - Semantic search index                             │ │
│  │  - Contradiction detection                           │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                            │
└───────────────────────────────────────────────────────────┘
```

### 6.2 File Storage Structure

```
/home/user/phdx/PHDx/
├── data/
│   ├── author_dna.json          # Linguistic profile
│   ├── audit_report.md          # Latest audit
│   ├── ai_usage_log.json        # Transparency log
│   └── mock_results.csv         # Test data
│
├── drafts/
│   ├── chapter_1_intro.docx
│   ├── chapter_2_literature.docx
│   ├── chapter_3_methodology.docx
│   └── ...
│
├── feedback/
│   ├── supervisor_feedback_2024_01.pdf
│   ├── comments_chapter_2.docx
│   └── ...
│
├── config/
│   ├── token.json               # Google OAuth tokens
│   ├── credentials.json         # Google app credentials
│   └── ...
│
└── snapshots/                   # Version snapshots
    ├── chapter_1_2024-01-15.docx
    └── ...
```

### 6.3 Vector Database Schema

**Collection:** `phdx-thesis`

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique paragraph ID |
| `text` | string | Paragraph content |
| `embedding` | vector[384] | sentence-transformer embedding |
| `source_file` | string | Original .docx filename |
| `chapter` | string | Chapter identifier |
| `paragraph_index` | int | Position in document |
| `created_at` | timestamp | Indexing timestamp |

---

## 7. API Specification

### 7.1 Endpoint Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/status` | System status + available models |
| `GET` | `/auth/google` | Initiate Google OAuth |
| `GET` | `/files/recent` | List recent documents |
| `POST` | `/generate` | Generate content |
| `POST` | `/snapshot` | Save version snapshot |
| `POST` | `/sync/google` | Sync to Google Docs |

### 7.2 Detailed Endpoint Specifications

#### GET /health
```json
// Response
{
  "status": "healthy"
}
```

#### GET /status
```json
// Response
{
  "status": "operational",
  "available_models": ["claude", "gpt-4", "gemini"],
  "google_connected": true,
  "vector_store": "pinecone",
  "version": "1.0.0"
}
```

#### GET /files/recent
```json
// Query parameters
limit: int = 10

// Response
[
  {
    "id": "1abc2def3ghi",
    "name": "Chapter 1 - Introduction",
    "source": "google_docs",
    "path": null,
    "modified": "2024-01-15T10:30:00Z",
    "size_bytes": 45678
  }
]
```

#### POST /generate
```json
// Request
{
  "doc_id": "1abc2def3ghi",
  "prompt": "Expand on the theoretical framework",
  "model": "claude"  // Optional: claude | gpt | gemini
}

// Response
{
  "success": true,
  "text": "Generated content...",
  "model": "claude-sonnet-4-20250514",
  "tokens_used": 1542,
  "scrubbed": true,
  "error": null
}
```

#### POST /snapshot
```json
// Request
{
  "doc_id": "1abc2def3ghi",
  "timestamp": "2024-01-15T10:30:00Z",
  "content": "Document content..."
}

// Response
{
  "success": true,
  "filename": "chapter_1_2024-01-15.docx",
  "path": "/snapshots/chapter_1_2024-01-15.docx",
  "size_bytes": 45678,
  "error": null
}
```

#### POST /sync/google
```json
// Request
{
  "doc_id": "1abc2def3ghi",
  "content": "Updated content...",
  "section_title": "3.2 Methodology"
}

// Response
{
  "success": true,
  "doc_url": "https://docs.google.com/document/d/1abc2def3ghi",
  "characters_synced": 5432,
  "error": null
}
```

### 7.3 Error Response Format
```json
{
  "success": false,
  "error": "Error message description",
  "error_code": "AUTH_FAILED",
  "details": {}
}
```

---

## 8. Frontend Architecture

### 8.1 Next.js Application Structure

```
web_client/
├── app/
│   ├── page.tsx              # Main dashboard
│   ├── layout.tsx            # Root layout + metadata
│   └── globals.css           # Global styles
│
├── components/
│   ├── DraftingEditor.tsx    # Text editor with AI integration
│   ├── ModelSwitcher.tsx     # AI model selection dropdown
│   ├── Sidebar.tsx           # Document browser
│   └── index.ts              # Component exports
│
├── public/
│   └── assets/               # Static files
│
├── styles/
│   └── tailwind.css          # TailwindCSS entry
│
├── package.json              # Dependencies
├── tailwind.config.js        # Tailwind configuration
├── tsconfig.json             # TypeScript config
└── next.config.js            # Next.js config
```

### 8.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        App Layout                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Header                              │  │
│  │  [Logo]  [API Status]  [Model Selector]  [Settings]   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌───────────────────────────────────────┐ │
│  │             │  │                                        │ │
│  │  Sidebar    │  │         Main Content Area             │ │
│  │             │  │                                        │ │
│  │ ┌─────────┐ │  │  ┌──────────────────────────────────┐ │ │
│  │ │Recent   │ │  │  │       Drafting Editor            │ │ │
│  │ │Docs     │ │  │  │                                  │ │ │
│  │ │         │ │  │  │  ┌─────────────────────────┐    │ │ │
│  │ │ - Doc 1 │ │  │  │  │    Prompt Input         │    │ │ │
│  │ │ - Doc 2 │ │  │  │  └─────────────────────────┘    │ │ │
│  │ │ - Doc 3 │ │  │  │                                  │ │ │
│  │ └─────────┘ │  │  │  ┌─────────────────────────┐    │ │ │
│  │             │  │  │  │    Response Output      │    │ │ │
│  │ ┌─────────┐ │  │  │  │                         │    │ │ │
│  │ │Quick    │ │  │  │  └─────────────────────────┘    │ │ │
│  │ │Actions  │ │  │  │                                  │ │ │
│  │ └─────────┘ │  │  └──────────────────────────────────┘ │ │
│  └─────────────┘  └───────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 State Management

| State | Location | Purpose |
|-------|----------|---------|
| `apiStatus` | Component | Connection status indicator |
| `recentFiles` | Component | List of available documents |
| `selectedDoc` | Component | Currently selected document |
| `prompt` | Component | User input text |
| `response` | Component | AI-generated output |
| `selectedModel` | Component | Active AI model |
| `isLoading` | Component | Request status |

### 8.4 API Integration

```typescript
// API Base URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://phdx-api.railway.app';

// Health check on mount
useEffect(() => {
  fetch(`${API_URL}/health`)
    .then(res => res.json())
    .then(data => setApiStatus('online'))
    .catch(() => setApiStatus('offline'));
}, []);

// Generate content
const handleGenerate = async () => {
  const response = await fetch(`${API_URL}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doc_id: selectedDoc?.id,
      prompt,
      model: selectedModel
    })
  });
  const data = await response.json();
  setResponse(data.text);
};
```

---

## 9. Security & Privacy

### 9.1 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Layer 1: Network Security                                   │
│  ├── HTTPS (TLS 1.3) via Traefik                            │
│  ├── Let's Encrypt certificate automation                   │
│  └── CORS policy enforcement                                │
│                                                              │
│  Layer 2: Authentication                                     │
│  ├── Google OAuth 2.0 for Drive access                      │
│  ├── API key validation for external services               │
│  └── Token refresh handling                                  │
│                                                              │
│  Layer 3: Data Protection                                    │
│  ├── PII anonymization before AI processing                 │
│  ├── Secure credential storage (env vars)                   │
│  └── No persistent storage of sensitive data                │
│                                                              │
│  Layer 4: Container Security                                 │
│  ├── Non-root user execution                                │
│  ├── Minimal base images (python:3.11-slim)                 │
│  └── No unnecessary packages                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 Privacy Compliance

| Requirement | Implementation |
|-------------|----------------|
| **GDPR Data Minimization** | Only process necessary thesis content |
| **PII Protection** | Automatic anonymization before LLM calls |
| **AI Transparency** | Full usage logging for academic declaration |
| **Data Retention** | User-controlled local storage |
| **Right to Erasure** | User can delete all local data |

### 9.3 Secret Management

**Environment Variables Required:**

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `PINECONE_API_KEY` | No | Pinecone vector DB (uses ChromaDB if absent) |
| `PINECONE_INDEX` | No | Pinecone index name |
| `ZOTERO_USER_ID` | No | Zotero library access |
| `ZOTERO_API_KEY` | No | Zotero API authentication |
| `GOOGLE_CREDENTIALS_PATH` | No | Path to Google OAuth credentials |

---

## 10. Deployment Architecture

### 10.1 Local Development

```bash
# Terminal 1: Streamlit UI
cd PHDx && streamlit run app.py --server.port 8501

# Terminal 2: FastAPI Backend
cd PHDx && python run_server.py  # Runs on :8000

# Terminal 3: Next.js Frontend (optional)
cd PHDx/web_client && npm run dev  # Runs on :3000
```

### 10.2 Docker Compose (Production)

```yaml
version: '3.8'
services:
  phdx-app:
    build: ./PHDx
    ports:
      - "8501:8501"
    volumes:
      - phdx-data:/app/data
      - phdx-drafts:/app/drafts
      - phdx-feedback:/app/feedback
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]

  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik:/etc/traefik
```

### 10.3 Railway.app Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                    RAILWAY DEPLOYMENT                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Service 1: phdx-streamlit                                   │
│  ├── Dockerfile: PHDx/Dockerfile                            │
│  ├── Port: 8501 (auto-mapped by Railway)                    │
│  └── URL: https://phdx.up.railway.app                       │
│                                                              │
│  Service 2: phdx-api                                         │
│  ├── Dockerfile: Dockerfile.railway (root)                  │
│  ├── Port: 8000 (auto-mapped by Railway)                    │
│  └── URL: https://phdx-api.up.railway.app                   │
│                                                              │
│  Environment Variables (Railway Dashboard):                  │
│  ├── ANTHROPIC_API_KEY=sk-ant-...                           │
│  ├── PINECONE_API_KEY=...                                   │
│  ├── PINECONE_INDEX=phdx-thesis                             │
│  └── GOOGLE_CREDENTIALS_PATH=/app/config/credentials.json   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 10.4 Health Monitoring

| Endpoint | Service | Check Interval |
|----------|---------|----------------|
| `/_stcore/health` | Streamlit | 30s |
| `/health` | FastAPI | 30s |

---

## 11. Integration Points

### 11.1 External Service Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                      PHDX CORE                               │
│                                                              │
│  ┌─────────┐        ┌─────────┐        ┌─────────┐         │
│  │ Airlock │        │ LLM     │        │Citation │         │
│  │ Module  │        │ Gateway │        │ Module  │         │
│  └────┬────┘        └────┬────┘        └────┬────┘         │
│       │                  │                  │               │
└───────┼──────────────────┼──────────────────┼───────────────┘
        │                  │                  │
        ▼                  │                  ▼
┌───────────────┐          │          ┌───────────────┐
│ GOOGLE APIS   │          │          │ ZOTERO API    │
│ ├─ Drive API  │          │          │ ├─ Library    │
│ ├─ Docs API   │          │          │ └─ Citations  │
│ └─ Sheets API │          │          └───────────────┘
└───────────────┘          │
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ ANTHROPIC API │  │ OPENAI API    │  │ GOOGLE AI API │
│ └─ Claude     │  │ └─ GPT-4o     │  │ └─ Gemini     │
└───────────────┘  └───────────────┘  └───────────────┘
```

### 11.2 Integration Authentication Methods

| Service | Auth Method | Credential Type |
|---------|-------------|-----------------|
| Google APIs | OAuth 2.0 | Access + Refresh Token |
| Anthropic | API Key | Bearer Token |
| OpenAI | API Key | Bearer Token |
| Pinecone | API Key | Header |
| Zotero | API Key | Header |

---

## 12. Development Roadmap

### 12.1 Development Phases

| Phase | Status | Features |
|-------|--------|----------|
| **Phase 1** | Completed | Foundation, DNA engine, basic Streamlit UI |
| **Phase 2** | In Progress | Google Drive sync, document management, FastAPI |
| **Phase 3** | Planned | Advanced AI features, style matching, feedback loop |
| **Phase 4** | Planned | Oxford Brookes templates, export features, PDF generation |

### 12.2 Phase 3 Planned Features

- [ ] Real-time collaborative editing
- [ ] Advanced style matching algorithm
- [ ] Automated chapter structure validation
- [ ] Enhanced contradiction detection
- [ ] Supervisor feedback portal

### 12.3 Phase 4 Planned Features

- [ ] Oxford Brookes thesis templates
- [ ] PDF export with proper formatting
- [ ] Table of contents generation
- [ ] Bibliography formatting automation
- [ ] Submission checklist validation

---

## Appendix A: Configuration Files

### A.1 Streamlit Config (`.streamlit/config.toml`)
```toml
[theme]
primaryColor = "#0071ce"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
headless = true
port = 8501
enableCORS = true

[browser]
gatherUsageStats = false
```

### A.2 Docker Compose Full Example
```yaml
version: '3.8'

services:
  phdx-app:
    build:
      context: ./PHDx
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    volumes:
      - phdx-data:/app/data
      - phdx-drafts:/app/drafts
      - phdx-feedback:/app/feedback
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX=${PINECONE_INDEX:-phdx-thesis}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

volumes:
  phdx-data:
  phdx-drafts:
  phdx-feedback:
  letsencrypt:
```

---

## Appendix B: Quick Reference

### B.1 Common Commands

```bash
# Start local development
cd PHDx && streamlit run app.py

# Start API server
cd PHDx && python run_server.py

# Run tests
cd PHDx && pytest tests/

# Build Docker image
docker build -t phdx ./PHDx

# Run with Docker Compose
docker-compose up -d
```

### B.2 Key File Locations

| File | Purpose |
|------|---------|
| `PHDx/app.py` | Streamlit entry point |
| `PHDx/api/server.py` | FastAPI server |
| `PHDx/core/llm_gateway.py` | LLM routing logic |
| `PHDx/core/dna_engine.py` | Style analysis |
| `PHDx/data/author_dna.json` | Stored author profile |
| `PHDx/config/token.json` | Google OAuth tokens |

---

*This document is maintained as part of the PHDx project. For updates, see the Git history.*
