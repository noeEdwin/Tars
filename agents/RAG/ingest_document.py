"""
Ingest a PDF document into the document_store table.

Used by the /roleplay/upload API endpoint.
Also runnable as a CLI tool for testing.

Usage:
    python agents/RAG/ingest_document.py <path_to_pdf>
"""
import logging
import os
import sys

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import RealDictCursor

from agents.brain.chains import get_embeddings_model
from agents.brain.identity_agent import extract_cast_from_text
from agents.dataBase.pool import get_db_connection
from agents.errors import RAGError

load_dotenv()

logger = logging.getLogger(__name__)


def ingest_pdf(file_path: str, user_id: int = None):
    """
    Read a PDF file, split it into chunks, generate embeddings,
    and store them in the document_store table.
    Runs Cast Sweep to auto-extract character personas.
    """
    if not os.path.exists(file_path):
        logger.error("File not found: %s", file_path)
        return

    logger.info("Processing PDF: %s", file_path)

    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        text = text.replace("\x00", "")

        if not text.strip():
            logger.warning("No text extracted from PDF. It might be scanned or empty.")
            return

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        logger.info("Split into %d chunks.", len(chunks))

        embedding_model = get_embeddings_model()
        embeddings = embedding_model.embed_documents(chunks)

        raw_filename = os.path.basename(file_path)
        filename = raw_filename[5:] if raw_filename.startswith("temp_") else raw_filename

        with get_db_connection() as conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    for chunk, embedding in zip(chunks, embeddings):
                        if user_id is not None:
                            query = """
                                INSERT INTO document_store (filename, content, embedding, user_id)
                                VALUES (%s, %s, %s, %s)
                            """
                            cur.execute(query, (filename, chunk, embedding, user_id))
                        else:
                            query = """
                                INSERT INTO document_store (filename, content, embedding)
                                VALUES (%s, %s, %s)
                            """
                            cur.execute(query, (filename, chunk, embedding))

                    conn.commit()

                    try:
                        if user_id is not None:
                            cur.execute(
                                "SELECT id FROM document_store WHERE filename = %s AND user_id = %s LIMIT 1",
                                (filename, user_id)
                            )
                        else:
                            cur.execute("SELECT id FROM document_store WHERE filename = %s LIMIT 1", (filename,))
                        row = cur.fetchone()

                        if row:
                            doc_id = row["id"]
                            sweep_text = text[:3000]
                            extract_cast_from_text(sweep_text, doc_id)
                    except Exception as e:
                        logger.warning("Could not perform Cast Sweep: %s", e)
            except psycopg2.Error as e:
                conn.rollback()
                logger.error("Error during PDF ingestion: %s", e, exc_info=True)
                raise RAGError.IngestionError(f"Failed to ingest PDF '{filename}'", original=e) from e

        logger.info("Successfully ingested %d chunks from %s into document_store.", len(chunks), filename)

    except RAGError:
        raise
    except Exception as e:
        logger.error("Error during PDF ingestion: %s", e, exc_info=True)
        raise RAGError.IngestionError(f"Failed to process PDF '{file_path}'", original=e) from e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python agents/RAG/ingest_document.py <path_to_pdf>")
        sys.exit(1)

    ingest_pdf(sys.argv[1])
