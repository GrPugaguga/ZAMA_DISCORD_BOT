from typing import List, Dict
from app.init.postgres import get_db_pool
from app.init.model import GPT
import logging

logger = logging.getLogger(__name__)


async def vector_search(query: str, limit: int = 5) -> List[Dict]:
    """Search documents by vector similarity"""
    try:
        client = GPT()
        embedding_str = await client.generate_embedding(query)
        
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            results = await conn.fetch('''
                SELECT 
                    title,
                    content,
                    category,
                    subcategory,
                    keywords,
                    1 - (content_vector <=> $1::vector) as similarity
                FROM zama_documents
                ORDER BY content_vector <=> $1::vector
                LIMIT $2
            ''', embedding_str, limit)
            
            return [dict(row) for row in results]
    
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []
