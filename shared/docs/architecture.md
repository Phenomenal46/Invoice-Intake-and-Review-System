# Architecture overview

### Data Flow

```
User Input (File or Text)
  ↓
[Frontend] Upload Form
  ↓
POST /api/documents
  ↓
[Backend] handle_upload()
  └─→ Store file (local or Cloudinary)
  ↓
llm.call_llm(text, file_path)
  └─→ Google Gemini API
  └─→ Parse JSON response
  └─→ Normalize dates (dd/mm/yyyy)
  ↓
validation.validate_fields(extracted_data)
  └─→ Check required fields
  └─→ Validate formats
  ↓
workflow.decide_status(validation, llm_output)
  └─→ Assign: Pending Review / Approved / Flagged
  ↓
[MongoDB] Insert document + metadata
  ↓
Return document to frontend
  ↓
[Frontend] Display Review Page
  ↓
User edits & clicks "Approve"
  ↓
PATCH /api/documents/{id}
  ↓
[MongoDB] Update extracted fields & status
  ↓
Show confirmation
```