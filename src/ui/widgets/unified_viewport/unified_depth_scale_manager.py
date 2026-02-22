"""
UnifiedDepthScaleManager - Synchronization engine for unified viewport.

Manages pixel-perfect depth synchronization between curves and stratigraphic column
with signal emission for depth and zoom changes.
"""

import logging
import math
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QRect, QPoint

logger = logging.getLogger(__name__)


class DepthScaleMode(Enum):
    """Depth scale synchronization modes."""
    PIXEL_PERFECT = "pixel_perfect"  # 1-pixel accuracy
    REAL_TIME = "real_time"  # Prioritize performance over perfect sync
    MANUAL = "manual"  # No automatic synchronization


@dataclass
class DepthScaleConfig:
    """Configuration for depth scale management."""
    # Synchronization settings
    mode: DepthScaleMode = DepthScaleMode.PIXEL_PERFECT
    pixel_tolerance: int = 1  # Maximum allowed pixel drift
    
    # Depth range settings
    min_depth: float = 0.0
    max_depth: float = 10000.0  # 10km default
    default_view_range: Tuple[float, float] = (0.0, 1000.0)  # Default 1km view
    
    # Zoom settings
    min_zoom_level: float = 0.01  # 1% zoom (very zoomed out)
    max_zoom_level: float = 100.0  # 100x zoom (very zoomed in)
    default_zoom_level: float = 1.0  # 1:1 scale
    zoom_step_factor: float = 1.2  # 20% zoom per step
    
    # Performance settings
    enable_caching: bool = True
    cache_size: int = 1000  # Number of depth-pixel mappings to cache
    update_throttle_ms: int = 16  # ~60 FPS throttle
    
    # Signal emission
    emit_signals_on_update: bool = True
    signal_throttle_ms: int = 50  # Throttle signal emission


class UnifiedDepthScaleManager(QObject):
    """
    Manages depth scale synchronization between unified viewport components.
    
    Provides pixel-perfect depth mapping and emits signals for depth and zoom changes.
    """
    
    # Signals
    depthChanged = pyqtSignal(float)  # Current depth position changed
    zoomLevelChanged = pyqtSignal(float)  # Zoom level changed
    viewRangeChanged = pyqtSignal(float, float)  # Visible depth range changed
    syncStatusChanged = pyqtSignal(bool, str)  # Sync status changed (in_sync, message)
    
    def __init__(self, config: Optional[DepthScaleConfig] = None):
        """
        Initialize the depth scale manager.
        
        Args:
            config: Configuration for depth scale management
        """
        super().__init__()
        
        self.config = config or DepthScaleConfig()
        self._current_depth: float = self.config.default_view_range[0]
        self._current_zoom: float = self.config.default_zoom_level
        self._view_range: Tuple[float, float] = self.config.default_view_range
        self._pixel_height: int = 0
        self._depth_per_pixel: float = 0.0
        self._is_synchronized: bool = False
        self._sync_error_message: str = ""
        
        # Cache for depth-pixel mappings
        self._depth_cache: Dict[float, int] = {}
        self._pixel_cache: Dict[int, float] = {}
        
        # Throttle timers
        self._signal_throttle_timer = QTimer()
        self._signal_throttle_timer.setSingleShot(True)
        self._signal_throttle_timer.timeout.connect(self._emit_throttled_signals)
        
        self._update_throttle_timer = QTimer()
        self._update_throttle_timer.setSingleShot(True)
        
        # Pending signal values
        self._pending_depth: Optional[float] = None
        self._pending_zoom: Optional[float] = None
        self._pending_view_range: Optional[Tuple[float, float]] = None
        
        logger.debug(f"UnifiedDepthScaleManager initialized with mode: {self.config.mode}")
    
    def set_viewport_height(self, height_pixels: int) -> None:
        """
        Set the viewport height in pixels.
        
        Args:
            height_pixels: Viewport height in pixels
        """
        if height_pixels <= 0:
            logger.warning(f"Invalid viewport height: {height_pixels}")
            return
            
        self._pixel_height = height_pixels
        self._update_depth_per_pixel()
        self._clear_cache()
        logger.debug(f"Viewport height set to {height_pixels} pixels")
    
    def _update_depth_per_pixel(self) -> None:
        """Update depth per pixel calculation based on current view range."""
        if self._pixel_height <= 0:
            self._depth_per_pixel = 0.0
            return
            
        view_range_size = self._view_range[1] - self._view_range[0]
        if view_range_size <= 0:
            self._depth_per_pixel = 0.0
            return
            
        # With N pixels, there are N-1 intervals between pixels
        # Pixel 0 maps to min_depth, pixel (height-1) maps to max_depth
        if self._pixel_height > 1:
            self._depth_per_pixel = view_range_size / (self._pixel_height - 1)
        else:
            self._depth_per_pixel = 0.0  # Single pixel viewport
            
        logger.debug(f"Depth per pixel: {self._depth_per_pixel:.6f} units/pixel")
    
    def depth_to_pixel(self, depth: float) -> int:
        """
        Convert depth value to pixel position.
        
        Args:
            depth: Depth value to convert
            
        Returns:
            Pixel position (0 at top, increasing downward)
        """
        # Check cache first
        if self.config.enable_caching and depth in self._depth_cache:
            return self._depth_cache[depth]
        
        # Calculate pixel position
        if self._depth_per_pixel <= 0:
            return 0
            
        # Use rounding for nearest pixel, not truncation
        pixel_float = (depth - self._view_range[0]) / self._depth_per_pixel
        pixel = int(round(pixel_float))
        
        # Clamp to viewport bounds
        pixel = max(0, min(pixel, self._pixel_height - 1))
        
        # Update cache
        if self.config.enable_caching:
            self._depth_cache[depth] = pixel
            self._pixel_cache[pixel] = depth
            
            # Limit cache size
            if len(self._depth_cache) > self.config.cache_size:
                self._prune_cache()
        
        return pixel
    
    def pixel_to_depth(self, pixel: int) -> float:
        """
        Convert pixel position to depth value.
        
        Args:
            pixel: Pixel position (0 at top, increasing downward)
            
        Returns:
            Depth value
        """
        # Check cache first
        if self.config.enable_caching and pixel in self._pixel_cache:
            return self._pixel_cache[pixel]
        
        # Calculate depth
        if self._pixel_height <= 0:
            return self._view_range[0]
            
        depth = self._view_range[0] + (pixel * self._depth_per_pixel)
        
        # Clamp to depth range
        depth = max(self.config.min_depth, min(depth, self.config.max_depth))
        
        # Update cache
        if self.config.enable_caching:
            self._pixel_cache[pixel] = depth
            self._depth_cache[depth] = pixel
            
            # Limit cache size
            if len(self._pixel_cache) > self.config.cache_size:
                self._prune_cache()
        
        return depth
    
    def set_depth(self, depth: float, emit_signal: bool = True) -> None:
        """
        Set the current depth position.
        
        Args:
            depth: New depth position
            emit_signal: Whether to emit depthChanged signal
        """
        # Clamp to valid range
        depth = max(self.config.min_depth, min(depth, self.config.max_depth))
        
        if abs(depth - self._current_depth) < 0.0001:  # Floating point tolerance
            return
            
        self._current_depth = depth
        
        if emit_signal and self.config.emit_signals_on_update:
            self._pending_depth = depth
            self._throttle_signal_emission()
        
        logger.debug(f"Depth set to {depth:.2f}")
    
    def set_zoom_level(self, zoom: float, emit_signal: bool = True) -> None:
        """
        Set the zoom level.
        
        Args:
            zoom: New zoom level (1.0 = 1:1 scale)
            emit_signal: Whether to emit zoomLevelChanged signal
        """
        # Clamp to valid range
        zoom = max(self.config.min_zoom_level, min(zoom, self.config.max_zoom_level))
        
        if abs(zoom - self._current_zoom) < 0.0001:  # Floating point tolerance
            return
            
        self._current_zoom = zoom
        
        # Update view range based on zoom
        self._update_view_range_from_zoom()
        
        if emit_signal and self.config.emit_signals_on_update:
            self._pending_zoom = zoom
            self._throttle_signal_emission()
        
        logger.debug(f"Zoom level set to {zoom:.2f}x")
    
    def zoom_in(self, factor: Optional[float] = None) -> None:
        """
        Zoom in by specified factor.
        
        Args:
            factor: Zoom factor (defaults to config.zoom_step_factor)
        """
        factor = factor or self.config.zoom_step_factor
        new_zoom = self._current_zoom * factor
        self.set_zoom_level(new_zoom)
    
    def zoom_out(self, factor: Optional[float] = None) -> None:
        """
        Zoom out by specified factor.
        
        Args:
            factor: Zoom factor (defaults to config.zoom_step_factor)
        """
        factor = factor or self.config.zoom_step_factor
        new_zoom = self._current_zoom / factor
        self.set_zoom_level(new_zoom)
    
    def set_view_range(self, start_depth: float, end_depth: float, 
                      emit_signal: bool = True) -> None:
        """
        Set the visible depth range.
        
        Args:
            start_depth: Start of visible range
            end_depth: End of visible range
            emit_signal: Whether to emit viewRangeChanged signal
        """
        # Validate and order range
        if start_depth >= end_depth:
            logger.warning(f"Invalid view range: {start_depth} >= {end_depth}")
            return
            
        # Clamp to valid depth range
        start_depth = max(self.config.min_depth, start_depth)
        end_depth = min(self.config.max_depth, end_depth)
        
        # Check if range actually changed
        if (abs(start_depth - self._view_range[0]) < 0.0001 and
            abs(end_depth - self._view_range[1]) < 0.0001):
            return
            
        self._view_range = (start_depth, end_depth)
        self._update_depth_per_pixel()
        self._clear_cache()
        
        # Update zoom level based on new range
        self._update_zoom_from_view_range()
        
        if emit_signal and self.config.emit_signals_on_update:
            self._pending_view_range = self._view_range
            self._throttle_signal_emission()
        
        logger.debug(f"View range set to [{start_depth:.2f}, {end_depth:.2f}]")
    
    def _update_view_range_from_zoom(self) -> None:
        """Update view range based on current zoom level."""
        if self._current_zoom <= 0:
            return
            
        # Calculate visible range based on zoom
        # At zoom=1.0, we show default range
        # Higher zoom = smaller range (more detail)
        range_size = (self.config.default_view_range[1] - 
                     self.config.default_view_range[0]) / self._current_zoom
        
        # Center on current depth
        center = self._current_depth
        half_range = range_size / 2
        start_depth = center - half_range
        end_depth = center + half_range
        
        # Clamp to valid range
        start_depth = max(self.config.min_depth, start_depth)
        end_depth = min(self.config.max_depth, end_depth)
        
        # Adjust if clamped
        if start_depth == self.config.min_depth:
            end_depth = min(self.config.max_depth, start_depth + range_size)
        elif end_depth == self.config.max_depth:
            start_depth = max(self.config.min_depth, end_depth - range_size)
        
        self.set_view_range(start_depth, end_depth, emit_signal=False)
    
    def _update_zoom_from_view_range(self) -> None:
        """Update zoom level based on current view range."""
        default_range_size = (self.config.default_view_range[1] - 
                            self.config.default_view_range[0])
        current_range_size = self._view_range[1] - self._view_range[0]
        
        if default_range_size <= 0 or current_range_size <= 0:
            return
            
        self._current_zoom = default_range_size / current_range_size
    
    def _throttle_signal_emission(self) -> None:
        """Throttle signal emission to avoid excessive updates."""
        if not self._signal_throttle_timer.isActive():
            self._signal_throttle_timer.start(self.config.signal_throttle_ms)
    
    def _emit_throttled_signals(self) -> None:
        """Emit throttled signals."""
        if self._pending_depth is not None:
            self.depthChanged.emit(self._pending_depth)
            self._pending_depth = None
            
        if self._pending_zoom is not None:
            self.zoomLevelChanged.emit(self._pending_zoom)
            self._pending_zoom = None
            
        if self._pending_view_range is not None:
            self.viewRangeChanged.emit(*self._pending_view_range)
            self._pending_view_range = None
    
    def _clear_cache(self) -> None:
        """Clear the depth-pixel cache."""
        self._depth_cache.clear()
        self._pixel_cache.clear()
    
    def _prune_cache(self) -> None:
        """Prune cache to maintain size limit."""
        # Simple strategy: remove oldest entries
        if len(self._depth_cache) > self.config.cache_size:
            # Convert to list and remove first N entries
            items = list(self._depth_cache.items())
            to_remove = items[:len(items) - self.config.cache_size]
            
            for depth, pixel in to_remove:
                del self._depth_cache[depth]
                if pixel in self._pixel_cache:
                    del self._pixel_cache[pixel]
    
    def check_synchronization(self, curve_pixel: int, column_pixel: int) -> bool:
        """
        Check if curve and column pixels are synchronized.
        
        Args:
            curve_pixel: Pixel position in curve view
            column_pixel: Pixel position in column view
            
        Returns:
            True if synchronized within tolerance
        """
        pixel_diff = abs(curve_pixel - column_pixel)
        is_synced = pixel_diff <= self.config.pixel_tolerance
        
        if is_synced != self._is_synchronized:
            self._is_synchronized = is_synced
            self._sync_error_message = (f"Pixel drift: {pixel_diff}px" 
                                      if not is_synced else "")
            self.syncStatusChanged.emit(is_synced, self._sync_error_message)
        
        return is_synced
    
    def get_sync_status(self) -> Tuple[bool, str]:
        """
        Get current synchronization status.
        
        Returns:
            Tuple of (is_synchronized, error_message)
        """
        return self._is_synchronized, self._sync_error_message
    
    @property
    def current_depth(self) -> float:
        """Get current depth position."""
        return self._current_depth
    
    @property
    def current_zoom(self) -> float:
        """Get current zoom level."""
        return self._current_zoom
    
    @property
    def view_range(self) -> Tuple[float, float]:
        """Get current view range."""
        return self._view_range
    
    @property
    def depth_per_pixel(self) -> float:
        """Get current depth per pixel ratio."""
        return self._depth_per_pixel
    
    @property
    def pixel_height(self) -> int:
        """Get viewport height in pixels."""
        return self._pixel_height