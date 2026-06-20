import time
import random
from functools import wraps
import openai
from openai import OpenAI
from ..config import settings

def retry_with_backoff(func):
    """
    Decorator that applies exponential backoff for specific OpenAI API errors.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 5
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (openai.AuthenticationError, openai.BadRequestError, openai.PermissionDeniedError) as e:
                # Fail fast on errors that will never succeed on retry
                raise e
            except (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError, openai.InternalServerError) as e:
                if attempt == max_retries - 1:
                    raise Exception(f"OpenAI API call failed after {max_retries} attempts: {e}") from e
                
                delay = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                print(f"Rate limited / transient error. Retry attempt {attempt + 1} of {max_retries} after {delay:.2f}s delay")
                time.sleep(delay)
            # Other exceptions will bubble up naturally
    return wrapper

def get_client() -> OpenAI:
    """
    Returns the configured OpenAI client.
    Input: None
    Process: Instantiates the OpenAI client using the API key from settings.
    Output: OpenAI client instance.
    """
    return OpenAI(api_key=settings.openai_api_key)
