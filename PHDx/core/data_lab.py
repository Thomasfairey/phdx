"""
Data Lab - Data Science Module for PHDx

Provides comprehensive data analysis capabilities for PhD research:
- Data loading from CSV, Excel, Google Sheets
- Automated Exploratory Data Analysis (EDA)
- Sentiment analysis for review data (TripAdvisor, Google Reviews)
- Statistical tests (t-test, chi-square, ANOVA, correlations)
- Visualization generation
- Narrative export for thesis integration

Designed for desk research analyzing review site data.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
import io

import pandas as pd
import numpy as np

# Optional imports - graceful degradation if not available
try:
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    stats = None

try:
    import plotly.express as px
    import plotly.graph_objects as go

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    px = None
    go = None

try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

# Local imports
from core.secrets_utils import get_secret
from core.ethics_utils import log_ai_usage

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
ANALYSIS_CACHE = DATA_DIR / "analysis_cache"
ANALYSIS_CACHE.mkdir(parents=True, exist_ok=True)


class DataLab:
    """
    Data Science Module for PHDx.

    Handles CSV/Excel/Google Sheets data with automated EDA,
    sentiment analysis, and statistical testing.
    """

    def __init__(self):
        """Initialize the Data Lab with optional components."""
        self._sentiment_pipeline = None
        self._llm_available = False

        # Check LLM availability for narrative generation
        try:
            from core import llm_gateway

            self._llm_gateway = llm_gateway
            self._llm_available = True
        except ImportError:
            self._llm_gateway = None

    # =========================================================================
    # DATA INGESTION
    # =========================================================================

    def load_csv(self, file_path: Union[str, Path, io.BytesIO], **kwargs) -> dict:
        """
        Load data from a CSV file.

        Args:
            file_path: Path to CSV file or file-like object
            **kwargs: Additional pandas read_csv arguments

        Returns:
            dict with status, dataframe, and metadata
        """
        try:
            df = pd.read_csv(file_path, **kwargs)
            return self._create_load_result(df, "csv", str(file_path))
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def load_excel(
        self,
        file_path: Union[str, Path, io.BytesIO],
        sheet_name: Optional[str] = None,
        **kwargs,
    ) -> dict:
        """
        Load data from an Excel file.

        Args:
            file_path: Path to Excel file or file-like object
            sheet_name: Specific sheet to load (None = first sheet)
            **kwargs: Additional pandas read_excel arguments

        Returns:
            dict with status, dataframe, and metadata
        """
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name or 0, **kwargs)
            return self._create_load_result(df, "excel", str(file_path))
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def load_google_sheet(self, sheet_id: str, range_name: str = "A:Z") -> dict:
        """
        Load data from a Google Sheet.

        Args:
            sheet_id: Google Sheet ID from URL
            range_name: Cell range to load (default: all columns)

        Returns:
            dict with status, dataframe, and metadata
        """
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            # Get credentials
            creds_path = get_secret("GOOGLE_SERVICE_ACCOUNT_PATH")
            if not creds_path:
                return {"status": "error", "error": "Google credentials not configured"}

            scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
            client = gspread.authorize(creds)

            sheet = client.open_by_key(sheet_id)
            worksheet = sheet.get_worksheet(0)
            data = worksheet.get_all_records()

            df = pd.DataFrame(data)
            return self._create_load_result(df, "google_sheets", sheet_id)

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _create_load_result(
        self, df: pd.DataFrame, source_type: str, source: str
    ) -> dict:
        """Create standardized load result."""
        return {
            "status": "success",
            "dataframe": df,
            "metadata": {
                "source_type": source_type,
                "source": source,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns),
                "loaded_at": datetime.now().isoformat(),
            },
        }

    def preview_data(self, df: pd.DataFrame, n_rows: int = 10) -> dict:
        """
        Get a preview of the dataframe.

        Args:
            df: DataFrame to preview
            n_rows: Number of rows to show

        Returns:
            dict with preview data and basic stats
        """
        return {
            "head": df.head(n_rows).to_dict(orient="records"),
            "shape": {"rows": len(df), "columns": len(df.columns)},
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing": df.isnull().sum().to_dict(),
        }

    # =========================================================================
    # EXPLORATORY DATA ANALYSIS
    # =========================================================================

    def run_eda(self, df: pd.DataFrame) -> dict:
        """
        Run automated Exploratory Data Analysis.

        Args:
            df: DataFrame to analyze

        Returns:
            Comprehensive EDA report dict
        """
        report_id = hashlib.md5(
            f"{len(df)}_{list(df.columns)[:3]}".encode(), usedforsecurity=False
        ).hexdigest()[:12]

        eda_report = {
            "report_id": report_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "overview": self._get_overview(df),
            "data_types": self._analyze_data_types(df),
            "missing_values": self._analyze_missing(df),
            "numeric_summary": self._summarize_numeric(df),
            "categorical_summary": self._summarize_categorical(df),
            "correlations": self._analyze_correlations(df),
        }

        return eda_report

    def _get_overview(self, df: pd.DataFrame) -> dict:
        """Get dataset overview."""
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "total_cells": len(df) * len(df.columns),
            "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
            "duplicates": df.duplicated().sum(),
        }

    def _analyze_data_types(self, df: pd.DataFrame) -> dict:
        """Analyze column data types."""
        type_mapping = {
            "int64": "numeric",
            "int32": "numeric",
            "float64": "numeric",
            "float32": "numeric",
            "object": "text",
            "bool": "boolean",
            "datetime64[ns]": "datetime",
            "category": "categorical",
        }

        columns = {}
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            inferred_type = type_mapping.get(dtype_str, "other")

            # Check if text column might be categorical
            if inferred_type == "text" and df[col].nunique() < len(df) * 0.1:
                inferred_type = "categorical"

            columns[col] = {
                "pandas_dtype": dtype_str,
                "inferred_type": inferred_type,
                "unique_values": df[col].nunique(),
                "sample_values": df[col].dropna().head(3).tolist(),
            }

        return {
            "columns": columns,
            "type_counts": {
                "numeric": sum(
                    1 for c in columns.values() if c["inferred_type"] == "numeric"
                ),
                "text": sum(
                    1 for c in columns.values() if c["inferred_type"] == "text"
                ),
                "categorical": sum(
                    1 for c in columns.values() if c["inferred_type"] == "categorical"
                ),
                "datetime": sum(
                    1 for c in columns.values() if c["inferred_type"] == "datetime"
                ),
            },
        }

    def _analyze_missing(self, df: pd.DataFrame) -> dict:
        """Analyze missing values."""
        missing = df.isnull().sum()
        missing_pct = (missing / len(df) * 100).round(2)

        return {
            "total_missing": int(missing.sum()),
            "total_missing_pct": round(
                missing.sum() / (len(df) * len(df.columns)) * 100, 2
            ),
            "by_column": {
                col: {"count": int(missing[col]), "percentage": float(missing_pct[col])}
                for col in df.columns
                if missing[col] > 0
            },
        }

    def _summarize_numeric(self, df: pd.DataFrame) -> dict:
        """Summarize numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {"columns": {}, "message": "No numeric columns found"}

        summary = {}
        for col in numeric_cols:
            series = df[col].dropna()
            summary[col] = {
                "count": len(series),
                "mean": round(float(series.mean()), 4),
                "std": round(float(series.std()), 4),
                "min": float(series.min()),
                "25%": float(series.quantile(0.25)),
                "50%": float(series.median()),
                "75%": float(series.quantile(0.75)),
                "max": float(series.max()),
                "skewness": round(float(series.skew()), 4) if len(series) > 2 else None,
            }

        return {"columns": summary}

    def _summarize_categorical(self, df: pd.DataFrame) -> dict:
        """Summarize categorical/text columns."""
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(cat_cols) == 0:
            return {"columns": {}, "message": "No categorical columns found"}

        summary = {}
        for col in cat_cols:
            value_counts = df[col].value_counts()
            summary[col] = {
                "unique_values": df[col].nunique(),
                "most_common": value_counts.head(5).to_dict(),
                "least_common": value_counts.tail(3).to_dict()
                if len(value_counts) > 5
                else {},
            }

        return {"columns": summary}

    def _analyze_correlations(self, df: pd.DataFrame) -> dict:
        """Analyze correlations between numeric columns."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return {"matrix": {}, "message": "Need at least 2 numeric columns"}

        corr_matrix = df[numeric_cols].corr()

        # Find strong correlations
        strong_correlations = []
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i + 1 :]:
                corr_value = corr_matrix.loc[col1, col2]
                if abs(corr_value) > 0.5:
                    strong_correlations.append(
                        {
                            "column_1": col1,
                            "column_2": col2,
                            "correlation": round(corr_value, 4),
                            "strength": "strong"
                            if abs(corr_value) > 0.7
                            else "moderate",
                        }
                    )

        return {
            "matrix": corr_matrix.round(4).to_dict(),
            "strong_correlations": strong_correlations,
        }

    # =========================================================================
    # SENTIMENT ANALYSIS
    # =========================================================================

    def _get_sentiment_pipeline(self):
        """Get or create sentiment analysis pipeline."""
        if self._sentiment_pipeline is None and TRANSFORMERS_AVAILABLE:
            try:
                self._sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    top_k=None,
                )
            except Exception:
                # Fall back to default model
                try:
                    self._sentiment_pipeline = pipeline("sentiment-analysis")
                except Exception:
                    self._sentiment_pipeline = None
        return self._sentiment_pipeline

    def analyze_sentiment(
        self, df: pd.DataFrame, text_column: str, batch_size: int = 32
    ) -> dict:
        """
        Analyze sentiment of text data (reviews, comments).

        Args:
            df: DataFrame with text data
            text_column: Name of column containing text
            batch_size: Processing batch size

        Returns:
            dict with sentiment analysis results
        """
        if text_column not in df.columns:
            return {"status": "error", "error": f"Column '{text_column}' not found"}

        texts = df[text_column].dropna().tolist()
        if not texts:
            return {"status": "error", "error": "No text data to analyze"}

        sentiment_pipe = self._get_sentiment_pipeline()

        if sentiment_pipe is None:
            # Fall back to simple rule-based sentiment
            return self._simple_sentiment_analysis(texts)

        try:
            # Process in batches
            results = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                # Truncate long texts
                batch = [t[:512] if len(t) > 512 else t for t in batch]
                batch_results = sentiment_pipe(batch)
                results.extend(batch_results)

            # Aggregate results
            sentiments = []
            for result in results:
                if isinstance(result, list):
                    # Multiple labels returned
                    top_label = max(result, key=lambda x: x["score"])
                else:
                    top_label = result

                sentiments.append(
                    {"label": top_label["label"], "score": round(top_label["score"], 4)}
                )

            # Calculate distribution
            label_counts = {}
            for s in sentiments:
                label = s["label"].upper()
                if "POS" in label or label == "POSITIVE":
                    normalized = "positive"
                elif "NEG" in label or label == "NEGATIVE":
                    normalized = "negative"
                else:
                    normalized = "neutral"

                label_counts[normalized] = label_counts.get(normalized, 0) + 1

            total = len(sentiments)
            distribution = {
                k: {"count": v, "percentage": round(v / total * 100, 2)}
                for k, v in label_counts.items()
            }

            # Calculate average sentiment score
            avg_score = np.mean([s["score"] for s in sentiments])

            return {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "total_analyzed": total,
                "distribution": distribution,
                "average_confidence": round(float(avg_score), 4),
                "detailed_results": sentiments[:100],  # Limit detailed output
                "model": "cardiffnlp/twitter-roberta-base-sentiment",
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _simple_sentiment_analysis(self, texts: list) -> dict:
        """Simple rule-based sentiment analysis fallback."""
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "love",
            "best",
            "perfect",
            "beautiful",
            "friendly",
            "helpful",
            "recommend",
            "delicious",
            "outstanding",
            "superb",
            "lovely",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "horrible",
            "worst",
            "poor",
            "hate",
            "disappointed",
            "disgusting",
            "rude",
            "dirty",
            "slow",
            "cold",
            "overpriced",
            "avoid",
            "never",
        }

        results = []
        for text in texts:
            words = set(text.lower().split())
            pos_count = len(words & positive_words)
            neg_count = len(words & negative_words)

            if pos_count > neg_count:
                label = "positive"
                score = min(0.5 + pos_count * 0.1, 0.95)
            elif neg_count > pos_count:
                label = "negative"
                score = min(0.5 + neg_count * 0.1, 0.95)
            else:
                label = "neutral"
                score = 0.5

            results.append({"label": label, "score": score})

        # Calculate distribution
        label_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for r in results:
            label_counts[r["label"]] += 1

        total = len(results)
        distribution = {
            k: {"count": v, "percentage": round(v / total * 100, 2)}
            for k, v in label_counts.items()
        }

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "total_analyzed": total,
            "distribution": distribution,
            "average_confidence": round(np.mean([r["score"] for r in results]), 4),
            "detailed_results": results[:100],
            "model": "rule-based (fallback)",
        }

    def sentiment_by_category(
        self, df: pd.DataFrame, text_column: str, category_column: str
    ) -> dict:
        """
        Analyze sentiment grouped by category.

        Args:
            df: DataFrame with text and category data
            text_column: Name of text column
            category_column: Name of category column

        Returns:
            dict with sentiment analysis per category
        """
        if text_column not in df.columns or category_column not in df.columns:
            return {"status": "error", "error": "Required columns not found"}

        categories = df[category_column].dropna().unique()
        results = {}

        for cat in categories:
            cat_df = df[df[category_column] == cat]
            sentiment_result = self.analyze_sentiment(cat_df, text_column)

            if sentiment_result.get("status") == "success":
                results[str(cat)] = {
                    "count": len(cat_df),
                    "distribution": sentiment_result.get("distribution", {}),
                    "avg_confidence": sentiment_result.get("average_confidence", 0),
                }

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "category_column": category_column,
            "categories_analyzed": len(results),
            "results_by_category": results,
        }

    # =========================================================================
    # STATISTICAL ANALYSIS
    # =========================================================================

    def descriptive_statistics(self, df: pd.DataFrame, columns: list = None) -> dict:
        """
        Calculate descriptive statistics for specified columns.

        Args:
            df: DataFrame to analyze
            columns: List of columns (None = all numeric)

        Returns:
            dict with descriptive statistics
        """
        if columns:
            cols = [c for c in columns if c in df.columns]
        else:
            cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not cols:
            return {"status": "error", "error": "No numeric columns found"}

        stats_dict = {}
        for col in cols:
            series = df[col].dropna()
            stats_dict[col] = {
                "n": len(series),
                "mean": round(float(series.mean()), 4),
                "median": round(float(series.median()), 4),
                "mode": float(series.mode().iloc[0])
                if len(series.mode()) > 0
                else None,
                "std": round(float(series.std()), 4),
                "variance": round(float(series.var()), 4),
                "min": float(series.min()),
                "max": float(series.max()),
                "range": float(series.max() - series.min()),
                "q1": round(float(series.quantile(0.25)), 4),
                "q3": round(float(series.quantile(0.75)), 4),
                "iqr": round(float(series.quantile(0.75) - series.quantile(0.25)), 4),
                "skewness": round(float(series.skew()), 4) if len(series) > 2 else None,
                "kurtosis": round(float(series.kurtosis()), 4)
                if len(series) > 3
                else None,
            }

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "columns_analyzed": len(cols),
            "statistics": stats_dict,
        }

    def correlation_analysis(
        self, df: pd.DataFrame, columns: list = None, method: str = "pearson"
    ) -> dict:
        """
        Perform correlation analysis.

        Args:
            df: DataFrame to analyze
            columns: Columns to include (None = all numeric)
            method: Correlation method ("pearson", "spearman", "kendall")

        Returns:
            dict with correlation results
        """
        if columns:
            cols = [c for c in columns if c in df.columns]
        else:
            cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if len(cols) < 2:
            return {"status": "error", "error": "Need at least 2 numeric columns"}

        corr_matrix = df[cols].corr(method=method)

        # Find significant correlations
        significant = []
        for i, col1 in enumerate(cols):
            for col2 in cols[i + 1 :]:
                r = corr_matrix.loc[col1, col2]
                if abs(r) > 0.3:  # Threshold for significance
                    significant.append(
                        {
                            "var1": col1,
                            "var2": col2,
                            "r": round(r, 4),
                            "r_squared": round(r**2, 4),
                            "interpretation": self._interpret_correlation(r),
                        }
                    )

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "matrix": corr_matrix.round(4).to_dict(),
            "significant_correlations": sorted(
                significant, key=lambda x: abs(x["r"]), reverse=True
            ),
        }

    def _interpret_correlation(self, r: float) -> str:
        """Interpret correlation coefficient."""
        abs_r = abs(r)
        direction = "positive" if r > 0 else "negative"

        if abs_r < 0.1:
            return "negligible"
        elif abs_r < 0.3:
            return f"weak {direction}"
        elif abs_r < 0.5:
            return f"moderate {direction}"
        elif abs_r < 0.7:
            return f"strong {direction}"
        else:
            return f"very strong {direction}"

    def significance_test(self, df: pd.DataFrame, test_type: str, **kwargs) -> dict:
        """
        Perform statistical significance tests.

        Args:
            df: DataFrame with data
            test_type: Type of test ("t_test", "chi_square", "anova", "mann_whitney")
            **kwargs: Test-specific parameters

        Returns:
            dict with test results
        """
        if not SCIPY_AVAILABLE:
            return {
                "status": "error",
                "error": "scipy not available for statistical tests",
            }

        try:
            if test_type == "t_test":
                return self._t_test(df, **kwargs)
            elif test_type == "chi_square":
                return self._chi_square_test(df, **kwargs)
            elif test_type == "anova":
                return self._anova_test(df, **kwargs)
            elif test_type == "mann_whitney":
                return self._mann_whitney_test(df, **kwargs)
            else:
                return {"status": "error", "error": f"Unknown test type: {test_type}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _t_test(
        self,
        df: pd.DataFrame,
        column: str,
        group_column: str = None,
        value1: float = None,
        paired: bool = False,
    ) -> dict:
        """Independent or one-sample t-test."""
        if group_column and group_column in df.columns:
            # Independent samples t-test
            groups = df[group_column].dropna().unique()
            if len(groups) != 2:
                return {"status": "error", "error": "Need exactly 2 groups for t-test"}

            group1 = df[df[group_column] == groups[0]][column].dropna()
            group2 = df[df[group_column] == groups[1]][column].dropna()

            t_stat, p_value = stats.ttest_ind(group1, group2)

            return {
                "status": "success",
                "test": "independent_samples_t_test",
                "groups": [str(groups[0]), str(groups[1])],
                "n1": len(group1),
                "n2": len(group2),
                "mean1": round(float(group1.mean()), 4),
                "mean2": round(float(group2.mean()), 4),
                "t_statistic": round(float(t_stat), 4),
                "p_value": round(float(p_value), 6),
                "significant": p_value < 0.05,
                "interpretation": self._interpret_p_value(p_value),
            }
        else:
            # One-sample t-test
            sample = df[column].dropna()
            test_value = value1 or 0

            t_stat, p_value = stats.ttest_1samp(sample, test_value)

            return {
                "status": "success",
                "test": "one_sample_t_test",
                "n": len(sample),
                "sample_mean": round(float(sample.mean()), 4),
                "test_value": test_value,
                "t_statistic": round(float(t_stat), 4),
                "p_value": round(float(p_value), 6),
                "significant": p_value < 0.05,
                "interpretation": self._interpret_p_value(p_value),
            }

    def _chi_square_test(self, df: pd.DataFrame, column1: str, column2: str) -> dict:
        """Chi-square test of independence."""
        contingency = pd.crosstab(df[column1], df[column2])
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        return {
            "status": "success",
            "test": "chi_square_independence",
            "variables": [column1, column2],
            "chi_square": round(float(chi2), 4),
            "p_value": round(float(p_value), 6),
            "degrees_of_freedom": int(dof),
            "significant": p_value < 0.05,
            "interpretation": self._interpret_p_value(p_value),
            "contingency_table": contingency.to_dict(),
        }

    def _anova_test(
        self, df: pd.DataFrame, value_column: str, group_column: str
    ) -> dict:
        """One-way ANOVA test."""
        groups = df[group_column].dropna().unique()
        group_data = [df[df[group_column] == g][value_column].dropna() for g in groups]

        f_stat, p_value = stats.f_oneway(*group_data)

        return {
            "status": "success",
            "test": "one_way_anova",
            "groups": [str(g) for g in groups],
            "n_groups": len(groups),
            "f_statistic": round(float(f_stat), 4),
            "p_value": round(float(p_value), 6),
            "significant": p_value < 0.05,
            "interpretation": self._interpret_p_value(p_value),
            "group_means": {
                str(g): round(float(df[df[group_column] == g][value_column].mean()), 4)
                for g in groups
            },
        }

    def _mann_whitney_test(
        self, df: pd.DataFrame, column: str, group_column: str
    ) -> dict:
        """Mann-Whitney U test (non-parametric alternative to t-test)."""
        groups = df[group_column].dropna().unique()
        if len(groups) != 2:
            return {"status": "error", "error": "Need exactly 2 groups"}

        group1 = df[df[group_column] == groups[0]][column].dropna()
        group2 = df[df[group_column] == groups[1]][column].dropna()

        u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative="two-sided")

        return {
            "status": "success",
            "test": "mann_whitney_u",
            "groups": [str(groups[0]), str(groups[1])],
            "n1": len(group1),
            "n2": len(group2),
            "u_statistic": round(float(u_stat), 4),
            "p_value": round(float(p_value), 6),
            "significant": p_value < 0.05,
            "interpretation": self._interpret_p_value(p_value),
        }

    def _interpret_p_value(self, p: float) -> str:
        """Interpret p-value for thesis writing."""
        if p < 0.001:
            return "highly significant (p < 0.001)"
        elif p < 0.01:
            return "very significant (p < 0.01)"
        elif p < 0.05:
            return "significant (p < 0.05)"
        elif p < 0.1:
            return "marginally significant (p < 0.1)"
        else:
            return "not significant (p >= 0.1)"

    # =========================================================================
    # VISUALIZATION
    # =========================================================================

    def generate_chart(self, df: pd.DataFrame, chart_type: str, **kwargs) -> dict:
        """
        Generate a visualization chart.

        Args:
            df: DataFrame with data
            chart_type: Type of chart ("histogram", "scatter", "bar", "box", "heatmap")
            **kwargs: Chart-specific parameters (x, y, color, title, etc.)

        Returns:
            dict with chart figure or error
        """
        if not PLOTLY_AVAILABLE:
            return {
                "status": "error",
                "error": "plotly not available for visualization",
            }

        try:
            if chart_type == "histogram":
                fig = px.histogram(df, **kwargs)
            elif chart_type == "scatter":
                fig = px.scatter(df, **kwargs)
            elif chart_type == "bar":
                fig = px.bar(df, **kwargs)
            elif chart_type == "box":
                fig = px.box(df, **kwargs)
            elif chart_type == "heatmap":
                # For correlation heatmap
                x = kwargs.get("x")
                y = kwargs.get("y")
                if x and y:
                    corr = df[[x, y]].corr()
                else:
                    corr = df.select_dtypes(include=[np.number]).corr()

                fig = go.Figure(
                    data=go.Heatmap(
                        z=corr.values,
                        x=corr.columns,
                        y=corr.index,
                        colorscale="RdBu_r",
                        zmin=-1,
                        zmax=1,
                    )
                )
                fig.update_layout(title=kwargs.get("title", "Correlation Heatmap"))
            elif chart_type == "pie":
                fig = px.pie(df, **kwargs)
            elif chart_type == "line":
                fig = px.line(df, **kwargs)
            else:
                return {"status": "error", "error": f"Unknown chart type: {chart_type}"}

            # Apply default styling
            fig.update_layout(
                template="plotly_white", font=dict(family="Inter, sans-serif")
            )

            return {
                "status": "success",
                "chart_type": chart_type,
                "figure": fig,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def create_dashboard_figures(self, df: pd.DataFrame) -> dict:
        """
        Auto-generate appropriate visualizations based on data types.

        Args:
            df: DataFrame to visualize

        Returns:
            dict with multiple chart figures
        """
        if not PLOTLY_AVAILABLE:
            return {"status": "error", "error": "plotly not available"}

        figures = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        # Histograms for numeric columns
        for col in numeric_cols[:3]:
            result = self.generate_chart(
                df, "histogram", x=col, title=f"Distribution of {col}"
            )
            if result.get("status") == "success":
                figures.append(
                    {"type": "histogram", "column": col, "figure": result["figure"]}
                )

        # Bar charts for categorical columns
        for col in categorical_cols[:2]:
            if df[col].nunique() <= 20:
                counts = df[col].value_counts().reset_index()
                counts.columns = [col, "count"]
                result = self.generate_chart(
                    counts, "bar", x=col, y="count", title=f"Frequency of {col}"
                )
                if result.get("status") == "success":
                    figures.append(
                        {"type": "bar", "column": col, "figure": result["figure"]}
                    )

        # Correlation heatmap if enough numeric columns
        if len(numeric_cols) >= 2:
            result = self.generate_chart(
                df[numeric_cols], "heatmap", title="Correlation Matrix"
            )
            if result.get("status") == "success":
                figures.append(
                    {
                        "type": "heatmap",
                        "column": "correlations",
                        "figure": result["figure"],
                    }
                )

        return {
            "status": "success",
            "figures_generated": len(figures),
            "figures": figures,
        }

    # =========================================================================
    # NARRATIVE EXPORT
    # =========================================================================

    def generate_analysis_narrative(
        self, analysis_results: dict, section_type: str = "findings"
    ) -> dict:
        """
        Generate thesis-ready narrative from analysis results.

        Uses LLM to convert statistical results to academic prose.

        Args:
            analysis_results: Results from EDA, sentiment, or statistical analysis
            section_type: Type of thesis section ("findings", "discussion", "methodology")

        Returns:
            dict with generated narrative text
        """
        if not self._llm_available:
            return {"status": "error", "error": "LLM gateway not available"}

        # Prepare analysis summary for LLM
        summary = json.dumps(analysis_results, indent=2, default=str)[:4000]

        prompt = f"""You are a PhD research assistant helping write a thesis.

Convert the following statistical analysis results into academic prose suitable for a {section_type} section.

Requirements:
- Use formal academic language
- Report statistics correctly (e.g., "t(df) = X.XX, p < .05")
- Interpret findings in context
- Use hedging language appropriately (e.g., "suggests", "indicates")
- Keep the narrative concise but thorough

Analysis Results:
{summary}

Write 2-3 paragraphs of thesis-ready text:"""

        try:
            log_ai_usage(
                action_type="narrative_generation",
                data_source="data_lab_analysis",
                prompt=prompt[:200],
                was_scrubbed=False,
            )

            result = self._llm_gateway.generate_content(
                prompt=prompt, task_type="drafting"
            )

            return {
                "status": "success",
                "narrative": result.get("content", ""),
                "section_type": section_type,
                "model_used": result.get("model_used", "unknown"),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}


# =============================================================================
# STANDALONE FUNCTIONS
# =============================================================================


def load_data(source: str, source_type: str = "csv", **kwargs) -> dict:
    """
    Standalone function to load data.

    Usage:
        from core.data_lab import load_data
        result = load_data("data.csv", source_type="csv")
    """
    lab = DataLab()
    if source_type == "csv":
        return lab.load_csv(source, **kwargs)
    elif source_type == "excel":
        return lab.load_excel(source, **kwargs)
    elif source_type == "google_sheets":
        return lab.load_google_sheet(source, **kwargs)
    else:
        return {"status": "error", "error": f"Unknown source type: {source_type}"}


def run_full_analysis(
    df: pd.DataFrame, include_sentiment: bool = False, text_column: str = None
) -> dict:
    """
    Run comprehensive analysis on a DataFrame.

    Usage:
        from core.data_lab import run_full_analysis
        result = run_full_analysis(df, include_sentiment=True, text_column="review")
    """
    lab = DataLab()

    results = {
        "eda": lab.run_eda(df),
        "descriptive_stats": lab.descriptive_statistics(df),
        "correlations": lab.correlation_analysis(df),
    }

    if include_sentiment and text_column:
        results["sentiment"] = lab.analyze_sentiment(df, text_column)

    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHDx Data Lab - Data Science Module")
    print("=" * 60)

    lab = DataLab()

    # Check available features
    print("\nAvailable Features:")
    print(f"  - scipy (statistics): {SCIPY_AVAILABLE}")
    print(f"  - plotly (visualization): {PLOTLY_AVAILABLE}")
    print(f"  - transformers (sentiment): {TRANSFORMERS_AVAILABLE}")

    # Demo with sample data
    print("\nDemo with sample data:")
    sample_data = {
        "rating": [4, 5, 3, 2, 5, 4, 3, 4, 5, 2],
        "review": [
            "Great experience, loved it!",
            "Excellent service, highly recommend",
            "Average, nothing special",
            "Disappointing, not worth it",
            "Amazing, will come back",
            "Good overall, minor issues",
            "Okay but overpriced",
            "Very nice atmosphere",
            "Perfect in every way",
            "Terrible service, avoid",
        ],
        "category": [
            "Hotel",
            "Restaurant",
            "Hotel",
            "Restaurant",
            "Hotel",
            "Restaurant",
            "Hotel",
            "Restaurant",
            "Hotel",
            "Restaurant",
        ],
    }

    df = pd.DataFrame(sample_data)
    print(f"\nSample data: {len(df)} rows, {len(df.columns)} columns")

    # Run EDA
    eda = lab.run_eda(df)
    print(f"\nEDA Report ID: {eda['report_id']}")
    print(f"  - Rows: {eda['overview']['rows']}")
    print(f"  - Numeric columns: {eda['data_types']['type_counts']['numeric']}")

    # Run sentiment analysis
    sentiment = lab.analyze_sentiment(df, "review")
    if sentiment.get("status") == "success":
        print("\nSentiment Analysis:")
        for label, data in sentiment.get("distribution", {}).items():
            print(f"  - {label}: {data['percentage']}%")

    print("\n" + "=" * 60)
