from typing import Optional
import asyncpg

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool(database_url: str, min_size: int = None, max_size: int = None, command_timeout: int = None) -> asyncpg.Pool:
    """Initialize database connection pool"""
    from app.init.config import get_settings
    
    global _db_pool
    if _db_pool is None:
        config = get_settings()
        _db_pool = await asyncpg.create_pool(
            database_url,
            min_size=min_size or config.DB_MIN_SIZE,
            max_size=max_size or config.DB_MAX_SIZE,
            command_timeout=command_timeout or config.DB_COMMAND_TIMEOUT
        )
    return _db_pool


async def get_db_pool() -> asyncpg.Pool:
    """Get existing connection pool"""
    global _db_pool
    if _db_pool is None:
        raise ValueError("Database pool is not initialized. Call init_db_pool() first.")
    return _db_pool


async def close_db_pool():
    """Close connection pool"""
    global _db_pool
    if _db_pool:
        await _db_pool.close()
        _db_pool = None
