# Tars

AI agent framework with Chinese language tutor ("Pingo"), RAG + TTS capabilities.

## Stack

- **Backend**: Python 3.12, FastAPI, LangChain, LangGraph, pgvector
- **Frontend**: React 19, TypeScript, Vite 7, Tailwind CSS 4
- **DB**: PostgreSQL + pgvector (hosted on Supabase)
- **Env Manager**: Conda (environment.yml)

## Local Development (Recommended)

Database is hosted on Supabase — no local DB needed. Develop locally with auto-reload:

```bash
# Terminal 1 - Backend
conda activate agentes_ia
pip install -e .
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload \
  --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem \
  --reload-dir api --reload-dir agents --reload-dir scripts

# Terminal 2 - Frontend
cd frontend && npm run dev
```

Backend available at `https://localhost:8000`, frontend at `http://localhost:5173`.

## Docker (Deployment Only)

```bash
docker compose up --build -d  # backend + frontend + gitea + runner
```

## Required Setup

1. **FFmpeg**: Required for audio playback (`apt install ffmpeg` or equivalent)
2. **.env file** at root (credentials in `.env`, not committed):
   ```
   DB_HOST=aws-1-us-east-1.pooler.supabase.com
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres.pysaqdfijktldrzjlqsm
   DB_PASS=...
   OPENAI_API_KEY=...
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
   ```
3. **Google Cloud credentials** (for TTS):
   - Option A: Set `GOOGLE_JSON_CREDENTIALS` env var with the JSON content of your service account key
   - Option B: Set `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to a JSON key file on disk
   - **Never commit service account keys to the repository** — `tars.json` and `*-service-account.json` are in `.gitignore`

## Architecture

- `agents/brain/nodes.py` - Main agent node entrypoint (LangGraph workflow)
- `agents/brain/` - Brain modules: schema, chains, nodes, context builders
- `agents/RAG/` - Retrieval-augmented generation
- `agents/dataBase/` - Database queries and user management
- `api/` - FastAPI app package (routes, models, app factory)
- `frontend/` - Separate npm project