import os
import fitz
from ..models import ValidationResult

def validate_pdf(file_path: str) -> ValidationResult:
    """
    Validates that a file is a valid PDF and can be opened.
    Input: file_path (str)
    Process: Checks extension, opens with PyMuPDF, checks page count, and file size.
    Output: ValidationResult containing filename, page_count, and file_size_bytes.
    """
    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"Validation failed: file is not a .pdf — got {file_path}")
        
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        raise ValueError("Validation failed: PyMuPDF cannot open the file — it may be corrupted or password protected") from e
        
    page_count = doc.page_count
    if page_count == 0:
        raise ValueError("Validation failed: PDF has zero pages")
        
    file_size_bytes = os.path.getsize(file_path)
    if file_size_bytes < 1024:
        raise ValueError("Validation failed: file is smaller than 1KB — likely empty or corrupt")
        
    filename = os.path.basename(file_path)
    print(f"Validation passed: {filename} has {page_count} pages")
    
    return ValidationResult(
        filename=filename,
        page_count=page_count,
        file_size_bytes=file_size_bytes
    )
