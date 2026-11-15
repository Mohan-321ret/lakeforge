"""Pydantic models for Lakeforge API."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    """Model for creating a new data source connection."""

    name: str = Field(..., description="Human-readable name for the source")
    uri: str = Field(..., description="Connection URI")
    description: Optional[str] = Field(None, description="Optional description")
    tags: List[str] = Field(default_factory=list, description="Optional tags")


class SourceResponse(BaseModel):
    """Model for data source response."""

    id: str
    name: str
    uri: str
    source_type: str
    description: Optional[str]
    tags: List[str]
    created_at: str
    last_accessed: Optional[str]
    row_count: Optional[int]
    table_count: Optional[int]


class InspectionRequest(BaseModel):
    """Model for inspection request."""

    source_id: str = Field(..., description="ID of the source to inspect")
    include_profile: bool = Field(True, description="Include statistical profiling")
    include_pii_detection: bool = Field(True, description="Detect PII columns")
    sample_size: int = Field(100, description="Number of sample rows")
    timeout_seconds: int = Field(30, description="Query timeout")


class SchemaInfo(BaseModel):
    """Model for table schema information."""

    table_name: str
    column_count: int
    row_count: Optional[int]
    columns: Dict[str, str]  # column_name -> data_type


class TableProfile(BaseModel):
    """Model for table profile statistics."""

    table_name: str
    row_count: int
    column_profiles: Dict[str, Dict[str, Any]]  # column_name -> stats


class QARequest(BaseModel):
    """Model for Q&A request."""

    source_id: str = Field(..., description="ID of the source")
    question: str = Field(..., description="Question to ask")
    session_id: Optional[str] = Field(None, description="Session ID for context")


class QAResponse(BaseModel):
    """Model for Q&A response."""

    question: str
    generated_sql: Optional[str]
    execution_status: str  # "success", "error"
    results: Optional[List[Dict[str, Any]]]
    error_message: Optional[str]
    execution_time_ms: float
    session_id: Optional[str] = None
    attempts: int = 1
    self_corrected: bool = False
    corrections: Optional[List[str]] = None


class ReportCreate(BaseModel):
    """Model for creating a report."""

    source_id: str
    title: str
    description: Optional[str] = None
    include_visualizations: bool = True


class ReportResponse(BaseModel):
    """Model for report response."""

    id: str
    source_id: str
    title: str
    description: Optional[str]
    created_at: str
    format: str  # "html", "pdf", "json"
    download_url: str
