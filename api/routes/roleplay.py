"""Roleplay routes: file listing, upload, and deletion."""
import logging
import os

import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from agents.dataBase.main_queries import (
    get_roleplay_contexts,
    delete_document_by_filename,
)
from agents.RAG.ingest_document import ingest_pdf
from auth.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/files")
def get_roleplay_files(current_user_id: int = Depends(get_current_user)):
    filenames = get_roleplay_contexts(current_user_id)
    return {"files": filenames}


@router.delete("/files/{filename:path}")
def delete_roleplay_file(filename: str, current_user_id: int = Depends(get_current_user)):
    """Delete a roleplay document."""
    success = delete_document_by_filename(current_user_id, filename)
    if success:
        return {"status": "success", "message": f"Document {filename} deleted"}
    else:
        raise HTTPException(status_code=500, detail="Error deleting file")


@router.post("/upload")
async def upload_roleplay_file(file: UploadFile = File(...), current_user_id: int = Depends(get_current_user)):
    """Receive a PDF file, save it temporarily, and process embeddings."""
    temp_file_path = None
    try:
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        logger.info("File %s saved temporarily. Starting RAG processing...", file.filename)

        await asyncio.to_thread(ingest_pdf, temp_file_path, current_user_id)

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return {"status": "success", "filename": file.filename, "message": "Document processed successfully"}

    except Exception as e:
        logger.error("Error processing uploaded file: %s", e)
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail="Document ingestion failed")
