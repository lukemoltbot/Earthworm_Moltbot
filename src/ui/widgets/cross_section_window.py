"""
CrossSectionWindow - Interactive fence diagram (cross-section) window.
Part of Phase 5: GIS & Cross-Sections implementation.
"""

import numpy as np
import pandas as pd
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QFrame,
    QSizePolicy, QMessageBox, QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtGui import QColor, QPen, QFont, QBrush, QPainter, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer, QSize
import pyqtgraph as pg

from .stratigraphic_column import StratigraphicColumn
from .map_window import MapWindow  # For coordinate extraction


class CrossSectionWindow(QWidget):
    """
    Interactive cross-section (fence diagram) window.
    
    Features:
    - Takes 3+ selected holes (from map or list)
    - Calculates true spacing using Pythagorean theorem on coordinates
    - Plots holes side-by-side as vertical stratigraphic columns
    - Draws connecting polygons for common seam names
    - Allows interactive adjustment of seam correlation
    """
    
    # Signal emitted when cross-section parameters change
    parametersChanged = pyqtSignal(dict)
    
    def __init__(self, hole_file_paths=None, parent=None):
        """
        Initialize cross-section window.
        
        Args:
            hole_file_paths: List of hole file paths to include in cross-section
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Data storage
        self.hole_file_paths = hole_file_paths or []
        self.hole_data = {}  # file_path -> dict with hole info and dataframe
        self.hole_coordinates = {}  # file_path -> (easting, northing)
        self.hole_spacings = []  # List of distances between consecutive holes
        self.hole_positions = {}  # file_path -> x_position in cross-section
        
        # Cross-section configuration
        self.vertical_exaggeration = 1.0
        self.column_width = 70  # pixels per column
        self.spacing_factor = 100.0  # pixels per meter between holes
        self.show_polygons = True
        self.show_labels = True
        self.color_by = "lithology"  # "lithology", "seam", "property"
        
        # UI elements
        self.strat_columns = {}  # file_path -> StratigraphicColumn widget
        self.column_widgets = {}  # file_path -> container widget
        self.polygon_items = []  # List of polygon graphic items
        
        # Initialize UI
        self.setup_ui()
        
        # Load hole data if provided
        if self.hole_file_paths:
            self.load_holes(self.hole_file_paths)
    
    def setup_ui(self):
        """Setup the cross-section window UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Vertical exaggeration control
        toolbar_layout.addWidget(QLabel("Vertical Exaggeration:"))
        self.vex_spin = QDoubleSpinBox()
        self.vex_spin.setRange(0.1, 10.0)
        self.vex_spin.setValue(self.vertical_exaggeration)
        self.vex_spin.setSingleStep(0.1)
        self.vex_spin.valueChanged.connect(self.update_vertical_exaggeration)
        toolbar_layout.addWidget(self.vex_spin)
        
        # Column width control
        toolbar_layout.addWidget(QLabel("Column Width:"))
        self.col_width_spin = QSpinBox()
        self.col_width_spin.setRange(30, 200)
        self.col_width_spin.setValue(self.column_width)
        self.col_width_spin.valueChanged.connect(self.update_column_width)
        toolbar_layout.addWidget(self.col_width_spin)
        
        # Spacing factor control
        toolbar_layout.addWidget(QLabel("Spacing Factor:"))
        self.spacing_spin = QDoubleSpinBox()
        self.spacing_spin.setRange(1.0, 1000.0)
        self.spacing_spin.setValue(self.spacing_factor)
        self.spacing_spin.setSingleStep(10.0)
        self.spacing_spin.valueChanged.connect(self.update_spacing_factor)
        toolbar_layout.addWidget(self.spacing_spin)
        
        # Color by combo box
        toolbar_layout.addWidget(QLabel("Color by:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Lithology", "Seam Name", "Weathering", "Strength"])
        self.color_combo.currentTextChanged.connect(self.update_colors)
        toolbar_layout.addWidget(self.color_combo)
        
        # Show polygons checkbox
        self.polygons_check = QCheckBox("Show Polygons")
        self.polygons_check.setChecked(self.show_polygons)
        self.polygons_check.toggled.connect(self.toggle_polygons)
        toolbar_layout.addWidget(self.polygons_check)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Create splitter for columns and controls
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: hole list and controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Hole list
        left_layout.addWidget(QLabel("Holes in Cross-Section:"))
        self.hole_list = QListWidget()
        self.hole_list.itemSelectionChanged.connect(self.on_hole_selection_changed)
        left_layout.addWidget(self.hole_list)
        
        # Hole controls
        controls_group = QGroupBox("Hole Controls")
        controls_layout = QVBoxLayout()
        
        up_button = QPushButton("Move Up")
        up_button.clicked.connect(self.move_hole_up)
        controls_layout.addWidget(up_button)
        
        down_button = QPushButton("Move Down")
        down_button.clicked.connect(self.move_hole_down)
        controls_layout.addWidget(down_button)
        
        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected_hole)
        controls_layout.addWidget(remove_button)
        
        controls_group.setLayout(controls_layout)
        left_layout.addWidget(controls_group)
        
        # Spacing info
        info_group = QGroupBox("Spacing Information")
        info_layout = QVBoxLayout()
        self.spacing_label = QLabel("Spacing: Not calculated")
        info_layout.addWidget(self.spacing_label)
        info_group.setLayout(info_layout)
        left_layout.addWidget(info_group)
        
        left_layout.addStretch()
        self.splitter.addWidget(left_panel)
        
        # Right panel: cross-section visualization
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create graphics view for cross-section
        self.graphics_view = pg.GraphicsView()
        self.graphics_scene = pg.GraphicsLayout()
        self.graphics_view.setCentralItem(self.graphics_scene)
        
        # Create main plot for cross-section
        self.cross_section_plot = self.graphics_scene.addPlot(title="Cross-Section")
        self.cross_section_plot.setLabel('left', 'Depth', units='m')
        self.cross_section_plot.setLabel('bottom', 'Distance', units='m')
        self.cross_section_plot.showGrid(x=True, y=True, alpha=0.3)
        self.cross_section_plot.setAspectLocked(False)
        
        # Enable mouse interaction
        self.cross_section_plot.setMouseEnabled(x=True, y=True)
        
        right_layout.addWidget(self.graphics_view)
        self.splitter.addWidget(right_panel)
        
        # Set splitter sizes
        self.splitter.setSizes([200, 800])
        
        main_layout.addWidget(self.splitter)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.hole_count_label = QLabel("Holes: 0")
        status_layout.addWidget(self.hole_count_label)
        
        main_layout.addLayout(status_layout)
    
    def load_holes(self, file_paths):
        """
        Load holes into cross-section.
        
        Args:
            file_paths: List of hole file paths
        """
        self.hole_file_paths = file_paths
        self.hole_data.clear()
        self.hole_coordinates.clear()
        
        # Extract coordinates and load data for each hole
        for file_path in file_paths:
            # Extract coordinates using MapWindow's method
            hole_info = MapWindow.extract_coordinates_from_file(MapWindow(), file_path)
            if hole_info and hole_info.get('easting') is not None and hole_info.get('northing') is not None:
                self.hole_coordinates[file_path] = (
                    hole_info.get('easting'),
                    hole_info.get('northing')
                )
                # TODO: Load hole data (dataframe) from file
                # For now, store basic info
                self.hole_data[file_path] = {
                    'info': hole_info,
                    'dataframe': None,  # Will be loaded later
                    'hole_id': hole_info.get('hole_id', os.path.basename(file_path))
                }
        
        # Calculate true spacing and positions
        self.calculate_spacing_and_positions()
        
        # Update UI
        self.update_hole_list()
        self.update_cross_section_plot()
        
        # Update status
        self.status_label.setText(f"Loaded {len(self.hole_data)} holes")
        self.hole_count_label.setText(f"Holes: {len(self.hole_data)}")
    
    def calculate_spacing_and_positions(self):
        """Calculate true spacing between holes and their x-positions."""
        if len(self.hole_file_paths) < 2:
            self.hole_spacings = []
            self.hole_positions = {path: 0 for path in self.hole_file_paths}
            return
        
        # Calculate distances between consecutive holes
        self.hole_spacings = []
        total_distance = 0
        
        # Start with first hole at position 0
        self.hole_positions = {self.hole_file_paths[0]: 0}
        
        for i in range(1, len(self.hole_file_paths)):
            path1 = self.hole_file_paths[i-1]
            path2 = self.hole_file_paths[i]
            
            if path1 in self.hole_coordinates and path2 in self.hole_coordinates:
                x1, y1 = self.hole_coordinates[path1]
                x2, y2 = self.hole_coordinates[path2]
                
                # Pythagorean theorem for true distance
                distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                self.hole_spacings.append(distance)
                total_distance += distance
                
                # Position is cumulative distance
                self.hole_positions[path2] = total_distance
            else:
                # If coordinates missing, use arbitrary spacing
                self.hole_spacings.append(100.0)  # 100m default
                total_distance += 100.0
                self.hole_positions[path2] = total_distance
        
        # Update spacing label
        if self.hole_spacings:
            avg_spacing = np.mean(self.hole_spacings)
            self.spacing_label.setText(f"Spacing: {avg_spacing:.1f} m avg, {total_distance:.1f} m total")
    
    def update_hole_list(self):
        """Update the hole list widget."""
        self.hole_list.clear()
        for file_path in self.hole_file_paths:
            hole_id = self.hole_data.get(file_path, {}).get('hole_id', os.path.basename(file_path))
            item = QListWidgetItem(hole_id)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.hole_list.addItem(item)
    
    def update_cross_section_plot(self):
        """Update the cross-section plot with current holes."""
        # Clear existing plot items
        self.cross_section_plot.clear()
        self.polygon_items.clear()
        
        if not self.hole_data:
            return
        
        # Plot each hole as a vertical column
        for file_path, hole_info in self.hole_data.items():
            if file_path not in self.hole_positions:
                continue
                
            x_pos = self.hole_positions[file_path]
            # TODO: Draw stratigraphic column at x_pos
            # For now, draw a simple vertical line
            depth_range = hole_info.get('info', {}).get('total_depth', 100.0)
            
            # Draw vertical line for hole
            line = pg.PlotCurveItem(
                x=[x_pos, x_pos],
                y=[0, -depth_range * self.vertical_exaggeration],  # Negative depth (downwards)
                pen=pg.mkPen(QColor(0, 0, 0), width=2)
            )
            self.cross_section_plot.addItem(line)
            
            # Add hole label
            label = pg.TextItem(
                text=hole_info.get('hole_id', 'Unknown'),
                color=(0, 0, 0),
                anchor=(0.5, 1.5)
            )
            label.setPos(x_pos, 0)
            self.cross_section_plot.addItem(label)
        
        # Draw connecting polygons if enabled
        if self.show_polygons and len(self.hole_file_paths) >= 2:
            self.draw_connecting_polygons()
        
        # Auto-range the plot
        self.cross_section_plot.autoRange()
    
    def draw_connecting_polygons(self):
        """Draw polygons connecting common seams across holes."""
        # TODO: Implement seam correlation logic
        # For now, draw simple connecting lines between hole tops/bottoms
        for i in range(len(self.hole_file_paths) - 1):
            path1 = self.hole_file_paths[i]
            path2 = self.hole_file_paths[i+1]
            
            if path1 in self.hole_positions and path2 in self.hole_positions:
                x1 = self.hole_positions[path1]
                x2 = self.hole_positions[path2]
                
                # Connect top of holes
                top_line = pg.PlotCurveItem(
                    x=[x1, x2],
                    y=[0, 0],
                    pen=pg.mkPen(QColor(255, 0, 0, 100), width=1)
                )
                self.cross_section_plot.addItem(top_line)
                self.polygon_items.append(top_line)
                
                # Connect bottom of holes (using max depth)
                depth1 = self.hole_data.get(path1, {}).get('info', {}).get('total_depth', 100.0)
                depth2 = self.hole_data.get(path2, {}).get('info', {}).get('total_depth', 100.0)
                
                bottom_line = pg.PlotCurveItem(
                    x=[x1, x2],
                    y=[-depth1 * self.vertical_exaggeration, -depth2 * self.vertical_exaggeration],
                    pen=pg.mkPen(QColor(0, 0, 255, 100), width=1)
                )
                self.cross_section_plot.addItem(bottom_line)
                self.polygon_items.append(bottom_line)
    
    def update_vertical_exaggeration(self, value):
        """Update vertical exaggeration factor."""
        self.vertical_exaggeration = value
        self.update_cross_section_plot()
        self.parametersChanged.emit({'vertical_exaggeration': value})
    
    def update_column_width(self, value):
        """Update column width."""
        self.column_width = value
        # TODO: Update column widths in visualization
        self.parametersChanged.emit({'column_width': value})
    
    def update_spacing_factor(self, value):
        """Update spacing factor."""
        self.spacing_factor = value
        # Recalculate positions with new spacing factor
        self.calculate_spacing_and_positions()
        self.update_cross_section_plot()
        self.parametersChanged.emit({'spacing_factor': value})
    
    def update_colors(self, color_by):
        """Update color scheme."""
        self.color_by = color_by.lower().replace(' ', '_')
        self.update_cross_section_plot()
        self.parametersChanged.emit({'color_by': color_by})
    
    def toggle_polygons(self, checked):
        """Toggle polygon display."""
        self.show_polygons = checked
        self.update_cross_section_plot()
        self.parametersChanged.emit({'show_polygons': checked})
    
    def on_hole_selection_changed(self):
        """Handle hole selection changes in list."""
        selected_items = self.hole_list.selectedItems()
        if selected_items:
            file_path = selected_items[0].data(Qt.ItemDataRole.UserRole)
            # TODO: Highlight selected hole in cross-section plot
            self.status_label.setText(f"Selected: {os.path.basename(file_path)}")
    
    def move_hole_up(self):
        """Move selected hole up in the order."""
        current_row = self.hole_list.currentRow()
        if current_row > 0:
            # Swap in file paths list
            self.hole_file_paths[current_row], self.hole_file_paths[current_row-1] = \
                self.hole_file_paths[current_row-1], self.hole_file_paths[current_row]
            
            # Recalculate spacing and update UI
            self.calculate_spacing_and_positions()
            self.update_hole_list()
            self.update_cross_section_plot()
            
            # Keep selection
            self.hole_list.setCurrentRow(current_row - 1)
    
    def move_hole_down(self):
        """Move selected hole down in the order."""
        current_row = self.hole_list.currentRow()
        if current_row < len(self.hole_file_paths) - 1:
            # Swap in file paths list
            self.hole_file_paths[current_row], self.hole_file_paths[current_row+1] = \
                self.hole_file_paths[current_row+1], self.hole_file_paths[current_row]
            
            # Recalculate spacing and update UI
            self.calculate_spacing_and_positions()
            self.update_hole_list()
            self.update_cross_section_plot()
            
            # Keep selection
            self.hole_list.setCurrentRow(current_row + 1)
    
    def remove_selected_hole(self):
        """Remove selected hole from cross-section."""
        current_row = self.hole_list.currentRow()
        if current_row >= 0:
            file_path = self.hole_file_paths.pop(current_row)
            
            # Remove from data structures
            if file_path in self.hole_data:
                del self.hole_data[file_path]
            if file_path in self.hole_coordinates:
                del self.hole_coordinates[file_path]
            
            # Recalculate spacing and update UI
            self.calculate_spacing_and_positions()
            self.update_hole_list()
            self.update_cross_section_plot()
    
    def add_hole(self, file_path):
        """Add a hole to the cross-section."""
        if file_path not in self.hole_file_paths:
            self.hole_file_paths.append(file_path)
            self.load_holes(self.hole_file_paths)
    
    def get_parameters(self):
        """Get current cross-section parameters."""
        return {
            'vertical_exaggeration': self.vertical_exaggeration,
            'column_width': self.column_width,
            'spacing_factor': self.spacing_factor,
            'show_polygons': self.show_polygons,
            'color_by': self.color_by,
            'hole_count': len(self.hole_data)
        }