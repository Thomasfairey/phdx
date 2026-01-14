"""
PHDx Dashboard v2 - PhD Thesis Command Center

Streamlit-based interface with Glassmorphism UI, Zotero integration,
and Google Sheets data injection.
"""

import json
import os
import sys
from pathlib import Path

import streamlit as st

# Add core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.citations import ZoteroSentinel, render_sentinel_widget
from core.red_thread import RedThreadEngine

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DRAFTS_DIR = ROOT_DIR / "drafts"
DNA_PATH = DATA_DIR / "author_dna.json"

# Page configuration
st.set_page_config(
    page_title="PHDx - PhD Thesis Command Center",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# GLASSMORPHISM CSS - Deep Charcoal (#121212) + Soft Blue (#00d4ff)
# ============================================================================
st.markdown("""
<style>
    /* Import professional sans-serif font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global font and background */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    /* Main app background - Deep Charcoal */
    .stApp {
        background: linear-gradient(135deg, #121212 0%, #1a1a2e 50%, #16213e 100%);
        background-attachment: fixed;
    }

    /* Glassmorphism card effect */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Main header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.25rem;
        letter-spacing: -0.02em;
    }

    .sub-header {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 2rem;
        font-weight: 400;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(18, 18, 18, 0.95);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(0, 212, 255, 0.2);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: rgba(255, 255, 255, 0.9);
    }

    /* Text colors for dark theme */
    .stMarkdown, .stText, p, span, label {
        color: rgba(255, 255, 255, 0.87) !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* Accent color - Soft Blue */
    .accent-blue {
        color: #00d4ff;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-weight: 600;
    }

    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.7) !important;
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 168, 204, 0.2) 100%);
        color: #00d4ff;
        border: 1px solid rgba(0, 212, 255, 0.4);
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        backdrop-filter: blur(5px);
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.4) 0%, rgba(0, 168, 204, 0.4) 100%);
        border-color: #00d4ff;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        transform: translateY(-1px);
    }

    /* Primary action button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 100%);
        color: #121212;
        border: none;
        font-weight: 600;
    }

    /* Text area styling */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 12px;
        color: rgba(255, 255, 255, 0.9);
        font-family: 'Inter', sans-serif;
    }

    .stTextArea textarea:focus {
        border-color: #00d4ff;
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
    }

    /* Select box styling */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 8px;
    }

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 12px;
        padding: 4px;
        gap: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        color: rgba(255, 255, 255, 0.6);
        border-radius: 8px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(0, 212, 255, 0.2);
        color: #00d4ff !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.9);
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00d4ff 0%, #00a8cc 100%);
    }

    /* Divider */
    hr {
        border-color: rgba(0, 212, 255, 0.2);
    }

    /* Warning/Info boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 8px;
    }

    /* Code blocks */
    .stCodeBlock {
        background: rgba(0, 0, 0, 0.3) !important;
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 8px;
    }

    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(0, 212, 255, 0.3);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 212, 255, 0.5);
    }

    /* Special glow effect for important elements */
    .glow-effect {
        box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
    }

    /* Stats cards row */
    .stats-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }

    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 1rem 1.5rem;
        flex: 1;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d4ff;
    }

    .stat-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "drafting_text" not in st.session_state:
    st.session_state.drafting_text = ""
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = "Chapter 1: Introduction"
if "zotero_sentinel" not in st.session_state:
    st.session_state.zotero_sentinel = ZoteroSentinel()
if "red_thread_engine" not in st.session_state:
    st.session_state.red_thread_engine = RedThreadEngine()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def load_author_dna() -> dict | None:
    """Load the author DNA profile if it exists."""
    if DNA_PATH.exists():
        with open(DNA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def inject_sheets_data() -> dict | None:
    """
    Pull active row from Google Sheets and generate synthesis.

    Returns synthesized text in author's DNA voice.
    """
    import anthropic
    from dotenv import load_dotenv

    load_dotenv()

    # Check for Google Sheets credentials
    sheets_url = os.getenv("GOOGLE_SHEETS_URL")
    if not sheets_url:
        return {"error": "GOOGLE_SHEETS_URL not configured in .env"}

    # Load author DNA for voice matching
    dna = load_author_dna()
    if not dna:
        return {"error": "Author DNA profile not found. Run dna_engine.py first."}

    # Get Claude client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not configured"}

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Try to connect to Google Sheets
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

        if not Path(creds_path).exists():
            return {"error": f"Google credentials not found at {creds_path}"}

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        gc = gspread.authorize(creds)

        # Open sheet and get active/first row with data
        sheet = gc.open_by_url(sheets_url).sheet1
        records = sheet.get_all_records()

        if not records:
            return {"error": "No data found in sheet"}

        # Get the first row (or could be configured to get "active" row)
        active_row = records[0]

        # Prepare DNA context
        dna_context = json.dumps(dna.get("claude_deep_analysis", {}), indent=2)

        # Generate synthesis with Claude
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""You are writing a critical synthesis for a PhD thesis. You must match the author's unique writing style.

AUTHOR'S WRITING DNA:
{dna_context}

Linguistic fingerprint:
- Average sentence length: {dna.get('sentence_complexity', {}).get('average_length', 20)} words
- Hedging density: {dna.get('hedging_analysis', {}).get('hedging_density_per_1000_words', 5)} per 1000 words
- Preferred transitions: {', '.join(dna.get('transition_vocabulary', {}).get('preferred_categories', ['contrast', 'addition'])[:3])}

DATA TO SYNTHESIZE:
{json.dumps(active_row, indent=2)}

Write a 300-word critical synthesis of this data that:
1. Matches the author's sentence structure and complexity
2. Uses their characteristic hedging language
3. Employs their preferred transition vocabulary
4. Maintains their academic voice and tone

Write ONLY the synthesis paragraph, no meta-commentary."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        return {
            "success": True,
            "data_row": active_row,
            "synthesis": response.content[0].text
        }

    except ImportError:
        return {"error": "gspread not installed. Run: pip install gspread"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# SIDEBAR
# ============================================================================
def render_sidebar():
    """Render the sidebar with data sources and Zotero Sentinel."""
    with st.sidebar:
        st.markdown("## 📁 Data Sources")
        st.markdown("---")

        # Local Files Section
        st.markdown("### Local Files")

        drafts_count = len(list(DRAFTS_DIR.glob("*.docx"))) if DRAFTS_DIR.exists() else 0
        st.metric("Draft Documents", drafts_count)

        if st.button("📂 Open Drafts Folder", use_container_width=True):
            st.info(f"Drafts location: {DRAFTS_DIR}")

        # DNA Profile status
        dna_exists = DNA_PATH.exists()
        st.markdown(f"**DNA Profile:** {'✅ Generated' if dna_exists else '❌ Not found'}")

        if st.button("🧬 Regenerate DNA Profile", use_container_width=True):
            st.warning("Run `python core/dna_engine.py` to regenerate")

        st.markdown("---")

        # Red Thread Engine
        st.markdown("### 🔴 Red Thread Engine")
        engine = st.session_state.red_thread_engine
        stats = engine.get_stats()
        st.metric("Indexed Paragraphs", stats["total_paragraphs"])

        if st.button("🔄 Re-index Drafts", use_container_width=True):
            with st.spinner("Indexing..."):
                result = engine.index_drafts_folder()
                st.success(f"Indexed {result['paragraphs_indexed']} paragraphs")

        st.markdown("---")

        # Zotero Sentinel Widget
        render_sentinel_widget(
            st.session_state.zotero_sentinel,
            st.session_state.drafting_text,
            st.session_state.current_chapter
        )

        st.markdown("---")

        # Settings
        st.markdown("### ⚙️ Settings")

        st.selectbox(
            "Citation Style",
            ["APA 7th", "Harvard", "Chicago", "MLA", "Oxford"],
            index=0
        )

        st.selectbox(
            "Language",
            ["British English", "American English"],
            index=0
        )


# ============================================================================
# MAIN CONTENT
# ============================================================================
def render_drafting_pane():
    """Render the main drafting pane."""
    st.markdown('<p class="main-header">PHDx</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">PhD Thesis Command Center | Oxford Brookes Standards</p>', unsafe_allow_html=True)

    # Status row
    col1, col2, col3, col4 = st.columns(4)

    dna_profile = load_author_dna()

    with col1:
        st.markdown("**📊 Word Count**")
        if dna_profile:
            st.markdown(f"### {dna_profile['metadata']['total_word_count']:,}")
        else:
            st.markdown("### --")

    with col2:
        st.markdown("**📄 Documents**")
        if dna_profile:
            st.markdown(f"### {len(dna_profile['metadata']['documents_analyzed'])}")
        else:
            st.markdown("### --")

    with col3:
        st.markdown("**📝 Avg Sentence**")
        if dna_profile:
            st.markdown(f"### {dna_profile['sentence_complexity']['average_length']} words")
        else:
            st.markdown("### --")

    with col4:
        st.markdown("**🎯 Target**")
        st.markdown("### 80,000")

    st.markdown("---")

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ Drafting", "🧬 DNA Profile", "📚 Chapters", "📈 Progress"])

    with tab1:
        render_drafting_tab()

    with tab2:
        render_dna_tab(dna_profile)

    with tab3:
        render_chapters_tab()

    with tab4:
        render_progress_tab()


def render_drafting_tab():
    """Render the main drafting interface."""
    st.markdown("### Drafting Pane")

    # Chapter selector
    col1, col2 = st.columns([2, 1])

    with col1:
        chapter = st.selectbox(
            "Working on:",
            [
                "Chapter 1: Introduction",
                "Chapter 2: Literature Review",
                "Chapter 3: Methodology",
                "Chapter 4: Results",
                "Chapter 5: Discussion",
                "Chapter 6: Conclusion",
                "Abstract",
                "Free Writing"
            ],
            key="chapter_select"
        )
        st.session_state.current_chapter = chapter

    with col2:
        st.selectbox(
            "AI Mode:",
            ["Style Match", "Expand", "Summarize", "Critique", "Off"]
        )

    # Writing area
    text_input = st.text_area(
        "Start writing...",
        height=400,
        placeholder="Begin drafting your thesis here. Your writing will be analyzed against your DNA profile for style consistency.",
        label_visibility="collapsed",
        key="draft_text"
    )
    st.session_state.drafting_text = text_input

    # Action buttons row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.button("🔍 Check Style", use_container_width=True)

    with col2:
        st.button("✨ AI Assist", use_container_width=True)

    with col3:
        st.button("💾 Save Draft", use_container_width=True)

    with col4:
        st.button("📤 Export", use_container_width=True)

    # Action buttons row 2 - Thematic Squeeze
    st.markdown("---")
    st.markdown("#### 📊 Thematic Squeeze")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("📥 Inject Data from Sheets", use_container_width=True, type="primary"):
            with st.spinner("Fetching data and generating synthesis..."):
                result = inject_sheets_data()

                if result.get("error"):
                    st.error(result["error"])
                else:
                    st.session_state.sheets_synthesis = result

    with col2:
        if "sheets_synthesis" in st.session_state and st.session_state.sheets_synthesis.get("success"):
            st.success("Synthesis generated in your Authorial DNA voice!")

    # Display synthesis result
    if "sheets_synthesis" in st.session_state and st.session_state.sheets_synthesis.get("success"):
        result = st.session_state.sheets_synthesis

        with st.expander("📋 Source Data Row", expanded=False):
            st.json(result["data_row"])

        st.markdown("#### Generated Synthesis (300 words, DNA-matched)")
        st.markdown(f'<div class="glass-card">{result["synthesis"]}</div>', unsafe_allow_html=True)

        if st.button("📋 Copy to Draft", use_container_width=True):
            st.session_state.drafting_text = result["synthesis"]
            st.rerun()

    # Red Thread continuity check
    st.markdown("---")
    st.markdown("#### 🔴 Continuity Check")

    if text_input and len(text_input) > 100:
        if st.button("Check for Contradictions", use_container_width=True):
            with st.spinner("Analyzing against your thesis corpus..."):
                engine = st.session_state.red_thread_engine
                results = engine.check_continuity(text_input)

                for r in results:
                    if r.get("type") == "none":
                        st.success("✓ No contradictions detected")
                    elif r.get("type") in ["contradiction", "inconsistency", "tension"]:
                        severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                        icon = severity_color.get(r.get("severity", "low"), "⚪")
                        st.warning(f"{icon} **{r.get('type', 'Issue').title()}**: {r.get('explanation', '')}")
                        if r.get("suggestion"):
                            st.info(f"💡 Suggestion: {r['suggestion']}")
                    elif r.get("status") == "no_context":
                        st.info(r.get("message", "Index your drafts first"))
    else:
        st.info("Write at least 100 characters to check for contradictions")


def render_dna_tab(dna_profile: dict | None):
    """Render the DNA profile analysis view."""
    st.markdown("### Your Writing DNA")

    if not dna_profile:
        st.warning("No DNA profile found. Add .docx files to the `/drafts` folder and run the DNA engine.")
        st.code("python core/dna_engine.py", language="bash")
        return

    # Metrics overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Sentence Complexity")
        st.metric(
            "Average Length",
            f"{dna_profile['sentence_complexity']['average_length']} words"
        )

        dist = dna_profile['sentence_complexity']['length_distribution']
        if dist:
            st.bar_chart(dist)

    with col2:
        st.markdown("#### Hedging Usage")
        st.metric(
            "Density",
            f"{dna_profile['hedging_analysis']['hedging_density_per_1000_words']}/1000 words"
        )

        top_hedges = dict(list(dna_profile['hedging_analysis']['phrases_found'].items())[:5])
        if top_hedges:
            st.markdown("**Top phrases:**")
            for phrase, count in top_hedges.items():
                st.markdown(f"- *{phrase}*: {count}")

    with col3:
        st.markdown("#### Transitions")
        st.metric(
            "Density",
            f"{dna_profile['transition_vocabulary']['transition_density_per_1000_words']}/1000 words"
        )

        prefs = dna_profile['transition_vocabulary']['preferred_categories']
        if prefs:
            st.markdown("**Preferred types:**")
            for cat in prefs:
                st.markdown(f"- {cat.replace('_', ' ').title()}")

    # Claude analysis
    st.markdown("---")
    st.markdown("#### Deep Analysis")

    claude_analysis = dna_profile.get('claude_deep_analysis', {})
    if "error" in claude_analysis:
        st.warning(f"Claude analysis unavailable: {claude_analysis['error']}")
    elif "raw_analysis" in claude_analysis:
        st.markdown(claude_analysis['raw_analysis'])
    else:
        st.json(claude_analysis)


def render_chapters_tab():
    """Render the chapters overview."""
    st.markdown("### Thesis Chapters")

    chapters = [
        {"name": "Introduction", "status": "In Progress", "words": 0, "target": 8000},
        {"name": "Literature Review", "status": "Not Started", "words": 0, "target": 20000},
        {"name": "Methodology", "status": "Not Started", "words": 0, "target": 15000},
        {"name": "Results", "status": "Not Started", "words": 0, "target": 15000},
        {"name": "Discussion", "status": "Not Started", "words": 0, "target": 15000},
        {"name": "Conclusion", "status": "Not Started", "words": 0, "target": 7000},
    ]

    for i, chapter in enumerate(chapters, 1):
        with st.expander(f"Chapter {i}: {chapter['name']} ({chapter['status']})"):
            progress = chapter['words'] / chapter['target'] if chapter['target'] > 0 else 0
            st.progress(progress)
            st.markdown(f"**Words:** {chapter['words']:,} / {chapter['target']:,}")

            col1, col2 = st.columns(2)
            with col1:
                st.button(f"📝 Edit", key=f"edit_{i}", use_container_width=True)
            with col2:
                st.button(f"📊 Analyze", key=f"analyze_{i}", use_container_width=True)


def render_progress_tab():
    """Render progress tracking."""
    st.markdown("### Thesis Progress")

    # Overall progress
    total_words = 0
    target_words = 80000
    progress = total_words / target_words

    st.markdown(f"**Overall: {total_words:,} / {target_words:,} words ({progress*100:.1f}%)**")
    st.progress(progress)

    # Milestones
    st.markdown("---")
    st.markdown("#### Milestones")

    milestones = [
        {"name": "Literature Review Complete", "done": False},
        {"name": "Methodology Approved", "done": False},
        {"name": "Data Collection Complete", "done": False},
        {"name": "First Draft Complete", "done": False},
        {"name": "Supervisor Review", "done": False},
        {"name": "Final Submission", "done": False},
    ]

    for milestone in milestones:
        icon = "✅" if milestone['done'] else "⬜"
        st.markdown(f"{icon} {milestone['name']}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
def main():
    """Main application entry point."""
    render_sidebar()
    render_drafting_pane()


if __name__ == "__main__":
    main()
