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

---

## Step 4.2: Convert `TarsState` from `TypedDict` to Pydantic `BaseModel`

### Problem

`TarsState` was a `TypedDict` with zero runtime validation. The code relied on defensive `.get()` calls with defaults everywhere, and missing fields were silently tolerated. This made it impossible to catch invalid state mutations at runtime.

### Solution

#### 1. Redefined `TarsState` as Pydantic `BaseModel` (`agents/brain/schema.py`)

**Before (TypedDict):**
```python
class TarsState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: Optional[int]
    active_expert: str
    user_mode: Optional[str]
    # ... 11 more Optional fields, no defaults
```

**After (BaseModel):**
```python
class TarsState(BaseModel):
    # Core fields — required at session creation
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    user_id: int
    active_expert: str
    user_mode: str

    # Optional fields with sensible defaults
    working_context: List[Dict[str, str]] = Field(default_factory=list)
    is_complete: bool = False
    selected_role: Optional[str] = None
    scene_context: Optional[str] = None
    user_role: Optional[str] = None
    selected_source: Optional[str] = None
    current_lesson: int = Field(default=1, ge=1)
    hsk_level: int = Field(default=1, ge=1, le=6)
    lesson_progress: int = Field(default=0, ge=0)
    target_word: Optional[str] = None
    lesson_words: List[str] = Field(default_factory=list)
    awaiting_answer: bool = False
```

Key changes:
- **4 core fields required**: `messages`, `user_id`, `active_expert`, `user_mode`
- **Validation constraints**: `hsk_level` must be 1-6, `current_lesson` >= 1, `lesson_progress` >= 0
- **Mutable defaults**: `Field(default_factory=list)` for `messages`, `working_context`, `lesson_words`
- **LangGraph reducer preserved**: `Annotated[List[BaseMessage], add_messages]` still works

#### 2. Updated Node Access Patterns

**Dict access → attribute access:**

| Pattern | Before | After |
|---------|--------|-------|
| `.get(key, default)` | `state.get("current_lesson", 1)` | `state.current_lesson` |
| `state["key"]` | `state["messages"]` | `state.messages` |
| `{**state, ...}` | `{**state, "messages": truncated}` | `state.model_dump() \| {"messages": truncated}` |

**Files updated:**
- `agents/brain/nodes.py` — `route_lesson()` uses `state.user_mode`, `state.awaiting_answer`
- `agents/brain/node_learning.py` — all `.get()` calls replaced with attribute access, `{**state}` → `state.model_dump() | {...}`
- `agents/brain/node_roleplay.py` — same pattern

#### 3. Strict Validation at API Boundary (`api/routes/chat.py`)

Session initialization now validates state before passing to LangGraph:

```python
# Before: plain dict, no validation
init_state = {"user_mode": "tars_roleplay", "active_expert": "tars_roleplay", ...}

# After: validates required fields, constraints, then serializes
init_state = TarsState(
    user_mode="tars_roleplay",
    active_expert="tars_roleplay",
    user_id=current_user_id,
    hsk_level=get_user_hsk_level(current_user_id),
    messages=[HumanMessage(content=sys_msg_text)],
).model_dump()
```

If any required field is missing or a constraint is violated (e.g., `hsk_level=0`), a `ValidationError` is raised immediately at the API boundary.

#### 4. Snapshot Validation (`api/routes/profile.py`)

Checkpointer snapshots are validated back into `TarsState` models:

```python
# Before: raw dict access with defaults
current_lesson = snapshot.values.get("current_lesson", 1)

# After: validates the snapshot shape, then uses typed attributes
state = TarsState.model_validate(snapshot.values)
current_lesson = state.current_lesson
```

#### 5. LangGraph Compatibility

- `StateGraph(TarsState)` works unchanged — LangGraph accepts Pydantic models as state schemas
- The `add_messages` reducer still functions correctly
- Node return values remain plain `dict` — LangGraph merges them into the state
- `AsyncPostgresSaver` serialization is unaffected (LangGraph handles `BaseMessage` serialization internally)

### Files Modified

| File | Action |
|------|--------|
| `agents/brain/schema.py` | Replaced `TypedDict` with `BaseModel`, 4 required fields, validation constraints |
| `agents/brain/nodes.py` | `route_lesson()` uses attribute access |
| `agents/brain/node_learning.py` | All `.get()` → attribute access, `{**state}` → `model_dump() \| {...}` |
| `agents/brain/node_roleplay.py` | Same pattern as `node_learning.py` |
| `api/routes/chat.py` | Strict validation via `TarsState(...).model_dump()` for `init_state` |
| `api/routes/profile.py` | Snapshot validation via `TarsState.model_validate(snapshot.values)` |

---

## Step 4.3: Add Return Type Annotations to All DB Functions

### Problem

After auditing 39 functions across all DB modules, 7 were missing return type annotations, 1 had an overly broad `Generator` annotation, and 2 had sentinel value issues where the annotation didn't match the actual behavior.

### Solution

#### 1. Added Missing Return Annotations (7 functions)

| File | Function | Added |
|------|----------|-------|
| `pool.py` | `close_pool()` | `-> None` |
| `ingest_document.py` | `ingest_pdf(...)` | `-> None` |
| `save_memory.py` | `save_long_term_memory(...)` | `-> None` |
| `vacuum.py` | `_update_job(...)` | `-> None` |
| `vacuum.py` | `_get_job_stats(...)` | `-> dict` |
| `vacuum.py` | `stage_e_db_optimization(conn)` | `-> None` |
| `vacuum.py` | `run_vacuum_job(job_id, n_limit)` | `-> None` |

#### 2. Fixed Overly Broad Annotation

| File | Function | Before | After |
|------|----------|--------|-------|
| `pool.py` | `get_db_connection()` | `Generator` | `Generator[psycopg2.extensions.connection, None, None]` |

#### 3. Fixed Sentinel Value Issues

**`get_user_hsk_level(user_id) -> int`** — Now raises `AuthenticationError.UserNotFound` when the user doesn't exist, instead of silently returning `1`. Callers can no longer confuse "user has HSK 1" with "user not found."

**`delete_document_by_filename(user_id, filename) -> bool`** — Now returns `cur.rowcount > 0` instead of always `True`. Returns `False` when no rows were deleted (file didn't exist).

#### 4. Added Parameter Type Annotations to `vacuum.py`

```python
def _update_job(
    conn: psycopg2.extensions.connection,
    job_id: uuid.UUID,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    current_stage: Optional[str] = None,
    stats: Optional[dict] = None,
    error_log: Optional[str] = None,
) -> None:

def _get_job_stats(conn: psycopg2.extensions.connection, job_id: uuid.UUID) -> dict:

def run_vacuum_job(job_id: uuid.UUID, n_limit: int = 500) -> None:

def stage_e_db_optimization(conn: psycopg2.extensions.connection) -> None:
```

Also added `import traceback` at module level (was previously imported inside the `except` block).

#### 5. Updated Callers for Breaking Change

**`api/routes/chat.py`** — Added `_get_hsk_level()` wrapper that catches `AuthenticationError.UserNotFound` and defaults to HSK 1. This preserves the existing graceful degradation behavior while still allowing the DB function to raise when appropriate:

```python
def _get_hsk_level(user_id: int) -> int:
    try:
        return get_user_hsk_level(user_id)
    except AuthenticationError.UserNotFound:
        logger.warning("User %d not found in DB, defaulting to HSK 1", user_id)
        return 1
```

**`api/routes/roleplay.py`** — Updated `delete_roleplay_file` to check the return value and raise `HTTPException(404)` when the file doesn't exist:

```python
if not delete_document_by_filename(current_user_id, filename):
    raise HTTPException(status_code=404, detail=f"Document {filename} not found")
```

### Files Modified

| File | Action |
|------|--------|
| `agents/dataBase/pool.py` | Added `-> None` to `close_pool()`, typed `Generator[connection, None, None]` |
| `agents/dataBase/main_queries.py` | `get_user_hsk_level` raises `UserNotFound`, `delete_document_by_filename` returns `rowcount > 0` |
| `agents/RAG/ingest_document.py` | Added `-> None` |
| `agents/RAG/save_memory.py` | Added `-> None` |
| `agents/RAG/vacuum.py` | Added return + parameter annotations to 7 functions, moved `traceback` import to module level |
| `api/routes/chat.py` | Added `_get_hsk_level()` wrapper, imported `AuthenticationError` |
| `api/routes/roleplay.py` | Check `delete_document_by_filename` return, raise 404 on not found |

---

## Step 4.4: Extract Protocol Text Building into `protocol_builder.py`

### Problem

Both `node_learning.py` and `node_roleplay.py` followed a nearly identical protocol building pipeline, but the logic was duplicated and interleaved with domain-specific code. Each node:

1. Retrieved the base protocol template from `PROTOCOLS`
2. Filled in mode-specific variables (lesson data vs. persona data)
3. Appended mode-specific instructions (3-word rule vs. character lock)
4. Replaced `{context}` with RAG results
5. Built RAG and memory context in parallel
6. Appended style examples
7. Created a dynamic chain and invoked it with truncated state

This resulted in ~90 lines of duplicated pipeline logic across the two nodes, making it hard to modify the protocol building process without touching both files.

### Solution

#### 1. Created `ProtocolBuilder` Class (`agents/brain/protocol_builder.py`)

A class that encapsulates the common protocol building pipeline:

```python
class ProtocolBuilder:
    def __init__(self, expert_type: str, state):
        # Initializes protocol text, extracts last user message, computes embedding

    def set_context(self, context_text: str):
        # Replaces {context} placeholder

    def append(self, text: str):
        # Appends arbitrary text to protocol

    async def enrich_rag(self, current_lesson: int = None):
        # Runs RAG and memory enrichment in parallel

    def enrich_style(self, feedback_type: str = "DEFAULT"):
        # Appends style examples

    def build_chain(self):
        # Creates the dynamic LLM chain

    def get_truncated_state(self) -> dict:
        # Returns state with truncated messages

    async def invoke(self, config: RunnableConfig):
        # Full pipeline: build chain → truncate → invoke
```

#### 2. Extracted Mode-Specific Protocol Text Functions

Three pure functions that generate the domain-specific protocol text:

| Function | Purpose |
|----------|---------|
| `build_lesson_introduce_protocol(...)` | "Introduce new word" instructions with 3-word rule |
| `build_lesson_check_protocol(...)` | "Check user answer" instructions with feedback type |
| `build_roleplay_protocol(...)` | Full roleplay protocol with persona, character lock, safety instructions |

#### 3. Simplified Nodes

**`node_learning.py` before (193 lines) → after (110 lines, 43% reduction)**

Before:
```python
protocol_text = PROTOCOLS.get("tars_normal", "Standard operating procedures.")
protocol_text = protocol_text.replace("{context}", "No relevant context for this turn.")
protocol_text += f"""... 20 lines of lesson instructions ..."""
# ... RAG calls ...
dynamic_chain = actor_prompt_template.partial(protocol=protocol_text) | llm_expert
truncated_state = state.model_dump() | {"messages": truncate_messages(state.messages)}
response = await dynamic_chain.ainvoke(truncated_state, config=config)
```

After:
```python
builder = ProtocolBuilder("tars_normal", state)
builder.append(build_lesson_introduce_protocol(...))
await builder.enrich_rag(current_lesson)
builder.enrich_style("INTRODUCE")
response = await builder.invoke(config)
```

**`node_roleplay.py` before (119 lines) → after (65 lines, 45% reduction)**

Before:
```python
# 60+ lines of persona fetching, protocol formatting, character lock,
# safety instructions, metamorphic prompt, scene context, RAG, memory,
# chain building, invocation, JSON cleanup
```

After:
```python
protocol_text = build_roleplay_protocol(char_name, user_role, persona_data, scene_context)
builder = ProtocolBuilder("tars_roleplay", state)
builder.protocol_text = protocol_text
# ... RAG + memory enrichment ...
response = await builder.invoke(config)
# ... JSON cleanup ...
```

### Files Modified

| File | Action |
|------|--------|
| `agents/brain/protocol_builder.py` | **Created** — ProtocolBuilder class + 3 protocol text functions |
| `agents/brain/node_learning.py` | Reduced from 193 → 110 lines, uses ProtocolBuilder |
| `agents/brain/node_roleplay.py` | Reduced from 119 → 65 lines, uses ProtocolBuilder |
