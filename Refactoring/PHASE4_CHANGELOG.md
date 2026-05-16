# Phase 4: Architecture — Changelog

## Step 4.1: Custom Exception Classes

### Problem

The codebase used bare `Exception` everywhere with inconsistent sentinel values:

- **DB modules** returned `None`, `False`, `[]`, `""`, `1`, or default dicts on error — callers had to check for different falsy types
- **API routes** wrapped DB calls in `try/except HTTPException(500)` — no way to distinguish "user not found" from "DB connection failed"
- **WebSocket** leaked raw exception strings to clients (SQL syntax, connection details)
- **No transaction rollback** — `save_memory.py` and `ingest_document.py` swallowed exceptions without `conn.rollback()`, leaving connections in undefined state

### Solution

#### 1. Exception Hierarchy (`agents/errors.py`)

```
TarsError (base)
├── DatabaseError
│   ├── ConnectionError (503)
│   └── QueryError (500)
├── RAGError
│   ├── RetrievalError (500)
│   └── IngestionError (500)
├── AuthenticationError
│   ├── InvalidCredentials (401)
│   ├── UserNotFound (404)
│   └── DuplicateUser (409)
├── ValidationError (422)
├── TTSError (500)
└── ResourceNotFoundError (404)
```

Each exception carries:
- `code: str` — machine-readable error code for frontend localization
- `status_code: int` — HTTP status code for automatic mapping
- `message: str` — human-readable description
- `original: Exception | None` — wrapped original exception for debugging

#### 2. FastAPI Global Exception Handlers (`api/exceptions.py`)

Registered in `api/app.py` via `register_exception_handlers(app)`. Maps each exception type to the appropriate HTTP response automatically. Routes no longer need `try/except HTTPException` blocks.

Response format:
```json
{"detail": "User not found", "code": "user_not_found"}
```

The `code` field is additive — existing frontend code that only reads `detail` continues to work.

#### 3. DB Module Migration

Converted all DB modules from "return sentinel on error" to "raise typed exception":

| Module | Before | After |
|--------|--------|-------|
| `auth_queries.py` | `except: return None` | `except psycopg2.Error: raise DatabaseError.QueryError(...)` |
| `main_queries.py` | `except: return False/[]/1` | `except psycopg2.Error: raise DatabaseError.QueryError(...)` |
| `conversations.py` | `except: return 1` | `except psycopg2.Error: raise DatabaseError.QueryError(...)` |
| `persona_db.py` | `except: return None` | `except psycopg2.Error: raise DatabaseError.QueryError(...)` |
| `retrieve.py` | `except: return []/""` | `except psycopg2.Error: raise RAGError.RetrievalError(...)` |
| `save_memory.py` | `except: log and swallow` | `except psycopg2.Error: conn.rollback(); raise DatabaseError.QueryError(...)` |
| `ingest_document.py` | `except: log and swallow` | `except psycopg2.Error: conn.rollback(); raise RAGError.IngestionError(...)` |

**Key design decision:** `None` is still returned for "not found" (valid result), while exceptions are raised only for actual failures (connection dropped, SQL error, constraint violation).

#### 4. API Route Cleanup

Removed redundant `try/except` blocks from routes:

| Route | Before | After |
|-------|--------|-------|
| `auth.py` `/register` | `try/except HTTPException(500)` | Let `create_user` raise `AuthenticationError.DuplicateUser` → global handler returns 409 |
| `profile.py` `/api/user/profile` PUT | `if not updated_user: HTTPException(500)` | `if not updated_user: raise AuthenticationError.UserNotFound` → global handler returns 404 |
| `roleplay.py` DELETE | `if not success: HTTPException(500)` | `delete_document_by_filename` raises on failure → global handler returns 500 |
| `roleplay.py` POST `/upload` | `try/except HTTPException(500)` | `ingest_pdf` raises `RAGError.IngestionError` → global handler returns 500 |

#### 5. WebSocket Error Sanitization

**Before:**
```python
except Exception as e:
    await websocket.send_json({"type": "error", "message": str(e)})
```

**After:**
```python
from agents.errors import TarsError

except TarsError as e:
    await websocket.send_json({"type": "error", "code": e.code, "message": str(e)})
except Exception:
    logger.exception("Unhandled error in WebSocket")
    await websocket.send_json({
        "type": "error",
        "code": "internal_error",
        "message": "An unexpected error occurred"
    })
```

#### 6. Bug Fix: Missing Transaction Rollback

Fixed in `save_memory.py` and `ingest_document.py`. Every DB `except` block now calls `conn.rollback()` before re-raising:

```python
except psycopg2.Error as e:
    conn.rollback()
    raise DatabaseError.QueryError("Failed to save long-term memory", original=e) from e
```

### Files Modified

| File | Action |
|------|--------|
| `agents/errors.py` | Created — exception hierarchy |
| `api/exceptions.py` | Created — FastAPI global exception handlers |
| `api/app.py` | Added `register_exception_handlers(app)` call |
| `agents/dataBase/auth_queries.py` | Raise typed exceptions, catch `psycopg2.errors.UniqueViolation` → `DuplicateUser` |
| `agents/dataBase/main_queries.py` | Raise typed exceptions, fix cursor context managers |
| `agents/dataBase/conversations.py` | Raise typed exceptions |
| `agents/dataBase/persona_db.py` | Raise typed exceptions, fix cursor context managers |
| `agents/RAG/retrieve.py` | Raise `RAGError.RetrievalError`, fix cursor context managers |
| `agents/RAG/save_memory.py` | Raise `DatabaseError.QueryError` + `conn.rollback()` |
| `agents/RAG/ingest_document.py` | Raise `RAGError.IngestionError` + `conn.rollback()` |
| `api/routes/auth.py` | Removed redundant `try/except HTTPException(500)` |
| `api/routes/profile.py` | Changed `HTTPException(500)` → `AuthenticationError.UserNotFound` |
| `api/routes/roleplay.py` | Removed redundant `try/except`, simplified delete route |
| `api/routes/chat.py` | Sanitized WebSocket error responses, catch `TarsError` specifically |
