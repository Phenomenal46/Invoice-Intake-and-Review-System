import json
from typing import Any

# OpenAI SDK replaces raw HTTP calls for cleaner API interaction
from openai import OpenAI

from app.config import settings
from app.schemas.document import LLMOutput

# Initialize OpenAI SDK client with API key and timeout settings
client = OpenAI(
    api_key=settings.llm_api_key,
    timeout=settings.llm_timeout_seconds,
)

SYSTEM_PROMPT = (
    "You are an assistant that extracts structured JSON. "
    "Return ONLY valid JSON with keys: summary, classification, confidence, "
    "key_points, risks."
)


def _fallback_llm_output(text: str) -> LLMOutput:
    snippet = text.strip().replace("\n", " ")[:200]
    return LLMOutput(
        summary=snippet or "No content provided.",
        classification="Unknown",
        confidence=0.0,
        key_points=[],
        risks=[],
    )


def _safe_parse_json(raw: str) -> dict[str, Any] | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or start >= end:
        return None

    try:
        return json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None


def call_llm(text: str) -> LLMOutput:
    # Skip API call if no API key is configured; return fallback instead
    if not settings.llm_api_key:
        return _fallback_llm_output(text)

    try:
        # Use OpenAI SDK to call the chat completions API
        # SDK handles all HTTP details, headers, and response parsing for us
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )
        
        # Extract response text from the first choice (SDK structures response as objects)
        content = response.choices[0].message.content
        
    except Exception:
        # Catch API errors: network failures, auth errors, rate limits, etc.
        # Return fallback instead of crashing the application
        return _fallback_llm_output(text)

    # Parse the LLM's JSON response string into a dictionary
    parsed = _safe_parse_json(content)
    if not parsed:
        # If JSON parsing fails, return fallback
        return _fallback_llm_output(text)

    # Map JSON fields to the LLMOutput schema with type conversions and defaults
    return LLMOutput(
        summary=str(parsed.get("summary", "")) or "No summary.",
        classification=str(parsed.get("classification", "Unknown")),
        confidence=float(parsed.get("confidence", 0.0) or 0.0),
        key_points=list(parsed.get("key_points", []) or []),
        risks=list(parsed.get("risks", []) or []),
    )
