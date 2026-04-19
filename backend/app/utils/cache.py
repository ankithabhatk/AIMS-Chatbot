"""
Caching utilities for query and embedding responses
- Redis integration for caching
- TTL-based cache expiration
- Cache key generation
"""

import json
import hashlib
import logging
from typing import Any, Optional
from redis import Redis
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheManager:
    """Redis-based cache manager"""
    
    def __init__(self):
        try:
            self.redis = Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis.ping()
            logger.info("✅ Connected to Redis cache")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            self.redis = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis:
            return None
        try:
            value = self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL"""
        if not self.redis:
            return False
        try:
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.redis:
            return False
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    @staticmethod
    def generate_key(prefix: str, *args) -> str:
        """Generate cache key from arguments"""
        key_str = f"{prefix}:{'_'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache instance
cache = CacheManager()
