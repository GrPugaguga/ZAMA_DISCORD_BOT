import os
from typing import Optional
import redis.asyncio as redis

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def init_redis_client(redis_url: str = None) -> redis.Redis:
    """Initialize Redis client"""
    from app.init.config import get_settings
    
    global _redis_client
    if _redis_client is None:
        if redis_url is None:
            config = get_settings()
            redis_url = config.REDIS_URL
        
        if not redis_url:
            raise ValueError("REDIS_URL is required")
        
        config = get_settings()
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=config.REDIS_HEALTH_CHECK_INTERVAL
        )
    return _redis_client


async def get_redis_client() -> redis.Redis:
    """Get existing Redis client"""
    global _redis_client
    if _redis_client is None:
        raise ValueError("Redis client is not initialized. Call init_redis_client() first.")
    return _redis_client


async def close_redis_client():
    """Close Redis client"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None