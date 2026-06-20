# Mortgage Extractor

An intelligent, 3-phase pipeline for extracting structured financial data from mortgage and appraisal PDF documents using Vision AI and deterministic Python math.

## Features

- **Phase 1: Ingestion & Vision Transcription**
  - Validates the PDF structure.
  - Renders pages as high-quality 200 DPI images.
  - Transcribes text using OpenAI's `gpt-4o` Vision model, capturing complex layouts, footnotes, and stamps.
  - **Robust Error Handling:** Features exponential backoff and jitter for resilient API interactions during rate limits.
  
- **Phase 2: LLM Data Extraction**
  - Extracts targeted fields using `gpt-4o` forced to output structured JSON.
  - Intelligently detects and applies corrections from underwriting notes or revision stamps.
  - Extracts fields reliably even when embedded within complex sentences.
  - Flags degraded text regions and identifies reconciliation formulas for validation.
  - **Comprehensive Extraction:** Enforces strict rules to capture embedded monetary values (e.g., LTV inputs) deep within underwriting paragraphs.

- **Phase 3: Deterministic Reconciliation & Audit Assembly**
  - **Zero LLM usage:** Uses deterministic Python `decimal.Decimal` arithmetic to verify financial formulas.
  - Automatically flags discrepancies where subtotals do not match inputs.
  - Builds a comprehensive Human Review Signal list (`critical`, `high`, `medium` priorities).
  - Creates a strict Audit Trail logging prompt versions and models for regulated environments.
  - Generates the final, clean `assignment.json`.

## Tech Stack

- **Language:** Python 3.12+
- **Package Manager:** `uv`
- **CLI Framework:** `Typer`
- **PDF Processing:** `PyMuPDF` (`fitz`)
- **LLM API:** OpenAI API (`gpt-4o`)
- **Data Validation:** `Pydantic`
- **Math Engine:** Native Python `decimal.Decimal`

## Prerequisites

1. Install `uv` (Fast Python package manager) if you haven't already.
2. Have an OpenAI API Key with access to the `gpt-4o` model.

## Setup

1. Navigate to the project root:
   ```bash
   cd mortgage-extractor
   ```

2. The dependencies are already managed via `pyproject.toml`. You can ensure they are synced by running:
   ```bash
   uv sync
   ```

3. Configure your `.env` file in the root of the project with your API key:
   ```env
   OPENAI_API_KEY=sk-proj-...
   ```

## Usage

You can extract data from any supported mortgage or appraisal document by pointing the CLI tool to the PDF file.

### Command

```bash
uv run fincap extract <path_to_pdf>
```

### Examples

Extract from a Loan Estimate:
```bash
uv run fincap extract fixtures/loan_doc.pdf
```

Extract from an Appraisal Document:
```bash
uv run fincap extract fixtures/appraisal_doc.pdf
```

## Outputs

After execution, the pipeline creates a dedicated per-document folder under `outputs/` (e.g., `outputs/<document_name>/`) containing three key files. If a folder for that document already exists, subsequent runs will safely append a timestamp to the folder name to preserve all historical data.

1. **`outputs/<document_name>/page_text.txt`**: The combined transcription from the Vision LLM (Phase 1).
2. **`outputs/<document_name>/extraction.json`**: The raw structured JSON extraction directly from the LLM (Phase 2).
3. **`outputs/<document_name>/assignment.json`**: The final verified, mathematically reconciled, and audited deliverable (Phase 3). This is the primary output containing confidence intervals, review flags, and the audit trail.
