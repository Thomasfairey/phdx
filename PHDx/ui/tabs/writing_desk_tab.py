"""
PHDx Writing Desk Tab - AI-assisted drafting workspace.

Features:
- Chapter outline builder with templates
- AI-assisted drafting with DNA voice matching
- Real-time gap identification
- Counter-argument generation
- Inline citation suggestions
"""

import streamlit as st


def render_writing_desk_tab():
    """Render the Writing Desk tab interface."""

    # Initialize session state
    _init_session_state()

    st.markdown(
        "<h2 style='font-family:Inter;font-weight:400;color:#9ca3af;'>"
        "✍️ Writing Desk</h2>",
        unsafe_allow_html=True
    )
    st.caption("AI-assisted drafting with your voice and style")

    # Sub-tabs for different writing modes
    outline_tab, draft_tab, refine_tab, cite_tab = st.tabs([
        "📋 Outline", "📝 Draft", "🔧 Refine", "📚 Cite"
    ])

    with outline_tab:
        _render_outline_section()

    with draft_tab:
        _render_draft_section()

    with refine_tab:
        _render_refine_section()

    with cite_tab:
        _render_citation_section()


def _init_session_state():
    """Initialize Writing Desk session state."""
    defaults = {
        "writing_outline": None,
        "writing_current_chapter": None,
        "writing_draft": "",
        "writing_gaps": None,
        "writing_counter_args": None,
        "writing_citations": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_outline_section():
    """Render chapter outline builder."""

    st.markdown("#### Chapter Outline Builder")

    # Chapter type selection
    chapter_type = st.selectbox(
        "Chapter type",
        [
            "introduction",
            "literature_review",
            "methodology",
            "findings",
            "discussion",
            "conclusion"
        ],
        format_func=lambda x: x.replace("_", " ").title()
    )

    # Get template info
    try:
        from core.writing_desk import WritingDesk, CHAPTER_TEMPLATES
        desk = WritingDesk()
        template = CHAPTER_TEMPLATES.get(chapter_type, {})
    except ImportError:
        template = _get_fallback_template(chapter_type)
        desk = None

    # Show template info
    if template:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Target Words", f"{template.get('target_words', 0):,}")
        with col2:
            st.metric("Sections", len(template.get("sections", [])))

        st.markdown("**Standard sections:**")
        for section in template.get("sections", []):
            st.markdown(f"- {section}")

    # Thesis context
    st.markdown("---")
    st.markdown("#### Your Thesis Context")

    thesis_title = st.text_input(
        "Thesis title",
        placeholder="e.g., 'Animal Welfare in Tourism: A Multi-Platform Analysis'"
    )

    research_questions = st.text_area(
        "Research questions",
        placeholder="List your main research questions (one per line)",
        height=100
    )

    key_themes = st.text_input(
        "Key themes/concepts",
        placeholder="e.g., animal welfare, responsible tourism, sentiment analysis"
    )

    # Generate outline
    if st.button("📋 Generate Outline", type="primary"):
        if not thesis_title:
            st.warning("Please provide your thesis title")
            return

        with st.spinner("Generating chapter outline..."):
            try:
                if desk:
                    outline = desk.build_outline(
                        chapter_type,
                        {
                            "thesis_title": thesis_title,
                            "research_questions": research_questions.split("\n") if research_questions else [],
                            "key_themes": [t.strip() for t in key_themes.split(",")] if key_themes else []
                        }
                    )
                else:
                    outline = _generate_basic_outline(chapter_type, thesis_title)

                st.session_state["writing_outline"] = outline
                st.session_state["writing_current_chapter"] = chapter_type

            except Exception as e:
                st.error(f"Error generating outline: {e}")

    # Display outline
    if st.session_state.get("writing_outline"):
        outline = st.session_state["writing_outline"]

        st.markdown("---")
        st.markdown("#### Generated Outline")

        if outline.get("error"):
            st.error(outline["error"])
        else:
            # Chapter title
            st.markdown(f"### {outline.get('chapter_title', chapter_type.replace('_', ' ').title())}")

            # Sections
            for i, section in enumerate(outline.get("sections", []), 1):
                with st.expander(f"{i}. {section.get('title', 'Section')}", expanded=True):
                    st.markdown(f"**Purpose:** {section.get('purpose', '')}")
                    st.markdown(f"**Target words:** {section.get('target_words', 0)}")

                    if section.get("key_points"):
                        st.markdown("**Key points to cover:**")
                        for point in section["key_points"]:
                            st.markdown(f"- {point}")

            # Download outline
            outline_md = _format_outline_markdown(outline)
            st.download_button(
                "📥 Download Outline",
                outline_md,
                f"outline_{chapter_type}.md",
                "text/markdown"
            )


def _render_draft_section():
    """Render AI-assisted drafting section."""

    st.markdown("#### AI-Assisted Drafting")

    # Check for DNA profile
    try:
        from core.services import get_services
        services = get_services()
        has_dna = services.has_dna_profile()
    except ImportError:
        has_dna = False

    if has_dna:
        st.success("DNA profile loaded - drafts will match your writing voice")
    else:
        st.info("No DNA profile found - drafts will use academic style")

    # Section context
    col1, col2 = st.columns(2)
    with col1:
        section_type = st.selectbox(
            "Section type",
            ["introduction", "literature_review", "methodology", "findings", "discussion", "conclusion", "general"],
            format_func=lambda x: x.replace("_", " ").title()
        )
    with col2:
        tone = st.selectbox(
            "Tone",
            ["academic", "analytical", "descriptive", "argumentative"]
        )

    # Drafting prompt
    prompt = st.text_area(
        "What would you like to draft?",
        placeholder="Describe what you want to write. Be specific about:\n- The argument or point to make\n- Key evidence to include\n- How it connects to your thesis",
        height=150
    )

    # Additional context
    with st.expander("Additional context (optional)"):
        existing_text = st.text_area(
            "Existing text to build upon",
            placeholder="Paste any existing draft text you want to continue or expand",
            height=100
        )
        notes = st.text_area(
            "Research notes",
            placeholder="Any notes, quotes, or data points to incorporate",
            height=100
        )

    # Generate draft
    col1, col2 = st.columns(2)
    with col1:
        use_dna = st.checkbox("Use DNA voice matching", value=has_dna, disabled=not has_dna)
    with col2:
        target_words = st.number_input("Target words", min_value=100, max_value=5000, value=500, step=100)

    if st.button("📝 Generate Draft", type="primary"):
        if not prompt:
            st.warning("Please describe what you want to draft")
            return

        with st.spinner("Generating draft..."):
            try:
                from core.writing_desk import WritingDesk
                desk = WritingDesk()

                section_context = {
                    "type": section_type,
                    "tone": tone,
                    "target_words": target_words,
                    "existing_text": existing_text,
                    "notes": notes
                }

                result = desk.generate_draft(prompt, section_context, use_dna=use_dna)

                if result.get("draft"):
                    st.session_state["writing_draft"] = result["draft"]
                else:
                    st.error(result.get("error", "Failed to generate draft"))

            except ImportError:
                st.error("Writing Desk module not available")
            except Exception as e:
                st.error(f"Error generating draft: {e}")

    # Display draft
    if st.session_state.get("writing_draft"):
        st.markdown("---")
        st.markdown("#### Generated Draft")

        draft = st.session_state["writing_draft"]
        word_count = len(draft.split())

        st.metric("Word Count", f"{word_count:,}")

        # Editable draft
        edited_draft = st.text_area(
            "Edit draft",
            value=draft,
            height=400,
            label_visibility="collapsed"
        )
        st.session_state["writing_draft"] = edited_draft

        # Actions
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                "📥 Download",
                edited_draft,
                "draft.md",
                "text/markdown"
            )
        with col2:
            if st.button("🔧 Analyze Gaps"):
                st.session_state["_analyze_gaps"] = True
        with col3:
            if st.button("🗑️ Clear"):
                st.session_state["writing_draft"] = ""
                st.rerun()


def _render_refine_section():
    """Render draft refinement section."""

    st.markdown("#### Refine Your Draft")

    # Input text
    draft_text = st.text_area(
        "Draft to refine",
        value=st.session_state.get("writing_draft", ""),
        height=200,
        placeholder="Paste or type the draft text you want to refine"
    )

    if not draft_text:
        st.info("Enter draft text above or generate one in the Draft tab")
        return

    # Refinement options
    st.markdown("#### Refinement Tools")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Identify Gaps", use_container_width=True):
            with st.spinner("Analyzing for gaps..."):
                try:
                    from core.writing_desk import WritingDesk
                    desk = WritingDesk()
                    gaps = desk.identify_gaps(draft_text)
                    st.session_state["writing_gaps"] = gaps
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("⚔️ Counter-Arguments", use_container_width=True):
            with st.spinner("Generating counter-arguments..."):
                try:
                    from core.writing_desk import WritingDesk
                    desk = WritingDesk()
                    counter = desk.generate_counter_arguments(draft_text)
                    st.session_state["writing_counter_args"] = counter
                except Exception as e:
                    st.error(f"Error: {e}")

    with col2:
        if st.button("✨ Strengthen Argument", use_container_width=True):
            with st.spinner("Strengthening argument..."):
                try:
                    from core.writing_desk import WritingDesk
                    desk = WritingDesk()
                    strengthened = desk.strengthen_argument(draft_text)

                    if strengthened.get("strengthened_text"):
                        st.session_state["writing_draft"] = strengthened["strengthened_text"]
                        st.success("Argument strengthened - see Draft tab")
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.button("🎯 Check Coherence", use_container_width=True):
            with st.spinner("Checking coherence..."):
                try:
                    from core.services import get_services
                    services = get_services()
                    result = services.check_consistency(draft_text)

                    if result.get("consistent"):
                        st.success("Text is coherent!")
                    else:
                        st.warning("Some inconsistencies found")
                        for issue in result.get("issues", []):
                            st.markdown(f"- {issue}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # Display gap analysis
    if st.session_state.get("writing_gaps"):
        gaps = st.session_state["writing_gaps"]
        st.markdown("---")
        st.markdown("#### Gap Analysis")

        if gaps.get("error"):
            st.error(gaps["error"])
        else:
            # Missing evidence
            if gaps.get("missing_evidence"):
                st.markdown("**Missing Evidence:**")
                for item in gaps["missing_evidence"]:
                    st.markdown(f"- {item}")

            # Logical gaps
            if gaps.get("logical_gaps"):
                st.markdown("**Logical Gaps:**")
                for item in gaps["logical_gaps"]:
                    st.markdown(f"- {item}")

            # Unsupported assertions
            if gaps.get("unsupported_assertions"):
                st.markdown("**Unsupported Assertions:**")
                for item in gaps["unsupported_assertions"]:
                    st.markdown(f"- {item}")

            # Suggestions
            if gaps.get("suggestions"):
                st.markdown("**Suggestions:**")
                for item in gaps["suggestions"]:
                    st.markdown(f"- {item}")

    # Display counter-arguments
    if st.session_state.get("writing_counter_args"):
        counter = st.session_state["writing_counter_args"]
        st.markdown("---")
        st.markdown("#### Counter-Arguments to Address")

        if counter.get("error"):
            st.error(counter["error"])
        else:
            for i, arg in enumerate(counter.get("counter_arguments", []), 1):
                with st.expander(f"Counter-argument {i}: {arg.get('argument', '')[:50]}..."):
                    st.markdown(f"**Argument:** {arg.get('argument', '')}")
                    st.markdown(f"**Strength:** {arg.get('strength', 'medium')}")
                    if arg.get("response_strategy"):
                        st.markdown(f"**Response strategy:** {arg['response_strategy']}")


def _render_citation_section():
    """Render citation suggestions section."""

    st.markdown("#### Citation Suggestions")
    st.caption("Get relevant citations from your Zotero library")

    # Check Zotero connection
    try:
        from core.services import get_services
        services = get_services()
        # Try to access zotero property
        zotero_available = True
    except Exception:
        zotero_available = False

    if not zotero_available:
        st.warning("Zotero integration not configured. Check your API credentials.")
        return

    # Context input
    context = st.text_area(
        "What are you writing about?",
        placeholder="Describe the topic or paste the text that needs citations",
        height=150
    )

    num_citations = st.slider("Number of suggestions", 3, 10, 5)

    if st.button("📚 Find Citations", type="primary"):
        if not context:
            st.warning("Please provide context for citation suggestions")
            return

        with st.spinner("Searching your Zotero library..."):
            try:
                citations = services.get_citations(context, num_citations)
                st.session_state["writing_citations"] = citations
            except Exception as e:
                st.error(f"Error: {e}")

    # Display citations
    if st.session_state.get("writing_citations"):
        citations = st.session_state["writing_citations"]

        if not citations:
            st.info("No matching citations found in your library")
        else:
            st.markdown("#### Suggested Citations")

            for i, cit in enumerate(citations, 1):
                with st.expander(f"{i}. {cit.get('title', 'Untitled')[:60]}..."):
                    # Author and year
                    authors = cit.get("creators", [])
                    author_str = ", ".join([
                        f"{a.get('lastName', '')}" for a in authors[:3]
                    ])
                    if len(authors) > 3:
                        author_str += " et al."

                    year = cit.get("date", "")[:4] if cit.get("date") else "n.d."

                    st.markdown(f"**{author_str} ({year})**")
                    st.markdown(f"*{cit.get('title', '')}*")

                    if cit.get("publicationTitle"):
                        st.markdown(f"Published in: {cit['publicationTitle']}")

                    if cit.get("abstractNote"):
                        st.caption(cit["abstractNote"][:300] + "...")

                    # Copy citation
                    cite_key = f"({author_str}, {year})"
                    st.code(cite_key, language=None)


def _get_fallback_template(chapter_type: str) -> dict:
    """Fallback templates when WritingDesk not available."""
    templates = {
        "introduction": {
            "target_words": 2000,
            "sections": [
                "Research context and background",
                "Problem statement",
                "Research questions",
                "Significance of the study",
                "Thesis structure overview"
            ]
        },
        "literature_review": {
            "target_words": 8000,
            "sections": [
                "Theoretical framework",
                "Key concepts and definitions",
                "Previous research",
                "Research gaps",
                "Chapter summary"
            ]
        },
        "methodology": {
            "target_words": 5000,
            "sections": [
                "Research philosophy",
                "Research design",
                "Data collection methods",
                "Data analysis approach",
                "Ethical considerations",
                "Limitations"
            ]
        },
        "findings": {
            "target_words": 6000,
            "sections": [
                "Overview of findings",
                "Theme/Finding 1",
                "Theme/Finding 2",
                "Theme/Finding 3",
                "Summary of key results"
            ]
        },
        "discussion": {
            "target_words": 5000,
            "sections": [
                "Summary of findings",
                "Interpretation and analysis",
                "Relation to literature",
                "Implications",
                "Limitations revisited"
            ]
        },
        "conclusion": {
            "target_words": 2000,
            "sections": [
                "Research summary",
                "Key contributions",
                "Practical implications",
                "Future research",
                "Final remarks"
            ]
        }
    }
    return templates.get(chapter_type, {"target_words": 3000, "sections": []})


def _generate_basic_outline(chapter_type: str, thesis_title: str) -> dict:
    """Generate basic outline without WritingDesk."""
    template = _get_fallback_template(chapter_type)
    return {
        "chapter_title": f"{chapter_type.replace('_', ' ').title()}: {thesis_title}",
        "sections": [
            {
                "title": section,
                "purpose": f"Address {section.lower()} for the thesis",
                "target_words": template["target_words"] // len(template["sections"]),
                "key_points": []
            }
            for section in template["sections"]
        ]
    }


def _format_outline_markdown(outline: dict) -> str:
    """Format outline as markdown."""
    lines = [
        f"# {outline.get('chapter_title', 'Chapter Outline')}",
        "",
    ]

    for i, section in enumerate(outline.get("sections", []), 1):
        lines.append(f"## {i}. {section.get('title', 'Section')}")
        lines.append(f"**Purpose:** {section.get('purpose', '')}")
        lines.append(f"**Target words:** {section.get('target_words', 0)}")
        lines.append("")

        if section.get("key_points"):
            lines.append("**Key points:**")
            for point in section["key_points"]:
                lines.append(f"- {point}")
            lines.append("")

    return "\n".join(lines)
