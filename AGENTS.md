# Tars

AI agent framework with Chinese language tutor ("Pingo"), RAG + TTS capabilities.

## Stack

- **Backend**: Python 3.12, FastAPI, LangChain, LangGraph, pgvector
- **Frontend**: React 19, TypeScript, Vite 7, Tailwind CSS 4
- **DB**: PostgreSQL + pgvector (port 5433 in Docker, 5432 manual)
- **Env Manager**: Conda (environment.yml)

## Commands

```bash
# Backend - requires conda env activated
conda activate agentes_ia
python agents/brain/nodes.py

# Frontend
cd frontend && npm install && npm run dev

# Database (Docker)
docker-compose up -d db  # available at localhost:5433

## Required Setup

1. **FFmpeg**: Required for audio playback (`apt install ffmpeg` or equivalent)
2. **.env file** at root:
   ```
   DB_HOST=localhost
   DB_PORT=5433          # 5433 for Docker, 5432 for manual
   DB_NAME=chinese_tutor_db
   DB_USER=lancelot
   DB_PASS=9474609
   OPENAI_API_KEY=...
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
   ```
3. **Google Cloud credentials** (for TTS):
   - Option A: Set `GOOGLE_JSON_CREDENTIALS` env var with the JSON content of your service account key
   - Option B: Set `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to a JSON key file on disk
   - **Never commit service account keys to the repository** — `tars.json` and `*-service-account.json` are in `.gitignore`

## Architecture

- `agents/brain/nodes.py` - Main agent node entrypoint
- `agents/RAG/` - Retrieval-augmented generation
- `agents/dataBase/` - Database queries and user management
- `api.py` - FastAPI app (not used directly, runs in Docker)
- `frontend/` - Separate npm project

## Docker Services

```bash
docker-compose up -d  # backend + frontend + gitea + runner
```