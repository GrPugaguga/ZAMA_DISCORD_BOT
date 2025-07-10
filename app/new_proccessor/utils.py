from typing import List, Dict
from app.init.postgres import get_db_pool
from app.init.model import GPT
import logging

logger = logging.getLogger(__name__)


async def vector_search(embedding_str: str, categories: List[str] ,limit: int = 5) -> List[Dict]:
    """Search documents by vector similarity"""
    try:
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            results = await conn.fetch('''
                SELECT 
                    title,
                    content,
                    link,
                    category,
                    GREATEST(
                        1 - (vector_title <=> $1::vector),
                        1 - (vector_content <=> $1::vector)
                    ) as similarity
                FROM zama_docs
                WHERE category = $2 OR category = $3
                ORDER BY GREATEST(
                    1 - (vector_title <=> $1::vector),
                    1 - (vector_content <=> $1::vector)
                    ) DESC
                LIMIT $4
            ''', embedding_str, categories[0], categories[1], limit)
            
            return [dict(row) for row in results]
    
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []
