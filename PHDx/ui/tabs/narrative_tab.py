"""
PHDx Narrative Tab - Thesis structure and argument intelligence.

Features:
- Thesis structure analysis
- Argument mapping and visualization
- Gap analysis
- Thematic coherence checking
- Literature synthesis assistance
"""

import streamlit as st


def render_narrative_tab():
    """Render the Narrative Intelligence tab interface."""

    # Initialize session state
    _init_session_state()

    st.markdown(
        "<h2 style='font-family:Inter;font-weight:400;color:#9ca3af;'>"
        "🧭 Narrative Intelligence</h2>",
        unsafe_allow_html=True
    )
    st.caption("Analyze thesis structure, map arguments, and ensure coherence")

    # Sub-tabs
    structure_tab, args_tab, gaps_tab, themes_tab = st.tabs([
        "📐 Structure", "🗺️ Arguments", "🔍 Gaps", "🎨 Themes"
    ])

    with structure_tab:
        _render_structure_section()

    with args_tab:
        _render_arguments_section()

    with gaps_tab:
        _render_gaps_section()

    with themes_tab:
        _render_themes_section()


def _init_session_state():
    """Initialize Narrative tab session state."""
    defaults = {
        "narrative_structure": None,
        "narrative_arguments": None,
        "narrative_gaps": None,
        "narrative_themes": None,
        "narrative_thesis_text": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_structure_section():
    """Render thesis structure analysis."""

    st.markdown("#### Thesis Structure Analysis")

    # Structure type selection
    try:
        from core.narrative_engine import NarrativeEngine, THESIS_STRUCTURES
        engine = NarrativeEngine()
        structure_types = list(THESIS_STRUCTURES.keys())
    except ImportError:
        structure_types = ["empirical", "theoretical", "papers_based", "practice_based"]
        engine = None

    col1, col2 = st.columns(2)
    with col1:
        structure_type = st.selectbox(
            "Thesis type",
            structure_types,
            format_func=lambda x: x.replace("_", " ").title()
        )
    with col2:
        total_words = st.number_input(
            "Target word count",
            min_value=50000,
            max_value=120000,
            value=80000,
            step=5000
        )

    # Show structure template
    if st.button("📐 Show Structure Template"):
        try:
            if engine:
                from core.narrative_engine import THESIS_STRUCTURES
                template = THESIS_STRUCTURES.get(structure_type, {})
            else:
                template = _get_fallback_structure(structure_type)

            st.markdown("---")
            st.markdown(f"#### {structure_type.replace('_', ' ').title()} Thesis Structure")

            chapters = template.get("chapters", [])
            for i, chapter in enumerate(chapters, 1):
                pct = chapter.get("target_pct", 10)
                words = int(total_words * pct / 100)

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{i}. {chapter.get('name', 'Chapter')}**")
                with col2:
                    st.caption(f"{pct}%")
                with col3:
                    st.caption(f"~{words:,} words")

                if chapter.get("key_elements"):
                    elements = ", ".join(chapter["key_elements"][:3])
                    st.caption(f"Key elements: {elements}")

        except Exception as e:
            st.error(f"Error: {e}")

    # Analyze existing structure
    st.markdown("---")
    st.markdown("#### Analyze Your Thesis Structure")

    thesis_text = st.text_area(
        "Paste your thesis text or chapter summaries",
        height=200,
        placeholder="Paste your thesis text here for structure analysis...\n\nYou can paste:\n- Full thesis text\n- Chapter summaries\n- Table of contents with descriptions"
    )

    if st.button("🔬 Analyze Structure", type="primary"):
        if not thesis_text or len(thesis_text) < 500:
            st.warning("Please provide at least 500 characters for meaningful analysis")
            return

        with st.spinner("Analyzing thesis structure..."):
            try:
                if engine:
                    result = engine.analyze_structure(thesis_text, structure_type)
                    st.session_state["narrative_structure"] = result
                else:
                    st.error("Narrative Engine not available")
                    return
            except Exception as e:
                st.error(f"Error: {e}")

    # Display analysis
    if st.session_state.get("narrative_structure"):
        result = st.session_state["narrative_structure"]
        _display_structure_analysis(result)


def _render_arguments_section():
    """Render argument mapping section."""

    st.markdown("#### Argument Mapping")
    st.caption("Trace your arguments from claims through evidence to conclusions")

    thesis_text = st.text_area(
        "Text to analyze",
        height=200,
        placeholder="Paste thesis text to map its argumentative structure...",
        key="args_text"
    )

    if st.button("🗺️ Map Arguments", type="primary"):
        if not thesis_text or len(thesis_text) < 300:
            st.warning("Please provide at least 300 characters")
            return

        with st.spinner("Mapping arguments..."):
            try:
                from core.narrative_engine import NarrativeEngine
                engine = NarrativeEngine()
                result = engine.map_arguments(thesis_text)
                st.session_state["narrative_arguments"] = result
            except ImportError:
                st.error("Narrative Engine not available")
            except Exception as e:
                st.error(f"Error: {e}")

    # Display argument map
    if st.session_state.get("narrative_arguments"):
        args = st.session_state["narrative_arguments"]

        if args.get("error"):
            st.error(args["error"])
            return

        st.markdown("---")

        # Main thesis
        if args.get("main_thesis"):
            st.markdown("#### Main Thesis")
            st.info(args["main_thesis"])

        # Supporting arguments
        if args.get("supporting_arguments"):
            st.markdown("#### Supporting Arguments")
            for i, arg in enumerate(args["supporting_arguments"], 1):
                with st.expander(f"Argument {i}: {arg.get('claim', '')[:50]}..."):
                    st.markdown(f"**Claim:** {arg.get('claim', '')}")

                    if arg.get("evidence"):
                        st.markdown("**Evidence:**")
                        for ev in arg["evidence"]:
                            st.markdown(f"- {ev}")

                    if arg.get("warrant"):
                        st.markdown(f"**Warrant:** {arg['warrant']}")

                    strength = arg.get("strength", "medium")
                    color = {"strong": "green", "medium": "orange", "weak": "red"}.get(strength, "gray")
                    st.markdown(f"**Strength:** :{color}[{strength}]")

        # Conclusions
        if args.get("conclusions"):
            st.markdown("#### Conclusions")
            for conc in args["conclusions"]:
                st.markdown(f"- {conc}")

        # Logical flow
        if args.get("logical_flow"):
            st.markdown("#### Logical Flow Assessment")
            st.markdown(args["logical_flow"])


def _render_gaps_section():
    """Render gap analysis section."""

    st.markdown("#### Gap Analysis")
    st.caption("Identify missing evidence, weak links, and areas needing development")

    # Input options
    input_type = st.radio(
        "Analysis type",
        ["Single chapter", "Multiple chapters", "Full thesis overview"],
        horizontal=True
    )

    if input_type == "Single chapter":
        chapter_type = st.selectbox(
            "Chapter type",
            ["introduction", "literature_review", "methodology", "findings", "discussion", "conclusion"],
            format_func=lambda x: x.replace("_", " ").title()
        )
        text = st.text_area("Chapter text", height=200, placeholder="Paste chapter text...")

        if st.button("🔍 Analyze Gaps", type="primary"):
            if not text or len(text) < 300:
                st.warning("Please provide at least 300 characters")
                return

            with st.spinner("Analyzing gaps..."):
                try:
                    from core.narrative_engine import NarrativeEngine
                    engine = NarrativeEngine()
                    result = engine.identify_gaps(text, chapter_type)
                    st.session_state["narrative_gaps"] = result
                except ImportError:
                    st.error("Narrative Engine not available")
                except Exception as e:
                    st.error(f"Error: {e}")

    elif input_type == "Multiple chapters":
        st.markdown("Enter text for each chapter:")

        chapters = []
        for ch_type in ["Introduction", "Literature Review", "Methodology", "Findings", "Discussion", "Conclusion"]:
            with st.expander(f"{ch_type}"):
                ch_text = st.text_area(f"{ch_type} text", height=100, key=f"gap_{ch_type.lower()}")
                if ch_text:
                    chapters.append({"type": ch_type.lower().replace(" ", "_"), "text": ch_text})

        if st.button("🔍 Analyze All Chapters", type="primary"):
            if not chapters:
                st.warning("Please provide text for at least one chapter")
                return

            with st.spinner("Analyzing gaps across chapters..."):
                try:
                    from core.narrative_engine import NarrativeEngine
                    engine = NarrativeEngine()

                    all_gaps = []
                    for ch in chapters:
                        gaps = engine.identify_gaps(ch["text"], ch["type"])
                        gaps["chapter"] = ch["type"]
                        all_gaps.append(gaps)

                    st.session_state["narrative_gaps"] = {"chapters": all_gaps}
                except Exception as e:
                    st.error(f"Error: {e}")

    else:  # Full thesis overview
        text = st.text_area(
            "Thesis overview or abstract",
            height=200,
            placeholder="Paste thesis overview, abstract, or summary..."
        )

        if st.button("🔍 Analyze Gaps", type="primary"):
            if not text:
                st.warning("Please provide thesis overview")
                return

            with st.spinner("Analyzing..."):
                try:
                    from core.narrative_engine import NarrativeEngine
                    engine = NarrativeEngine()
                    result = engine.identify_gaps(text, "overview")
                    st.session_state["narrative_gaps"] = result
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display gaps
    if st.session_state.get("narrative_gaps"):
        gaps = st.session_state["narrative_gaps"]
        _display_gaps(gaps)


def _render_themes_section():
    """Render thematic coherence section."""

    st.markdown("#### Thematic Coherence")
    st.caption("Check consistency of themes across your thesis")

    st.markdown("Enter key sections from your thesis:")

    chapters = []
    for i, ch_name in enumerate(["Introduction", "Literature Review", "Discussion", "Conclusion"]):
        text = st.text_area(
            f"{ch_name} key themes/text",
            height=100,
            placeholder=f"Enter key themes or text from {ch_name}...",
            key=f"theme_{ch_name}"
        )
        if text:
            chapters.append({
                "name": ch_name,
                "text": text,
                "themes": []  # Will be extracted
            })

    if st.button("🎨 Check Thematic Coherence", type="primary"):
        if len(chapters) < 2:
            st.warning("Please provide text for at least 2 sections")
            return

        with st.spinner("Analyzing thematic coherence..."):
            try:
                from core.narrative_engine import NarrativeEngine
                engine = NarrativeEngine()
                result = engine.check_thematic_consistency(chapters)
                st.session_state["narrative_themes"] = result
            except ImportError:
                st.error("Narrative Engine not available")
            except Exception as e:
                st.error(f"Error: {e}")

    # Display themes
    if st.session_state.get("narrative_themes"):
        themes = st.session_state["narrative_themes"]

        if themes.get("error"):
            st.error(themes["error"])
            return

        st.markdown("---")

        # Coherence score
        score = themes.get("coherence_score", 0)
        color = "#00c853" if score >= 0.7 else "#ffc107" if score >= 0.5 else "#f44336"
        st.markdown(
            f"<div style='text-align:center;'>"
            f"<h1 style='color:{color};'>{score:.0%}</h1>"
            f"<p>Thematic Coherence</p></div>",
            unsafe_allow_html=True
        )

        # Consistent themes
        if themes.get("consistent_themes"):
            st.markdown("#### Consistent Themes")
            for theme in themes["consistent_themes"]:
                st.success(f"✓ {theme}")

        # Inconsistent themes
        if themes.get("inconsistent_themes"):
            st.markdown("#### Inconsistent Themes")
            for theme in themes["inconsistent_themes"]:
                st.warning(f"⚠ {theme}")

        # Dropped themes
        if themes.get("dropped_themes"):
            st.markdown("#### Dropped Themes")
            st.caption("Themes introduced but not carried through")
            for theme in themes["dropped_themes"]:
                st.error(f"✗ {theme}")

        # Emergent themes
        if themes.get("emergent_themes"):
            st.markdown("#### Emergent Themes")
            st.caption("Themes that appear later without introduction")
            for theme in themes["emergent_themes"]:
                st.info(f"+ {theme}")

        # Recommendations
        if themes.get("recommendations"):
            st.markdown("#### Recommendations")
            for rec in themes["recommendations"]:
                st.markdown(f"- {rec}")


def _display_structure_analysis(result: dict):
    """Display structure analysis results."""

    if result.get("error"):
        st.error(result["error"])
        return

    st.markdown("---")
    st.markdown("#### Structure Analysis Results")

    # Identified structure
    if result.get("identified_structure"):
        st.info(f"**Identified structure type:** {result['identified_structure']}")

    # Chapter breakdown
    if result.get("chapters"):
        st.markdown("#### Chapter Analysis")

        for ch in result["chapters"]:
            with st.expander(f"{ch.get('name', 'Chapter')} ({ch.get('word_count', 0):,} words)"):
                # Progress toward target
                actual = ch.get("word_count", 0)
                target = ch.get("target_words", actual)
                pct = (actual / target * 100) if target > 0 else 0

                st.progress(min(pct / 100, 1.0))
                st.caption(f"{actual:,} / {target:,} words ({pct:.0f}%)")

                if ch.get("assessment"):
                    st.markdown(f"**Assessment:** {ch['assessment']}")

                if ch.get("missing_elements"):
                    st.markdown("**Missing elements:**")
                    for elem in ch["missing_elements"]:
                        st.markdown(f"- {elem}")

    # Overall assessment
    if result.get("overall_assessment"):
        st.markdown("#### Overall Assessment")
        st.markdown(result["overall_assessment"])

    # Recommendations
    if result.get("recommendations"):
        st.markdown("#### Recommendations")
        for rec in result["recommendations"]:
            st.markdown(f"- {rec}")


def _display_gaps(gaps: dict):
    """Display gap analysis results."""

    st.markdown("---")

    # Multi-chapter view
    if gaps.get("chapters"):
        st.markdown("#### Gap Analysis by Chapter")

        for ch_gaps in gaps["chapters"]:
            ch_name = ch_gaps.get("chapter", "Chapter").replace("_", " ").title()

            with st.expander(f"{ch_name}"):
                if ch_gaps.get("error"):
                    st.error(ch_gaps["error"])
                    continue

                _display_single_chapter_gaps(ch_gaps)

    else:
        _display_single_chapter_gaps(gaps)


def _display_single_chapter_gaps(gaps: dict):
    """Display gaps for a single chapter."""

    if gaps.get("error"):
        st.error(gaps["error"])
        return

    # Missing evidence
    if gaps.get("missing_evidence"):
        st.markdown("**Missing Evidence:**")
        for item in gaps["missing_evidence"]:
            st.markdown(f"- 📚 {item}")

    # Logical gaps
    if gaps.get("logical_gaps"):
        st.markdown("**Logical Gaps:**")
        for item in gaps["logical_gaps"]:
            st.markdown(f"- 🔗 {item}")

    # Weak connections
    if gaps.get("weak_connections"):
        st.markdown("**Weak Connections:**")
        for item in gaps["weak_connections"]:
            st.markdown(f"- ⚡ {item}")

    # Suggestions
    if gaps.get("suggestions"):
        st.markdown("**Suggestions:**")
        for item in gaps["suggestions"]:
            st.markdown(f"- 💡 {item}")

    # Priority actions
    if gaps.get("priority_actions"):
        st.markdown("**Priority Actions:**")
        for i, action in enumerate(gaps["priority_actions"], 1):
            st.markdown(f"{i}. {action}")


def _get_fallback_structure(structure_type: str) -> dict:
    """Fallback structure templates."""
    structures = {
        "empirical": {
            "chapters": [
                {"name": "Introduction", "target_pct": 8, "key_elements": ["Context", "Problem", "Questions"]},
                {"name": "Literature Review", "target_pct": 20, "key_elements": ["Theory", "Previous research", "Gaps"]},
                {"name": "Methodology", "target_pct": 15, "key_elements": ["Design", "Methods", "Ethics"]},
                {"name": "Findings", "target_pct": 25, "key_elements": ["Results", "Analysis", "Themes"]},
                {"name": "Discussion", "target_pct": 20, "key_elements": ["Interpretation", "Implications", "Limitations"]},
                {"name": "Conclusion", "target_pct": 7, "key_elements": ["Summary", "Contributions", "Future work"]},
            ]
        },
        "theoretical": {
            "chapters": [
                {"name": "Introduction", "target_pct": 10, "key_elements": ["Context", "Argument", "Structure"]},
                {"name": "Literature Review", "target_pct": 25, "key_elements": ["Theoretical landscape", "Key debates"]},
                {"name": "Theoretical Framework", "target_pct": 20, "key_elements": ["Framework development", "Key concepts"]},
                {"name": "Analysis", "target_pct": 25, "key_elements": ["Application", "Critical analysis"]},
                {"name": "Discussion", "target_pct": 12, "key_elements": ["Implications", "Contributions"]},
                {"name": "Conclusion", "target_pct": 8, "key_elements": ["Summary", "Future directions"]},
            ]
        },
        "papers_based": {
            "chapters": [
                {"name": "Introduction", "target_pct": 12, "key_elements": ["Overview", "Linking narrative"]},
                {"name": "Paper 1", "target_pct": 22, "key_elements": ["Study 1"]},
                {"name": "Paper 2", "target_pct": 22, "key_elements": ["Study 2"]},
                {"name": "Paper 3", "target_pct": 22, "key_elements": ["Study 3"]},
                {"name": "Discussion", "target_pct": 15, "key_elements": ["Synthesis", "Contributions"]},
                {"name": "Conclusion", "target_pct": 7, "key_elements": ["Summary", "Implications"]},
            ]
        },
        "practice_based": {
            "chapters": [
                {"name": "Introduction", "target_pct": 10, "key_elements": ["Context", "Practice focus"]},
                {"name": "Context/Literature", "target_pct": 18, "key_elements": ["Practice context", "Theory"]},
                {"name": "Methodology", "target_pct": 15, "key_elements": ["Practice-based methods"]},
                {"name": "Practice Documentation", "target_pct": 25, "key_elements": ["Process", "Artifacts"]},
                {"name": "Critical Reflection", "target_pct": 20, "key_elements": ["Analysis", "Insights"]},
                {"name": "Conclusion", "target_pct": 12, "key_elements": ["Contributions", "Future practice"]},
            ]
        }
    }
    return structures.get(structure_type, structures["empirical"])
