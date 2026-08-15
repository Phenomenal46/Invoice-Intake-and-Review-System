import json
from google import genai
from google.genai import types

from app.config import settings
from app.schemas.document import LLMOutput, ExtractedFields
from app.utils.dates import normalize_date_to_ddmmyyyy

# The Prompt: We explicitly tell the AI to act as a visual data extractor.
SYSTEM_PROMPT = (
    "You are a professional document analyst. Look at the provided document (pdf/image/text/docx or any valid format). "
    "1. Extract the vendor name, invoice number, date, and total amount into 'extracted_data'. "
    "2. Return the date only in dd/mm/yyyy format. "
    "3. Provide a short summary, a classification(Invoice, Receipt, etc), and list any risks."
)

def _fallback_llm_output(text: str) -> LLMOutput:
    snippet = text.strip().replace("\\n", " ")[:200]
    return LLMOutput(
        extracted_data=ExtractedFields(), # Safe empty data keeps the app running when Gemini is unavailable.
        summary=snippet or "No content provided.",
        classification="Unknown",
        confidence=0.0,
        key_points=[],
        risks=[],
    )


def _normalize_parsed_data(parsed_data: dict) -> dict:
    extracted_data = parsed_data.get("extracted_data") or {}
    extracted_data["invoice_date"] = normalize_date_to_ddmmyyyy(extracted_data.get("invoice_date"))
    parsed_data["extracted_data"] = extracted_data

    classification = str(parsed_data.get("classification") or "Unknown").strip()
    parsed_data["classification"] = classification or "Unknown"
    return parsed_data

# NEW: We now accept an optional 'file_path'
def _upload_file_to_gemini(client, file_path: str):
    return client.files.upload(file=file_path)


def call_llm(text: str, file_path: str | None = None) -> LLMOutput:
    if not settings.gemini_api_key:
        print("Warning: No Gemini API key provided. Using fallback.")
        return _fallback_llm_output(text)

    client = None
    uploaded_file = None
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
            uploaded_file = _upload_file_to_gemini(client, file_path)
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
        
        parsed_data = _normalize_parsed_data(json.loads(response.text))
        return LLMOutput(**parsed_data)
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return _fallback_llm_output(text)
    finally:
        # The temporary Gemini upload must be deleted even if the request fails, so repeated uploads do not leak storage.
        if client is not None and uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass