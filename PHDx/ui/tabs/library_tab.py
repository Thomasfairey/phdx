"""
PHDx Library Tab - Zotero integration and citation management.

Features:
- Browse Zotero library
- Search for citations
- Generate bibliographies
- Citation coverage analysis
"""

import streamlit as st


def render_library_tab():
    """Render the Library tab interface."""

    # Initialize session state
    _init_session_state()

    st.markdown(
        "<h2 style='font-family:Inter;font-weight:400;color:#9ca3af;'>📚 Library</h2>",
        unsafe_allow_html=True,
    )
    st.caption("Manage citations from your Zotero library")

    # Check Zotero connection
    zotero_status = _check_zotero_connection()

    if not zotero_status["connected"]:
        _render_connection_setup()
        return

    st.success(f"Connected to Zotero ({zotero_status.get('item_count', 0):,} items)")

    # Sub-tabs
    browse_tab, search_tab, bib_tab, coverage_tab = st.tabs(
        ["📖 Browse", "🔍 Search", "📋 Bibliography", "📊 Coverage"]
    )

    with browse_tab:
        _render_browse_section()

    with search_tab:
        _render_search_section()

    with bib_tab:
        _render_bibliography_section()

    with coverage_tab:
        _render_coverage_section()


def _init_session_state():
    """Initialize Library tab session state."""
    defaults = {
        "library_items": None,
        "library_search_results": None,
        "library_selected_items": [],
        "library_bibliography": None,
        "library_coverage": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _check_zotero_connection() -> dict:
    """Check if Zotero is configured and connected."""
    try:
        from core.services import get_services

        services = get_services()
        zotero = services.zotero

        # Try a simple operation to verify connection
        if hasattr(zotero, "get_library_stats"):
            stats = zotero.get_library_stats()
            return {"connected": True, "item_count": stats.get("total_items", 0)}

        return {"connected": True, "item_count": 0}

    except Exception as e:
        return {"connected": False, "error": str(e)}


def _render_connection_setup():
    """Render Zotero connection setup."""

    st.warning("Zotero not connected")

    st.markdown("""
    ### Connect to Zotero

    To use the Library features, you need to configure your Zotero API credentials.

    **Steps:**
    1. Go to [Zotero Settings](https://www.zotero.org/settings/keys)
    2. Create a new API key with read access
    3. Note your User ID from the page
    4. Add to your `.env` or `secrets.toml` file:
    """)

    st.code(
        """
ZOTERO_USER_ID=your_user_id
ZOTERO_API_KEY=your_api_key
    """,
        language="toml",
    )

    st.markdown("After adding credentials, restart the application.")


def _render_browse_section():
    """Render library browsing section."""

    st.markdown("#### Browse Library")

    # Collection filter
    col1, col2 = st.columns([2, 1])
    with col1:
        collection = st.text_input(
            "Filter by collection (optional)", placeholder="Collection name..."
        )
    with col2:
        limit = st.number_input("Items to load", min_value=10, max_value=100, value=25)

    if st.button("📖 Load Items"):
        with st.spinner("Loading from Zotero..."):
            try:
                from core.services import get_services

                services = get_services()

                if collection:
                    items = services.zotero.search_library(collection, limit)
                else:
                    items = services.zotero.get_recent_items(limit)

                st.session_state["library_items"] = items

            except Exception as e:
                st.error(f"Error loading items: {e}")

    # Display items
    if st.session_state.get("library_items"):
        items = st.session_state["library_items"]

        if not items:
            st.info("No items found")
            return

        st.markdown(f"**{len(items)} items**")

        for item in items:
            _render_item_card(item)


def _render_search_section():
    """Render citation search section."""

    st.markdown("#### Search Library")

    search_query = st.text_input(
        "Search query", placeholder="Search by title, author, or keywords..."
    )

    col1, col2 = st.columns(2)
    with col1:
        _ = st.selectbox(  # search_type not yet implemented
            "Search in", ["All fields", "Title", "Author", "Tags"]
        )
    with col2:
        max_results = st.number_input(
            "Max results", min_value=5, max_value=50, value=20
        )

    if st.button("🔍 Search", type="primary"):
        if not search_query:
            st.warning("Please enter a search query")
            return

        with st.spinner("Searching..."):
            try:
                from core.services import get_services

                services = get_services()

                results = services.zotero.search_library(search_query, max_results)
                st.session_state["library_search_results"] = results

            except Exception as e:
                st.error(f"Search error: {e}")

    # Display results
    if st.session_state.get("library_search_results"):
        results = st.session_state["library_search_results"]

        st.markdown("---")
        st.markdown(f"#### Search Results ({len(results)} items)")

        if not results:
            st.info("No results found")
            return

        for item in results:
            _render_item_card(item, selectable=True)


def _render_bibliography_section():
    """Render bibliography generation section."""

    st.markdown("#### Generate Bibliography")
    st.caption("Create an Oxford Brookes Harvard formatted bibliography")

    # Selection method
    method = st.radio(
        "Select items by",
        ["Search and select", "Paste citation keys", "Use selected items"],
        horizontal=True,
    )

    if method == "Search and select":
        search = st.text_input("Search for items to add", placeholder="Search...")

        if search:
            try:
                from core.services import get_services

                services = get_services()
                results = services.zotero.search_library(search, 10)

                for item in results:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{item.get('title', 'Untitled')}**")
                        authors = _format_authors(item.get("creators", []))
                        st.caption(f"{authors} ({item.get('date', 'n.d.')[:4]})")
                    with col2:
                        key = item.get("key", "")
                        if st.button("Add", key=f"add_{key}"):
                            if key not in st.session_state["library_selected_items"]:
                                st.session_state["library_selected_items"].append(key)
                                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

    elif method == "Paste citation keys":
        keys_text = st.text_area(
            "Citation keys (one per line)",
            placeholder="ABC123\nDEF456\n...",
            height=100,
        )
        if keys_text:
            st.session_state["library_selected_items"] = [
                k.strip() for k in keys_text.strip().split("\n") if k.strip()
            ]

    # Show selected items
    selected = st.session_state.get("library_selected_items", [])
    if selected:
        st.markdown(f"**Selected items:** {len(selected)}")
        st.caption(", ".join(selected[:10]) + ("..." if len(selected) > 10 else ""))

        if st.button("Clear selection"):
            st.session_state["library_selected_items"] = []
            st.rerun()

    # Sort option
    sort_by = st.selectbox("Sort bibliography by", ["author", "date", "title"])

    # Generate
    if st.button("📋 Generate Bibliography", type="primary"):
        if not selected:
            st.warning("No items selected")
            return

        with st.spinner("Generating bibliography..."):
            try:
                from core.services import get_services

                services = get_services()

                bib = services.zotero.generate_bibliography(
                    citation_keys=selected, sort_by=sort_by
                )
                st.session_state["library_bibliography"] = bib

            except Exception as e:
                st.error(f"Error: {e}")

    # Display bibliography
    if st.session_state.get("library_bibliography"):
        bib = st.session_state["library_bibliography"]

        st.markdown("---")
        st.markdown("#### Generated Bibliography")
        st.markdown("*Oxford Brookes Harvard format*")

        st.text_area(
            "Bibliography", value=bib, height=300, label_visibility="collapsed"
        )

        st.download_button(
            "📥 Download Bibliography", bib, "bibliography.txt", "text/plain"
        )


def _render_coverage_section():
    """Render citation coverage analysis section."""

    st.markdown("#### Citation Coverage Analysis")
    st.caption("Analyze citation density and find gaps in your references")

    draft_text = st.text_area(
        "Draft text to analyze",
        height=200,
        placeholder="Paste your draft text with in-text citations (Author, Year) format...",
    )

    chapter_type = st.selectbox(
        "Chapter type",
        [
            "introduction",
            "literature_review",
            "methodology",
            "findings",
            "discussion",
            "conclusion",
        ],
        format_func=lambda x: x.replace("_", " ").title(),
    )

    if st.button("📊 Analyze Coverage", type="primary"):
        if not draft_text or len(draft_text) < 200:
            st.warning("Please provide at least 200 characters of draft text")
            return

        with st.spinner("Analyzing citation coverage..."):
            try:
                from core.services import get_services

                services = get_services()

                coverage = services.zotero.analyze_citation_coverage(
                    draft_text, chapter_type
                )
                st.session_state["library_coverage"] = coverage

            except Exception as e:
                st.error(f"Error: {e}")

    # Display coverage
    if st.session_state.get("library_coverage"):
        coverage = st.session_state["library_coverage"]

        if coverage.get("error"):
            st.error(coverage["error"])
            return

        st.markdown("---")

        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Citations Found", coverage.get("citation_count", 0))
        with col2:
            density = coverage.get("citation_density", 0)
            st.metric("Citation Density", f"{density:.1f}/1000 words")
        with col3:
            matched = coverage.get("matched_count", 0)
            total = coverage.get("citation_count", 1)
            st.metric("Library Match Rate", f"{matched}/{total}")

        # Density assessment
        density = coverage.get("citation_density", 0)
        if chapter_type == "literature_review":
            if density < 5:
                st.warning(
                    "Citation density is low for a literature review (recommended: 8-15 per 1000 words)"
                )
            elif density > 20:
                st.info(
                    "Citation density is high - ensure your own voice comes through"
                )
            else:
                st.success("Citation density is appropriate for a literature review")
        else:
            if density < 2:
                st.warning("Consider adding more citations to support your claims")
            else:
                st.success("Citation density is reasonable")

        # Cited papers
        if coverage.get("cited_papers"):
            with st.expander("📚 Cited Papers"):
                for paper in coverage["cited_papers"]:
                    st.markdown(f"- {paper}")

        # Unmatched citations
        if coverage.get("unmatched_citations"):
            with st.expander("⚠️ Unmatched Citations"):
                st.caption("These citations weren't found in your Zotero library")
                for cit in coverage["unmatched_citations"]:
                    st.markdown(f"- {cit}")

        # Suggested papers
        if coverage.get("suggested_papers"):
            st.markdown("#### Suggested Additional Citations")
            st.caption("Papers in your library that might be relevant")
            for paper in coverage["suggested_papers"][:5]:
                st.markdown(
                    f"- {paper.get('title', 'Untitled')} ({paper.get('date', 'n.d.')[:4]})"
                )


def _render_item_card(item: dict, selectable: bool = False):
    """Render a single library item card."""

    title = item.get("title", "Untitled")
    authors = _format_authors(item.get("creators", []))
    year = item.get("date", "n.d.")[:4] if item.get("date") else "n.d."
    item_type = item.get("itemType", "document")

    with st.container():
        col1, col2 = st.columns([5, 1])

        with col1:
            st.markdown(f"**{title}**")
            st.caption(f"{authors} ({year}) • {item_type}")

            if item.get("publicationTitle"):
                st.caption(f"*{item['publicationTitle']}*")

        with col2:
            if selectable:
                key = item.get("key", "")
                selected = key in st.session_state.get("library_selected_items", [])
                if st.checkbox("Select", value=selected, key=f"sel_{key}"):
                    if key not in st.session_state["library_selected_items"]:
                        st.session_state["library_selected_items"].append(key)
                else:
                    if key in st.session_state["library_selected_items"]:
                        st.session_state["library_selected_items"].remove(key)

        # Expandable details
        with st.expander("Details"):
            if item.get("abstractNote"):
                st.markdown("**Abstract:**")
                st.markdown(
                    item["abstractNote"][:500]
                    + ("..." if len(item.get("abstractNote", "")) > 500 else "")
                )

            if item.get("tags"):
                tags = ", ".join([t.get("tag", "") for t in item["tags"][:5]])
                st.markdown(f"**Tags:** {tags}")

            if item.get("DOI"):
                st.markdown(f"**DOI:** {item['DOI']}")

            if item.get("url"):
                st.markdown(f"**URL:** {item['url']}")

        st.markdown("---")


def _format_authors(creators: list) -> str:
    """Format creator list as author string."""
    if not creators:
        return "Unknown"

    authors = [c for c in creators if c.get("creatorType") == "author"]
    if not authors:
        authors = creators

    if len(authors) == 1:
        return authors[0].get("lastName", authors[0].get("name", "Unknown"))
    elif len(authors) == 2:
        return f"{authors[0].get('lastName', '')} & {authors[1].get('lastName', '')}"
    else:
        return f"{authors[0].get('lastName', '')} et al."
