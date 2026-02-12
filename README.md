# Tars

Tars is an AI agent framework designed to assist with various tasks, featuring a modular architecture with specialized experts. This project includes a Chinese language tutor implementation ("Pingo") that uses RAG (Retrieval-Augmented Generation) and TTS (Text-to-Speech) capabilities.

## Prerequisites

Before setting up the project, ensure you have the following installed:

1.  **Conda** (Miniconda or Anaconda) - [Installation Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
2.  **FFmpeg** - Required for audio playback.
    *   **Linux**: `sudo apt install ffmpeg`
    *   **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your system PATH.
3.  **Database**:
    *   **Docker Desktop** (Recommended for easiest setup) - [Get Docker](https://www.docker.com/products/docker-desktop/)
    *   **OR**
    *   **PostgreSQL 16+** with **pgvector** extension (Manual setup instructions below).

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

You have two options for setting up the database. **Option A (Docker)** is recommended for simplicity, but **Option B (Manual)** is fully supported if you prefer not to use Docker.

#### Option A: Docker (Recommended)

If you have Docker installed, you can spin up the database with a single command. This automatically configures PostgreSQL with the `pgvector` extension.

1.  Start the database container:
    ```bash
    docker-compose up -d db
    ```
2.  The database will be available at `localhost:5433`.

#### Option B: Manual Installation (No Docker)

If you cannot or do not want to use Docker, follow these steps to set up PostgreSQL and `pgvector` manually.

**Linux:**

1.  **Install PostgreSQL 16**:
    ```bash
    sudo apt install postgresql-16
    ```
2.  **Install pgvector**:
    ```bash
    # You might need to install build dependencies first
    sudo apt install postgresql-server-dev-16 build-essential
    
    # Install pgvector (example for Debian/Ubuntu)
    sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
    sudo apt install postgresql-16-pgvector
    ```
3.  **Create User and Database**:
    ```bash
    sudo -u postgres psql
    
    # Inside psql shell:
    CREATE USER lancelot WITH PASSWORD '9474609';
    CREATE DATABASE chinese_tutor_db OWNER lancelot;
    \q
    ```

**Windows:**

1.  **Install PostgreSQL**: Download and install PostgreSQL 16 from the [official website](https://www.postgresql.org/download/windows/).
2.  **Install pgvector**:
    *   The easiest way on Windows is to use the official installer if available or follow the instructions on the [pgvector GitHub repository](https://github.com/pgvector/pgvector).
    *   **Note**: `pgvector` support on Windows can be complex to build from source. Using the [Postgres.app](https://postgresapp.com/) (Mac) or a pre-packaged installer is recommended. 
    *   If installing from source is required: requires Visual Studio C++ build tools.
3.  **Create Database**: Use **pgAdmin 4** (installed with PostgreSQL) to create a new database named `chinese_tutor_db`.

### 4. Configuration

Create a `.env` file in the root directory. You can use the following template:

```ini
# Database Connection
DB_HOST=localhost
DB_PORT=5433          # Use 5433 for Docker, likely 5432 for manual install
DB_NAME=chinese_tutor_db
DB_USER=lancelot
DB_PASS=9474609

# API Keys
OPENAI_API_KEY=your_openai_api_key

# Google Cloud Credentials (for TTS)
# Option 1: Path to JSON file
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/your/google_credentials.json

# Option 2: JSON content as string (useful for deployment)
# GOOGLE_JSON_CREDENTIALS='{...}'
```

**Important**: 
- If using **Docker**, set `DB_PORT=5433`.
- If using **Manual Install**, functionality usually defaults to `DB_PORT=5432`. Check your PostgreSQL configuration.

### 5. Database Initialization

After setting up the database and `.env` file, you need to create the required tables.

Run the provided SQL script using `psql` or a database tool (like pgAdmin or DBeaver), or simply copy-paste the commands:

**Using psql:**
```bash
psql -h localhost -p 5433 -U lancelot -d chinese_tutor_db -f setup_db.sql
```
*(Replace `5433` with `5432` if using manual installation)*

## Execution

To run the application:

1.  Ensure your Conda environment is active:
    ```bash
    conda activate agentes_ia
    ```

2.  Run the main agent node:
    ```bash
    python agents/brain/nodes.py
    ```

## Troubleshooting

-   **Audio not playing**: 
    -   Ensure `ffmpeg` is installed and `ffplay` is available in your terminal path.
    -   Error: `FileNotFoundError: [Errno 2] No such file or directory: 'ffplay'` -> Install FFmpeg.
-   **Database Connection Error**:
    -   Check if the database is running (`docker ps` or `sudo service postgresql status`).
    -   Verify the `DB_PORT` in your `.env` file matches your setup (Docker maps to **5433**, standard install uses **5432**).
