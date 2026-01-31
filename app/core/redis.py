"""
Redis Connection and Cache Management
"""

import redis.asyncio as aioredis
import redis
from typing import Optional
import json
from datetime import timedelta

from app.core.config import settings


class RedisClient:
    """Synchronous Redis client wrapper"""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    def connect(self) -> redis.Redis:
        """Create Redis connection"""
        if self._client is None:
            self._client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True
            )
        return self._client
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance"""
        if self._client is None:
            self.connect()
        return self._client
    
    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            self._client = None
    
    def set_with_expiry(self, key: str, value: dict, expiry_seconds: int) -> bool:
        """Set a key with expiration time"""
        try:
            self.client.setex(
                name=key,
                time=expiry_seconds,
                value=json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    def get(self, key: str) -> Optional[dict]:
        """Get value by key"""
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key"""
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis EXISTS error: {e}")
            return False
    
    def get_ttl(self, key: str) -> int:
        """Get remaining TTL for a key in seconds"""
        try:
            return self.client.ttl(key)
        except Exception as e:
            print(f"Redis TTL error: {e}")
            return -1
    
    def increment(self, key: str, expiry_seconds: Optional[int] = None) -> int:
        """Increment a counter with optional expiry"""
        try:
            count = self.client.incr(key)
            if expiry_seconds and count == 1:
                self.client.expire(key, expiry_seconds)
            return count
        except Exception as e:
            print(f"Redis INCR error: {e}")
            return 0


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Get Redis client dependency"""
    return redis_client
