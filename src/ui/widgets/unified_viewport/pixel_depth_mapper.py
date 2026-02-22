"""
PixelDepthMapper - Pixel-accurate depth to pixel mapping.

Provides integer pixel mapping for depth values with 1-pixel accuracy.
"""

import logging
import math
from typing import Optional, Tuple, List
from dataclasses import dataclass

from PyQt6.QtCore import QRect, QPoint

logger = logging.getLogger(__name__)

@dataclass
class PixelMappingConfig:
    """Configuration for pixel-depth mapping."""
    # Depth range
    min_depth: float = 0.0
    max_depth: float = 100.0
    
    # Viewport dimensions
    viewport_width: int = 800
    viewport_height: int = 600
    
    # Display settings
    vertical_padding: int = 2  # pixels at top and bottom
    pixel_tolerance: int = 1   # Maximum allowed pixel drift
    
    # Performance
    enable_caching: bool = True
    cache_size: int = 1000     # Number of mappings to cache


class PixelDepthMapper:
    """
    Maps depth values to pixel positions with 1-pixel accuracy.
    
    Provides bidirectional mapping:
    - depth → pixel (for rendering)
    - pixel → depth (for interaction)
    
    Key features:
    - Integer pixel positions (no sub-pixel rendering)
    - Consistent rounding (always round down or always round to nearest)
    - Caching for performance
    - Validation of pixel alignment
    """
    
    def __init__(self, config: Optional[PixelMappingConfig] = None):
        """
        Initialize the pixel-depth mapper.
        
        Args:
            config: Configuration object, or None for defaults
        """
        self.config = config or PixelMappingConfig()
        
        # State
        self._depth_range = (self.config.min_depth, self.config.max_depth)
        self._viewport_size = (self.config.viewport_width, self.config.viewport_height)
        
        # Cache for depth→pixel mappings
        self._depth_to_pixel_cache = {}
        self._pixel_to_depth_cache = {}
        
        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        
        logger.debug(f"PixelDepthMapper initialized: {self.config}")
    
    def update_viewport_size(self, width: int, height: int) -> None:
        """
        Update viewport dimensions.
        
        Args:
            width: New viewport width in pixels
            height: New viewport height in pixels
        """
        old_size = self._viewport_size
        self._viewport_size = (width, height)
        self.config.viewport_width = width
        self.config.viewport_height = height
        
        # Clear cache when size changes
        self._clear_cache()
        
        logger.debug(f"Viewport size updated: {old_size} → {self._viewport_size}")
    
    def set_depth_range(self, min_depth: float, max_depth: float) -> None:
        """
        Set the depth range to map.
        
        Args:
            min_depth: Minimum depth value
            max_depth: Maximum depth value
        """
        if min_depth >= max_depth:
            raise ValueError(f"Invalid depth range: {min_depth} >= {max_depth}")
        
        old_range = self._depth_range
        self._depth_range = (min_depth, max_depth)
        self.config.min_depth = min_depth
        self.config.max_depth = max_depth
        
        # Clear cache when range changes
        self._clear_cache()
        
        logger.debug(f"Depth range updated: {old_range} → {self._depth_range}")
    
    def depth_to_pixel(self, depth: float) -> Optional[int]:
        """
        Convert depth to pixel position.
        
        Args:
            depth: Depth value to convert
            
        Returns:
            Pixel position (0 at top, height-1 at bottom), or None if out of range
        """
        # Check cache first
        if self.config.enable_caching and depth in self._depth_to_pixel_cache:
            self._cache_hits += 1
            return self._depth_to_pixel_cache[depth]
        
        self._cache_misses += 1
        
        # Check if depth is in range
        min_depth, max_depth = self._depth_range
        if depth < min_depth or depth > max_depth:
            logger.debug(f"Depth {depth} out of range [{min_depth}, {max_depth}]")
            return None
        
        # Calculate pixel position
        # Map depth to [0, 1] range (0 at min_depth, 1 at max_depth)
        depth_normalized = (depth - min_depth) / (max_depth - min_depth)
        
        # Map to pixel range, accounting for padding
        # Top padding at top, bottom padding at bottom
        usable_height = self.config.viewport_height - (2 * self.config.vertical_padding)
        
        if usable_height <= 0:
            logger.warning(f"Usable height <= 0: {usable_height}")
            return None
        
        # Pixel position from top (0 at top of usable area)
        pixel_from_top = depth_normalized * usable_height
        
        # Convert to integer pixel with consistent rounding
        # Use round() for nearest pixel, or math.floor() for always rounding down
        pixel_from_top_int = int(round(pixel_from_top))
        
        # Add top padding
        pixel = self.config.vertical_padding + pixel_from_top_int
        
        # Ensure pixel is within viewport bounds
        pixel = max(self.config.vertical_padding, 
                   min(self.config.viewport_height - self.config.vertical_padding - 1, 
                       pixel))
        
        # Cache the result
        if self.config.enable_caching:
            self._depth_to_pixel_cache[depth] = pixel
        
        return pixel
    
    def pixel_to_depth(self, pixel: int) -> Optional[float]:
        """
        Convert pixel position to depth.
        
        Args:
            pixel: Pixel position (0 at top, height-1 at bottom)
            
        Returns:
            Depth value, or None if pixel is out of usable area
        """
        # Check cache first
        if self.config.enable_caching and pixel in self._pixel_to_depth_cache:
            self._cache_hits += 1
            return self._pixel_to_depth_cache[pixel]
        
        self._cache_misses += 1
        
        # Check if pixel is in usable area (excluding padding)
        if (pixel < self.config.vertical_padding or 
            pixel >= self.config.viewport_height - self.config.vertical_padding):
            logger.debug(f"Pixel {pixel} outside usable area "
                        f"[{self.config.vertical_padding}, "
                        f"{self.config.viewport_height - self.config.vertical_padding})")
            return None
        
        # Calculate depth
        min_depth, max_depth = self._depth_range
        usable_height = self.config.viewport_height - (2 * self.config.vertical_padding)
        
        if usable_height <= 0:
            logger.warning(f"Usable height <= 0: {usable_height}")
            return None
        
        # Pixel position relative to usable area (0 at top of usable area)
        pixel_in_usable = pixel - self.config.vertical_padding
        
        # Normalize to [0, 1] range
        normalized = pixel_in_usable / usable_height
        
        # Map to depth range
        depth = min_depth + (normalized * (max_depth - min_depth))
        
        # Cache the result
        if self.config.enable_caching:
            self._pixel_to_depth_cache[pixel] = depth
        
        return depth
    
    def validate_pixel_alignment(self, test_depths: Optional[List[float]] = None) -> dict:
        """
        Validate pixel alignment accuracy.
        
        Tests that depth→pixel→depth round-trip maintains ≤1 pixel drift.
        
        Args:
            test_depths: List of depths to test, or None for automatic test points
            
        Returns:
            Dictionary with validation results
        """
        min_depth, max_depth = self._depth_range
        
        if test_depths is None:
            # Generate test points: min, max, and 3 evenly spaced points
            test_depths = [
                min_depth,
                min_depth + (max_depth - min_depth) * 0.25,
                min_depth + (max_depth - min_depth) * 0.5,
                min_depth + (max_depth - min_depth) * 0.75,
                max_depth
            ]
        
        results = {
            'test_points': len(test_depths),
            'max_pixel_drift': 0,
            'pixel_drift_exceeded': False,
            'details': [],
            'cache_stats': self.get_cache_stats()
        }
        
        for depth in test_depths:
            # Depth → Pixel
            pixel = self.depth_to_pixel(depth)
            
            if pixel is None:
                results['details'].append({
                    'depth': depth,
                    'error': 'Depth out of range or mapping failed',
                    'pixel_drift': None
                })
                continue
            
            # Pixel → Depth (round trip)
            round_trip_depth = self.pixel_to_depth(pixel)
            
            if round_trip_depth is None:
                results['details'].append({
                    'depth': depth,
                    'error': 'Pixel to depth mapping failed',
                    'pixel_drift': None
                })
                continue
            
            # Calculate pixel drift
            # What pixel would the round-trip depth map to?
            round_trip_pixel = self.depth_to_pixel(round_trip_depth)
            
            if round_trip_pixel is None:
                results['details'].append({
                    'depth': depth,
                    'error': 'Round trip pixel mapping failed',
                    'pixel_drift': None
                })
                continue
            
            pixel_drift = abs(round_trip_pixel - pixel)
            
            results['max_pixel_drift'] = max(results['max_pixel_drift'], pixel_drift)
            
            if pixel_drift > self.config.pixel_tolerance:
                results['pixel_drift_exceeded'] = True
            
            results['details'].append({
                'depth': depth,
                'pixel': pixel,
                'round_trip_depth': round_trip_depth,
                'round_trip_pixel': round_trip_pixel,
                'pixel_drift': pixel_drift,
                'within_tolerance': pixel_drift <= self.config.pixel_tolerance
            })
        
        # Overall validation result
        results['validation_passed'] = (
            not results['pixel_drift_exceeded'] and 
            results['max_pixel_drift'] <= self.config.pixel_tolerance
        )
        
        logger.debug(f"Pixel alignment validation: "
                    f"max_drift={results['max_pixel_drift']}px, "
                    f"passed={results['validation_passed']}")
        
        return results
    
    def get_pixel_range_for_depth_range(self, min_depth: float, max_depth: float) -> Tuple[int, int]:
        """
        Get pixel range for a depth range.
        
        Args:
            min_depth: Minimum depth
            max_depth: Maximum depth
            
        Returns:
            Tuple of (min_pixel, max_pixel)
        """
        min_pixel = self.depth_to_pixel(min_depth)
        max_pixel = self.depth_to_pixel(max_depth)
        
        if min_pixel is None or max_pixel is None:
            raise ValueError(f"Depth range [{min_depth}, {max_depth}] maps outside viewport")
        
        # Ensure min_pixel <= max_pixel
        if min_pixel > max_pixel:
            min_pixel, max_pixel = max_pixel, min_pixel
        
        return (min_pixel, max_pixel)
    
    def get_depth_range_for_pixel_range(self, min_pixel: int, max_pixel: int) -> Tuple[float, float]:
        """
        Get depth range for a pixel range.
        
        Args:
            min_pixel: Minimum pixel
            max_pixel: Maximum pixel
            
        Returns:
            Tuple of (min_depth, max_depth)
        """
        min_depth = self.pixel_to_depth(min_pixel)
        max_depth = self.pixel_to_depth(max_pixel)
        
        if min_depth is None or max_depth is None:
            raise ValueError(f"Pixel range [{min_pixel}, {max_pixel}] maps outside depth range")
        
        # Ensure min_depth <= max_depth
        if min_depth > max_depth:
            min_depth, max_depth = max_depth, min_depth
        
        return (min_depth, max_depth)
    
    def _clear_cache(self) -> None:
        """Clear the mapping caches."""
        self._depth_to_pixel_cache.clear()
        self._pixel_to_depth_cache.clear()
        logger.debug("Pixel-depth mapping cache cleared")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'depth_cache_size': len(self._depth_to_pixel_cache),
            'pixel_cache_size': len(self._pixel_to_depth_cache)
        }
    
    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._cache_hits = 0
        self._cache_misses = 0
        logger.debug("Cache statistics reset")
    
    # Properties
    
    @property
    def depth_range(self) -> Tuple[float, float]:
        """Get current depth range."""
        return self._depth_range
    
    @property
    def viewport_size(self) -> Tuple[int, int]:
        """Get current viewport size."""
        return self._viewport_size
    
    @property
    def usable_height(self) -> int:
        """Get usable height (excluding padding)."""
        return self.config.viewport_height - (2 * self.config.vertical_padding)


# Test function
def test_pixel_depth_mapper():
    """Test function for PixelDepthMapper."""
    import sys
    
    print("Testing PixelDepthMapper...")
    
    # Create mapper with test configuration
    config = PixelMappingConfig(
        min_depth=0.0,
        max_depth=100.0,
        viewport_width=800,
        viewport_height=600,
        vertical_padding=2,
        pixel_tolerance=1
    )
    
    mapper = PixelDepthMapper(config)
    
    # Test basic mapping
    print(f"Depth range: {mapper.depth_range}")
    print(f"Viewport size: {mapper.viewport_size}")
    print(f"Usable height: {mapper.usable_height}px")
    
    # Test depth → pixel
    test_depths = [0.0, 25.0, 50.0, 75.0, 100.0]
    for depth in test_depths:
        pixel = mapper.depth_to_pixel(depth)
        print(f"  Depth {depth:.1f} → Pixel {pixel}")
    
    # Test pixel → depth
    test_pixels = [2, 150, 300, 450, 597]  # Within padding bounds
    for pixel in test_pixels:
        depth = mapper.pixel_to_depth(pixel)
        if depth is not None:
            print(f"  Pixel {pixel} → Depth {depth:.2f}")
    
    # Validate pixel alignment
    print("\nValidating pixel alignment...")
    validation = mapper.validate_pixel_alignment()
    
    print(f"  Test points: {validation['test_points']}")
    print(f"  Max pixel drift: {validation['max_pixel_drift']}px")
    print(f"  Tolerance: {config.pixel_tolerance}px")
    print(f"  Validation passed: {validation['validation_passed']}")
    
    # Show cache stats
    stats = mapper.get_cache_stats()
    print(f"\nCache stats: {stats['hits']} hits, {stats['misses']} misses, "
          f"hit rate: {stats['hit_rate']:.1%}")
    
    return validation['validation_passed']


if __name__ == "__main__":
    success = test_pixel_depth_mapper()
    sys.exit(0 if success else 1)