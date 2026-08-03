# AI powered Invoice Intake and Review System

## What this project does
A user can paste text or upload a file. The system extracts key fields, validates them, calls an LLM for summary/classification, assigns a workflow status, and stores history.

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
- If `GEMINI_API_KEY` is empty, the backend will return a safe fallback summary.
- MongoDB must be running locally or the URI should point to a remote cluster.

## 🚨 About the "429 Error" (Quota Exceeded)

The app uses **Google Gemini API** which has **FREE TIER QUOTAS**:
- You can make about **15 requests per minute**
- You get about **1 million tokens per day** (tokens = words)

**If you get a 429 Error, it means:**
- You've exceeded your free tier quota
- OR You sent too many requests too quickly

**How to fix it:**
1. **Wait 60 seconds** and try again
2. **Check your quota**: Visit https://ai.dev/rate-limit
3. **Upgrade to Paid Plan**: Get unlimited access
4. **Don't worry**: Even if the API fails, our app returns a SAFE FALLBACK SUMMARY, so users still see something!
