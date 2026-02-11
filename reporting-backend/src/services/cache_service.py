import redis
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
import json
import os
import logging
from datetime import timedelta
from typing import Optional, Any, Callable
import hashlib

logger = logging.getLogger(__name__)

class CacheService:
    """Redis caching service for dashboard and report data with in-memory fallback"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}  # Fallback in-memory cache
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """Connect to Redis if available"""
        try:
            # Get Redis URL from environment
            redis_url = os.environ.get('REDIS_URL')
            
            if redis_url:
                logger.info(f"🔌 Attempting Redis connection (URL found, length={len(redis_url)})")
                # Parse Redis URL and connect with proper retry imports
                retry_strategy = Retry(
                    backoff=ExponentialBackoff(cap=10, base=0.1),
                    retries=3
                )
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                    retry=retry_strategy
                )
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                logger.info("✅ Redis cache connected successfully")
            else:
                logger.warning("⚠️ REDIS_URL not found in environment variables, using in-memory cache fallback")
                self.enabled = True  # Enable caching with in-memory fallback
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {type(e).__name__}: {str(e)}")
            logger.warning("⚠️ Falling back to in-memory cache")
            self.enabled = True  # Enable caching with in-memory fallback
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
        """Get value from cache (Redis or in-memory fallback)"""
        if not self.enabled:
            return None
        
        try:
            if self.redis_client:
                # Use Redis if available
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Use in-memory cache as fallback
                import time
                cache_item = self.memory_cache.get(key)
                if cache_item:
                    if time.time() < cache_item['expires']:
                        return cache_item['value']
                    else:
                        # Expired, remove from cache
                        del self.memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {str(e)}")
        
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set value in cache with TTL (Redis or in-memory fallback)"""
        if not self.enabled:
            return
        
        try:
            if self.redis_client:
                # Use Redis if available
                json_value = json.dumps(value)
                self.redis_client.setex(key, ttl_seconds, json_value)
            else:
                # Use in-memory cache as fallback
                import time
                self.memory_cache[key] = {
                    'value': value,
                    'expires': time.time() + ttl_seconds
                }
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {str(e)}")
    
    def delete(self, pattern: str):
        """Delete cache entries matching pattern (Redis or in-memory fallback)"""
        if not self.enabled:
            return
        
        try:
            if self.redis_client:
                # Use Redis if available
                keys = self.redis_client.keys(f"{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Deleted {len(keys)} cache entries matching {pattern}")
            else:
                # Use in-memory cache as fallback
                keys_to_delete = [key for key in self.memory_cache.keys() if key.startswith(pattern)]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                if keys_to_delete:
                    logger.info(f"Deleted {len(keys_to_delete)} cache entries matching {pattern}")
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
                logger.info(f"✅ CACHE HIT for {cache_key} (using {'Redis' if self.redis_client else 'memory'})")
                return cached_result
        
        # Execute query
        if force_refresh:
            logger.info(f"🔄 FORCE REFRESH for {cache_key}, bypassing cache")
        else:
            logger.info(f"❌ CACHE MISS for {cache_key}, executing query")
        
        result = query_func()
        
        # Store in cache
        self.set(cache_key, result, ttl_seconds)
        logger.info(f"💾 Cached result for {cache_key} (TTL: {ttl_seconds}s, backend: {'Redis' if self.redis_client else 'memory'})")
        
        return result
    
    def invalidate_dashboard(self):
        """Invalidate all dashboard cache entries"""
        self.delete("dashboard:")
        logger.info("Dashboard cache invalidated")


    def get_status(self) -> dict:
        """Return cache status for diagnostics"""
        status = {
            'enabled': self.enabled,
            'backend': 'redis' if self.redis_client else 'memory',
            'redis_url_set': bool(os.environ.get('REDIS_URL')),
        }
        if self.redis_client:
            try:
                info = self.redis_client.info('memory')
                status['redis_connected'] = True
                status['redis_used_memory'] = info.get('used_memory_human', 'unknown')
                status['redis_keys'] = self.redis_client.dbsize()
            except Exception as e:
                status['redis_connected'] = False
                status['redis_error'] = str(e)
        else:
            status['memory_cache_keys'] = len(self.memory_cache)
        return status


# Global cache instance
cache_service = CacheService()