"""
PHDx Data Lab Tab - Data science workspace for PhD research.

Features:
- CSV/Excel/Google Sheets data import
- Automated exploratory data analysis
- Sentiment analysis for review data
- Statistical testing
- Visualization generation
- Narrative export for thesis
"""

import streamlit as st
import pandas as pd
from io import StringIO, BytesIO
from typing import Optional


def render_data_lab_tab():
    """Render the Data Lab tab interface."""

    # Initialize session state
    _init_session_state()

    st.markdown(
        "<h2 style='font-family:Inter;font-weight:400;color:#9ca3af;'>"
        "📊 Data Lab</h2>",
        unsafe_allow_html=True
    )
    st.caption("Upload, analyze, and visualize your research data")

    # Data import section
    _render_import_section()

    # Only show analysis if data is loaded
    if st.session_state.get("data_lab_df") is not None:
        st.markdown("---")
        _render_analysis_section()


def _init_session_state():
    """Initialize Data Lab session state."""
    defaults = {
        "data_lab_df": None,
        "data_lab_filename": None,
        "data_lab_eda": None,
        "data_lab_sentiment": None,
        "data_lab_stats": None,
        "data_lab_charts": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _render_import_section():
    """Render data import controls."""

    with st.expander("📁 Data Import", expanded=st.session_state.get("data_lab_df") is None):
        import_method = st.radio(
            "Import method",
            ["Upload file", "Google Sheets URL", "Paste CSV"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if import_method == "Upload file":
            uploaded = st.file_uploader(
                "Upload CSV or Excel",
                type=["csv", "xlsx", "xls"],
                label_visibility="collapsed"
            )
            if uploaded:
                try:
                    if uploaded.name.endswith(".csv"):
                        df = pd.read_csv(uploaded)
                    else:
                        df = pd.read_excel(uploaded)

                    st.session_state["data_lab_df"] = df
                    st.session_state["data_lab_filename"] = uploaded.name
                    st.session_state["data_lab_eda"] = None  # Reset analysis
                    st.success(f"Loaded {len(df):,} rows from {uploaded.name}")
                except Exception as e:
                    st.error(f"Error loading file: {e}")

        elif import_method == "Google Sheets URL":
            sheets_url = st.text_input(
                "Google Sheets URL",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                label_visibility="collapsed"
            )
            if st.button("Load Sheet") and sheets_url:
                df = _load_google_sheet(sheets_url)
                if df is not None:
                    st.session_state["data_lab_df"] = df
                    st.session_state["data_lab_filename"] = "Google Sheet"
                    st.session_state["data_lab_eda"] = None
                    st.success(f"Loaded {len(df):,} rows")

        else:  # Paste CSV
            csv_text = st.text_area(
                "Paste CSV data",
                height=150,
                placeholder="col1,col2,col3\nval1,val2,val3\n...",
                label_visibility="collapsed"
            )
            if st.button("Parse CSV") and csv_text:
                try:
                    df = pd.read_csv(StringIO(csv_text))
                    st.session_state["data_lab_df"] = df
                    st.session_state["data_lab_filename"] = "Pasted data"
                    st.session_state["data_lab_eda"] = None
                    st.success(f"Loaded {len(df):,} rows")
                except Exception as e:
                    st.error(f"Error parsing CSV: {e}")

        # Show current data info
        if st.session_state.get("data_lab_df") is not None:
            df = st.session_state["data_lab_df"]
            st.info(f"**Current data**: {st.session_state['data_lab_filename']} | {len(df):,} rows | {len(df.columns)} columns")

            if st.button("Clear data"):
                st.session_state["data_lab_df"] = None
                st.session_state["data_lab_eda"] = None
                st.session_state["data_lab_sentiment"] = None
                st.session_state["data_lab_stats"] = None
                st.rerun()


def _load_google_sheet(url: str) -> Optional[pd.DataFrame]:
    """Load data from a public Google Sheet."""
    try:
        # Convert to CSV export URL
        if "/edit" in url:
            sheet_id = url.split("/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        elif "export?format=csv" in url:
            csv_url = url
        else:
            sheet_id = url.split("/d/")[1].split("/")[0] if "/d/" in url else url
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        st.caption("Note: The sheet must be publicly accessible or shared with 'Anyone with the link'")
        return None


def _render_analysis_section():
    """Render analysis controls and results."""
    df = st.session_state["data_lab_df"]

    # Data preview
    with st.expander("👀 Data Preview", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Rows", f"{len(df):,}")
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            st.metric("Numeric", len(df.select_dtypes(include='number').columns))
        with col4:
            st.metric("Text", len(df.select_dtypes(include='object').columns))

    # Analysis tabs
    analysis_tab, sentiment_tab, stats_tab, viz_tab, export_tab = st.tabs([
        "📈 EDA", "💬 Sentiment", "📊 Statistics", "🎨 Visualize", "📝 Export"
    ])

    with analysis_tab:
        _render_eda_section(df)

    with sentiment_tab:
        _render_sentiment_section(df)

    with stats_tab:
        _render_stats_section(df)

    with viz_tab:
        _render_viz_section(df)

    with export_tab:
        _render_export_section(df)


def _render_eda_section(df: pd.DataFrame):
    """Render exploratory data analysis."""

    if st.button("🔍 Run Exploratory Analysis", type="primary"):
        with st.spinner("Analyzing data..."):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                eda = lab.run_eda(df)
                st.session_state["data_lab_eda"] = eda
            except ImportError:
                st.session_state["data_lab_eda"] = _basic_eda(df)

    if st.session_state.get("data_lab_eda"):
        eda = st.session_state["data_lab_eda"]

        # Overview
        st.markdown("#### Dataset Overview")
        overview = eda.get("overview", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Rows", f"{overview.get('rows', 0):,}")
        with col2:
            st.metric("Total Columns", overview.get("columns", 0))
        with col3:
            missing = overview.get("missing_cells", 0)
            total = overview.get("rows", 1) * overview.get("columns", 1)
            st.metric("Missing Values", f"{missing:,} ({100*missing/total:.1f}%)" if total > 0 else "0")

        # Data types
        st.markdown("#### Column Types")
        dtypes = eda.get("data_types", {})
        if dtypes:
            dtype_df = pd.DataFrame([
                {"Column": col, "Type": dtype}
                for col, dtype in dtypes.items()
            ])
            st.dataframe(dtype_df, use_container_width=True, hide_index=True)

        # Numeric summary
        if eda.get("numeric_summary"):
            st.markdown("#### Numeric Summary")
            num_df = pd.DataFrame(eda["numeric_summary"]).T
            st.dataframe(num_df, use_container_width=True)

        # Categorical summary
        if eda.get("categorical_summary"):
            st.markdown("#### Categorical Summary")
            for col, info in eda["categorical_summary"].items():
                with st.expander(f"📋 {col} ({info.get('unique', 0)} unique values)"):
                    if info.get("top_values"):
                        top_df = pd.DataFrame([
                            {"Value": v, "Count": c}
                            for v, c in info["top_values"].items()
                        ])
                        st.dataframe(top_df, use_container_width=True, hide_index=True)


def _basic_eda(df: pd.DataFrame) -> dict:
    """Basic EDA without DataLab module."""
    return {
        "overview": {
            "rows": len(df),
            "columns": len(df.columns),
            "missing_cells": df.isna().sum().sum(),
        },
        "data_types": df.dtypes.astype(str).to_dict(),
        "numeric_summary": df.describe().to_dict() if len(df.select_dtypes(include='number').columns) > 0 else {},
        "categorical_summary": {
            col: {
                "unique": df[col].nunique(),
                "top_values": df[col].value_counts().head(5).to_dict()
            }
            for col in df.select_dtypes(include='object').columns[:5]
        }
    }


def _render_sentiment_section(df: pd.DataFrame):
    """Render sentiment analysis controls."""

    st.markdown("#### Sentiment Analysis")
    st.caption("Analyze text columns for sentiment (ideal for review data)")

    # Get text columns
    text_cols = df.select_dtypes(include='object').columns.tolist()

    if not text_cols:
        st.warning("No text columns found in your data.")
        return

    text_col = st.selectbox("Select text column to analyze", text_cols)

    # Preview sample
    if text_col:
        st.markdown("**Sample values:**")
        samples = df[text_col].dropna().head(3).tolist()
        for i, sample in enumerate(samples, 1):
            st.caption(f"{i}. {str(sample)[:200]}...")

    if st.button("💬 Run Sentiment Analysis", type="primary"):
        with st.spinner("Analyzing sentiment... (this may take a moment)"):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                result = lab.analyze_sentiment(df, text_col)
                st.session_state["data_lab_sentiment"] = result
            except ImportError:
                st.error("DataLab module not available. Please ensure dependencies are installed.")
                return
            except Exception as e:
                st.error(f"Sentiment analysis error: {e}")
                return

    if st.session_state.get("data_lab_sentiment"):
        result = st.session_state["data_lab_sentiment"]

        if result.get("error"):
            st.error(result["error"])
            return

        # Summary metrics
        dist = result.get("distribution", {})
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Positive", f"{dist.get('positive', 0):.1%}")
        with col2:
            st.metric("Neutral", f"{dist.get('neutral', 0):.1%}")
        with col3:
            st.metric("Negative", f"{dist.get('negative', 0):.1%}")
        with col4:
            avg = result.get("average_score", 0)
            st.metric("Avg Score", f"{avg:.2f}")

        # Show enhanced dataframe with sentiment
        if result.get("dataframe") is not None:
            st.markdown("#### Results Preview")
            result_df = result["dataframe"]
            display_cols = [text_col]
            if "sentiment_label" in result_df.columns:
                display_cols.append("sentiment_label")
            if "sentiment_score" in result_df.columns:
                display_cols.append("sentiment_score")

            st.dataframe(result_df[display_cols].head(20), use_container_width=True)

            # Download enhanced data
            csv = result_df.to_csv(index=False)
            st.download_button(
                "📥 Download with Sentiment",
                csv,
                "data_with_sentiment.csv",
                "text/csv"
            )


def _render_stats_section(df: pd.DataFrame):
    """Render statistical testing section."""

    st.markdown("#### Statistical Tests")

    test_type = st.selectbox(
        "Select test type",
        ["t_test", "chi_square", "anova", "mann_whitney", "correlation"]
    )

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    params = {}

    if test_type == "t_test":
        st.caption("Compare means between two groups")
        if len(numeric_cols) < 1 or len(categorical_cols) < 1:
            st.warning("Need at least one numeric and one categorical column")
            return
        params["value_column"] = st.selectbox("Value column", numeric_cols)
        params["group_column"] = st.selectbox("Group column", categorical_cols)

    elif test_type == "chi_square":
        st.caption("Test independence between two categorical variables")
        if len(categorical_cols) < 2:
            st.warning("Need at least two categorical columns")
            return
        params["column1"] = st.selectbox("First column", categorical_cols)
        params["column2"] = st.selectbox("Second column", categorical_cols, index=1 if len(categorical_cols) > 1 else 0)

    elif test_type == "anova":
        st.caption("Compare means across multiple groups")
        if len(numeric_cols) < 1 or len(categorical_cols) < 1:
            st.warning("Need at least one numeric and one categorical column")
            return
        params["value_column"] = st.selectbox("Value column", numeric_cols)
        params["group_column"] = st.selectbox("Group column", categorical_cols)

    elif test_type == "mann_whitney":
        st.caption("Non-parametric comparison between two groups")
        if len(numeric_cols) < 1 or len(categorical_cols) < 1:
            st.warning("Need at least one numeric and one categorical column")
            return
        params["value_column"] = st.selectbox("Value column", numeric_cols)
        params["group_column"] = st.selectbox("Group column", categorical_cols)

    elif test_type == "correlation":
        st.caption("Calculate correlation between numeric variables")
        if len(numeric_cols) < 2:
            st.warning("Need at least two numeric columns")
            return
        params["column1"] = st.selectbox("First column", numeric_cols)
        params["column2"] = st.selectbox("Second column", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)

    if st.button("📊 Run Test", type="primary"):
        with st.spinner("Running statistical test..."):
            try:
                from core.data_lab import DataLab
                lab = DataLab()

                if test_type == "correlation":
                    result = lab.correlation_analysis(df, params["column1"], params["column2"])
                else:
                    result = lab.significance_test(df, test_type, **params)

                st.session_state["data_lab_stats"] = result
            except ImportError:
                st.error("DataLab module not available")
                return
            except Exception as e:
                st.error(f"Test error: {e}")
                return

    if st.session_state.get("data_lab_stats"):
        result = st.session_state["data_lab_stats"]

        if result.get("error"):
            st.error(result["error"])
            return

        st.markdown("#### Test Results")

        # Display key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Test", result.get("test_name", test_type))
        with col2:
            stat = result.get("statistic", result.get("correlation", 0))
            st.metric("Statistic", f"{stat:.4f}")
        with col3:
            pval = result.get("p_value", 1)
            sig = "Yes" if pval < 0.05 else "No"
            st.metric("Significant (p<0.05)", sig, f"p={pval:.4f}")

        # Interpretation
        if result.get("interpretation"):
            st.info(f"**Interpretation:** {result['interpretation']}")


def _render_viz_section(df: pd.DataFrame):
    """Render visualization section."""

    st.markdown("#### Create Visualizations")

    viz_type = st.selectbox(
        "Chart type",
        ["histogram", "bar_chart", "scatter", "box_plot", "line_chart"]
    )

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()
    all_cols = df.columns.tolist()

    if viz_type == "histogram":
        if not numeric_cols:
            st.warning("No numeric columns for histogram")
            return
        col = st.selectbox("Column", numeric_cols)
        bins = st.slider("Bins", 5, 50, 20)

        if st.button("Create Chart"):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                fig = lab.create_visualization(df, "histogram", x_column=col, bins=bins)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                # Fallback to streamlit native
                st.bar_chart(df[col].value_counts(bins=bins).sort_index())

    elif viz_type == "bar_chart":
        if not categorical_cols:
            st.warning("No categorical columns for bar chart")
            return
        col = st.selectbox("Column", categorical_cols)

        if st.button("Create Chart"):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                fig = lab.create_visualization(df, "bar", x_column=col)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.bar_chart(df[col].value_counts())

    elif viz_type == "scatter":
        if len(numeric_cols) < 2:
            st.warning("Need at least two numeric columns")
            return
        x_col = st.selectbox("X axis", numeric_cols)
        y_col = st.selectbox("Y axis", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
        color_col = st.selectbox("Color by (optional)", ["None"] + categorical_cols)

        if st.button("Create Chart"):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                color = color_col if color_col != "None" else None
                fig = lab.create_visualization(df, "scatter", x_column=x_col, y_column=y_col, color_column=color)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.scatter_chart(df[[x_col, y_col]])

    elif viz_type == "box_plot":
        if not numeric_cols:
            st.warning("No numeric columns for box plot")
            return
        value_col = st.selectbox("Value column", numeric_cols)
        group_col = st.selectbox("Group by (optional)", ["None"] + categorical_cols)

        if st.button("Create Chart"):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                group = group_col if group_col != "None" else None
                fig = lab.create_visualization(df, "box", y_column=value_col, x_column=group)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.warning("Plotly required for box plots")

    elif viz_type == "line_chart":
        x_col = st.selectbox("X axis", all_cols)
        y_col = st.selectbox("Y axis", numeric_cols if numeric_cols else all_cols)

        if st.button("Create Chart"):
            try:
                from core.data_lab import DataLab
                lab = DataLab()
                fig = lab.create_visualization(df, "line", x_column=x_col, y_column=y_col)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.line_chart(df.set_index(x_col)[y_col])


def _render_export_section(df: pd.DataFrame):
    """Render export and narrative generation section."""

    st.markdown("#### Export Analysis")

    # Download processed data
    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            "processed_data.csv",
            "text/csv"
        )

    with col2:
        try:
            buffer = BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button(
                "📥 Download Excel",
                buffer.getvalue(),
                "processed_data.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except ImportError:
            st.caption("Install openpyxl for Excel export")

    st.markdown("---")
    st.markdown("#### Generate Thesis Narrative")
    st.caption("Transform your analysis into thesis-ready prose")

    chapter_context = st.selectbox(
        "Chapter context",
        ["Methodology", "Findings", "Discussion", "Results"]
    )

    focus = st.text_area(
        "Analysis focus",
        placeholder="What aspect of the data should the narrative focus on?\ne.g., 'The sentiment distribution across review platforms' or 'Statistical comparison of ratings by year'",
        height=100
    )

    if st.button("📝 Generate Narrative", type="primary"):
        if not focus:
            st.warning("Please describe what the narrative should focus on")
            return

        with st.spinner("Generating thesis narrative..."):
            try:
                from core.data_lab import DataLab
                lab = DataLab()

                # Gather available analyses
                analysis_results = {}
                if st.session_state.get("data_lab_eda"):
                    analysis_results["eda"] = st.session_state["data_lab_eda"]
                if st.session_state.get("data_lab_sentiment"):
                    analysis_results["sentiment"] = st.session_state["data_lab_sentiment"]
                if st.session_state.get("data_lab_stats"):
                    analysis_results["statistics"] = st.session_state["data_lab_stats"]

                narrative = lab.generate_narrative(
                    analysis_results,
                    chapter_context.lower(),
                    focus
                )

                if narrative.get("narrative"):
                    st.markdown("#### Generated Narrative")
                    st.markdown(narrative["narrative"])

                    st.download_button(
                        "📥 Download Narrative",
                        narrative["narrative"],
                        f"data_narrative_{chapter_context.lower()}.md",
                        "text/markdown"
                    )
                else:
                    st.error(narrative.get("error", "Failed to generate narrative"))

            except Exception as e:
                st.error(f"Error generating narrative: {e}")
