# Architecture overview

- Frontend (React) sends documents to the backend and displays results.
- Backend (FastAPI) extracts fields, validates, calls LLM, decides workflow status, and stores records.
- MongoDB stores documents and audit logs.
