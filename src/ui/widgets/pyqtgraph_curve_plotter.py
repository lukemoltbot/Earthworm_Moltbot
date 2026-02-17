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
# Disable auto-legend globally in pyqtgraph
pg.setConfigOptions(antialias=True, foreground='k', background='w')
from pyqtgraph import AxisItem

# Import ScrollPolicyManager for scroll control
from .scroll_policy_manager import ScrollPolicyManager

# Import Phase 3 performance components
from .data_stream_manager import DataStreamManager, LoadingStrategy
from .viewport_cache_manager import ViewportCacheManager
from .scroll_optimizer import ScrollOptimizer

# Import 1Point-style curve display modes
from .curve_display_modes import CurveDisplayModes, create_curve_display_modes

class PyQtGraphCurvePlotter(QWidget):
    """A PyQtGraph-based curve plotter widget with improved performance and dual-axis support."""
    
    # Signal emitted when user clicks on the plot (for synchronization with table)
    pointClicked = pyqtSignal(float)  # depth value
    
    # Signal emitted when view range changes (for synchronization with overview)
    viewRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth
    
    # Signal emitted when zoom level changes
    zoomLevelChanged = pyqtSignal(float)  # zoom_factor
    
    # Signal emitted when a boundary line is dragged (for updating table data)
    boundaryDragged = pyqtSignal(int, str, float)  # row_index, boundary_type, new_depth
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuration
        self.data = None
        self.depth_column = 'DEPT'  # Assuming 'DEPT' is the standardized depth column name
        self.curve_configs = []  # List of dictionaries for curve configurations
        self.depth_scale = 50  # Pixels per depth unit (matches EnhancedStratigraphicColumn for 20m view)
        self.plot_width = 110  # Width of the plot area
        
        # Legacy feature migration: X-axis label area
        self.x_axis_height = 60  # Space for curve labels, similar to legacy CurvePlotter
        self.x_axis_labels = {}  # Dictionary to store X-axis label items
        self.plot_area_separator = None  # Top border line separating plot from X-axis labels
        
        # Multi-axis configuration
        self.gamma_viewbox = None  # Secondary ViewBox for Gamma Ray
        self.gamma_axis = None  # Top axis for Gamma Ray
        self.gamma_curves = []  # List of Gamma Ray curves
        self.density_curves = []  # List of Density curves
        self.caliper_viewbox = None  # Third ViewBox for Caliper
        self.caliper_axis = None  # Bottom2 axis for Caliper
        self.caliper_curves = []  # List of Caliper curves
        self.resistivity_viewbox = None  # Fourth ViewBox for Resistivity
        self.resistivity_axis = None  # Bottom3 axis for Resistivity
        self.resistivity_curves = []  # List of Resistivity curves
        self.curve_items = {}  # Dictionary mapping curve_name -> curve item(s)
        
        # Curve type identification patterns
        self.gamma_patterns = ['gamma', 'gr', 'gamma_ray', 'gammaray']
        self.density_patterns = ['density', 'den', 'rhob', 'ss', 'ls']
        self.caliper_patterns = ['caliper', 'cal', 'cd', 'diameter']
        self.resistivity_patterns = ['resistivity', 'res', 'rt', 'ild']
        
        # Lithology data for boundary lines
        self.lithology_data = None
        self.boundary_lines = {}  # Dict mapping (row_index, boundary_type) -> pg.InfiniteLine
        
        # Recursion protection for viewbox updates
        self._updating_all_viewboxes = False
        
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
        
        # Zoom state management
        self.zoom_state_manager = None
        self.is_zooming = False
        self.fixed_scale_enabled = True  # Prevent scale changes during scrolling
        
        # Anomaly detection
        self.bit_size_mm = 150.0  # Default bit size in mm
        self.anomaly_regions = []  # List of pg.LinearRegionItem for anomaly highlighting
        self.anomaly_brush = (255, 0, 0, 50)  # Semi-transparent red for anomaly regions
        
        # Synchronization state tracking to prevent infinite loops
        from .sync_state_tracker import SyncStateTracker
        self.sync_tracker = SyncStateTracker(debounce_ms=50)
        self.sync_enabled = True
        
        # Phase 3 Performance Components
        self.data_stream_manager = None
        self.viewport_cache_manager = None
        self.scroll_optimizer = None
        self.performance_monitor_enabled = False
        
        # 1Point-style Curve Display Modes
        self.curve_display_modes = create_curve_display_modes()
        self.current_display_mode = 'overlaid'  # Default to overlaid mode
        
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
        # Ensure no legend - set both public and private attributes
        try:
            self.plot_item.legend = None
            if hasattr(self.plot_item, '_legend'):
                self.plot_item._legend = None
        except:
            pass  # Some pyqtgraph versions might not like this, but we try
        
        # Configure Y-axis for whole metre increments
        self.configure_y_axis_ticks()
        
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
        
        # Connect view range change signal with recursion protection
        self._updating_view_range = False
        self.plot_widget.sigRangeChanged.connect(self.on_view_range_changed)
        
        layout.addWidget(self.plot_widget)
        
        # Add X-axis controls for each curve (legacy style)
        self.axis_controls_widget = QWidget()
        self.axis_controls_layout = QVBoxLayout(self.axis_controls_widget)
        self.axis_controls_layout.setContentsMargins(5, 5, 5, 5)
        self.axis_controls_layout.setSpacing(2)
        
        layout.addWidget(self.axis_controls_widget)
        
        # Initialize Phase 3 performance components
        self.initialize_performance_components()
        
    def initialize_performance_components(self):
        """Initialize Phase 3 performance optimization components."""
        try:
            # Initialize DataStreamManager for efficient LAS data loading
            self.data_stream_manager = DataStreamManager(
                max_memory_mb=500,  # 500MB memory limit
                chunk_size_points=10000,  # 10,000 points per chunk
                loading_strategy=LoadingStrategy.PROGRESSIVE
            )
#             print("✓ DataStreamManager initialized for LAS file loading")
            
            # Initialize ViewportCacheManager for hardware-accelerated rendering
            self.viewport_cache_manager = ViewportCacheManager(
                max_cache_size_mb=50.0  # 50MB cache limit
            )
            print("✓ ViewportCacheManager initialized for viewport caching")
            
            # Initialize ScrollOptimizer for smooth scrolling
            self.scroll_optimizer = ScrollOptimizer(
                target_fps=60,
                enable_inertia=True,
                enable_prediction=True
            )
#             print("✓ ScrollOptimizer initialized for smooth scrolling")
            
            # Note: Full integration requires:
            # 1. Connecting ScrollOptimizer to mouse events
            # 2. Using ViewportCacheManager for viewport rendering
            # 3. Using DataStreamManager for LAS file loading
            
            # Enable performance monitoring
            self.performance_monitor_enabled = True
            print("Phase 3 performance components initialized successfully")
            
        except Exception as e:
            pass
#             print(f"Warning: Could not initialize Phase 3 performance components: {e}")
            print("Falling back to standard rendering mode")
            self.performance_monitor_enabled = False
        
    def setup_x_axis_labels(self):
        """Setup X-axis labels area similar to legacy CurvePlotter."""
        # Clear existing labels
        self.clear_x_axis_labels()
        
        if not self.curve_configs:
            return
            
        # Sort curves for consistent stacking order (legacy ordering)
        sorted_configs = self.get_sorted_curve_configs()
        
        # Create plot area separator (top border line)
        self.create_plot_area_separator()
        
        # Create labels for each curve
        self.create_curve_labels(sorted_configs)
        
    def get_sorted_curve_configs(self):
        """Sort curves using legacy ordering: gamma → short_space_density → long_space_density → others."""
        if not self.curve_configs:
            return []
            
        # Create a copy to avoid modifying original
        configs = self.curve_configs.copy()
        
        # Define sorting priority
        def get_curve_priority(config):
            curve_name = config['name'].lower()
            if 'gamma' in curve_name:
                return 0  # Gamma first
            elif 'short_space_density' in curve_name or 'ss' in curve_name or 'short' in curve_name:
                return 1  # Short space density second
            elif 'long_space_density' in curve_name or 'ls' in curve_name or 'long' in curve_name:
                return 2  # Long space density third
            else:
                return 3  # Other curves last
        
        # Sort by priority, then by name for consistent ordering
        return sorted(configs, key=lambda x: (get_curve_priority(x), x['name']))
        
    def create_plot_area_separator(self):
        """Create top border line separating plot area from X-axis labels."""
        # Remove existing separator if any
        if self.plot_area_separator:
            self.plot_widget.removeItem(self.plot_area_separator)
            
        # Get current view range to position separator at top of X-axis area
        view_range = self.plot_widget.viewRange()
        if view_range and len(view_range) > 1:
            y_min, y_max = view_range[1]
            
            # Position separator at the top of X-axis label area
            # X-axis labels are below the plot, so separator goes at y_max (bottom of plot)
            separator_y = y_max
            
            # Create line item
            self.plot_area_separator = pg.InfiniteLine(
                pos=separator_y,
                angle=0,  # Horizontal line
                pen=pg.mkPen(color='black', width=1),
                movable=False
            )
            
            # Add to plot
            self.plot_widget.addItem(self.plot_area_separator)
            
    def create_curve_labels(self, sorted_configs):
        """Create X-axis labels for each curve with min/max values."""
        # Calculate label positions
        view_range = self.plot_widget.viewRange()
        if not view_range or len(view_range) < 2:
            return
            
        y_min, y_max = view_range[1]
        
        # Start position for labels (below plot area)
        current_y_offset = y_max + 5
        
        for config in sorted_configs:
            curve_name = config['name']
            min_value = config['min']
            max_value = config['max']
            color = config['color']
            inverted = config.get('inverted', False)
            
            # Format values appropriately
            # Gamma values are typically integers, density values are decimals
            if 'gamma' in curve_name.lower():
                min_str = f"{min_value:.0f}"
                max_str = f"{max_value:.0f}"
            else:
                min_str = f"{min_value:.2f}"
                max_str = f"{max_value:.2f}"
            
            # Create text items for min and max values
            min_text = pg.TextItem(text=min_str, color=color, anchor=(0, 0))
            max_text = pg.TextItem(text=max_str, color=color, anchor=(1, 0))
            
            # Position labels at plot edges
            # Note: For inverted axes (well log style), x_min > x_max
            x_range = self.plot_widget.viewRange()[0]
            if x_range:
                x_min, x_max = x_range
                
                # For inverted curves (well log style), min value is on right, max on left
                if inverted:
                    pass
                    # Not inverted: min on left, max on right
                    min_text.setPos(x_min, current_y_offset)
                    max_text.setPos(x_max, current_y_offset)
                else:
                    # Inverted (well log style): min on right, max on left
                    min_text.setPos(x_max, current_y_offset)
                    max_text.setPos(x_min, current_y_offset)
            
            # Create curve name label (centered)
            name_text = pg.TextItem(text=curve_name, color=color, anchor=(0.5, 0))
            if x_range:
                center_x = (x_min + x_max) / 2
                name_text.setPos(center_x, current_y_offset - 15)  # Position above min/max labels
            
            # Add to plot and store references
            self.plot_widget.addItem(min_text)
            self.plot_widget.addItem(max_text)
            self.plot_widget.addItem(name_text)
            
            # Store in dictionary for later updates
            self.x_axis_labels[curve_name] = {
                'min': min_text,
                'max': max_text,
                'name': name_text
            }
            
            # Adjust offset for next curve
            current_y_offset += 25  # Space for next curve's labels
            
    def clear_x_axis_labels(self):
        """Remove all X-axis labels from the plot."""
        for curve_name, labels in self.x_axis_labels.items():
            for label_type, label_item in labels.items():
                if label_item and label_item in self.plot_widget.items():
                    self.plot_widget.removeItem(label_item)
        self.x_axis_labels.clear()
        
        # Remove separator
        if self.plot_area_separator and self.plot_area_separator in self.plot_widget.items():
            self.plot_widget.removeItem(self.plot_area_separator)
        self.plot_area_separator = None
        
    def update_x_axis_labels_position(self):
        """Update X-axis labels position when view range changes."""
        if not self.x_axis_labels:
            return
            
        view_range = self.plot_widget.viewRange()
        if not view_range or len(view_range) < 2:
            return
            
        y_min, y_max = view_range[1]
        
        # Update separator position
        if self.plot_area_separator:
            self.plot_area_separator.setPos(y_max)
        
        # Update label positions
        current_y_offset = y_max + 5
        
        # Get sorted curve names to maintain stacking order
        sorted_configs = self.get_sorted_curve_configs()
        
        for config in sorted_configs:
            curve_name = config['name']
            if curve_name not in self.x_axis_labels:
                continue
                
            labels = self.x_axis_labels[curve_name]
            x_range = self.plot_widget.viewRange()[0]
            
            if x_range:
                x_min, x_max = x_range
                center_x = (x_min + x_max) / 2
                
                # Update min label position
                if 'min' in labels and labels['min']:
                    labels['min'].setPos(x_min, current_y_offset)
                
                # Update max label position
                if 'max' in labels and labels['max']:
                    labels['max'].setPos(x_max, current_y_offset)
                
                # Update name label position
                if 'name' in labels and labels['name']:
                    labels['name'].setPos(center_x, current_y_offset - 15)
            
            current_y_offset += 25
        
    def setup_dual_axes(self):
        """Setup multi X-axes for LAS curve plotting (gamma, density, caliper, resistivity)."""
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
        
        # Create caliper axis (bottom2) and ViewBox
        self.caliper_axis = AxisItem('bottom')
        self.plot_item.layout.addItem(self.caliper_axis, 2, 1)  # row 2, col 1 (below main bottom axis)
        self.caliper_axis.linkToView(self.plot_item.vb)  # Link to main viewbox for Y
        self.caliper_viewbox = pg.ViewBox()
        self.plot_item.scene().addItem(self.caliper_viewbox)
        self.caliper_axis.linkToView(self.caliper_viewbox)
        self.caliper_viewbox.setXLink(self.plot_item)  # Share X-axis transform
        self.caliper_viewbox.setYLink(self.plot_item.vb)
        self.caliper_axis.setLabel('Caliper', units='mm', color='#FFA500')
        self.caliper_axis.setVisible(False)  # Hide until caliper curves are added
        
        # Create resistivity axis (bottom3) and ViewBox
        self.resistivity_axis = AxisItem('bottom')
        self.plot_item.layout.addItem(self.resistivity_axis, 3, 1)  # row 3, col 1 (below caliper axis)
        self.resistivity_axis.linkToView(self.plot_item.vb)
        self.resistivity_viewbox = pg.ViewBox()
        self.plot_item.scene().addItem(self.resistivity_viewbox)
        self.resistivity_axis.linkToView(self.resistivity_viewbox)
        self.resistivity_viewbox.setXLink(self.plot_item)
        self.resistivity_viewbox.setYLink(self.plot_item.vb)
        self.resistivity_axis.setLabel('Resistivity', units='ohm.m', color='#FF0000')
        self.resistivity_axis.setVisible(False)  # Hide until resistivity curves are added
        
        # Handle view synchronization for all viewboxes
        def update_all_viewboxes():
            """Update all ViewBox geometries when main view changes."""
            rect = self.plot_item.vb.sceneBoundingRect()
            if self.gamma_viewbox:
                self.gamma_viewbox.setGeometry(rect)
                self.gamma_viewbox.linkedViewChanged(self.plot_item.vb, self.gamma_viewbox.YAxis)
            if self.caliper_viewbox:
                self.caliper_viewbox.setGeometry(rect)
                self.caliper_viewbox.linkedViewChanged(self.plot_item.vb, self.caliper_viewbox.YAxis)
            if self.resistivity_viewbox:
                self.resistivity_viewbox.setGeometry(rect)
                self.resistivity_viewbox.linkedViewChanged(self.plot_item.vb, self.resistivity_viewbox.YAxis)
        
        def update_all_on_scroll():
            """Update all ViewBoxes during scrolling."""
            # Add recursion protection
            if hasattr(self, '_updating_all_viewboxes') and self._updating_all_viewboxes:
                return
                
            self._updating_all_viewboxes = True
            try:
                rect = self.plot_item.vb.sceneBoundingRect()
                view_range = self.plot_item.vb.viewRange()
                if view_range and len(view_range) > 1:
                    y_min, y_max = view_range[1]
                    if self.gamma_viewbox:
                        self.gamma_viewbox.setGeometry(rect)
                        self.gamma_viewbox.setYRange(y_min, y_max, padding=0)
                    if self.caliper_viewbox:
                        self.caliper_viewbox.setGeometry(rect)
                        self.caliper_viewbox.setYRange(y_min, y_max, padding=0)
                    if self.resistivity_viewbox:
                        self.resistivity_viewbox.setGeometry(rect)
                        self.resistivity_viewbox.setYRange(y_min, y_max, padding=0)
            finally:
                self._updating_all_viewboxes = False
        
        # Connect resize signal
        self.plot_item.vb.sigResized.connect(update_all_viewboxes)
        # Connect view range changes for scrolling
        self.plot_item.vb.sigRangeChanged.connect(update_all_on_scroll)
        
        # Store update functions for later use
        self.update_gamma_view_func = update_all_viewboxes
        
        # Initial update
        update_all_viewboxes()
        
    def configure_y_axis_ticks(self):
        """Configure Y-axis to show ticks at every whole metre."""
        try:
            # Get the Y-axis
            y_axis = self.plot_item.getAxis('left')
            
            if y_axis is None:
                print("ERROR (PyQtGraphCurvePlotter.configure_y_axis_ticks): Could not get Y-axis")
                return
            
            # Note: PyQtGraph's AxisItem doesn't have setAutoTick or setTickSpacing methods
            # We'll handle tick configuration in update_y_axis_ticks instead
            self.y_axis = y_axis
            
#             print(f"DEBUG (PyQtGraphCurvePlotter.configure_y_axis_ticks): Y-axis reference stored for tick configuration")
            
        except Exception as e:
            print(f"ERROR (PyQtGraphCurvePlotter.configure_y_axis_ticks): Failed to configure Y-axis: {e}")
        
    def update_y_axis_ticks(self):
        """Update Y-axis ticks based on current view range."""
        try:
            if not hasattr(self, 'y_axis') or self.y_axis is None:
                pass
#                 print("DEBUG (PyQtGraphCurvePlotter.update_y_axis_ticks): Y-axis not initialized")
                return
                
            # Get current view range
            view_range = self.get_view_range()
            if view_range is None:
                pass
#                 print("DEBUG (PyQtGraphCurvePlotter.update_y_axis_ticks): No view range available")
                return
                
            y_min, y_max = view_range
            
            # Validate range
            if y_min >= y_max:
                print(f"ERROR (PyQtGraphCurvePlotter.update_y_axis_ticks): Invalid range {y_min:.1f} >= {y_max:.1f}")
                return
            
            # Create ticks at every whole metre within the visible range
            # Round to nearest whole metre
            start_tick = np.floor(y_min)
            end_tick = np.ceil(y_max)
            
            # Limit number of ticks to prevent performance issues with very long holes
            max_ticks = 200  # Reasonable maximum for display
            tick_count = int(end_tick - start_tick) + 1
            
            if tick_count > max_ticks:
                pass
                # Show ticks at coarser intervals if there are too many
                interval = max(1, int(np.ceil(tick_count / max_ticks)))
                major_ticks = np.arange(start_tick, end_tick + 1, interval)
#                 print(f"DEBUG (PyQtGraphCurvePlotter.update_y_axis_ticks): Too many ticks ({tick_count}), using interval {interval}")
            else:
                # Generate ticks at every whole metre
                major_ticks = np.arange(start_tick, end_tick + 1, 1.0)
            
            # Create tick dictionary: [(position1, label1), (position2, label2), ...]
            tick_dict = [(tick, f"{tick:.0f}") for tick in major_ticks]
            
            # Set the ticks
            self.y_axis.setTicks([tick_dict])
            
            print(f"DEBUG (PyQtGraphCurvePlotter.update_y_axis_ticks): Updated Y-axis ticks for range {y_min:.1f}-{y_max:.1f}m, "
                  f"{len(major_ticks)} ticks at: {[f'{t:.0f}' for t in major_ticks[:5]]}...")
            
        except Exception as e:
            print(f"ERROR (PyQtGraphCurvePlotter.update_y_axis_ticks): Failed to update ticks: {e}")
        
    def set_curve_configs(self, configs):
        """Set curve configurations and redraw."""
        self.curve_configs = configs
        self.draw_curves()
        self.update_axis_controls()
        # Update X-axis labels
        self.setup_x_axis_labels()
        
    def set_data(self, dataframe):
        """Set data and redraw curves."""
        self.data = dataframe
        self.draw_curves()
        self.on_data_updated()
        # Update Y-axis ticks after data is set
        if self.data is not None and not self.data.empty:
            self.update_y_axis_ticks()
        
    def set_display_mode(self, mode_name: str) -> bool:
        """
        Set the curve display mode.
        
        Args:
            mode_name: One of 'overlaid', 'stacked', 'side_by_side', 'histogram'
        
        Returns:
            bool: True if mode was changed, False otherwise
        """
        if mode_name not in self.curve_display_modes.get_available_modes():
            pass
#             print(f"Warning: Unknown display mode: {mode_name}")
            return False
            
        if self.curve_display_modes.set_mode(mode_name):
            self.current_display_mode = mode_name
#             print(f"Display mode changed to: {mode_name}")
            
            # Redraw curves with new mode
            if self.data is not None and not self.data.empty:
                self.draw_curves()
            return True
            
        return False
    
    def get_display_mode(self) -> str:
        """Get current display mode name."""
        return self.current_display_mode
    
    def get_available_display_modes(self) -> list:
        """Get list of available display mode names."""
        return self.curve_display_modes.get_available_modes()
    
    def get_display_mode_info(self, mode_name: str = None) -> dict:
        """
        Get information about a display mode.
        
        Args:
            mode_name: Mode name (defaults to current mode)
        
        Returns:
            dict: Mode information
        """
        if mode_name is None:
            mode_name = self.current_display_mode
        return self.curve_display_modes.get_mode_info(mode_name) or {}
    
    def draw_curves(self):
        """Draw all configured curves using PyQtGraph with dual-axis support."""
        # CRITICAL FIX: Ensure no legend exists BEFORE drawing any curves
        # In pyqtgraph, accessing plot_item.legend can automatically create a legend!
        # We must NEVER access plot_item.legend property.
        
        # Method 1: Remove any LegendItem from plot items without accessing legend property
        items_to_remove = []
        for item in self.plot_item.items[:]:
            # Check if this is a LegendItem by class name (safer than checking legend property)
            class_name = item.__class__.__name__
            if 'Legend' in class_name or 'legend' in str(item).lower():
                print(f"DEBUG (draw_curves): Found potential legend item: {class_name}, removing")
                items_to_remove.append(item)
        
        for item in items_to_remove:
            try:
                self.plot_item.removeItem(item)
                item.hide()
                if hasattr(item, 'setParent'):
                    item.setParent(None)
                if hasattr(item, 'close'):
                    item.close()
            except Exception as e:
                print(f"DEBUG (draw_curves): Error removing legend item: {e}")
        
        # Method 2: Try to set private _legend attribute if it exists
        # This avoids triggering the legend property getter
        try:
            if hasattr(self.plot_item, '_legend'):
                self.plot_item._legend = None
        except:
            pass
        
        # Method 3: Disable auto-add-to-legend behavior if possible
        # Some pyqtgraph versions have autoAddToLegend setting
        try:
            if hasattr(self.plot_item, 'autoAddToLegend'):
                self.plot_item.autoAddToLegend = False
        except:
            pass
        
        # Phase 3.2: Try to use viewport cache first
        # TODO: Implement viewport cache properly
        # if self.viewport_cache_manager and self.performance_monitor_enabled:
        #     cache_key = self._get_viewport_cache_key()
        #     cached_result = self.viewport_cache_manager.get_cached(cache_key)
        #     
        #     if cached_result:
        #         # Apply cached rendering
        #         self._apply_cached_curves(cached_result)
        #         return
        
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
        
        # Configure plot for current display mode
        if self.current_display_mode == 'histogram':
            pass
            # For histogram mode, configure the plot
            self.curve_display_modes.configure_plot(self.plot_widget, self.curve_configs)
        # Note: Other modes will use existing dual-axis configuration
        
        # Get sorted curve configs using legacy ordering
        sorted_configs = self.get_sorted_curve_configs()
        
        # Separate curve configs into gamma, density, caliper, and resistivity curves
        gamma_configs = []
        density_configs = []
        caliper_configs = []
        resistivity_configs = []
        
        for config in sorted_configs:
            curve_name = config['name'].lower()
            
            # Check curve type patterns
            is_gamma = any(pattern in curve_name for pattern in self.gamma_patterns)
            is_caliper = any(pattern in curve_name for pattern in self.caliper_patterns)
            is_resistivity = any(pattern in curve_name for pattern in self.resistivity_patterns)
            
            if is_gamma:
                gamma_configs.append(config)
            elif is_caliper:
                caliper_configs.append(config)
            elif is_resistivity:
                resistivity_configs.append(config)
            else:
                # Assume it's a density curve (or other curve that goes on main axis)
                density_configs.append(config)
        
        # Track curves for legend and visibility control
        self.gamma_curves = []
        self.density_curves = []
        self.caliper_curves = []
        self.resistivity_curves = []
        self.curve_items = {}  # Dictionary mapping curve_name -> curve item(s)
        
        # Use 1Point-style display modes for density curves
        if self.current_display_mode == 'histogram':
            pass
            # For histogram mode, use the display modes system
            self.curve_display_modes.draw_curves(
                self.plot_widget, 
                self.data, 
                self.depth_column, 
                density_configs
            )
        else:
            # For other modes, use existing dual-axis logic (for now)
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
                
                # Phase 5: Apply downsampling for performance optimization
                if self.performance_monitor_enabled and len(valid_values) > 1000:
                    valid_values, valid_depths = self._get_downsampled_data(
                        valid_values, valid_depths, self.get_view_range()
                    )
                
                # Create pen for the curve with line style
                line_style = config.get('line_style', 'solid')
                if line_style == 'dotted':
                    pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DotLine)
                elif line_style == 'dashed':
                    pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashLine)
                elif line_style == 'dash_dot':
                    pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashDotLine)
                else:  # solid
                    pen = pg.mkPen(color=color, width=thickness)
                
                # Apply inversion if specified
                # Note: In legacy plotter:
                # - inverted=False: axis IS inverted (for well logs) - low values on right, high on left
                # - inverted=True: axis is NOT inverted - low values on left, high on right
                inverted = config.get('inverted', False)
                
                # Plot the curve - we'll handle inversion at axis level
                curve = self.plot_widget.plot(valid_values, valid_depths, pen=pen)
                
                # Store inversion state
                curve.inverted = inverted
                
                # Store reference
                curve.config = config
                self.density_curves.append(curve)
                # Store in dictionary for visibility control
                self.curve_items[curve_name] = curve
        
        # Plot caliper curves on caliper viewbox (bottom2 axis)
        for config in caliper_configs:
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
            
            # Phase 5: Apply downsampling for performance optimization
            if self.performance_monitor_enabled and len(valid_values) > 1000:
                valid_values, valid_depths = self._get_downsampled_data(
                    valid_values, valid_depths, self.get_view_range()
                )
            
            # Create pen for the curve with line style
            line_style = config.get('line_style', 'solid')
            if line_style == 'dotted':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DotLine)
            elif line_style == 'dashed':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashLine)
            elif line_style == 'dash_dot':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashDotLine)
            else:  # solid
                pen = pg.mkPen(color=color, width=thickness)
            
            # Apply inversion if specified
            inverted = config.get('inverted', False)
            
            # Create PlotCurveItem for caliper viewbox
            curve = pg.PlotCurveItem(valid_values, valid_depths, pen=pen)
            curve.inverted = inverted
            curve.config = config
            
            # Add to caliper viewbox
            if self.caliper_viewbox:
                self.caliper_viewbox.addItem(curve)
                # Make axis visible
                if self.caliper_axis:
                    self.caliper_axis.setVisible(True)
            
            # Store reference
            self.caliper_curves.append(curve)
            self.curve_items[curve_name] = curve
        
        # Plot resistivity curves on resistivity viewbox (bottom3 axis)
        for config in resistivity_configs:
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
            
            # Phase 5: Apply downsampling for performance optimization
            if self.performance_monitor_enabled and len(valid_values) > 1000:
                valid_values, valid_depths = self._get_downsampled_data(
                    valid_values, valid_depths, self.get_view_range()
                )
            
            # Create pen for the curve with line style
            line_style = config.get('line_style', 'solid')
            if line_style == 'dotted':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DotLine)
            elif line_style == 'dashed':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashLine)
            elif line_style == 'dash_dot':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashDotLine)
            else:  # solid
                pen = pg.mkPen(color=color, width=thickness)
            
            # Apply inversion if specified
            inverted = config.get('inverted', False)
            
            # Create PlotCurveItem for resistivity viewbox
            curve = pg.PlotCurveItem(valid_values, valid_depths, pen=pen)
            curve.inverted = inverted
            curve.config = config
            
            # Add to resistivity viewbox
            if self.resistivity_viewbox:
                self.resistivity_viewbox.addItem(curve)
                # Make axis visible
                if self.resistivity_axis:
                    self.resistivity_axis.setVisible(True)
            
            # Store reference
            self.resistivity_curves.append(curve)
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
            
            # Phase 5: Apply downsampling for performance optimization
            if self.performance_monitor_enabled and len(valid_values) > 1000:
                valid_values, valid_depths = self._get_downsampled_data(
                    valid_values, valid_depths, self.get_view_range()
                )
            
            # Create pen for the curve with line style
            line_style = config.get('line_style', 'solid')
            if line_style == 'dotted':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DotLine)
            elif line_style == 'dashed':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashLine)
            elif line_style == 'dash_dot':
                pen = pg.mkPen(color=color, width=thickness, style=Qt.PenStyle.DashDotLine)
            else:  # solid
                pen = pg.mkPen(color=color, width=thickness)
            
            # Apply inversion if specified
            inverted = config.get('inverted', False)
            
            # Create PlotCurveItem for gamma viewbox with a name for the legend
            curve = pg.PlotCurveItem(valid_values, valid_depths, pen=pen)
            
            # Store inversion state
            curve.inverted = inverted
            
            # Add to gamma viewbox
            if self.gamma_viewbox:
                self.gamma_viewbox.addItem(curve)
            
            # Store reference
            curve.config = config
            self.gamma_curves.append(curve)
            # Store in dictionary for visibility control
            self.curve_items[curve_name] = curve
        
        # LEGEND REMOVAL: No legend should ever be shown
        # All legend removal is done at the beginning of draw_curves
        # We must NOT access plot_item.legend property here as it may create a legend
        
        # Set axis ranges and labels
        self.update_axis_ranges()
        
        # Setup X-axis labels (legacy feature migration)
        self.setup_x_axis_labels()
        
    def update_axis_ranges(self):
        """Update plot axis ranges based on curve configurations for dual-axis system."""
        if not self.curve_configs:
            return
            
        # Separate curve configs into gamma, density, caliper, and resistivity
        gamma_configs = []
        density_configs = []
        caliper_configs = []
        resistivity_configs = []
        
        for config in self.curve_configs:
            curve_name = config['name'].lower()
            is_gamma = any(pattern in curve_name for pattern in self.gamma_patterns)
            is_caliper = any(pattern in curve_name for pattern in self.caliper_patterns)
            is_resistivity = any(pattern in curve_name for pattern in self.resistivity_patterns)
            
            if is_gamma:
                gamma_configs.append(config)
            elif is_caliper:
                caliper_configs.append(config)
            elif is_resistivity:
                resistivity_configs.append(config)
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
            
            # Check inversion for density curves
            # Default is inverted=False (well log style, axis inverted)
            # If first density curve has inverted=True, don't invert axis
            if density_configs and density_configs[0].get('inverted', False):
                pass
                # Not inverted: low values on left, high on right
                self.plot_widget.setXRange(density_x_min - x_padding, density_x_max + x_padding)
            else:
                # Inverted (well log style): low values on right, high on left
                self.plot_widget.setXRange(density_x_max + x_padding, density_x_min - x_padding)
            
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
                
            # Check inversion for gamma curves
            # Default is inverted=False (well log style, axis inverted)
            # If first gamma curve has inverted=True, don't invert axis
            if gamma_configs and gamma_configs[0].get('inverted', False):
                pass
                # Not inverted: low values on left, high on right
                self.gamma_viewbox.setXRange(gamma_x_min, gamma_x_max)
            else:
                # Inverted (well log style): low values on right, high on left
                self.gamma_viewbox.setXRange(gamma_x_max, gamma_x_min)
            
            # Update top axis label if gamma axis exists
            if self.gamma_axis:
                self.gamma_axis.setLabel('Gamma Ray', units='API', color='#8b008b')
        
        # Set X-axis range for caliper curves (caliper viewbox, bottom2 axis)
        if caliper_configs and self.caliper_viewbox:
            caliper_x_min = float('inf')
            caliper_x_max = float('-inf')
            
            for config in caliper_configs:
                caliper_x_min = min(caliper_x_min, config['min'])
                caliper_x_max = max(caliper_x_max, config['max'])
            
            # Default range for caliper curves if not specified: 100 to 300 mm
            if caliper_x_min == float('inf'):
                caliper_x_min = 100.0
            if caliper_x_max == float('-inf'):
                caliper_x_max = 300.0
                
            # Check inversion for caliper curves
            if caliper_configs and caliper_configs[0].get('inverted', False):
                pass
                # Not inverted: low values on left, high on right
                self.caliper_viewbox.setXRange(caliper_x_min, caliper_x_max)
            else:
                # Inverted (well log style): low values on right, high on left
                self.caliper_viewbox.setXRange(caliper_x_max, caliper_x_min)
            
            # Update caliper axis label
            if self.caliper_axis:
                self.caliper_axis.setLabel('Caliper', units='mm', color='#FFA500')
                self.caliper_axis.setVisible(True)
        
        # Set X-axis range for resistivity curves (resistivity viewbox, bottom3 axis)
        if resistivity_configs and self.resistivity_viewbox:
            resistivity_x_min = float('inf')
            resistivity_x_max = float('-inf')
            
            for config in resistivity_configs:
                resistivity_x_min = min(resistivity_x_min, config['min'])
                resistivity_x_max = max(resistivity_x_max, config['max'])
            
            # Default range for resistivity curves if not specified: 0.1 to 1000 ohm.m
            if resistivity_x_min == float('inf'):
                resistivity_x_min = 0.1
            if resistivity_x_max == float('-inf'):
                resistivity_x_max = 1000.0
                
            # Check inversion for resistivity curves
            if resistivity_configs and resistivity_configs[0].get('inverted', False):
                pass
                # Not inverted: low values on left, high on right
                self.resistivity_viewbox.setXRange(resistivity_x_min, resistivity_x_max)
            else:
                # Inverted (well log style): low values on right, high on left
                self.resistivity_viewbox.setXRange(resistivity_x_max, resistivity_x_min)
            
            # Update resistivity axis label
            if self.resistivity_axis:
                self.resistivity_axis.setLabel('Resistivity', units='ohm.m', color='#FF0000')
                self.resistivity_axis.setVisible(True)
        
        # Set Y-axis range based on data
        if self.data is not None and not self.data.empty:
            y_min = self.data[self.depth_column].min()
            y_max = self.data[self.depth_column].max()
            self.setYRange(y_min, y_max)
            
    def update_axis_controls(self):
        """Update the X-axis controls widget with current curve configurations for dual-axis."""
        # Clear existing controls
        while self.axis_controls_layout.count():
            item = self.axis_controls_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        if not self.curve_configs:
            return
            
        # Separate curves into gamma, density, caliper, and resistivity for better organization
        gamma_configs = []
        density_configs = []
        caliper_configs = []
        resistivity_configs = []
        
        for config in self.curve_configs:
            curve_name = config['name'].lower()
            is_gamma = any(pattern in curve_name for pattern in self.gamma_patterns)
            is_caliper = any(pattern in curve_name for pattern in self.caliper_patterns)
            is_resistivity = any(pattern in curve_name for pattern in self.resistivity_patterns)
            
            if is_gamma:
                gamma_configs.append(config)
            elif is_caliper:
                caliper_configs.append(config)
            elif is_resistivity:
                resistivity_configs.append(config)
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
        
        # Add section header for Caliper curves (bottom2 axis)
        if caliper_configs:
            separator = QLabel()
            separator.setFixedHeight(10)
            self.axis_controls_layout.addWidget(separator)
            
            caliper_header = QLabel("<b>Caliper Curves (Bottom2 Axis)</b>")
            caliper_header.setStyleSheet("color: #FFA500; padding: 2px;")
            self.axis_controls_layout.addWidget(caliper_header)
            
            sorted_caliper = sorted(caliper_configs, key=lambda x: x['name'])
            for config in sorted_caliper:
                self.add_curve_control_row(config, 'caliper')
        
        # Add section header for Resistivity curves (bottom3 axis)
        if resistivity_configs:
            separator = QLabel()
            separator.setFixedHeight(10)
            self.axis_controls_layout.addWidget(separator)
            
            resistivity_header = QLabel("<b>Resistivity Curves (Bottom3 Axis)</b>")
            resistivity_header.setStyleSheet("color: #FF0000; padding: 2px;")
            self.axis_controls_layout.addWidget(resistivity_header)
            
            sorted_resistivity = sorted(resistivity_configs, key=lambda x: x['name'])
            for config in sorted_resistivity:
                self.add_curve_control_row(config, 'resistivity')
        
        # Add section header for Gamma Ray curves (top axis)
        if gamma_configs:
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
        elif curve_type == 'caliper':
            name_label.setStyleSheet("color: #FFA500;")
        elif curve_type == 'resistivity':
            name_label.setStyleSheet("color: #FF0000;")
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
        if curve_type == 'gamma':
            axis_text = "(Top)"
        elif curve_type == 'caliper':
            axis_text = "(Bottom2)"
        elif curve_type == 'resistivity':
            axis_text = "(Bottom3)"
        else:
            axis_text = "(Bottom)"
        axis_label = QLabel(axis_text)
        axis_label.setFixedWidth(60)
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
            pass
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
        self.setYRange(new_y_min, new_y_max)
        
    def set_depth_range(self, min_depth, max_depth):
        """Set the visible depth range."""
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.setYRange(min_depth, max_depth)
        
    def scroll_to_depth(self, depth):
        """Scroll the view to make the given depth visible with center alignment."""
        if self.data is None or self.data.empty:
            pass
#             print("WARNING: No data available for scrolling")
            return
            
        # Check if synchronization should proceed (prevent infinite loops)
        if self.sync_enabled and not self.sync_tracker.should_sync():
            pass
#             print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Sync blocked by tracker")
            return
            
        self.sync_tracker.begin_sync()
        
        try:
            print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Scrolling to depth {depth}")
            
            # Get current view range
            view_range = self.plot_widget.viewRange()
            current_y_min = view_range[1][0]
            current_y_max = view_range[1][1]
            current_height = current_y_max - current_y_min
            
#             print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Current range: {current_y_min:.2f}-{current_y_max:.2f}, Height: {current_height:.2f}")
            
            # Validate current_height to prevent division by zero or invalid ranges
            if current_height <= 0:
                pass
                # Use default height based on data range
                data_y_min = self.data[self.depth_column].min()
                data_y_max = self.data[self.depth_column].max()
                current_height = (data_y_max - data_y_min) * 0.1  # 10% of data range
                if current_height <= 0:
                    current_height = 10.0  # Default fallback
                print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Using calculated height: {current_height}")
            
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
#                 print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Adjusted for min bound, new range: {new_y_min:.2f}-{new_y_max:.2f}")
            elif new_y_max > data_y_max:
                offset = new_y_max - data_y_max
                new_y_max = data_y_max
                new_y_min = max(new_y_min - offset, data_y_min)
                print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Adjusted for max bound, new range: {new_y_min:.2f}-{new_y_max:.2f}")
            
            # Ensure valid range (new_y_min must be less than new_y_max)
            if new_y_min >= new_y_max:
                pass
                # Fallback to centered view with reasonable height
                range_height = data_y_max - data_y_min
                if range_height <= 0:
                    range_height = 10.0
                new_y_min = depth - range_height / 2
                new_y_max = depth + range_height / 2
#                 print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Using fallback centered view")
            
            print(f"DEBUG (PyQtGraphCurvePlotter.scroll_to_depth): Setting range: {new_y_min:.2f}-{new_y_max:.2f}")
            
            # Apply the new range
            self.setYRange(new_y_min, new_y_max)
            
            # Update stored depth range
            self.min_depth = new_y_min
            self.max_depth = new_y_max
            
            # Emit view range changed signal for synchronization
            self.viewRangeChanged.emit(new_y_min, new_y_max)
            
        finally:
            self.sync_tracker.end_sync()
    def on_plot_clicked(self, event):
        """Handle mouse clicks on the plot."""
        if event.button() == Qt.MouseButton.LeftButton:
            pass
            # Get mouse position in plot coordinates
            pos = event.scenePos()
            if self.plot_widget.plotItem.vb.mapSceneToView(pos):
                view_coords = self.plot_widget.plotItem.vb.mapSceneToView(pos)
                depth = view_coords.y()
                
                # Emit signal with depth value
                self.pointClicked.emit(depth)
                
    def on_view_range_changed(self):
        """Handle view range changes and emit signal for overview synchronization."""
        # Prevent recursion
        if hasattr(self, '_updating_view_range') and self._updating_view_range:
            return
            
        # Use ScrollOptimizer for smooth scrolling if available
        if self.scroll_optimizer and self.performance_monitor_enabled:
            self.scroll_optimizer.handle_view_range_change()
        
        # Check if synchronization should proceed (prevent infinite loops)
        if self.sync_enabled and not self.sync_tracker.should_sync():
            pass
#             print(f"DEBUG (PyQtGraphCurvePlotter.on_view_range_changed): Sync blocked by tracker")
            return
            
        self.sync_tracker.begin_sync()
        
        try:
            view_range = self.plot_widget.viewRange()
            y_min = view_range[1][0]
            y_max = view_range[1][1]
            
            print(f"DEBUG (PyQtGraphCurvePlotter.on_view_range_changed): View range changed to {y_min:.2f}-{y_max:.2f}")
            
            self.viewRangeChanged.emit(y_min, y_max)
            
        finally:
            self.sync_tracker.end_sync()
                
    def get_view_range(self):
        """Get the current visible depth range."""
        view_range = self.plot_widget.viewRange()
        return view_range[1][0], view_range[1][1]  # y_min, y_max
    
    def _get_downsampled_data(self, values, depths, view_range=None, max_points=1000):
        """
        Downsample data for performance optimization.
        
        Args:
            values: Curve values array
            depths: Depth values array
            view_range: (min_depth, max_depth) tuple or None for current view
            max_points: Maximum number of points to keep
            
        Returns:
            Tuple of (downsampled_values, downsampled_depths)
        """
        if len(values) <= max_points:
            return values, depths
            
        # If view_range is provided, prioritize points in visible range
        if view_range and len(view_range) == 2:
            min_depth, max_depth = view_range
            # Find indices in visible range
            in_view_mask = (depths >= min_depth) & (depths <= max_depth)
            in_view_count = np.sum(in_view_mask)
            
            if in_view_count > 0:
                pass
                # Keep more points in visible range
                visible_ratio = min(0.7, in_view_count / len(values))
                visible_points = int(max_points * visible_ratio)
                outside_points = max_points - visible_points
                
                # Sample visible range more densely
                if in_view_count > visible_points:
                    visible_indices = np.where(in_view_mask)[0]
                    step = max(1, in_view_count // visible_points)
                    visible_sample = visible_indices[::step][:visible_points]
                else:
                    visible_sample = np.where(in_view_mask)[0]
                
                # Sample outside range less densely
                outside_indices = np.where(~in_view_mask)[0]
                if len(outside_indices) > outside_points:
                    step = max(1, len(outside_indices) // outside_points)
                    outside_sample = outside_indices[::step][:outside_points]
                else:
                    outside_sample = outside_indices
                
                # Combine samples
                sample_indices = np.sort(np.concatenate([visible_sample, outside_sample]))
                return values[sample_indices], depths[sample_indices]
        
        # Simple uniform sampling if no view range or all points outside
        step = max(1, len(values) // max_points)
        return values[::step], depths[::step]
    
    def _get_viewport_cache_key(self):
        """Generate a cache key for the current viewport state."""
        if not hasattr(self, 'data') or self.data is None or self.data.empty:
            return None
            
        # Get current view range
        view_range = self.get_view_range()
        if not view_range:
            return None
            
        # Get curve configuration signature
        config_signature = self._get_curve_config_signature()
        
        # Combine into cache key
        cache_key = f"{view_range[0]:.2f}-{view_range[1]:.2f}-{config_signature}"
        return cache_key
    
    def _get_curve_config_signature(self):
        """Generate a signature for current curve configurations."""
        if not self.curve_configs:
            return "no-curves"
        
        # Create a simple hash of curve configurations
        config_strings = []
        for config in sorted(self.curve_configs, key=lambda x: x.get('name', '')):
            config_str = f"{config.get('name', '')}:{config.get('visible', True)}:{config.get('color', '')}:{config.get('line_style', 'solid')}:{config.get('thickness', 1.0)}"
            config_strings.append(config_str)
        
        return hash(tuple(config_strings)) % 1000000
        
    def view_range_changed(self):
        """Signal handler for view range changes (for synchronization with overview)."""
        # This can be connected to external signals
        pass
        
    def set_sync_enabled(self, enabled):
        """Enable or disable synchronization with stratigraphic column."""
        self.sync_enabled = enabled
#         print(f"DEBUG (PyQtGraphCurvePlotter.set_sync_enabled): Sync enabled = {enabled}")
    
    def wheelEvent(self, event):
        """Handle wheel events for vertical scrolling (or zoom with Ctrl)."""
        # Check for Ctrl modifier for zoom
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            pass
            # Let PyQtGraph handle zoom (default behavior)
            super().wheelEvent(event)
            return
        
        # Normal wheel scroll: move view vertically
        delta = event.angleDelta().y()
        if delta == 0:
            pass
            # Horizontal wheel, ignore
            return
        
        # Get current view range
        view_range = self.plot_widget.viewRange()
        y_min, y_max = view_range[1]
        visible_height = y_max - y_min
        
        # Scroll step: move by 10% of visible height per wheel step
        scroll_factor = 0.1
        scroll_amount = visible_height * scroll_factor * (delta / 120.0)  # delta typically 120 per step
        
        # Apply new range
        new_y_min = y_min + scroll_amount
        new_y_max = y_max + scroll_amount
        
        # Ensure we stay within data bounds if data is loaded
        if self.data is not None and not self.data.empty:
            data_min = self.data[self.depth_column].min()
            data_max = self.data[self.depth_column].max()
            # If new range exceeds bounds, adjust
            if new_y_min < data_min:
                offset = data_min - new_y_min
                new_y_min += offset
                new_y_max += offset
            if new_y_max > data_max:
                offset = new_y_max - data_max
                new_y_min -= offset
                new_y_max -= offset
        
        # Apply the new Y range (this will emit viewRangeChanged signal)
        self.setYRange(new_y_min, new_y_max)
        
        # Accept the event
        event.accept()
    
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
            pass
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
            pass
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
            pass
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
            pass
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
        Set visibility of a curve by name with enhanced functionality.
        
        Enhanced features:
        1. Better curve name matching with pattern recognition
        2. Support for curve groups (gamma, density, etc.)
        3. Legend synchronization
        4. Optional persistence layer integration
        
        Args:
            curve_name: Internal curve name (e.g., 'short_space_density', 'gamma', etc.)
                      Can also be a group name: 'all_gamma', 'all_density', 'all'
            visible: True to show the curve, False to hide it
        """
        # Validate curve_name is a string, handle method objects
        if not isinstance(curve_name, str):
            print(f"ERROR (set_curve_visibility): curve_name must be string, got {type(curve_name)}: {curve_name}")
            # Try to convert to string if it's a method or callable
            if hasattr(curve_name, '__name__'):
                curve_name = curve_name.__name__
            elif callable(curve_name):
                try:
                    curve_name = str(curve_name())
                except:
                    curve_name = str(curve_name)
            else:
                curve_name = str(curve_name)
            print(f"DEBUG (set_curve_visibility): Converted to string: {curve_name}")
            
        # Check if this is a group toggle request
        if curve_name.startswith('all_'):
            group_name = curve_name[4:]  # Remove 'all_' prefix
            self._set_group_visibility(group_name, visible)
            return
        
        # Map internal curve names to actual curve column names
        # This mapping might need to be adjusted based on actual data column names
        curve_name_mapping = {
            'short_space_density': ['SS', 'DENS', 'RHOB', 'short_space_density', 'density', 'short', 'ss_density'],
            'long_space_density': ['LS', 'LSD', 'long_space_density', 'long', 'ls_density'],
            'gamma': ['GR', 'gamma', 'gamma_ray', 'Gamma', 'GAMMA', 'GRAPI', 'gapi'],
            'cd': ['CD', 'cd', 'caliper', 'Caliper', 'CALI', 'caliper_diameter'],
            'res': ['RES', 'resistivity', 'res', 'Resistivity', 'RT', 'ILD', 'ild'],
            'cal': ['CAL', 'cal', 'caliper', 'Caliper', 'CALI', 'caliper_diameter'],
            'neutron': ['NEUT', 'neutron', 'NPHI', 'nphi', 'neutron_porosity'],
            'sonic': ['DT', 'dt', 'sonic', 'AC', 'ac', 'sonic_transit_time'],
            'sp': ['SP', 'sp', 'spontaneous_potential']
        }
        
        # Get possible column names for this curve type
        possible_names = curve_name_mapping.get(curve_name, [curve_name])
        
        # Track if we found and updated any curves
        curves_updated = []
        
        # Try to find the curve by checking all possible names
        for name in possible_names:
            if name in self.curve_items:
                found_curve = self.curve_items[name]
                self._update_curve_visibility(found_curve, visible, name)
                curves_updated.append(name)
        
        # If not found by exact name, try case-insensitive and partial matching
        if not curves_updated and self.curve_items:
            curve_name_lower = curve_name.lower()
            for stored_name, curve_item in self.curve_items.items():
                stored_lower = stored_name.lower()
                
                # Check for direct match or partial match
                if (curve_name_lower == stored_lower or 
                    curve_name_lower in stored_lower or 
                    stored_lower in curve_name_lower):
                    
                    self._update_curve_visibility(curve_item, visible, stored_name)
                    curves_updated.append(stored_name)
        
        # Also check gamma_curves, density_curves, caliper_curves, and resistivity_curves lists
        if not curves_updated:
            pass
            # Check gamma curves
            if hasattr(self, 'gamma_curves'):
                for curve in self.gamma_curves:
                    if hasattr(curve, 'name') and curve.name.lower() == curve_name.lower():
                        self._update_curve_visibility(curve, visible, curve.name)
                        curves_updated.append(curve.name)
            
            # Check density curves
            if hasattr(self, 'density_curves'):
                for curve in self.density_curves:
                    if hasattr(curve, 'name') and curve.name.lower() == curve_name.lower():
                        self._update_curve_visibility(curve, visible, curve.name)
                        curves_updated.append(curve.name)
            
            # Check caliper curves
            if hasattr(self, 'caliper_curves'):
                for curve in self.caliper_curves:
                    if hasattr(curve, 'name') and curve.name.lower() == curve_name.lower():
                        self._update_curve_visibility(curve, visible, curve.name)
                        curves_updated.append(curve.name)
            
            # Check resistivity curves
            if hasattr(self, 'resistivity_curves'):
                for curve in self.resistivity_curves:
                    if hasattr(curve, 'name') and curve.name.lower() == curve_name.lower():
                        self._update_curve_visibility(curve, visible, curve.name)
                        curves_updated.append(curve.name)
        
        # Log results
        if curves_updated:
            print(f"Curve visibility updated for '{curve_name}': {curves_updated} -> {visible}")
        else:
            print(f"Warning: Curve '{curve_name}' not found in plot. Available curves: {list(self.curve_items.keys())}")
    
    def _update_curve_visibility(self, curve_item, visible: bool, curve_name: str):
        """Update visibility of a single curve item."""
        # Set visibility of the curve item
        curve_item.setVisible(visible)
        
        # NO LEGEND SYNCHRONIZATION - We never want a legend to appear
        # Accessing plot_item.legend can automatically create a legend in pyqtgraph
        # So we must never check or update the legend
    
    def _set_group_visibility(self, group_name: str, visible: bool):
        """Set visibility for an entire group of curves."""
        group_name_lower = group_name.lower()
        
        # Define curve groups with their patterns
        curve_groups = {
            'gamma': ['gamma', 'gr', 'gammaray', 'gapi'],
            'density': ['density', 'den', 'rhob', 'ss', 'ls', 'short', 'long'],
            'caliper': ['caliper', 'cal', 'cd', 'diameter'],
            'resistivity': ['resistivity', 'res', 'rt', 'ild'],
            'neutron': ['neutron', 'neut', 'nphi'],
            'sonic': ['sonic', 'dt', 'ac'],
            'sp': ['sp', 'spontaneous_potential'],
            'all': []  # Special case for all curves
        }
        
        # Get patterns for the requested group
        if group_name_lower not in curve_groups:
            pass
#             print(f"Warning: Unknown curve group '{group_name}'")
            return
        
        patterns = curve_groups[group_name_lower]
        curves_updated = []
        
        # Handle 'all' group specially
        if group_name_lower == 'all':
            for curve_name, curve_item in self.curve_items.items():
                self._update_curve_visibility(curve_item, visible, curve_name)
                curves_updated.append(curve_name)
        else:
            # Update curves matching group patterns
            for curve_name, curve_item in self.curve_items.items():
                curve_name_lower = curve_name.lower()
                
                # Check if curve matches any pattern in the group
                if any(pattern in curve_name_lower for pattern in patterns):
                    self._update_curve_visibility(curve_item, visible, curve_name)
                    curves_updated.append(curve_name)
        
        # Also check gamma_curves, density_curves, caliper_curves, resistivity_curves lists for respective groups
        if group_name_lower == 'gamma' and hasattr(self, 'gamma_curves'):
            for curve in self.gamma_curves:
                if hasattr(curve, 'name'):
                    self._update_curve_visibility(curve, visible, curve.name)
                    curves_updated.append(curve.name)
        
        if group_name_lower == 'density' and hasattr(self, 'density_curves'):
            for curve in self.density_curves:
                if hasattr(curve, 'name'):
                    self._update_curve_visibility(curve, visible, curve.name)
                    curves_updated.append(curve.name)
        
        if group_name_lower == 'caliper' and hasattr(self, 'caliper_curves'):
            for curve in self.caliper_curves:
                if hasattr(curve, 'name'):
                    self._update_curve_visibility(curve, visible, curve.name)
                    curves_updated.append(curve.name)
        
        if group_name_lower == 'resistivity' and hasattr(self, 'resistivity_curves'):
            for curve in self.resistivity_curves:
                if hasattr(curve, 'name'):
                    self._update_curve_visibility(curve, visible, curve.name)
                    curves_updated.append(curve.name)
        
#         print(f"Group '{group_name}' visibility set to {visible}. Updated {len(curves_updated)} curves.")
    
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
                pass
                # Start of anomaly interval
                in_anomaly = True
                start_idx = i
            elif not is_anomaly and in_anomaly:
                pass
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
            pass
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
        
    # =========================================================================
    # Zoom State Management Methods
    # =========================================================================
    
    def set_zoom_state_manager(self, zoom_manager):
        """Set the zoom state manager for synchronization."""
        self.zoom_state_manager = zoom_manager
        if self.zoom_state_manager:
            pass
            # Connect signals
            self.zoom_state_manager.zoomStateChanged.connect(self._on_zoom_state_changed)
            self.zoom_state_manager.zoomLevelChanged.connect(self._on_zoom_level_changed)
            self.zoom_state_manager.depthScaleChanged.connect(self._on_depth_scale_changed)
            
            # Connect engineering scale signal if available
            if hasattr(self.zoom_state_manager, 'engineeringScaleChanged'):
                self.zoom_state_manager.engineeringScaleChanged.connect(self._on_engineering_scale_changed)
            
#             print(f"DEBUG (PyQtGraphCurvePlotter): Zoom state manager set")
    
    def _on_engineering_scale_changed(self, scale_label, pixels_per_metre):
        """Handle engineering scale changes."""
        self.depth_scale = pixels_per_metre
        self.current_scale_label = scale_label
        
        # Update scale display
        self.update_scale_display()
        
        print(f"DEBUG (PyQtGraphCurvePlotter): Engineering scale changed: {scale_label} ({pixels_per_metre:.1f} px/m)")
            
    def _on_zoom_state_changed(self, center_depth, min_depth, max_depth):
        """Handle zoom state changes from zoom manager."""
        if not self.is_zooming:
            self.is_zooming = True
            try:
                # Update view range
                self.setYRange(min_depth, max_depth)
                # print(f"DEBUG (PyQtGraphCurvePlotter): Zoom state applied: "
                #       f"range=[{min_depth:.2f}, {max_depth:.2f}], center={center_depth:.2f}")
            finally:
                self.is_zooming = False
                
    def _on_zoom_level_changed(self, zoom_factor):
        """Handle zoom level changes from zoom manager."""
        self.current_zoom_factor = zoom_factor
        self.zoomLevelChanged.emit(zoom_factor)
        print(f"DEBUG (PyQtGraphCurvePlotter): Zoom level changed: {zoom_factor:.2f}")
        
    def _on_depth_scale_changed(self, depth_scale, scale_label=None):
        """Handle depth scale changes from zoom manager."""
        if depth_scale > 0:
            self.depth_scale = depth_scale
            self.current_scale_label = scale_label or f"{depth_scale:.1f} px/m"
            
            # Update scale display if available
            self.update_scale_display()
            
#             print(f"DEBUG (PyQtGraphCurvePlotter): Depth scale changed: {depth_scale} ({self.current_scale_label})")
    
    def update_scale_display(self):
        """Update the scale display in the plot."""
        # Create or update scale text item
        if not hasattr(self, 'scale_text_item'):
            pass
            # Create scale text item
            self.scale_text_item = pg.TextItem(
                text="",
                color=(0, 0, 0),  # Black
                anchor=(1, 1)  # Bottom-right corner
            )
            self.plot_widget.addItem(self.scale_text_item)
        
        # Set scale text
        scale_text = f"Scale: {self.current_scale_label}"
        self.scale_text_item.setText(scale_text)
        
        # Position in bottom-right corner
        view_range = self.plot_widget.viewRange()
        if view_range and len(view_range) > 1:
            x_min, x_max = view_range[0]
            y_min, y_max = view_range[1]
            
            # Position at bottom-right with padding
            self.scale_text_item.setPos(x_max - 10, y_min + 10)
            
    def get_zoom_factor(self):
        """Get current zoom factor."""
        return self.current_zoom_factor
        
    def set_fixed_scale_enabled(self, enabled):
        """Enable or disable fixed scale (prevent scale changes during scrolling)."""
        self.fixed_scale_enabled = enabled
        print(f"DEBUG (PyQtGraphCurvePlotter): Fixed scale {'enabled' if enabled else 'disabled'}")
        
    # =========================================================================
    # Phase 3 Performance Monitoring Methods
    # =========================================================================
    
    def get_performance_metrics(self):
        """Get performance metrics from all Phase 3 components."""
        metrics = {
            'performance_monitor_enabled': self.performance_monitor_enabled,
            'data_stream_manager': None,
            'viewport_cache_manager': None,
            'scroll_optimizer': None
        }
        
        if self.data_stream_manager:
            metrics['data_stream_manager'] = {
                'cache_hit_rate': self.data_stream_manager.get_cache_hit_rate(),
                'memory_usage_mb': self.data_stream_manager.get_memory_usage_mb(),
                'active_chunks': self.data_stream_manager.get_active_chunk_count(),
                'loading_strategy': str(self.data_stream_manager.loading_strategy)
            }
            
        if self.viewport_cache_manager:
            metrics['viewport_cache_manager'] = {
                'cache_hit_rate': self.viewport_cache_manager.get_cache_hit_rate(),
                'cache_size': self.viewport_cache_manager.get_cache_size(),
                'gpu_acceleration': self.viewport_cache_manager.gpu_acceleration,
                'items_cached': len(self.viewport_cache_manager.get_cached_items())
            }
            
        if self.scroll_optimizer:
            metrics['scroll_optimizer'] = {
                'current_fps': self.scroll_optimizer.get_current_fps(),
                'target_fps': self.scroll_optimizer.target_fps,
                'event_batching': self.scroll_optimizer.event_batching,
                'predictive_rendering': self.scroll_optimizer.predictive_rendering,
                'smooth_scrolling': self.scroll_optimizer.smooth_scrolling
            }
            
        return metrics
        
    def print_performance_report(self):
        """Print a performance report to console."""
        if not self.performance_monitor_enabled:
            pass
#             print("Performance monitoring is disabled")
            return
            
        metrics = self.get_performance_metrics()
        
        print("\n" + "="*60)
#         print("PHASE 3 PERFORMANCE REPORT")
        print("="*60)
        
#         print(f"\nPerformance Monitoring: {'ENABLED' if metrics['performance_monitor_enabled'] else 'DISABLED'}")
        
        if metrics['data_stream_manager']:
            ds_metrics = metrics['data_stream_manager']
            print(f"\nDataStreamManager:")
#             print(f"  • Cache Hit Rate: {ds_metrics['cache_hit_rate']:.1%}")
            print(f"  • Memory Usage: {ds_metrics['memory_usage_mb']:.1f} MB")
#             print(f"  • Active Chunks: {ds_metrics['active_chunks']}")
            print(f"  • Loading Strategy: {ds_metrics['loading_strategy']}")
            
        if metrics['viewport_cache_manager']:
            vc_metrics = metrics['viewport_cache_manager']
#             print(f"\nViewportCacheManager:")
            print(f"  • Cache Hit Rate: {vc_metrics['cache_hit_rate']:.1%}")
#             print(f"  • Cache Size: {vc_metrics['cache_size']}")
            print(f"  • GPU Acceleration: {'ENABLED' if vc_metrics['gpu_acceleration'] else 'DISABLED'}")
#             print(f"  • Items Cached: {vc_metrics['items_cached']}")
            
        if metrics['scroll_optimizer']:
            so_metrics = metrics['scroll_optimizer']
            print(f"\nScrollOptimizer:")
#             print(f"  • Current FPS: {so_metrics['current_fps']:.1f}")
            print(f"  • Target FPS: {so_metrics['target_fps']}")
#             print(f"  • Event Batching: {'ENABLED' if so_metrics['event_batching'] else 'DISABLED'}")
            print(f"  • Predictive Rendering: {'ENABLED' if so_metrics['predictive_rendering'] else 'DISABLED'}")
#             print(f"  • Smooth Scrolling: {'ENABLED' if so_metrics['smooth_scrolling'] else 'DISABLED'}")
            
        print("\n" + "="*60)
        
    def enable_performance_monitoring(self, enable=True):
        """Enable or disable performance monitoring."""
        self.performance_monitor_enabled = enable
#         print(f"Performance monitoring {'enabled' if enable else 'disabled'}")
        
    def cleanup_performance_components(self):
        """Clean up Phase 3 performance components."""
        if self.data_stream_manager:
            self.data_stream_manager.cleanup()
            self.data_stream_manager = None
            
        if self.viewport_cache_manager:
            self.viewport_cache_manager.cleanup()
            self.viewport_cache_manager = None
            
        if self.scroll_optimizer:
            self.scroll_optimizer.disconnect_widget()
            self.scroll_optimizer = None
            
        self.performance_monitor_enabled = False
        print("Phase 3 performance components cleaned up")
        
    def setYRange(self, min_depth, max_depth, padding=0):
        """
        Override setYRange to add fixed scale enforcement and debug logging.
        
        Args:
            min_depth: Minimum Y value
            max_depth: Maximum Y value
            padding: Optional padding
        """
        # Ensure valid range
        if min_depth >= max_depth:
            print(f"ERROR (PyQtGraphCurvePlotter): Invalid range in setYRange: {min_depth} >= {max_depth}")
            return
            
        # Apply fixed scale if enabled
        if self.fixed_scale_enabled and hasattr(self, 'depth_scale'):
            pass
            # Calculate expected pixel height based on depth scale
            expected_pixel_height = (max_depth - min_depth) * self.depth_scale
            actual_pixel_height = self.plot_widget.height()
            
            # Adjust range to maintain fixed scale if needed
            if abs(expected_pixel_height - actual_pixel_height) > 10:  # 10 pixel tolerance
                pass
#                 print(f"DEBUG (PyQtGraphCurvePlotter): Adjusting range to maintain fixed scale")
                # Recalculate range based on actual pixel height and depth scale
                adjusted_range = actual_pixel_height / self.depth_scale
                center = (min_depth + max_depth) / 2
                min_depth = center - adjusted_range / 2
                max_depth = center + adjusted_range / 2
                
        # Set recursion protection flag
        self._updating_view_range = True
        
        try:
            # Call parent method
            self.plot_widget.setYRange(min_depth, max_depth, padding)
            
            # Update stored depth range
            self.min_depth = min_depth
            self.max_depth = max_depth
            
            # Update Y-axis ticks for whole metre increments
            self.update_y_axis_ticks()
            
            # Update X-axis labels position
            self.update_x_axis_labels_position()
            
            # Emit view range changed signal
            self.viewRangeChanged.emit(min_depth, max_depth)
            
            print(f"DEBUG (PyQtGraphCurvePlotter): setYRange called: [{min_depth:.2f}, {max_depth:.2f}]")
        finally:
            # Clear recursion protection flag
            self._updating_view_range = False