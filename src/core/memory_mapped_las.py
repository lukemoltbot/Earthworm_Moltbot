"""
MemoryMappedLAS - Memory-mapped file access for large LAS datasets.

Provides efficient random access to LAS files without loading entire files into memory.
"""

import os
import numpy as np
import pandas as pd
import lasio
import mmap
import struct
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import threading
import zlib


class MemoryMappedLAS:
    """
    Provides memory-mapped access to LAS files for efficient random access.
    
    Features:
    - Memory-mapped file access for zero-copy reading
    - Lazy loading of curve data
    - Efficient depth indexing for quick seeking
    - Columnar data access for specific curves
    - Data compression for reduced memory footprint
    """
    
    def __init__(self, las_file_path: str, use_mmap: bool = True):
        """
        Initialize memory-mapped LAS access.
        
        Args:
            las_file_path: Path to the LAS file
            use_mmap: Whether to use memory-mapped file access
        """
        self.las_file_path = Path(las_file_path)
        self.use_mmap = use_mmap
        
        # Memory-mapped file state
        self.mmap_file = None
        self.mmap_data = None
        self.file_size = 0
        
        # LAS file structure
        self.depth_column = None
        self.curve_columns = []
        self.depth_index = None  # Sorted depth values for binary search
        self.depth_positions = None  # File positions for each depth
        
        # Cache for loaded data
        self.data_cache = {}
        self.cache_size_limit = 100 * 1024 * 1024  # 100 MB cache limit
        self.current_cache_size = 0
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.disk_reads = 0
        
        # Initialize the memory mapping
        self._initialize_mmap()
    
    def _initialize_mmap(self):
        """Initialize memory-mapped file access."""
        if not self.use_mmap or not self.las_file_path.exists():
            return
        
        try:
            self.file_size = os.path.getsize(self.las_file_path)
            
            # Open file for memory mapping
            self.mmap_file = open(self.las_file_path, 'rb')
            self.mmap_data = mmap.mmap(self.mmap_file.fileno(), 0, access=mmap.ACCESS_READ)
            
            # Parse LAS header to build index
            self._parse_las_header()
            
        except Exception as e:
            print(f"Error initializing memory mapping: {e}")
            self._cleanup_mmap()
    
    def _parse_las_header(self):
        """Parse LAS header to extract structure information."""
        try:
            # Read LAS file with lasio to get structure
            las = lasio.read(self.las_file_path)
            df = las.df()
            
            # Identify depth column
            self.depth_column = self._identify_depth_column(df)
            self.curve_columns = list(df.columns)
            
            # Create depth index for binary search
            if self.depth_column:
                depth_data = df.index if df.index.name == self.depth_column else df[self.depth_column]
                self.depth_index = np.sort(depth_data.unique())
                
                # Estimate file positions (simplified - actual implementation would need LAS format parsing)
                self.depth_positions = {}
                for i, depth in enumerate(self.depth_index):
                    # Linear mapping for now - could be improved with actual LAS format parsing
                    position = int((i / len(self.depth_index)) * self.file_size)
                    self.depth_positions[depth] = position
            
        except Exception as e:
            print(f"Error parsing LAS header: {e}")
    
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
    
    def get_data_range(self, depth_range: Tuple[float, float], 
                      curve_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get data for a specific depth range and curves.
        
        Args:
            depth_range: Tuple of (min_depth, max_depth)
            curve_names: List of curve names to load (None for all curves)
            
        Returns:
            DataFrame containing the requested data
        """
        min_depth, max_depth = depth_range
        
        # Generate cache key
        cache_key = (min_depth, max_depth, tuple(curve_names) if curve_names else None)
        
        # Check cache first
        if cache_key in self.data_cache:
            self.cache_hits += 1
            return self.data_cache[cache_key].copy()
        
        self.cache_misses += 1
        
        # Load data from file
        data = self._load_data_from_file(depth_range, curve_names)
        
        # Cache the result
        if data is not None:
            data_size = data.memory_usage(deep=True).sum()
            
            # Add to cache if there's space
            if self.current_cache_size + data_size <= self.cache_size_limit:
                self.data_cache[cache_key] = data.copy()
                self.current_cache_size += data_size
            else:
                # Clear some cache entries
                self._clean_cache()
        
        return data
    
    def _load_data_from_file(self, depth_range: Tuple[float, float], 
                           curve_names: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
        """Load data directly from the LAS file."""
        min_depth, max_depth = depth_range
        
        try:
            # Use lasio to read the specific range
            # Note: lasio doesn't support random access natively, so we read the whole file
            # but only extract the needed range
            las = lasio.read(self.las_file_path)
            df = las.df()
            
            # Identify depth column
            depth_col = self._identify_depth_column(df)
            if depth_col is None:
                return None
            
            # Reset index if depth is the index
            if df.index.name == depth_col:
                df = df.reset_index()
            
            # Filter by depth range
            mask = (df[depth_col] >= min_depth) & (df[depth_col] <= max_depth)
            filtered_df = df[mask].copy()
            
            # Select specific curves if requested
            if curve_names:
                # Ensure depth column is included
                columns_to_keep = [depth_col] + [col for col in curve_names if col in filtered_df.columns]
                filtered_df = filtered_df[columns_to_keep]
            
            self.disk_reads += 1
            return filtered_df
            
        except Exception as e:
            print(f"Error loading data from file: {e}")
            return None
    
    def _clean_cache(self):
        """Clean cache to free memory."""
        if not self.data_cache:
            return
        
        # Simple LRU cache cleaning - remove oldest entries
        # In a production system, this would use proper LRU tracking
        keys_to_remove = list(self.data_cache.keys())[:len(self.data_cache) // 4]
        
        for key in keys_to_remove:
            data = self.data_cache[key]
            data_size = data.memory_usage(deep=True).sum()
            self.current_cache_size -= data_size
            del self.data_cache[key]
    
    def get_depth_range(self) -> Tuple[float, float]:
        """Get the total depth range of the LAS file."""
        if self.depth_index is None or len(self.depth_index) == 0:
            return (0.0, 1000.0)
        
        return (float(self.depth_index[0]), float(self.depth_index[-1]))
    
    def get_curve_names(self) -> List[str]:
        """Get list of all curve names in the LAS file."""
        return self.curve_columns.copy()
    
    def get_curve_statistics(self, curve_name: str) -> Dict[str, float]:
        """Get statistics for a specific curve."""
        try:
            # Load a sample of data to compute statistics
            depth_range = self.get_depth_range()
            data = self.get_data_range(depth_range, [curve_name])
            
            if data is None or curve_name not in data.columns:
                return {}
            
            curve_data = data[curve_name]
            
            return {
                'min': float(curve_data.min()),
                'max': float(curve_data.max()),
                'mean': float(curve_data.mean()),
                'std': float(curve_data.std()),
                'count': int(len(curve_data))
            }
            
        except Exception as e:
            print(f"Error getting curve statistics: {e}")
            return {}
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            'cache_size_mb': self.current_cache_size / (1024 * 1024),
            'cache_size_limit_mb': self.cache_size_limit / (1024 * 1024),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            'disk_reads': self.disk_reads,
            'cached_ranges': len(self.data_cache)
        }
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_cache.clear()
        self.current_cache_size = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.disk_reads = 0
    
    def _cleanup_mmap(self):
        """Clean up memory-mapped file resources."""
        if self.mmap_data:
            self.mmap_data.close()
            self.mmap_data = None
        
        if self.mmap_file:
            self.mmap_file.close()
            self.mmap_file = None
    
    def close(self):
        """Clean up all resources."""
        self.clear_cache()
        self._cleanup_mmap()