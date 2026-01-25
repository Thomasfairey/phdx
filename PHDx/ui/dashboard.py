"""
PHDx Orbit - PhD Thesis Command Center

5-Tab dashboard providing comprehensive thesis management:
- Data Lab: Data science and analysis
- Writing Desk: AI-assisted drafting
- Narrative: Structure and argument intelligence
- Auditor: Oxford Brookes evaluation
- Library: Zotero citation management
"""

import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main entry point for PHDx dashboard."""
    st.set_page_config(
        layout="wide",
        page_title="PHDx Orbit",
        page_icon="🧬",
        initial_sidebar_state="collapsed"
    )

    from ui.styles import load_css
    from core import airlock

    load_css()

    # Initialize core session state
    _init_session_state()

    # Render header
    _render_header()

    # Render main tabs
    _render_tabs()


def _init_session_state():
    """Initialize all session state variables."""
    defaults = {
        # Core state
        'active_doc_id': None,
        'loaded_doc_text': "",
        'last_model_used': "",

        # Writing state
        'generated_draft': "",
        'writing_outline': None,
        'writing_draft': "",

        # Data Lab state
        'data_lab_df': None,
        'data_lab_eda': None,
        'data_lab_sentiment': None,

        # Narrative state
        'narrative_structure': None,
        'narrative_arguments': None,

        # Auditor state
        'audit_report': None,
        'audit_text': "",

        # Library state
        'library_items': None,
        'library_selected_items': [],
    }

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_header():
    """Render the dashboard header."""
    from core import airlock

    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        st.markdown(
            "<h1 style='font-family:Inter;font-weight:300;font-size:28px;'>"
            "🧬 <b>PHDx</b> <span style='color:#6b7280'>Orbit</span></h1>",
            unsafe_allow_html=True
        )

    with col2:
        creds = airlock.get_credentials()
        if creds:
            st.markdown(
                "<span style='color:#10b981;font-weight:600;'>● Connected</span>",
                unsafe_allow_html=True
            )
        else:
            if st.button("🔗 Connect Drive"):
                try:
                    airlock.authenticate_user()
                    st.rerun()
                except Exception as e:
                    st.error(str(e))

    with col3:
        # Model info
        try:
            from core.llm_gateway import get_opus_model
            model_name = get_opus_model()
            st.caption(f"Primary model: {model_name}")
        except ImportError:
            pass


def _render_tabs():
    """Render the 5 main tabs."""

    # Tab configuration
    tab_icons = ["📊", "✍️", "🧭", "🔬", "📚"]
    tab_names = ["Data Lab", "Writing Desk", "Narrative", "Auditor", "Library"]

    tabs = st.tabs([f"{icon} {name}" for icon, name in zip(tab_icons, tab_names)])

    # Data Lab Tab
    with tabs[0]:
        try:
            from ui.tabs.data_lab_tab import render_data_lab_tab
            render_data_lab_tab()
        except ImportError as e:
            st.error(f"Data Lab module not available: {e}")
            _render_fallback_data_lab()

    # Writing Desk Tab
    with tabs[1]:
        try:
            from ui.tabs.writing_desk_tab import render_writing_desk_tab
            render_writing_desk_tab()
        except ImportError as e:
            st.error(f"Writing Desk module not available: {e}")
            _render_fallback_writing_desk()

    # Narrative Tab
    with tabs[2]:
        try:
            from ui.tabs.narrative_tab import render_narrative_tab
            render_narrative_tab()
        except ImportError as e:
            st.error(f"Narrative module not available: {e}")
            _render_fallback_narrative()

    # Auditor Tab
    with tabs[3]:
        try:
            from ui.tabs.auditor_tab import render_auditor_tab
            render_auditor_tab()
        except ImportError as e:
            st.error(f"Auditor module not available: {e}")
            _render_fallback_auditor()

    # Library Tab
    with tabs[4]:
        try:
            from ui.tabs.library_tab import render_library_tab
            render_library_tab()
        except ImportError as e:
            st.error(f"Library module not available: {e}")
            _render_fallback_library()


# =============================================================================
# FALLBACK RENDERERS (when modules unavailable)
# =============================================================================

def _render_fallback_data_lab():
    """Fallback Data Lab when module unavailable."""
    st.markdown("### 📊 Data Lab")
    st.info("Data Lab requires additional dependencies. Install with:")
    st.code("pip install pandas scipy plotly transformers", language="bash")


def _render_fallback_writing_desk():
    """Fallback Writing Desk - basic drafting."""
    from core import llm_gateway

    st.markdown("### ✍️ Writing Desk")

    # Reference source
    with st.expander("📚 Reference Source / Context", expanded=False):
        from core import airlock
        creds = airlock.get_credentials()
        if creds:
            docs = airlock.list_recent_docs(limit=10)
            if docs:
                opts = {"-- Select --": None} | {d['name']: d['id'] for d in docs}
                sel = st.selectbox("Doc", list(opts.keys()), label_visibility="collapsed")
                if sel != "-- Select --" and opts[sel] != st.session_state['active_doc_id']:
                    st.session_state['active_doc_id'] = opts[sel]
                    st.session_state['loaded_doc_text'] = airlock.load_google_doc(opts[sel])
        if st.session_state['loaded_doc_text']:
            st.markdown(
                f"<div class='scroll-container'>{st.session_state['loaded_doc_text'][:5000]}</div>",
                unsafe_allow_html=True
            )

    # Drafting
    prompt = st.text_area(
        "Prompt",
        height=200,
        placeholder="Enter your drafting prompt...",
        label_visibility="collapsed"
    )

    if st.button("🚀 Generate", type="primary"):
        if prompt:
            with st.spinner("Generating..."):
                result = llm_gateway.generate_content(
                    prompt,
                    "drafting",
                    st.session_state.get('loaded_doc_text', '')
                )
                st.session_state['generated_draft'] = result['content']
                st.session_state['last_model_used'] = result['model_used']

    if st.session_state['generated_draft']:
        st.markdown(
            f"<span class='model-badge'>{st.session_state['last_model_used']}</span>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='glass-panel'>{st.session_state['generated_draft']}</div>",
            unsafe_allow_html=True
        )
        st.download_button("📥 Download", st.session_state['generated_draft'], "draft.md")


def _render_fallback_narrative():
    """Fallback Narrative tab."""
    st.markdown("### 🧭 Narrative Intelligence")
    st.info("Narrative Engine requires the full PHDx installation.")


def _render_fallback_auditor():
    """Fallback Auditor - uses core auditor directly."""
    try:
        from core.auditor import BrookesAuditor, get_marking_criteria
        auditor = BrookesAuditor()

        st.markdown("### 🔬 Brookes Auditor")

        audit_text = st.text_area(
            "Draft to audit",
            height=200,
            placeholder="Paste your thesis draft here..."
        )

        chapter = st.selectbox(
            "Chapter",
            ["General", "Introduction", "Literature Review", "Methodology",
             "Findings", "Discussion", "Conclusion"]
        )

        if st.button("🔬 Run Audit", type="primary"):
            if audit_text and len(audit_text) > 100:
                with st.spinner("Auditing..."):
                    report = auditor.audit_draft(audit_text, chapter)
                    if report.get('status') == 'success':
                        grade = report['overall_grade']
                        st.metric("Score", f"{grade.get('score', 0)}/100")
                        st.markdown(report.get('examiner_summary', ''))
            else:
                st.warning("Please provide at least 100 characters")

    except ImportError:
        st.error("Auditor module not available")


def _render_fallback_library():
    """Fallback Library tab."""
    st.markdown("### 📚 Library")
    st.info("Connect Zotero by adding credentials to your .env file:")
    st.code("ZOTERO_USER_ID=your_id\nZOTERO_API_KEY=your_key", language="bash")


if __name__ == "__main__":
    main()
