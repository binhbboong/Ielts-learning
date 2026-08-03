# IELTS Learning Dashboard

Angular frontend + FastAPI backend + PostgreSQL for a single IELTS learner.

The local product includes the 180-day study plan, mistake and vocabulary review,
Reading/Listening progress tracking, Writing and Speaking coaches, authentication, and a
complete JSON data export.

## Local prerequisites

- Node.js and npm
- Python 3.10+
- Docker Desktop (for PostgreSQL)

## First-time setup

From the repository root:

```powershell
docker compose up -d postgres
Copy-Item backend/.env.example backend/.env
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
Push-Location backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.db.seed_study_plan
Pop-Location
npm install
```

The example local password is `changeme123`. Replace the example password hash and session
secret before using any non-local environment.

The example environment uses `AI_PROVIDER=local`, a zero-cost deterministic provider that keeps
both coach flows runnable and labels its output as demo feedback. For genuine AI evaluation
with OpenAI, set `AI_PROVIDER=openai`, provide `OPENAI_API_KEY`, and optionally override
`OPENAI_MODEL`.

Speaking transcription also defaults to a local demo adapter because the AI-SDLC plan leaves
the external speech-to-text vendor intentionally swappable. The recording, 120-second cap,
step-tracked processing, retry paths, transcript persistence, and feedback flow all run locally;
replace `get_speech_to_text()` in
`backend/app/services/speech_to_text.py` when a production vendor is selected.

## Run locally

Start the backend in one terminal:

```powershell
Push-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Start the frontend in another terminal:

```powershell
npm start
```

Open [http://localhost:4200](http://localhost:4200). Angular proxies `/api` requests to the
backend at `http://127.0.0.1:8001`.

The backend API is also available at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

## Verify

```powershell
Push-Location backend
.\.venv\Scripts\python.exe -m pytest -q
Pop-Location
npx ng test --watch=false --browsers=ChromeHeadless
npm run build
```
