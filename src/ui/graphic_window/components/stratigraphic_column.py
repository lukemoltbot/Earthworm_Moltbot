"""
StratigraphicColumn component - displays lithology intervals as colored rectangles.
Follows the blueprint pattern: uses shared DepthStateManager and DepthCoordinateSystem.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QRect
from typing import Optional, List
from src.core.graphic_models import HoleDataProvider, LithologyInterval
from src.ui.graphic_window.state import DepthStateManager, DepthRange, DepthCoordinateSystem


class StratigraphicColumn(QWidget):
    """
    Left panel: Colored column showing lithology intervals.
    
    CRITICAL: Uses SHARED DepthCoordinateSystem to ensure alignment.
    All rectangles positioned using depth_to_screen_y().
    
    Pattern:
    1. Takes shared state manager and coordinate system in __init__
    2. Subscribes to ALL state change signals
    3. Updates coordinate system when viewport changes
    4. Uses coordinate system for all positioning
    5. Updates central state on user interaction (click)
    """
    
    def __init__(self, data_provider: HoleDataProvider,
                 depth_state_manager: DepthStateManager,
                 depth_coord_system: DepthCoordinateSystem):
        super().__init__()
        
        self.data_provider = data_provider
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMinimumWidth(120)
        self.setStyleSheet("background-color: white;")
        
        # Cache lithology data
        self.lithology_intervals: List[LithologyInterval] = (
            self.data_provider.get_lithology_intervals()
        )
        
        # Subscribe to state changes (CRITICAL!)
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        self.state.zoomLevelChanged.connect(self.on_zoom_changed)
        
        self.selected_range: Optional[DepthRange] = None
        self.cursor_depth: Optional[float] = None
    
    def on_viewport_changed(self, depth_range: DepthRange):
        """Viewport changed - update coordinates and repaint."""
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()  # Triggers paintEvent()
    
    def on_cursor_changed(self, depth: float):
        """Cursor changed - repaint to show new cursor line."""
        self.cursor_depth = depth
        self.update()
    
    def on_selection_changed(self, depth_range: Optional[DepthRange]):
        """Selection changed - repaint to show selection highlight."""
        self.selected_range = depth_range
        self.update()
    
    def on_zoom_changed(self, zoom_level: float):
        """Zoom changed - update coordinate system and repaint."""
        # Note: DepthCoordinateSystem may need zoom support
        # For now, just repaint
        self.update()
    
    def paintEvent(self, event):
        """Render the stratigraphic column."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Get visible depth range from coordinate system
        min_depth, max_depth = self.coords.min_depth, self.coords.max_depth
        
        # Draw each lithology interval
        for interval in self.lithology_intervals:
            # Skip if outside viewport
            if interval.to_depth < min_depth or interval.from_depth > max_depth:
                continue
            
            # Convert depths to screen coordinates using SHARED system
            screen_y1 = self.coords.depth_to_screen_y(interval.from_depth)
            screen_y2 = self.coords.depth_to_screen_y(interval.to_depth)
            
            # Clamp to visible area
            screen_y1 = max(screen_y1, 0)
            screen_y2 = min(screen_y2, self.height())
            
            height = screen_y2 - screen_y1
            if height <= 0:
                continue
            
            # Draw rectangle
            rect = QRect(10, int(screen_y1), self.width() - 20, int(height))
            color = QColor(*interval.color)
            painter.fillRect(rect, QBrush(color))
            
            # Draw border
            painter.drawRect(rect)
        
        # Draw selection highlight
        if self.selected_range:
            self.draw_selection(painter)
        
        # Draw cursor line
        if self.cursor_depth is not None:
            self.draw_cursor(painter)
        
        # Draw depth scale on left edge
        self.draw_depth_scale(painter)
    
    def draw_selection(self, painter: QPainter):
        """Draw highlight around selected interval."""
        if self.selected_range is None:
            return
        
        screen_y1 = self.coords.depth_to_screen_y(self.selected_range.from_depth)
        screen_y2 = self.coords.depth_to_screen_y(self.selected_range.to_depth)
        
        rect = QRect(10, int(screen_y1), self.width() - 20, 
                    int(screen_y2 - screen_y1))
        
        painter.setPen(QPen(QColor(0, 0, 255), 3))
        painter.drawRect(rect)
    
    def draw_cursor(self, painter: QPainter):
        """Draw horizontal line at cursor depth."""
        if self.cursor_depth is None:
            return
        
        screen_y = self.coords.depth_to_screen_y(self.cursor_depth)
        
        painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, int(screen_y), self.width(), int(screen_y))
    
    def draw_depth_scale(self, painter: QPainter):
        """Draw depth numbers on left edge."""
        min_depth, max_depth = self.coords.min_depth, self.coords.max_depth
        
        # Draw every 1 meter
        step = 1.0
        depth = int(min_depth) + (1 if int(min_depth) < min_depth else 0)
        
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 8))
        
        while depth <= max_depth:
            screen_y = self.coords.depth_to_screen_y(depth)
            if 0 <= screen_y <= self.height():
                painter.drawText(5, int(screen_y), f"{depth:.0f}")
            depth += step
    
    def mousePressEvent(self, event):
        """Handle click - update central state."""
        screen_y = event.y()
        
        # Convert click to depth using SHARED coordinate system
        depth = self.coords.screen_y_to_depth(screen_y)
        
        # Find lithology interval at this depth
        for interval in self.lithology_intervals:
            if interval.contains_depth(depth):
                # UPDATE CENTRAL STATE (not local data!)
                self.state.set_selection_range(interval.from_depth, interval.to_depth)
                self.state.set_cursor_depth(depth)
                return
    
    def wheelEvent(self, event):
        """Handle scroll wheel - scroll viewport."""
        scroll_delta = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.state.scroll_viewport(scroll_delta)