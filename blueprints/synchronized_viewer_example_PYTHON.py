# ============================================================================
# SYNCHRONIZED DEPTH VIEWER - PYTHON/PyQt6 WORKING EXAMPLE
# This demonstrates the exact pattern you need for Earthworm
# ============================================================================

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QApplication
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt6.QtCore import Qt, QObject, pyqtSignal
from dataclasses import dataclass
from typing import List, Optional, Tuple
import sys


# ============================================================================
# 1. CORE DATA STRUCTURES
# ============================================================================

@dataclass
class DepthRange:
    """Immutable depth range"""
    from_depth: float
    to_depth: float
    
    @property
    def range_size(self) -> float:
        return self.to_depth - self.from_depth
    
    def contains(self, depth: float) -> bool:
        return self.from_depth <= depth <= self.to_depth


@dataclass
class LithologyInterval:
    """Single lithology layer"""
    from_depth: float
    to_depth: float
    code: str
    description: str
    color: Tuple[int, int, int] = (128, 128, 128)
    thickness: float = None
    
    def __post_init__(self):
        self.thickness = self.to_depth - self.from_depth
    
    def contains_depth(self, depth: float) -> bool:
        return self.from_depth <= depth <= self.to_depth


@dataclass
class LASPoint:
    """Single geophysical curve data point"""
    depth: float
    curves: dict  # {curve_name: value}
    
    def get_curve_value(self, curve_name: str, default: float = None) -> float:
        return self.curves.get(curve_name, default)
    
    def has_curve(self, curve_name: str) -> bool:
        return curve_name in self.curves


# ============================================================================
# 2. CENTRAL STATE MANAGER (THE MOST CRITICAL CLASS)
# ============================================================================

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
    selectionRangeChanged = pyqtSignal(DepthRange)
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
        """Set the depth range being viewed"""
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
        """Scroll viewport by depth delta"""
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
        """Set cursor depth for highlighting"""
        depth = max(self.min_depth, min(self.max_depth, depth))
        
        if depth != self._cursor_depth:
            self._cursor_depth = depth
            self.cursorDepthChanged.emit(depth)
    
    def get_cursor_depth(self) -> float:
        return self._cursor_depth
    
    # ========== SELECTION MANAGEMENT ==========
    
    def set_selection_range(self, from_depth: float, to_depth: float):
        """Set selected depth range"""
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
        """Clear selection"""
        if self._selection_range is not None:
            self._selection_range = None
            self.selectionRangeChanged.emit(None)


# ============================================================================
# 3. SHARED COORDINATE SYSTEM (CRITICAL FOR ALIGNMENT)
# ============================================================================

class DepthCoordinateSystem:
    """
    Transforms between model depth (meters) and screen coordinates (pixels).
    
    CRITICAL: This MUST be the ONLY coordinate system used.
    All components share the same instance.
    All coordinate transformations use these identical functions.
    This is what ensures perfect alignment!
    """
    
    def __init__(self, canvas_height: float, canvas_width: float,
                 padding_top: float = 20, padding_bottom: float = 20,
                 padding_left: float = 50, padding_right: float = 50):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom
        self.padding_left = padding_left
        self.padding_right = padding_right
        
        # Current depth range
        self.min_depth = 0.0
        self.max_depth = 100.0
        self.zoom_level = 1.0
    
    def set_depth_range(self, min_depth: float, max_depth: float):
        """Set the depth range being displayed"""
        self.min_depth = min_depth
        self.max_depth = max_depth
    
    # ===== THE MOST IMPORTANT FUNCTIONS =====
    # These MUST be used by ALL components for vertical positioning
    
    def depth_to_screen_y(self, depth: float) -> float:
        """
        Convert depth (meters) to screen Y coordinate (pixels).
        
        This is THE CRITICAL FUNCTION.
        Every component must use this for vertical positioning.
        """
        total_depth = self.max_depth - self.min_depth
        
        if total_depth <= 0:
            return self.padding_top
        
        # Calculate depth ratio
        depth_ratio = (depth - self.min_depth) / total_depth
        
        # Map to screen
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        screen_y = self.padding_top + (depth_ratio * usable_height)
        
        return screen_y
    
    def screen_y_to_depth(self, screen_y: float) -> float:
        """
        Inverse: Convert screen Y back to depth.
        Used when processing clicks.
        """
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        
        if usable_height <= 0:
            return self.min_depth
        
        # Calculate screen ratio
        screen_ratio = (screen_y - self.padding_top) / usable_height
        
        # Map back to depth
        total_depth = self.max_depth - self.min_depth
        depth = self.min_depth + (screen_ratio * total_depth)
        
        return depth
    
    def depth_thickness_to_pixel_height(self, thickness: float) -> float:
        """Convert depth thickness to pixel height"""
        total_depth = self.max_depth - self.min_depth
        
        if total_depth <= 0:
            return 0
        
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        pixel_height = (thickness / total_depth) * usable_height
        
        return pixel_height
    
    def get_pixels_per_meter(self) -> float:
        """Get scale: pixels per meter"""
        total_depth = self.max_depth - self.min_depth
        if total_depth <= 0:
            return 0
        
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        return usable_height / total_depth
    
    def get_usable_canvas_area(self) -> Tuple[float, float, float, float]:
        """Get (left, top, right, bottom) of usable drawing area"""
        left = self.padding_left
        top = self.padding_top
        right = self.canvas_width - self.padding_right
        bottom = self.canvas_height - self.padding_bottom
        return (left, top, right, bottom)


# ============================================================================
# 4. STRATIGRAPHIC COLUMN COMPONENT
# ============================================================================

class StratigraphicColumn(QWidget):
    """
    Left panel: Colored column showing lithology intervals.
    
    CRITICAL PATTERN:
    1. Takes shared state manager and coordinate system in __init__
    2. Subscribes to ALL state change signals
    3. Updates coordinate system when viewport changes
    4. Uses coordinate system for all positioning
    5. Updates central state on user interaction (click)
    """
    
    def __init__(self, lithology_data: List[LithologyInterval],
                 depth_state_manager: DepthStateManager,
                 depth_coord_system: DepthCoordinateSystem):
        super().__init__()
        
        self.lithology = lithology_data
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMinimumWidth(120)
        self.setStyleSheet("background-color: white;")
        
        # Subscribe to state changes (CRITICAL!)
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        
        self.selected_range: Optional[DepthRange] = None
        self.cursor_depth: Optional[float] = None
    
    def on_viewport_changed(self, depth_range: DepthRange):
        """Viewport changed - update coordinates and repaint"""
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()  # Triggers paintEvent()
    
    def on_cursor_changed(self, depth: float):
        """Cursor changed - repaint to show new cursor line"""
        self.cursor_depth = depth
        self.update()
    
    def on_selection_changed(self, depth_range: Optional[DepthRange]):
        """Selection changed - repaint to show selection highlight"""
        self.selected_range = depth_range
        self.update()
    
    def paintEvent(self, event):
        """Render the stratigraphic column"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        min_depth, max_depth = self.coords.min_depth, self.coords.max_depth
        
        # Draw lithology intervals
        for interval in self.lithology:
            # Skip if outside viewport
            if interval.to_depth < min_depth or interval.from_depth > max_depth:
                continue
            
            # Convert to screen coordinates using SHARED system
            screen_y1 = self.coords.depth_to_screen_y(interval.from_depth)
            screen_y2 = self.coords.depth_to_screen_y(interval.to_depth)
            
            height = screen_y2 - screen_y1
            if height <= 0:
                continue
            
            # Draw rectangle
            color = QColor(*interval.color)
            painter.fillRect(int(10), int(screen_y1), 
                           self.width() - 20, int(height), color)
            painter.drawRect(int(10), int(screen_y1), 
                           self.width() - 20, int(height))
        
        # Draw selection highlight
        if self.selected_range:
            screen_y1 = self.coords.depth_to_screen_y(self.selected_range.from_depth)
            screen_y2 = self.coords.depth_to_screen_y(self.selected_range.to_depth)
            
            painter.setPen(QPen(QColor(0, 0, 255), 3))
            painter.drawRect(int(10), int(screen_y1), 
                           self.width() - 20, int(screen_y2 - screen_y1))
        
        # Draw cursor line
        if self.cursor_depth is not None:
            screen_y = self.coords.depth_to_screen_y(self.cursor_depth)
            painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
            painter.drawLine(0, int(screen_y), self.width(), int(screen_y))
    
    def mousePressEvent(self, event):
        """Handle click - update central state"""
        screen_y = event.y()
        
        # Convert click to depth using SHARED coordinate system
        depth = self.coords.screen_y_to_depth(screen_y)
        
        # Find interval at this depth
        for interval in self.lithology:
            if interval.contains_depth(depth):
                # UPDATE CENTRAL STATE (not local data!)
                self.state.set_selection_range(interval.from_depth, interval.to_depth)
                self.state.set_cursor_depth(depth)
                return
    
    def wheelEvent(self, event):
        """Handle scroll"""
        scroll_delta = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.state.scroll_viewport(scroll_delta)


# ============================================================================
# 5. LAS CURVES COMPONENT
# ============================================================================

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
    
    def __init__(self, las_data: List[LASPoint],
                 depth_state_manager: DepthStateManager,
                 depth_coord_system: DepthCoordinateSystem):
        super().__init__()
        
        self.las_points = las_data
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        # Curve display settings
        self.displayed_curves = {
            'gamma': {'color': QColor(255, 0, 0), 'min': 0, 'max': 200},
            'density': {'color': QColor(0, 0, 255), 'min': 1.5, 'max': 2.5},
        }
        
        # Subscribe to state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        
        self.selected_range: Optional[DepthRange] = None
        self.cursor_depth: Optional[float] = None
    
    def on_viewport_changed(self, depth_range: DepthRange):
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()
    
    def on_cursor_changed(self, depth: float):
        self.cursor_depth = depth
        self.update()
    
    def on_selection_changed(self, depth_range: Optional[DepthRange]):
        self.selected_range = depth_range
        self.update()
    
    def paintEvent(self, event):
        """Render LAS curves"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        min_depth, max_depth = self.coords.min_depth, self.coords.max_depth
        
        # Filter visible points
        visible_points = [p for p in self.las_points 
                         if min_depth <= p.depth <= max_depth]
        
        # Draw each curve
        for curve_name, curve_config in self.displayed_curves.items():
            self.draw_curve(painter, visible_points, curve_name, curve_config)
        
        # Draw selection box
        if self.selected_range:
            screen_y1 = self.coords.depth_to_screen_y(self.selected_range.from_depth)
            screen_y2 = self.coords.depth_to_screen_y(self.selected_range.to_depth)
            
            left, top, right, bottom = self.coords.get_usable_canvas_area()
            
            painter.setPen(QPen(QColor(0, 0, 255), 2))
            painter.drawRect(int(left), int(screen_y1), 
                           int(right - left), int(screen_y2 - screen_y1))
        
        # Draw cursor line
        if self.cursor_depth is not None:
            screen_y = self.coords.depth_to_screen_y(self.cursor_depth)
            left, top, right, bottom = self.coords.get_usable_canvas_area()
            
            painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
            painter.drawLine(int(left), int(screen_y), int(right), int(screen_y))
    
    def draw_curve(self, painter: QPainter, points: List[LASPoint],
                   curve_name: str, config: dict):
        """Draw a single curve line"""
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
            
            # Normalize to 0-1
            if max_value <= min_value:
                value_ratio = 0.5
            else:
                value_ratio = (value - min_value) / (max_value - min_value)
                value_ratio = max(0, min(1, value_ratio))
            
            screen_x = left + (value_ratio * usable_width)
            
            # Draw line
            if prev_x is not None:
                painter.drawLine(int(prev_x), int(prev_y), int(screen_x), int(screen_y))
            
            prev_x = screen_x
            prev_y = screen_y
    
    def wheelEvent(self, event):
        """Handle scroll"""
        scroll_delta = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.state.scroll_viewport(scroll_delta)


# ============================================================================
# 6. EXAMPLE USAGE - PUTTING IT ALL TOGETHER
# ============================================================================

def create_example_data() -> Tuple[List[LithologyInterval], List[LASPoint]]:
    """Create sample data for demonstration"""
    
    # Sample lithology
    lithology = [
        LithologyInterval(87.0, 87.5, 'SAND', 'Fine Sand', (255, 215, 0)),
        LithologyInterval(87.5, 88.0, 'COAL', 'Coal Seam', (0, 0, 0)),
        LithologyInterval(88.0, 88.5, 'SHALE', 'Shale', (169, 169, 169)),
        LithologyInterval(88.5, 89.0, 'SAND', 'Fine Sand', (255, 215, 0)),
        LithologyInterval(89.0, 90.0, 'COAL', 'Coal Seam', (0, 0, 0)),
        LithologyInterval(90.0, 91.0, 'MUDSTONE', 'Mudstone', (128, 128, 128)),
        LithologyInterval(91.0, 92.0, 'SILT', 'Silt', (210, 180, 140)),
        LithologyInterval(92.0, 93.0, 'COAL', 'Coal Seam', (0, 0, 0)),
        LithologyInterval(93.0, 94.0, 'SHALE', 'Shale', (169, 169, 169)),
        LithologyInterval(94.0, 95.0, 'SAND', 'Fine Sand', (255, 215, 0)),
    ]
    
    # Sample LAS curves (Gamma Ray and Density)
    las_points = []
    for depth in [round(d * 0.1, 1) for d in range(870, 950)]:
        point = LASPoint(
            depth=depth,
            curves={
                'gamma': 50 + (depth - 87) * 2,  # Increasing gamma
                'density': 1.9 + (depth - 87) * 0.01,  # Increasing density
            }
        )
        las_points.append(point)
    
    return lithology, las_points


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Create sample data
    lithology_data, las_data = create_example_data()
    
    # Create shared state managers (THESE ARE SHARED BY ALL COMPONENTS!)
    depth_state = DepthStateManager(87, 95)
    depth_coords = DepthCoordinateSystem(600, 1000)
    
    # Create components (pass shared managers to each)
    strat_col = StratigraphicColumn(lithology_data, depth_state, depth_coords)
    las_curves = LASCurvesDisplay(las_data, depth_state, depth_coords)
    
    # Create simple window to show both
    window = QWidget()
    window.setWindowTitle("Synchronized Depth Viewer - Python/PyQt6 Example")
    window.setGeometry(100, 100, 1200, 600)
    
    layout = QHBoxLayout(window)
    layout.addWidget(strat_col)
    layout.addWidget(las_curves)
    
    # Initialize viewport
    depth_state.set_viewport_range(87, 95)
    
    window.show()
    sys.exit(app.exec())


# ============================================================================
# KEY PATTERNS TO UNDERSTAND
# ============================================================================

"""
PATTERN 1: Component Initialization
------------------------------------
class MyComponent(QWidget):
    def __init__(self, depth_state_manager, depth_coord_system):
        self.state = depth_state_manager  # SHARED
        self.coords = depth_coord_system  # SHARED
        
        # Subscribe to ALL signals
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)


PATTERN 2: Responding to State Changes
---------------------------------------
def on_viewport_changed(self, depth_range: DepthRange):
    # Update coordinate system
    self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
    
    # Trigger repaint
    self.update()  # Calls paintEvent()


PATTERN 3: User Interaction Updates State
------------------------------------------
def mousePressEvent(self, event):
    # Convert screen coordinate to depth using SHARED coordinate system
    depth = self.coords.screen_y_to_depth(event.y())
    
    # UPDATE CENTRAL STATE (not local variables!)
    self.state.set_cursor_depth(depth)
    self.state.set_selection_range(from_depth, to_depth)
    # Other components automatically receive signals and update!


PATTERN 4: Drawing with Coordinate System
------------------------------------------
def paintEvent(self, event):
    painter = QPainter(self)
    
    for item in self.items:
        # ALWAYS use shared coordinate system for positioning
        screen_y = self.coords.depth_to_screen_y(item.depth)
        height = self.coords.depth_thickness_to_pixel_height(item.thickness)
        
        # Draw using calculated positions
        painter.drawRect(x, screen_y, width, height)


THE MAGIC
---------
When you click on the strat column:
1. StratigraphicColumn.mousePressEvent() is called
2. It calculates depth from click position (using shared coords)
3. It calls state.set_cursor_depth(depth)
4. DepthStateManager emits cursorDepthChanged signal
5. BOTH StratigraphicColumn AND LASCurvesDisplay receive the signal
6. Both call self.update() → paintEvent() → both repaint
7. Both use SAME coordinate system for positioning
8. Result: Perfect alignment, zero misalignment!
"""
