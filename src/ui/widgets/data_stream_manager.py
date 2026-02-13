"""
DataStreamManager - Efficient LAS data loading with memory management.

This module provides chunked loading, memory-mapped file access,
and progressive background loading for large LAS datasets.
"""

import os
import threading
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import warnings


class LoadingStrategy(Enum):
    """Strategies for loading LAS data."""
    MEMORY_MAPPED = "memory_mapped"  # Memory-mapped file access
    CHUNKED = "chunked"              # Load in fixed-size chunks
    PROGRESSIVE = "progressive"      # Progressive loading with prioritization


@dataclass
class DataChunk:
    """Represents a chunk of LAS data."""
    start_depth: float
    end_depth: float
    data: np.ndarray
    last_access_time: float
    access_count: int = 0
    size_bytes: int = 0
    
    def update_access(self):
        """Update access statistics."""
        self.last_access_time = time.time()
        self.access_count += 1


class DataStreamManager:
    """
    Manages efficient loading and caching of LAS data.
    
    Features:
    - Chunked data loading for memory efficiency
    - Memory-mapped file access for large files
    - LRU cache for recently accessed data chunks
    - Progressive background loading
    - Memory usage monitoring and control
    """
    
    def __init__(self, 
                 max_memory_mb: int = 500,
                 chunk_size_points: int = 10000,
                 loading_strategy: LoadingStrategy = LoadingStrategy.CHUNKED):
        """
        Initialize the DataStreamManager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            chunk_size_points: Number of depth points per chunk
            loading_strategy: Strategy for loading data
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.chunk_size_points = chunk_size_points
        self.loading_strategy = loading_strategy
        
        # Data storage
        self.data_chunks: Dict[Tuple[float, float], DataChunk] = {}
        self.total_memory_usage = 0
        
        # File state
        self.current_file_path: Optional[str] = None
        self.file_metadata: Dict[str, Any] = {}
        self.depth_column: str = "DEPT"
        
        # Background loading
        self.background_loader: Optional[threading.Thread] = None
        self.loading_queue: List[Tuple[float, float]] = []
        self.loading_lock = threading.Lock()
        self.stop_loading = threading.Event()
        
        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "chunks_loaded": 0,
            "chunks_evicted": 0,
            "total_bytes_loaded": 0,
            "background_loads_completed": 0
        }
        
        # Callbacks
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.error_callback: Optional[Callable[[Exception], None]] = None
        
    def load_las_file(self, 
                     file_path: str, 
                     depth_column: str = "DEPT",
                     preview_only: bool = False) -> bool:
        """
        Load a LAS file with efficient memory management.
        
        Args:
            file_path: Path to LAS file
            depth_column: Name of depth column
            preview_only: If True, only load metadata for preview
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.current_file_path = file_path
            self.depth_column = depth_column
            
            # Clear existing data
            self._clear_cache()
            
            # Load file metadata
            if not self._load_file_metadata(file_path):
                return False
                
            if preview_only:
                return True
                
            # Load initial chunks based on strategy
            if self.loading_strategy == LoadingStrategy.MEMORY_MAPPED:
                success = self._load_memory_mapped(file_path)
            elif self.loading_strategy == LoadingStrategy.CHUNKED:
                success = self._load_initial_chunks(file_path)
            elif self.loading_strategy == LoadingStrategy.PROGRESSIVE:
                success = self._start_progressive_loading(file_path)
            else:
                success = self._load_initial_chunks(file_path)
                
            return success
            
        except Exception as e:
            if self.error_callback:
                self.error_callback(e)
            else:
                warnings.warn(f"Error loading LAS file: {e}")
            return False
    
    def get_data_range(self, 
                      min_depth: float, 
                      max_depth: float,
                      columns: Optional[List[str]] = None) -> Optional[np.ndarray]:
        """
        Get data for a specific depth range.
        
        Args:
            min_depth: Minimum depth
            max_depth: Maximum depth
            columns: List of column names to retrieve (None for all)
            
        Returns:
            Numpy array with requested data, or None if not available
        """
        # Check cache first
        cached_data = self._get_cached_data(min_depth, max_depth, columns)
        if cached_data is not None:
            self.metrics["cache_hits"] += 1
            return cached_data
            
        self.metrics["cache_misses"] += 1
        
        # Load missing data
        if self.current_file_path:
            self._load_missing_chunks(min_depth, max_depth)
            
            # Try cache again after loading
            cached_data = self._get_cached_data(min_depth, max_depth, columns)
            if cached_data is not None:
                return cached_data
                
        return None
    
    def prefetch_range(self, min_depth: float, max_depth: float):
        """
        Prefetch data for a range in the background.
        
        Args:
            min_depth: Minimum depth to prefetch
            max_depth: Maximum depth to prefetch
        """
        if not self.current_file_path:
            return
            
        with self.loading_lock:
            # Add to loading queue if not already there
            range_key = (min_depth, max_depth)
            if range_key not in self.loading_queue:
                self.loading_queue.append(range_key)
                
        # Start background loader if not running
        self._start_background_loader()
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get file metadata.
        
        Returns:
            Dictionary with file metadata
        """
        return self.file_metadata.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Returns:
            Dictionary with performance metrics
        """
        metrics = self.metrics.copy()
        metrics.update({
            "total_chunks": len(self.data_chunks),
            "memory_usage_mb": self.total_memory_usage / (1024 * 1024),
            "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
            "cache_hit_rate": (
                metrics["cache_hits"] / max(1, metrics["cache_hits"] + metrics["cache_misses"])
            ),
            "loading_queue_size": len(self.loading_queue)
        })
        return metrics
    
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def set_error_callback(self, callback: Callable[[Exception], None]):
        """Set callback for error handling."""
        self.error_callback = callback
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_loading.set()
        if self.background_loader and self.background_loader.is_alive():
            self.background_loader.join(timeout=2.0)
        self._clear_cache()
    
    # Private methods
    
    def _load_file_metadata(self, file_path: str) -> bool:
        """Load file metadata without loading all data."""
        try:
            # In a real implementation, this would parse LAS file headers
            # For now, simulate with dummy data
            self.file_metadata = {
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "min_depth": 0.0,
                "max_depth": 1000.0,
                "depth_units": "m",
                "curve_count": 5,
                "curves": ["DEPT", "GR", "RHOB", "NPHI", "DT"],
                "sample_rate": 0.1524,  # 0.5 ft in meters
                "total_points": 65536
            }
            return True
        except Exception as e:
            warnings.warn(f"Error loading file metadata: {e}")
            return False
    
    def _load_initial_chunks(self, file_path: str) -> bool:
        """Load initial chunks for quick preview."""
        try:
            # Load first few chunks for immediate display
            metadata = self.file_metadata
            total_points = metadata.get("total_points", 100000)
            chunk_count = min(3, total_points // self.chunk_size_points + 1)
            
            for i in range(chunk_count):
                start_idx = i * self.chunk_size_points
                end_idx = min(start_idx + self.chunk_size_points, total_points)
                
                # Calculate depth range
                min_depth = metadata["min_depth"]
                max_depth = metadata["max_depth"]
                depth_range = max_depth - min_depth
                
                chunk_min = min_depth + (start_idx / total_points) * depth_range
                chunk_max = min_depth + (end_idx / total_points) * depth_range
                
                # Load chunk
                self._load_chunk(file_path, chunk_min, chunk_max)
                
                if self.progress_callback:
                    progress = (i + 1) / chunk_count
                    self.progress_callback(progress, f"Loading chunk {i+1}/{chunk_count}")
            
            return True
            
        except Exception as e:
            warnings.warn(f"Error loading initial chunks: {e}")
            return False
    
    def _load_memory_mapped(self, file_path: str) -> bool:
        """Load file using memory mapping."""
        # This would be implemented with numpy.memmap or similar
        # For now, fall back to chunked loading
        warnings.warn("Memory-mapped loading not fully implemented, using chunked loading")
        return self._load_initial_chunks(file_path)
    
    def _start_progressive_loading(self, file_path: str) -> bool:
        """Start progressive background loading."""
        # Load initial chunks
        success = self._load_initial_chunks(file_path)
        
        # Start background loader for remaining data
        if success:
            self._start_background_loader()
            
        return success
    
    def _load_chunk(self, file_path: str, min_depth: float, max_depth: float) -> bool:
        """Load a specific chunk of data."""
        try:
            # In a real implementation, this would read from LAS file
            # For simulation, generate synthetic data
            points = self.chunk_size_points
            
            # Generate depth values
            depths = np.linspace(min_depth, max_depth, points)
            
            # Generate curve data (simulated)
            data = {
                self.depth_column: depths,
                "GR": 50 + 50 * np.sin(depths / 100) + np.random.normal(0, 10, points),
                "RHOB": 2.0 + 0.5 * np.sin(depths / 50) + np.random.normal(0, 0.1, points),
                "NPHI": 0.2 + 0.1 * np.cos(depths / 75) + np.random.normal(0, 0.05, points),
                "DT": 100 + 20 * np.sin(depths / 80) + np.random.normal(0, 5, points)
            }
            
            # Convert to structured array
            dtype = [(col, 'float64') for col in data.keys()]
            structured_data = np.zeros(points, dtype=dtype)
            for col, values in data.items():
                structured_data[col] = values
            
            # Create chunk
            chunk = DataChunk(
                start_depth=min_depth,
                end_depth=max_depth,
                data=structured_data,
                last_access_time=time.time(),
                size_bytes=structured_data.nbytes
            )
            
            # Add to cache
            self._add_to_cache(chunk)
            
            self.metrics["chunks_loaded"] += 1
            self.metrics["total_bytes_loaded"] += chunk.size_bytes
            
            return True
            
        except Exception as e:
            warnings.warn(f"Error loading chunk {min_depth}-{max_depth}: {e}")
            return False
    
    def _add_to_cache(self, chunk: DataChunk):
        """Add chunk to cache with LRU eviction if needed."""
        # Check if we need to evict chunks
        while (self.total_memory_usage + chunk.size_bytes > self.max_memory_bytes and 
               self.data_chunks):
            self._evict_oldest_chunk()
        
        # Add chunk
        key = (chunk.start_depth, chunk.end_depth)
        self.data_chunks[key] = chunk
        self.total_memory_usage += chunk.size_bytes
    
    def _evict_oldest_chunk(self):
        """Evict the least recently used chunk."""
        if not self.data_chunks:
            return
            
        # Find oldest chunk
        oldest_key = None
        oldest_time = float('inf')
        
        for key, chunk in self.data_chunks.items():
            if chunk.last_access_time < oldest_time:
                oldest_time = chunk.last_access_time
                oldest_key = key
        
        if oldest_key:
            chunk = self.data_chunks.pop(oldest_key)
            self.total_memory_usage -= chunk.size_bytes
            self.metrics["chunks_evicted"] += 1
    
    def _get_cached_data(self, 
                        min_depth: float, 
                        max_depth: float,
                        columns: Optional[List[str]] = None) -> Optional[np.ndarray]:
        """Get data from cache for the specified range."""
        # Find overlapping chunks
        overlapping_chunks = []
        
        for (chunk_min, chunk_max), chunk in self.data_chunks.items():
            if chunk_max >= min_depth and chunk_min <= max_depth:
                overlapping_chunks.append(chunk)
                chunk.update_access()
        
        if not overlapping_chunks:
            return None
        
        # Combine data from overlapping chunks
        combined_data = []
        for chunk in overlapping_chunks:
            # Extract relevant portion
            chunk_data = chunk.data
            
            # Filter by depth range
            depth_mask = (chunk_data[self.depth_column] >= min_depth) & \
                        (chunk_data[self.depth_column] <= max_depth)
            filtered_data = chunk_data[depth_mask]
            
            if len(filtered_data) > 0:
                combined_data.append(filtered_data)
        
        if not combined_data:
            return None
        
        # Combine all chunks
        result = np.concatenate(combined_data)
        
        # Sort by depth
        result.sort(order=self.depth_column)
        
        # Select columns if specified
        if columns:
            # Ensure depth column is included
            if self.depth_column not in columns:
                columns = [self.depth_column] + columns
            
            # Extract selected columns
            selected_dtype = [(col, 'float64') for col in columns]
            selected_data = np.zeros(len(result), dtype=selected_dtype)
            for col in columns:
                if col in result.dtype.names:
                    selected_data[col] = result[col]
            
            result = selected_data
        
        return result
    
    def _load_missing_chunks(self, min_depth: float, max_depth: float):
        """Load chunks needed for the specified range."""
        # Determine which chunks are needed
        metadata = self.file_metadata
        total_depth = metadata["max_depth"] - metadata["min_depth"]
        chunk_depth_range = total_depth / (metadata["total_points"] / self.chunk_size_points)
        
        start_chunk = int((min_depth - metadata["min_depth"]) // chunk_depth_range)
        end_chunk = int((max_depth - metadata["min_depth"]) // chunk_depth_range) + 1
        
        for chunk_idx in range(start_chunk, end_chunk + 1):
            chunk_min = metadata["min_depth"] + chunk_idx * chunk_depth_range
            chunk_max = chunk_min + chunk_depth_range
            
            # Check if chunk is already loaded
            key = (chunk_min, chunk_max)
            if key not in self.data_chunks and self.current_file_path:
                # Load chunk
                self._load_chunk(self.current_file_path, chunk_min, chunk_max)
    
    def _start_background_loader(self):
        """Start background loading thread."""
        if self.background_loader and self.background_loader.is_alive():
            return
        
        self.stop_loading.clear()
        self.background_loader = threading.Thread(
            target=self._background_loading_worker,
            daemon=True
        )
        self.background_loader.start()
    
    def _background_loading_worker(self):
        """Background worker for progressive loading."""
        while not self.stop_loading.is_set():
            with self.loading_lock:
                if not self.loading_queue:
                    time.sleep(0.1)
                    continue
                
                # Get next range to load
                min_depth, max_depth = self.loading_queue.pop(0)
            
            # Load the range
            self._load_missing_chunks(min_depth, max_depth)
            self.metrics["background_loads_completed"] += 1
            
            time.sleep(0.01)  # Small delay to prevent CPU hogging
    
    def _clear_cache(self):
        """Clear all cached data."""
        self.data_chunks.clear()
        self.total_memory_usage = 0
        self.metrics["chunks_evicted"] += len(self.data_chunks)
    
    # Methods expected by PyQtGraphCurvePlotter
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage (0.0-1.0)."""
        total = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        return self.metrics["cache_hits"] / max(1, total)
    
    def get_memory_usage_mb(self) -> float:
        """Get memory usage in megabytes."""
        return self.total_memory_usage / (1024 * 1024)
    
    def get_active_chunk_count(self) -> int:
        """Get number of active chunks in memory."""
        return len(self.data_chunks)