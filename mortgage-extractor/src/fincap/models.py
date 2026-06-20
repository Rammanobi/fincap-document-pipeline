from pydantic import BaseModel
from typing import Any, Optional, Dict, List

class PageText(BaseModel):
    page_number: int
    text: str

class DocumentText(BaseModel):
    filename: str
    page_count: int
    pages: list[PageText]

class ValidationResult(BaseModel):
    filename: str
    page_count: int
    file_size_bytes: int

class FieldResult(BaseModel):
    value: Any
    original_value: Optional[float] = None
    source_page: int
    confidence: str
    confidence_reason: Optional[str] = None
    correction_applied: bool = False
    decision_reason: Optional[str] = None
    requires_review: bool = False

class ReconciliationFormula(BaseModel):
    description: str
    formula: str
    fields_involved: List[str]

class DegradedRegion(BaseModel):
    page: int
    raw_text: str
    best_guess: str
    reason: str

class ExtractionResult(BaseModel):
    document_type: FieldResult
    fields: Dict[str, FieldResult]
    reconciliation_formulas: List[ReconciliationFormula]
    degraded_regions: List[DegradedRegion]

class ReconciliationResult(BaseModel):
    description: str
    formula: str
    as_stated: Optional[float] = None
    computed: Optional[float] = None
    difference: Optional[float] = None
    status: str
    note: Optional[str] = None

class ReviewSignal(BaseModel):
    field_name: str
    reasons: List[str]
    priority: str
    source_page: Optional[int] = None

class AuditEntry(BaseModel):
    field_name: str
    selected_value: Any
    source_page: Optional[int] = None
    confidence: str
    decision_reason: Optional[str] = None
    model_used: str
    prompt_version: str

class ReviewBlock(BaseModel):
    requires_review: bool
    priority: str
    review_signals: List[ReviewSignal]

class ProcessingBlock(BaseModel):
    model_used: str
    prompt_version: str
    phase_count: int

class FinalAssignment(BaseModel):
    document_id: str
    document_type: FieldResult
    status: str
    fields: Dict[str, FieldResult]
    reconciliations: List[ReconciliationResult]
    degraded_regions: List[DegradedRegion]
    review: ReviewBlock
    audit_trail: List[AuditEntry]
    processing: ProcessingBlock
