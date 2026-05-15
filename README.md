# Tars

Tars is an AI agent framework designed to assist with various tasks, featuring a modular architecture with specialized experts. This project includes a Chinese language tutor implementation ("Pingo") that uses RAG (Retrieval-Augmented Generation) and TTS (Text-to-Speech) capabilities.

## Prerequisites

Before setting up the project, ensure you have the following installed:

1.  **Conda** (Miniconda or Anaconda) - [Installation Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
2.  **FFmpeg** - Required for audio playback.
    *   **Linux**: `sudo apt install ffmpeg`
    *   **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system PATH.

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Tars
```

### 2. Environment Setup

Create and activate the Conda environment using the provided `environment.yml` file.

```bash
conda env create -f environment.yml
conda activate agentes_ia
```

### 3. Database Setup

This project uses **Supabase** (hosted PostgreSQL with pgvector). No local database is needed. The connection details are stored in the `.env` file.

### 4. Configuration

Create a `.env` file in the root directory. You can use the following template:

```ini
# Database Connection (Supabase)
DB_HOST=aws-1-us-east-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.<your-project-ref>
DB_PASS=<your-db-password>

# API Keys
OPENAI_API_KEY=your_openai_api_key

# Google Cloud Credentials (for TTS)
# Option 1: Path to JSON file
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/your/google_credentials.json

# Option 2: JSON content as string (useful for deployment)
# GOOGLE_JSON_CREDENTIALS='{...}'
```

**Important**: 
- **Never commit the `.env` file** — it contains credentials.
- **Never commit Google service account keys** — `tars.json` and `*-service-account.json` are in `.gitignore`.

## Running the Application

### Local Development (Recommended)

The fastest way to develop. Auto-reloads on file changes — no Docker rebuild needed.

```bash
# Terminal 1 - Backend
conda activate agentes_ia
pip install -e .
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload \
  --ssl-keyfile=certs/key.pem --ssl-certfile=certs/cert.pem \
  --reload-dir api --reload-dir agents --reload-dir scripts

# Terminal 2 - Frontend
cd frontend && npm install && npm run dev
```

Backend runs at `https://localhost:8000`, frontend at `http://localhost:5173`.

### Docker (Deployment)

For production or when you want to run the full stack:

```bash
docker compose up --build -d  # backend + frontend + gitea + runner
```

## Troubleshooting

-   **Audio not playing**: 
    -   Ensure `ffmpeg` is installed and `ffplay` is available in your terminal path.
    -   Error: `FileNotFoundError: [Errno 2] No such file or directory: 'ffplay'` -> Install FFmpeg.
-   **Database Connection Error**:
    -   Verify the Supabase credentials in your `.env` file are correct.
    -   Check your Supabase project settings for the connection string.
