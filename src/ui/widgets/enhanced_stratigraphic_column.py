"""
Enhanced Stratigraphic Column with Real-time LAS Curve Synchronization

This widget extends the base StratigraphicColumn to provide:
1. Real-time vertical scrolling synchronization with LAS curves pane
2. More detailed lithology unit display than overview column
3. Depth synchronization signals/events for bidirectional communication
4. Enhanced unit selection highlighting
5. Integration with existing stratigraphic_column.py base functionality
"""

import os
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsSimpleTextItem
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap, QPen, QLinearGradient
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF, Qt, pyqtSignal, QPointF
import numpy as np
from ...core.config import LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN
from .svg_renderer import SvgRenderer
from .stratigraphic_column import StratigraphicColumn  # Inherit from base class


class EnhancedStratigraphicColumn(StratigraphicColumn):
    """
    Enhanced stratigraphic column with real-time synchronization to LAS curves.
    
    Features:
    - Synchronized vertical scrolling with curve plotter
    - More detailed lithology information display
    - Depth synchronization via signals
    - Enhanced selection highlighting
    - Real-time depth range updates
    """
    
    # Signals for synchronization
    depthRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth (visible range)
    depthScrolled = pyqtSignal(float)  # center_depth (when user scrolls)
    unitSelected = pyqtSignal(int)  # unit_index (when user selects a unit)
    syncRequested = pyqtSignal()  # Request synchronization with curve plotter
    
    def __init__(self, parent=None):
        """Initialize enhanced stratigraphic column with synchronization features."""
        super().__init__(parent)
        
        # Enhanced display settings
        self.show_detailed_labels = True
        self.show_lithology_codes = True
        self.show_thickness_values = True
        self.show_qualifiers = True
        
        # Synchronization settings
        self.sync_enabled = True
        self.sync_curve_plotter = None  # Reference to curve plotter for direct sync
        self.last_sync_depth = 0.0
        
        # Enhanced visualization settings
        self.unit_label_font = QFont("Arial", 7)
        self.unit_label_color = QColor(0, 0, 0)  # Black
        self.highlight_gradient_enabled = True
        
        # Current visible depth range (for synchronization)
        self.visible_min_depth = 0.0
        self.visible_max_depth = 100.0
        
        # Enhanced unit data storage
        self.unit_rect_items = []  # Store references to unit rectangles for quick access
        self.unit_label_items = []  # Store references to unit labels
        
        # Connect scroll events for synchronization
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)
        
        # Enhanced scene setup
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
    def draw_column(self, units_dataframe, min_overall_depth, max_overall_depth, 
                   separator_thickness=0.5, draw_separators=True, disable_svg=False):
        """
        Draw enhanced stratigraphic column with detailed unit information.
        
        Overrides base class method to add detailed labels and enhanced visualization.
        """
        print(f"DEBUG (EnhancedStratigraphicColumn): draw_column called with {len(units_dataframe)} units")
        
        # Clear enhanced data structures
        self.unit_rect_items.clear()
        self.unit_label_items.clear()
        
        # Call parent method for basic drawing
        super().draw_column(units_dataframe, min_overall_depth, max_overall_depth, 
                           separator_thickness, draw_separators, disable_svg)
        
        # Add enhanced features if we have units
        if units_dataframe is not None and not units_dataframe.empty:
            self._add_detailed_unit_labels(units_dataframe)
            self._add_enhanced_visualization(units_dataframe)
            
        # Update visible depth range
        self._update_visible_depth_range()
        
    def _add_detailed_unit_labels(self, units_dataframe):
        """Add detailed labels to each lithology unit."""
        if not self.show_detailed_labels:
            return
            
        for index, unit in units_dataframe.iterrows():
            from_depth = unit['from_depth']
            to_depth = unit['to_depth']
            thickness = unit[RECOVERED_THICKNESS_COLUMN]
            lithology_code = unit[LITHOLOGY_COLUMN]
            lithology_qualifier = unit.get('lithology_qualifier', '')
            
            # Calculate position
            y_start = (from_depth - self.min_depth) * self.depth_scale
            rect_height = thickness * self.depth_scale
            
            # Apply minimum display height
            if rect_height > 0 and rect_height < self.min_display_height_pixels:
                rect_height = self.min_display_height_pixels
                
            if rect_height <= 0:
                continue
                
            # Only add labels if unit is tall enough
            if rect_height >= 15:  # Minimum height for readable labels
                # Create label text based on settings
                label_parts = []
                
                if self.show_lithology_codes:
                    label_parts.append(str(lithology_code))
                    
                if self.show_thickness_values and rect_height >= 25:
                    label_parts.append(f"{thickness:.2f}m")
                    
                if self.show_qualifiers and lithology_qualifier and rect_height >= 30:
                    label_parts.append(lithology_qualifier)
                    
                if label_parts:
                    label_text = "\n".join(label_parts)
                    
                    # Create text item
                    text_item = QGraphicsSimpleTextItem(label_text)
                    text_item.setFont(self.unit_label_font)
                    text_item.setBrush(QBrush(self.unit_label_color))
                    
                    # Position text in center of unit
                    text_rect = text_item.boundingRect()
                    text_x = self.y_axis_width + self.column_width / 2 - text_rect.width() / 2
                    text_y = y_start + rect_height / 2 - text_rect.height() / 2
                    
                    # Adjust for very tall units - position near top
                    if rect_height > 100:
                        text_y = y_start + 5
                        
                    text_item.setPos(text_x, text_y)
                    
                    # Add to scene and store reference
                    self.scene.addItem(text_item)
                    self.unit_label_items.append(text_item)
                    
    def _add_enhanced_visualization(self, units_dataframe):
        """Add enhanced visualization features like gradients and borders."""
        if not self.highlight_gradient_enabled:
            return
            
        # Store references to unit rectangles for quick access
        # (Note: parent class already created these, we just need to find them)
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                # Check if this is a unit rectangle (not axis or other rect)
                rect = item.rect()
                if rect.x() == self.y_axis_width and rect.width() == self.column_width:
                    self.unit_rect_items.append(item)
                    
                    # Add subtle gradient effect for depth perception
                    if rect.height() > 20:
                        current_brush = item.brush()
                        if current_brush.style() != Qt.BrushStyle.NoBrush:
                            # Create a subtle vertical gradient
                            gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                            color = current_brush.color()
                            gradient.setColorAt(0.0, color.lighter(110))
                            gradient.setColorAt(0.5, color)
                            gradient.setColorAt(1.0, color.darker(110))
                            item.setBrush(QBrush(gradient))
                            
    def _on_scroll_value_changed(self, value):
        """Handle scroll bar value changes for synchronization."""
        if not self.sync_enabled:
            return
            
        # Calculate visible depth range
        view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        visible_min_y = view_rect.top()
        visible_max_y = view_rect.bottom()
        
        # Convert to depth values
        self.visible_min_depth = self.min_depth + (visible_min_y / self.depth_scale)
        self.visible_max_depth = self.min_depth + (visible_max_y / self.depth_scale)
        
        # Calculate center depth
        center_depth = (self.visible_min_depth + self.visible_max_depth) / 2
        
        # Emit signals for synchronization
        self.depthRangeChanged.emit(self.visible_min_depth, self.visible_max_depth)
        
        # Only emit scroll signal if depth changed significantly
        if abs(center_depth - self.last_sync_depth) > 0.1:
            self.depthScrolled.emit(center_depth)
            self.last_sync_depth = center_depth
            
    def _update_visible_depth_range(self):
        """Update the visible depth range based on current view."""
        view_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        visible_min_y = view_rect.top()
        visible_max_y = view_rect.bottom()
        
        self.visible_min_depth = self.min_depth + (visible_min_y / self.depth_scale)
        self.visible_max_depth = self.min_depth + (visible_max_y / self.depth_scale)
        
    def sync_with_curve_plotter(self, curve_plotter):
        """
        Synchronize vertical scrolling with a curve plotter.
        
        Args:
            curve_plotter: PyQtGraphCurvePlotter instance to sync with
        """
        self.sync_curve_plotter = curve_plotter
        
        # Connect signals for bidirectional synchronization
        if curve_plotter:
            # When curve plotter scrolls, update strat column
            if hasattr(curve_plotter, 'viewRangeChanged'):
                # Note: PyQtGraphCurvePlotter already has viewRangeChanged signal
                curve_plotter.viewRangeChanged.connect(self._on_curve_plotter_scrolled)
                
            # When strat column scrolls, update curve plotter
            self.depthScrolled.connect(self._on_strat_column_scrolled)
            
    def _on_curve_plotter_scrolled(self, min_depth, max_depth):
        """Handle when curve plotter scrolls - update strat column view."""
        if not self.sync_enabled or not self.sync_curve_plotter:
            return
            
        # Calculate center depth
        center_depth = (min_depth + max_depth) / 2
        
        # Scroll strat column to match
        self.scroll_to_depth(center_depth)
        
        # Update visible depth range
        self.visible_min_depth = min_depth
        self.visible_max_depth = max_depth
        
    def _on_strat_column_scrolled(self, center_depth):
        """Handle when strat column scrolls - update curve plotter view."""
        if not self.sync_enabled or not self.sync_curve_plotter:
            return
            
        # Get current view height from curve plotter
        if hasattr(self.sync_curve_plotter, 'plot_widget'):
            view_range = self.sync_curve_plotter.plot_widget.viewRange()
            if view_range and len(view_range) > 1:
                current_y_min = view_range[1][0]
                current_y_max = view_range[1][1]
                current_height = current_y_max - current_y_min
                
                # Calculate new range centered on target depth
                new_y_min = center_depth - current_height / 2
                new_y_max = center_depth + current_height / 2
                
                # Update curve plotter
                self.sync_curve_plotter.plot_widget.setYRange(new_y_min, new_y_max)
                
    def scroll_to_depth(self, depth):
        """
        Scroll the view to make the given depth visible.
        
        Overrides base method to add synchronization.
        """
        # Call parent method
        super().scroll_to_depth(depth)
        
        # Update visible depth range
        self._update_visible_depth_range()
        
        # Emit synchronization signal
        if self.sync_enabled:
            self.depthScrolled.emit(depth)
            
    def set_sync_enabled(self, enabled):
        """Enable or disable synchronization with curve plotter."""
        self.sync_enabled = enabled
        
    def get_visible_depth_range(self):
        """Get the currently visible depth range."""
        return self.visible_min_depth, self.visible_max_depth
        
    def set_detailed_labels_enabled(self, enabled):
        """Enable or disable detailed unit labels."""
        self.show_detailed_labels = enabled
        
    def set_lithology_codes_enabled(self, enabled):
        """Enable or display of lithology codes."""
        self.show_lithology_codes = enabled
        
    def set_thickness_values_enabled(self, enabled):
        """Enable or disable display of thickness values."""
        self.show_thickness_values = enabled
        
    def set_qualifiers_enabled(self, enabled):
        """Enable or disable display of lithology qualifiers."""
        self.show_qualifiers = enabled
        
    def set_highlight_gradient_enabled(self, enabled):
        """Enable or disable gradient highlighting on units."""
        self.highlight_gradient_enabled = enabled
        
    def resizeEvent(self, event):
        """Handle resize events to update visible depth range."""
        super().resizeEvent(event)
        self._update_visible_depth_range()
        
    def wheelEvent(self, event):
        """Handle wheel events for zooming with synchronization."""
        # First, let the parent handle the wheel event (for zooming)
        super().wheelEvent(event)
        
        # Then update synchronization
        self._update_visible_depth_range()
        if self.sync_enabled:
            center_depth = (self.visible_min_depth + self.visible_max_depth) / 2
            self.depthScrolled.emit(center_depth)
            
    def mousePressEvent(self, event):
        """Handle mouse clicks with enhanced selection highlighting."""
        # Call parent method first
        super().mousePressEvent(event)
        
        # Emit enhanced selection signal
        if self.selected_unit_index is not None:
            self.unitSelected.emit(self.selected_unit_index)
            
    def clear_column(self):
        """Clear the column and reset enhanced data structures."""
        self.scene.clear()
        self.unit_rect_items.clear()
        self.unit_label_items.clear()
        self.visible_min_depth = 0.0
        self.visible_max_depth = 100.0
        self.selected_unit_index = None
        self.highlight_rect_item = None
        self.units_dataframe = None
        
    def update_synchronization(self):
        """Force update of synchronization with curve plotter."""
        if self.sync_enabled and self.sync_curve_plotter:
            self._update_visible_depth_range()
            center_depth = (self.visible_min_depth + self.visible_max_depth) / 2
            self._on_strat_column_scrolled(center_depth)