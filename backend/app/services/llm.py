import json
from typing import Any

import httpx

from app.config import settings
from app.schemas.document import LLMOutput


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
    if not settings.llm_api_key:
        return _fallback_llm_output(text)

    payload = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.2,
    }

    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}

    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(
                f"{settings.llm_api_base}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
        return _fallback_llm_output(text)

    parsed = _safe_parse_json(content)
    if not parsed:
        return _fallback_llm_output(text)

    return LLMOutput(
        summary=str(parsed.get("summary", "")) or "No summary.",
        classification=str(parsed.get("classification", "Unknown")),
        confidence=float(parsed.get("confidence", 0.0) or 0.0),
        key_points=list(parsed.get("key_points", []) or []),
        risks=list(parsed.get("risks", []) or []),
    )
