import json
from google import genai
from google.genai import types

from app.config import settings
from app.schemas.document import LLMOutput, ExtractedFields

# The Prompt: We explicitly tell the AI to act as a visual data extractor.
SYSTEM_PROMPT = (
    "You are a professional document analyst. Look at the provided document (pdf/image/text or any valid format). "
    "1. Extract the vendor name, invoice number, date, and total amount into 'extracted_data'. "
    "2. Provide a short summary, a classification (e.g., 'Invoice'), and list any risks."
)

def _fallback_llm_output(text: str) -> LLMOutput:
    snippet = text.strip().replace("\\n", " ")[:200]
    return LLMOutput(
        extracted_data=ExtractedFields(), # Returns empty fields so app doesn't crash
        summary=snippet or "No content provided.",
        classification="Unknown",
        confidence=0.0,
        key_points=[],
        risks=[],
    )

# NEW: We now accept an optional 'file_path'
def call_llm(text: str, file_path: str | None = None) -> LLMOutput:
    if not settings.gemini_api_key:
        print("Warning: No Gemini API key provided. Using fallback.")
        return _fallback_llm_output(text)

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        
        schema = {
    "type": "OBJECT",
    "properties": {
        "extracted_data": {
            "type": "OBJECT",
            "properties": {
                "vendor": {
                    "type": "STRING"
                },
                "invoice_number": {
                    "type": "STRING"
                },
                "invoice_date": {
                    "type": "STRING"
                },
                "total_amount": {
                    "type": "NUMBER"
                }
            }
        },
        "summary": {
            "type": "STRING"
        },
        "classification": {
            "type": "STRING"
        },
        "confidence": {
            "type": "NUMBER"
        },
        "key_points": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        },
        "risks": {
            "type": "ARRAY",
            "items": {
                "type": "STRING"
            }
        }
    }
        }

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            # We lower the temperature to 0.0. This makes the AI "robotic" and 
            # strictly factual, which is exactly what we want for reading numbers!
            temperature=0.0, 
            response_mime_type="application/json",
            response_schema=schema
        )

        # ---------------------------------------------------------
        # Build the list of inputs that Gemini will receive.
        # Gemini accepts multiple "contents".
        # Example:
        # contents = [
        #       uploaded_pdf,
        #       "Extract invoice details."
        # ]
        # or
        # contents = [
        #       "Hello"
        # ]
        # ---------------------------------------------------------

        contents = []

        # Upload the document if one exists.
        if file_path:
            uploaded_file = client.files.upload(
                file=file_path
            )
            contents.append(uploaded_file)

        # Add user text if available.
        if text.strip():
            contents.append(text)
        
        # Call the AI with our image and/or text
        response = client.models.generate_content(
            model=settings.llm_model, 
            contents=contents,
            config=config
        )
        
        # ---------------------------------------------------------
        # Delete the temporary uploaded Gemini file.
        #
        # This keeps your Gemini file storage clean.
        # ---------------------------------------------------------

        if file_path:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass
        
        parsed_data = json.loads(response.text)
        return LLMOutput(**parsed_data)
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return _fallback_llm_output(text)