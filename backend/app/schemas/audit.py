from datetime import datetime

from pydantic import BaseModel


class AuditEvent(BaseModel):
    id: str | None = None
    document_id: str
    action: str
    detail: str
    created_at: datetime
