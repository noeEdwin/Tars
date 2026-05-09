-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table for chat history
CREATE TABLE IF NOT EXISTS historial_chat (
    id SERIAL PRIMARY KEY,
    rol TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    embedding VECTOR(1536), -- Dimension based on OpenAI embedding model usually used
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

-- ─── Tabla de Usuarios (Autenticación) ───────────────────────────────────────
-- ⚠️  La tabla `users` YA EXISTE en Supabase con ID Integer (SERIAL).
--     NO ejecutes el bloque de abajo si la tabla ya existe.
--     Solo úsalo como referencia de la estructura real, o ejecuta los ALTER
--     si necesitas añadir las nuevas columnas de perfil.

-- EJECUTA ESTO EN SUPABASE PARA AÑADIR LAS COLUMNAS FALTANTES:
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS learning_goals TEXT DEFAULT 'Travel';
-- ALTER TABLE users ADD COLUMN IF NOT EXISTS interests TEXT DEFAULT '';

-- Estructura de referencia (NO re-crear si ya existe):
-- CREATE TABLE IF NOT EXISTS users (
--     id              SERIAL      PRIMARY KEY,
--     username        TEXT        NOT NULL UNIQUE,
--     first_name      TEXT        NOT NULL,
--     last_name       TEXT        NOT NULL,
--     email           TEXT        UNIQUE,
--     hashed_password TEXT        NOT NULL,
--     hsk_level       INTEGER     NOT NULL DEFAULT 1,
--     native_language TEXT        NOT NULL DEFAULT 'es',
--     learning_goals  TEXT        DEFAULT 'Travel',
--     interests       TEXT        DEFAULT ''
-- );

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users (email);