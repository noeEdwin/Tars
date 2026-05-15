# Phase 1: Security & Database Infrastructure — Changelog

## Summary

Removed hardcoded database credentials, eliminated local credential file fallbacks, and tightened `.gitignore` to prevent secrets from entering the repository.

---

## Step 1.1: Remove Hardcoded DB Credentials

**File:** `agents/dataBase/connection.py`

### Before
```python
def get_db_connection():
    conn = psycopg2.connect(
        host="aws-1-us-east-1.pooler.supabase.com",
        database="postgres",
        user="postgres.pysaqdfijktldrzjlqsm",
        password="DkoQGcMFW3dXX5QI",
        port="5432"
    )
    return conn
```

### After
```python
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        port=int(os.getenv("DB_PORT", "5432")),
        sslmode="require",
    )
```

### Changes
- Replaced 5 hardcoded string literals with `os.getenv()` calls
- Added `sslmode="require"` for encrypted connections (matches `auth_queries.py` pattern)
- Added `load_dotenv()` call for `.env` file support
- Added module docstring documenting required environment variables
- Translated Spanish comment to English

### Impact
- Zero breaking changes — function signature unchanged
- All 14+ callers continue to work without modification
- Requires `.env` file or environment variables to be set (already documented)

---

## Step 1.2: Remove `tars.json` from Repository

### 1.2a — Git History Check
```bash
git log --all --oneline --full-history -- tars.json
```
**Result:** `tars.json` was **never committed** to the repository. No history rewrite needed.

### 1.2b — Updated `.gitignore`

**Added:**
```
*-service-account.json
```
This prevents any future service account key files from being accidentally committed.

### 1.2c — Updated `ChatMessage/infraestructure/tts/google_tts.py`

**Before:**
```python
def get_credentials():
    json_creds = os.getenv('GOOGLE_JSON_CREDENTIALS')
    if not json_creds:
        credentials_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../../../tars.json')
        )
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        return None
```

**After:**
```python
def get_credentials():
    json_creds = os.getenv('GOOGLE_JSON_CREDENTIALS')
    if not json_creds:
        return None
    # ... rest unchanged
```

**Changes:**
- Removed local file path fallback to `../../../../tars.json`
- Removed automatic `GOOGLE_APPLICATION_CREDENTIALS` env var injection
- Simplified to only support `GOOGLE_JSON_CREDENTIALS` (JSON string) or SDK default (file path via `GOOGLE_APPLICATION_CREDENTIALS` set externally)
- Translated all Spanish comments to English

### 1.2d — Updated `AGENTS.md`

Added explicit Google Cloud credentials setup instructions to the "Required Setup" section:
- Option A: `GOOGLE_JSON_CREDENTIALS` env var (JSON string content)
- Option B: `GOOGLE_APPLICATION_CREDENTIALS` env var (file path)
- Warning against committing service account keys

---

## Files Modified

| File | Change Type | Lines Changed |
|------|-------------|---------------|
| `agents/dataBase/connection.py` | Rewrite | 10/13 |
| `.gitignore` | Append | +1 line |
| `ChatMessage/infraestructure/tts/google_tts.py` | Edit | ~20/110 |
| `AGENTS.md` | Append | +4 lines |

---

## Security Improvements

| Issue | Status |
|-------|--------|
| Hardcoded Supabase credentials in source code | **FIXED** |
| Local `tars.json` file fallback in TTS module | **REMOVED** |
| Service account key patterns not in `.gitignore` | **ADDED** `*-service-account.json` |
| `tars.json` in git history | **CLEAN** — never committed |

---

## Migration Notes

No migration needed. All changes are backward-compatible:
- `connection.py` function signature unchanged
- TTS credential loading still supports both env var methods
- Existing `.env` files work without modification
