-- Create table for generic document storage (PDFs, etc.)
CREATE TABLE IF NOT EXISTS document_store (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster vector similarity search (IVFFlat or HNSW)
-- For now, we rely on the extension being enabled in setup_db.sql
CREATE INDEX IF NOT EXISTS document_embedding_idx ON document_store USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
