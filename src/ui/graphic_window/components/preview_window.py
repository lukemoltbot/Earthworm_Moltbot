"""
PreviewWindow component - miniature overview of entire hole.
Allows quick navigation by clicking.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from PyQt6.QtCore import Qt, QRect
from typing import Optional
from src.core.graphic_models import HoleDataProvider
from src.ui.graphic_window.state import DepthStateManager, DepthRange, DepthCoordinateSystem


class PreviewWindow(QWidget):
    """
    Left panel: Miniature overview of entire hole.
    
    Shows:
    - Entire hole depth range (from min to max depth)
    - Current viewport range (highlighted rectangle)
    - Allows clicking to navigate (center viewport on clicked depth)
    """
    
    def __init__(self, data_provider: HoleDataProvider,
                 depth_state_manager: DepthStateManager,
                 depth_coord_system: DepthCoordinateSystem):
        super().__init__()
        
        self.data_provider = data_provider
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMaximumWidth(150)
        self.setMinimumWidth(80)
        self.setStyleSheet("background-color: white;")
        
        # Get hole depth range
        self.hole_min_depth, self.hole_max_depth = self.data_provider.get_depth_range()
        
        # Create a separate coordinate system for preview (full hole range)
        self.preview_coords = DepthCoordinateSystem(
            canvas_height=self.height(),
            canvas_width=self.width(),
            padding_top=10,
            padding_bottom=10,
            padding_left=10,
            padding_right=10
        )
        self.preview_coords.set_depth_range(self.hole_min_depth, self.hole_max_depth)
        
        # Subscribe to state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        
        self.current_viewport_range: Optional[DepthRange] = None
        self.selected_range: Optional[DepthRange] = None
    
    def resizeEvent(self, event):
        """Update preview coordinate system when widget resizes."""
        super().resizeEvent(event)
        self.preview_coords.canvas_height = self.height()
        self.preview_coords.canvas_width = self.width()
        self.update()
    
    def on_viewport_changed(self, depth_range: DepthRange):
        """Viewport changed - update and repaint."""
        self.current_viewport_range = depth_range
        self.update()
    
    def on_selection_changed(self, depth_range: Optional[DepthRange]):
        """Selection changed - update and repaint."""
        self.selected_range = depth_range
        self.update()
    
    def paintEvent(self, event):
        """Render the preview window."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Draw hole outline
        left, top, right, bottom = self.preview_coords.get_usable_canvas_area()
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(int(left), int(top), int(right - left), int(bottom - top))
        
        # Draw lithology intervals (simplified)
        intervals = self.data_provider.get_lithology_intervals()
        for interval in intervals:
            # Convert to preview coordinates
            screen_y1 = self.preview_coords.depth_to_screen_y(interval.from_depth)
            screen_y2 = self.preview_coords.depth_to_screen_y(interval.to_depth)
            
            height = screen_y2 - screen_y1
            if height <= 0:
                continue
            
            # Draw simplified rectangle (thin)
            color = QColor(*interval.color)
            painter.fillRect(int(left), int(screen_y1), int(right - left), int(height), color)
        
        # Draw current viewport range highlight
        if self.current_viewport_range:
            screen_y1 = self.preview_coords.depth_to_screen_y(
                self.current_viewport_range.from_depth
            )
            screen_y2 = self.preview_coords.depth_to_screen_y(
                self.current_viewport_range.to_depth
            )
            
            # Draw highlight rectangle
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.drawRect(int(left), int(screen_y1), int(right - left), int(screen_y2 - screen_y1))
        
        # Draw selection highlight
        if self.selected_range:
            screen_y1 = self.preview_coords.depth_to_screen_y(self.selected_range.from_depth)
            screen_y2 = self.preview_coords.depth_to_screen_y(self.selected_range.to_depth)
            
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawRect(int(left), int(screen_y1), int(right - left), int(screen_y2 - screen_y1))
    
    def mousePressEvent(self, event):
        """Handle click - center viewport on clicked depth."""
        screen_y = event.y()
        
        # Convert click to depth using preview coordinate system
        depth = self.preview_coords.screen_y_to_depth(screen_y)
        
        # Center viewport on this depth
        self.state.center_on_depth(depth)