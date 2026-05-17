"""
FastAPI exception handlers for Tars.
Maps custom exception classes to appropriate HTTP responses.
"""
import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from agents.errors import (
    TarsError,
    DatabaseError,
    RAGError,
    AuthenticationError,
    ValidationError,
    TTSError,
    ResourceNotFoundError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AuthenticationError.DuplicateUser)
    async def duplicate_user_handler(request: Request, exc: AuthenticationError.DuplicateUser):
        return JSONResponse(
            status_code=409,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(AuthenticationError.InvalidCredentials)
    async def invalid_credentials_handler(request: Request, exc: AuthenticationError.InvalidCredentials):
        return JSONResponse(
            status_code=401,
            content={"detail": exc.message, "code": exc.code},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthenticationError.UserNotFound)
    async def user_not_found_handler(request: Request, exc: AuthenticationError.UserNotFound):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(DatabaseError.ConnectionError)
    async def db_connection_error_handler(request: Request, exc: DatabaseError.ConnectionError):
        logger.critical("Database connection failure: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=503,
            content={"detail": "Service temporarily unavailable", "code": exc.code}
        )

    @app.exception_handler(DatabaseError.QueryError)
    async def db_query_error_handler(request: Request, exc: DatabaseError.QueryError):
        logger.error("Database query error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "code": exc.code}
        )

    @app.exception_handler(DatabaseError)
    async def db_error_handler(request: Request, exc: DatabaseError):
        logger.error("Database error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": "Database error", "code": exc.code}
        )

    @app.exception_handler(RAGError.RetrievalError)
    async def rag_retrieval_error_handler(request: Request, exc: RAGError.RetrievalError):
        logger.error("RAG retrieval error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(RAGError.IngestionError)
    async def rag_ingestion_error_handler(request: Request, exc: RAGError.IngestionError):
        logger.error("RAG ingestion error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(RAGError)
    async def rag_error_handler(request: Request, exc: RAGError):
        logger.error("RAG error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(TTSError)
    async def tts_error_handler(request: Request, exc: TTSError):
        logger.error("TTS error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=500,
            content={"detail": exc.message, "code": exc.code}
        )

    @app.exception_handler(TarsError)
    async def tars_error_handler(request: Request, exc: TarsError):
        logger.error("Tars error: %s", exc.message, exc_info=exc.original)
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code}
        )
