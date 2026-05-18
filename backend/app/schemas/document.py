from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    approved = "Approved"
    needs_review = "Needs Review"
    error = "Error"


class DocumentInput(BaseModel):
    text: str | None = None
    filename: str | None = None
    source: str = "unknown"


class ExtractedFields(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    total_amount: float | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class LLMOutput(BaseModel):
    summary: str
    classification: str
    confidence: float
    key_points: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class DocumentRecord(BaseModel):
    id: str | None = None
    created_at: datetime
    source: str
    text: str
    extracted: ExtractedFields
    validation: ValidationResult
    llm: LLMOutput
    workflow_status: WorkflowStatus
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    document: DocumentRecord
