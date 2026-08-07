import math
import re
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel

from app.db.mongo import get_documents_collection
from app.schemas.document import DocumentResponse
from app.services.storage import StoredUpload, store_upload
from app.services import llm, validation, workflow
from app.utils.dates import normalize_date_to_ddmmyyyy
from app.utils.serialization import parse_object_id, serialize_document

router = APIRouter()


SEARCH_FIELDS = (
    "metadata.title",
    "metadata.filename",
    "extracted.vendor",
    "extracted.invoice_number",
    "workflow_status",
)


def handle_upload(text: str | None, file: UploadFile | None, request: Request) -> tuple[str, str, dict, StoredUpload | None]:
    # The storage helper now handles both local files and Cloudinary, so this route only builds the shared metadata.
    metadata = {"filename": None, "file_url": None}
    raw_text = text or ""
    source = "unknown"
    stored_upload: StoredUpload | None = None

    if text:
        source = "text"

    if file:
        source = "file"
        stored_upload = store_upload(file, str(request.base_url))
        metadata["filename"] = stored_upload.filename or file.filename
        metadata["mime_type"] = stored_upload.mime_type
        metadata["file_url"] = stored_upload.file_url
        raw_text = text or ""

    if not text and not file:
        raise HTTPException(status_code=400, detail="Provide text or a file.")

    return raw_text, source, metadata, stored_upload


def _parse_document_id(raw_id: str):
    try:
        return parse_object_id(raw_id)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid document id.") from exc


def normalize_search_query(raw_search: str | None) -> str:
    if not raw_search:
        return ""
    return " ".join(raw_search.strip().split())


def _search_regex_parts(search_text: str) -> dict[str, str]:
    escaped_search = re.escape(search_text)
    return {
        "starts_with": rf"^{escaped_search}",
        "whole_word": rf"(^|[^A-Za-z0-9]){escaped_search}([^A-Za-z0-9]|$)",
        "contains": escaped_search,
    }


def _search_match_expression(field_path: str, regex_pattern: str) -> dict:
    return {
        "$regexMatch": {
            "input": {"$ifNull": [f"${field_path}", ""]},
            "regex": regex_pattern,
            "options": "i",
        }
    }


def _field_relevance_expression(field_path: str, search_patterns: dict[str, str]) -> dict:
    return {
        "$switch": {
            "branches": [
                {"case": _search_match_expression(field_path, search_patterns["starts_with"]), "then": 0},
                {"case": _search_match_expression(field_path, search_patterns["whole_word"]), "then": 1},
                {"case": _search_match_expression(field_path, search_patterns["contains"]), "then": 2},
            ],
            "default": 3,
        }
    }


@router.post("/documents", response_model=DocumentResponse)
def create_document(
    request: Request,
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> dict:
    raw_text, source, metadata, stored_upload = handle_upload(text, file, request)
    local_path = stored_upload.local_path if stored_upload else None
    now = datetime.now(timezone.utc)

    # Problem: text-only documents had no filename, so the dashboard had nothing human-friendly to show.
    # Fix: create a stable fallback title from the save date. This keeps the table readable even without a file.
    metadata["title"] = metadata.get("filename") or f"Raw Text Entry - {now.strftime('%d/%m/%Y')}"
    
    try:
        # The Gemini call needs the temporary local file path, but the frontend only needs the public URL.
        llm_output = llm.call_llm(raw_text, file_path=local_path)

        extracted = llm_output.extracted_data
        validation_result = validation.validate_fields(extracted)
        status = workflow.decide_status(validation_result, llm_output)

        documents = get_documents_collection()
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

        doc["_id"] = result.inserted_id
        return {"document": serialize_document(doc)}
    finally:
        if stored_upload and stored_upload.cleanup_path:
            stored_upload.cleanup_path.unlink(missing_ok=True)


@router.get("/documents")
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_direction: str = Query("desc"),
    status: str | None = Query(None),
) -> dict:
    documents = get_documents_collection()

    # Problem: loading every document at once made the table harder to read and impossible to page.
    # Fix: build a MongoDB filter, count the matches first, then fetch only the current page.
    filter_query: dict = {}
    normalized_search = normalize_search_query(search)

    if status:
        filter_query["workflow_status"] = status

    if normalized_search:
        search_text = re.escape(normalized_search)
        if search_text:
            filter_query["$or"] = [
                {"metadata.title": {"$regex": search_text, "$options": "i"}},
                {"metadata.filename": {"$regex": search_text, "$options": "i"}},
                {"extracted.vendor": {"$regex": search_text, "$options": "i"}},
                {"extracted.invoice_number": {"$regex": search_text, "$options": "i"}},
                {"workflow_status": {"$regex": search_text, "$options": "i"}},
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

    if normalized_search:
        search_patterns = _search_regex_parts(normalized_search)
        cursor = documents.aggregate(
            [
                {"$match": filter_query},
                {
                    "$addFields": {
                        "search_rank": {
                            "$min": [
                                _field_relevance_expression(field_path, search_patterns)
                                for field_path in SEARCH_FIELDS
                            ]
                        }
                    }
                },
                {"$sort": {"search_rank": 1, "created_at": -1, "_id": -1}},
                {"$skip": skip_amount},
                {"$limit": page_size},
                {"$project": {"text": 0, "search_rank": 0}},
            ]
        )
    else:
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
    documents = get_documents_collection()
    object_id = _parse_document_id(document_id)
    doc = documents.find_one({"_id": object_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document": serialize_document(doc)}




# 1. Define what data we expect from the frontend when a user clicks "Approve"
class DocumentUpdate(BaseModel):
    vendor: str
    invoice_number: str
    invoice_date: str
    total_amount: float | str | None = None

# 2. Create a PATCH route (PATCH is used for updating existing data)
@router.patch("/documents/{document_id}", response_model=DocumentResponse)
def update_document(document_id: str, update_data: DocumentUpdate) -> dict:
    documents = get_documents_collection()
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

    # Return the newly updated document
    updated_doc = documents.find_one({"_id": object_id})
    return {"document": serialize_document(updated_doc)}