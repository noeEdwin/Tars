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