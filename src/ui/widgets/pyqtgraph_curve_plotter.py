"""
PyQtGraphCurvePlotter - A PyQtGraph-based curve plotter widget for Earthworm Moltbot.
Provides improved performance and features over the QGraphicsScene-based CurvePlotter.
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QToolTip
from PyQt6.QtGui import QColor, QPen, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QTimer
import pyqtgraph as pg

class PyQtGraphCurvePlotter(QWidget):
    """A PyQtGraph-based curve plotter widget with improved performance."""
    
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