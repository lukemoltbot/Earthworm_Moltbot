"""
MapWindow - Interactive map window for displaying hole locations with Easting/Northing coordinates.
Part of Phase 5: GIS & Cross-Sections implementation.
"""

import numpy as np
import pandas as pd
import os
import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton, 
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QFrame,
    QSizePolicy, QMessageBox
)
from PyQt6.QtGui import QColor, QPen, QFont, QBrush, QPainter, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
import pyqtgraph as pg

class MapWindow(QWidget):
    """
    Interactive map window for displaying hole locations.
    
    Features:
    - Scatter plot of hole locations (Easting vs Northing)
    - Lasso (polygon) selection tool
    - Synchronization with Holes List sidebar
    - Color coding based on hole properties
    """
    
    # Signal emitted when hole selection changes
    selectionChanged = pyqtSignal(list)  # List of selected hole file paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data storage
        self.hole_data = {}  # Dict: file_path -> dict with hole info
        self.selected_holes = set()  # Set of selected hole file paths
        
        # Map configuration
        self.point_size = 10
        self.selected_point_size = 15
        self.point_color = QColor(70, 130, 180)  # Steel blue
        self.selected_point_color = QColor(220, 20, 60)  # Crimson red
        
        # Lasso selection state
        self.lasso_mode = False
        self.lasso_points = []
        self.lasso_item = None
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the map window UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Lasso selection button
        self.lasso_button = QPushButton("Lasso Select")
        self.lasso_button.setCheckable(True)
        self.lasso_button.toggled.connect(self.toggle_lasso_mode)
        toolbar_layout.addWidget(self.lasso_button)
        
        # Clear selection button
        clear_button = QPushButton("Clear Selection")
        clear_button.clicked.connect(self.clear_selection)
        toolbar_layout.addWidget(clear_button)
        
        # Point size control
        toolbar_layout.addWidget(QLabel("Point Size:"))
        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(5, 30)
        self.point_size_spin.setValue(self.point_size)
        self.point_size_spin.valueChanged.connect(self.update_point_size)
        toolbar_layout.addWidget(self.point_size_spin)
        
        # Color by combo box
        toolbar_layout.addWidget(QLabel("Color by:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Default", "Total Depth", "Hole Count", "File Type"])
        self.color_combo.currentTextChanged.connect(self.update_colors)
        toolbar_layout.addWidget(self.color_combo)
        
        toolbar_layout.addStretch()
        main_layout.addLayout(toolbar_layout)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', 'Northing', units='m')
        self.plot_widget.setLabel('bottom', 'Easting', units='m')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setAspectLocked(True)  # Keep aspect ratio 1:1
        
        # Enable mouse interaction
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self.plot_widget.scene().sigMouseClicked.connect(self.on_plot_clicked)
        self.plot_widget.scene().sigMouseMoved.connect(self.on_plot_mouse_move)
        
        # Create scatter plot item
        self.scatter_plot = pg.ScatterPlotItem(size=self.point_size, pen=pg.mkPen(None), brush=pg.mkBrush(self.point_color))
        self.plot_widget.addItem(self.scatter_plot)
        
        # Create lasso item (initially hidden)
        self.lasso_item = pg.PlotCurveItem(pen=pg.mkPen(QColor(255, 165, 0), width=2), 
                                          brush=pg.mkBrush(QColor(255, 165, 0, 50)))
        self.plot_widget.addItem(self.lasso_item)
        self.lasso_item.hide()
        
        main_layout.addWidget(self.plot_widget)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        self.hole_count_label = QLabel("Holes: 0")
        status_layout.addWidget(self.hole_count_label)
        
        self.selected_count_label = QLabel("Selected: 0")
        status_layout.addWidget(self.selected_count_label)
        
        main_layout.addLayout(status_layout)
        
    def add_hole(self, file_path, hole_info):
        """
        Add a hole to the map.
        
        Args:
            file_path: Path to the hole file
            hole_info: Dict with hole information including:
                - easting: Easting coordinate (float)
                - northing: Northing coordinate (float)
                - hole_id: Hole identifier (str)
                - total_depth: Total depth (float, optional)
                - other metadata
        """
        self.hole_data[file_path] = hole_info
        self.update_plot()
        
    def remove_hole(self, file_path):
        """Remove a hole from the map."""
        if file_path in self.hole_data:
            del self.hole_data[file_path]
            if file_path in self.selected_holes:
                self.selected_holes.remove(file_path)
            self.update_plot()
            
    def clear_holes(self):
        """Clear all holes from the map."""
        self.hole_data.clear()
        self.selected_holes.clear()
        self.update_plot()
        
    def update_plot(self):
        """Update the scatter plot with current hole data."""
        if not self.hole_data:
            self.scatter_plot.setData([], [])
            self.hole_count_label.setText("Holes: 0")
            self.selected_count_label.setText("Selected: 0")
            return
            
        # Prepare data arrays
        eastings = []
        northings = []
        sizes = []
        brushes = []
        symbols = []
        
        for file_path, hole_info in self.hole_data.items():
            easting = hole_info.get('easting', 0)
            northing = hole_info.get('northing', 0)
            
            # Skip holes without coordinates
            if easting is None or northing is None:
                continue
                
            eastings.append(easting)
            northings.append(northing)
            
            # Set point properties based on selection
            if file_path in self.selected_holes:
                sizes.append(self.selected_point_size)
                brushes.append(pg.mkBrush(self.selected_point_color))
                symbols.append('o')  # Circle
            else:
                sizes.append(self.point_size)
                brushes.append(pg.mkBrush(self.point_color))
                symbols.append('o')  # Circle
                
        # Update scatter plot
        self.scatter_plot.setData(x=eastings, y=northings, size=sizes, brush=brushes, symbol=symbols)
        
        # Update labels
        self.hole_count_label.setText(f"Holes: {len(self.hole_data)}")
        self.selected_count_label.setText(f"Selected: {len(self.selected_holes)}")
        
        # Auto-range if needed
        if eastings and northings:
            self.plot_widget.autoRange()
            
    def toggle_lasso_mode(self, enabled):
        """Toggle lasso selection mode."""
        self.lasso_mode = enabled
        self.lasso_points.clear()
        self.lasso_item.hide()
        
        if enabled:
            self.status_label.setText("Lasso mode: Click to draw polygon, double-click to finish")
            self.lasso_button.setStyleSheet("background-color: #FFA500;")  # Orange
        else:
            self.status_label.setText("Ready")
            self.lasso_button.setStyleSheet("")  # Reset
            
    def on_plot_clicked(self, event):
        """Handle mouse clicks on the plot."""
        if event.double():
            # Double click - finish lasso if in lasso mode
            if self.lasso_mode and len(self.lasso_points) >= 3:
                self.finish_lasso()
            return
            
        if not self.lasso_mode:
            # Single click in normal mode - select/deselect point
            pos = self.plot_widget.plotItem.vb.mapSceneToView(event.scenePos())
            self.select_point_at(pos.x(), pos.y())
        else:
            # Single click in lasso mode - add point to lasso
            pos = self.plot_widget.plotItem.vb.mapSceneToView(event.scenePos())
            self.lasso_points.append(QPointF(pos.x(), pos.y()))
            self.update_lasso_display()
            
    def on_plot_mouse_move(self, pos):
        """Handle mouse movement on the plot."""
        if self.lasso_mode and self.lasso_points:
            # Update temporary lasso line to current mouse position
            view_pos = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            temp_points = self.lasso_points + [QPointF(view_pos.x(), view_pos.y())]
            
            if len(temp_points) >= 2:
                x = [p.x() for p in temp_points]
                y = [p.y() for p in temp_points]
                self.lasso_item.setData(x, y)
                self.lasso_item.show()
                
    def update_lasso_display(self):
        """Update the lasso polygon display."""
        if len(self.lasso_points) >= 2:
            x = [p.x() for p in self.lasso_points]
            y = [p.y() for p in self.lasso_points]
            self.lasso_item.setData(x, y)
            self.lasso_item.show()
            
    def finish_lasso(self):
        """Finish lasso selection and select holes inside polygon."""
        if len(self.lasso_points) < 3:
            return
            
        # Create QPainterPath for polygon
        path = QPainterPath()
        path.moveTo(self.lasso_points[0])
        for point in self.lasso_points[1:]:
            path.lineTo(point)
        path.closeSubpath()
        
        # Find holes inside polygon
        selected = []
        for file_path, hole_info in self.hole_data.items():
            easting = hole_info.get('easting')
            northing = hole_info.get('northing')
            
            if easting is not None and northing is not None:
                if path.contains(QPointF(easting, northing)):
                    selected.append(file_path)
                    
        # Update selection
        self.selected_holes = set(selected)
        self.update_plot()
        
        # Emit selection changed signal
        self.selectionChanged.emit(list(self.selected_holes))
        
        # Reset lasso
        self.toggle_lasso_mode(False)
        self.status_label.setText(f"Selected {len(selected)} holes")
        
    def select_point_at(self, x, y, tolerance=10):
        """
        Select/deselect point near given coordinates.
        
        Args:
            x, y: Coordinates to check
            tolerance: Selection tolerance in plot units
        """
        closest_distance = float('inf')
        closest_file = None
        
        for file_path, hole_info in self.hole_data.items():
            easting = hole_info.get('easting')
            northing = hole_info.get('northing')
            
            if easting is not None and northing is not None:
                distance = np.sqrt((easting - x)**2 + (northing - y)**2)
                if distance < tolerance and distance < closest_distance:
                    closest_distance = distance
                    closest_file = file_path
                    
        if closest_file:
            # Toggle selection
            if closest_file in self.selected_holes:
                self.selected_holes.remove(closest_file)
            else:
                self.selected_holes.add(closest_file)
                
            self.update_plot()
            self.selectionChanged.emit(list(self.selected_holes))
            
    def clear_selection(self):
        """Clear all selections."""
        self.selected_holes.clear()
        self.update_plot()
        self.selectionChanged.emit([])
        self.status_label.setText("Selection cleared")
        
    def update_point_size(self, size):
        """Update point size."""
        self.point_size = size
        self.update_plot()
        
    def update_colors(self, color_by):
        """Update point colors based on selected property."""
        # TODO: Implement color coding based on hole properties
        pass
        
    def get_selected_holes(self):
        """Get list of selected hole file paths."""
        return list(self.selected_holes)
        
    def extract_coordinates_from_file(self, file_path):
        """
        Extract coordinates from a hole file.
        
        Args:
            file_path: Path to the hole file
            
        Returns:
            Dict with easting, northing, hole_id, and other metadata,
            or None if coordinates not found.
        """
        try:
            # Read file as text to look for header comments
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            hole_info = {
                'file_path': file_path,
                'hole_id': os.path.basename(file_path).replace('.csv', '').replace('.xlsx', ''),
                'easting': None,
                'northing': None,
                'total_depth': None
            }
            
            # Look for coordinate patterns in header comments
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and data rows
                if not line or line[0].isdigit() or line[0] == '-':
                    continue
                    
                # Check for Easting
                easting_match = re.search(r'[Ee]asting\s*[:=]\s*([\d\.]+)', line)
                if easting_match:
                    try:
                        hole_info['easting'] = float(easting_match.group(1))
                    except ValueError:
                        pass
                        
                # Check for Northing
                northing_match = re.search(r'[Nn]orthing\s*[:=]\s*([\d\.]+)', line)
                if northing_match:
                    try:
                        hole_info['northing'] = float(northing_match.group(1))
                    except ValueError:
                        pass
                        
                # Check for Total Depth
                td_match = re.search(r'[Tt]otal\s*[Dd]epth\s*[:=]\s*([\d\.]+)', line)
                if td_match:
                    try:
                        hole_info['total_depth'] = float(td_match.group(1))
                    except ValueError:
                        pass
                        
                # Check for Hole ID
                hole_match = re.search(r'[Hh]ole\s*[:=]\s*([\w\d\-_]+)', line)
                if hole_match:
                    hole_info['hole_id'] = hole_match.group(1)
                    
            # If coordinates found, return hole info
            if hole_info['easting'] is not None and hole_info['northing'] is not None:
                return hole_info
            else:
                return None
                
        except Exception as e:
            print(f"Error extracting coordinates from {file_path}: {e}")
            return None