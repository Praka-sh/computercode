from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
from typing import List, Optional
import json


async def create_vector_extension(session: AsyncSession):
    """Create pgvector extension if not exists."""
    await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await session.commit()


async def create_hnsw_index(
    session: AsyncSession,
    table: str,
    column: str,
    m: int = 16,
    ef_construction: int = 64,
):
    """Create HNSW index for vector similarity search."""
    await session.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS {table}_{column}_hnsw_idx "
            f"ON {table} USING hnsw ({column} vector_cosine_ops) "
            f"WITH (m = {m}, ef_construction = {ef_construction})"
        )
    )
    await session.commit()


async def create_ivfflat_index(
    session: AsyncSession,
    table: str,
    column: str,
    lists: int = 100,
):
    """Create IVFFlat index for vector similarity search."""
    await session.execute(
        text(
            f"CREATE INDEX IF NOT EXISTS {table}_{column}_ivfflat_idx "
            f"ON {table} USING ivfflat ({column} vector_cosine_ops) "
            f"WITH (lists = {lists})"
        )
    )
    await session.commit()


def vector_to_list(vector) -> List[float]:
    """Convert pgvector result to Python list."""
    if vector is None:
        return None
    if isinstance(vector, list):
        return vector
    if isinstance(vector, str):
        # Parse string format: '[1,2,3]' or '{1,2,3}'
        return json.loads(vector.replace('{', '[').replace('}', ']'))
    return list(vector)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)