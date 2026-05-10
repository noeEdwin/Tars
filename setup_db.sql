-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for long-term semantic memory (RAG)
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    normalized_text TEXT,
    last_used_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INT DEFAULT 0,
    has_chinese BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for messages table
CREATE INDEX IF NOT EXISTS idx_messages_normalized ON messages (normalized_text);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_access ON messages (access_count, created_at);

-- Create table for knowledge base (HSK data)
CREATE TABLE IF NOT EXISTS base_conocimiento (
    id SERIAL PRIMARY KEY,
    contenido_zh TEXT,
    pinyin TEXT,
    traduccion_es TEXT,
    nivel_hsk INTEGER,
    categoria TEXT,
    tipo_item TEXT,
    embedding VECTOR(1536)
);

CREATE TABLE IF NOT EXISTS character_personas (
    id SERIAL PRIMARY KEY,
    -- Relación con el PDF original en tu tabla DOCUMENT_STORE
    document_id INT REFERENCES document_store(id) ON DELETE CASCADE,
    
    -- Datos de Identidad
    name VARCHAR(255) NOT NULL,
    archetype VARCHAR(100), -- Ejemplo: "Trickster", "Mentor Cínico", "Héroe reacio"
    
    -- Comportamiento y Actuación (Textos largos para el System Prompt)
    speech_style TEXT,      -- Cadencia, muletillas, formalidad
    traits TEXT,            -- Rasgos de personalidad
    
    -- Reglas de Oro (Usamos JSONB para manejar listas de "Nunca" y "Siempre")
    rules JSONB DEFAULT '[]'::jsonb, 
    
    -- Restricciones de Trama
    knowledge_limit TEXT,   -- Lo que el personaje NO sabe (ej: tecnología moderna)
    emotional_anchor TEXT,  -- Qué lo motiva o le importa en el libro
    
    -- Metadatos para gestión
    is_auto_generated BOOLEAN DEFAULT FALSE, -- Para saber si lo hizo la IA o tú
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Evita duplicar el mismo personaje para el mismo libro
    UNIQUE(document_id, name)
);

-- Índice para búsquedas rápidas cuando TARS necesita "ponerse la máscara"
CREATE INDEX idx_persona_name ON character_personas (name);

-- Table for tracking async vacuum jobs
CREATE TABLE IF NOT EXISTS vacuum_jobs (
    job_id UUID PRIMARY KEY,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    progress INT DEFAULT 0,
    current_stage TEXT,
    stats JSONB DEFAULT '{}',
    error_log TEXT
);

-- ─── Tabla de Usuarios (Autenticación) ───────────────────────────────────────
-- La tabla `users` YA EXISTE en Supabase con ID Integer (SERIAL).
-- Ejecuta los ALTER si necesitas añadir las nuevas columnas de perfil:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name TEXT;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS learning_goals TEXT DEFAULT 'Travel';
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users (email);