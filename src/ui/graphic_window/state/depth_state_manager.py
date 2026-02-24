"""
DepthStateManager - Central state manager for depth synchronization.

Follows the blueprint pattern: single source of truth for all depth-related state.
All components must get a reference to this manager, subscribe to its signals,
update it on user interaction, and never store duplicate state.

Enhanced with synchronizers for advanced functionality.
"""

from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from src.core.graphic_models import HoleDataProvider
# Synchronizers imported lazily in _init_synchronizers to avoid circular imports


from .depth_range import DepthRange


class DepthStateManager(QObject):
    """
    Central state manager for all depth-related state.
    This is the SINGLE SOURCE OF TRUTH.
    All components subscribe to signals and update accordingly.
    
    This is critical: do NOT let components maintain their own depth state.
    All depth changes MUST go through this manager.
    
    Enhanced with synchronizers for:
    - Advanced scroll handling (smooth scrolling, acceleration)
    - Selection validation and multi-select modes
    - Cursor snapping to data points
    """
    
    # Signals - emitted when state changes
    viewportRangeChanged = pyqtSignal(DepthRange)      # Visible depth range changed
    cursorDepthChanged = pyqtSignal(float)              # Cursor/selection depth changed
    selectionRangeChanged = pyqtSignal(object)         # Selected interval changed (DepthRange or None)
    zoomLevelChanged = pyqtSignal(float)                # Zoom factor changed
    
    # Additional signals from synchronizers
    cursorSnapped = pyqtSignal(float, str)             # (snapped_depth, snap_type)
    selectionValidated = pyqtSignal(bool, str)         # (is_valid, message)
    scrollPositionChanged = pyqtSignal(float)          # 0-1 representing scroll position
    
    def __init__(self, min_depth: float = 0.0, max_depth: float = 100.0,
                 data_provider: Optional[HoleDataProvider] = None):
        super().__init__()
        
        # Depth bounds
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.data_provider = data_provider
        
        # Viewport (what's visible on screen)
        window_size = max_depth - min_depth
        self._viewport_range = DepthRange(min_depth, min(max_depth, min_depth + window_size / 2))
        
        # Cursor depth (for highlighting)
        self._cursor_depth = min_depth
        
        # Selection range (from lithology selection)
        self._selection_range: Optional[DepthRange] = None
        
        # Zoom level (1.0 = normal, >1 = zoomed in, <1 = zoomed out)
        self._zoom_level = 1.0
        
        # Initialize synchronizers
        self._init_synchronizers()
    
    def _init_synchronizers(self):
        """Initialize and connect synchronizers."""
        # Lazy import to avoid circular imports
        from src.ui.graphic_window.synchronizers import (
            ScrollSynchronizer, SelectionSynchronizer, DepthSynchronizer
        )
        
        # ScrollSynchronizer - needs viewport height (depth range visible)
        viewport_height = self._viewport_range.range_size
        self.scroll_sync = ScrollSynchronizer(
            min_depth=self.min_depth,
            max_depth=self.max_depth,
            viewport_height=viewport_height
        )
        
        # SelectionSynchronizer
        self.selection_sync = SelectionSynchronizer()
        
        # DepthSynchronizer (only if data provider available)
        self.depth_sync = None
        if self.data_provider is not None:
            self.depth_sync = DepthSynchronizer(self.data_provider)
        
        # Connect synchronizer signals to our signals
        self.scroll_sync.depthRangeChanged.connect(self._on_sync_depth_range_changed)
        self.scroll_sync.scrollPositionChanged.connect(self.scrollPositionChanged.emit)
        
        self.selection_sync.selectionChanged.connect(self._on_sync_selection_changed)
        self.selection_sync.selectionValidated.connect(self.selectionValidated.emit)
        
        if self.depth_sync is not None:
            self.depth_sync.cursorSnapped.connect(self.cursorSnapped.emit)
            # DepthSynchronizer.cursorDepthChanged is connected internally in set_cursor_depth
    
    def _on_sync_depth_range_changed(self, depth_range: DepthRange):
        """Handle depth range change from ScrollSynchronizer."""
        if (depth_range.from_depth != self._viewport_range.from_depth or
            depth_range.to_depth != self._viewport_range.to_depth):
            self._viewport_range = depth_range
            self.viewportRangeChanged.emit(depth_range)
    
    def _on_sync_selection_changed(self, selection):
        """Handle selection change from SelectionSynchronizer."""
        if selection is None:
            self._selection_range = None
        elif isinstance(selection, DepthRange):
            self._selection_range = selection
        elif isinstance(selection, list):
            # Multiple selections - for now, take the first one
            # TODO: Support multiple selections properly
            if selection:
                self._selection_range = selection[0]
            else:
                self._selection_range = None
        
        self.selectionRangeChanged.emit(self._selection_range)
    
    # ========== VIEWPORT MANAGEMENT ==========
    
    def set_viewport_range(self, from_depth: float, to_depth: float):
        """
        Set the depth range being viewed.
        Called when user scrolls or changes view window.
        """
        # Use ScrollSynchronizer for consistency
        self.scroll_sync.set_viewport_range(from_depth, to_depth)
        # Note: _on_sync_depth_range_changed will update _viewport_range and emit signal
    
    def get_viewport_range(self) -> DepthRange:
        """Get currently visible depth range."""
        return self._viewport_range
    
    def scroll_viewport(self, depth_delta: float):
        """
        Scroll viewport by depth delta.
        Positive = deeper, Negative = shallower.
        """
        # Use ScrollSynchronizer for advanced scrolling
        if depth_delta > 0:
            self.scroll_sync.scroll_down(abs(depth_delta))
        else:
            self.scroll_sync.scroll_up(abs(depth_delta))
    
    def handle_wheel_event(self, delta: int, ctrl_pressed: bool = False):
        """
        Handle mouse wheel event.
        
        Args:
            delta: Wheel delta (positive = scroll up, negative = scroll down)
            ctrl_pressed: Whether Ctrl key is pressed (zoom vs scroll)
        """
        self.scroll_sync.handle_wheel_event(delta, ctrl_pressed)
    
    def set_scroll_position(self, position: float):
        """
        Set scroll position (0 = top, 1 = bottom).
        
        Args:
            position: Scroll position from 0.0 to 1.0
        """
        self.scroll_sync.set_scroll_position(position)
    
    def get_scrollbar_values(self):
        """Get values for scrollbar (min, max, page_step, value)."""
        return self.scroll_sync.get_scrollbar_values()
    
    # ========== CURSOR MANAGEMENT ==========
    
    def set_cursor_depth(self, depth: float, snap: bool = True):
        """
        Set the cursor depth (for highlighting/crosshair).
        Called when user clicks or moves cursor.
        
        Args:
            depth: Target depth
            snap: Whether to snap to nearest data point (if DepthSynchronizer available)
        """
        # Use DepthSynchronizer if available
        if self.depth_sync is not None and snap:
            self.depth_sync.set_cursor_depth(depth, snap=True)
            # DepthSynchronizer will emit cursorDepthChanged which we need to forward
            # Connect signal if not already connected
            if not hasattr(self, '_depth_sync_connected'):
                self.depth_sync.cursorDepthChanged.connect(self._on_sync_cursor_changed)
                self._depth_sync_connected = True
        else:
            # Simple version without snapping
            depth = max(self.min_depth, min(self.max_depth, depth))
            if depth != self._cursor_depth:
                self._cursor_depth = depth
                self.cursorDepthChanged.emit(depth)
    
    def _on_sync_cursor_changed(self, depth: float):
        """Handle cursor depth change from DepthSynchronizer."""
        if depth != self._cursor_depth:
            self._cursor_depth = depth
            self.cursorDepthChanged.emit(depth)
    
    def get_cursor_depth(self) -> float:
        """Get current cursor depth."""
        return self._cursor_depth
    
    # ========== SELECTION MANAGEMENT ==========
    
    def set_selection_range(self, from_depth: float, to_depth: float):
        """
        Set selected lithology range.
        Called when user selects interval in table or strat column.
        """
        # Use SelectionSynchronizer for validation and advanced features
        self.selection_sync.set_selection(from_depth, to_depth)
        # Note: _on_sync_selection_changed will update _selection_range and emit signal
    
    def get_selection_range(self) -> Optional[DepthRange]:
        """Get selected depth range, or None if nothing selected."""
        return self._selection_range
    
    def clear_selection(self):
        """Clear selection."""
        self.selection_sync.clear_selection()
    
    def set_selection_mode(self, mode: str):
        """
        Set selection mode.
        
        Args:
            mode: "single", "range", or "multiple"
        """
        self.selection_sync.set_selection_mode(mode)
    
    def get_selection_mode(self) -> str:
        """Get current selection mode."""
        return self.selection_sync.selection_mode
    
    # ========== ZOOM MANAGEMENT ==========
    
    def set_zoom_level(self, zoom: float):
        """
        Set zoom level.
        1.0 = normal, 2.0 = zoomed in 2x, 0.5 = zoomed out 2x.
        """
        zoom = max(0.1, min(10.0, zoom))  # Clamp between 0.1x and 10x
        
        if zoom != self._zoom_level:
            self._zoom_level = zoom
            self.zoomLevelChanged.emit(zoom)
            
            # Update viewport range based on zoom
            # When zooming, we keep the center depth constant
            center_depth = (self._viewport_range.from_depth + self._viewport_range.to_depth) / 2
            new_range_size = (self.max_depth - self.min_depth) / zoom
            
            from_depth = max(self.min_depth, center_depth - new_range_size / 2)
            to_depth = min(self.max_depth, from_depth + new_range_size)
            
            self.set_viewport_range(from_depth, to_depth)
    
    def get_zoom_level(self) -> float:
        """Get current zoom level."""
        return self._zoom_level
    
    def zoom_in(self, factor: float = 1.25):
        """Zoom in by factor."""
        self.set_zoom_level(self._zoom_level * factor)
    
    def zoom_out(self, factor: float = 0.8):
        """Zoom out by factor."""
        self.set_zoom_level(self._zoom_level * factor)
    
    # ========== UTILITY METHODS ==========
    
    def center_on_depth(self, depth: float):
        """
        Center viewport on a specific depth.
        Used when user clicks to navigate.
        """
        self.scroll_sync.scroll_to_depth(depth)
    
    def reset_to_defaults(self):
        """Reset all state to defaults."""
        window_size = self.max_depth - self.min_depth
        self.set_viewport_range(self.min_depth, min(self.max_depth, self.min_depth + window_size / 2))
        self.set_cursor_depth(self.min_depth, snap=False)
        self.clear_selection()
        self.set_zoom_level(1.0)
    
    def get_state_dict(self) -> dict:
        """Get complete state as dict (for saving/debugging)."""
        result = {
            'viewport': {
                'from': self._viewport_range.from_depth,
                'to': self._viewport_range.to_depth
            },
            'cursor': self._cursor_depth,
            'selection': None,
            'zoom': self._zoom_level,
            'scroll_position': self.scroll_sync.scroll_position if hasattr(self, 'scroll_sync') else 0.0
        }
        if self._selection_range is not None:
            result['selection'] = {
                'from': self._selection_range.from_depth,
                'to': self._selection_range.to_depth
            }
        return result
    
    # ========== SYNCHRONIZER ACCESS ==========
    
    def get_scroll_synchronizer(self) -> 'ScrollSynchronizer':
        """Get the ScrollSynchronizer instance."""
        return self.scroll_sync
    
    def get_selection_synchronizer(self) -> 'SelectionSynchronizer':
        """Get the SelectionSynchronizer instance."""
        return self.selection_sync
    
    def get_depth_synchronizer(self) -> Optional['DepthSynchronizer']:
        """Get the DepthSynchronizer instance (if available)."""
        return self.depth_sync