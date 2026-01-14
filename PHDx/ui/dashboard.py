"""
PHDx Dashboard - PhD Thesis Command Center

Streamlit-based interface for managing thesis drafts and AI-assisted writing.
"""

import json
from pathlib import Path

import streamlit as st

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

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .status-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #666;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E3A5F;
    }
</style>
""", unsafe_allow_html=True)


def load_author_dna() -> dict | None:
    """Load the author DNA profile if it exists."""
    if DNA_PATH.exists():
        with open(DNA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def render_sidebar():
    """Render the sidebar with data source controls."""
    with st.sidebar:
        st.markdown("## 📁 Data Sources")
        st.markdown("---")

        # Local Files Section
        st.markdown("### Local Files")

        # Drafts folder status
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

        # Google Drive Section
        st.markdown("### Google Drive")
        st.markdown("*Coming in Phase 2*")

        gdrive_connected = False  # Placeholder
        status_icon = "✅" if gdrive_connected else "❌"
        st.markdown(f"**Status:** {status_icon} {'Connected' if gdrive_connected else 'Not connected'}")

        if st.button("🔗 Connect Google Drive", use_container_width=True, disabled=True):
            pass

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
        st.selectbox(
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
            ]
        )

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
        label_visibility="collapsed"
    )

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.button("🔍 Check Style", use_container_width=True)

    with col2:
        st.button("✨ AI Assist", use_container_width=True)

    with col3:
        st.button("💾 Save Draft", use_container_width=True)

    with col4:
        st.button("📤 Export", use_container_width=True)


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


def main():
    """Main application entry point."""
    render_sidebar()
    render_drafting_pane()


if __name__ == "__main__":
    main()
