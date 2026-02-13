"""
ViewportCacheManager - Manages caching of pre-rendered views for smooth scrolling.

This class provides:
1. Predictive rendering of adjacent depth ranges
2. Progressive quality rendering (low-res → high-res)
3. Background thread rendering for off-screen views
4. Memory-aware cache management
5. Integration with ScrollOptimizer
"""

import threading
import time
import weakref
from collections import OrderedDict
from typing import Dict, List, Tuple, Optional, Callable, Any
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap, QPainter


class RenderTask:
    """Represents a rendering task for predictive caching."""
    
    def __init__(self, view_range: Tuple[float, float], priority: int = 0, 
                 quality: float = 1.0):
        """
        Initialize a render task.
        
        Args:
            view_range: (min_depth, max_depth) to render
            priority: Higher priority tasks are rendered first (0=lowest)
            quality: Render quality (0.0-1.0)
        """
        self.view_range = view_range
        self.priority = priority
        self.quality = quality
        self.created_time = time.time()
        self.status = 'pending'  # pending, rendering, completed, failed
        self.result = None  # Rendered image or data
        self.error = None
    
    def __lt__(self, other):
        """Compare tasks by priority (higher priority first)."""
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.created_time < other.created_time


class ViewportCacheManager(QObject):
    """
    Manages caching of pre-rendered views for predictive rendering.
    """
    
    # Signals
    cacheUpdated = pyqtSignal(str)  # cache_key
    renderCompleted = pyqtSignal(str, object)  # cache_key, result
    memoryWarning = pyqtSignal(float)  # memory_usage_percentage
    
    def __init__(self, max_cache_size_mb: float = 50.0, parent: Optional[QObject] = None):
        """
        Initialize the ViewportCacheManager.
        
        Args:
            max_cache_size_mb: Maximum cache size in megabytes
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # Cache configuration
        self.max_cache_size_bytes = max_cache_size_mb * 1024 * 1024
        self.current_cache_size_bytes = 0
        self.cache: OrderedDict[str, Any] = OrderedDict()
        
        # Render task queue
        self.render_queue: List[RenderTask] = []
        self.render_queue_lock = threading.Lock()
        
        # Background rendering
        self.render_thread = None
        self.render_thread_active = False
        self.render_thread_semaphore = threading.Semaphore(0)
        
        # Performance tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_render_time = 0
        self.total_renders = 0
        
        # Integration
        self.render_callback = None  # Function to call for rendering
        self.quality_adjustment_callback = None  # Function to adjust quality
        
        # Memory monitoring
        self.memory_monitor_timer = QTimer(self)
        self.memory_monitor_timer.timeout.connect(self._check_memory_usage)
        self.memory_monitor_timer.start(5000)  # Check every 5 seconds
        
        # Cache cleanup timer
        self.cache_cleanup_timer = QTimer(self)
        self.cache_cleanup_timer.timeout.connect(self._cleanup_old_cache)
        self.cache_cleanup_timer.start(30000)  # Cleanup every 30 seconds
        
    def set_render_callback(self, callback: Callable):
        """
        Set the callback function for rendering.
        
        Args:
            callback: Function that takes (view_range, quality) and returns rendered data
        """
        self.render_callback = callback
    
    def set_quality_adjustment_callback(self, callback: Callable):
        """
        Set the callback function for quality adjustment.
        
        Args:
            callback: Function that takes quality (0.0-1.0) and adjusts rendering quality
        """
        self.quality_adjustment_callback = callback
    
    def get_cached_view(self, view_range: Tuple[float, float], 
                       quality: float = 1.0) -> Optional[Any]:
        """
        Get a cached view if available.
        
        Args:
            view_range: (min_depth, max_depth) to retrieve
            quality: Minimum quality required
            
        Returns:
            Cached render data or None if not available
        """
        cache_key = self._get_cache_key(view_range, quality)
        
        if cache_key in self.cache:
            # Cache hit - move to end (most recently used)
            self.cache.move_to_end(cache_key)
            self.cache_hits += 1
            return self.cache[cache_key]['data']
        
        # Check for lower quality versions
        for q in [0.75, 0.5, 0.25]:
            if q < quality:
                low_quality_key = self._get_cache_key(view_range, q)
                if low_quality_key in self.cache:
                    # Use lower quality version temporarily
                    self.cache.move_to_end(low_quality_key)
                    self.cache_hits += 1
                    return self.cache[low_quality_key]['data']
        
        # Cache miss
        self.cache_misses += 1
        return None
    
    def request_predictive_render(self, view_range: Tuple[float, float], 
                                 priority: int = 0, quality: float = 1.0):
        """
        Request predictive rendering of a view range.
        
        Args:
            view_range: (min_depth, max_depth) to render
            priority: Render priority (higher = more important)
            quality: Render quality (0.0-1.0)
        """
        if not self.render_callback:
            return
        
        # Check if already in cache
        cache_key = self._get_cache_key(view_range, quality)
        if cache_key in self.cache:
            return
        
        # Check if already in queue
        with self.render_queue_lock:
            for task in self.render_queue:
                if task.view_range == view_range and task.quality == quality:
                    # Update priority if higher
                    if priority > task.priority:
                        task.priority = priority
                    return
        
        # Create new render task
        task = RenderTask(view_range, priority, quality)
        
        # Add to queue
        with self.render_queue_lock:
            self.render_queue.append(task)
            self.render_queue.sort()  # Sort by priority
        
        # Start render thread if not running
        if not self.render_thread_active:
            self._start_render_thread()
        
        # Signal render thread
        self.render_thread_semaphore.release()
    
    def _get_cache_key(self, view_range: Tuple[float, float], quality: float) -> str:
        """Generate cache key for a view range and quality."""
        min_depth, max_depth = view_range
        return f"{min_depth:.2f}_{max_depth:.2f}_{quality:.2f}"
    
    def _start_render_thread(self):
        """Start the background render thread."""
        if self.render_thread_active:
            return
        
        self.render_thread_active = True
        self.render_thread = threading.Thread(target=self._render_worker, daemon=True)
        self.render_thread.start()
    
    def _render_worker(self):
        """Background worker thread for rendering."""
        while self.render_thread_active:
            # Wait for work
            self.render_thread_semaphore.acquire()
            
            if not self.render_thread_active:
                break
            
            # Get next task
            task = None
            with self.render_queue_lock:
                if self.render_queue:
                    task = self.render_queue.pop(0)
            
            if task and self.render_callback:
                try:
                    # Update task status
                    task.status = 'rendering'
                    
                    # Start timing
                    start_time = time.time()
                    
                    # Perform rendering
                    task.result = self.render_callback(task.view_range, task.quality)
                    
                    # Calculate render time
                    render_time = time.time() - start_time
                    self.total_render_time += render_time
                    self.total_renders += 1
                    
                    # Update task status
                    task.status = 'completed'
                    
                    # Cache the result
                    self._cache_result(task)
                    
                    # Emit completion signal
                    cache_key = self._get_cache_key(task.view_range, task.quality)
                    self.renderCompleted.emit(cache_key, task.result)
                    
                except Exception as e:
                    task.status = 'failed'
                    task.error = str(e)
                    print(f"Render task failed: {e}")
    
    def _cache_result(self, task: RenderTask):
        """Cache a completed render task."""
        if not task.result:
            return
        
        cache_key = self._get_cache_key(task.view_range, task.quality)
        
        # Estimate size (this is approximate)
        size_bytes = self._estimate_size(task.result)
        
        # Check if we have space
        if size_bytes > self.max_cache_size_bytes:
            return  # Result too large for cache
        
        # Make space if needed
        while (self.current_cache_size_bytes + size_bytes > self.max_cache_size_bytes and 
               self.cache):
            # Remove oldest item
            oldest_key, oldest_item = self.cache.popitem(last=False)
            self.current_cache_size_bytes -= oldest_item['size']
        
        # Add to cache
        self.cache[cache_key] = {
            'data': task.result,
            'size': size_bytes,
            'timestamp': time.time(),
            'quality': task.quality,
            'view_range': task.view_range
        }
        self.current_cache_size_bytes += size_bytes
        
        # Emit cache update
        self.cacheUpdated.emit(cache_key)
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate the size of rendered data in bytes."""
        if isinstance(data, QImage):
            return data.sizeInBytes()
        elif isinstance(data, QPixmap):
            # Estimate based on image format and size
            if data.isNull():
                return 0
            # Rough estimate: width * height * 4 bytes (ARGB)
            return data.width() * data.height() * 4
        elif isinstance(data, dict):
            # For dictionary data, estimate based on content
            import json
            return len(json.dumps(data).encode('utf-8'))
        else:
            # Default estimate
            return 1024  # 1KB
    
    def _check_memory_usage(self):
        """Check memory usage and emit warnings if high."""
        usage_percentage = (self.current_cache_size_bytes / self.max_cache_size_bytes) * 100
        
        if usage_percentage > 90:
            self.memoryWarning.emit(usage_percentage)
            
            # Aggressive cleanup if memory is very high
            if usage_percentage > 95:
                self._cleanup_cache(0.5)  # Remove 50% of cache
    
    def _cleanup_old_cache(self):
        """Clean up old cache entries."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, item in self.cache.items():
            # Remove entries older than 5 minutes
            if current_time - item['timestamp'] > 300:  # 5 minutes
                keys_to_remove.append(key)
        
        # Remove old entries
        for key in keys_to_remove:
            item = self.cache.pop(key, None)
            if item:
                self.current_cache_size_bytes -= item['size']
    
    def _cleanup_cache(self, fraction: float = 0.3):
        """
        Clean up a fraction of the cache.
        
        Args:
            fraction: Fraction of cache to remove (0.0-1.0)
        """
        if not self.cache:
            return
        
        num_to_remove = int(len(self.cache) * fraction)
        removed_size = 0
        
        for _ in range(num_to_remove):
            if not self.cache:
                break
            
            key, item = self.cache.popitem(last=False)
            removed_size += item['size']
        
        self.current_cache_size_bytes -= removed_size
    
    def clear_cache(self):
        """Clear the entire cache."""
        self.cache.clear()
        self.current_cache_size_bytes = 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size_bytes': self.current_cache_size_bytes,
            'max_cache_size_bytes': self.max_cache_size_bytes,
            'cache_usage_percentage': (self.current_cache_size_bytes / self.max_cache_size_bytes) * 100,
            'cache_entries': len(self.cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            'average_render_time': self.total_render_time / max(1, self.total_renders),
            'render_queue_size': len(self.render_queue),
            'render_thread_active': self.render_thread_active
        }
    
    def stop(self):
        """Stop all background threads and timers."""
        self.render_thread_active = False
        self.render_thread_semaphore.release()  # Wake up thread to exit
        
        if self.render_thread:
            self.render_thread.join(timeout=2.0)
        
        self.memory_monitor_timer.stop()
        self.cache_cleanup_timer.stop()
        
        # Clear cache
        self.clear_cache()
        
        # Clear render queue
        with self.render_queue_lock:
            self.render_queue.clear()
    
    # Methods expected by PyQtGraphCurvePlotter
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage (0.0-1.0)."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / max(1, total)
    
    def get_cache_size(self) -> float:
        """Get cache size in megabytes."""
        return self.current_cache_size_bytes / (1024 * 1024)
    
    def get_cached_items(self) -> list:
        """Get list of cached item keys."""
        return list(self.cache.keys())
    
    def cleanup(self):
        """Alias for stop() method for compatibility."""
        self.stop()
    
    @property
    def gpu_acceleration(self) -> bool:
        """Check if GPU acceleration is available."""
        # TODO: Implement actual GPU detection
        # For now, return False to indicate software rendering
        return False