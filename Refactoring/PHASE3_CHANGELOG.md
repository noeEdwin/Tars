# Phase 3: Code Quality — Changelog

## Step 3.1: Standardize to English

### What was translated

**Comments:**
- `agents/brain/nodes.py` — "Importamos los nodos modularizados" → "Import modularized nodes"
- `agents/brain/node_roleplay.py` — 2 comments translated
- `agents/brain/chains.py` — 2 comments/docstrings translated

**Print/log messages:**
- `agents/brain/node_learning.py` — 4 timer messages translated
- `agents/brain/identity_agent.py` — 6 print messages translated (emojis removed)
- `data_normal_mode/ingest_hsk1.py` — 5 print messages translated
- `data_normal_mode/verify_translations.py` — 2 print messages translated

**API error/detail messages:**
- `api/routes/auth.py` — 5 error messages translated
- `api/routes/profile.py` — 2 error messages translated
- `api/routes/roleplay.py` — 4 status/error messages translated
- `api/routes/chat.py` — 3 system messages + 1 status message translated

**LLM prompts (instructions translated, output language preserved):**
- `api/routes/profile.py` — preload_message prompt translated to English (output still in Spanish)
- `data_normal_mode/verify_translations.py` — system_prompt translated to English (output still in Spanish)

**Formatting strings:**
- `agents/brain/context_builders.py` — "Significado" → "Meaning", "Regla HSK" → "HSK Rule"

**Variable names:**
- `api/routes/chat.py` — `texto_secreto` → `kickstart_msg`

### What was NOT translated (intentionally)

- **Protocol/prompt text in `node_learning.py` and `node_roleplay.py`** — These are system instructions sent to the LLM telling it how to communicate with Spanish-speaking users. The content must remain in Spanish for the LLM to produce Spanish responses.
- **Database column names** — `contenido_zh`, `traduccion_es`, `titulo_es_leccion`, etc. map to the actual PostgreSQL schema.
- **JSON data keys** — `modulos_de_aprendizaje`, `vocabulario_extraido`, `gramatica_claves`, `palabra`, `significado`, `metadatos`, `libro`, `total_lecciones`, `titulo_original`, `titulo_es`, `lecciones` are keys in existing data files (`tars_150_hsk1.json`, lesson JSON files).
- **Lesson title translations** — The `title_translations` dict in `clean_hsk1.py` contains the actual Spanish lesson titles shown to users.
- **Grammar rule names** — Chinese grammar identifiers from the HSK curriculum.

### Files modified

| File | Changes |
|------|---------|
| `agents/brain/nodes.py` | 1 comment |
| `agents/brain/node_roleplay.py` | 2 comments |
| `agents/brain/node_learning.py` | 4 print messages |
| `agents/brain/identity_agent.py` | 6 print messages |
| `agents/brain/chains.py` | 2 comments/docstrings |
| `agents/brain/context_builders.py` | 2 format strings |
| `api/routes/chat.py` | 4 messages + 1 variable name |
| `api/routes/profile.py` | 2 error messages + 1 LLM prompt |
| `api/routes/auth.py` | 5 error messages |
| `api/routes/roleplay.py` | 4 status/error messages |
| `data_normal_mode/ingest_hsk1.py` | 5 print messages |
| `data_normal_mode/verify_translations.py` | 2 print messages + 1 LLM prompt |

---

## Step 3.2: Extract `useWebSocket` Hook

### Problem

The `socket.onmessage` handler was **duplicated in 3 places** within `ConversationContainer.tsx`:

| Location | Lines | Context |
|----------|-------|---------|
| Pre-warmed session | 73-114 | Socket from pre-warmed session |
| Main session | 158-201 | Fresh WebSocket connection |
| Reconnect | 243-278 | Socket reconnection in `sendMessage()` |

All three handled the same message types identically: `token`, `audio_chunk`/`tars_answer`, `tars_answer_end`, and `error`. ~90 lines of duplicated code.

### Solution

Created `frontend/src/hooks/useWebSocket.ts` — a custom React hook that encapsulates:

1. **Shared message handler** — `handleSocketMessage()` processes all WebSocket message types in one place
2. **Handler attachment** — `attachMessageHandler()` reusable function to wire up any WebSocket
3. **Pre-warmed session adoption** — takes over an existing socket and buffered state
4. **Fresh session creation** — creates WebSocket after session is ready
5. **Reconnect logic** — handles socket reconnection in `sendMessage()`
6. **State management** — messages, audio queue, processing state, teaching message tracking
7. **Actions** — `sendMessage()`, `interruptTars()`

### Results

**`ConversationContainer.tsx`: 329 lines → 103 lines** (69% reduction)

The component now focuses purely on:
- Starting the session via `/start_session`
- Routing between `VoiceConversationScreen` and `ConversationScreen`
- Passing hook outputs as props

### Files

| File | Action | Lines |
|------|--------|-------|
| `frontend/src/hooks/useWebSocket.ts` | Created | 195 |
| `frontend/src/components/ConversationContainer.tsx` | Rewritten | 103 (was 329) |

### Hook API

```typescript
function useWebSocket(options: UseWebSocketOptions) {
    return {
        messages,           // Message[]
        audioQueue,         // string[]
        currentAudioIndex,  // number
        setCurrentAudioIndex,
        isProcessing,       // boolean
        sendMessage,        // (text: string) => void
        interruptTars,      // () => void
    };
}
```

---

## Step 3.5: Preload Messages with Lesson Progress & Roleplay Greeting

### Problem

- Normal mode preload message (`/preload_message`) was a generic greeting — no lesson context
- Roleplay mode had no preload message at all — the character greeting only arrived after WebSocket kickstart

### Solution

**Backend — `api/routes/profile.py`:**

1. **Enhanced `/preload_message`** — Now reads the user's LangGraph state to get:
   - `current_lesson` — which lesson the user is on
   - `lesson_progress` — how many words completed
   - `target_word` — the next word to practice
   
   The LLM prompt includes: *"The user's next word to learn is 你 (nǐ) — 'tú'. Weave this into the greeting."*
   
   Falls back to lesson 1, word 1 (`我` — "Yo") if no state exists.

2. **New `/preload_message_roleplay`** — Accepts `tars_role` and `filename` as query params:
   - Fetches persona from DB via `fetch_persona_from_db`
   - Uses persona traits (archetype, speech style, rules) in the LLM prompt
   - Generates an in-character greeting: *"You are {character}. Stay in character. End with a question."*
   - Returns `{ text, audio_b64 }` same format as normal preload

3. **Shared `app_state`** with profile module in `api/app.py` — enables reading LangGraph state

**Frontend — `frontend/src/utils/usePreWarmSession.ts`:**

4. Changed preload fetch from `if (mode === 'tars_normal')` to both modes:
   - Normal: `GET /preload_message`
   - Roleplay: `GET /preload_message_roleplay?tars_role=...&filename=...`

### Files

| File | Change |
|------|--------|
| `api/app.py` | Share `app_state` with profile module |
| `api/routes/profile.py` | Enhanced `/preload_message` + new `/preload_message_roleplay` |
| `frontend/src/utils/usePreWarmSession.ts` | Fetch preload for roleplay too |

### API Endpoints

| Endpoint | Method | Query Params | Description |
|----------|--------|--------------|-------------|
| `/preload_message` | GET | — | Normal mode greeting with lesson context |
| `/preload_message_roleplay` | GET | `tars_role`, `filename` | In-character roleplay greeting |

---

## Step 3.3: Replace `print()` with `logging`

### Problem

74 `print()` statements across 14 backend Python files provided no log levels, no timestamps, and no structured output.

### Solution

Replaced all `print()` statements with proper `logging` calls using appropriate log levels:

| Level | Use Case | Count |
|-------|----------|-------|
| `logger.error()` | Error handling in `except` blocks | 29 |
| `logger.info()` | Progress/status messages | 28 |
| `logger.debug()` | Timer/performance metrics | 5 |
| `logger.warning()` | Warnings | 1 |
| CLI `print()` | Usage messages in standalone scripts | 2 (kept) |

### Files Modified

| File | Changes |
|------|---------|
| `agents/brain/node_roleplay.py` | 2 prints → logging |
| `agents/brain/identity_agent.py` | 6 prints → logging |
| `agents/brain/context_builders.py` | 2 prints → logging |
| `agents/brain/node_learning.py` | 5 prints → logging (debug level for timers) |
| `agents/dataBase/persona_db.py` | 2 prints → logging |
| `agents/dataBase/main_queries.py` | 6 prints → logging |
| `agents/RAG/retrieve.py` | 5 prints → logging |
| `agents/RAG/save_memory.py` | 2 prints → logging |
| `scripts/run_vacuum.py` | 10 prints → logging |
| `data_normal_mode/ingest_hsk1.py` | 9 prints → logging |

### Notes

- Timer prints in `node_learning.py` use `logger.debug()` to avoid noise in production
- Error prints use `logger.error()` with `exc_info=True` for traceback logging where needed
- CLI scripts (`run_vacuum.py`, `ingest_hsk1.py`) have `logging.basicConfig()` configured for standalone use
- Usage messages in `ingest_hsk_csv.py` and `ingest_document.py` kept as `print()` (appropriate for CLI entry points)
