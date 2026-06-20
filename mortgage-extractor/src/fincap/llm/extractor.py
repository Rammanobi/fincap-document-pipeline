import json
from .client import get_client, retry_with_backoff
from ..config import settings

def extract_fields(page_text: str) -> dict:
    """
    Sends the full text to gpt-4o for structured extraction.
    """
    client = get_client()
    
    system_prompt = (
        "You are an expert mortgage document extraction system. You receive the full text of a mortgage document with [PAGE N] markers. Extract all fields and return ONE valid JSON object. No markdown, no commentary, only JSON.\n\n"
        "EXTRACTION RULES:\n\n"
        "1. Extract every field present in the document. Common fields include: document_type, loan_number, borrower_name, co_borrower, property_address, loan_amount, loan_purpose, interest_rate, loan_term, origination_charges, services_not_shopped, services_shopped, total_loan_costs, government_fees, prepaids, total_other_costs, total_closing_costs, initial_escrow_deposit, monthly_escrow_payment, aggregate_adjustment. For appraisal documents also extract: appraised_value, appraiser_name, appraiser_cert, property_type, year_built, gross_living_area, comparable_sales, ltv_original, ltv_revised, adjustment_amount, adjustment_reason, hazard_insurance, property_tax, flood_zone_surcharge. Extract any other clearly labeled field you find even if not in this list. CRITICAL: Always extract loan_amount if it appears anywhere in the text, including inside underwriting notes like '($586,500.00 value, $490,000.00 loan)'.\n\n"
        "2. For every field record the source_page — the page number where the final selected value appears.\n\n"
        "3. CORRECTION DETECTION. When you see revision language like \"REVISED to\", \"REVISED DOWNWARD to\", \"CORRECTED to\", \"supersedes\", \"amended to\", or \"originally stated ... now\", you must do this: set value to the NEW corrected number, set original_value to the OLD number, set correction_applied to true, set source_page to the page where the correction appears, and write decision_reason explaining the revision. CRITICAL: in a sentence like \"($9,920.00) is REVISED to $11,475.00\" the value is 11475.00 and original_value is 9920.00. Never miss the revised number.\n\n"
        "4. CONFLICT RULES when the same field appears with different values and there is NO explicit revision language:\n"
        "   - If one value contains the other as a substring, use the shorter cleaner value. This is not a conflict. Example: document_type \"LOAN ESTIMATE\" wins over \"ADDENDUM TO LOAN ESTIMATE — FEE CORRECTION\".\n"
        "   - If one value has obvious OCR character errors (letter O for zero, letter I for one) and another is clean, use the clean value and record the messy one in degraded_regions.\n"
        "   - If genuinely ambiguous with no way to decide, set value to null, set requires_review to true, and explain in confidence_reason.\n\n"
        "5. MONEY FORMATTING. Return money as plain numbers — no dollar signs, no commas. Parentheses mean negative: \"$(140.00)\" becomes -140.00 and \"$(0.00)\" becomes 0.00. Strip footnote markers: \"$9,920.00 *see note\" becomes just the number for the value field, but mention the footnote in confidence_reason.\n\n"
        "6. CONFIDENCE for every field:\n"
        "   - high: a single clean value, no conflict, clearly readable, no correction needed.\n"
        "   - medium: a correction was applied, OR the value was inferred, OR a footnote or note affects it, OR a conflict was resolved by a rule.\n"
        "   - low: text was degraded or marked [UNCLEAR] or [STAMP, partial], OR an unresolved conflict, OR you are genuinely unsure.\n"
        "   Always give a one-line confidence_reason whenever confidence is not high.\n\n"
        "7. DEGRADED REGIONS. Any text marked [UNCLEAR: ...] or [STAMP, partial] or that you found hard to read goes into the degraded_regions list with the page number, the raw text, your best_guess, and a short reason.\n\n"
        "8. RECONCILIATION FORMULAS. List every total or computed value that should be arithmetically checked, expressed as a formula naming the fields. Do NOT compute the arithmetic yourself — only state the formula. Examples:\n"
        "   - origination_charges + services_not_shopped + services_shopped = total_loan_costs\n"
        "   - government_fees + prepaids = total_other_costs\n"
        "   - total_loan_costs + total_other_costs = total_closing_costs\n"
        "   For appraisals: loan_amount / appraised_value = ltv_revised (as a percentage)\n\n"
        "CRITICAL COMPLETENESS RULES — these prevent missing embedded values:\n\n"
        "A. EXTRACT VALUES EMBEDDED INSIDE SENTENCES, NOT JUST LABELED ROWS.\n"
        "Monetary values and percentages do not always appear as a clean \"Label: $value\" row. They are often embedded inside descriptive sentences, parentheses, or notes. You MUST extract these too. Examples of embedded values you must capture:\n"
        "  - \"Original LTV (at $845,000.00 value, $680,000.00 loan): 80.47%\" → extract loan_amount = 680000.00 AND appraised_value reference AND ltv_original = 80.47\n"
        "  - \"Revised LTV (at $798,000.00 value, $680,000.00 loan): 85.2%\" → the $680,000.00 loan figure is the loan_amount\n"
        "  - \"Adjustment basis: -$25,500.00 (deferred maintenance)\" → extract adjustment_amount = -25500.00\n"
        "When the same value (like loan_amount) appears inside multiple sentences, extract it once with the page where it is clearest.\n\n"
        "B. SCAN FOR EVERY MONETARY VALUE AND PERCENTAGE IN THE ENTIRE DOCUMENT.\n"
        "Before finishing, re-read the full document text and confirm that EVERY dollar amount, EVERY percentage, and EVERY numeric identifier you can see has been mapped to a field. If you find a monetary value or percentage that you have not yet placed into a field, create an appropriately named field for it rather than dropping it. Never silently skip a number that appears in the text.\n\n"
        "C. MORTGAGE DOMAIN KNOWLEDGE — values are frequently embedded in these locations:\n"
        "  - Underwriting notes (loan amount, LTV inputs)\n"
        "  - Parenthetical explanations (adjustment basis, value breakdowns)\n"
        "  - LTV calculation sentences (both the property value and the loan amount are stated inside the LTV line)\n"
        "  - Footnotes and correction notices (the revised value lives in the sentence, not a row)\n"
        "  - Escrow and insurance reference blocks\n"
        "Always check these locations for embedded monetary values.\n\n"
        "D. LTV LINES CONTAIN THREE NUMBERS — extract all three.\n"
        "A line like \"Revised LTV (at $798,000.00 value, $680,000.00 loan): 85.2%\" contains: the property/appraised value, the loan amount, and the LTV percentage. Extract the loan amount as loan_amount and the percentage as the LTV field. Do not extract only the percentage.\n\n"
        "E. IF A FIELD IS NEEDED FOR A RECONCILIATION FORMULA, IT MUST BE EXTRACTED.\n"
        "When you write a reconciliation formula that references a field (for example loan_amount / appraised_value = ltv_revised), every field named in that formula MUST exist in your fields output with a real value. Never write a formula that references a field you did not extract. If you reference loan_amount in a formula, you must also extract loan_amount as a field.\n\n"
        "OUTPUT SCHEMA — return exactly this structure:\n"
        "{\n"
        "  \"document_type\": {\n"
        "    \"value\": \"string\",\n"
        "    \"source_page\": 1,\n"
        "    \"confidence\": \"high\",\n"
        "    \"confidence_reason\": null\n"
        "  },\n"
        "  \"fields\": {\n"
        "    \"field_name\": {\n"
        "      \"value\": \"number or string or null\",\n"
        "      \"original_value\": \"number or null\",\n"
        "      \"source_page\": 1,\n"
        "      \"confidence\": \"high or medium or low\",\n"
        "      \"confidence_reason\": \"string or null\",\n"
        "      \"correction_applied\": false,\n"
        "      \"decision_reason\": \"string or null\",\n"
        "      \"requires_review\": false\n"
        "    }\n"
        "  },\n"
        "  \"reconciliation_formulas\": [\n"
        "    {\n"
        "      \"description\": \"string\",\n"
        "      \"formula\": \"string\",\n"
        "      \"fields_involved\": [\"field_a\", \"field_b\", \"field_c\"]\n"
        "    }\n"
        "  ],\n"
        "  \"degraded_regions\": [\n"
        "    {\n"
        "      \"page\": 2,\n"
        "      \"raw_text\": \"string\",\n"
        "      \"best_guess\": \"string\",\n"
        "      \"reason\": \"string\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    user_message = (
        "Here is the full mortgage document text. Extract everything according to the rules and return only the JSON object.\n\n"
        "--- DOCUMENT TEXT ---\n"
        f"{page_text}\n"
        "--- END DOCUMENT TEXT ---"
    )

    @retry_with_backoff
    def do_call(messages):
        response = client.chat.completions.create(
            model=settings.vision_model,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    try:
        content = do_call(messages)
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}. Raw response: {content}")
        messages.append({"role": "assistant", "content": content})
        messages.append({"role": "user", "content": "Your previous response was not valid JSON. Return ONLY a valid JSON object, no markdown, no commentary."})
        content2 = do_call(messages)
        try:
            return json.loads(content2)
        except json.JSONDecodeError as e2:
            raise ValueError(f"Failed to parse JSON after retry. Raw response: {content2}") from e2
