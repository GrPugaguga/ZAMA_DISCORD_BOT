import time
from typing import Tuple, Optional
from app.init.redis import get_redis_client
from app.init.config import get_settings
import logging

logger = logging.getLogger(__name__)

# Get settings
config = get_settings()
USER_LIMIT_PER_MINUTE = config.USER_RATE_LIMIT_PER_MINUTE
CHANNEL_LIMIT_PER_MINUTE = config.CHANNEL_RATE_LIMIT_PER_MINUTE
RATE_LIMIT_TTL = config.RATE_LIMIT_TTL


def _get_current_minute_window() -> int:
    """Get current minute window for rate limiting"""
    return int(time.time()) // 60


def _get_rate_limit_keys(user_id: int, channel_id: int) -> Tuple[str, str]:
    """Generate Redis keys for user and channel rate limits"""
    minute_window = _get_current_minute_window()
    user_key = f"rate_limit:user:{user_id}:{minute_window}"
    channel_key = f"rate_limit:channel:{channel_id}:{minute_window}"
    return user_key, channel_key


async def check_rate_limit(user_id: int, channel_id: int) -> Tuple[bool, Optional[int]]:
    """
    Check if user and channel are within rate limits
    
    Args:
        user_id: Discord user ID
        channel_id: Discord channel ID
        
    Returns:
        Tuple of (is_allowed: bool, seconds_to_wait: Optional[int])
    """
    try:
        redis_client = await get_redis_client()
        user_key, channel_key = _get_rate_limit_keys(user_id, channel_id)
        
        # Get current counts
        pipe = redis_client.pipeline()
        pipe.get(user_key)
        pipe.get(channel_key)
        current_counts = await pipe.execute()
        
        user_count = int(current_counts[0] or 0)
        channel_count = int(current_counts[1] or 0)
        
        # Check limits
        user_limit_exceeded = user_count >= USER_LIMIT_PER_MINUTE
        channel_limit_exceeded = channel_count >= CHANNEL_LIMIT_PER_MINUTE
        
        if user_limit_exceeded or channel_limit_exceeded:
            # Calculate seconds to wait (until next minute window)
            current_time = time.time()
            next_minute = (int(current_time) // 60 + 1) * 60
            seconds_to_wait = int(next_minute - current_time)
            
            # Log rate limit hit
            limit_type = "user" if user_limit_exceeded else "channel"
            limit_id = user_id if user_limit_exceeded else channel_id
            current_limit = user_count if user_limit_exceeded else channel_count
            max_limit = USER_LIMIT_PER_MINUTE if user_limit_exceeded else CHANNEL_LIMIT_PER_MINUTE
            
            logger.warning(f"Rate limit exceeded - {limit_type} {limit_id}: {current_limit}/{max_limit}")
            
            return False, seconds_to_wait
        
        # Increment counters if within limits
        pipe = redis_client.pipeline()
        
        # Increment user counter
        pipe.incr(user_key)
        pipe.expire(user_key, RATE_LIMIT_TTL)
        
        # Increment channel counter  
        pipe.incr(channel_key)
        pipe.expire(channel_key, RATE_LIMIT_TTL)
        
        await pipe.execute()
        
        logger.debug(f"Rate limit check passed - user {user_id}: {user_count + 1}/{USER_LIMIT_PER_MINUTE}, "
                    f"channel {channel_id}: {channel_count + 1}/{CHANNEL_LIMIT_PER_MINUTE}")
        
        return True, None
        
    except Exception as e:
        logger.error(f"Rate limit check error: {e}")
        # On error, allow the request (fail open)
        return True, None


async def get_rate_limit_status(user_id: int, channel_id: int) -> dict:
    """
    Get current rate limit status for user and channel
    
    Returns:
        Dict with current usage and limits
    """
    try:
        redis_client = await get_redis_client()
        user_key, channel_key = _get_rate_limit_keys(user_id, channel_id)
        
        # Get current counts
        pipe = redis_client.pipeline()
        pipe.get(user_key)
        pipe.get(channel_key)
        current_counts = await pipe.execute()
        
        user_count = int(current_counts[0] or 0)
        channel_count = int(current_counts[1] or 0)
        
        return {
            "user": {
                "current": user_count,
                "limit": USER_LIMIT_PER_MINUTE,
                "remaining": max(0, USER_LIMIT_PER_MINUTE - user_count)
            },
            "channel": {
                "current": channel_count,
                "limit": CHANNEL_LIMIT_PER_MINUTE,
                "remaining": max(0, CHANNEL_LIMIT_PER_MINUTE - channel_count)
            },
            "window_resets_in": RATE_LIMIT_TTL - (int(time.time()) % 60)
        }
        
    except Exception as e:
        logger.error(f"Rate limit status error: {e}")
        return {
            "user": {"current": 0, "limit": USER_LIMIT_PER_MINUTE, "remaining": USER_LIMIT_PER_MINUTE},
            "channel": {"current": 0, "limit": CHANNEL_LIMIT_PER_MINUTE, "remaining": CHANNEL_LIMIT_PER_MINUTE},
            "window_resets_in": 60
        }


async def reset_rate_limit(user_id: int = None, channel_id: int = None):
    """
    Reset rate limits for specific user or channel (admin function)
    
    Args:
        user_id: Reset all rate limits for this user
        channel_id: Reset all rate limits for this channel
    """
    try:
        redis_client = await get_redis_client()
        
        if user_id:
            # Reset user rate limits for all time windows
            pattern = f"rate_limit:user:{user_id}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Reset rate limits for user {user_id}")
        
        if channel_id:
            # Reset channel rate limits for all time windows
            pattern = f"rate_limit:channel:{channel_id}:*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                logger.info(f"Reset rate limits for channel {channel_id}")
                
    except Exception as e:
        logger.error(f"Rate limit reset error: {e}")