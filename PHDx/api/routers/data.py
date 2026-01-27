"""
Data Lab API Router.

Endpoints for data analysis:
- File upload (CSV, Excel)
- Exploratory data analysis
- Sentiment analysis
- Statistical tests
- Visualization generation
- Narrative export
"""

import sys
import uuid
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

# Ensure core is importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter()

# In-memory dataset storage (would use Redis/DB in production)
_datasets: Dict[str, Dict[str, Any]] = {}


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class DatasetInfo(BaseModel):
    """Dataset information."""
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    column_types: Dict[str, str]
    uploaded_at: str


class UploadResponse(BaseModel):
    """File upload response."""
    success: bool
    dataset_id: str = ""
    info: Optional[DatasetInfo] = None
    preview: List[Dict[str, Any]] = []
    error: Optional[str] = None


class EDARequest(BaseModel):
    """Request for EDA."""
    dataset_id: str


class NumericSummary(BaseModel):
    """Summary statistics for numeric column."""
    count: int = 0
    mean: float = 0
    std: float = 0
    min: float = 0
    q25: float = 0
    median: float = 0
    q75: float = 0
    max: float = 0


class CategoricalSummary(BaseModel):
    """Summary for categorical column."""
    unique: int = 0
    top_values: Dict[str, int] = {}


class EDAResponse(BaseModel):
    """EDA results."""
    success: bool
    overview: Dict[str, Any] = {}
    data_types: Dict[str, str] = {}
    missing_values: Dict[str, int] = {}
    numeric_summary: Dict[str, NumericSummary] = {}
    categorical_summary: Dict[str, CategoricalSummary] = {}
    correlations: Dict[str, Dict[str, float]] = {}
    error: Optional[str] = None


class SentimentRequest(BaseModel):
    """Request for sentiment analysis."""
    dataset_id: str
    text_column: str


class SentimentResponse(BaseModel):
    """Sentiment analysis results."""
    success: bool
    distribution: Dict[str, float] = {}
    average_score: float = 0
    total_analyzed: int = 0
    sample_results: List[Dict[str, Any]] = []
    error: Optional[str] = None


class StatisticalTestRequest(BaseModel):
    """Request for statistical test."""
    dataset_id: str
    test_type: str = Field(..., description="t_test, chi_square, anova, mann_whitney, correlation")
    column1: Optional[str] = None
    column2: Optional[str] = None
    value_column: Optional[str] = None
    group_column: Optional[str] = None


class StatisticalTestResponse(BaseModel):
    """Statistical test results."""
    success: bool
    test_name: str = ""
    statistic: float = 0
    p_value: float = 1
    significant: bool = False
    interpretation: str = ""
    details: Dict[str, Any] = {}
    error: Optional[str] = None


class VisualizationRequest(BaseModel):
    """Request for visualization."""
    dataset_id: str
    chart_type: str = Field(..., description="histogram, scatter, bar, box, line, heatmap, pie")
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    color_column: Optional[str] = None
    title: Optional[str] = None


class VisualizationResponse(BaseModel):
    """Visualization response."""
    success: bool
    chart_type: str = ""
    plotly_json: Dict[str, Any] = {}
    error: Optional[str] = None


class NarrativeRequest(BaseModel):
    """Request for narrative generation."""
    analysis_results: Dict[str, Any]
    chapter_context: str = "findings"
    focus: str = ""


class NarrativeResponse(BaseModel):
    """Narrative generation response."""
    success: bool
    narrative: str = ""
    word_count: int = 0
    error: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_dataset(dataset_id: str):
    """Get dataset by ID."""
    if dataset_id not in _datasets:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    return _datasets[dataset_id]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
):
    """Upload a CSV or Excel file."""
    try:
        import pandas as pd

        # Generate dataset ID
        dataset_id = str(uuid.uuid4())[:8]

        # Read file
        content = await file.read()
        filename = file.filename or "uploaded_file"

        if filename.endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(BytesIO(content))
        else:
            return UploadResponse(
                success=False,
                error="Unsupported file type. Please upload CSV or Excel."
            )

        # Store dataset
        _datasets[dataset_id] = {
            "df": df,
            "filename": filename,
            "uploaded_at": datetime.now().isoformat()
        }

        # Create info
        info = DatasetInfo(
            dataset_id=dataset_id,
            filename=filename,
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            column_types={col: str(dtype) for col, dtype in df.dtypes.items()},
            uploaded_at=datetime.now().isoformat()
        )

        # Create preview
        preview = df.head(10).to_dict(orient="records")

        return UploadResponse(
            success=True,
            dataset_id=dataset_id,
            info=info,
            preview=preview
        )

    except Exception as e:
        return UploadResponse(success=False, error=str(e))


@router.post("/upload/url", response_model=UploadResponse)
async def upload_from_url(
    url: str = Form(...),
):
    """Upload from a Google Sheets URL."""
    try:
        import pandas as pd

        dataset_id = str(uuid.uuid4())[:8]

        # Convert Google Sheets URL to CSV export
        if "docs.google.com/spreadsheets" in url:
            if "/edit" in url:
                sheet_id = url.split("/d/")[1].split("/")[0]
            else:
                sheet_id = url.split("/d/")[1].split("/")[0] if "/d/" in url else url
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            csv_url = url

        df = pd.read_csv(csv_url)

        _datasets[dataset_id] = {
            "df": df,
            "filename": "Google Sheet",
            "uploaded_at": datetime.now().isoformat()
        }

        info = DatasetInfo(
            dataset_id=dataset_id,
            filename="Google Sheet",
            rows=len(df),
            columns=len(df.columns),
            column_names=df.columns.tolist(),
            column_types={col: str(dtype) for col, dtype in df.dtypes.items()},
            uploaded_at=datetime.now().isoformat()
        )

        preview = df.head(10).to_dict(orient="records")

        return UploadResponse(
            success=True,
            dataset_id=dataset_id,
            info=info,
            preview=preview
        )

    except Exception as e:
        return UploadResponse(success=False, error=str(e))


@router.get("/datasets")
async def list_datasets():
    """List all uploaded datasets."""
    datasets = []
    for dataset_id, data in _datasets.items():
        df = data["df"]
        datasets.append({
            "dataset_id": dataset_id,
            "filename": data["filename"],
            "rows": len(df),
            "columns": len(df.columns),
            "uploaded_at": data["uploaded_at"]
        })
    return {"datasets": datasets}


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    if dataset_id in _datasets:
        del _datasets[dataset_id]
        return {"success": True, "message": f"Dataset {dataset_id} deleted"}
    raise HTTPException(status_code=404, detail="Dataset not found")


@router.post("/eda/{dataset_id}", response_model=EDAResponse)
async def run_eda(dataset_id: str):
    """Run exploratory data analysis."""
    try:
        from core.data_lab import DataLab

        data = _get_dataset(dataset_id)
        df = data["df"]

        lab = DataLab()
        result = lab.run_eda(df)

        if result.get("error"):
            return EDAResponse(success=False, error=result["error"])

        # Convert numeric summary
        numeric_summary = {}
        for col, stats in result.get("numeric_summary", {}).items():
            numeric_summary[col] = NumericSummary(
                count=int(stats.get("count", 0)),
                mean=float(stats.get("mean", 0)),
                std=float(stats.get("std", 0)),
                min=float(stats.get("min", 0)),
                q25=float(stats.get("25%", 0)),
                median=float(stats.get("50%", 0)),
                q75=float(stats.get("75%", 0)),
                max=float(stats.get("max", 0))
            )

        # Convert categorical summary
        categorical_summary = {}
        for col, info in result.get("categorical_summary", {}).items():
            categorical_summary[col] = CategoricalSummary(
                unique=info.get("unique", 0),
                top_values=info.get("top_values", {})
            )

        return EDAResponse(
            success=True,
            overview=result.get("overview", {}),
            data_types=result.get("data_types", {}),
            missing_values=result.get("missing_values", {}),
            numeric_summary=numeric_summary,
            categorical_summary=categorical_summary,
            correlations=result.get("correlations", {})
        )

    except ImportError:
        # Fallback without DataLab
        data = _get_dataset(dataset_id)
        df = data["df"]

        return EDAResponse(
            success=True,
            overview={
                "rows": len(df),
                "columns": len(df.columns),
                "missing_cells": int(df.isna().sum().sum())
            },
            data_types={col: str(dtype) for col, dtype in df.dtypes.items()},
            missing_values={col: int(df[col].isna().sum()) for col in df.columns}
        )
    except Exception as e:
        return EDAResponse(success=False, error=str(e))


@router.post("/sentiment/{dataset_id}", response_model=SentimentResponse)
async def analyze_sentiment(dataset_id: str, request: SentimentRequest):
    """Run sentiment analysis on a text column."""
    try:
        from core.data_lab import DataLab

        data = _get_dataset(dataset_id)
        df = data["df"]

        if request.text_column not in df.columns:
            return SentimentResponse(
                success=False,
                error=f"Column '{request.text_column}' not found in dataset"
            )

        lab = DataLab()
        result = lab.analyze_sentiment(df, request.text_column)

        if result.get("error"):
            return SentimentResponse(success=False, error=result["error"])

        # Get sample results
        result_df = result.get("dataframe")
        sample_results = []
        if result_df is not None:
            sample_cols = [request.text_column]
            if "sentiment_label" in result_df.columns:
                sample_cols.append("sentiment_label")
            if "sentiment_score" in result_df.columns:
                sample_cols.append("sentiment_score")
            sample_results = result_df[sample_cols].head(10).to_dict(orient="records")

        return SentimentResponse(
            success=True,
            distribution=result.get("distribution", {}),
            average_score=result.get("average_score", 0),
            total_analyzed=result.get("total_analyzed", 0),
            sample_results=sample_results
        )

    except ImportError:
        return SentimentResponse(
            success=False,
            error="Sentiment analysis requires transformers library"
        )
    except Exception as e:
        return SentimentResponse(success=False, error=str(e))


@router.post("/statistics/{dataset_id}", response_model=StatisticalTestResponse)
async def run_statistical_test(dataset_id: str, request: StatisticalTestRequest):
    """Run a statistical test."""
    try:
        from core.data_lab import DataLab

        data = _get_dataset(dataset_id)
        df = data["df"]

        lab = DataLab()

        if request.test_type == "correlation":
            result = lab.correlation_analysis(
                df,
                request.column1,
                request.column2
            )
        else:
            result = lab.significance_test(
                df,
                request.test_type,
                value_column=request.value_column,
                group_column=request.group_column,
                column1=request.column1,
                column2=request.column2
            )

        if result.get("error"):
            return StatisticalTestResponse(success=False, error=result["error"])

        return StatisticalTestResponse(
            success=True,
            test_name=result.get("test_name", request.test_type),
            statistic=result.get("statistic", result.get("correlation", 0)),
            p_value=result.get("p_value", 1),
            significant=result.get("p_value", 1) < 0.05,
            interpretation=result.get("interpretation", ""),
            details=result
        )

    except ImportError:
        return StatisticalTestResponse(
            success=False,
            error="Statistical tests require scipy library"
        )
    except Exception as e:
        return StatisticalTestResponse(success=False, error=str(e))


@router.post("/visualize/{dataset_id}", response_model=VisualizationResponse)
async def create_visualization(dataset_id: str, request: VisualizationRequest):
    """Create a visualization."""
    try:
        from core.data_lab import DataLab

        data = _get_dataset(dataset_id)
        df = data["df"]

        lab = DataLab()
        fig = lab.create_visualization(
            df,
            request.chart_type,
            x_column=request.x_column,
            y_column=request.y_column,
            color_column=request.color_column,
            title=request.title
        )

        if fig is None:
            return VisualizationResponse(
                success=False,
                error="Failed to create visualization"
            )

        # Convert to JSON
        plotly_json = json.loads(fig.to_json())

        return VisualizationResponse(
            success=True,
            chart_type=request.chart_type,
            plotly_json=plotly_json
        )

    except ImportError:
        return VisualizationResponse(
            success=False,
            error="Visualization requires plotly library"
        )
    except Exception as e:
        return VisualizationResponse(success=False, error=str(e))


@router.post("/narrative/generate", response_model=NarrativeResponse)
async def generate_narrative(request: NarrativeRequest):
    """Generate thesis-ready narrative from analysis results."""
    try:
        from core.data_lab import DataLab

        lab = DataLab()
        result = lab.generate_narrative(
            request.analysis_results,
            request.chapter_context,
            request.focus
        )

        if result.get("error"):
            return NarrativeResponse(success=False, error=result["error"])

        narrative = result.get("narrative", "")
        return NarrativeResponse(
            success=True,
            narrative=narrative,
            word_count=len(narrative.split())
        )

    except Exception as e:
        return NarrativeResponse(success=False, error=str(e))


@router.get("/preview/{dataset_id}")
async def get_preview(dataset_id: str, rows: int = 20):
    """Get a preview of the dataset."""
    data = _get_dataset(dataset_id)
    df = data["df"]

    return {
        "preview": df.head(rows).to_dict(orient="records"),
        "total_rows": len(df),
        "columns": df.columns.tolist()
    }


@router.get("/columns/{dataset_id}")
async def get_columns(dataset_id: str):
    """Get column information for a dataset."""
    data = _get_dataset(dataset_id)
    df = data["df"]

    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        is_numeric = dtype in ["int64", "float64", "int32", "float32"]
        is_text = dtype == "object"

        columns.append({
            "name": col,
            "dtype": dtype,
            "is_numeric": is_numeric,
            "is_text": is_text,
            "unique_count": int(df[col].nunique()),
            "missing_count": int(df[col].isna().sum())
        })

    return {"columns": columns}
