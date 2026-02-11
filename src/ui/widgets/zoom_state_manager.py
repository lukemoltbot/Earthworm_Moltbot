"""
ZoomStateManager - Manages zoom state and synchronization between widgets.

This class provides:
1. Centralized zoom state storage
2. Depth bounds enforcement
3. Zoom center alignment
4. Consistent depth scale management
5. Debug logging for zoom operations
"""

import time
import logging
from PyQt6.QtCore import QObject, pyqtSignal


class ZoomStateManager(QObject):
    """
    Manages zoom state synchronization between EnhancedStratigraphicColumn and PyQtGraphCurvePlotter.
    
    Features:
    - Centralized zoom state storage
    - Depth bounds enforcement (1m above top, 5m below bottom)
    - Zoom center alignment
    - Consistent depth scale (10 pixels per metre)
    - Debug logging
    """
    
    # Signals
    zoomStateChanged = pyqtSignal(float, float, float)  # center_depth, min_depth, max_depth
    zoomLevelChanged = pyqtSignal(float)  # zoom_factor
    depthScaleChanged = pyqtSignal(float)  # depth_scale
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Zoom state
        self.center_depth = 0.0
        self.visible_min_depth = 0.0
        self.visible_max_depth = 100.0
        self.zoom_factor = 1.0
        
        # Depth bounds
        self.hole_top_depth = 0.0
        self.hole_bottom_depth = 100.0
        self.min_zoom_above_top = 1.0  # 1m above top of hole
        self.max_zoom_below_bottom = 5.0  # 5m below bottom
        
        # Depth scale (must be consistent between widgets)
        self.depth_scale = 10.0  # 10 pixels per metre
        
        # Widget references
        self.enhanced_column = None
        self.curve_plotter = None
        
        # Synchronization control
        self.sync_in_progress = False
        self.last_sync_time = 0
        self.sync_debounce_ms = 50
        
        # Debug logging
        self.logger = logging.getLogger(__name__)
        self.debug_enabled = True
        
    def set_widgets(self, enhanced_column, curve_plotter):
        """Set references to the widgets being synchronized."""
        self.enhanced_column = enhanced_column
        self.curve_plotter = curve_plotter
        
        # Ensure both widgets use the same depth scale
        if self.enhanced_column:
            self.enhanced_column.depth_scale = self.depth_scale
        if self.curve_plotter:
            self.curve_plotter.depth_scale = self.depth_scale
            
        self._log_debug(f"Widgets set: enhanced_column={enhanced_column is not None}, curve_plotter={curve_plotter is not None}")
        
    def set_hole_depth_range(self, top_depth, bottom_depth):
        """Set the hole depth range for bounds enforcement."""
        self.hole_top_depth = top_depth
        self.hole_bottom_depth = bottom_depth
        self._log_debug(f"Hole depth range set: top={top_depth:.2f}, bottom={bottom_depth:.2f}")
        
    def set_depth_scale(self, depth_scale):
        """Set the depth scale (pixels per metre)."""
        if depth_scale <= 0:
            self._log_error(f"Invalid depth scale: {depth_scale}")
            return
            
        self.depth_scale = depth_scale
        
        # Update widgets
        if self.enhanced_column:
            self.enhanced_column.depth_scale = depth_scale
        if self.curve_plotter:
            self.curve_plotter.depth_scale = depth_scale
            
        self.depthScaleChanged.emit(depth_scale)
        self._log_debug(f"Depth scale set: {depth_scale} pixels per metre")
        
    def get_zoom_state(self):
        """Get current zoom state."""
        return {
            'center_depth': self.center_depth,
            'visible_min_depth': self.visible_min_depth,
            'visible_max_depth': self.visible_max_depth,
            'zoom_factor': self.zoom_factor,
            'depth_scale': self.depth_scale,
            'visible_range': self.visible_max_depth - self.visible_min_depth
        }
        
    def zoom_to_depth(self, center_depth, zoom_factor=None):
        """
        Zoom to a specific depth with optional zoom factor.
        
        Args:
            center_depth: Target center depth
            zoom_factor: Optional zoom factor (None to keep current)
        """
        if self._should_sync():
            self.sync_in_progress = True
            self.last_sync_time = time.time() * 1000
            
            try:
                # Update zoom factor if provided
                if zoom_factor is not None:
                    self.zoom_factor = zoom_factor
                    self.zoomLevelChanged.emit(zoom_factor)
                
                # Calculate visible range based on current view height or zoom factor
                visible_range = self._calculate_visible_range(zoom_factor)
                
                # Calculate min and max depths
                new_min_depth = center_depth - visible_range / 2
                new_max_depth = center_depth + visible_range / 2
                
                # Apply depth bounds
                new_min_depth, new_max_depth = self._apply_depth_bounds(new_min_depth, new_max_depth)
                
                # Recalculate center depth after bounds enforcement
                self.center_depth = (new_min_depth + new_max_depth) / 2
                self.visible_min_depth = new_min_depth
                self.visible_max_depth = new_max_depth
                
                # Apply to widgets
                self._apply_to_widgets()
                
                # Emit signals
                self.zoomStateChanged.emit(self.center_depth, self.visible_min_depth, self.visible_max_depth)
                
                self._log_debug(f"Zoomed to depth: center={self.center_depth:.2f}, "
                              f"range=[{self.visible_min_depth:.2f}, {self.visible_max_depth:.2f}], "
                              f"zoom_factor={self.zoom_factor:.2f}")
                
            finally:
                self.sync_in_progress = False
                
    def zoom_to_range(self, min_depth, max_depth):
        """
        Zoom to a specific depth range.
        
        Args:
            min_depth: Minimum visible depth
            max_depth: Maximum visible depth
        """
        if self._should_sync():
            self.sync_in_progress = True
            self.last_sync_time = time.time() * 1000
            
            try:
                # Apply depth bounds
                min_depth, max_depth = self._apply_depth_bounds(min_depth, max_depth)
                
                # Update state
                self.visible_min_depth = min_depth
                self.visible_max_depth = max_depth
                self.center_depth = (min_depth + max_depth) / 2
                
                # Calculate zoom factor
                total_range = self.hole_bottom_depth - self.hole_top_depth
                visible_range = max_depth - min_depth
                if total_range > 0 and visible_range > 0:
                    self.zoom_factor = total_range / visible_range
                    self.zoomLevelChanged.emit(self.zoom_factor)
                
                # Apply to widgets
                self._apply_to_widgets()
                
                # Emit signals
                self.zoomStateChanged.emit(self.center_depth, self.visible_min_depth, self.visible_max_depth)
                
                self._log_debug(f"Zoomed to range: [{min_depth:.2f}, {max_depth:.2f}], "
                              f"center={self.center_depth:.2f}, zoom_factor={self.zoom_factor:.2f}")
                
            finally:
                self.sync_in_progress = False
                
    def sync_from_enhanced_column(self, center_depth, min_depth, max_depth):
        """
        Synchronize zoom state from enhanced stratigraphic column.
        
        Args:
            center_depth: Center depth from enhanced column
            min_depth: Minimum visible depth from enhanced column
            max_depth: Maximum visible depth from enhanced column
        """
        if self._should_sync():
            self.sync_in_progress = True
            self.last_sync_time = time.time() * 1000
            
            try:
                # Update state
                self.center_depth = center_depth
                self.visible_min_depth = min_depth
                self.visible_max_depth = max_depth
                
                # Calculate zoom factor
                total_range = self.hole_bottom_depth - self.hole_top_depth
                visible_range = max_depth - min_depth
                if total_range > 0 and visible_range > 0:
                    self.zoom_factor = total_range / visible_range
                    self.zoomLevelChanged.emit(self.zoom_factor)
                
                # Apply to curve plotter
                if self.curve_plotter:
                    self.curve_plotter.setYRange(min_depth, max_depth)
                
                self._log_debug(f"Synced from enhanced column: center={center_depth:.2f}, "
                              f"range=[{min_depth:.2f}, {max_depth:.2f}]")
                
            finally:
                self.sync_in_progress = False
                
    def sync_from_curve_plotter(self, min_depth, max_depth):
        """
        Synchronize zoom state from curve plotter.
        
        Args:
            min_depth: Minimum visible depth from curve plotter
            max_depth: Maximum visible depth from curve plotter
        """
        if self._should_sync():
            self.sync_in_progress = True
            self.last_sync_time = time.time() * 1000
            
            try:
                # Apply depth bounds
                min_depth, max_depth = self._apply_depth_bounds(min_depth, max_depth)
                
                # Update state
                self.visible_min_depth = min_depth
                self.visible_max_depth = max_depth
                self.center_depth = (min_depth + max_depth) / 2
                
                # Calculate zoom factor
                total_range = self.hole_bottom_depth - self.hole_top_depth
                visible_range = max_depth - min_depth
                if total_range > 0 and visible_range > 0:
                    self.zoom_factor = total_range / visible_range
                    self.zoomLevelChanged.emit(self.zoom_factor)
                
                # Apply to enhanced column
                if self.enhanced_column:
                    self.enhanced_column.scroll_to_depth(self.center_depth)
                
                self._log_debug(f"Synced from curve plotter: center={self.center_depth:.2f}, "
                              f"range=[{min_depth:.2f}, {max_depth:.2f}]")
                
            finally:
                self.sync_in_progress = False
                
    def _calculate_visible_range(self, zoom_factor=None):
        """Calculate visible depth range based on zoom factor or current view."""
        if zoom_factor is not None:
            # Calculate based on zoom factor
            total_range = self.hole_bottom_depth - self.hole_top_depth
            if total_range > 0:
                return total_range / zoom_factor
            else:
                return 100.0  # Default fallback
        else:
            # Use current visible range
            return self.visible_max_depth - self.visible_min_depth
            
    def _apply_depth_bounds(self, min_depth, max_depth):
        """
        Apply depth bounds enforcement.
        
        Rules:
        1. Minimum zoom = 1m above top of hole
        2. Maximum zoom = 5m below bottom
        3. Ensure min_depth < max_depth
        """
        # Calculate bounds
        min_allowed = self.hole_top_depth - self.min_zoom_above_top
        max_allowed = self.hole_bottom_depth + self.max_zoom_below_bottom
        
        # Apply bounds
        min_depth = max(min_depth, min_allowed)
        max_depth = min(max_depth, max_allowed)
        
        # Ensure valid range
        if min_depth >= max_depth:
            # Fallback to reasonable range
            range_size = max_allowed - min_allowed
            if range_size > 0:
                min_depth = min_allowed
                max_depth = min_allowed + min(range_size, 100.0)  # Max 100m range
            else:
                min_depth = 0.0
                max_depth = 100.0
                
        return min_depth, max_depth
        
    def _apply_to_widgets(self):
        """Apply current zoom state to widgets."""
        # Apply to enhanced column
        if self.enhanced_column:
            # Enhanced column uses scroll_to_depth for centering
            self.enhanced_column.scroll_to_depth(self.center_depth)
            
        # Apply to curve plotter
        if self.curve_plotter:
            self.curve_plotter.setYRange(self.visible_min_depth, self.visible_max_depth)
            
    def _should_sync(self):
        """Check if synchronization should proceed."""
        current_time = time.time() * 1000
        
        # Check if sync is already in progress
        if self.sync_in_progress:
            return False
            
        # Check if enough time has passed since last sync
        time_since_last_sync = current_time - self.last_sync_time
        if time_since_last_sync < self.sync_debounce_ms:
            return False
            
        return True
        
    def _log_debug(self, message):
        """Log debug message if debug is enabled."""
        if self.debug_enabled:
            print(f"DEBUG [ZoomStateManager]: {message}")
            
    def _log_error(self, message):
        """Log error message."""
        print(f"ERROR [ZoomStateManager]: {message}")
        
    def enable_debug_logging(self, enabled):
        """Enable or disable debug logging."""
        self.debug_enabled = enabled
        print(f"ZoomStateManager debug logging {'enabled' if enabled else 'disabled'}")
        
    def get_status(self):
        """Get current status for debugging."""
        return {
            'center_depth': self.center_depth,
            'visible_min_depth': self.visible_min_depth,
            'visible_max_depth': self.visible_max_depth,
            'zoom_factor': self.zoom_factor,
            'depth_scale': self.depth_scale,
            'hole_top_depth': self.hole_top_depth,
            'hole_bottom_depth': self.hole_bottom_depth,
            'sync_in_progress': self.sync_in_progress,
            'last_sync_time': self.last_sync_time
        }