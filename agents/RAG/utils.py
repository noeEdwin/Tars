from agents.brain.chains import get_embeddings_model

_embedding_client = None
_turn_cache: dict[str, list[float]] = {}


def get_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for the given text using the configured OpenAI client.
    Uses per-turn cache to avoid redundant API calls for the same text.
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = get_embeddings_model()

    if text in _turn_cache:
        return _turn_cache[text]

    vector = _embedding_client.embed_query(text)
    _turn_cache[text] = vector
    return vector


def clear_turn_cache():
    """Call at the start of each user turn to reset the embedding cache."""
    _turn_cache.clear()
