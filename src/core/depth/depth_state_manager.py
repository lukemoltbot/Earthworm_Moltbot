"""
DepthStateManager - Central state manager for depth synchronization.

Follows the blueprint pattern: single source of truth for all depth-related state.
All components must get a reference to this manager, subscribe to its signals,
update it on user interaction, and never store duplicate state.
"""

from dataclasses import dataclass
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


@dataclass
class DepthRange:
    """Immutable depth range."""
    from_depth: float
    to_depth: float
    
    @property
    def range_size(self) -> float:
        return self.to_depth - self.from_depth
    
    def contains(self, depth: float) -> bool:
        return self.from_depth <= depth <= self.to_depth


class DepthStateManager(QObject):
    """
    Central state manager - SINGLE SOURCE OF TRUTH for all depth-related state.
    
    All components MUST:
    1. Get a reference to this manager
    2. Subscribe to its signals
    3. Update this when user interacts
    4. Never store duplicate state
    """
    
    # Signals - all components listen to these
    viewportRangeChanged = pyqtSignal(DepthRange)
    cursorDepthChanged = pyqtSignal(float)
    selectionRangeChanged = pyqtSignal(object)  # DepthRange or None
    zoomLevelChanged = pyqtSignal(float)
    
    def __init__(self, min_depth: float = 0.0, max_depth: float = 100.0):
        super().__init__()
        
        # Depth bounds
        self.min_depth = min_depth
        self.max_depth = max_depth
        
        # Internal state (NEVER access these directly from outside!)
        self._viewport_range = DepthRange(min_depth, min(max_depth, min_depth + 10))
        self._cursor_depth = min_depth
        self._selection_range: Optional[DepthRange] = None
        self._zoom_level = 1.0
    
    # ========== VIEWPORT MANAGEMENT ==========
    
    def set_viewport_range(self, from_depth: float, to_depth: float):
        """Set the depth range being viewed."""
        from_depth = max(self.min_depth, from_depth)
        to_depth = min(self.max_depth, to_depth)
        
        if from_depth >= to_depth:
            return
        
        new_range = DepthRange(from_depth, to_depth)
        
        if (new_range.from_depth != self._viewport_range.from_depth or
            new_range.to_depth != self._viewport_range.to_depth):
            self._viewport_range = new_range
            self.viewportRangeChanged.emit(new_range)
    
    def get_viewport_range(self) -> DepthRange:
        return self._viewport_range
    
    def scroll_viewport(self, depth_delta: float):
        """Scroll viewport by depth delta."""
        new_from = self._viewport_range.from_depth + depth_delta
        new_to = self._viewport_range.to_depth + depth_delta
        
        if new_from < self.min_depth:
            new_from = self.min_depth
            new_to = new_from + self._viewport_range.range_size
        elif new_to > self.max_depth:
            new_to = self.max_depth
            new_from = new_to - self._viewport_range.range_size
        
        self.set_viewport_range(new_from, new_to)
    
    # ========== CURSOR MANAGEMENT ==========
    
    def set_cursor_depth(self, depth: float):
        """Set cursor depth for highlighting."""
        depth = max(self.min_depth, min(self.max_depth, depth))
        
        if depth != self._cursor_depth:
            self._cursor_depth = depth
            self.cursorDepthChanged.emit(depth)
    
    def get_cursor_depth(self) -> float:
        return self._cursor_depth
    
    # ========== SELECTION MANAGEMENT ==========
    
    def set_selection_range(self, from_depth: float, to_depth: float):
        """Set selected depth range."""
        if from_depth >= to_depth:
            return
        
        new_range = DepthRange(from_depth, to_depth)
        
        if (self._selection_range is None or
            self._selection_range.from_depth != new_range.from_depth or
            self._selection_range.to_depth != new_range.to_depth):
            self._selection_range = new_range
            self.selectionRangeChanged.emit(new_range)
    
    def get_selection_range(self) -> Optional[DepthRange]:
        return self._selection_range
    
    def clear_selection(self):
        """Clear selection."""
        if self._selection_range is not None:
            self._selection_range = None
            self.selectionRangeChanged.emit(None)