import sys
from pathlib import Path

# Add parent path to allow imports from sibling packages
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brain.chains import get_embeddings_model

_embedding_client = None

def get_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for the given text using the configured OpenAI client.
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = get_embeddings_model()
    
    # embed_query is specifically for queries/documents, distinct from embed_documents
    return _embedding_client.embed_query(text)
