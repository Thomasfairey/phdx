"""
PHDx Auditor Tab - Oxford Brookes thesis evaluation.

Features:
- Evaluation against Oxford Brookes marking criteria
- Originality, criticality, and rigour assessment
- Detailed feedback and recommendations
- Exportable audit reports
"""

import streamlit as st


def render_auditor_tab():
    """Render the Auditor tab interface."""

    from core.auditor import BrookesAuditor, get_marking_criteria

    # Initialize auditor
    auditor = BrookesAuditor()

    # Session state
    if "audit_report" not in st.session_state:
        st.session_state["audit_report"] = None
    if "audit_text" not in st.session_state:
        st.session_state["audit_text"] = ""

    st.markdown(
        "<h2 style='font-family:Inter;font-weight:400;color:#9ca3af;'>"
        "🔬 Brookes Auditor</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Evaluate your draft against Oxford Brookes PhD marking criteria")

    # Show criteria info
    with st.expander("📋 Oxford Brookes Marking Criteria", expanded=False):
        criteria = get_marking_criteria()
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("**Originality (35%)**")
            st.markdown("_Original contribution to knowledge_")
            for ind in criteria["criteria"]["originality"]["indicators"][:3]:
                st.markdown(f"• {ind}")

        with col_b:
            st.markdown("**Critical Analysis (35%)**")
            st.markdown("_Rigorous argumentation_")
            for ind in criteria["criteria"]["criticality"]["indicators"][:3]:
                st.markdown(f"• {ind}")

        with col_c:
            st.markdown("**Methodological Rigour (30%)**")
            st.markdown("_Appropriate research design_")
            for ind in criteria["criteria"]["rigour"]["indicators"][:3]:
                st.markdown(f"• {ind}")

    st.markdown("---")

    # Input section
    st.markdown("#### Draft to Audit")

    # Source selection
    source_opt = st.radio(
        "Draft source",
        ["Paste text", "Use generated draft", "Load from document"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if source_opt == "Paste text":
        audit_text = st.text_area(
            "Draft text",
            height=250,
            placeholder="Paste your thesis draft here (minimum 100 characters)...",
            label_visibility="collapsed",
            value=st.session_state.get("audit_text", ""),
        )
        st.session_state["audit_text"] = audit_text
    elif source_opt == "Use generated draft":
        if st.session_state.get("writing_draft"):
            audit_text = st.session_state["writing_draft"]
            st.text_area(
                "Preview",
                value=audit_text[:2000] + ("..." if len(audit_text) > 2000 else ""),
                height=150,
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            audit_text = ""
            st.info(
                "No generated draft available. Generate one in the Writing Desk tab first."
            )
    else:  # Load from document
        if st.session_state.get("loaded_doc_text"):
            audit_text = st.session_state["loaded_doc_text"]
            st.text_area(
                "Preview",
                value=audit_text[:2000] + ("..." if len(audit_text) > 2000 else ""),
                height=150,
                disabled=True,
                label_visibility="collapsed",
            )
        else:
            audit_text = ""
            st.info(
                "No document loaded. Connect to Google Drive and load a document first."
            )

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
            "Other",
        ],
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
                st.session_state["audit_report"] = report

    # Display results
    if st.session_state.get("audit_report"):
        report = st.session_state["audit_report"]

        if report.get("error"):
            st.error(f"Audit error: {report['error']}")
        elif report.get("status") == "success":
            st.markdown("---")
            st.markdown("#### Audit Results")

            # Overall grade display
            grade = report["overall_grade"]
            level_colors = {
                "excellent": "#00c853",
                "good": "#0071ce",
                "satisfactory": "#ffc107",
                "needs_improvement": "#ff9800",
                "unsatisfactory": "#f44336",
            }
            grade_color = level_colors.get(grade.get("level", ""), "#e0e0e0")

            st.markdown(
                f"<div class='glass-panel' style='text-align:center;'>"
                f"<h1 style='color:{grade_color};font-size:48px;margin:0;'>{grade.get('score', 0)}/100</h1>"
                f"<p style='font-size:20px;color:#9ca3af;'>{grade.get('level', 'Unknown').replace('_', ' ').title()}</p>"
                f"<p>{grade.get('descriptor', '')}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # Criteria breakdown
            st.markdown("#### Criteria Breakdown")
            scores = report.get("criteria_scores", {})

            col1, col2, col3 = st.columns(3)
            with col1:
                orig = scores.get("originality", {})
                st.metric(
                    "Originality (35%)",
                    f"{orig.get('score', 0)}/100",
                    orig.get("level", "").replace("_", " ").title(),
                )
                st.caption(orig.get("feedback", ""))

            with col2:
                crit = scores.get("criticality", {})
                st.metric(
                    "Critical Analysis (35%)",
                    f"{crit.get('score', 0)}/100",
                    crit.get("level", "").replace("_", " ").title(),
                )
                st.caption(crit.get("feedback", ""))

            with col3:
                rig = scores.get("rigour", {})
                st.metric(
                    "Methodological Rigour (30%)",
                    f"{rig.get('score', 0)}/100",
                    rig.get("level", "").replace("_", " ").title(),
                )
                st.caption(rig.get("feedback", ""))

            # Strengths and improvements
            col_s, col_i = st.columns(2)
            with col_s:
                st.markdown("#### Strengths")
                for s in report.get("strengths", []):
                    st.markdown(f"✅ {s}")

            with col_i:
                st.markdown("#### Areas for Improvement")
                for a in report.get("areas_for_improvement", []):
                    st.markdown(f"⚠️ {a}")

            # Recommendations
            st.markdown("#### Recommendations")
            for i, rec in enumerate(report.get("specific_recommendations", []), 1):
                st.markdown(f"**{i}.** {rec}")

            # Examiner summary
            with st.expander("📜 Full Examiner Summary", expanded=False):
                st.markdown(report.get("examiner_summary", "No summary available."))

            # Export options
            st.markdown("---")
            formatted_report = auditor.format_audit_for_display(report)
            st.download_button(
                "📥 Download Audit Report (Markdown)",
                formatted_report,
                file_name=f"phdx_audit_{report.get('audit_id', 'report')}.md",
                mime="text/markdown",
            )

            # Clear button
            if st.button("🗑️ Clear Results"):
                st.session_state["audit_report"] = None
                st.rerun()
