import os
import sys
from pathlib import Path
import psycopg2
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

# Add parent directory to path to allow imports from sibling packages if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain.chains import get_embeddings_model
from brain.identity_agent import extract_cast_from_text
from dataBase.connection import get_db_connection

load_dotenv()

def ingest_pdf(file_path: str, user_id: int = None):
    """
    Reads a PDF file, splits it into chunks, generates embeddings,
    and stores them in the document_store table.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    print(f"🚀 Processing PDF: {file_path}")
    
    try:
        # 1. Read PDF content
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        text = text.replace('\x00', '')
            
        if not text.strip():
            print("⚠️ Warning: No text extracted from PDF. It might be scanned or empty.")
            return

        # 2. Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_text(text)
        print(f"📄 Split into {len(chunks)} chunks.")

        # 3. Generate embeddings
        embedding_model = get_embeddings_model()
        # Batch embedding for efficiency could be done here, 
        # but for simplicity we do one by one or small batches.
        # LangChain's embed_documents handles lists.
        embeddings = embedding_model.embed_documents(chunks)

        # 4. Store in database
        conn = get_db_connection()
        cur = conn.cursor()
        
        raw_filename = os.path.basename(file_path)
        filename = raw_filename[5:] if raw_filename.startswith("temp_") else raw_filename
        
        # Determine current max ID to maybe help with debugging or just rely on SERIAL
        
        inserted_count = 0
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
            inserted_count += 1
            
        conn.commit()
        
        # Determine the doc_id to run Layer A Cast Sweep
        try:
            if user_id is not None:
                cur.execute("SELECT id FROM document_store WHERE filename = %s AND user_id = %s LIMIT 1", (filename, user_id))
            else:
                cur.execute("SELECT id FROM document_store WHERE filename = %s LIMIT 1", (filename,))
            row = cur.fetchone()
            
            if row:
                doc_id = row[0]
                # Combine first ~3000 chars of the text to give to the Identity Agent for Cast Sweep
                sweep_text = text[:3000] 
                extract_cast_from_text(sweep_text, doc_id)
        except Exception as e:
            print(f"⚠️ Could not perform Cast Sweep: {e}")
            
        cur.close()
        conn.close()
        
        print(f"✅ Successfully ingested {inserted_count} chunks from {filename} into document_store.")

    except Exception as e:
        print(f"❌ Error during PDF ingestion: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest_document.py <path_to_pdf>")
    else:
        ingest_pdf(sys.argv[1])
