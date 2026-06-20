import base64
from .client import get_client
from ..config import settings

def read_page_with_vision(image_path: str, page_number: int) -> str:
    """
    Transcribes a page image using gpt-4o vision.
    Input: image_path (str), page_number (int)
    Process: Encodes the PNG to base64, calls the vision API, extracts text.
    Output: Transcribed text (str).
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        data_url = f"data:image/png;base64,{encoded_image}"
        
        client = get_client()
        
        response = client.chat.completions.create(
            model=settings.vision_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise document transcription system for mortgage documents. "
                        "You receive an image of one page. Transcribe ALL text exactly as it appears, "
                        "preserving reading order, tables, and structure.\n\n"
                        "RULES:\n"
                        "1. Transcribe every number, label, and value exactly as shown.\n"
                        "2. Preserve table structure using spacing or pipe characters so rows and columns stay readable.\n"
                        "3. If any text is degraded, partially cut off, or a stamp is unclear, transcribe your best reading "
                        "and mark it inline as [UNCLEAR: your best guess] so later steps know it was hard to read.\n"
                        "4. For money keep the ORIGINAL notation. Do not normalize. Transcribe $(140.00) exactly as $(140.00). "
                        "Transcribe a value with a footnote like $9,920.00 *see note below exactly as written including the asterisk.\n"
                        "5. If you see revision language such as \"REVISED to\" or \"CORRECTED to\" or \"supersedes\", transcribe "
                        "the full sentence including BOTH the old and new values exactly.\n"
                        "6. Do not summarize. Do not add commentary or explanation. Output only the transcribed text of this single page."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Transcribe all text from this mortgage document page exactly as it appears. This is page {page_number}."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        }
                    ]
                }
            ],
            temperature=0
        )
        
        print(f"Vision transcribed page {page_number}")
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error calling vision API for page {page_number}: {e}")
        raise
