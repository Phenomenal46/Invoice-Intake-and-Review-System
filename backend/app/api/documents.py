import os
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.db.mongo import get_collections
from app.schemas.audit import AuditEvent
from app.schemas.document import DocumentResponse
from app.services import audit, llm, validation, workflow
from app.utils.serialization import parse_object_id, serialize_document

router = APIRouter()


def handle_upload(text: str | None, file: UploadFile | None) -> tuple[str, str, dict]:
    metadata = {"filename": None, "file_url": None}
    raw_text = text or ""
    source = "unknown"

    if text:
        source = "text"

    if file:
        source = "file"
        metadata["filename"] = file.filename
        
        # 1. Extract the file extension (e.g., '.pdf' or '.png')
        file_extension = os.path.splitext(file.filename)[1]
        
        # 2. Create a unique file name using UUID
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("uploads", unique_filename)
        metadata["local_path"] = file_path
        
        # 3. Save the actual file to our "uploads" folder
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 4. Save the URL so the frontend can find it later
        metadata["file_url"] = f"http://localhost:8000/uploads/{unique_filename}"

        # Temporary fix: Let's not crash if it's an image. 
        # We will replace this with AI Vision in Phase 3!
        file.file.seek(0) # Reset file pointer
        try:
            raw_text = file.file.read().decode("utf-8", errors="ignore")
        except Exception:
            raw_text = "Image or PDF uploaded. AI Vision will process this soon."

    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide text or a file.")

    return raw_text, source, metadata


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
    raw_text, source, metadata = handle_upload(text, file)
    
    local_path = metadata.get("local_path")
    
    # 1. Ask the AI to look at the file and text
    llm_output = llm.call_llm(raw_text, file_path=local_path)
    
    # 2. Grab the extracted data directly from the AI's brain!
    extracted = llm_output.extracted_data 
    
    # 3. Validate it using our existing rules
    validation_result = validation.validate_fields(extracted)
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
    audit_logs.insert_one(audit.build_audit_event(document_id, "workflow_assigned", f"Status: {status.value}"))

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
