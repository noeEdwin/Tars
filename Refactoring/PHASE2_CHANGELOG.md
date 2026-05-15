# Phase 2: Backend Restructuring — Changelog

## Summary

Split the 665-line monolithic `api.py` into a modular package with 6 route modules, created shared models, and established backward compatibility for Docker deployments.

---

## Step 2.1: Split `api.py` into Route Modules

### New Package Structure

```
api/
├── __init__.py              # exports `app` for backward compat
├── app.py                   # FastAPI app, lifespan, CORS, router includes
├── models.py                # Pydantic request/response models
└── routes/
    ├── __init__.py          # imports all routers
    ├── auth.py              # /auth/register, /auth/login
    ├── chat.py              # /start_session, /ws/{user_id}, handle_tars_response
    ├── profile.py           # /api/user/profile, /greeting, /preload_message
    ├── roleplay.py          # /roleplay/files, /roleplay/upload, /roleplay/files/{filename}
    ├── stt.py               # /stt
    └── admin.py             # /admin/vacuum, /admin/vacuum/status/{job_id}
```

### Route Module Breakdown

| Module | Lines | Endpoints | Key Functions |
|--------|-------|-----------|---------------|
| `auth.py` | ~90 | 2 | `register()`, `login()` |
| `chat.py` | ~250 | 1 + WebSocket | `start_session()`, `websocket_endpoint()`, `handle_tars_response()` |
| `profile.py` | ~120 | 4 | `get_profile()`, `update_profile()`, `get_greeting()`, `get_preload_message()` |
| `roleplay.py` | ~55 | 3 | `get_roleplay_files()`, `delete_roleplay_file()`, `upload_roleplay_file()` |
| `stt.py` | ~35 | 1 | `stt_endpoint()` |
| `admin.py` | ~20 | 2 | `trigger_vacuum()`, `get_vacuum_status()` |

### `api/app.py` — Application Factory

- Creates FastAPI app with lifespan context manager
- Sets up CORS middleware (6 allowed origins)
- Includes all 6 route modules with appropriate prefixes
- Exposes `/health` endpoint
- Shares `app_state` dict with `chat.py` router for LangGraph workflow access

### `api/models.py` — Shared Pydantic Models

Extracted 4 models from the monolith:
- `StartSessionRequest`
- `StartSessionResponse`
- `ChatRequest`
- `ChatResponse`

### Root `api.py` — Backward Compatibility Shim

```python
"""
Backward compatibility shim.
Allows Docker to continue running: uvicorn api:app --host 0.0.0.0 --port 8000
The actual application lives in api/app.py.
"""
from api.app import app
```

This keeps Docker's `uvicorn api:app` command working without any changes to `docker-compose.yml` or `Dockerfile`.

### Improvements During Migration

| Change | Before | After |
|--------|--------|-------|
| Logging | `print()` statements | `logging.getLogger(__name__)` |
| Error handling | `print(f"Error: {e}")` | `logger.error("...", e)` |
| Debug output | `print("DEBUG: ...")` | `logger.debug("...")` |
| Warnings | `print("Warning: ...")` | `logger.warning("...")` |
| Constants | `WHISPER_HALLUCINATIONS` in `api.py` | Moved to `stt.py` |
| Constants | `EMOTION_MAP` in `api.py` | Moved to `profile.py` |
| Constants | `active_tasks` in `api.py` | Moved to `chat.py` |
| Shared state | `app_state` in `api.py` | In `app.py`, shared via import in `chat.py` |

### Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `api/__init__.py` | 1 | Package export |
| `api/app.py` | ~70 | App factory, lifespan, CORS |
| `api/models.py` | ~30 | Pydantic models |
| `api/routes/__init__.py` | ~15 | Router exports |
| `api/routes/auth.py` | ~90 | Auth endpoints |
| `api/routes/chat.py` | ~250 | WebSocket + session |
| `api/routes/profile.py` | ~120 | Profile + greeting |
| `api/routes/roleplay.py` | ~55 | Roleplay file management |
| `api/routes/stt.py` | ~35 | Speech-to-text |
| `api/routes/admin.py` | ~20 | Vacuum management |

### Files Modified

| File | Change |
|------|--------|
| `api.py` (root) | Replaced with 6-line backward-compat shim |

### URL Mapping (unchanged)

All endpoints maintain their original URLs:

| URL | Method | Module |
|-----|--------|--------|
| `/auth/register` | POST | `auth.py` |
| `/auth/login` | POST | `auth.py` |
| `/start_session` | POST | `chat.py` |
| `/ws/{user_id}` | WebSocket | `chat.py` |
| `/api/user/profile` | GET, PUT | `profile.py` |
| `/greeting` | GET | `profile.py` |
| `/preload_message` | GET | `profile.py` |
| `/roleplay/files` | GET | `roleplay.py` |
| `/roleplay/files/{filename}` | DELETE | `roleplay.py` |
| `/roleplay/upload` | POST | `roleplay.py` |
| `/stt` | POST | `stt.py` |
| `/admin/vacuum` | POST | `admin.py` |
| `/admin/vacuum/status/{job_id}` | GET | `admin.py` |
| `/health` | GET | `app.py` |

### Remaining Work (Step 2.2, 2.3 & 2.4)

- **Step 2.2**: Fix import system — remove `sys.path.insert()`, add `pyproject.toml`
- **Step 2.3**: Fix circular import in `personality_rag.py` (`from api import app_state`)
- **Step 2.4**: Delete backward-compat shims:
  - `agents/dataBase/connection.py` — shim wrapping `pool.py`
  - Root `api.py` — 6-line shim (`from api.app import app`)

