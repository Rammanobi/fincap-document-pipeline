import os
import sys
import json
from .ingestion.validator import validate_pdf
from .ingestion.renderer import render_pages
from .llm.vision_reader import read_page_with_vision
from .llm.extractor import extract_fields
from .models import DocumentText, PageText
from .config import settings

from .reconciler import reconcile
from .review import build_review
from .audit import build_audit
from .assembler import assemble

def run_phase1(file_path: str, output_folder: str) -> tuple[DocumentText, str]:
    """
    Orchestrates Phase 1: validate, render pages, transcribe via vision, and save combined text.
    Input: file_path (str)
    Process: Validates PDF, renders it to PNGs, transcribes each page with gpt-4o, and writes output.
    Output: DocumentText object and combined text string.
    """
    try:
        val_result = validate_pdf(file_path)
        
        image_paths = render_pages(file_path, dpi=settings.render_dpi)
        
        page_texts = []
        for i, img_path in enumerate(image_paths):
            page_num = i + 1
            text = read_page_with_vision(img_path, page_num)
            page_texts.append(PageText(page_number=page_num, text=text))
            
        doc_text = DocumentText(
            filename=val_result.filename,
            page_count=val_result.page_count,
            pages=page_texts
        )
        
        combined_parts = []
        for pt in doc_text.pages:
            combined_parts.append(f"[PAGE {pt.page_number}]\n{pt.text}\n")
        combined_text = "\n".join(combined_parts)
        
        os.makedirs(output_folder, exist_ok=True)
        output_file = os.path.join(output_folder, "page_text.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(combined_text)
            
        print(f"Phase 1 complete. Combined text written to {output_file}")
        
        return doc_text, combined_text
    except Exception as e:
        print(f"\nPipeline Failed during Phase 1: {e}")
        if 'page_texts' in locals() and page_texts:
            partial_parts = [f"[PAGE {pt.page_number}]\n{pt.text}\n" for pt in page_texts]
            partial_text = "\n".join(partial_parts)
            os.makedirs(output_folder, exist_ok=True)
            output_file = os.path.join(output_folder, "partial_page_text.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(partial_text)
            print(f"Partial output saved to {output_file}")
        sys.exit(1)

def run_phase2(page_text: str, output_folder: str) -> dict:
    """
    Orchestrates Phase 2: extract structured JSON using LLM.
    """
    try:
        extraction_result = extract_fields(page_text)
        
        output_file = os.path.join(output_folder, "extraction.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(extraction_result, f, indent=2)
            
        print("Phase 2 complete. Extraction written to outputs/extraction.json")
        return extraction_result
    except Exception as e:
        print(f"\nPipeline Failed during Phase 2 (Extraction): {e}")
        sys.exit(1)

def run_phase3(extraction: dict, document_id: str, output_folder: str) -> dict:
    """
    Orchestrates Phase 3: verify math, set review flags, assemble final JSON.
    """
    try:
        reconciliations = reconcile(extraction)
        review = build_review(extraction, reconciliations)
        audit = build_audit(extraction)
        assignment = assemble(document_id, extraction, reconciliations, review, audit)
        
        output_file = os.path.join(output_folder, "assignment.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(assignment, f, indent=2)
            
        print("Phase 3 complete. Final output at outputs/assignment.json")
        return assignment
    except Exception as e:
        print(f"\nPipeline Failed during Phase 3 (Reconciliation/Assembly): {e}")
        sys.exit(1)
