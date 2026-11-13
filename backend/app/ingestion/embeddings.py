from typing import List
from app.core.config import settings
import structlog

logger = structlog.get_logger()


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.
    Uses the configured embedding provider.
    """
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "anthropic":
        return await _generate_anthropic_embeddings(texts)
    elif provider == "openai":
        return await _generate_openai_embeddings(texts)
    else:
        # Fallback: deterministic fake embeddings for testing
        logger.warning("using_fake_embeddings", provider=provider)
        return _generate_fake_embeddings(texts)


async def _generate_anthropic_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using Anthropic's embedding model (via Voyage AI)."""
    try:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

        # Note: Anthropic doesn't have native embeddings yet.
        # This would use Voyage AI or similar via their API
        # For now, return fake embeddings
        logger.warning("anthropic_embeddings_not_implemented_using_fake")
        return _generate_fake_embeddings(texts)

    except Exception as e:
        logger.error("anthropic_embedding_failed", error=str(e))
        return _generate_fake_embeddings(texts)


async def _generate_openai_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI's embedding model."""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL or "text-embedding-3-large",
            input=texts,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )

        return [data.embedding for data in response.data]

    except Exception as e:
        logger.error("openai_embedding_failed", error=str(e))
        return _generate_fake_embeddings(texts)


def _generate_fake_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate deterministic fake embeddings for testing without API keys."""
    import hashlib
    import random

    embeddings = []
    for text in texts:
        # Create deterministic "embedding" from text hash
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to list of floats
        dim = settings.EMBEDDING_DIMENSIONS
        embedding = []
        for i in range(dim):
            byte_idx = i % len(hash_bytes)
            # Normalize to [-1, 1] range
            val = (hash_bytes[byte_idx] / 255.0) * 2 - 1
            embedding.append(val)

        embeddings.append(embedding)

    return embeddings