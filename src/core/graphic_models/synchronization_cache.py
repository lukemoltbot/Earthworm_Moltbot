"""
Cache for performance optimization in synchronization.
"""

from typing import Dict, Any, Optional
import time


class SynchronizationCache:
    """
    Cache for depth-to-pixel mappings and other expensive calculations.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        if key in self._cache:
            self._timestamps[key] = time.time()
            return self._cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set cached value."""
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def _evict_oldest(self):
        """Evict oldest cache entry."""
        if not self._timestamps:
            return
        oldest_key = min(self._timestamps, key=self._timestamps.get)
        del self._cache[oldest_key]
        del self._timestamps[oldest_key]
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        self._timestamps.clear()
    
    def invalidate(self, key_prefix: str):
        """Invalidate all cache entries with given prefix."""
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(key_prefix)]
        for key in keys_to_delete:
            del self._cache[key]
            del self._timestamps[key]