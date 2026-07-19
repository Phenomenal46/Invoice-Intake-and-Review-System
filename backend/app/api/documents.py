from email.mime import text
import os
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.db.mongo import get_collections
from app.schemas.audit import AuditEvent
from app.schemas.document import DocumentResponse
from app.services import audit, llm, validation, workflow
from app.utils.dates import normalize_date_to_ddmmyyyy
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
        # Original filename
        metadata["filename"] = file.filename
        # MIME type
        metadata["mime_type"] = file.content_type
        
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

        # ---------------------------------------------------------
        # IMPORTANT
        #
        # Do NOT try to manually convert PDFs/images/docx into text.
        # Gemini understands these files directly.
        # We only keep raw text if the user actually typed something.
        # ---------------------------------------------------------

        raw_text = text or ""
        
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




# 1. Define what data we expect from the frontend when a user clicks "Approve"
class DocumentUpdate(BaseModel):
    vendor: str
    invoice_number: str
    invoice_date: str
    total_amount: float | str | None = None

# 2. Create a PATCH route (PATCH is used for updating existing data)
@router.patch("/documents/{document_id}", response_model=DocumentResponse)
def update_document(document_id: str, update_data: DocumentUpdate) -> dict:
    documents, audit_logs = get_collections()
    object_id = _parse_document_id(document_id)
    
    # Clean up the total_amount (ensure it is a float if possible)
    try:
        clean_amount = float(update_data.total_amount) if update_data.total_amount else 0.0
    except ValueError:
        clean_amount = 0.0

    clean_invoice_date = normalize_date_to_ddmmyyyy(update_data.invoice_date)

    # 3. Tell MongoDB to find the document and update its specific fields
    update_result = documents.update_one(
        {"_id": object_id},
        {"$set": {
            "extracted.vendor": update_data.vendor,
            "extracted.invoice_number": update_data.invoice_number,
            # Problem: the same date could be saved in different formats after user edits.
            # Fix: store only dd/mm/yyyy so the dashboard, review screen, and database all match.
            "extracted.invoice_date": clean_invoice_date,
            "extracted.total_amount": clean_amount,
            "workflow_status": "Approved" # Change status instantly!
        }}
    )

    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 4. Add an Audit Log so the company knows WHO changed the data and WHEN
    audit_logs.insert_one(
        audit.build_audit_event(
            document_id,
            "document_approved",
            "Document manually reviewed and approved by user."
        )
    )

    # Return the newly updated document
    updated_doc = documents.find_one({"_id": object_id})
    return {"document": serialize_document(updated_doc)}