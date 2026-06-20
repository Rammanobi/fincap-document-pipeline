import typer
import os
import re
from datetime import datetime
from .pipeline import run_phase1, run_phase2, run_phase3
from .config import settings

app = typer.Typer()

@app.callback()
def callback():
    pass

@app.command("extract")
def extract(pdf_path: str):
    try:
        doc_id = os.path.basename(pdf_path)
        base_name = os.path.splitext(doc_id)[0]
        clean_name = re.sub(r'[^a-zA-Z0-9_\-.]', '_', base_name)
        
        output_folder = os.path.join(settings.output_dir, clean_name)
        if os.path.exists(output_folder):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_folder = os.path.join(settings.output_dir, f"{clean_name}_{timestamp}")
            
        os.makedirs(output_folder, exist_ok=True)
        
        doc_text, combined_text = run_phase1(pdf_path, output_folder)
        extraction_result = run_phase2(combined_text, output_folder)
        assignment_result = run_phase3(extraction_result, doc_id, output_folder)
        
        output_txt = os.path.join(output_folder, "page_text.txt")
        output_json = os.path.join(output_folder, "extraction.json")
        output_final = os.path.join(output_folder, "assignment.json")
        
        print(f"Outputs saved to directory: {output_folder}")
        
        status = assignment_result.get("status", "unknown")
        review_signals = assignment_result.get("review", {}).get("review_signals", [])
        fields_requiring_review = len(set([sig.get("field_name") for sig in review_signals]))
        
        print(f"Summary: Document status is {status.upper()}. {fields_requiring_review} field(s) require review.")
        
    except Exception as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
