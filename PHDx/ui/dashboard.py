"""
PHDx Orbit - PhD Thesis Command Center
Data Connector + Intelligence Layer Dashboard

Features:
- Obsidian Theme with Glassmorphism
- Google Drive Integration via Airlock
- Multi-model LLM routing via Gateway
- Studio (Drafting) and Auditor tabs
"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import airlock
from core import llm_gateway


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    layout="wide",
    page_title="PHDx Orbit",
    page_icon="🧬"
)


# =============================================================================
# OBSIDIAN THEME STYLING
# =============================================================================
def inject_obsidian_theme():
    """Inject the Obsidian theme with glassmorphism effects."""
    st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* Obsidian Background */
        .stApp {
            background-color: #0E1117;
        }

        /* Glassmorphism Card */
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: rgba(14, 17, 23, 0.95);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Text colors */
        .stApp, .stApp p, .stApp span, .stApp label {
            color: #E0E0E0;
        }

        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            padding: 4px;
        }

        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border-radius: 8px;
            color: #A0A0A0;
            padding: 10px 20px;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(102, 126, 234, 0.2);
            color: #667eea;
        }

        /* Text area styling */
        .stTextArea textarea {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #E0E0E0;
        }

        /* Select box styling */
        .stSelectbox > div > div {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }

        /* Scrollable container */
        .scroll-container {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
            height: 600px;
            overflow-y: auto;
            font-family: 'Georgia', serif;
            line-height: 1.8;
        }

        /* Model indicator badge */
        .model-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
            margin-bottom: 10px;
        }

        .model-badge.claude {
            background: rgba(102, 126, 234, 0.2);
            color: #667eea;
            border: 1px solid rgba(102, 126, 234, 0.3);
        }

        .model-badge.gpt {
            background: rgba(16, 163, 127, 0.2);
            color: #10a37f;
            border: 1px solid rgba(16, 163, 127, 0.3);
        }

        .model-badge.gemini {
            background: rgba(234, 179, 8, 0.2);
            color: #eab308;
            border: 1px solid rgba(234, 179, 8, 0.3);
        }

        /* Radio button horizontal layout */
        .stRadio > div {
            flex-direction: row;
            gap: 20px;
        }

        /* Connection status indicators */
        .status-connected {
            color: #10B981;
        }

        .status-disconnected {
            color: #EF4444;
        }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
def init_session_state():
    """Initialize session state variables."""
    if 'active_doc_id' not in st.session_state:
        st.session_state['active_doc_id'] = None

    if 'active_doc_name' not in st.session_state:
        st.session_state['active_doc_name'] = None

    if 'loaded_doc_text' not in st.session_state:
        st.session_state['loaded_doc_text'] = ""

    if 'generated_draft' not in st.session_state:
        st.session_state['generated_draft'] = ""

    if 'last_model_used' not in st.session_state:
        st.session_state['last_model_used'] = ""

    if 'drive_connected' not in st.session_state:
        st.session_state['drive_connected'] = False


# =============================================================================
# SIDEBAR - THE CONNECTION RAIL
# =============================================================================
def render_sidebar():
    """Render the sidebar with data connections."""
    with st.sidebar:
        st.markdown("## 📡 Data Link")
        st.markdown("---")

        # Google Drive Connection
        creds = airlock.get_credentials()

        if creds is None:
            st.markdown("**Google Drive**: <span class='status-disconnected'>Disconnected</span>",
                       unsafe_allow_html=True)

            if st.button("🔗 Connect Google Drive", use_container_width=True):
                try:
                    airlock.authenticate_user()
                    st.session_state['drive_connected'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Connection failed: {e}")
        else:
            st.markdown("**Google Drive**: <span class='status-connected'>Connected</span>",
                       unsafe_allow_html=True)
            st.session_state['drive_connected'] = True

            # List recent documents
            st.markdown("---")
            st.markdown("### 📂 Active Chapter")

            try:
                docs = airlock.list_recent_docs(limit=15)

                if docs:
                    # Create options for selectbox
                    doc_options = {f"{d['name']} ({d['type']})": d['id'] for d in docs}
                    doc_names = ["-- Select a document --"] + list(doc_options.keys())

                    # Get current selection index
                    current_idx = 0
                    if st.session_state['active_doc_name'] in doc_names:
                        current_idx = doc_names.index(st.session_state['active_doc_name'])

                    selected = st.selectbox(
                        "Choose file:",
                        doc_names,
                        index=current_idx,
                        label_visibility="collapsed"
                    )

                    if selected != "-- Select a document --":
                        doc_id = doc_options[selected]
                        if doc_id != st.session_state['active_doc_id']:
                            st.session_state['active_doc_id'] = doc_id
                            st.session_state['active_doc_name'] = selected
                            st.session_state['loaded_doc_text'] = ""  # Reset loaded text
                            st.rerun()
                else:
                    st.info("No Google Docs or Sheets found.")

            except Exception as e:
                st.error(f"Error loading docs: {e}")

            # Disconnect option
            st.markdown("---")
            if st.button("🔌 Disconnect", use_container_width=True):
                airlock.clear_credentials()
                st.session_state['drive_connected'] = False
                st.session_state['active_doc_id'] = None
                st.session_state['active_doc_name'] = None
                st.session_state['loaded_doc_text'] = ""
                st.rerun()

        # LLM Status
        st.markdown("---")
        st.markdown("### 🧠 Intelligence Layer")
        try:
            available = llm_gateway.get_available_models()
            for model in available:
                model_names = {'writer': 'Claude', 'auditor': 'GPT', 'context': 'Gemini'}
                st.markdown(f"✓ {model_names.get(model, model)}")
        except Exception as e:
            st.warning(f"LLM not configured: {e}")


# =============================================================================
# TAB 1: THE STUDIO
# =============================================================================
def render_studio_tab():
    """Render the Studio tab for drafting."""
    col_data, col_draft = st.columns([1, 2])

    # LEFT COLUMN - Source Data
    with col_data:
        st.markdown("### 📄 Source Document")

        if st.session_state['active_doc_id']:
            # Load document if not already loaded
            if not st.session_state['loaded_doc_text']:
                with st.spinner("Loading document..."):
                    try:
                        text = airlock.load_google_doc(st.session_state['active_doc_id'])
                        st.session_state['loaded_doc_text'] = text
                    except Exception as e:
                        st.error(f"Error loading document: {e}")
                        st.session_state['loaded_doc_text'] = ""

            # Display document in scrollable container
            if st.session_state['loaded_doc_text']:
                doc_text = st.session_state['loaded_doc_text']
                st.markdown(
                    f"<div class='scroll-container'>{doc_text[:10000]}{'...' if len(doc_text) > 10000 else ''}</div>",
                    unsafe_allow_html=True
                )
                st.caption(f"📊 {len(doc_text):,} characters | ~{len(doc_text)//4:,} tokens")
            else:
                st.info("No content loaded.")
        else:
            st.markdown(
                "<div class='glass-card'>Select a document from the sidebar to load content.</div>",
                unsafe_allow_html=True
            )

    # RIGHT COLUMN - Drafting
    with col_draft:
        st.markdown("### ✍️ Drafting Studio")

        # Prompt input
        prompt = st.text_area(
            "Drafting Prompt",
            placeholder="e.g., Synthesize the key themes from this chapter...",
            height=120,
            key="drafting_prompt"
        )

        # Model selection
        col_model, col_generate = st.columns([2, 1])

        with col_model:
            model_choice = st.radio(
                "Model Select",
                ["Claude 3.5 (Prose)", "GPT-5 (Logic)"],
                horizontal=True,
                key="model_select"
            )

        with col_generate:
            generate_clicked = st.button(
                "🚀 Generate Draft",
                use_container_width=True,
                type="primary"
            )

        # Generate action
        if generate_clicked:
            if not prompt.strip():
                st.warning("Please enter a drafting prompt.")
            else:
                # Determine task type based on model choice
                task_type = "drafting" if "Claude" in model_choice else "audit"
                context = st.session_state.get('loaded_doc_text', '')

                with st.spinner(f"Generating with {model_choice}..."):
                    try:
                        result = llm_gateway.generate_content(
                            prompt=prompt,
                            task_type=task_type,
                            context_text=context
                        )
                        st.session_state['generated_draft'] = result['content']
                        st.session_state['last_model_used'] = result['model_used']
                    except Exception as e:
                        st.error(f"Generation failed: {e}")

        # Display generated content
        st.markdown("---")
        st.markdown("### 📝 Generated Draft")

        if st.session_state['generated_draft']:
            # Model badge
            model_used = st.session_state['last_model_used']
            badge_class = "claude" if "Claude" in model_used else "gpt" if "GPT" in model_used else "gemini"
            st.markdown(
                f"<span class='model-badge {badge_class}'>{model_used}</span>",
                unsafe_allow_html=True
            )

            # Content display
            st.markdown(
                f"<div class='glass-card'>{st.session_state['generated_draft']}</div>",
                unsafe_allow_html=True
            )

            # Copy button
            st.download_button(
                "📋 Download Draft",
                st.session_state['generated_draft'],
                file_name="draft.md",
                mime="text/markdown"
            )
        else:
            st.markdown(
                "<div class='glass-card' style='color: #666;'>Generated content will appear here...</div>",
                unsafe_allow_html=True
            )


# =============================================================================
# TAB 2: THE AUDITOR
# =============================================================================
def render_auditor_tab():
    """Render the Auditor tab for quality checks."""
    st.markdown("### 🔍 Brookes Audit System")

    st.markdown("""
    <div class='glass-card'>
        <p>The Brookes Auditor performs comprehensive quality checks on your academic writing:</p>
        <ul>
            <li>Argument coherence analysis</li>
            <li>Citation consistency verification</li>
            <li>Methodological rigor assessment</li>
            <li>Red thread continuity check</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔬 Run Brookes Audit", use_container_width=True, type="primary"):
            st.info("Audit Module Pending...")
            st.toast("🔬 Audit system coming soon!", icon="🔍")

    with col2:
        if st.button("📊 View Audit History", use_container_width=True):
            st.info("No audit history available yet.")


# =============================================================================
# MAIN APPLICATION
# =============================================================================
def main():
    """Main application entry point."""
    # Initialize
    inject_obsidian_theme()
    init_session_state()

    # Render sidebar
    render_sidebar()

    # Main title
    st.markdown("# 🧬 PHDx Orbit")
    st.markdown("*Your PhD Command Center*")
    st.markdown("---")

    # Create tabs
    tab_studio, tab_auditor = st.tabs(["🎨 The Studio", "🔍 The Auditor"])

    with tab_studio:
        render_studio_tab()

    with tab_auditor:
        render_auditor_tab()


if __name__ == "__main__":
    main()
