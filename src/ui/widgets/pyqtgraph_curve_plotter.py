"""
PyQtGraphCurvePlotter - A PyQtGraph-based curve plotter widget for Earthworm Moltbot.
Provides improved performance and features over the QGraphicsScene-based CurvePlotter.
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton
from PyQt6.QtGui import QColor, QPen
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
import pyqtgraph as pg

class PyQtGraphCurvePlotter(QWidget):
    """A PyQtGraph-based curve plotter widget with improved performance."""
    
    # Signal emitted when user clicks on the plot (for synchronization with table)
    pointClicked = pyqtSignal(float)  # depth value
    
    # Signal emitted when view range changes (for synchronization with overview)
    viewRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.data = None
        self.depth_column = 'DEPT'  # Assuming 'DEPT' is the standardized depth column name
        self.curve_configs = []  # List of dictionaries for curve configurations
        self.depth_scale = 10  # Pixels per depth unit (should match StratigraphicColumn)
        self.plot_width = 110  # Width of the plot area
        
        # Current view state
        self.current_zoom_factor = 1.0
        self.min_depth = 0.0
        self.max_depth = 100.0
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the PyQtGraph plot and controls."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create PyQtGraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Depth', units='m')
        self.plot_widget.setLabel('bottom', 'Value')
        
        # Invert Y-axis so 0 (surface) is at top, increasing depth downward
        self.plot_widget.invertY(True)
        
        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.setMenuEnabled(False)  # Disable right-click menu
        
        # Connect mouse click signal
        self.plot_widget.scene().sigMouseClicked.connect(self.on_plot_clicked)
        
        # Connect view range change signal
        self.plot_widget.sigRangeChanged.connect(self.on_view_range_changed)
        
        layout.addWidget(self.plot_widget)
        
        # Add X-axis controls for each curve
        self.axis_controls_widget = QWidget()
        self.axis_controls_layout = QVBoxLayout(self.axis_controls_widget)
        self.axis_controls_layout.setContentsMargins(5, 5, 5, 5)
        self.axis_controls_layout.setSpacing(2)
        
        layout.addWidget(self.axis_controls_widget)
        
    def set_curve_configs(self, configs):
        """Set curve configurations and redraw."""
        self.curve_configs = configs
        self.draw_curves()
        self.update_axis_controls()
        
    def set_data(self, dataframe):
        """Set data and redraw curves."""
        self.data = dataframe
        self.draw_curves()
        
    def draw_curves(self):
        """Draw all configured curves using PyQtGraph."""
        # Clear the plot
        self.plot_widget.clear()
        
        if self.data is None or self.data.empty or not self.curve_configs:
            return
        
        # Extract depth data
        if self.depth_column not in self.data.columns:
            return
            
        depth_data = self.data[self.depth_column].values
        
        # Draw each curve
        for config in self.curve_configs:
            curve_name = config['name']
            min_value = config['min']
            max_value = config['max']
            color = config['color']
            thickness = config.get('thickness', 1.5)
            inverted = config.get('inverted', False)
            
            if curve_name not in self.data.columns:
                continue
                
            # Extract curve data
            curve_data = self.data[curve_name].values
            
            # Filter out NaN values
            mask = ~np.isnan(curve_data)
            if not np.any(mask):
                continue
                
            valid_depths = depth_data[mask]
            valid_values = curve_data[mask]
            
            # Apply inversion if specified
            if inverted:
                # For inverted curves, we need to map values differently
                # In PyQtGraph, we can just plot the data as-is and handle axis inversion
                pass
            
            # Create pen for the curve
            pen = pg.mkPen(color=color, width=thickness)
            
            # Plot the curve
            curve = self.plot_widget.plot(valid_values, valid_depths, pen=pen, name=curve_name)
            
            # Store reference for potential updates
            curve.config = config
            
        # Set axis ranges
        self.update_axis_ranges()
        
    def update_axis_ranges(self):
        """Update plot axis ranges based on curve configurations."""
        if not self.curve_configs:
            return
            
        # Determine X-axis range from all curves
        x_min = float('inf')
        x_max = float('-inf')
        
        for config in self.curve_configs:
            x_min = min(x_min, config['min'])
            x_max = max(x_max, config['max'])
            
        # Set X-axis range with some padding
        x_padding = (x_max - x_min) * 0.05
        self.plot_widget.setXRange(x_min - x_padding, x_max + x_padding)
        
        # Set Y-axis range based on data
        if self.data is not None and not self.data.empty:
            y_min = self.data[self.depth_column].min()
            y_max = self.data[self.depth_column].max()
            self.plot_widget.setYRange(y_min, y_max)
            
    def update_axis_controls(self):
        """Update the X-axis controls widget with current curve configurations."""
        # Clear existing controls
        while self.axis_controls_layout.count():
            item = self.axis_controls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not self.curve_configs:
            return
            
        # Sort curves for consistent display
        sorted_configs = sorted(self.curve_configs, key=lambda x: (
            0 if x['name'] == 'gamma' else
            1 if x['name'] == 'short_space_density' else
            2 if x['name'] == 'long_space_density' else
            3
        ))
        
        # Create controls for each curve
        for config in sorted_configs:
            curve_name = config['name']
            min_value = config['min']
            max_value = config['max']
            color = config['color']
            
            # Create control row
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            
            # Color indicator
            color_label = QLabel()
            color_label.setFixedSize(15, 15)
            color_label.setStyleSheet(f"background-color: {color}; border: 1px solid black;")
            row_layout.addWidget(color_label)
            
            # Curve name
            name_label = QLabel(curve_name)
            name_label.setFixedWidth(80)
            row_layout.addWidget(name_label)
            
            # Min value
            min_label = QLabel(f"{min_value:.0f}")
            min_label.setFixedWidth(40)
            row_layout.addWidget(min_label)
            
            # Separator
            row_layout.addWidget(QLabel("-"))
            
            # Max value
            max_label = QLabel(f"{max_value:.0f}")
            max_label.setFixedWidth(40)
            row_layout.addWidget(max_label)
            
            row_layout.addStretch()
            self.axis_controls_layout.addWidget(row_widget)
            
    def set_zoom_level(self, zoom_factor):
        """Set zoom level (1.0 = 100% = normal fit level)."""
        self.current_zoom_factor = zoom_factor
        
        if self.data is None or self.data.empty:
            return
            
        # Get current view range
        view_range = self.plot_widget.viewRange()
        current_y_range = view_range[1][1] - view_range[1][0]
        
        # Calculate new Y range based on zoom factor
        data_y_min = self.data[self.depth_column].min()
        data_y_max = self.data[self.depth_column].max()
        data_y_range = data_y_max - data_y_min
        
        if zoom_factor > 1.0:
            # Zoom in: show smaller range
            new_y_range = data_y_range / zoom_factor
            # Keep center at current view center
            current_center = (view_range[1][0] + view_range[1][1]) / 2
            new_y_min = current_center - new_y_range / 2
            new_y_max = current_center + new_y_range / 2
        else:
            # Zoom out: show full range
            new_y_min = data_y_min
            new_y_max = data_y_max
            
        # Apply new Y range
        self.plot_widget.setYRange(new_y_min, new_y_max)
        
    def set_depth_range(self, min_depth, max_depth):
        """Set the visible depth range."""
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.plot_widget.setYRange(min_depth, max_depth)
        
    def scroll_to_depth(self, depth):
        """Scroll the view to make the given depth visible."""
        if self.data is None or self.data.empty:
            return
            
        # Get current view range
        view_range = self.plot_widget.viewRange()
        current_y_min = view_range[1][0]
        current_y_max = view_range[1][1]
        current_height = current_y_max - current_y_min
        
        # Calculate new view range centered on target depth
        new_y_min = depth - current_height / 2
        new_y_max = depth + current_height / 2
        
        # Ensure we don't go beyond data bounds
        data_y_min = self.data[self.depth_column].min()
        data_y_max = self.data[self.depth_column].max()
        
        if new_y_min < data_y_min:
            new_y_min = data_y_min
            new_y_max = new_y_min + current_height
            
        if new_y_max > data_y_max:
            new_y_max = data_y_max
            new_y_min = new_y_max - current_height
            
        # Apply new range
        self.plot_widget.setYRange(new_y_min, new_y_max)
        
    def on_plot_clicked(self, event):
        """Handle mouse clicks on the plot."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Get mouse position in plot coordinates
            pos = event.scenePos()
            if self.plot_widget.plotItem.vb.mapSceneToView(pos):
                view_coords = self.plot_widget.plotItem.vb.mapSceneToView(pos)
                depth = view_coords.y()
                
                # Emit signal with depth value
                self.pointClicked.emit(depth)
                
    def on_view_range_changed(self):
        """Handle view range changes and emit signal for overview synchronization."""
        view_range = self.plot_widget.viewRange()
        y_min = view_range[1][0]
        y_max = view_range[1][1]
        self.viewRangeChanged.emit(y_min, y_max)
                
    def get_view_range(self):
        """Get the current visible depth range."""
        view_range = self.plot_widget.viewRange()
        return view_range[1][0], view_range[1][1]  # y_min, y_max
        
    def view_range_changed(self):
        """Signal handler for view range changes (for synchronization with overview)."""
        # This can be connected to external signals
        pass