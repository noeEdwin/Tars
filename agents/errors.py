"""
Custom exception hierarchy for Tars.
"""


class TarsError(Exception):
    """Base for all Tars-specific exceptions."""
    code: str = "internal_error"
    status_code: int = 500

    def __init__(self, message: str, original: Exception | None = None):
        super().__init__(message)
        self.message = message
        self.original = original


class DatabaseError(TarsError):
    """PostgreSQL / connection pool failures."""
    code = "database_error"

    class ConnectionError(TarsError):
        """Pool exhausted, network timeout, SSL failure."""
        code = "db_connection_error"
        status_code = 503

    class QueryError(TarsError):
        """SQL execution failure, syntax error, constraint violation."""
        code = "db_query_error"
        status_code = 500


class RAGError(TarsError):
    """Vector search, embedding, or document ingestion failures."""
    code = "rag_error"

    class RetrievalError(TarsError):
        """Vector search or similarity lookup failed."""
        code = "rag_retrieval_error"
        status_code = 500

    class IngestionError(TarsError):
        """PDF parsing, embedding generation, or storage failed."""
        code = "rag_ingestion_error"
        status_code = 500


class AuthenticationError(TarsError):
    """Login, registration, token validation failures."""
    code = "auth_error"
    status_code = 401

    class InvalidCredentials(TarsError):
        code = "invalid_credentials"
        status_code = 401

    class UserNotFound(TarsError):
        code = "user_not_found"
        status_code = 404

    class DuplicateUser(TarsError):
        code = "duplicate_user"
        status_code = 409


class ValidationError(TarsError):
    """Business-logic validation failures (not Pydantic schema errors)."""
    code = "validation_error"
    status_code = 422


class TTSError(TarsError):
    """Audio synthesis failed."""
    code = "tts_error"
    status_code = 500


class ResourceNotFoundError(TarsError):
    """Generic 404 for documents, jobs, personas, etc."""
    code = "not_found"
    status_code = 404
