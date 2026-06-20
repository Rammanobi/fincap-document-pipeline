import typer
import os
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
        doc_text, combined_text = run_phase1(pdf_path)
        extraction_result = run_phase2(combined_text)
        assignment_result = run_phase3(extraction_result, doc_id)
        
        output_txt = os.path.join(settings.output_dir, "page_text.txt")
        output_json = os.path.join(settings.output_dir, "extraction.json")
        output_final = os.path.join(settings.output_dir, "assignment.json")
        
        print(f"Output saved to: {output_txt}")
        print(f"Output saved to: {output_json}")
        print(f"Output saved to: {output_final}")
        
        status = assignment_result.get("status", "unknown")
        review_signals = assignment_result.get("review", {}).get("review_signals", [])
        fields_requiring_review = len(set([sig.get("field_name") for sig in review_signals]))
        
        print(f"Summary: Document status is {status.upper()}. {fields_requiring_review} field(s) require review.")
        
    except Exception as e:
        typer.secho(f"ERROR: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
