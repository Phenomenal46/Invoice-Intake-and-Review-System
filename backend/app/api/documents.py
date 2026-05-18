from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db.mongo import get_collections
from app.schemas.audit import AuditEvent
from app.schemas.document import DocumentResponse
from app.services import audit, extraction, llm, validation, workflow
from app.utils.serialization import parse_object_id, serialize_document

router = APIRouter()


def _load_text(text: str | None, file: UploadFile | None) -> tuple[str, str, dict]:
    if text:
        return text, "text", {"filename": None}

    if file:
        raw_bytes = file.file.read()
        return (
            raw_bytes.decode("utf-8", errors="ignore"),
            "file",
            {"filename": file.filename},
        )

    raise HTTPException(status_code=400, detail="Provide text or a file.")


def _parse_document_id(raw_id: str):
    try:
        return parse_object_id(raw_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid document id.") from exc


@router.post("/documents", response_model=DocumentResponse)
def create_document(
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> dict:
    raw_text, source, metadata = _load_text(text, file)
    extracted = extraction.extract_fields(raw_text)
    validation_result = validation.validate_fields(extracted)
    llm_output = llm.call_llm(raw_text)
    status = workflow.decide_status(validation_result, llm_output)

    documents, audit_logs = get_collections()
    now = datetime.now(timezone.utc)
    doc = {
        "created_at": now,
        "source": source,
        "text": raw_text,
        "extracted": extracted.model_dump(),
        "validation": validation_result.model_dump(),
        "llm": llm_output.model_dump(),
        "workflow_status": status.value,
        "metadata": metadata,
    }

    result = documents.insert_one(doc)
    document_id = str(result.inserted_id)

    audit_logs.insert_one(audit.build_audit_event(document_id, "document_created", "Document ingested."))
    audit_logs.insert_one(
        audit.build_audit_event(
            document_id,
            "workflow_assigned",
            f"Status: {status.value}",
        )
    )

    doc["_id"] = result.inserted_id
    return {"document": serialize_document(doc)}


@router.get("/documents")
def list_documents() -> dict:
    documents, _ = get_collections()
    cursor = documents.find({}, {"text": 0}).sort("created_at", -1).limit(50)
    items = [serialize_document(doc) for doc in cursor]
    return {"items": items}


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str) -> dict:
    documents, _ = get_collections()
    object_id = _parse_document_id(document_id)
    doc = documents.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document": serialize_document(doc)}


@router.get("/documents/{document_id}/audit")
def get_audit(document_id: str) -> dict:
    _, audit_logs = get_collections()
    cursor = audit_logs.find({"document_id": document_id}).sort("created_at", -1)
    items = []
    for entry in cursor:
        entry["id"] = str(entry.pop("_id"))
        items.append(AuditEvent(**entry).model_dump())
    return {"items": items}
