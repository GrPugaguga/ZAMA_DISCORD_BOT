from typing import List, Dict
from app.init.postgres import get_db_pool
from app.init.model import GPT
from app.services.redis_service import get_cached_documents, cache_documents
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


async def title_search(query: str, limit: int = 10) -> List[Dict]:
    """Search documents by title with Redis caching"""
    try:
        # First, check Redis cache
        cached_documents = await get_cached_documents(query)
        if cached_documents is not None:
            # Apply limit to cached results
            return cached_documents[:limit]
        
        # Cache miss - query database
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            results = await conn.fetch('''
                SELECT 
                    title,
                    content,
                    category,
                    subcategory,
                    keywords
                FROM zama_documents
                WHERE LOWER(title) LIKE LOWER($1)
                LIMIT $2
            ''', f'%{query}%', limit)
            
            documents = [dict(row) for row in results]
            
            # Cache the results for next time
            if documents:
                await cache_documents(query, documents)
            
            return documents
    
    except Exception as e:
        logger.error(f"Title search error: {e}")
        return []