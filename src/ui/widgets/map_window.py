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
    QSizePolicy, QMessageBox, QToolTip, QProgressBar
)
from PyQt6.QtGui import QColor, QPen, QFont, QBrush, QPainter, QPainterPath
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
import pyqtgraph as pg

# Import the worker
from .map_render_worker import MapRenderWorker

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
        
        # Point labels
        self.point_labels = []
        
        # Rendering worker
        self.render_worker = None
        self.is_rendering = False
        self.pending_update = False
        
        # Progressive rendering state
        self.progressive_data = {
            'eastings': [],
            'northings': [],
            'sizes': [],
            'brushes': [],
            'symbols': [],
            'labels': []
        }
        
        # Initialize UI
        self.setup_ui()
    
    def __del__(self):
        """Clean up worker thread."""
        self._cleanup_worker()
    
    def closeEvent(self, event):
        """Handle window close event."""
        self._cleanup_worker()
        super().closeEvent(event)
    
    def _cleanup_worker(self):
        """Clean up the rendering worker."""
        if self.render_worker and self.render_worker.isRunning():
            self.render_worker.cancel()
            self.render_worker.wait()
        
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
        
        # Connect view range changes to update scale bar
        self.plot_widget.sigRangeChanged.connect(self.on_view_range_changed)
        
        # Create scatter plot item with hover events
        self.scatter_plot = pg.ScatterPlotItem(
            size=self.point_size, 
            pen=pg.mkPen(None), 
            brush=pg.mkBrush(self.point_color),
            hoverable=True,
            hoverPen=pg.mkPen(QColor(255, 255, 0), width=2),  # Yellow border on hover
            hoverSize=self.point_size + 2
        )
        self.scatter_plot.sigHovered.connect(self.on_point_hovered)
        self.plot_widget.addItem(self.scatter_plot)
        
        # Create lasso item (initially hidden)
        self.lasso_item = pg.PlotCurveItem(
            pen=pg.mkPen(QColor(255, 165, 0), width=2, style=Qt.PenStyle.DashLine), 
            brush=pg.mkBrush(QColor(255, 165, 0, 30))
        )
        self.plot_widget.addItem(self.lasso_item)
        self.lasso_item.hide()
        
        # Create lasso fill item for better visibility
        self.lasso_fill = pg.PlotCurveItem(
            pen=pg.mkPen(None),
            brush=pg.mkBrush(QColor(255, 165, 0, 20))
        )
        self.plot_widget.addItem(self.lasso_fill)
        self.lasso_fill.hide()
        
        # Create scale bar item
        self.scale_bar = pg.PlotCurveItem(
            pen=pg.mkPen(QColor(0, 0, 0), width=3),
            brush=pg.mkBrush(QColor(0, 0, 0, 100))
        )
        self.plot_widget.addItem(self.scale_bar)
        self.scale_bar.hide()
        
        # Create scale text item
        self.scale_text = pg.TextItem("", color=(0, 0, 0), anchor=(0.5, 1.5))
        self.plot_widget.addItem(self.scale_text)
        self.scale_text.hide()
        
        main_layout.addWidget(self.plot_widget)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # Progress bar for rendering
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
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
        
    def update_plot(self, force_sync=False):
        """
        Update the scatter plot with current hole data.
        
        Args:
            force_sync: If True, force synchronous rendering (for small datasets or testing)
        """
        if not self.hole_data:
            self.scatter_plot.setData([], [])
            self.hole_count_label.setText("Holes: 0")
            self.selected_count_label.setText("Selected: 0")
            self.progress_bar.hide()
            return
        
        # For very small datasets or when forced, use synchronous rendering
        if force_sync or len(self.hole_data) <= 10:
            self._update_plot_sync()
            return
            
        # Check if we're already rendering
        if self.is_rendering:
            self.pending_update = True
            return
            
        # Start rendering in background
        self._start_render_worker()
    
    def _update_plot_sync(self):
        """Synchronous version of update_plot for small datasets."""
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
        labels = []
        
        # Get color by setting
        color_by = self.color_combo.currentText()
        
        for file_path, hole_info in self.hole_data.items():
            easting = hole_info.get('easting', 0)
            northing = hole_info.get('northing', 0)
            
            # Skip holes without coordinates
            if easting is None or northing is None:
                continue
                
            eastings.append(easting)
            northings.append(northing)
            labels.append(hole_info.get('hole_id', os.path.basename(file_path)))
            
            # Determine point color based on selection and color_by setting
            if file_path in self.selected_holes:
                sizes.append(self.selected_point_size)
                brush_color = self.selected_point_color
                symbols.append('o')  # Circle
            else:
                sizes.append(self.point_size)
                brush_color = self.get_color_for_hole(hole_info, color_by)
                symbols.append('o')  # Circle
                
            brushes.append(pg.mkBrush(brush_color))
                
        # Update scatter plot
        self.scatter_plot.setData(x=eastings, y=northings, size=sizes, brush=brushes, symbol=symbols)
        
        # Add labels if there are not too many points
        if len(eastings) <= 50:  # Only show labels for reasonable number of points
            self.add_point_labels(eastings, northings, labels)
        else:
            self.clear_point_labels()
        
        # Update labels
        self.hole_count_label.setText(f"Holes: {len(self.hole_data)}")
        self.selected_count_label.setText(f"Selected: {len(self.selected_holes)}")
        
        # Auto-range if needed
        if eastings and northings:
            self.plot_widget.autoRange()
            # Update scale bar after auto-ranging
            self.update_scale_bar()
    
    def _start_render_worker(self):
        """Start the background rendering worker."""
        # Cancel any existing worker
        if self.render_worker and self.render_worker.isRunning():
            self.render_worker.cancel()
            self.render_worker.wait()
        
        # Reset progressive data
        self.progressive_data = {
            'eastings': [],
            'northings': [],
            'sizes': [],
            'brushes': [],
            'symbols': [],
            'labels': []
        }
        
        # Create new worker
        self.render_worker = MapRenderWorker(
            hole_data=self.hole_data,
            selected_holes=self.selected_holes,
            color_by=self.color_combo.currentText(),
            point_size=self.point_size,
            selected_point_size=self.selected_point_size,
            point_color=self.point_color,
            selected_point_color=self.selected_point_color,
            batch_size=50  # Render 50 points at a time
        )
        
        # Connect signals
        self.render_worker.progress.connect(self._on_render_progress)
        self.render_worker.batch_ready.connect(self._on_batch_ready)
        self.render_worker.data_ready.connect(self._on_data_ready)
        self.render_worker.finished.connect(self._on_render_finished)
        self.render_worker.error.connect(self._on_render_error)
        
        # Update UI state
        self.is_rendering = True
        self.pending_update = False
        self.status_label.setText("Rendering map...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Start worker
        self.render_worker.start()
    
    def _on_render_progress(self, progress):
        """Handle progress updates from the worker."""
        self.progress_bar.setValue(progress)
        
    def _on_batch_ready(self, eastings, northings, sizes, brushes, symbols, labels):
        """Handle batch data from the worker (progressive loading)."""
        # Append batch data
        self.progressive_data['eastings'].extend(eastings)
        self.progressive_data['northings'].extend(northings)
        self.progressive_data['sizes'].extend(sizes)
        self.progressive_data['brushes'].extend(brushes)
        self.progressive_data['symbols'].extend(symbols)
        self.progressive_data['labels'].extend(labels)
        
        # Update plot with current data
        self._update_plot_from_data(self.progressive_data, is_final=False)
        
    def _on_data_ready(self, eastings, northings, sizes, brushes, symbols, labels):
        """Handle complete data from the worker."""
        # Update progressive data
        self.progressive_data = {
            'eastings': eastings,
            'northings': northings,
            'sizes': sizes,
            'brushes': brushes,
            'symbols': symbols,
            'labels': labels
        }
        
        # Update plot with final data
        self._update_plot_from_data(self.progressive_data, is_final=True)
        
    def _update_plot_from_data(self, data, is_final=False):
        """
        Update the scatter plot from prepared data.
        
        Args:
            data: Dict with 'eastings', 'northings', 'sizes', 'brushes', 'symbols', 'labels'
            is_final: Whether this is the final update
        """
        eastings = data['eastings']
        northings = data['northings']
        sizes = data['sizes']
        brushes = data['brushes']
        symbols = data['symbols']
        labels = data['labels']
        
        # Convert brush tuples back to QBrush objects
        brush_objects = []
        for brush_tuple in brushes:
            if isinstance(brush_tuple, tuple):
                # Convert (r, g, b, a) tuple to QBrush
                brush_objects.append(pg.mkBrush(brush_tuple))
            else:
                brush_objects.append(brush_tuple)
        
        # Update scatter plot
        self.scatter_plot.setData(x=eastings, y=northings, size=sizes, brush=brush_objects, symbol=symbols)
        
        # Add labels if there are not too many points (only on final update)
        if is_final and len(eastings) <= 50:
            self.add_point_labels(eastings, northings, labels)
        elif is_final:
            self.clear_point_labels()
        
        # Update labels
        self.hole_count_label.setText(f"Holes: {len(self.hole_data)}")
        self.selected_count_label.setText(f"Selected: {len(self.selected_holes)}")
        
        # Auto-range if needed (only on final update to avoid constant re-ranging)
        if is_final and eastings and northings:
            self.plot_widget.autoRange()
            self.update_scale_bar()
        
    def _on_render_finished(self):
        """Handle worker finished signal."""
        self.is_rendering = False
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
        
        # Check if we have a pending update
        if self.pending_update:
            self.pending_update = False
            self.update_plot()
        else:
            self.status_label.setText("Ready")
    
    def _on_render_error(self, error_message):
        """Handle worker error signal."""
        self.is_rendering = False
        self.progress_bar.hide()
        self.status_label.setText(f"Error: {error_message}")
        
        # Fall back to synchronous rendering
        self._update_plot_sync()
            
    def get_color_for_hole(self, hole_info, color_by):
        """Get color for a hole based on the color_by setting."""
        if color_by == "Default":
            return self.point_color
        elif color_by == "Total Depth":
            return self.get_color_by_depth(hole_info.get('total_depth'))
        elif color_by == "Hole Count":
            # Color by sequence - just for demonstration
            return QColor(70, 130, 180)  # Steel blue
        elif color_by == "File Type":
            # Color by file extension - just for demonstration
            return QColor(100, 149, 237)  # Cornflower blue
        else:
            return self.point_color
            
    def get_color_by_depth(self, depth):
        """Get color based on total depth."""
        if depth is None:
            return self.point_color
            
        # Color gradient from light blue (shallow) to dark blue (deep)
        # Normalize depth to 0-1 range (assuming max depth ~500m)
        normalized = min(depth / 500.0, 1.0)
        
        # Interpolate between light blue and dark blue
        r = int(70 + normalized * 30)  # 70-100
        g = int(130 + normalized * 50)  # 130-180
        b = int(180 + normalized * 75)  # 180-255
        
        return QColor(r, g, b)
        
    def add_point_labels(self, eastings, northings, labels):
        """Add text labels to points."""
        # Clear existing labels
        self.clear_point_labels()
        
        # Create new text items
        self.point_labels = []
        for i, (x, y, label) in enumerate(zip(eastings, northings, labels)):
            text_item = pg.TextItem(label, color=(255, 255, 255), anchor=(0.5, 1.5))
            text_item.setPos(x, y)
            self.plot_widget.addItem(text_item)
            self.point_labels.append(text_item)
            
    def clear_point_labels(self):
        """Clear all point labels."""
        if hasattr(self, 'point_labels'):
            for label in self.point_labels:
                self.plot_widget.removeItem(label)
            self.point_labels = []
            
    def toggle_lasso_mode(self, enabled):
        """Toggle lasso selection mode."""
        self.lasso_mode = enabled
        self.lasso_points.clear()
        self.lasso_item.hide()
        
        if enabled:
            self.status_label.setText("Lasso mode: Click to draw polygon, double-click to finish")
            self.lasso_button.setStyleSheet("background-color: #FFA500; color: black; font-weight: bold;")  # Orange
            # Change cursor to crosshair
            self.plot_widget.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.status_label.setText("Ready")
            self.lasso_button.setStyleSheet("")  # Reset
            # Restore default cursor
            self.plot_widget.setCursor(Qt.CursorShape.ArrowCursor)
            
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
            
            # Update lasso line
            self.lasso_item.setData(x, y)
            self.lasso_item.show()
            
            # Update lasso fill (close the polygon)
            if len(self.lasso_points) >= 3:
                # Close the polygon by repeating the first point
                x_fill = x + [x[0]]
                y_fill = y + [y[0]]
                self.lasso_fill.setData(x_fill, y_fill)
                self.lasso_fill.show()
            else:
                self.lasso_fill.hide()
            
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
        self.lasso_fill.hide()
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
        self.update_plot()
        
    def on_point_hovered(self, points, event):
        """Handle point hover events to show tooltips."""
        if points and len(points) > 0:
            # Get the point index
            point_index = points[0].index()
            
            # Get the corresponding file path
            file_paths = list(self.hole_data.keys())
            if 0 <= point_index < len(file_paths):
                file_path = file_paths[point_index]
                hole_info = self.hole_data[file_path]
                
                # Create tooltip text
                tooltip_text = f"Hole: {hole_info.get('hole_id', 'N/A')}\n"
                tooltip_text += f"Easting: {hole_info.get('easting', 'N/A'):.2f}\n"
                tooltip_text += f"Northing: {hole_info.get('northing', 'N/A'):.2f}\n"
                
                if hole_info.get('total_depth'):
                    tooltip_text += f"Total Depth: {hole_info['total_depth']:.2f}m\n"
                    
                if hole_info.get('elevation'):
                    tooltip_text += f"Elevation: {hole_info['elevation']:.2f}m\n"
                    
                tooltip_text += f"File: {os.path.basename(file_path)}"
                
                # Show tooltip
                QToolTip.showText(event.screenPos().toPoint(), tooltip_text, self.plot_widget)
        else:
            # Hide tooltip when not hovering over a point
            QToolTip.hideText()
        
    def get_selected_holes(self):
        """Get list of selected hole file paths."""
        return list(self.selected_holes)
        
    def set_selected_holes(self, file_paths):
        """
        Set selected holes from external source (e.g., holes list sidebar).
        
        Args:
            file_paths: List of file paths to select
        """
        # Convert to set for efficient operations
        new_selection = set(file_paths)
        
        # Only update if selection has changed
        if new_selection != self.selected_holes:
            self.selected_holes = new_selection
            self.update_plot()
            
            # Emit signal (but don't cause infinite loop)
            # We'll use a flag to prevent re-emission
            if not hasattr(self, '_updating_from_external'):
                self._updating_from_external = True
                try:
                    self.selectionChanged.emit(list(self.selected_holes))
                finally:
                    delattr(self, '_updating_from_external')
                    
    def select_all_holes(self):
        """Select all holes in the map."""
        self.selected_holes = set(self.hole_data.keys())
        self.update_plot()
        self.selectionChanged.emit(list(self.selected_holes))
        
    def deselect_all_holes(self):
        """Deselect all holes in the map."""
        self.selected_holes.clear()
        self.update_plot()
        self.selectionChanged.emit([])
        
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
            hole_info = {
                'file_path': file_path,
                'hole_id': os.path.basename(file_path).replace('.csv', '').replace('.xlsx', '').replace('.las', ''),
                'easting': None,
                'northing': None,
                'total_depth': None,
                'elevation': None,
                'collar_elevation': None
            }
            
            # Handle different file types
            if file_path.lower().endswith('.csv'):
                hole_info = self._extract_from_csv(file_path, hole_info)
            elif file_path.lower().endswith('.las'):
                hole_info = self._extract_from_las(file_path, hole_info)
            elif file_path.lower().endswith('.xlsx'):
                hole_info = self._extract_from_excel(file_path, hole_info)
            else:
                # Try generic text file extraction
                hole_info = self._extract_from_text(file_path, hole_info)
            
            # If coordinates found, return hole info
            if hole_info['easting'] is not None and hole_info['northing'] is not None:
                return hole_info
            else:
                # Return None if no coordinates found
                return None
                
        except Exception as e:
            print(f"Error extracting coordinates from {file_path}: {e}")
            return None
            
    def _extract_from_csv(self, file_path, hole_info):
        """Extract coordinates from CSV file."""
        try:
            # Read file as text to look for header comments
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            return self._extract_from_text_lines(lines, hole_info)
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
            return hole_info
            
    def _extract_from_las(self, file_path, hole_info):
        """Extract coordinates from LAS file."""
        try:
            # Read file as text to look for header section
            with open(file_path, 'r') as f:
                lines = f.readlines()
                
            # LAS files have specific sections
            in_well_section = False
            for line in lines:
                line = line.strip()
                
                # Check for well section
                if line.startswith('~W'):
                    in_well_section = True
                    continue
                elif line.startswith('~') and not line.startswith('~W'):
                    in_well_section = False
                    continue
                    
                if in_well_section and line:
                    # Parse LAS well information
                    parts = line.split('.')
                    if len(parts) >= 2:
                        mnemonic = parts[0].strip()
                        value_part = '.'.join(parts[1:]).strip()
                        
                        # Extract value (remove unit if present)
                        if ':' in value_part:
                            value = value_part.split(':')[0].strip()
                        else:
                            value = value_part
                            
                        # Check for coordinates
                        if mnemonic.upper() in ['X', 'EAST', 'EASTING']:
                            try:
                                hole_info['easting'] = float(value)
                            except ValueError:
                                pass
                        elif mnemonic.upper() in ['Y', 'NORTH', 'NORTHING']:
                            try:
                                hole_info['northing'] = float(value)
                            except ValueError:
                                pass
                        elif mnemonic.upper() in ['ELEV', 'ELEVATION', 'KB', 'GL']:
                            try:
                                hole_info['elevation'] = float(value)
                            except ValueError:
                                pass
                        elif mnemonic.upper() in ['WELL', 'UWI']:
                            hole_info['hole_id'] = value
                            
            return hole_info
        except Exception as e:
            print(f"Error reading LAS {file_path}: {e}")
            return hole_info
            
    def _extract_from_excel(self, file_path, hole_info):
        """Extract coordinates from Excel file."""
        try:
            import pandas as pd
            # Try to read the first few rows as text to find metadata
            df = pd.read_excel(file_path, nrows=10)
            
            # Check for coordinates in column names or first row
            for col in df.columns:
                col_lower = str(col).lower()
                if 'easting' in col_lower or 'x' == col_lower:
                    if not pd.isna(df[col].iloc[0]):
                        try:
                            hole_info['easting'] = float(df[col].iloc[0])
                        except (ValueError, TypeError):
                            pass
                elif 'northing' in col_lower or 'y' == col_lower:
                    if not pd.isna(df[col].iloc[0]):
                        try:
                            hole_info['northing'] = float(df[col].iloc[0])
                        except (ValueError, TypeError):
                            pass
                            
            return hole_info
        except Exception as e:
            print(f"Error reading Excel {file_path}: {e}")
            # Fall back to text extraction
            try:
                with open(file_path, 'rb') as f:
                    # Try to read as text (Excel files are binary, but we'll try)
                    # This is a fallback for very simple Excel files
                    return hole_info
            except:
                return hole_info
                
    def _extract_from_text(self, file_path, hole_info):
        """Extract coordinates from generic text file."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            return self._extract_from_text_lines(lines, hole_info)
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return hole_info
            
    def _extract_from_text_lines(self, lines, hole_info):
        """Extract coordinates from text lines."""
        # Look for coordinate patterns in header comments
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and data rows (starting with numbers or dashes)
            if not line or (line[0].isdigit() if line else False) or (line[0] == '-' if line else False):
                continue
                
            # Check for Easting (various patterns)
            easting_patterns = [
                r'[Ee]asting\s*[:=]\s*([\d\.\-]+)',  # Easting: 500000
                r'[Xx]\s*[:=]\s*([\d\.\-]+)',        # X: 500000
                r'[Ee]asting\s+([\d\.\-]+)',         # Easting 500000
                r'[Xx]\s+([\d\.\-]+)',               # X 500000
                r'EAST\s*[:=]\s*([\d\.\-]+)',        # EAST: 500000
            ]
            
            for pattern in easting_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        hole_info['easting'] = float(match.group(1))
                        break
                    except ValueError:
                        pass
                        
            # Check for Northing (various patterns)
            northing_patterns = [
                r'[Nn]orthing\s*[:=]\s*([\d\.\-]+)',  # Northing: 7000000
                r'[Yy]\s*[:=]\s*([\d\.\-]+)',         # Y: 7000000
                r'[Nn]orthing\s+([\d\.\-]+)',         # Northing 7000000
                r'[Yy]\s+([\d\.\-]+)',                # Y 7000000
                r'NORTH\s*[:=]\s*([\d\.\-]+)',        # NORTH: 7000000
            ]
            
            for pattern in northing_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        hole_info['northing'] = float(match.group(1))
                        break
                    except ValueError:
                        pass
                        
            # Check for Total Depth
            td_patterns = [
                r'[Tt]otal\s*[Dd]epth\s*[:=]\s*([\d\.\-]+)',
                r'[Tt][Dd]\s*[:=]\s*([\d\.\-]+)',
                r'[Ff]inal\s*[Dd]epth\s*[:=]\s*([\d\.\-]+)',
                r'[Ee]nd\s*[Dd]epth\s*[:=]\s*([\d\.\-]+)',
            ]
            
            for pattern in td_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        hole_info['total_depth'] = float(match.group(1))
                        break
                    except ValueError:
                        pass
                        
            # Check for Elevation
            elev_patterns = [
                r'[Ee]levation\s*[:=]\s*([\d\.\-]+)',
                r'[Ee]lev\s*[:=]\s*([\d\.\-]+)',
                r'[Cc]ollar\s*[Ee]levation\s*[:=]\s*([\d\.\-]+)',
                r'[Kk][Bb]\s*[:=]\s*([\d\.\-]+)',  # Kelly Bushing
                r'[Gg][Ll]\s*[:=]\s*([\d\.\-]+)',  # Ground Level
            ]
            
            for pattern in elev_patterns:
                match = re.search(pattern, line)
                if match:
                    try:
                        hole_info['elevation'] = float(match.group(1))
                        break
                    except ValueError:
                        pass
                        
            # Check for Hole ID
            hole_patterns = [
                r'[Hh]ole\s*[:=]\s*([\w\d\-_\.]+)',
                r'[Ww]ell\s*[:=]\s*([\w\d\-_\.]+)',
                r'[Bb]orehole\s*[:=]\s*([\w\d\-_\.]+)',
                r'[Dd]rillhole\s*[:=]\s*([\w\d\-_\.]+)',
                r'[Ii][Dd]\s*[:=]\s*([\w\d\-_\.]+)',
            ]
            
            for pattern in hole_patterns:
                match = re.search(pattern, line)
                if match:
                    hole_info['hole_id'] = match.group(1)
                    break
                    
        return hole_info
    
    def on_view_range_changed(self):
        """Handle view range changes (zooming/panning)."""
        # Cancel any ongoing rendering if user is interacting with the map
        if self.is_rendering and self.render_worker:
            self.render_worker.cancel()
            self.status_label.setText("Rendering cancelled (user interaction)")
        
        self.update_scale_bar()
        
    def update_scale_bar(self):
        """Update the scale bar based on current view range."""
        # Get current view range
        view_range = self.plot_widget.viewRange()
        if not view_range:
            return
            
        x_range = view_range[0]  # [x_min, x_max]
        y_range = view_range[1]  # [y_min, y_max]
        
        # Calculate 10% of the x-range for scale bar length
        x_span = x_range[1] - x_range[0]
        scale_length = x_span * 0.1  # 10% of visible x-range
        
        # Round to nice value (10, 25, 50, 100, 250, 500, etc.)
        nice_length = self._round_to_nice_value(scale_length)
        
        # Position scale bar at bottom-left with some margin
        margin_x = x_range[0] + x_span * 0.05  # 5% from left
        margin_y = y_range[0] + (y_range[1] - y_range[0]) * 0.05  # 5% from bottom
        
        # Create scale bar line
        scale_x = [margin_x, margin_x + nice_length]
        scale_y = [margin_y, margin_y]
        
        self.scale_bar.setData(scale_x, scale_y)
        self.scale_bar.show()
        
        # Add scale text
        scale_text = f"{nice_length:.0f} m"
        self.scale_text.setText(scale_text)
        self.scale_text.setPos(margin_x + nice_length / 2, margin_y)
        self.scale_text.show()
        
    def _round_to_nice_value(self, value):
        """Round a value to a nice round number for scale bar."""
        if value <= 0:
            return 10
            
        # Find order of magnitude
        import numpy as np
        magnitude = 10 ** np.floor(np.log10(value))
        
        # Normalize to 1-10 range
        normalized = value / magnitude
        
        # Round to 1, 2, 5, or 10
        if normalized < 1.5:
            nice = 1
        elif normalized < 3:
            nice = 2
        elif normalized < 7:
            nice = 5
        else:
            nice = 10
            
        return nice * magnitude