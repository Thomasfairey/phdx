"""
PHDx Orbit - Focus Layout Dashboard
"""

import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(layout="wide", page_title="PHDx Orbit", page_icon="🧬")

from ui.styles import load_css
from core import airlock
from core import llm_gateway

load_css()

# Session state
for key, val in {'active_doc_id': None, 'loaded_doc_text': "", 'generated_draft': "", 'last_model_used': ""}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Top bar
col1, col2, col3 = st.columns([2, 2, 3])
with col1:
    st.markdown("<h1 style='font-family:Inter;font-weight:300;font-size:28px;'>🧬 <b>PHDx</b> <span style='color:#6b7280'>Orbit</span></h1>", unsafe_allow_html=True)
with col2:
    creds = airlock.get_credentials()
    if creds:
        st.markdown("<span style='color:#10b981;font-weight:600;'>● Connected</span>", unsafe_allow_html=True)
    else:
        if st.button("🔗 Connect Drive"):
            try:
                airlock.authenticate_user()
                st.rerun()
            except Exception as e:
                st.error(str(e))
with col3:
    model = st.radio("Model", ["Claude (Prose)", "GPT (Logic)"], horizontal=True, label_visibility="collapsed")

# Tabs
tab1, tab2 = st.tabs(["🎨 Studio", "🔍 Auditor"])

with tab1:
    with st.expander("📚 Reference Source / Context", expanded=False):
        if creds:
            docs = airlock.list_recent_docs(limit=10)
            if docs:
                opts = {"-- Select --": None} | {d['name']: d['id'] for d in docs}
                sel = st.selectbox("Doc", list(opts.keys()), label_visibility="collapsed")
                if sel != "-- Select --" and opts[sel] != st.session_state['active_doc_id']:
                    st.session_state['active_doc_id'] = opts[sel]
                    st.session_state['loaded_doc_text'] = airlock.load_google_doc(opts[sel])
        if st.session_state['loaded_doc_text']:
            st.markdown(f"<div class='scroll-container'>{st.session_state['loaded_doc_text'][:5000]}</div>", unsafe_allow_html=True)

    st.markdown("<h2 style='font-family:Inter;font-weight:400;color:#9ca3af;'>✍️ Drafting Studio</h2>", unsafe_allow_html=True)
    prompt = st.text_area("Prompt", height=280, placeholder="Enter your drafting prompt...", label_visibility="collapsed")
    
    if st.button("🚀 Generate", type="primary"):
        if prompt:
            task = "drafting" if "Claude" in model else "audit"
            with st.spinner("Generating..."):
                result = llm_gateway.generate_content(prompt, task, st.session_state.get('loaded_doc_text', ''))
                st.session_state['generated_draft'] = result['content']
                st.session_state['last_model_used'] = result['model_used']

    if st.session_state['generated_draft']:
        badge = "claude" if "Claude" in st.session_state['last_model_used'] else "gpt"
        st.markdown(f"<span class='model-badge {badge}'>{st.session_state['last_model_used']}</span>", unsafe_allow_html=True)
        st.markdown(f"<div class='glass-panel'>{st.session_state['generated_draft']}</div>", unsafe_allow_html=True)
        st.download_button("📥 Download", st.session_state['generated_draft'], "draft.md")

with tab2:
    st.markdown("<div class='glass-panel'><p>🔬 Brookes Audit System - Coming Soon</p></div>", unsafe_allow_html=True)
    if st.button("🔬 Run Audit", type="primary"):
        st.info("Audit module pending...")
