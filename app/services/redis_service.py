import json
import hashlib
from typing import List, Dict, Optional
from app.init.redis import get_redis_client
from app.init.config import get_settings
import logging

logger = logging.getLogger(__name__)

# Get cache TTL from config
config = get_settings()
CACHE_TTL = config.CACHE_TTL_SECONDS


def _normalize_query(query: str) -> str:
    """Normalize query for consistent caching"""
    return query.lower().strip()


def _generate_cache_key(query: str) -> str:
    """Generate cache key for title search"""
    normalized_query = _normalize_query(query)
    # Use hash for consistent key generation
    query_hash = hashlib.md5(normalized_query.encode()).hexdigest()
    return f"title_search:{query_hash}"


async def get_cached_documents(query: str) -> Optional[List[Dict]]:
    """Get cached documents from Redis"""
    try:
        redis_client = await get_redis_client()
        cache_key = _generate_cache_key(query)
        
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return json.loads(cached_data)
        
        logger.debug(f"Cache miss for query: {query[:50]}...")
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached documents: {e}")
        return None


async def cache_documents(query: str, documents: List[Dict], ttl: int = CACHE_TTL):
    """Cache documents in Redis"""
    try:
        redis_client = await get_redis_client()
        cache_key = _generate_cache_key(query)
        
        # Serialize documents to JSON
        cached_data = json.dumps(documents, ensure_ascii=False)
        
        # Set with TTL
        await redis_client.setex(cache_key, ttl, cached_data)
        
        logger.debug(f"Cached {len(documents)} documents for query: {query[:50]}...")
        
    except Exception as e:
        logger.error(f"Error caching documents: {e}")


async def clear_cache_pattern(pattern: str = "title_search:*"):
    """Clear cache by pattern (useful for cache invalidation)"""
    try:
        redis_client = await get_redis_client()
        
        # Get all keys matching pattern
        keys = await redis_client.keys(pattern)
        
        if keys:
            # Delete all matching keys
            await redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
        else:
            logger.info(f"No cache entries found matching pattern: {pattern}")
            
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")


async def get_cache_stats() -> Dict[str, int]:
    """Get cache statistics"""
    try:
        redis_client = await get_redis_client()
        
        # Count title_search keys
        title_search_keys = await redis_client.keys("title_search:*")
        
        # Get Redis info
        info = await redis_client.info("memory")
        
        return {
            "title_search_entries": len(title_search_keys),
            "memory_used_bytes": info.get("used_memory", 0),
            "memory_used_human": info.get("used_memory_human", "0B")
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"title_search_entries": 0, "memory_used_bytes": 0, "memory_used_human": "0B"}