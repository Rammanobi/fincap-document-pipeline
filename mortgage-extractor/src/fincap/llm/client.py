from openai import OpenAI
from ..config import settings

def get_client() -> OpenAI:
    """
    Returns the configured OpenAI client.
    Input: None
    Process: Instantiates the OpenAI client using the API key from settings.
    Output: OpenAI client instance.
    """
    return OpenAI(api_key=settings.openai_api_key)
