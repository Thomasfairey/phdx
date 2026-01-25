"""
PHDx Orbit - Focus Layout Dashboard
"""

import sys
from pathlib import Path
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main entry point for PHDx dashboard."""
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
        from core.auditor import BrookesAuditor, get_marking_criteria

        # Initialize auditor
        auditor = BrookesAuditor()

        # Session state for auditor
        if 'audit_report' not in st.session_state:
            st.session_state['audit_report'] = None
        if 'audit_text' not in st.session_state:
            st.session_state['audit_text'] = ""

        # Show criteria info
        with st.expander("📋 Oxford Brookes Marking Criteria", expanded=False):
            criteria = get_marking_criteria()
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.markdown("**Originality (35%)**")
                st.markdown("_Original contribution to knowledge_")
                for ind in criteria['criteria']['originality']['indicators'][:3]:
                    st.markdown(f"• {ind}")

            with col_b:
                st.markdown("**Critical Analysis (35%)**")
                st.markdown("_Rigorous argumentation_")
                for ind in criteria['criteria']['criticality']['indicators'][:3]:
                    st.markdown(f"• {ind}")

            with col_c:
                st.markdown("**Methodological Rigour (30%)**")
                st.markdown("_Appropriate research design_")
                for ind in criteria['criteria']['rigour']['indicators'][:3]:
                    st.markdown(f"• {ind}")

        st.markdown("---")

        # Input section
        st.markdown("<h3 style='font-family:Inter;font-weight:400;color:#9ca3af;'>📝 Draft to Audit</h3>", unsafe_allow_html=True)

        # Source selection
        source_opt = st.radio(
            "Draft source",
            ["Paste text", "Use generated draft", "Load from document"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if source_opt == "Paste text":
            audit_text = st.text_area(
                "Draft text",
                height=250,
                placeholder="Paste your thesis draft here (minimum 100 characters)...",
                label_visibility="collapsed",
                value=st.session_state.get('audit_text', '')
            )
            st.session_state['audit_text'] = audit_text
        elif source_opt == "Use generated draft":
            if st.session_state.get('generated_draft'):
                audit_text = st.session_state['generated_draft']
                st.text_area("Preview", value=audit_text[:2000] + ("..." if len(audit_text) > 2000 else ""), height=150, disabled=True, label_visibility="collapsed")
            else:
                audit_text = ""
                st.info("No generated draft available. Generate one in the Studio tab first.")
        else:  # Load from document
            if st.session_state.get('loaded_doc_text'):
                audit_text = st.session_state['loaded_doc_text']
                st.text_area("Preview", value=audit_text[:2000] + ("..." if len(audit_text) > 2000 else ""), height=150, disabled=True, label_visibility="collapsed")
            else:
                audit_text = ""
                st.info("No document loaded. Load one in the Studio tab first.")

        # Chapter context
        chapter_context = st.selectbox(
            "Chapter Context",
            [
                "General Draft",
                "Chapter 1: Introduction",
                "Chapter 2: Literature Review",
                "Chapter 3: Methodology",
                "Chapter 4: Findings/Results",
                "Chapter 5: Discussion",
                "Chapter 6: Conclusion",
                "Abstract",
                "Other"
            ]
        )

        # Audit button
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            run_audit = st.button("🔬 Run Audit", type="primary", use_container_width=True)

        if run_audit:
            if not audit_text or len(audit_text.strip()) < 100:
                st.error("Please provide at least 100 characters of text to audit.")
            else:
                with st.spinner("Evaluating against Oxford Brookes criteria..."):
                    report = auditor.audit_draft(audit_text, chapter_context)
                    st.session_state['audit_report'] = report

        # Display results
        if st.session_state.get('audit_report'):
            report = st.session_state['audit_report']

            if report.get('error'):
                st.error(f"Audit error: {report['error']}")
            elif report.get('status') == 'success':
                st.markdown("---")
                st.markdown("<h3 style='font-family:Inter;font-weight:400;color:#9ca3af;'>📊 Audit Results</h3>", unsafe_allow_html=True)

                # Overall grade display
                grade = report['overall_grade']
                level_colors = {
                    "excellent": "#00c853",
                    "good": "#0071ce",
                    "satisfactory": "#ffc107",
                    "needs_improvement": "#ff9800",
                    "unsatisfactory": "#f44336"
                }
                grade_color = level_colors.get(grade.get('level', ''), '#e0e0e0')

                st.markdown(
                    f"<div class='glass-panel' style='text-align:center;'>"
                    f"<h1 style='color:{grade_color};font-size:48px;margin:0;'>{grade.get('score', 0)}/100</h1>"
                    f"<p style='font-size:20px;color:#9ca3af;'>{grade.get('level', 'Unknown').replace('_', ' ').title()}</p>"
                    f"<p>{grade.get('descriptor', '')}</p>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # Criteria breakdown
                st.markdown("#### Criteria Breakdown")
                scores = report.get('criteria_scores', {})

                col1, col2, col3 = st.columns(3)
                with col1:
                    orig = scores.get('originality', {})
                    st.metric("Originality (35%)", f"{orig.get('score', 0)}/100", orig.get('level', '').replace('_', ' ').title())
                    st.caption(orig.get('feedback', ''))

                with col2:
                    crit = scores.get('criticality', {})
                    st.metric("Critical Analysis (35%)", f"{crit.get('score', 0)}/100", crit.get('level', '').replace('_', ' ').title())
                    st.caption(crit.get('feedback', ''))

                with col3:
                    rig = scores.get('rigour', {})
                    st.metric("Methodological Rigour (30%)", f"{rig.get('score', 0)}/100", rig.get('level', '').replace('_', ' ').title())
                    st.caption(rig.get('feedback', ''))

                # Strengths and improvements
                col_s, col_i = st.columns(2)
                with col_s:
                    st.markdown("#### Strengths")
                    for s in report.get('strengths', []):
                        st.markdown(f"✅ {s}")

                with col_i:
                    st.markdown("#### Areas for Improvement")
                    for a in report.get('areas_for_improvement', []):
                        st.markdown(f"⚠️ {a}")

                # Recommendations
                st.markdown("#### Recommendations")
                for i, rec in enumerate(report.get('specific_recommendations', []), 1):
                    st.markdown(f"**{i}.** {rec}")

                # Examiner summary
                with st.expander("📜 Full Examiner Summary", expanded=False):
                    st.markdown(report.get('examiner_summary', 'No summary available.'))

                # Export options
                st.markdown("---")
                formatted_report = auditor.format_audit_for_display(report)
                st.download_button(
                    "📥 Download Audit Report (Markdown)",
                    formatted_report,
                    file_name=f"phdx_audit_{report.get('audit_id', 'report')}.md",
                    mime="text/markdown"
                )

                # Clear button
                if st.button("🗑️ Clear Results"):
                    st.session_state['audit_report'] = None
                    st.rerun()


if __name__ == "__main__":
    main()
