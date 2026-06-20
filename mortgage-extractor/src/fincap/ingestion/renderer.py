import os
import shutil
import fitz
from ..config import settings

def render_pages(file_path: str, dpi: int = 200) -> list[str]:
    """
    Renders each page of a PDF as a PNG image.
    Input: file_path (str), dpi (int, default 200)
    Process: Opens PDF, creates a temp folder, loops through pages, and saves each as PNG.
    Output: List of file paths to the rendered PNG images.
    """
    doc = fitz.open(file_path)
    
    page_images_dir = os.path.join(settings.output_dir, "page_images")
    if os.path.exists(page_images_dir):
        shutil.rmtree(page_images_dir)
    os.makedirs(page_images_dir, exist_ok=True)
    
    image_paths = []
    # 200 DPI is a deliberate choice — sharp enough for the vision model to read small text and degraded blocks, but not so large that the image files become huge and slow to upload.
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    
    for i in range(doc.page_count):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=matrix)
        
        page_num = i + 1
        output_path = os.path.join(page_images_dir, f"page_{page_num}.png")
        pix.save(output_path)
        
        image_paths.append(output_path)
        print(f"Rendered page {page_num} at {dpi} DPI")
        
    return image_paths
