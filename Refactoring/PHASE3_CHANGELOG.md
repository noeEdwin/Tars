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
