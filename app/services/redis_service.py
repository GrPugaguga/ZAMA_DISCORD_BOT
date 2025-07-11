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


async def get_cached_categories() -> Optional[List[Dict]]:
    """Get cached categories from Redis"""
    try:
        redis_client = await get_redis_client()
        cache_key = "categories:all"
        
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            logger.debug("Cache hit for categories")
            return json.loads(cached_data)
        
        logger.debug("Cache miss for categories")
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached categories: {e}")
        return None


async def cache_categories(categories: List[Dict], ttl: int = CACHE_TTL * 24):  # Longer TTL for categories
    """Cache categories in Redis"""
    try:
        redis_client = await get_redis_client()
        cache_key = "categories:all"
        
        # Serialize categories to JSON
        cached_data = json.dumps(categories, ensure_ascii=False)
        
        # Set with TTL (24x longer than regular cache)
        await redis_client.setex(cache_key, ttl, cached_data)
        
        logger.debug(f"Cached {len(categories)} categories")
        
    except Exception as e:
        logger.error(f"Error caching categories: {e}")


async def get_cached_titles(categories: List[str]) -> Optional[List[Dict]]:
    """Get cached titles for categories from Redis"""
    try:
        redis_client = await get_redis_client()
        
        all_titles = []
        missing_categories = []
        
        for category in categories:
            cache_key = f"titles:{category}"
            cached_data = await redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit for category: {category}")
                all_titles.extend(json.loads(cached_data))
            else:
                logger.debug(f"Cache miss for category: {category}")
                missing_categories.append(category)
        
        # If any category is missing, return None to trigger full DB query
        if missing_categories:
            logger.debug(f"Missing categories in cache: {missing_categories}")
            return None
        
        return all_titles
        
    except Exception as e:
        logger.error(f"Error getting cached titles: {e}")
        return None


async def cache_titles_by_category(titles_by_category: Dict[str, List[Dict]], ttl: int = CACHE_TTL * 24):
    """Cache titles by category in Redis"""
    try:
        redis_client = await get_redis_client()
        
        for category, titles in titles_by_category.items():
            cache_key = f"titles:{category}"
            
            # Serialize titles to JSON
            cached_data = json.dumps(titles, ensure_ascii=False)
            
            # Set with TTL (12x longer than regular cache)
            await redis_client.setex(cache_key, ttl, cached_data)
            
            logger.debug(f"Cached {len(titles)} titles for category: {category}")
        
    except Exception as e:
        logger.error(f"Error caching titles by category: {e}")


async def get_cached_documents_by_title_category(titles: List[str], categories: List[str]) -> Optional[List[Dict]]:
    """Get cached documents by titles and categories from Redis"""
    try:
        redis_client = await get_redis_client()
        
        all_documents = []
        missing_combinations = []
        
        # Check each title-category combination
        for title in titles:
            for category in categories:
                cache_key = f"docs:{category}:{title}"
                cached_data = await redis_client.get(cache_key)
                
                if cached_data:
                    logger.debug(f"Cache hit for title: {title}, category: {category}")
                    documents = json.loads(cached_data)
                    all_documents.extend(documents)
                else:
                    logger.debug(f"Cache miss for title: {title}, category: {category}")
                    missing_combinations.append((title, category))
        
        # If any combination is missing, return None to trigger full DB query
        if missing_combinations:
            logger.debug(f"Missing combinations in cache: {missing_combinations}")
            return None
        
        return all_documents
        
    except Exception as e:
        logger.error(f"Error getting cached documents: {e}")
        return None


async def cache_documents_by_title_category(documents: List[Dict], ttl: int = CACHE_TTL * 24):
    """Cache documents by title and category in Redis"""
    try:
        redis_client = await get_redis_client()
        
        # Group documents by title and category
        docs_by_title_category = {}
        for doc in documents:
            title = doc.get('title', '')
            category = doc.get('category', '')
            key = f"{category}:{title}"
            
            if key not in docs_by_title_category:
                docs_by_title_category[key] = []
            docs_by_title_category[key].append(doc)
        
        # Cache each title-category combination
        for key, docs in docs_by_title_category.items():
            cache_key = f"docs:{key}"
            
            # Serialize documents to JSON
            cached_data = json.dumps(docs, ensure_ascii=False)
            
            # Set with TTL (24 hours)
            await redis_client.setex(cache_key, ttl, cached_data)
            
            logger.debug(f"Cached {len(docs)} documents for key: {key}")
        
    except Exception as e:
        logger.error(f"Error caching documents by title category: {e}")


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
        
        # Check if categories are cached
        categories_cached = await redis_client.exists("categories:all")
        
        # Get Redis info
        info = await redis_client.info("memory")
        
        return {
            "title_search_entries": len(title_search_keys),
            "categories_cached": bool(categories_cached),
            "memory_used_bytes": info.get("used_memory", 0),
            "memory_used_human": info.get("used_memory_human", "0B")
        }
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {"title_search_entries": 0, "memory_used_bytes": 0, "memory_used_human": "0B"}