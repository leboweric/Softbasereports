import redis
import json
import os
import logging
from datetime import timedelta
from typing import Optional, Any, Callable
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """Redis caching service for dashboard and report data"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """Connect to Redis if available"""
        try:
            # Get Redis URL from environment
            redis_url = os.environ.get('REDIS_URL')
            
            if redis_url:
                # Parse Redis URL and connect
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                    retry=redis.Retry(backoff=redis.ExponentialBackoff(cap=10, base=0.1), retries=3)
                )
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("Redis cache connected successfully")
            else:
                logger.info("Redis URL not found, caching disabled")
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {str(e)}")
            self.enabled = False
            self.redis_client = None
    
    def _make_key(self, prefix: str, params: dict = None) -> str:
        """Create a cache key from prefix and parameters"""
        if params:
            # Sort params for consistent keys
            sorted_params = json.dumps(params, sort_keys=True)
            param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
            return f"{prefix}:{param_hash}"
        return prefix
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL"""
        if not self.enabled:
            return
        
        try:
            json_value = json.dumps(value)
            self.redis_client.setex(key, ttl_seconds, json_value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
    
    def delete(self, pattern: str):
        """Delete cache entries matching pattern"""
        if not self.enabled:
            return
        
        try:
            keys = self.redis_client.keys(f"{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Deleted {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.error(f"Cache delete error for pattern {pattern}: {str(e)}")
    
    def cache_query(self, cache_key: str, query_func: Callable, ttl_seconds: int = 300, force_refresh: bool = False) -> Any:
        """
        Cache the result of a query function
        
        Args:
            cache_key: Unique key for this query
            query_func: Function that executes the query
            ttl_seconds: Time to live in seconds (default 5 minutes)
            force_refresh: Force refresh the cache
        
        Returns:
            Query result (from cache or fresh)
        """
        # Check cache first unless force refresh
        if not force_refresh:
            cached_result = self.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        # Execute query
        logger.debug(f"Cache miss for {cache_key}, executing query")
        result = query_func()
        
        # Store in cache
        self.set(cache_key, result, ttl_seconds)
        
        return result
    
    def invalidate_dashboard(self):
        """Invalidate all dashboard cache entries"""
        self.delete("dashboard:")
        logger.info("Dashboard cache invalidated")


# Global cache instance
cache_service = CacheService()