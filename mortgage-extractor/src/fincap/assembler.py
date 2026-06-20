from .models import FinalAssignment

def assemble(document_id: str, extraction: dict, reconciliations: list, review: dict, audit: list) -> dict:
    fields = extraction.get("fields", {})
    
    for rec in reconciliations:
        if rec.status == "discrepancy":
            target_field = rec.formula.split("=")[-1].strip() if "=" in rec.formula else None
            if target_field and target_field in fields:
                fields[target_field]["requires_review"] = True
                fields[target_field]["confidence"] = "low"
                
    status = "requires_review" if review.get("requires_review") else "clean"
    
    final_assignment = FinalAssignment(
        document_id=document_id,
        document_type=extraction.get("document_type", {}),
        status=status,
        fields=fields,
        reconciliations=reconciliations,
        degraded_regions=extraction.get("degraded_regions", []),
        review=review,
        audit_trail=audit,
        processing={
            "model_used": "gpt-4o",
            "prompt_version": "v1.0",
            "phase_count": 3
        }
    )
    
    return final_assignment.model_dump()
