# VectorHire AI — Complete Windows Setup Guide

> This guide will take you from zero to a fully running VectorHire AI platform on a Windows machine.
> Follow every step in order. Estimated time: 20–40 minutes (most time is download/install).

>The most critical order of operations is:

<!-- 
-Install Python 3.11 + Node.js 20
-pip install -r requirements.txt (inside a venv)
-Add GEMINI_API_KEY to backend/.env
-python scripts/generate_resumes.py → makes the dummy PDFs
-python scripts/seed_vectordb.py → populates ChromaDB (without this, no jobs appear)
-uvicorn app.main:app --reload → start backend
-npm install && npm run dev → start frontend at http://localhost:3000
 -->

---

## Prerequisites Checklist

Before you start, make sure you have:
- [ ] Windows 10 or Windows 11
- [ ] Internet connection
- [ ] Your **Gemini API key** (from [Google AI Studio](https://aistudio.google.com/app/apikey))
- [ ] At least **8 GB RAM** (16 GB recommended)
- [ ] At least **5 GB free disk space**

---

## Part 1 — Install Core Tools

### 1.1 Install Python 3.11

1. Go to: https://www.python.org/downloads/release/python-3119/
2. Download **"Windows installer (64-bit)"**
3. Run the installer
4. **IMPORTANT:** Check "Add Python to PATH" at the bottom before clicking Install
5. Click "Install Now"
6. Verify: Open **Command Prompt** (`Win + R`, type `cmd`, press Enter)
   ```
   python --version
   ```
   You should see: `Python 3.11.x`

### 1.2 Install Node.js 20 LTS

1. Go to: https://nodejs.org/
2. Click **"LTS"** (recommended for most users)
3. Download and run the Windows installer
4. Accept all defaults, click Next/Install through the wizard
5. Verify in Command Prompt:
   ```
   node --version
   npm --version
   ```
   You should see `v20.x.x` and `10.x.x`

### 1.3 Install Git

1. Go to: https://git-scm.com/download/win
2. Download the latest Windows installer
3. Run it, accept all defaults
4. Verify:
   ```
   git --version
   ```

---

## Part 2 — Get the Project Files

If you received the project as a zip file:
1. Extract the zip to a folder, e.g. `C:\Projects\VectorHire AI\`

If you're cloning from a Git repo:
```
git clone <your-repo-url> "C:\Projects\VectorHire AI"
```

Open Command Prompt and navigate to the project folder:
```
cd "C:\Projects\VectorHire AI"
```

> **Keep this Command Prompt open** — you'll run commands from here throughout this guide.

---

## Part 3 — Backend Setup

### 3.1 Create a Python Virtual Environment

```
cd "C:\Projects\VectorHire AI\backend"
python -m venv venv
```

This creates an isolated Python environment in `backend\venv\`

### 3.2 Activate the Virtual Environment

```
venv\Scripts\activate
```

Your prompt should change to show `(venv)` at the start. You must do this every time you open a new terminal to work on the backend.

### 3.3 Install Python Dependencies

```
pip install --upgrade pip
pip install -r requirements.txt
```

This will download ~2–3 GB of packages including PyTorch and the embedding model. **This will take 5–15 minutes** depending on your internet speed.

If you see an error about `Microsoft C++ Build Tools`, install them from:
https://visualstudio.microsoft.com/visual-cpp-build-tools/
(Select "C++ build tools" workload → Install)

### 3.4 Configure Environment Variables

```
copy .env.example .env
```

Now open `.env` in Notepad:
```
notepad .env
```

Replace `your_gemini_api_key_here` with your actual Gemini API key:
```
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```

Save and close Notepad.

### 3.5 Generate Dummy Resume PDFs

```
python ..\scripts\generate_resumes.py
```

This creates 5 realistic PDF resumes in `backend\app\data\resumes\`
You should see:
```
✓ Generated: resume_1_alex_chen.pdf  (Alex Chen)
✓ Generated: resume_2_priya_sharma.pdf  (Priya Sharma)
...
```

### 3.6 Seed the Vector Database

**This is required before the backend will return any results.**

```
python ..\scripts\seed_vectordb.py
```

On first run, this downloads the embedding model (~90 MB). Then it embeds all 20 jobs and stores them in ChromaDB.

Expected output:
```
✓ Ingested 20 jobs → ~50 document chunks in ChromaDB
Ready! You can now start the backend server.
```

If it asks `Re-seed? [y/N]`, type `y` and press Enter.

### 3.7 Test the Pipeline

```
python ..\scripts\test_pipeline.py
```

Expected output:
```
[1/4] Testing ChromaDB...
  OK: 50 document chunks in jobs collection
[2/4] Testing embedding model...
  OK: Embedding generated (384 dimensions)
[3/4] Testing semantic job search...
  → AI Backend Engineering Intern at NeuralStack Labs (score: 0.847)
  OK: 3 jobs retrieved
[4/4] Testing Gemini LLM connectivity...
  Response: VectorHire AI is ready!
  OK: LLM responding

Results:
  PASS chromadb
  PASS embeddings
  PASS search
  PASS llm

✓ All tests passed!
```

If any test fails, see **Troubleshooting** at the bottom.

### 3.8 Start the Backend Server

```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Embedding model ready
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Leave this terminal open.**

Open your browser and go to: http://localhost:8000/docs

You should see the FastAPI Swagger UI. The backend is running!

---

## Part 4 — Frontend Setup

Open a **new** Command Prompt window (leave the backend terminal running).

```
cd "C:\Projects\VectorHire AI\frontend"
```

### 4.1 Configure Frontend Environment

```
copy .env.local.example .env.local
```

The default value `http://localhost:8000/api/v1` is correct — no changes needed unless your backend runs on a different port.

### 4.2 Install Node.js Dependencies

```
npm install
```

This downloads the Next.js and React packages into `frontend\node_modules\`. Takes 1–3 minutes.

### 4.3 Start the Frontend Development Server

```
npm run dev
```

You should see:
```
  ▲ Next.js 15.0.4
  - Local:        http://localhost:3000
  - Ready in 2.3s
```

**Leave this terminal open.**

Open your browser and go to: http://localhost:3000

You should see the VectorHire AI home page!

---

## Part 5 — Test the Full Application

Now both servers are running. Let's test the full pipeline:

### 5.1 Test Job Search (no resume needed)

1. Click **"Job Search"** in the navigation
2. Click one of the sample query chips, e.g. "AI backend intern FastAPI LangGraph"
3. You should see a list of matching job cards with similarity scores

### 5.2 Test Full Resume Analysis

1. Click **"Analyze Resume"** in the navigation
2. Click the upload area and select one of the generated PDFs from:
   `backend\app\data\resumes\resume_1_alex_chen.pdf`
3. Optionally add a search focus like "remote AI internship"
4. Click **"Analyze with AI"**
5. Wait 30–60 seconds for the full pipeline to run
6. You should see:
   - AI Career Summary
   - Top Skills to Learn
   - Improvement Roadmap
   - Ranked Job Matches with explanations

---

## Part 6 — Daily Workflow

Every time you want to run VectorHire AI:

**Terminal 1 — Backend:**
```
cd "C:\Projects\VectorHire AI\backend"
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```
cd "C:\Projects\VectorHire AI\frontend"
npm run dev
```

Then open: http://localhost:3000

---

## Part 7 — API Documentation

The backend has interactive API docs:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Key endpoints:
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/health` | GET | Check all services status |
| `/api/v1/resume/upload` | POST | Parse a resume PDF |
| `/api/v1/resume/analyze` | POST | Full analysis pipeline |
| `/api/v1/search/jobs` | POST | Semantic job search |
| `/api/v1/search/jobs/sample` | GET | Quick test — get sample jobs |

---

## Troubleshooting

### "pip install failed" / "Microsoft C++ Build Tools required"
Install build tools from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
Select "Desktop development with C++" → Install → Re-run `pip install -r requirements.txt`

### "GEMINI_API_KEY not set" or "401 Unauthorized"
- Make sure your `.env` file exists in the `backend\` folder
- Make sure your API key starts with `AIza...`
- Get a free key at: https://aistudio.google.com/app/apikey

### "ChromaDB is empty" or "No jobs found"
Run the seeder:
```
cd backend
venv\Scripts\activate
python ..\scripts\seed_vectordb.py
```

### "Embedding model downloading every time"
The model should cache after first download. Check that `~/.cache/huggingface/` exists.
If downloads keep failing, try:
```
pip install huggingface-hub
huggingface-cli download sentence-transformers/all-MiniLM-L6-v2
```

### Frontend shows "Failed to fetch" or network errors
Make sure the backend is running (`uvicorn` terminal is active).
Check that CORS is configured — the backend allows `http://localhost:3000` by default.

### "ModuleNotFoundError: No module named 'app'"
Make sure you're running Python commands from the `backend\` directory with the `(venv)` active.

### Port already in use
- Backend port 8000: `netstat -ano | findstr :8000` then `taskkill /PID <pid> /F`
- Frontend port 3000: `netstat -ano | findstr :3000` then `taskkill /PID <pid> /F`

### Reset everything and start fresh
```
cd backend
venv\Scripts\activate
python ..\scripts\reset_db.py
python ..\scripts\seed_vectordb.py
```

---

## Useful Scripts

| Script | Purpose | Run from |
|--------|---------|----------|
| `scripts/generate_resumes.py` | Generate 5 dummy PDF resumes | `backend\` |
| `scripts/seed_vectordb.py` | Populate ChromaDB with jobs | `backend\` |
| `scripts/test_pipeline.py` | Test all components | `backend\` |
| `scripts/reset_db.py` | Wipe ChromaDB (requires re-seed) | `backend\` |
| `scripts/ingest_jobs.py` | Add new TXT job files to jobs.json | `backend\` |

---

## Project Structure Quick Reference

```
VectorHire AI/
├── backend/           ← Python FastAPI + LangGraph backend
│   ├── app/
│   │   ├── graph/     ← LangGraph workflow (5 nodes)
│   │   ├── rag/       ← ChromaDB + embeddings
│   │   ├── llm/       ← Gemini API integration
│   │   ├── services/  ← Business logic
│   │   └── data/      ← Job data + ChromaDB storage
│   ├── .env           ← Your API keys (create this from .env.example)
│   └── requirements.txt
├── frontend/          ← Next.js 15 frontend
│   ├── app/           ← Pages (/, /upload, /dashboard)
│   └── components/    ← React components
├── scripts/           ← Setup and utility scripts
└── docs/              ← Architecture documentation
```
