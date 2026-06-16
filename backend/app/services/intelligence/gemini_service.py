import re
import json
import httpx
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel
from app.core.config import settings

class GeminiService:
    @classmethod
    def clean_json_response(cls, text: str) -> str:
        """Strip markdown code block ticks if Gemini wraps JSON in them."""
        text = text.strip()
        if text.startswith("```"):
            # Try to strip ```json ... ```
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text

    @classmethod
    def call_gemini(
        cls, 
        system_instruction: str, 
        prompt: str, 
        response_schema: Type[BaseModel],
        max_retries: int = 1
    ) -> BaseModel:
        """Call the Gemini API with strict JSON constraint and validate against pydantic schema."""
        api_key = getattr(settings, "GEMINI_API_KEY", None)
        model = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
        timeout = getattr(settings, "GEMINI_TIMEOUT_SECONDS", 25)

        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing in backend configuration")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }

        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                with httpx.Client(timeout=float(timeout)) as client:
                    response = client.post(url, headers=headers, json=payload)
                    
                    # Prevent logging the API key or raw sensitive error tracebacks
                    if response.status_code != 200:
                        raise RuntimeError(f"Gemini API returned status code {response.status_code}")
                    
                    res_json = response.json()
                    
                    # Extract the response text
                    candidates = res_json.get("candidates", [])
                    if not candidates:
                        raise RuntimeError("No generation candidates returned from Gemini")
                    
                    part = candidates[0].get("content", {}).get("parts", [])[0]
                    text_out = part.get("text", "")
                    
                    cleaned_text = cls.clean_json_response(text_out)
                    parsed_dict = json.loads(cleaned_text)
                    
                    # Validate against Pydantic schema
                    validated_obj = response_schema.model_validate(parsed_dict)
                    return validated_obj

            except Exception as e:
                # Sanitize error message to prevent leaking secrets/keys
                err_msg = str(e)
                if api_key in err_msg:
                    err_msg = err_msg.replace(api_key, "[REDACTED_API_KEY]")
                last_exception = RuntimeError(f"Gemini call failed (attempt {attempt + 1}): {err_msg}")

        raise last_exception if last_exception else RuntimeError("Failed to communicate with Gemini")
