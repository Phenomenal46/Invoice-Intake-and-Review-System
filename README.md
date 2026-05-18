# AI Document Workflow Mini-System

## What this project does
A user can paste text or upload a file. The system extracts key fields, validates them, calls an LLM for summary/classification, assigns a workflow status, and stores history plus audit logs.

## Tech stack
- Backend: FastAPI
- Frontend: React (Vite)
- Database: MongoDB

## Quick start

### Backend
1. Create a virtual environment (optional but recommended).
2. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy env:
   ```bash
   copy .env.example .env
   ```
4. Start API:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend
1. Install deps:
   ```bash
   npm install
   ```
2. Copy env:
   ```bash
   copy .env.example .env
   ```
3. Start app:
   ```bash
   npm run dev
   ```

## Notes
- If `LLM_API_KEY` is empty, the backend will return a safe fallback summary.
- MongoDB must be running locally or the URI should point to a remote cluster.
