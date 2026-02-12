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

