"""
LASCurvesDisplay component - visualizes LAS curve data.
Follows the blueprint pattern: uses shared DepthStateManager and DepthCoordinateSystem.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QRect
from typing import Optional, List, Dict, Any
from src.core.graphic_models import HoleDataProvider, LASPoint
from src.ui.graphic_window.state import DepthStateManager, DepthRange, DepthCoordinateSystem


class LASCurvesDisplay(QWidget):
    """
    Center panel: LAS curve visualization.
    
    SAME PATTERN as StratigraphicColumn:
    - Shared state manager
    - Shared coordinate system
    - Subscribe to signals
    - Use coordinate system for positioning
    - Update state on interaction
    """
    
    def __init__(self, data_provider: HoleDataProvider,
                 depth_state_manager: DepthStateManager,
                 depth_coord_system: DepthCoordinateSystem):
        super().__init__()
        
        self.data_provider = data_provider
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        # Curve display settings
        self.displayed_curves = {
            'gamma': {'color': QColor(255, 0, 0), 'min': 0, 'max': 200},
            'density': {'color': QColor(0, 0, 255), 'min': 1.5, 'max': 2.5},
            'caliper': {'color': QColor(0, 128, 0), 'min': 6, 'max': 16},
            'resistivity': {'color': QColor(128, 0, 128), 'min': 0, 'max': 100},
        }
        
        # Subscribe to state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        self.state.zoomLevelChanged.connect(self.on_zoom_changed)
        
        self.selected_range: Optional[DepthRange] = None
        self.cursor_depth: Optional[float] = None
    
    def on_viewport_changed(self, depth_range: DepthRange):
        """Viewport changed - update coordinates and repaint."""
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()
    
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
        """Render LAS curves."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        # Get visible depth range
        min_depth, max_depth = self.coords.min_depth, self.coords.max_depth
        
        # Get LAS points for visible depth range
        # Note: In production, we'd want to filter points efficiently
        # For now, get all points and filter
        all_points = self.data_provider.get_las_points()
        visible_points = [p for p in all_points 
                         if min_depth <= p.depth <= max_depth]
        
        # Sort by depth for drawing
        visible_points.sort(key=lambda p: p.depth)
        
        # Draw each curve
        for curve_name, curve_config in self.displayed_curves.items():
            self.draw_curve(painter, visible_points, curve_name, curve_config)
        
        # Draw selection box
        if self.selected_range:
            self.draw_selection(painter)
        
        # Draw cursor line
        if self.cursor_depth is not None:
            self.draw_cursor(painter)
        
        # Draw value scales (axes)
        self.draw_value_scales(painter)
    
    def draw_curve(self, painter: QPainter, points: List[LASPoint],
                   curve_name: str, config: Dict[str, Any]):
        """Draw a single curve line."""
        if len(points) < 2:
            return
        
        color = config['color']
        min_value = config['min']
        max_value = config['max']
        
        painter.setPen(QPen(color, 2))
        
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        usable_width = right - left
        
        # Draw curve segments
        prev_x = None
        prev_y = None
        
        for point in points:
            if not point.has_curve(curve_name):
                continue
            
            # Convert depth to Y using SHARED coordinate system
            screen_y = self.coords.depth_to_screen_y(point.depth)
            
            # Convert value to X
            value = point.get_curve_value(curve_name)
            if value is None:
                continue
            
            # Normalize to 0-1 within min/max range
            if max_value <= min_value:
                value_ratio = 0.5
            else:
                value_ratio = (value - min_value) / (max_value - min_value)
                value_ratio = max(0.0, min(1.0, value_ratio))
            
            # Map to screen X (left to right)
            screen_x = left + (value_ratio * usable_width)
            
            # Draw line segment
            if prev_x is not None:
                painter.drawLine(int(prev_x), int(prev_y), 
                               int(screen_x), int(screen_y))
            
            prev_x = screen_x
            prev_y = screen_y
    
    def draw_selection(self, painter: QPainter):
        """Draw highlight around selected interval."""
        if self.selected_range is None:
            return
        
        screen_y1 = self.coords.depth_to_screen_y(self.selected_range.from_depth)
        screen_y2 = self.coords.depth_to_screen_y(self.selected_range.to_depth)
        
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.drawRect(int(left), int(screen_y1), 
                       int(right - left), int(screen_y2 - screen_y1))
    
    def draw_cursor(self, painter: QPainter):
        """Draw horizontal line at cursor depth."""
        if self.cursor_depth is None:
            return
        
        screen_y = self.coords.depth_to_screen_y(self.cursor_depth)
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        
        painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(left), int(screen_y), int(right), int(screen_y))
    
    def draw_value_scales(self, painter: QPainter):
        """Draw value scales (axes) for each curve."""
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        usable_width = right - left
        
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setFont(QFont("Arial", 8))
        
        # Draw each curve's scale at the bottom
        curve_count = len(self.displayed_curves)
        if curve_count == 0:
            return
        
        section_width = usable_width / curve_count
        for i, (curve_name, curve_config) in enumerate(self.displayed_curves.items()):
            section_left = left + (i * section_width)
            section_center = section_left + (section_width / 2)
            
            # Draw curve name
            painter.drawText(int(section_center - 20), int(bottom + 20), 
                           f"{curve_name}")
            
            # Draw min/max values
            min_val = curve_config['min']
            max_val = curve_config['max']
            
            # Left side (min)
            painter.drawText(int(section_left + 5), int(bottom + 35), 
                           f"{min_val:.1f}")
            # Right side (max)
            painter.drawText(int(section_left + section_width - 25), 
                           int(bottom + 35), f"{max_val:.1f}")
    
    def wheelEvent(self, event):
        """Handle scroll wheel - scroll viewport."""
        scroll_delta = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.state.scroll_viewport(scroll_delta)