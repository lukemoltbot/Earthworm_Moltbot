"""
PyQtGraphCurvePlotter - A PyQtGraph-based curve plotter widget for Earthworm Moltbot.
Provides improved performance and features over the QGraphicsScene-based CurvePlotter.
Supports dual-axis plotting for LAS comparative analysis.
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QToolTip
from PyQt6.QtGui import QColor, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QTimer
import pyqtgraph as pg

# Import ScrollPolicyManager for scroll control
from .scroll_policy_manager import ScrollPolicyManager

class PyQtGraphCurvePlotter(QWidget):
    """A PyQtGraph-based curve plotter widget with improved performance and dual-axis support."""
    
    # Signal emitted when user clicks on the plot (for synchronization with table)
    pointClicked = pyqtSignal(float)  # depth value
    
    # Signal emitted when view range changes (for synchronization with overview)
    viewRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth
    
    # Signal emitted when a boundary line is dragged (for updating table data)
    boundaryDragged = pyqtSignal(int, str, float)  # row_index, boundary_type, new_depth
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.data = None
        self.depth_column = 'DEPT'  # Assuming 'DEPT' is the standardized depth column name
        self.curve_configs = []  # List of dictionaries for curve configurations
        self.depth_scale = 10  # Pixels per depth unit (should match StratigraphicColumn)
        self.plot_width = 110  # Width of the plot area
        
        # Dual-axis configuration
        self.gamma_viewbox = None  # Secondary ViewBox for Gamma Ray
        self.gamma_axis = None  # Top axis for Gamma Ray
        self.gamma_curves = []  # List of Gamma Ray curves
        self.density_curves = []  # List of Density curves
        self.curve_items = {}  # Dictionary mapping curve_name -> curve item(s)
        
        # Curve type identification patterns
        self.gamma_patterns = ['gamma', 'gr', 'gamma_ray', 'gammaray']
        self.density_patterns = ['density', 'den', 'rhob', 'ss', 'ls', 'cd']
        
        # Lithology data for boundary lines
        self.lithology_data = None
        self.boundary_lines = {}  # Dict mapping (row_index, boundary_type) -> pg.InfiniteLine
        
        # Boundary line styling
        self.top_boundary_color = QColor(0, 128, 0)  # Green for top boundaries (From_Depth)
        self.bottom_boundary_color = QColor(128, 0, 0)  # Red for bottom boundaries (To_Depth)
        self.dragging_boundary_color = QColor(255, 165, 0)  # Orange for dragging
        self.boundary_width = 2
        self.dragging_width = 4
        
        # Snapping configuration
        self.snap_threshold = 0.5  # Depth units for snapping
        
        # Current dragging state
        self.dragging_line = None
        self.dragging_original_depth = None
        
        # Current view state
        self.current_zoom_factor = 1.0
        self.min_depth = 0.0
        self.max_depth = 100.0
        
        # Anomaly detection
        self.bit_size_mm = 150.0  # Default bit size in mm
        self.anomaly_regions = []  # List of pg.LinearRegionItem for anomaly highlighting
        self.anomaly_brush = (255, 0, 0, 50)  # Semi-transparent red for anomaly regions
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the PyQtGraph plot and controls with dual-axis support."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create PyQtGraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Depth', units='m')
        self.plot_widget.setLabel('bottom', 'Value')
        
        # Get the plot item for dual-axis configuration
        self.plot_item = self.plot_widget.plotItem
        
        # Initialize dual-axis system for Gamma Ray
        self.setup_dual_axes()
        
        # Invert Y-axis so 0 (surface) is at top, increasing depth downward
        self.plot_widget.invertY(True)
        
        # Enable mouse interaction - DISABLE HORIZONTAL SCROLLING FOR PHASE 1
        self.plot_widget.setMouseEnabled(x=False, y=True)
        self.plot_widget.setMenuEnabled(False)  # Disable right-click menu
        
        # Apply scroll policy manager for comprehensive scroll control
        ScrollPolicyManager.disable_horizontal_scrolling(self.plot_widget)
        ScrollPolicyManager.enable_vertical_only(self.plot_widget)
        
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
        
    def setup_dual_axes(self):
        """Setup dual X-axes for LAS curve plotting."""
        # Show and configure top axis for Gamma Ray
        self.plot_item.showAxis('top')
        self.gamma_axis = self.plot_item.getAxis('top')
        
        # Create secondary ViewBox for Gamma Ray curves
        self.gamma_viewbox = pg.ViewBox()
        self.plot_item.scene().addItem(self.gamma_viewbox)
        
        # Link top axis to Gamma Ray ViewBox
        self.gamma_axis.linkToView(self.gamma_viewbox)
        self.gamma_viewbox.setXLink(self.plot_item)  # Share X-axis transform
        # CRITICAL FIX: Add Y-axis linking for scrolling synchronization
        self.gamma_viewbox.setYLink(self.plot_item.vb)
        self.gamma_axis.setLabel('Gamma Ray', units='API', color='#8b008b')
        
        # Handle view synchronization
        def update_gamma_view():
            """Update Gamma Ray ViewBox geometry when main view changes."""
            if self.gamma_viewbox:
                self.gamma_viewbox.setGeometry(self.plot_item.vb.sceneBoundingRect())
                # Force Y-axis synchronization with main view
                self.gamma_viewbox.linkedViewChanged(self.plot_item.vb, self.gamma_viewbox.YAxis)
        
        def update_gamma_view_on_scroll():
            """Update Gamma Ray ViewBox during scrolling (not just resize)."""
            if self.gamma_viewbox:
                # Update geometry to match main view
                self.gamma_viewbox.setGeometry(self.plot_item.vb.sceneBoundingRect())
                # Ensure Y-axis is synchronized with main view range
                view_range = self.plot_item.vb.viewRange()
                if view_range and len(view_range) > 1:
                    y_min, y_max = view_range[1]
                    self.gamma_viewbox.setYRange(y_min, y_max, padding=0)
        
        # Connect resize signal
        self.plot_item.vb.sigResized.connect(update_gamma_view)
        # CRITICAL FIX: Connect to view range changes for scrolling
        self.plot_item.vb.sigRangeChanged.connect(update_gamma_view_on_scroll)
        
        # Store update function for later use
        self.update_gamma_view_func = update_gamma_view
        
        # Initial update
        update_gamma_view()
        
    def set_curve_configs(self, configs):
        """Set curve configurations and redraw."""
        self.curve_configs = configs
        self.draw_curves()
        self.update_axis_controls()
        
    def set_data(self, dataframe):
        """Set data and redraw curves."""
        self.data = dataframe
        self.draw_curves()
        self.on_data_updated()
        
    def draw_curves(self):
        """Draw all configured curves using PyQtGraph with dual-axis support."""
        # Remove existing curve items without clearing the entire plot
        # This preserves the dual-axis setup
        
        
        
        # Clear anomaly regions (they will be recreated after curves are drawn)
        self.clear_anomaly_highlights()
        
        # Track curves to remove
        items_to_remove = []
        
        # Find and remove previous curve items from main plot
        for item in self.plot_item.items[:]:  # Copy list to avoid modification during iteration
            if hasattr(item, 'config'):  # This is one of our curve items
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.plot_item.removeItem(item)
        
        # Clear gamma viewbox if it exists
        if self.gamma_viewbox:
            self.gamma_viewbox.clear()
        
        # Ensure dual axes are set up
        if not self.gamma_viewbox:
            self.setup_dual_axes()
        
        if self.data is None or self.data.empty or not self.curve_configs:
            return
        
        # Extract depth data
        if self.depth_column not in self.data.columns:
            return
            
        depth_data = self.data[self.depth_column].values
        
        # Separate curve configs into gamma and density curves
        gamma_configs = []
        density_configs = []
        
        for config in self.curve_configs:
            curve_name = config['name'].lower()
            
            # Check if this is a gamma curve
            is_gamma = any(pattern in curve_name for pattern in self.gamma_patterns)
            
            if is_gamma:
                gamma_configs.append(config)
            else:
                # Assume it's a density curve (or other curve that goes on main axis)
                density_configs.append(config)
        
        # Track curves for legend and visibility control
        self.gamma_curves = []
        self.density_curves = []
        self.curve_items = {}  # Dictionary mapping curve_name -> curve item(s)
        
        # Plot density curves on main plot (bottom axis)
        for config in density_configs:
            curve_name = config['name']
            color = config['color']
            thickness = config.get('thickness', 1.5)
            
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
            
            # Create pen for the curve
            pen = pg.mkPen(color=color, width=thickness)
            
            # Plot the curve on main plot
            curve = self.plot_widget.plot(valid_values, valid_depths, pen=pen, name=curve_name)
            
            # Store reference
            curve.config = config
            self.density_curves.append(curve)
            # Store in dictionary for visibility control
            self.curve_items[curve_name] = curve
        
        # Plot gamma curves on gamma viewbox (top axis)
        for config in gamma_configs:
            curve_name = config['name']
            color = config['color']
            thickness = config.get('thickness', 1.5)
            
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
            
            # Create pen for the curve
            pen = pg.mkPen(color=color, width=thickness)
            
            # Create PlotCurveItem for gamma viewbox with a name for the legend
            curve = pg.PlotCurveItem(valid_values, valid_depths, pen=pen, name=curve_name)
            
            # Add to gamma viewbox
            if self.gamma_viewbox:
                self.gamma_viewbox.addItem(curve)
            
            # Store reference
            curve.config = config
            self.gamma_curves.append(curve)
            # Store in dictionary for visibility control
            self.curve_items[curve_name] = curve
        
        # Add legend
        self.plot_item.addLegend()
        
        # Set axis ranges and labels
        self.update_axis_ranges()
        
    def update_axis_ranges(self):
        """Update plot axis ranges based on curve configurations for dual-axis system."""
        if not self.curve_configs:
            return
            
        # Separate curve configs into gamma and density
        gamma_configs = []
        density_configs = []
        
        for config in self.curve_configs:
            curve_name = config['name'].lower()
            is_gamma = any(pattern in curve_name for pattern in self.gamma_patterns)
            
            if is_gamma:
                gamma_configs.append(config)
            else:
                density_configs.append(config)
        
        # Set X-axis range for density curves (main plot, bottom axis)
        if density_configs:
            density_x_min = float('inf')
            density_x_max = float('-inf')
            
            for config in density_configs:
                density_x_min = min(density_x_min, config['min'])
                density_x_max = max(density_x_max, config['max'])
            
            # Default range for density curves if not specified: 0.0 to 4.0
            if density_x_min == float('inf'):
                density_x_min = 0.0
            if density_x_max == float('-inf'):
                density_x_max = 4.0
                
            # Set X-axis range with some padding
            x_padding = (density_x_max - density_x_min) * 0.05
            self.plot_widget.setXRange(density_x_min - x_padding, density_x_max + x_padding)
            
            # Update bottom axis label
            self.plot_widget.setLabel('bottom', 'Density', units='g/cc')
        
        # Set X-axis range for gamma curves (gamma viewbox, top axis)
        if gamma_configs and self.gamma_viewbox:
            gamma_x_min = float('inf')
            gamma_x_max = float('-inf')
            
            for config in gamma_configs:
                gamma_x_min = min(gamma_x_min, config['min'])
                gamma_x_max = max(gamma_x_max, config['max'])
            
            # Default range for gamma curves if not specified: 0 to 300
            if gamma_x_min == float('inf'):
                gamma_x_min = 0
            if gamma_x_max == float('-inf'):
                gamma_x_max = 300
                
            # Set gamma viewbox X-axis range
            self.gamma_viewbox.setXRange(gamma_x_min, gamma_x_max)
            
            # Update top axis label if gamma axis exists
            if self.gamma_axis:
                self.gamma_axis.setLabel('Gamma Ray', units='API', color='#8b008b')
        
        # Set Y-axis range based on data
        if self.data is not None and not self.data.empty:
            y_min = self.data[self.depth_column].min()
            y_max = self.data[self.depth_column].max()
            self.plot_widget.setYRange(y_min, y_max)
            
    def update_axis_controls(self):
        """Update the X-axis controls widget with current curve configurations for dual-axis."""
        # Clear existing controls
        while self.axis_controls_layout.count():
            item = self.axis_controls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not self.curve_configs:
            return
            
        # Separate curves into gamma and density for better organization
        gamma_configs = []
        density_configs = []
        
        for config in self.curve_configs:
            curve_name = config['name'].lower()
            is_gamma = any(pattern in curve_name for pattern in self.gamma_patterns)
            
            if is_gamma:
                gamma_configs.append(config)
            else:
                density_configs.append(config)
        
        # Add section header for Density curves (bottom axis)
        if density_configs:
            density_header = QLabel("<b>Density Curves (Bottom Axis)</b>")
            density_header.setStyleSheet("color: #333; padding: 2px;")
            self.axis_controls_layout.addWidget(density_header)
            
            # Sort density curves for consistent display
            sorted_density = sorted(density_configs, key=lambda x: x['name'])
            
            for config in sorted_density:
                self.add_curve_control_row(config, 'density')
        
        # Add section header for Gamma Ray curves (top axis)
        if gamma_configs:
            # Add separator
            separator = QLabel()
            separator.setFixedHeight(10)
            self.axis_controls_layout.addWidget(separator)
            
            gamma_header = QLabel("<b>Gamma Ray Curves (Top Axis)</b>")
            gamma_header.setStyleSheet("color: #8b008b; padding: 2px;")
            self.axis_controls_layout.addWidget(gamma_header)
            
            # Sort gamma curves for consistent display
            sorted_gamma = sorted(gamma_configs, key=lambda x: x['name'])
            
            for config in sorted_gamma:
                self.add_curve_control_row(config, 'gamma')
    
    def add_curve_control_row(self, config, curve_type='density'):
        """Add a single curve control row to the axis controls widget."""
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
        name_label.setFixedWidth(120)
        if curve_type == 'gamma':
            name_label.setStyleSheet("color: #8b008b;")
        row_layout.addWidget(name_label)
        
        # Min value
        min_label = QLabel(f"{min_value:.1f}")
        min_label.setFixedWidth(50)
        min_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        row_layout.addWidget(min_label)
        
        # Separator
        row_layout.addWidget(QLabel("-"))
        
        # Max value
        max_label = QLabel(f"{max_value:.1f}")
        max_label.setFixedWidth(50)
        max_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        row_layout.addWidget(max_label)
        
        # Axis indicator
        axis_label = QLabel("(Top)" if curve_type == 'gamma' else "(Bottom)")
        axis_label.setFixedWidth(50)
        axis_label.setStyleSheet("color: #666; font-size: 10px;")
        row_layout.addWidget(axis_label)
        
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
            print("WARNING: No data available for scrolling")
            return
            
        # Get current view range
        view_range = self.plot_widget.viewRange()
        current_y_min = view_range[1][0]
        current_y_max = view_range[1][1]
        current_height = current_y_max - current_y_min
        
        # Validate current_height to prevent division by zero or invalid ranges
        if current_height <= 0:
            # Use default height based on data range
            data_y_min = self.data[self.depth_column].min()
            data_y_max = self.data[self.depth_column].max()
            current_height = (data_y_max - data_y_min) * 0.1  # 10% of data range
            if current_height <= 0:
                current_height = 10.0  # Default fallback
            print(f"WARNING: Invalid current_height in scroll_to_depth, using: {current_height}")
        
        # Calculate new view range centered on target depth
        new_y_min = depth - current_height / 2
        new_y_max = depth + current_height / 2
        
        # Ensure we don't go beyond data bounds
        data_y_min = self.data[self.depth_column].min()
        data_y_max = self.data[self.depth_column].max()
        
        # Adjust if we're trying to view above or below data
        if new_y_min < data_y_min:
            offset = data_y_min - new_y_min
            new_y_min = data_y_min
            new_y_max = min(new_y_max + offset, data_y_max)
        elif new_y_max > data_y_max:
            offset = new_y_max - data_y_max
            new_y_max = data_y_max
            new_y_min = max(new_y_min - offset, data_y_min)
        
        # Ensure valid range (new_y_min must be less than new_y_max)
        if new_y_min >= new_y_max:
            # Fallback to centered view with reasonable height
            range_height = data_y_max - data_y_min
            if range_height <= 0:
                range_height = 10.0
            new_y_min = depth - range_height / 2
            new_y_max = depth + range_height / 2
            print(f"WARNING: Invalid range in scroll_to_depth, using centered view")
        
        # Apply the new range
        self.plot_widget.setYRange(new_y_min, new_y_max)
        
        # Update stored depth range
        self.min_depth = new_y_min
        self.max_depth = new_y_max
        
        # Emit view range changed signal for synchronization
        self.viewRangeChanged.emit(new_y_min, new_y_max)
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
    
    # =========================================================================
    # Boundary Line Methods (Phase 4: Depth Correction)
    # =========================================================================
    
    def set_lithology_data(self, dataframe):
        """Set lithology data and create boundary lines."""
        self.lithology_data = dataframe
        self.create_boundary_lines()
        
    def create_boundary_lines(self):
        """Create horizontal boundary lines for each lithology unit."""
        # Clear existing boundary lines
        self.clear_boundary_lines()
        
        if self.lithology_data is None or self.lithology_data.empty:
            return
            
        # Check for required columns
        required_columns = ['From_Depth', 'To_Depth']
        if not all(col in self.lithology_data.columns for col in required_columns):
            return
            
        # Create boundary lines for each row
        for idx, row in self.lithology_data.iterrows():
            # Create top boundary (From_Depth)
            top_depth = row['From_Depth']
            top_line = self.create_boundary_line(
                depth=top_depth,
                row_index=idx,
                boundary_type='top',
                color=self.top_boundary_color
            )
            
            # Create bottom boundary (To_Depth)
            bottom_depth = row['To_Depth']
            bottom_line = self.create_boundary_line(
                depth=bottom_depth,
                row_index=idx,
                boundary_type='bottom',
                color=self.bottom_boundary_color
            )
            
            # Store references
            self.boundary_lines[(idx, 'top')] = top_line
            self.boundary_lines[(idx, 'bottom')] = bottom_line
            
    def create_boundary_line(self, depth, row_index, boundary_type, color):
        """Create a single movable boundary line."""
        # Create infinite horizontal line
        line = pg.InfiniteLine(
            pos=depth,
            angle=0,  # Horizontal line
            movable=True,
            pen=pg.mkPen(color=color, width=self.boundary_width),
            hoverPen=pg.mkPen(color=color, width=self.boundary_width + 1)  # Thicker on hover
        )
        
        # Store metadata on the line object
        line.row_index = row_index
        line.boundary_type = boundary_type
        line.original_color = color
        line.original_pen = pg.mkPen(color=color, width=self.boundary_width)
        
        # Connect signals
        line.sigDragged.connect(lambda: self.on_boundary_dragged(line))
        line.sigPositionChangeFinished.connect(lambda: self.on_boundary_drag_finished(line))
        
        # Add to plot
        self.plot_widget.addItem(line)
        
        return line
        
    def clear_boundary_lines(self):
        """Remove all boundary lines from the plot."""
        for key, line in list(self.boundary_lines.items()):
            self.plot_widget.removeItem(line)
        self.boundary_lines.clear()
        
    def on_boundary_dragged(self, line):
        """Handle boundary line dragging."""
        # Store dragging state
        if self.dragging_line is None:
            self.dragging_line = line
            self.dragging_original_depth = line.pos().y()
            
            # Highlight the line with dragging style
            line.setPen(pg.mkPen(color=self.dragging_boundary_color, width=self.dragging_width))
            
        # Get current depth
        current_depth = line.pos().y()
        
        # Constrain movement to prevent invalid positions
        constrained_depth = self.constrain_boundary_movement(line, current_depth)
        if constrained_depth != current_depth:
            line.setPos(constrained_depth)
            current_depth = constrained_depth
        
        # Apply snapping to nearby boundaries
        snapped_depth = self.apply_snapping(current_depth, line)
        if snapped_depth != current_depth:
            line.setPos(snapped_depth)
            current_depth = snapped_depth
            
        # Show tooltip with depth value
        self.show_depth_tooltip(line, current_depth)
        
    def on_boundary_drag_finished(self, line):
        """Handle boundary line drag completion."""
        if self.dragging_line is not line:
            return
            
        # Get final depth
        final_depth = line.pos().y()
        original_depth = self.dragging_original_depth
        
        # Calculate the adjustment needed
        depth_change = final_depth - original_depth
        
        # Apply roof and floor correction logic
        adjusted_data = self.apply_roof_floor_correction(
            line.row_index, 
            line.boundary_type, 
            final_depth, 
            depth_change
        )
        
        # Restore original line style
        line.setPen(line.original_pen)
        
        # Emit signal with updated boundary information
        # The signal now includes whether data was successfully adjusted
        self.boundaryDragged.emit(line.row_index, line.boundary_type, final_depth)
        
        # Update lithology data if adjustment was successful
        if adjusted_data is not None:
            self.lithology_data = adjusted_data
            
            # Update all boundary lines to reflect changes
            self.update_all_boundary_lines()
        
        # Clear dragging state
        self.dragging_line = None
        self.dragging_original_depth = None
        
        # Hide tooltip
        QToolTip.hideText()
        
    def apply_roof_floor_correction(self, row_index, boundary_type, new_depth, depth_change):
        """
        Apply roof and floor correction logic when a boundary is moved.
        
        Logic:
        - When a boundary is dragged, the unit above shrinks/expands 
          and the unit below expands/shrinks to keep total depth unchanged.
        - This maintains the integrity of the geological column.
        
        Returns:
            Updated lithology DataFrame or None if adjustment is not possible
        """
        if self.lithology_data is None:
            return None
            
        # Create a copy of the data to modify
        adjusted_data = self.lithology_data.copy()
        
        if boundary_type == 'top':
            # Moving a top boundary (From_Depth)
            # This affects the current unit and the unit above
            
            # Update the current unit's From_Depth
            adjusted_data.loc[row_index, 'From_Depth'] = new_depth
            
            # If there's a unit above, adjust its To_Depth
            if row_index > 0:
                adjusted_data.loc[row_index - 1, 'To_Depth'] = new_depth
                
            # Update thickness for affected units
            self.update_thickness(adjusted_data, row_index)
            if row_index > 0:
                self.update_thickness(adjusted_data, row_index - 1)
                
        else:
            # Moving a bottom boundary (To_Depth)
            # This affects the current unit and the unit below
            
            # Update the current unit's To_Depth
            adjusted_data.loc[row_index, 'To_Depth'] = new_depth
            
            # If there's a unit below, adjust its From_Depth
            if row_index < len(adjusted_data) - 1:
                adjusted_data.loc[row_index + 1, 'From_Depth'] = new_depth
                
            # Update thickness for affected units
            self.update_thickness(adjusted_data, row_index)
            if row_index < len(adjusted_data) - 1:
                self.update_thickness(adjusted_data, row_index + 1)
        
        # Validate the adjustment
        if self.validate_adjustment(adjusted_data):
            return adjusted_data
        else:
            # Revert to original data
            return None
            
    def update_thickness(self, dataframe, row_index):
        """Update thickness calculation for a row."""
        if 'Thickness' in dataframe.columns:
            from_depth = dataframe.loc[row_index, 'From_Depth']
            to_depth = dataframe.loc[row_index, 'To_Depth']
            dataframe.loc[row_index, 'Thickness'] = to_depth - from_depth
            
    def validate_adjustment(self, dataframe):
        """Validate that the adjusted data is still valid."""
        # Check for basic validity
        if dataframe is None or dataframe.empty:
            return False
            
        # Check that From_Depth < To_Depth for all rows
        if not (dataframe['From_Depth'] < dataframe['To_Depth']).all():
            return False
            
        # Check for gaps or overlaps
        for i in range(len(dataframe) - 1):
            current_bottom = dataframe.loc[i, 'To_Depth']
            next_top = dataframe.loc[i + 1, 'From_Depth']
            
            # Allow small floating point differences
            if abs(current_bottom - next_top) > 0.001:
                return False
                
        return True
        
    def constrain_boundary_movement(self, line, depth):
        """Constrain boundary movement to prevent invalid positions."""
        if self.lithology_data is None:
            return depth
            
        row_index = line.row_index
        boundary_type = line.boundary_type
        
        # Get neighboring boundaries for constraints
        if boundary_type == 'top':
            # Top boundary (From_Depth) constraints:
            # 1. Must be above the bottom boundary of the same unit
            # 2. Should not go below the top boundary of the unit below (if exists)
            unit_bottom = self.lithology_data.loc[row_index, 'To_Depth']
            
            # Constraint 1: Must be above unit bottom
            if depth >= unit_bottom:
                return unit_bottom - 0.01  # Just above the bottom
                
            # Constraint 2: Check unit above
            if row_index > 0:
                unit_above_bottom = self.lithology_data.loc[row_index - 1, 'To_Depth']
                if depth <= unit_above_bottom:
                    return unit_above_bottom + 0.01  # Just below the unit above
        else:
            # Bottom boundary (To_Depth) constraints:
            # 1. Must be below the top boundary of the same unit
            # 2. Should not go above the bottom boundary of the unit above (if exists)
            unit_top = self.lithology_data.loc[row_index, 'From_Depth']
            
            # Constraint 1: Must be below unit top
            if depth <= unit_top:
                return unit_top + 0.01  # Just below the top
                
            # Constraint 2: Check unit below
            if row_index < len(self.lithology_data) - 1:
                unit_below_top = self.lithology_data.loc[row_index + 1, 'From_Depth']
                if depth >= unit_below_top:
                    return unit_below_top - 0.01  # Just above the unit below
        
        return depth
        
    def apply_snapping(self, depth, dragged_line):
        """Apply snapping to nearby boundaries."""
        if not self.boundary_lines:
            return depth
            
        # Get all other boundary depths
        other_depths = []
        for (row_idx, boundary_type), line in self.boundary_lines.items():
            if line is dragged_line:
                continue
            other_depths.append(line.pos().y())
            
        if not other_depths:
            return depth
            
        # Find closest boundary
        closest_depth = min(other_depths, key=lambda d: abs(d - depth))
        
        # Snap if within threshold
        if abs(closest_depth - depth) <= self.snap_threshold:
            return closest_depth
            
        return depth
        
    def show_depth_tooltip(self, line, depth):
        """Show tooltip with depth value near the dragged line."""
        # Get lithology information if available
        lithology_info = ""
        if self.lithology_data is not None and line.row_index < len(self.lithology_data):
            row_data = self.lithology_data.iloc[line.row_index]
            if 'Lithology' in row_data:
                lithology_info = f"\nLithology: {row_data['Lithology']}"
        
        # Create tooltip text
        boundary_type_str = "Top" if line.boundary_type == 'top' else "Bottom"
        tooltip_text = f"{boundary_type_str} Boundary\nDepth: {depth:.2f} m{lithology_info}"
        
        # Show tooltip at mouse position (simplified)
        # In a full implementation, we'd track mouse position
        QToolTip.showText(
            self.mapToGlobal(self.rect().center()),
            tooltip_text,
            self,
            self.rect(),
            2000  # Show for 2 seconds
        )
        
    def update_boundary_line(self, row_index, boundary_type, new_depth):
        """Update a boundary line position (called when table data changes)."""
        key = (row_index, boundary_type)
        if key in self.boundary_lines:
            line = self.boundary_lines[key]
            line.setPos(new_depth)
            
    def update_all_boundary_lines(self):
        """Update all boundary lines based on current lithology data."""
        if self.lithology_data is None:
            return
            
        for idx, row in self.lithology_data.iterrows():
            # Update top boundary
            top_key = (idx, 'top')
            if top_key in self.boundary_lines:
                self.boundary_lines[top_key].setPos(row['From_Depth'])
                
            # Update bottom boundary
            bottom_key = (idx, 'bottom')
            if bottom_key in self.boundary_lines:
                self.boundary_lines[bottom_key].setPos(row['To_Depth'])
    
    def set_curve_visibility(self, curve_name: str, visible: bool):
        """
        Set visibility of a curve by name.
        
        Args:
            curve_name: Internal curve name (e.g., 'short_space_density', 'gamma', etc.)
            visible: True to show the curve, False to hide it
        """
        # Map internal curve names to actual curve column names
        # This mapping might need to be adjusted based on actual data column names
        curve_name_mapping = {
            'short_space_density': ['SS', 'DENS', 'RHOB', 'short_space_density', 'density'],
            'long_space_density': ['LS', 'LSD', 'long_space_density'],
            'gamma': ['GR', 'gamma', 'gamma_ray', 'Gamma', 'GAMMA'],
            'cd': ['CD', 'cd', 'caliper', 'Caliper', 'CALI'],
            'res': ['RES', 'resistivity', 'res', 'Resistivity', 'RT'],
            'cal': ['CAL', 'cal', 'caliper', 'Caliper', 'CALI']
        }
        
        # Get possible column names for this curve type
        possible_names = curve_name_mapping.get(curve_name, [curve_name])
        
        # Try to find the curve by checking all possible names
        found_curve = None
        for name in possible_names:
            if name in self.curve_items:
                found_curve = self.curve_items[name]
                break
        
        # If not found by exact name, try case-insensitive search
        if not found_curve and self.curve_items:
            for stored_name, curve_item in self.curve_items.items():
                stored_lower = stored_name.lower()
                for possible_name in possible_names:
                    if possible_name.lower() in stored_lower or stored_lower in possible_name.lower():
                        found_curve = curve_item
                        break
                if found_curve:
                    break
        
        if found_curve:
            # Set visibility of the curve item
            found_curve.setVisible(visible)
            
            # Also update legend if it exists
            if hasattr(self.plot_item, 'legend'):
                legend = self.plot_item.legend
                if legend:
                    # Find the legend item for this curve and update its visibility
                    for item in legend.items:
                        if hasattr(item, 'item') and item.item == found_curve:
                            item.setVisible(visible)
                            break
            
            print(f"Curve '{curve_name}' visibility set to: {visible}")
        else:
            print(f"Warning: Curve '{curve_name}' not found in plot. Available curves: {list(self.curve_items.keys())}")
    
    # =========================================================================
    # Anomaly Detection Methods (Phase 3: Advanced LAS Comparative Plotting)
    # =========================================================================
    
    def set_bit_size(self, bit_size_mm):
        """Set bit size for caliper anomaly detection."""
        self.bit_size_mm = bit_size_mm
        self.update_anomaly_detection()
        
    def update_anomaly_detection(self):
        """Update anomaly detection based on current bit size and data."""
        if self.data is None or self.data.empty:
            return
            
        # Detect anomalies
        anomaly_intervals = self.detect_caliper_anomalies(self.bit_size_mm)
        
        # Highlight anomalies
        self.highlight_anomalies(anomaly_intervals)
        
    def detect_caliper_anomalies(self, bit_size_mm):
        """
        Detect caliper anomalies where (CAL - BitSize) > 20 mm.
        
        Args:
            bit_size_mm: Bit size in millimeters
            
        Returns:
            List of (start_depth, end_depth) tuples for anomaly intervals
        """
        if self.data is None or self.data.empty:
            return []
            
        # Try to find CAL column using various possible names
        cal_column = None
        cal_column_names = ['CAL', 'cal', 'caliper', 'Caliper', 'CALI', 'CD', 'cd']
        
        for col_name in cal_column_names:
            if col_name in self.data.columns:
                cal_column = col_name
                break
                
        if cal_column is None:
            print("Warning: CAL (caliper) column not found in data")
            return []
            
        # Get depth and CAL data
        depth_data = self.data[self.depth_column].values
        cal_data = self.data[cal_column].values
        
        # Handle NaN values
        valid_mask = ~np.isnan(cal_data)
        if not np.any(valid_mask):
            return []
            
        valid_depths = depth_data[valid_mask]
        valid_cal = cal_data[valid_mask]
        
        # Convert bit size from mm to same units as CAL data (assuming CAL is also in mm)
        # If CAL is in inches, we'd need to convert, but assuming mm for now
        bit_size = bit_size_mm
        
        # Detect anomalies: (CAL - BitSize) > 20 mm
        anomaly_mask = (valid_cal - bit_size) > 20
        
        # If no anomalies, return empty list
        if not np.any(anomaly_mask):
            return []
            
        # Convert mask to contiguous intervals
        anomaly_intervals = []
        in_anomaly = False
        start_idx = -1
        
        for i, is_anomaly in enumerate(anomaly_mask):
            if is_anomaly and not in_anomaly:
                # Start of anomaly interval
                in_anomaly = True
                start_idx = i
            elif not is_anomaly and in_anomaly:
                # End of anomaly interval
                in_anomaly = False
                # Add interval (start_depth, end_depth)
                anomaly_intervals.append((valid_depths[start_idx], valid_depths[i-1]))
                
        # Handle case where anomaly continues to end of data
        if in_anomaly:
            anomaly_intervals.append((valid_depths[start_idx], valid_depths[-1]))
            
        return anomaly_intervals
        
    def highlight_anomalies(self, anomaly_intervals):
        """
        Highlight anomaly intervals with semi-transparent red regions.
        
        Args:
            anomaly_intervals: List of (start_depth, end_depth) tuples
        """
        # Clear previous anomaly regions
        self.clear_anomaly_highlights()
        
        # Create new regions for each anomaly interval
        for start_depth, end_depth in anomaly_intervals:
            # Create linear region item for anomaly interval
            region = pg.LinearRegionItem(
                values=[start_depth, end_depth],
                orientation='horizontal',
                brush=self.anomaly_brush,
                movable=False
            )
            
            # Add to plot
            self.plot_widget.addItem(region)
            
            # Store reference
            self.anomaly_regions.append(region)
            
    def clear_anomaly_highlights(self):
        """Remove all anomaly highlight regions from the plot."""
        for region in self.anomaly_regions:
            self.plot_widget.removeItem(region)
        self.anomaly_regions.clear()
        
    def set_anomaly_highlight_visible(self, visible):
        """Show or hide anomaly highlight regions.
        
        Args:
            visible: Boolean indicating whether to show anomaly highlights
        """
        for region in self.anomaly_regions:
            region.setVisible(visible)
        
    def on_data_updated(self):
        """Called when data is updated to refresh anomaly detection."""
        self.update_anomaly_detection()