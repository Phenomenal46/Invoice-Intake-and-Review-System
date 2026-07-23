import os
import math
import re
import shutil
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.db.mongo import get_collections
from app.schemas.audit import AuditEvent
from app.schemas.document import DocumentResponse
from app.services import audit, llm, validation, workflow
from app.utils.dates import normalize_date_to_ddmmyyyy
from app.utils.serialization import parse_object_id, serialize_document

router = APIRouter()


def handle_upload(text: str | None, file: UploadFile | None) -> tuple[str, str, dict]:
    # Problem: the old upload handler returned only when a file existed, so raw-text submissions had a broken path.
    # Fix: build the shared upload metadata first, then return once at the end for both file and text-only requests.
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
        metadata["filename"] = file.filename

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
    now = datetime.now(timezone.utc)

    # Problem: text-only documents had no filename, so the dashboard had nothing human-friendly to show.
    # Fix: create a stable fallback title from the save date. This keeps the table readable even without a file.
    metadata["title"] = metadata.get("filename") or f"Raw Text Entry - {now.strftime('%d/%m/%Y')}"
    
    # 1. Ask the AI to look at the file and text
    llm_output = llm.call_llm(raw_text, file_path=local_path)
    
    # 2. Grab the extracted data directly from the AI's brain!
    extracted = llm_output.extracted_data 
    
    # 3. Validate it using our existing rules
    validation_result = validation.validate_fields(extracted)
    status = workflow.decide_status(validation_result, llm_output)

    documents, audit_logs = get_collections()
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
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_direction: str = Query("desc"),
    status: str | None = Query(None),
) -> dict:
    documents, _ = get_collections()

    # Problem: loading every document at once made the table harder to read and impossible to page.
    # Fix: build a MongoDB filter, count the matches first, then fetch only the current page.
    filter_query: dict = {}

    if status:
        filter_query["workflow_status"] = status

    if search:
        search_text = re.escape(search.strip())
        if search_text:
            filter_query["$or"] = [
                {"metadata.title": {"$regex": search_text, "$options": "i"}},
                {"metadata.filename": {"$regex": search_text, "$options": "i"}},
                {"extracted.vendor": {"$regex": search_text, "$options": "i"}},
            ]

    sort_field_map = {
        "created_at": "created_at",
        "vendor": "extracted.vendor",
        "amount": "extracted.total_amount",
        "status": "workflow_status",
        "title": "metadata.title",
    }
    sort_field = sort_field_map.get(sort_by, "created_at")
    sort_order = 1 if sort_direction.lower() == "asc" else -1

    total_items = documents.count_documents(filter_query)
    total_pages = math.ceil(total_items / page_size) if total_items else 0
    current_page = min(page, total_pages) if total_pages else 1
    skip_amount = (current_page - 1) * page_size

    cursor = (
        documents.find(filter_query, {"text": 0})
        .sort(sort_field, sort_order)
        .skip(skip_amount)
        .limit(page_size)
    )

    items = [serialize_document(doc) for doc in cursor]
    return {
        "items": items,
        "page": current_page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": current_page < total_pages,
        "has_prev": current_page > 1 and total_pages > 0,
    }


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