from datetime import datetime, timezone


def build_audit_event(document_id: str, action: str, detail: str) -> dict:
    return {
        "document_id": document_id,
        "action": action,
        "detail": detail,
        "created_at": datetime.now(timezone.utc),
    }
