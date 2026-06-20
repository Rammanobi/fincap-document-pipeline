import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str
    vision_model: str = "gpt-4o"
    render_dpi: int = 200
    output_dir: str = "outputs"
    prompt_version: str = "v1.0"

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY is not set in the .env file.")

settings = Settings(
    openai_api_key=api_key,
    vision_model="gpt-4o",
    render_dpi=200,
    output_dir="outputs",
    prompt_version="v1.0"
)
