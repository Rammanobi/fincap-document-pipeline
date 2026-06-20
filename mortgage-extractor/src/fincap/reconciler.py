from decimal import Decimal, InvalidOperation
from .models import ReconciliationResult

def reconcile(extraction: dict) -> list[ReconciliationResult]:
    reconciliations = []
    formulas = extraction.get("reconciliation_formulas", [])
    fields = extraction.get("fields", {})
    
    for f in formulas:
        description = f.get("description", "")
        formula = f.get("formula", "")
        fields_involved = f.get("fields_involved", [])
        
        if not fields_involved or len(fields_involved) < 2:
            continue
            
        inputs = fields_involved[:-1]
        target = fields_involved[-1]
        
        # Pull values
        missing_fields = []
        input_decimals = []
        target_decimal = None
        
        for inp in inputs:
            val = fields.get(inp, {}).get("value")
            if val is None:
                missing_fields.append(inp)
            else:
                try:
                    input_decimals.append(Decimal(str(val)))
                except (InvalidOperation, ValueError, TypeError):
                    missing_fields.append(inp)
                    
        target_val = fields.get(target, {}).get("value")
        if target_val is None:
            missing_fields.append(target)
        else:
            try:
                target_decimal = Decimal(str(target_val))
            except (InvalidOperation, ValueError, TypeError):
                missing_fields.append(target)
                
        if missing_fields:
            reconciliations.append(ReconciliationResult(
                description=description,
                formula=formula,
                status="skipped",
                note=f"Missing or invalid field(s): {', '.join(missing_fields)}"
            ))
            continue
            
        is_ratio = "/" in formula
        is_sum = "+" in formula
        
        computed = Decimal(0)
        if is_sum:
            computed = sum(input_decimals)
        elif is_ratio and len(input_decimals) == 2:
            if input_decimals[1] == Decimal(0):
                computed = Decimal(0)
            else:
                computed = (input_decimals[0] / input_decimals[1]) * Decimal(100)
                computed = computed.quantize(Decimal("0.01"))
        else:
            # Fallback if neither plus nor slash
            computed = sum(input_decimals)
            
        difference = target_decimal - computed
        
        if abs(difference) <= Decimal("0.01"):
            status = "reconciled"
            note = None
        else:
            status = "discrepancy"
            note = f"Stated total {target_decimal} does not match computed {computed} — subtotal not updated after a corrected input value or calculation error"
            
        reconciliations.append(ReconciliationResult(
            description=description,
            formula=formula,
            as_stated=float(target_decimal),
            computed=float(computed),
            difference=float(difference),
            status=status,
            note=note
        ))
        
    return reconciliations
