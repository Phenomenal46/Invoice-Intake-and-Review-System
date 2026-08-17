# Invoice Intake and Review System

**An AI-powered full-stack application for extracting, validating, and reviewing invoice data with automated workflow assignment.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![JavaScript](https://img.shields.io/badge/javascript-ES6%2B-yellow)
![MongoDB](https://img.shields.io/badge/mongodb-latest-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## 📋 Overview

A full-stack web application that streamlines invoice processing by automating data extraction, validation, and review workflows. Users can upload invoices as files (PDF, PNG, JPG) or paste raw text. The system extracts key fields (vendor, invoice number, date, amount), validates them against business rules, uses **Google Gemini API** for intelligent summaries and classification, and automatically assigns a workflow status (Pending Review, Approved, Flagged for Manual Review). All documents and changes are stored in MongoDB for audit trails and history.

**Ideal for:** Entry-level portfolio projects, learning full-stack development, understanding AI integration, or as a foundation for document processing workflows.

---

## 🎬 Demo & Screenshots

*[Add screenshots here]*

**To add your own demo:**
1. Record a short video or GIF of the upload → extraction → review workflow
2. Add the asset to a `docs/` folder in the repo
3. Replace the placeholder below with:
   ```markdown
   ![Demo GIF](docs/demo.gif)
   ```
   Or for live demo:
   ```markdown
   **[Live Demo](https://invoice-intake-and-review-system.vercel.app)**
   ```

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Project Architecture](#-project-architecture)
- [Roadmap](#-roadmap--future-improvements)
- [License](#-license)
- [Contact](#-contact--author)

---

## ✨ Features

- **📤 Multi-format Input:** Upload PDF, PNG, JPG files or paste raw invoice text
- **🤖 AI-Powered Extraction:** Google Gemini API extracts vendor, invoice number, date, and amount
- **✅ Smart Validation:** Business rule validation with detailed feedback on data quality
- **📊 Intelligent Classification:** Automatic document classification (Invoice, Receipt, etc.) with confidence scores
- **⚠️ Risk Detection:** Identifies potential issues (missing fields, format anomalies, etc.)
- **🔄 Workflow Assignment:** Automatically assigns status (Pending Review, Approved, Flagged) based on validation
- **📝 Editable Review:** Users can correct extracted data before final approval
- **🔍 Search & Filter:** Full-text search across documents by title, vendor, invoice number, or status
- **📄 Pagination:** Efficient browsing with configurable page sizes
- **💾 Audit Trail:** Complete history of all documents and changes in MongoDB
- **☁️ Cloud Storage:** Supports both local file storage and Cloudinary for production deployments
- **🔐 Secure API:** CORS-protected endpoints with environment-based configuration
- **⚡ Fallback Logic:** Graceful degradation if Gemini API quota is exceeded

---

## 🛠️ Tech Stack

### Frontend
- **React** 18.3+ — UI component library
- **Vite** 5.4+ — Fast build tool & dev server
- **Tailwind CSS** 4.3+ — Utility-first styling with `@tailwindcss/vite` plugin
- **React Router** 7.18+ — Client-side routing
- **PDF.js** 6.2+ — PDF rendering in the browser
- **React Hot Toast** 2.5+ — Toast notifications

### Backend
- **FastAPI** 0.111+ — Modern, fast web framework
- **Uvicorn** 0.30+ — ASGI server
- **Pydantic** 2.13+ — Data validation & settings management
- **PyMongo** 4.7+ — MongoDB driver
- **Google Generative AI** 2.14+ — Gemini API integration
- **Cloudinary** 1.41+ — Cloud file storage (optional, production)
- **Python Multipart** 0.0.9 — Form data parsing

### Database
- **MongoDB** — NoSQL document store for invoices, extracted fields, validation results, and workflow status

### Tools & DevOps
- **Python Dotenv** — Environment variable management
- **HTTPX** — Async HTTP client
- **Git / GitHub** — Version control
- **Vercel** — Frontend deployment (optional)
- **Render** — Backend deployment (optional)

---

## 📁 Project Structure

```
Invoice-Intake-and-Review-System/
├── frontend/                          # React + Vite frontend
│   ├── public/                        # Static assets
│   ├── src/
│   │   ├── pages/                     # React pages (Upload.jsx, Dashboard.jsx, ReviewDocument.jsx, etc.)
│   │   ├── components/                # Reusable React components
│   │   ├── api.js                     # API client functions (submitDocument, fetchHistory, etc.)
│   │   ├── App.jsx                    # Main app routing
│   │   ├── main.jsx                   # React entry point
│   │   └── styles.css                 # Global styles
│   ├── index.html                     # HTML template
│   ├── vite.config.js                 # Vite configuration
│   ├── package.json                   # Frontend dependencies
│   └── .env.example                   # Environment template
│
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── main.py                    # FastAPI app setup, CORS, static file mounting
│   │   ├── config.py                  # Settings & environment variables (Pydantic)
│   │   ├── api/
│   │   │   ├── router.py              # Main API router aggregation
│   │   │   ├── documents.py           # Document CRUD routes (POST, GET, PATCH)
│   │   │   └── health.py              # Health check route
│   │   ├── db/
│   │   │   └── mongo.py               # MongoDB client & connection helpers
│   │   ├── services/
│   │   │   ├── llm.py                 # Google Gemini API wrapper & fallback logic
│   │   │   ├── validation.py          # Field validation rules
│   │   │   ├── workflow.py            # Workflow status assignment logic
│   │   │   └── storage.py             # File storage (local or Cloudinary)
│   │   ├── schemas/
│   │   │   └── document.py            # Pydantic models for documents, validation, LLM output
│   │   └── utils/
│   │       ├── dates.py               # Date normalization (dd/mm/yyyy format)
│   │       └── serialization.py       # MongoDB ObjectId serialization
│   ├── uploads/                       # Local file uploads (created at runtime)
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                   # Environment template
│   └── .gitkeep                       # Ensures uploads/ is tracked
│
├── .gitignore                         # Ignores node_modules, .env, __pycache__, uploads/*
├── README.md                          # This file
└── package.json                       # Root package.json (optional, for shared dependencies)
```

---

## 📋 Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** & **npm 9+** (for frontend)
- **MongoDB 4.4+** (local instance or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) free tier)
- **Google Gemini API Key** (free tier available at [Google AI Studio](https://aistudio.google.com/app/apikey))
- **Git** (for cloning the repository)

### Optional

- **Cloudinary Account** (if using cloud file storage in production)
- **Vercel Account** (for frontend deployment)
- **Render Account** (for backend deployment)

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Phenomenal46/Invoice-Intake-and-Review-System.git
cd Invoice-Intake-and-Review-System
```

### 2. Backend Setup

#### Create a Python Virtual Environment

```bash
cd backend
python -m venv venv
```

**Activate the virtual environment:**

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

- **Windows (PowerShell):**
  ```bash
  .\venv\Scripts\Activate.ps1
  ```

- **Windows (Command Prompt):**
  ```bash
  venv\Scripts\activate.bat
  ```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment Variables

```bash
copy .env.example .env
# OR on macOS/Linux:
cp .env.example .env
```

Then open `backend/.env` and fill in:
- `GEMINI_API_KEY` — Get from [Google AI Studio](https://aistudio.google.com/app/apikey)
- `MONGODB_URI` — Use `mongodb://localhost:27017` for local development
- `CORS_ORIGINS` — Should include your frontend URL (default: `http://localhost:5173`)

#### Start MongoDB (if running locally)

```bash
mongod
# Or use MongoDB Atlas for a free cloud database
```

#### Start the Backend Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. API docs: `http://localhost:8000/docs` (Swagger UI).

---

### 3. Frontend Setup

#### Navigate to Frontend Directory

```bash
cd frontend
```

#### Install Node Dependencies

```bash
npm install
```

#### Configure Environment Variables

```bash
copy .env.example .env
# OR on macOS/Linux:
cp .env.example .env
```

Then open `frontend/.env` and set:
- `VITE_API_URL=http://localhost:8000/api` (for local development)

#### Start the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## 🔧 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `MONGODB_URI` | ✅ | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB` | ❌ | `doc_workflow` | Database name |
| `GEMINI_API_KEY` | ❌ | (empty) | Google Gemini API key; if empty, app uses safe fallback |
| `LLM_MODEL` | ❌ | `gemini-2.5-flash` | LLM model to use (fast, good for beginners) |
| `LLM_TIMEOUT_SECONDS` | ❌ | `20` | Timeout for LLM requests |
| `CORS_ORIGINS` | ❌ | `http://localhost:5173,https://invoice-intake-and-review-system.vercel.app` | Comma-separated allowed frontend origins |
| `STORAGE_MODE` | ❌ | `local` | File storage mode: `local` or `cloudinary` |
| `CLOUDINARY_CLOUD_NAME` | ❌ | (empty) | Cloudinary cloud name (required if `STORAGE_MODE=cloudinary`) |
| `CLOUDINARY_API_KEY` | ❌ | (empty) | Cloudinary API key (required if `STORAGE_MODE=cloudinary`) |
| `CLOUDINARY_API_SECRET` | ❌ | (empty) | Cloudinary API secret (required if `STORAGE_MODE=cloudinary`) |

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_URL` | ✅ | (none) | Backend API URL; must be set, no fallback to localhost in production |

---

## 💻 Usage

### Running in Development

1. **Terminal 1 — Backend:**
   ```bash
   cd backend
   source venv/bin/activate  # or .\venv\Scripts\activate on Windows
   uvicorn app.main:app --reload
   ```

2. **Terminal 2 — Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open in Browser:**
   Navigate to `http://localhost:5173`

### Running in Production

1. **Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   gunicorn app.main:app -w 4 -b 0.0.0.0:8000
   # Or use Uvicorn with multiple workers
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Frontend:**
   ```bash
   cd frontend
   npm run build
   # Serve the dist/ folder with your hosting provider (Vercel, Netlify, etc.)
   ```

### Using the Application

1. **Upload an Invoice:**
   - Paste raw invoice text OR upload a file (PDF, PNG, JPG)
   - Click "Process"

2. **Review Extracted Data:**
   - The system displays extracted fields (vendor, invoice number, date, amount)
   - Review the AI-generated summary and classification
   - Check for any flagged risks

3. **Approve or Edit:**
   - Edit any field if needed
   - Click "Approve" to finalize

4. **View History:**
   - Browse all processed documents
   - Search by vendor, invoice number, or status
   - Sort by date, amount, or vendor

---

## 🔌 API Endpoints

### Documents API

All endpoints require `Content-Type: application/json` or `multipart/form-data` (for file uploads).

#### Create Document

```
POST /api/documents
```

**Request:**
- `text` (optional, form field) — Raw invoice text
- `file` (optional, file upload) — Invoice file (PDF, PNG, JPG, JPEG)

**Response:**
```json
{
  "document": {
    "id": "507f1f77bcf86cd799439011",
    "created_at": "2026-08-17T12:30:00Z",
    "source": "file",
    "metadata": {
      "title": "Invoice-2024.pdf",
      "filename": "Invoice-2024.pdf",
      "file_url": "http://localhost:8000/uploads/...",
      "mime_type": "application/pdf"
    },
    "extracted": {
      "vendor": "Acme Corp",
      "invoice_number": "INV-2024-001",
      "invoice_date": "15/08/2026",
      "total_amount": 1500.00
    },
    "validation": {
      "is_valid": true,
      "errors": [],
      "warnings": []
    },
    "llm": {
      "summary": "Invoice from Acme Corp...",
      "classification": "Invoice",
      "confidence": 0.95,
      "key_points": [...],
      "risks": [...]
    },
    "workflow_status": "Pending Review"
  }
}
```

#### List Documents

```
GET /api/documents?page=1&page_size=5&search=&sort_by=created_at&sort_direction=desc
```

**Query Parameters:**
- `page` (default: `1`) — Page number
- `page_size` (default: `5`, max: `100`) — Items per page
- `search` (optional) — Search term (searches title, vendor, invoice number, status)
- `sort_by` (default: `created_at`) — Sort field: `created_at`, `vendor`, `amount`, `status`, `title`
- `sort_direction` (default: `desc`) — `asc` or `desc`
- `status` (optional) — Filter by workflow status

**Response:**
```json
{
  "items": [...],
  "page": 1,
  "page_size": 5,
  "total_items": 42,
  "total_pages": 9,
  "has_next": true,
  "has_prev": false
}
```

#### Get Document by ID

```
GET /api/documents/{document_id}
```

**Response:** Single document object (same structure as Create Document response)

#### Update Document (Approve)

```
PATCH /api/documents/{document_id}
```

**Request:**
```json
{
  "vendor": "Acme Corp",
  "invoice_number": "INV-2024-001",
  "invoice_date": "15/08/2026",
  "total_amount": 1500.00
}
```

**Response:** Updated document with `workflow_status: "Approved"`

### Health Check

```
GET /api/health
```

**Response:**
```json
{ "status": "ok" }
```

---

## 🏗️ Project Architecture

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

### Folder-by-Folder Explanation

#### `backend/app/api/`
Contains route handlers:
- `documents.py` — CRUD operations for invoices (Create, Read, Update)
- `health.py` — Health check endpoint
- `router.py` — Aggregates all routes under `/api` prefix

#### `backend/app/services/`
Business logic:
- `llm.py` — Integrates with Google Gemini, handles API fallbacks
- `validation.py` — Validates extracted fields against rules
- `workflow.py` — Determines workflow status based on validation & LLM confidence
- `storage.py` — Manages local and Cloudinary file uploads

#### `backend/app/db/`
Data access:
- `mongo.py` — MongoDB client management, lazy initialization, collection helpers

#### `backend/app/schemas/`
Data models (Pydantic):
- `document.py` — Defines structures for documents, extracted fields, validation results, LLM output

#### `backend/app/utils/`
Utilities:
- `dates.py` — Converts dates to `dd/mm/yyyy` format consistently
- `serialization.py` — Converts MongoDB ObjectId to string for JSON responses

#### `frontend/src/pages/`
Full-page React components:
- `Upload.jsx` — File/text upload form
- `Dashboard.jsx` — Document history & search
- `ReviewDocument.jsx` — Review & edit extracted data

#### `frontend/src/components/`
Reusable UI components (e.g., forms, tables, modals)

---

## 🚀 Roadmap & Future Improvements

- [ ] **Batch Processing** — Upload multiple invoices at once for bulk processing
- [ ] **Email Integration** — Auto-send approved invoices to vendor email or accounting system
- [ ] **Advanced OCR** — Switch from Gemini to specialized OCR for better extraction accuracy on complex layouts
- [ ] **User Authentication** — Add login/roles (Admin, Reviewer, Viewer) for multi-user workflows
- [ ] **Webhook Support** — Notify external systems (ERPs, accounting software) on document approval
- [ ] **Dark Mode** — Add dark theme toggle for accessibility
- [ ] **Duplicate Detection** — Flag potential duplicate invoices based on vendor + amount
- [ ] **Export Reports** — Generate PDF or CSV reports of processed invoices for audit trails
- [ ] **Retry Logic** — Auto-retry LLM calls on transient failures (429, 5xx errors)
- [ ] **Docker Compose** — Add docker-compose.yml for one-command local setup with MongoDB

---

## 📄 License

This project is licensed under the **MIT License**. See the `LICENSE` file (or create one) for details.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions...
```

---

## 👋 Contact & Author

**Developer:** [Your Name]

- **Email:** yourname@example.com
- **LinkedIn:** [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)
- **GitHub:** [@Phenomenal46](https://github.com/Phenomenal46)
- **Portfolio:** [yourportfolio.com](https://yourportfolio.com)

### Questions or Issues?

- Open a [GitHub Issue](https://github.com/Phenomenal46/Invoice-Intake-and-Review-System/issues) for bugs or feature requests
- Reach out via email for freelance or collaboration inquiries
- Check [Discussions](https://github.com/Phenomenal46/Invoice-Intake-and-Review-System/discussions) for Q&A

---

**Built with ❤️ using React, FastAPI, and MongoDB.**
