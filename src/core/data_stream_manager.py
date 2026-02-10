"""
DataStreamManager - Efficient memory management and data streaming for large LAS datasets.

This module provides chunked loading, memory-mapped file access, and progressive
data streaming to handle large geological datasets without memory pressure.
"""

import os
import numpy as np
import pandas as pd
import lasio
import threading
import time
import psutil
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from collections import OrderedDict
import mmap
import struct
import pickle
import zlib
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


@dataclass
class DataChunk:
    """Represents a chunk of LAS data for a specific depth range."""
    depth_range: Tuple[float, float]  # (min_depth, max_depth)
    data: pd.DataFrame
    metadata: Dict[str, Any]
    size_bytes: int
    access_time: float
    compressed: bool = False
    compressed_data: Optional[bytes] = None


@dataclass
class ChunkMetadata:
    """Metadata for a data chunk to enable quick seeking."""
    depth_range: Tuple[float, float]
    file_offset: int
    size_bytes: int
    curve_columns: List[str]
    num_points: int
    min_values: Dict[str, float]
    max_values: Dict[str, float]


class DataStreamManager(QObject):
    """
    Manages efficient streaming and memory management for large LAS datasets.
    
    Features:
    - Chunked loading based on depth ranges
    - Memory-mapped file access for large files
    - LRU cache for loaded chunks
    - Progressive loading with background threads
    - Memory pressure monitoring and automatic cache clearing
    - Data compression for transmission and storage
    """
    
    # Signals for UI updates
    chunk_loaded = pyqtSignal(Tuple[float, float], int)  # depth_range, size_bytes
    chunk_unloaded = pyqtSignal(Tuple[float, float])
    memory_usage_updated = pyqtSignal(int, int)  # current_memory_mb, max_memory_mb
    loading_progress = pyqtSignal(int, str)  # progress_percentage, status_message
    data_ready = pyqtSignal(pd.DataFrame, Dict[str, Any])  # data, metadata
    
    def __init__(self, las_file_path: str, chunk_size_mb: float = 10.0, 
                 max_loaded_chunks: int = 5, max_total_memory_mb: int = 500):
        """
        Initialize the DataStreamManager.
        
        Args:
            las_file_path: Path to the LAS file
            chunk_size_mb: Target chunk size in megabytes
            max_loaded_chunks: Maximum number of chunks to keep in memory
            max_total_memory_mb: Maximum total memory usage in MB
        """
        super().__init__()
        
        self.las_file_path = Path(las_file_path)
        self.chunk_size_bytes = int(chunk_size_mb * 1024 * 1024)
        self.max_loaded_chunks = max_loaded_chunks
        self.max_total_memory_mb = max_total_memory_mb
        
        # Chunk management
        self.loaded_chunks: OrderedDict[Tuple[float, float], DataChunk] = OrderedDict()
        self.chunk_metadata: Dict[Tuple[float, float], ChunkMetadata] = {}
        self.chunk_access_times: Dict[Tuple[float, float], float] = {}
        
        # Memory-mapped file access
        self.mmap_file = None
        self.mmap_data = None
        self.file_size = 0
        
        # Background loading
        self.loading_thread = None
        self.loading_queue = []
        self.cancel_loading = False
        
        # Memory monitoring
        self.current_memory_mb = 0
        self.memory_monitor_timer = QTimer()
        self.memory_monitor_timer.timeout.connect(self._update_memory_usage)
        self.memory_monitor_timer.start(5000)  # Check every 5 seconds
        
        # Statistics
        self.total_chunks_loaded = 0
        self.total_chunks_unloaded = 0
        self.total_data_transferred_mb = 0
        
        # Initialize the chunk metadata
        self._initialize_chunk_metadata()
    
    def _initialize_chunk_metadata(self):
        """Initialize chunk metadata by scanning the LAS file."""
        try:
            # Read LAS file header to get depth range and curve information
            las = lasio.read(self.las_file_path)
            df = las.df()
            
            # Get depth column
            depth_col = self._identify_depth_column(df)
            if depth_col is None:
                raise ValueError("Could not identify depth column in LAS file")
            
            # Get depth range
            depth_data = df.index if df.index.name == depth_col else df[depth_col]
            min_depth = float(depth_data.min())
            max_depth = float(depth_data.max())
            total_depth_range = max_depth - min_depth
            
            # Estimate chunk boundaries
            num_points = len(df)
            avg_point_size = self._estimate_point_size(df)
            points_per_chunk = self.chunk_size_bytes // avg_point_size
            
            # Create chunk metadata
            self.chunk_metadata = {}
            current_depth = min_depth
            
            while current_depth < max_depth:
                # Calculate chunk depth range
                chunk_max_depth = min(current_depth + (total_depth_range * points_per_chunk / num_points), 
                                     max_depth)
                
                depth_range = (current_depth, chunk_max_depth)
                
                # Create metadata for this chunk
                metadata = ChunkMetadata(
                    depth_range=depth_range,
                    file_offset=0,  # Will be populated during actual loading
                    size_bytes=0,   # Will be populated during actual loading
                    curve_columns=list(df.columns),
                    num_points=0,   # Will be populated during actual loading
                    min_values={col: float(df[col].min()) for col in df.columns},
                    max_values={col: float(df[col].max()) for col in df.columns}
                )
                
                self.chunk_metadata[depth_range] = metadata
                current_depth = chunk_max_depth
            
            self.loading_progress.emit(100, f"Initialized {len(self.chunk_metadata)} chunks")
            
        except Exception as e:
            print(f"Error initializing chunk metadata: {e}")
            # Fall back to single chunk
            self.chunk_metadata = {
                (0.0, 1000.0): ChunkMetadata(
                    depth_range=(0.0, 1000.0),
                    file_offset=0,
                    size_bytes=0,
                    curve_columns=[],
                    num_points=0,
                    min_values={},
                    max_values={}
                )
            }
    
    def _identify_depth_column(self, df: pd.DataFrame) -> Optional[str]:
        """Identify the depth column in a DataFrame."""
        depth_patterns = ['DEPT', 'DEPTH', 'MD', 'depth', 'dept']
        
        # Check column names
        for col in df.columns:
            if any(pattern in col.upper() for pattern in depth_patterns):
                return col
        
        # Check index
        if df.index.name and any(pattern in df.index.name.upper() for pattern in depth_patterns):
            return df.index.name
        
        return None
    
    def _estimate_point_size(self, df: pd.DataFrame) -> int:
        """Estimate the average size of a data point in bytes."""
        # Rough estimate: 8 bytes per float value + overhead
        num_columns = len(df.columns)
        return num_columns * 8 + 32  # 32 bytes overhead per row
    
    def get_data_for_range(self, depth_range: Tuple[float, float]) -> Optional[pd.DataFrame]:
        """
        Get data for a specific depth range, loading it if necessary.
        
        Args:
            depth_range: Tuple of (min_depth, max_depth)
            
        Returns:
            DataFrame containing data for the requested range, or None if not available
        """
        # Check if chunk is already loaded
        chunk_key = self._find_chunk_for_range(depth_range)
        if chunk_key in self.loaded_chunks:
            # Update access time for LRU tracking
            self.chunk_access_times[chunk_key] = time.time()
            self.loaded_chunks.move_to_end(chunk_key)
            
            chunk = self.loaded_chunks[chunk_key]
            
            # Extract data for the specific range
            data = self._extract_subrange(chunk.data, depth_range)
            return data
        
        # Chunk not loaded, load it
        self._load_chunk(chunk_key)
        
        # Check again after loading
        if chunk_key in self.loaded_chunks:
            chunk = self.loaded_chunks[chunk_key]
            data = self._extract_subrange(chunk.data, depth_range)
            
            # Prefetch adjacent chunks
            self.prefetch_adjacent_ranges(depth_range)
            
            return data
        
        return None
    
    def _find_chunk_for_range(self, depth_range: Tuple[float, float]) -> Tuple[float, float]:
        """Find the chunk that contains the requested depth range."""
        min_depth, max_depth = depth_range
        
        for chunk_range in self.chunk_metadata.keys():
            chunk_min, chunk_max = chunk_range
            if chunk_min <= min_depth and chunk_max >= max_depth:
                return chunk_range
        
        # If no chunk fully contains the range, find the closest
        for chunk_range in self.chunk_metadata.keys():
            chunk_min, chunk_max = chunk_range
            if chunk_min <= max_depth and chunk_max >= min_depth:
                return chunk_range
        
        # Fallback to first chunk
        return list(self.chunk_metadata.keys())[0]
    
    def _extract_subrange(self, data: pd.DataFrame, depth_range: Tuple[float, float]) -> pd.DataFrame:
        """Extract data for a specific subrange from a chunk."""
        min_depth, max_depth = depth_range
        
        # Identify depth column
        depth_col = self._identify_depth_column(data)
        if depth_col is None:
            return data
        
        # Filter data for the requested range
        mask = (data[depth_col] >= min_depth) & (data[depth_col] <= max_depth)
        return data[mask].copy()
    
    def _load_chunk(self, chunk_range: Tuple[float, float]):
        """Load a chunk of data from the LAS file."""
        if chunk_range not in self.chunk_metadata:
            return
        
        # Check memory pressure before loading
        if self._check_memory_pressure():
            self.unload_unused_chunks()
        
        # Load the chunk
        try:
            # Read LAS file and extract chunk
            las = lasio.read(self.las_file_path)
            df = las.df()
            
            # Identify depth column
            depth_col = self._identify_depth_column(df)
            if depth_col is None:
                return
            
            # Reset index if depth is the index
            if df.index.name == depth_col:
                df = df.reset_index()
            
            # Filter data for chunk range
            chunk_min, chunk_max = chunk_range
            mask = (df[depth_col] >= chunk_min) & (df[depth_col] <= chunk_max)
            chunk_data = df[mask].copy()
            
            # Create chunk object
            size_bytes = chunk_data.memory_usage(deep=True).sum()
            chunk = DataChunk(
                depth_range=chunk_range,
                data=chunk_data,
                metadata={},
                size_bytes=size_bytes,
                access_time=time.time()
            )
            
            # Add to loaded chunks
            self.loaded_chunks[chunk_range] = chunk
            self.chunk_access_times[chunk_range] = time.time()
            
            # Update memory usage
            self.current_memory_mb += size_bytes // (1024 * 1024)
            self.total_chunks_loaded += 1
            
            # Emit signals
            self.chunk_loaded.emit(chunk_range, size_bytes)
            self.memory_usage_updated.emit(self.current_memory_mb, self.max_total_memory_mb)
            
            # Enforce max loaded chunks
            if len(self.loaded_chunks) > self.max_loaded_chunks:
                self.unload_unused_chunks()
                
        except Exception as e:
            print(f"Error loading chunk {chunk_range}: {e}")
    
    def prefetch_adjacent_ranges(self, current_range: Tuple[float, float]):
        """
        Pre-load adjacent depth ranges for smoother scrolling.
        
        Args:
            current_range: The currently visible depth range
        """
        # Find current chunk
        current_chunk = self._find_chunk_for_range(current_range)
        
        # Get all chunk ranges
        chunk_ranges = list(self.chunk_metadata.keys())
        
        # Find index of current chunk
        try:
            current_idx = chunk_ranges.index(current_chunk)
        except ValueError:
            return
        
        # Prefetch next chunk
        if current_idx + 1 < len(chunk_ranges):
            next_chunk = chunk_ranges[current_idx + 1]
            if next_chunk not in self.loaded_chunks:
                self._load_chunk_in_background(next_chunk)
        
        # Prefetch previous chunk
        if current_idx - 1 >= 0:
            prev_chunk = chunk_ranges[current_idx - 1]
            if prev_chunk not in self.loaded_chunks:
                self._load_chunk_in_background(prev_chunk)
    
    def _load_chunk_in_background(self, chunk_range: Tuple[float, float]):
        """Load a chunk in a background thread."""
        if chunk_range in self.loading_queue:
            return
        
        self.loading_queue.append(chunk_range)
        
        if self.loading_thread is None or not self.loading_thread.is_alive():
            self.loading_thread = threading.Thread(target=self._background_loader)
            self.loading_thread.daemon = True
            self.loading_thread.start()
    
    def _background_loader(self):
        """Background thread for loading chunks."""
        while self.loading_queue and not self.cancel_loading:
            chunk_range = self.loading_queue.pop(0)
            
            # Check if already loaded
            if chunk_range in self.loaded_chunks:
                continue
            
            # Load the chunk
            self._load_chunk(chunk_range)
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.1)
    
    def unload_unused_chunks(self):
        """Unload least recently used chunks to free memory."""
        if not self.loaded_chunks:
            return
        
        # Sort chunks by access time (oldest first)
        sorted_chunks = sorted(self.chunk_access_times.items(), key=lambda x: x[1])
        
        # Unload chunks until we're under the limit
        while (len(self.loaded_chunks) > self.max_loaded_chunks or 
               self.current_memory_mb > self.max_total_memory_mb):
            
            if not sorted_chunks:
                break
            
            chunk_range, _ = sorted_chunks.pop(0)
            
            if chunk_range in self.loaded_chunks:
                chunk = self.loaded_chunks[chunk_range]
                
                # Update memory usage
                self.current_memory_mb -= chunk.size_bytes // (1024 * 1024)
                self.total_chunks_unloaded += 1
                
                # Remove from collections
                del self.loaded_chunks[chunk_range]
                del self.chunk_access_times[chunk_range]
                
                # Emit signal
                self.chunk_unloaded.emit(chunk_range)
                self.memory_usage_updated.emit(self.current_memory_mb, self.max_total_memory_mb)
    
    def _check_memory_pressure(self) -> bool:
        """Check if system is under memory pressure."""
        try:
            memory = psutil.virtual_memory()
            return memory.percent > 80  # 80% memory usage threshold
        except:
            return False
    
    def _update_memory_usage(self):
        """Update memory usage statistics."""
        try:
            # Calculate current memory usage
            total_size = sum(chunk.size_bytes for chunk in self.loaded_chunks.values())
            self.current_memory_mb = total_size // (1024 * 1024)
            
            # Emit update
            self.memory_usage_updated.emit(self.current_memory_mb, self.max_total_memory_mb)
            
            # Check memory pressure
            if self._check_memory_pressure():
                self.unload_unused_chunks()
                
        except Exception as e:
            print(f"Error updating memory usage: {e}")
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            'current_memory_mb': self.current_memory_mb,
            'max_memory_mb': self.max_total_memory_mb,
            'loaded_chunks': len(self.loaded_chunks),
            'total_chunks': len(self.chunk_metadata),
            'total_chunks_loaded': self.total_chunks_loaded,
            'total_chunks_unloaded': self.total_chunks_unloaded,
            'total_data_transferred_mb': self.total_data_transferred_mb
        }
    
    def clear_cache(self):
        """Clear all loaded chunks from memory."""
        for chunk_range in list(self.loaded_chunks.keys()):
            chunk = self.loaded_chunks[chunk_range]
            self.current_memory_mb -= chunk.size_bytes // (1024 * 1024)
            del self.loaded_chunks[chunk_range]
            
            if chunk_range in self.chunk_access_times:
                del self.chunk_access_times[chunk_range]
            
            self.chunk_unloaded.emit(chunk_range)
        
        self.memory_usage_updated.emit(self.current_memory_mb, self.max_total_memory_mb)
    
    def close(self):
        """Clean up resources."""
        self.cancel_loading = True
        self.memory_monitor_timer.stop()
        self.clear_cache()
        
        if self.mmap_file:
            self.mmap_file.close()
            self.mmap_file = None
            self.mmap_data = None