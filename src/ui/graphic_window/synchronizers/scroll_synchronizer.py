"""
ScrollSynchronizer - Handles scroll synchronization across components.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, Tuple
from src.ui.graphic_window.state.depth_range import DepthRange


class ScrollSynchronizer(QObject):
    """
    Handles scroll synchronization across all graphic window components.
    
    Responsibilities:
    1. Convert scroll events to depth range changes
    2. Handle smooth scrolling with acceleration
    3. Coordinate scroll bars across components
    4. Ensure consistent scroll behavior
    """
    
    # Signals
    depthRangeChanged = pyqtSignal(DepthRange)
    scrollPositionChanged = pyqtSignal(float)  # 0-1 representing scroll position
    
    def __init__(self, min_depth: float, max_depth: float, viewport_height: float):
        super().__init__()
        
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.viewport_height = viewport_height  # Depth range visible at once
        
        self.current_depth_range: Optional[DepthRange] = None
        self.scroll_position = 0.0  # 0 = top, 1 = bottom
        
        # Scroll settings
        self.scroll_sensitivity = 0.5  # Depth units per scroll tick
        self.smooth_scroll_enabled = True
        self.scroll_acceleration = 1.2
    
    def set_depth_range(self, min_depth: float, max_depth: float):
        """Set the total depth range (entire hole)."""
        self.min_depth = min_depth
        self.max_depth = max_depth
        self._update_scroll_position()
    
    def set_viewport_height(self, viewport_height: float):
        """Set the viewport height in depth units."""
        self.viewport_height = viewport_height
        self._update_scroll_position()
    
    def handle_wheel_event(self, delta: int, ctrl_pressed: bool = False):
        """
        Handle mouse wheel event.
        
        Args:
            delta: Wheel delta (positive = scroll up, negative = scroll down)
            ctrl_pressed: Whether Ctrl key is pressed (zoom vs scroll)
        """
        # Calculate scroll amount
        scroll_amount = self.scroll_sensitivity
        if ctrl_pressed:
            scroll_amount *= 0.1  # Fine scroll with Ctrl
        
        # Apply acceleration if enabled
        if self.smooth_scroll_enabled:
            scroll_amount *= self.scroll_acceleration
        
        # Determine direction
        if delta > 0:
            # Scroll up (shallower depths)
            self.scroll_up(scroll_amount)
        else:
            # Scroll down (deeper depths)
            self.scroll_down(scroll_amount)
    
    def scroll_up(self, amount: float):
        """Scroll up (toward shallower depths)."""
        if self.current_depth_range is None:
            return
        
        new_from_depth = max(self.min_depth, self.current_depth_range.from_depth - amount)
        new_to_depth = new_from_depth + self.viewport_height
        
        # Ensure we don't go past the top
        if new_to_depth > self.max_depth:
            new_to_depth = self.max_depth
            new_from_depth = new_to_depth - self.viewport_height
        
        self.set_viewport_range(new_from_depth, new_to_depth)
    
    def scroll_down(self, amount: float):
        """Scroll down (toward deeper depths)."""
        if self.current_depth_range is None:
            return
        
        new_from_depth = min(self.max_depth - self.viewport_height,
                            self.current_depth_range.from_depth + amount)
        new_to_depth = new_from_depth + self.viewport_height
        
        self.set_viewport_range(new_from_depth, new_to_depth)
    
    def set_viewport_range(self, from_depth: float, to_depth: float):
        """Set the visible depth range."""
        # Clamp to valid range
        from_depth = max(self.min_depth, min(from_depth, self.max_depth - self.viewport_height))
        to_depth = min(self.max_depth, max(to_depth, self.min_depth + self.viewport_height))
        
        # Ensure valid range
        if to_depth - from_depth < 0.001:
            return
        
        self.current_depth_range = DepthRange(from_depth, to_depth)
        self._update_scroll_position()
        
        # Emit signals
        self.depthRangeChanged.emit(self.current_depth_range)
    
    def set_scroll_position(self, position: float):
        """
        Set scroll position (0 = top, 1 = bottom).
        
        Args:
            position: Scroll position from 0.0 to 1.0
        """
        position = max(0.0, min(1.0, position))
        self.scroll_position = position
        
        # Calculate depth range from scroll position
        total_depth = self.max_depth - self.min_depth
        scrollable_depth = total_depth - self.viewport_height
        
        if scrollable_depth <= 0:
            from_depth = self.min_depth
        else:
            from_depth = self.min_depth + (scrollable_depth * position)
        
        to_depth = from_depth + self.viewport_height
        
        self.set_viewport_range(from_depth, to_depth)
        self.scrollPositionChanged.emit(position)
    
    def _update_scroll_position(self):
        """Update scroll position based on current depth range."""
        if self.current_depth_range is None:
            return
        
        total_depth = self.max_depth - self.min_depth
        scrollable_depth = total_depth - self.viewport_height
        
        if scrollable_depth <= 0:
            self.scroll_position = 0.0
        else:
            self.scroll_position = (self.current_depth_range.from_depth - self.min_depth) / scrollable_depth
            self.scroll_position = max(0.0, min(1.0, self.scroll_position))
    
    def get_scrollbar_values(self) -> Tuple[float, float, float, float]:
        """
        Get values for scrollbar.
        
        Returns:
            Tuple of (minimum, maximum, page_step, value)
            Suitable for QScrollBar.setRange() and .setValue()
        """
        total_depth = self.max_depth - self.min_depth
        
        # Convert to integer values for scrollbar (0-1000 range)
        scale = 1000.0
        if total_depth <= 0:
            return 0.0, scale, scale, 0.0
        
        min_val = 0.0
        max_val = scale
        page_step = (self.viewport_height / total_depth) * scale
        value = self.scroll_position * scale
        
        return min_val, max_val, page_step, value
    
    def scroll_to_depth(self, depth: float):
        """Scroll to center the viewport on a specific depth."""
        from_depth = depth - (self.viewport_height / 2)
        from_depth = max(self.min_depth, min(from_depth, self.max_depth - self.viewport_height))
        
        self.set_viewport_range(from_depth, from_depth + self.viewport_height)