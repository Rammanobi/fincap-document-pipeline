from .models import AuditEntry
from .config import settings

def build_audit(extraction: dict) -> list[AuditEntry]:
    audit_trail = []
    
    doc_type = extraction.get("document_type", {})
    audit_trail.append(AuditEntry(
        field_name="document_type",
        selected_value=doc_type.get("value"),
        source_page=doc_type.get("source_page"),
        confidence=doc_type.get("confidence", "high"),
        decision_reason=doc_type.get("decision_reason") or "Direct extraction, no conflict",
        model_used=settings.vision_model,
        prompt_version=settings.prompt_version
    ))
    
    fields = extraction.get("fields", {})
    for field_name, f_data in fields.items():
        audit_trail.append(AuditEntry(
            field_name=field_name,
            selected_value=f_data.get("value"),
            source_page=f_data.get("source_page"),
            confidence=f_data.get("confidence", "high"),
            decision_reason=f_data.get("decision_reason") or "Direct extraction, no conflict",
            model_used=settings.vision_model,
            prompt_version=settings.prompt_version
        ))
        
    return audit_trail
