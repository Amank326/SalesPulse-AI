import os
from typing import Dict, Any

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

class GeminiService:
    """Minimal wrapper for Gemini API calls. Reads API key from environment.
    This file intentionally does not perform any network calls until the key
    is provided and a proper HTTP client is configured.
    """

    def __init__(self):
        if not GEMINI_API_KEY:
            raise RuntimeError('GEMINI_API_KEY is not set in environment. Set it in .env or env vars.')
        self.api_key = GEMINI_API_KEY

    def summarize_business(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder: implement requests to Gemini API securely using `requests` or `httpx`.
        # Returns a minimal structure for now.
        return {"summary": "Gemini integration not yet implemented on this instance."}
