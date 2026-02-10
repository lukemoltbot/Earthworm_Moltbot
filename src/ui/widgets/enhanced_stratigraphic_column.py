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
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem, QGraphicsSimpleTextItem, QToolTip
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap, QPen, QLinearGradient
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF, Qt, pyqtSignal, QPointF, QPoint
from ...core.config import LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN
from .svg_renderer import SvgRenderer
from .stratigraphic_column import StratigraphicColumn  # Inherit from base class


class HoverRectItem(QGraphicsRectItem):
    """Custom rectangle item that emits hover events."""
    
    def __init__(self, x, y, width, height, parent=None):
        super().__init__(x, y, width, height, parent)
        self.setAcceptHoverEvents(True)
        self.unit_index = -1
        self.parent_widget = None
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        if self.parent_widget:
            self.parent_widget._on_unit_hover_enter(event, self.unit_index)
        # Don't call super() to prevent any default behavior that might interfere
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        if self.parent_widget:
            self.parent_widget._on_unit_hover_leave(event, self.unit_index)
        # Don't call super() to prevent any default behavior that might interfere


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
        self.show_detailed_labels = False  # Disable labels inside units - will show on hover instead
        self.show_lithology_codes = False  # Disable - will show in tooltip
        self.show_thickness_values = False  # Disable - will show in tooltip
        self.show_qualifiers = False  # Disable - will show in tooltip
        
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
        self.unit_hover_items = []  # Store references to hover rectangles
        self.unit_data = []  # Store additional unit data for tooltips
        self.classified_dataframe = None  # Store original classified data for curve values
        
        # Hover tracking
        self.hovered_unit_index = None
        self.hover_timer = None
        self.tooltip_delay = 500  # ms delay before showing tooltip
        
        # Connect scroll events for synchronization
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_value_changed)
        
        # Enhanced scene setup
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Enable mouse tracking for hover events
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)
        
        # Match curve plotter scale for synchronization
        # Curve plotter uses depth_scale = 10, so enhanced column should match
        # This ensures they show the same depth range and scroll together
        self.depth_scale = 10.0  # Match curve plotter scale
        
    def set_classified_data(self, classified_dataframe):
        """Set the classified dataframe containing original curve data."""
        self.classified_dataframe = classified_dataframe.copy() if classified_dataframe is not None else None
        if self.classified_dataframe is not None:
            print(f"DEBUG (EnhancedStratigraphicColumn): Set classified dataframe with {len(self.classified_dataframe)} rows")
            print(f"DEBUG (EnhancedStratigraphicColumn): Classified dataframe columns: {list(self.classified_dataframe.columns)}")
    
    def draw_column(self, units_dataframe, min_overall_depth, max_overall_depth, 
                   separator_thickness=0.5, draw_separators=True, disable_svg=False):
        """
        Draw enhanced stratigraphic column with detailed unit information.
        
        Overrides base class method to add detailed labels and enhanced visualization.
        """
        print(f"DEBUG (EnhancedStratigraphicColumn): draw_column called with {len(units_dataframe)} units, min_depth={min_overall_depth}, max_depth={max_overall_depth}, depth_scale={self.depth_scale}")
        print(f"DEBUG (EnhancedStratigraphicColumn): units_dataframe is None: {units_dataframe is None}, empty: {units_dataframe.empty if units_dataframe is not None else 'N/A'}")
        
        # Debug: print available columns
        if units_dataframe is not None and not units_dataframe.empty:
            print(f"DEBUG (EnhancedStratigraphicColumn): Available columns: {list(units_dataframe.columns)}")
            
            # Check for curve columns
            curve_columns = ['gamma', 'density', 'short_space_density', 'long_space_density']
            available_curves = [col for col in curve_columns if col in units_dataframe.columns]
            if available_curves:
                print(f"DEBUG (EnhancedStratigraphicColumn): Available curve columns: {available_curves}")
                # Print first unit's curve values
                first_unit = units_dataframe.iloc[0]
                for curve in available_curves:
                    print(f"DEBUG (EnhancedStratigraphicColumn): First unit {curve}: {first_unit.get(curve, 'N/A')}")
        
        # Clear enhanced data structures
        self.unit_rect_items.clear()
        self.unit_label_items.clear()
        self.unit_hover_items.clear()
        self.unit_data.clear()
        
        # Store the units dataframe for reference
        self.units_dataframe = units_dataframe.copy() if units_dataframe is not None else None
        
        # Call parent method for basic drawing
        super().draw_column(units_dataframe, min_overall_depth, max_overall_depth, 
                           separator_thickness, draw_separators, disable_svg)
        
        # Store unit data for tooltips and set up hover events
        if units_dataframe is not None and not units_dataframe.empty:
            self._store_unit_data(units_dataframe)
            
        # Update visible depth range
        self._update_visible_depth_range()
        
    def _store_unit_data(self, units_dataframe):
        """Store unit data for tooltips and hover events."""
        print(f"DEBUG (EnhancedStratigraphicColumn._store_unit_data): Storing data for {len(units_dataframe)} units")
        print(f"DEBUG (EnhancedStratigraphicColumn._store_unit_data): self.min_depth = {self.min_depth}, self.depth_scale = {self.depth_scale}")
        
        for index, unit in units_dataframe.iterrows():
            from_depth = unit['from_depth']
            to_depth = unit['to_depth']
            thickness = unit[RECOVERED_THICKNESS_COLUMN]
            lithology_code = unit[LITHOLOGY_COLUMN]
            lithology_qualifier = unit.get('lithology_qualifier', '')
            
            # Calculate position
            y_start = (from_depth - self.min_depth) * self.depth_scale
            rect_height = thickness * self.depth_scale
            
            print(f"DEBUG (EnhancedStratigraphicColumn._store_unit_data): Unit {index}: from={from_depth}, to={to_depth}, thickness={thickness}, y_start={y_start}, rect_height={rect_height}")
            
            # Apply minimum display height
            if rect_height > 0 and rect_height < self.min_display_height_pixels:
                rect_height = self.min_display_height_pixels
                print(f"DEBUG (EnhancedStratigraphicColumn._store_unit_data): Applied min display height: {rect_height}")
                
            if rect_height <= 0:
                print(f"DEBUG (EnhancedStratigraphicColumn._store_unit_data): Skipping unit {index} - rect_height <= 0")
                continue
            
            # Store unit data for tooltips
            unit_info = {
                'index': index,
                'from_depth': from_depth,
                'to_depth': to_depth,
                'thickness': thickness,
                'lithology_code': lithology_code,
                'lithology_qualifier': lithology_qualifier,
                'y_start': y_start,
                'rect_height': rect_height,
                'rect_x': self.y_axis_width,
                'rect_width': self.column_width
            }
            
            # Check for and store any available curve values
            curve_columns = ['gamma', 'density', 'short_space_density', 'long_space_density']
            for curve in curve_columns:
                if curve in unit:
                    value = unit[curve]
                    # Check if it's a valid number (not NaN or None)
                    if pd.notna(value) and value is not None:
                        unit_info[curve] = float(value)
                    else:
                        unit_info[curve] = None
                else:
                    unit_info[curve] = None
            
            # If curve values are not in units dataframe, try to get them from classified dataframe
            if self.classified_dataframe is not None and 'DEPT' in self.classified_dataframe.columns:
                # Get average curve values for this unit's depth range
                from_depth = unit_info['from_depth']
                to_depth = unit_info['to_depth']
                
                # Find rows in classified dataframe within this depth range
                mask = (self.classified_dataframe['DEPT'] >= from_depth) & (self.classified_dataframe['DEPT'] <= to_depth)
                unit_rows = self.classified_dataframe[mask]
                
                if not unit_rows.empty:
                    for curve in curve_columns:
                        if curve in self.classified_dataframe.columns and curve not in unit_info:
                            # Calculate average value for this curve in the unit
                            curve_values = unit_rows[curve]
                            valid_values = curve_values[pd.notna(curve_values)]
                            if not valid_values.empty:
                                unit_info[curve] = float(valid_values.mean())
                                print(f"DEBUG (EnhancedStratigraphicColumn): Retrieved {curve} value {unit_info[curve]:.2f} from classified data for unit {index}")
            
            self.unit_data.append(unit_info)
            
            # Create invisible hover rectangle for this unit
            hover_rect = HoverRectItem(
                self.y_axis_width, y_start, self.column_width, rect_height
            )
            hover_rect.setPen(QPen(Qt.GlobalColor.black, 0))
            hover_rect.setBrush(QBrush(QColor(0, 0, 0, 1)))  # Almost fully transparent (alpha=1 for event handling)
            hover_rect.unit_index = index
            hover_rect.parent_widget = self
            
            self.scene.addItem(hover_rect)
            self.unit_hover_items.append(hover_rect)
    
    def _on_unit_hover_enter(self, event, unit_index):
        """Handle mouse hover enter event for a unit."""
        print(f"DEBUG (EnhancedStratigraphicColumn._on_unit_hover_enter): Hover entered unit {unit_index}")
        self.hovered_unit_index = unit_index
        
        # Find unit data
        unit_info = None
        for info in self.unit_data:
            if info['index'] == unit_index:
                unit_info = info
                break
        
        if unit_info:
            print(f"DEBUG (EnhancedStratigraphicColumn._on_unit_hover_enter): Found unit info for index {unit_index}")
            # Create tooltip text
            tooltip_text = self._create_unit_tooltip(unit_info)
            
            # Show tooltip immediately
            # Convert scene coordinates to global screen coordinates
            scene_pos = QPointF(
                unit_info['rect_x'] + unit_info['rect_width'] / 2,
                unit_info['y_start'] + unit_info['rect_height'] / 2
            )
            view_pos = self.mapFromScene(scene_pos)
            global_pos = self.mapToGlobal(view_pos)
            
            print(f"DEBUG (EnhancedStratigraphicColumn._on_unit_hover_enter): Showing tooltip at global position {global_pos}")
            QToolTip.showText(global_pos, tooltip_text, self)
        else:
            print(f"DEBUG (EnhancedStratigraphicColumn._on_unit_hover_enter): No unit info found for index {unit_index}")
    
    def _on_unit_hover_leave(self, event, unit_index):
        """Handle mouse hover leave event for a unit."""
        if self.hovered_unit_index == unit_index:
            self.hovered_unit_index = None
            QToolTip.hideText()
    
    def _create_unit_tooltip(self, unit_info):
        """Create tooltip text for a lithology unit."""
        lines = []
        
        # Basic unit information
        lines.append(f"<b>Lithology Unit Details</b>")
        lines.append(f"Lithology Code: <b>{unit_info['lithology_code']}</b>")
        
        if unit_info['lithology_qualifier']:
            lines.append(f"Qualifier: {unit_info['lithology_qualifier']}")
        
        lines.append(f"Depth Range: {unit_info['from_depth']:.2f}m - {unit_info['to_depth']:.2f}m")
        lines.append(f"Thickness: {unit_info['thickness']:.3f}m")
        
        # Add LAS curve values if available
        lines.append("")
        lines.append("<i>LAS Curve Values:</i>")
        
        # Check for each curve value
        curve_display_names = {
            'gamma': 'Gamma Ray',
            'density': 'Density',
            'short_space_density': 'Short Space Density',
            'long_space_density': 'Long Space Density'
        }
        
        curve_units = {
            'gamma': 'API',
            'density': 'g/cc',
            'short_space_density': 'g/cc',
            'long_space_density': 'g/cc'
        }
        
        has_curve_data = False
        for curve_key, display_name in curve_display_names.items():
            if curve_key in unit_info and unit_info[curve_key] is not None:
                value = unit_info[curve_key]
                unit = curve_units.get(curve_key, '')
                lines.append(f"  {display_name}: {value:.2f} {unit}")
                has_curve_data = True
            else:
                lines.append(f"  {display_name}: <i>Not available</i>")
        
        if not has_curve_data:
            lines.append("<small><i>No LAS curve data available for this unit</i></small>")
        
        lines.append("")
        lines.append("<small><i>Hover over unit to see details</i></small>")
        
        return "<br>".join(lines)
                    
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