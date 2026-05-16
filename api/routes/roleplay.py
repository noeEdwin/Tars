"""Roleplay routes: file listing, upload, and deletion."""
import logging
import os

import asyncio
from fastapi import APIRouter, Depends, UploadFile, File

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
    delete_document_by_filename(current_user_id, filename)
    return {"status": "success", "message": f"Document {filename} deleted"}


@router.post("/upload")
async def upload_roleplay_file(file: UploadFile = File(...), current_user_id: int = Depends(get_current_user)):
    """Receive a PDF file, save it temporarily, and process embeddings."""
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            buffer.write(await file.read())

        logger.info("File %s saved temporarily. Starting RAG processing...", file.filename)

        await asyncio.to_thread(ingest_pdf, temp_file_path, current_user_id)
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return {"status": "success", "filename": file.filename, "message": "Document processed successfully"}
