# Tars Refactoring Plan — Master Tracker

## Legend
- ✅ Complete
- 🔄 In progress
- ⏳ Not started

---

## Phase 1: Security & Database Infrastructure ✅ COMPLETE

**Goal:** Remove hardcoded credentials, consolidate DB connections, add connection pooling.

| Step | Status | Description |
|------|--------|-------------|
| 1.1 | ✅ | Remove hardcoded DB credentials from `connection.py` |
| 1.2 | ✅ | Remove `tars.json` fallback, tighten `.gitignore`, update docs |
| 1.3 | ✅ | Create `pool.py` with connection pooling, migrate all 12 consumers |
| Cleanup | ✅ | Delete dead `user_management.py` functions → `conversations.py`, move `ingest_pdf.py` → `scripts/ingest_hsk_csv.py`, replace `print()` with `logging` |

**Files changed:** 20+ files. See `PHASE1_CHANGELOG.md` for full details.

---

## Phase 2: Backend Restructuring ✅ COMPLETE

**Goal:** Split monolithic `api.py`, fix import system, resolve circular dependencies.

| Step | Status | Description |
|------|--------|-------------|
| 2.1 | ✅ | Split `api.py` (665 lines) into route modules |
| 2.2 | ✅ | Fix import system — remove `sys.path.insert()`, add `pyproject.toml` |
| 2.3 | ✅ | Resolve circular import in `personality_rag.py` |
| 2.4 | ✅ | Delete backward-compat shims: `agents/dataBase/connection.py`, root `api.py` |

### Step 2.1 Details

Split `api.py` into:
```
api/
├── __init__.py              # exports `app`
├── app.py                   # FastAPI app, lifespan, CORS, router includes
├── models.py                # Pydantic request/response models
├── routes/
│   ├── __init__.py          # imports all routers
│   ├── auth.py              # /auth/register, /auth/login
│   ├── chat.py              # /start_session, /ws/{user_id}, handle_tars_response
│   ├── profile.py           # /api/user/profile, /greeting, /preload_message
│   ├── roleplay.py          # /roleplay/files, /roleplay/upload, /roleplay/files/{filename}
│   ├── stt.py               # /stt
│   └── admin.py             # /admin/vacuum, /admin/vacuum/status/{job_id}
```

Root `api.py` becomes a backward-compat shim: `from api.app import app`

### Step 2.2 Details

- Create `pyproject.toml` with editable install
- Fix all imports: `from brain.xxx` → `from agents.brain.xxx`, `from RAG.xxx` → `from agents.RAG.xxx`
- Remove all `sys.path.insert()` calls from every file
- Run `pip install -e .`

### Step 2.3 Details

- `personality_rag.py` imports `from api import app_state` (circular)
- `app_state["style_library"]` is never populated (dead code)
- Fix: remove import, return `protocol_text` unchanged, add TODO comment

### Step 2.4: Delete Backward-Compat Shims

After Step 2.2 completes (all imports fixed via `pyproject.toml`):

**Delete `agents/dataBase/connection.py`** — shim wrapping `pool.py`. No file imports it after Phase 1 + 2.2.

**Delete root `api.py`** — 6-line shim (`from api.app import app`). After `pyproject.toml` editable install, update Docker to use `uvicorn api.app:app` or update `docker-compose.yml`.

**Delete `_extract_tars_message()` in `api/routes/chat.py`** — dead code, never called anywhere.

---

## Phase 3: Code Quality ✅ COMPLETE

**Goal:** Standardize language, deduplicate code, improve patterns.

| Step | Status | Description |
|------|--------|-------------|
| 3.1 | ✅ | Standardize to English — translate Spanish comments, variable names, print messages |
| 3.2 | ✅ | Extract duplicated WebSocket `onmessage` logic in `ConversationContainer.tsx` into `useWebSocket` hook |
| 3.3 | ✅ | Replace remaining `print()` with `logging` across all backend modules |
| 3.4 | ✅ | Consolidate DB query patterns — ensure `RealDictCursor` everywhere |
| 3.5 | ✅ | Add preload messages with lesson progress (normal) and in-character greeting (roleplay) |

---

## Phase 4: Architecture 🔄 IN PROGRESS

**Goal:** Error handling, typing, separation of concerns.

| Step | Status | Description |
|------|--------|-------------|
| 4.1 | ✅ | Add custom exception classes (`TarsError`, `DatabaseError`, `RAGError`, `AuthenticationError`) |
| 4.2 | ✅ | Convert `TarsState` from `TypedDict` to Pydantic `BaseModel` |
| 4.3 | ✅ | Add return type annotations to all DB functions |
| 4.4 | ⏳ | Extract protocol text building from `node_learning.py` and `node_roleplay.py` into `protocol_builder.py` |

---

## Phase 5: Frontend ⏳ NOT STARTED

**Goal:** State management, component organization, API client.

| Step | Status | Description |
|------|--------|-------------|
| 5.1 | ⏳ | Add Zustand for state management (`authStore`, `sessionStore`, `chatStore`) |
| 5.2 | ⏳ | Reorganize components into folders with co-located CSS (`auth/`, `chat/`, `roleplay/`, `layout/`, `ui/`) |
| 5.3 | ⏳ | Create typed API client layer (`src/api/client.ts`) replacing scattered `fetch()` calls |

---

## Changelog Files

- `Refactoring/PHASE1_CHANGELOG.md` — Phase 1 detailed changelog
- `Refactoring/PHASE2_CHANGELOG.md` — Phase 2 detailed changelog
- `Refactoring/PHASE3_CHANGELOG.md` — Phase 3 detailed changelog
- `Refactoring/PHASE4_CHANGELOG.md` — Phase 4 detailed changelog
