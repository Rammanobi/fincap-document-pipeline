from .models import ReviewSignal

def build_review(extraction: dict, reconciliations: list) -> dict:
    review_signals = []
    fields = extraction.get("fields", {})
    
    critical_fields = {
        "government_fees", "loan_amount", "appraised_value", 
        "total_closing_costs", "total_other_costs", "loan_number", "property_address"
    }
    
    for field_name, f_data in fields.items():
        reasons = []
        if f_data.get("value") is None:
            reasons.append("SELECTED_VALUE_MISSING")
        if f_data.get("requires_review"):
            reasons.append("FIELD_FLAGGED_BY_EXTRACTOR")
        if f_data.get("confidence") == "low":
            reasons.append("LOW_CONFIDENCE")
        if f_data.get("correction_applied"):
            reasons.append("CORRECTION_APPLIED_VERIFY")
            
        if reasons:
            priority = "medium"
            if field_name in critical_fields and ("SELECTED_VALUE_MISSING" in reasons or "FIELD_FLAGGED_BY_EXTRACTOR" in reasons or "RECONCILIATION_DISCREPANCY" in reasons):
                priority = "critical"
            elif field_name in critical_fields and "LOW_CONFIDENCE" in reasons:
                priority = "high"
                
            review_signals.append(ReviewSignal(
                field_name=field_name,
                reasons=reasons,
                priority=priority,
                source_page=f_data.get("source_page")
            ))
            
    for rec in reconciliations:
        if rec.status == "discrepancy":
            target_field = rec.formula.split("=")[-1].strip() if "=" in rec.formula else "unknown"
            review_signals.append(ReviewSignal(
                field_name=target_field,
                reasons=["RECONCILIATION_DISCREPANCY"],
                priority="critical",
                source_page=None
            ))
            
    requires_review = len(review_signals) > 0
    priority = "low"
    if requires_review:
        priorities = [sig.priority for sig in review_signals]
        if "critical" in priorities:
            priority = "critical"
        elif "high" in priorities:
            priority = "high"
        else:
            priority = "medium"
            
    return {
        "requires_review": requires_review,
        "priority": priority,
        "review_signals": review_signals
    }
