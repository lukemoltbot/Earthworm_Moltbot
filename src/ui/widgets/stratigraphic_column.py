import os
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, QGraphicsLineItem
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPixmap, QPen, QTransform
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QRectF, Qt, pyqtSignal
import numpy as np # Import numpy
from ...core.config import LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN
from .svg_renderer import SvgRenderer

class StratigraphicColumn(QGraphicsView):
    unitClicked = pyqtSignal(int)  # emits unit index when a unit is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.column_width = 40  # Reduced from 140px to 40px (1/3 of original)
#         print(f"DEBUG (StratigraphicColumn.__init__): column_width set to {self.column_width}px (1/3 of original 140px)")
        self.min_display_height_pixels = 2 # Minimum height for very thin units
        self.litho_svg_path = "../../assets/svg/"
        self.svg_renderer = SvgRenderer()

        self.y_axis_width = 20  # Reduced from 40px to 20px for Y-axis scale
        self.x_axis_height = 60 # Height reserved for X-axis (to match curve plotter)

        # Selection highlighting attributes
        self.selected_unit_index = None
        self.highlight_rect_item = None
        self.units_dataframe = None
        self.min_depth = 0.0
        self.max_depth = 100.0
        
        # Overview view attributes (Subtask 3.3)
        self.overview_mode = False  # Whether this is showing entire hole (overview) or zoomed section
        self.zoom_overlay_rect = None  # Rectangle showing current zoom region in plot view
        self.current_zoom_min = 0.0
        self.current_zoom_max = 100.0
        
        # Initialize depth scale AFTER overview_mode is set
        self.depth_scale = 10 # Pixels per depth unit
        
        # Fixed overview attributes
        self.hole_min_depth = 0.0  # Entire hole minimum depth (for overview mode)
        self.hole_max_depth = 500.0  # Entire hole maximum depth (for overview mode)
        self.overview_scale_locked = False  # Whether depth scale is locked in overview mode
        self.overview_fixed_scale = 10.0  # Fixed depth scale for overview mode
        
        # Private depth scale storage
        self._depth_scale = 10.0  # Default depth scale
        
        # Engineering scale display
        self.current_scale_label = "1:50"  # Default engineering scale
        self.show_scale_display = True  # Whether to show scale display
        
        # Engineering scale converter
        from .scale_converter import EngineeringScaleConverter
        self.scale_converter = EngineeringScaleConverter(self)
        self.scale_converter.scaleChanged.connect(self._on_scale_changed)

    @property
    def depth_scale(self):
        """Get depth scale property."""
        return self._depth_scale
    
    @depth_scale.setter
    def depth_scale(self, value):
        """Set depth scale property with overview mode protection."""
        # In overview mode with locked scale, prevent changes
        # Check if overview_mode exists (it might not during __init__)
        if hasattr(self, 'overview_mode') and self.overview_mode and self.overview_scale_locked:
            print(f"DEBUG (StratigraphicColumn.depth_scale.setter): Attempt to change depth_scale in overview mode blocked (value={value})")
#             print(f"DEBUG (StratigraphicColumn.depth_scale.setter): Keeping fixed overview scale: {self._depth_scale}")
            return
            
        # Validate value
        if value <= 0:
            print(f"WARNING (StratigraphicColumn.depth_scale.setter): Invalid depth_scale value: {value}")
            return
            
        self._depth_scale = value
#         print(f"DEBUG (StratigraphicColumn.depth_scale.setter): Set depth_scale to {value}")

    def draw_column(self, units_dataframe, min_overall_depth, max_overall_depth, separator_thickness=0.5, draw_separators=True, disable_svg=False):
        print(f"DEBUG (StratigraphicColumn): draw_column called with {len(units_dataframe)} units, min_depth={min_overall_depth}, max_depth={max_overall_depth}, depth_scale={self.depth_scale}, overview_mode={self.overview_mode}")
        if units_dataframe is not None and not units_dataframe.empty:
            pass
#             print(f"DEBUG (StratigraphicColumn): columns present: {list(units_dataframe.columns)}")
        self.disable_svg = disable_svg
        self.scene.clear()
        # Clear references to deleted items
        self.highlight_rect_item = None
        self.zoom_overlay_rect = None

        # Store data for highlighting functionality
        self.units_dataframe = units_dataframe.copy() if units_dataframe is not None else None
        
        print(f"DEBUG (StratigraphicColumn.draw_column): overview_mode={self.overview_mode}, scale_locked={self.overview_scale_locked}")
        
        # In overview mode, ALWAYS show entire hole from hole_min_depth to hole_max_depth
        # Ignore the min_overall_depth/max_overall_depth parameters for depth range
        if self.overview_mode and self.overview_scale_locked:
            pass
            # Use fixed hole depth range and scale
            self.min_depth = self.hole_min_depth
            self.max_depth = self.hole_max_depth
            
            # Use the fixed overview scale
            if hasattr(self, 'overview_fixed_scale') and self.overview_fixed_scale > 0:
                pass
                # Bypass setter protection by setting _depth_scale directly
                self._depth_scale = self.overview_fixed_scale
#                 print(f"DEBUG (StratigraphicColumn.draw_column): Using fixed overview scale: {self._depth_scale:.4f} px/m")
            else:
                # Fallback: calculate scale to fit hole in viewport
                available_height = max(1, self.viewport().height() - self.x_axis_height)
                hole_depth_range = max(1.0, self.hole_max_depth - self.hole_min_depth)
                self.overview_fixed_scale = available_height / hole_depth_range
                # Bypass setter protection by setting _depth_scale directly
                self._depth_scale = self.overview_fixed_scale
                print(f"DEBUG (StratigraphicColumn.draw_column): Calculated fallback overview scale: {self._depth_scale:.4f} px/m")
        else:
            # Normal mode: use provided depth range
            self.min_depth = min_overall_depth
            self.max_depth = max_overall_depth
#             print(f"DEBUG (StratigraphicColumn.draw_column): Using normal mode with depth_scale={self.depth_scale}")

        # Use the min/max depths for scene scaling
        min_depth_for_scene = self.min_depth
        max_depth_for_scene = self.max_depth

        # Adjust scene rect to include space for the Y-axis
        # In overview mode, we use fitInView with padding, so scene rect should be exact content size
        if self.overview_mode:
            pass
            # For overview mode: Use a reasonable scene height (fitInView will scale it)
            # We're using 10px per metre as a base - fitInView will scale to fill height
            scene_height = (max_depth_for_scene - min_depth_for_scene) * 10.0
            print(f"DEBUG (StratigraphicColumn.draw_column): Overview mode - scene height: {scene_height:.1f}px")
        else:
            # In detailed mode, include X-axis height to match curve plotter
            scene_height = (max_depth_for_scene - min_depth_for_scene) * self.depth_scale + self.x_axis_height
#             print(f"DEBUG (StratigraphicColumn.draw_column): Detailed mode - scene height with X-axis: {scene_height:.1f}px")
            
        self.scene.setSceneRect(0, 0, self.y_axis_width + self.column_width, scene_height)
        
        print(f"DEBUG (StratigraphicColumn.draw_column): Scene rect: {self.y_axis_width + self.column_width:.1f}x{scene_height:.1f}px, depth_range={max_depth_for_scene - min_depth_for_scene:.1f}m, overview_mode={self.overview_mode}")

        # Draw Y-axis scale
        self._draw_y_axis(min_depth_for_scene, max_depth_for_scene)

        # Draw stratigraphic units
#         print(f"DEBUG (StratigraphicColumn): Drawing {len(units_dataframe)} units, min_depth={self.min_depth}, max_depth={self.max_depth}")
        for index, unit in units_dataframe.iterrows():
            from_depth = unit['from_depth']
            to_depth = unit['to_depth']
            thickness = unit[RECOVERED_THICKNESS_COLUMN]
            lithology_code = unit[LITHOLOGY_COLUMN]
            lithology_qualifier = unit.get('lithology_qualifier', '')
            svg_file = unit.get('svg_path')
            if svg_file is None:
                svg_file = ''
            bg_color_str = unit.get('background_color')
            if not bg_color_str:
                bg_color_str = '#FFFFFF'
            bg_color = QColor(bg_color_str)
            if not bg_color.isValid():
                print(f"WARNING (StratigraphicColumn): Invalid background_color '{bg_color_str}' for lithology {lithology_code}, falling back to white")
                bg_color = QColor('#FFFFFF')

            # Commented out verbose debug - keep console clean
            # print(f"DEBUG (StratigraphicColumn): Drawing unit {index}: from={from_depth}, to={to_depth}, thickness={thickness}, code={lithology_code}, background_color_raw={unit.get('background_color', 'MISSING')}, color={bg_color.name()}, svg={svg_file}")
#             print(f"DEBUG (StratigraphicColumn): Unit columns: {list(unit.keys()) if hasattr(unit, 'keys') else 'not a dict'}")

            y_start = (from_depth - self.min_depth) * self.depth_scale
            rect_height = thickness * self.depth_scale

            # Apply minimum display height for very thin units
            if rect_height > 0 and rect_height < self.min_display_height_pixels:
                rect_height = self.min_display_height_pixels
            
            # Safety check to prevent drawing zero-height rectangles
            if rect_height <= 0:
                continue

#             print(f"DEBUG (StratigraphicColumn): Unit {index} rect_height={rect_height:.2f}px, border={'gray 0.5px' if rect_height >= 5 else 'transparent'}")

            # Position the column to the right of the Y-axis
            rect_item = QGraphicsRectItem(self.y_axis_width, y_start, self.column_width, rect_height)
            
            # Add a subtle border to make units visible, but use transparent for very thin units
            # Thin units (< 5px) get transparent borders to prevent grey appearance
            if rect_height >= 5:
                rect_item.setPen(QPen(QColor(Qt.GlobalColor.gray), 0.5))
            else:
                # For very thin units, use transparent border to avoid grey appearance
                rect_item.setPen(QPen(Qt.GlobalColor.transparent, 0))

            # Check if SVG patterns are disabled
            if self.disable_svg:
                print(f"DEBUG (StratigraphicColumn): SVG patterns disabled, using solid color")
                pixmap = None
            else:
                pixmap = self.svg_renderer.render_svg(svg_file, self.column_width, int(rect_height), bg_color)
#             print(f"DEBUG (StratigraphicColumn): pixmap created: {pixmap is not None}")
            if pixmap:
                print(f"DEBUG (StratigraphicColumn): Setting pixmap brush for unit {index}")
                rect_item.setBrush(QBrush(pixmap))
            else:
#                 print(f"DEBUG (StratigraphicColumn): Setting solid color brush for unit {index}: {bg_color.name()}")
                rect_item.setBrush(QBrush(bg_color))
            
            self.scene.addItem(rect_item)

            # Draw a thin grey line at the bottom of each unit to act as a separator
            if draw_separators and separator_thickness > 0:
                separator_pen = QPen(QColor(Qt.GlobalColor.gray))
                separator_pen.setWidthF(separator_thickness)
                line_item = QGraphicsLineItem(self.y_axis_width, y_start + rect_height, self.y_axis_width + self.column_width, y_start + rect_height)
                line_item.setPen(separator_pen)
                self.scene.addItem(line_item)

        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum()) # Scroll to bottom to show top of log

    def set_zoom_level(self, zoom_factor):
        """Set zoom level (1.0 = 100% = normal fit level)."""
        # In overview mode, ignore zoom commands - overview should not zoom
        if self.overview_mode:
            print(f"DEBUG (StratigraphicColumn.set_zoom_level): Ignoring zoom command in overview mode (zoom_factor={zoom_factor})")
            return
            
        if self.scene.sceneRect().isEmpty():
            return  # No scene to zoom

        # Store current zoom factor for reference
        self.current_zoom_factor = zoom_factor

        # Calculate the zoom rectangle based on the zoom factor
        # zoom_factor of 1.0 means fit to view (normal), 2.0 means zoom in (show 50% of content), etc.
        original_rect = self.scene.sceneRect()

        # For zoom_factor > 1.0, we want to zoom in (show smaller area)
        # For zoom_factor < 1.0, we want to zoom out (show larger area)
        zoom_rect = original_rect
        if zoom_factor > 1.0:
            pass
            # Zoom in: make the rectangle smaller
            new_width = original_rect.width() / zoom_factor
            new_height = original_rect.height() / zoom_factor
            center_x = original_rect.center().x()
            center_y = original_rect.center().y()
            zoom_rect.setRect(center_x - new_width/2, center_y - new_height/2, new_width, new_height)
        elif zoom_factor < 1.0:
            pass
            # Zoom out: make the rectangle larger (but still fit in view)
            scale_factor = 1.0 / zoom_factor
            new_width = original_rect.width() * scale_factor
            new_height = original_rect.height() * scale_factor
            center_x = original_rect.center().x()
            center_y = original_rect.center().y()
            zoom_rect.setRect(center_x - new_width/2, center_y - new_height/2, new_width, new_height)

        # Apply the zoom while maintaining aspect ratio
        self.fitInView(zoom_rect, Qt.AspectRatioMode.KeepAspectRatio)


    def _draw_y_axis(self, min_depth, max_depth):
        pass
        # Debug: Track how many times this method is called
        if not hasattr(self, '_y_axis_draw_count'):
            self._y_axis_draw_count = 0
        self._y_axis_draw_count += 1
        
        print(f"DEBUG (StratigraphicColumn._draw_y_axis): CALL #{self._y_axis_draw_count} with range {min_depth:.2f}-{max_depth:.2f}")
        
        # Use a thinner pen for the axis (0.5px instead of default 1px)
        axis_pen = QPen(Qt.GlobalColor.black, 0.5)
        axis_font = QFont("Arial", 8)

        # Calculate Y positions based on scene height and depth range
        scene_rect = self.scene.sceneRect()
        scene_height = scene_rect.height()
        depth_range = max(1.0, max_depth - min_depth)
        
        # For overview mode, we need to calculate Y positions differently
        # since fitInView will scale everything
        if self.overview_mode:
            pass
            # In overview mode, positions are proportional to scene height
            y_top = 0
            y_bottom = scene_height
#             print(f"DEBUG (StratigraphicColumn._draw_y_axis): Overview mode - using scene height: {scene_height:.1f}px")
        else:
            # In detailed mode, calculate Y positions relative to self.min_depth
            # This ensures axis line aligns with lithology units
            y_top = (min_depth - self.min_depth) * self.depth_scale
            y_bottom = (max_depth - self.min_depth) * self.depth_scale
            print(f"DEBUG (StratigraphicColumn._draw_y_axis): Detailed mode - y_top={y_top:.1f}, y_bottom={y_bottom:.1f}, "
                  f"min_depth={min_depth:.2f}, self.min_depth={self.min_depth:.2f}")

        # Draw the main axis line with thin pen
        self.scene.addLine(self.y_axis_width, y_top, 
                           self.y_axis_width, y_bottom, axis_pen)
#         print(f"DEBUG (StratigraphicColumn._draw_y_axis): Drew axis line from y={y_top:.1f} to y={y_bottom:.1f}")

        # For overview mode: Skip tick marks and labels (not needed for visual reference)
        if self.overview_mode:
            print(f"DEBUG (StratigraphicColumn._draw_y_axis): Overview mode - skipping tick marks and labels")
            return  # Exit early, only draw the axis line
        
        # For detailed mode: Draw tick marks and labels as before
        # Determine tick intervals - show every whole metre
        depth_range = max_depth - min_depth
        major_tick_interval = 1.0  # Show labels at every metre
        minor_tick_interval = 0.1  # Minor ticks at every 0.1m (optional, can be removed)

        # Remove adaptive interval logic for this view
        # Always show whole metre increments regardless of depth range
#         print(f"DEBUG (StratigraphicColumn._draw_y_axis): Detailed mode - drawing Y-axis with major_tick_interval={major_tick_interval}, "
#               f"minor_tick_interval={minor_tick_interval}, depth_range={depth_range:.1f}m")

        # Draw tick marks and labels - ensure EVERY whole metre gets a mark
        # Start from the first whole metre at or below min_depth
        start_whole_metre = np.floor(min_depth)
        end_whole_metre = np.ceil(max_depth)
        
        print(f"DEBUG (StratigraphicColumn._draw_y_axis): Drawing metre marks from {start_whole_metre:.0f}m to {end_whole_metre:.0f}m")
        
        # Draw major ticks at every whole metre
        current_whole_metre = start_whole_metre
        while current_whole_metre <= end_whole_metre:
            pass
            # Calculate Y position relative to self.min_depth (data reference point)
            y_pos = (current_whole_metre - self.min_depth) * self.depth_scale
            
            # Draw tick mark (10px long)
            self.scene.addLine(self.y_axis_width - 10, y_pos, self.y_axis_width, y_pos, axis_pen)
            
            # Draw label (integer depth)
            label_text = f"{current_whole_metre:.0f}"
            text_item = QGraphicsTextItem(label_text)
            text_item.setFont(axis_font)
            text_item.setPos(self.y_axis_width - 30, y_pos - text_item.boundingRect().height() / 2)
            self.scene.addItem(text_item)
            
#             print(f"DEBUG (StratigraphicColumn._draw_y_axis): Drew metre mark at {current_whole_metre:.0f}m, y_pos={y_pos:.1f}px")
            
            current_whole_metre += 1.0
        
        # Draw minor ticks ONLY when zoomed in enough (pixels between ticks > 5px)
        # This prevents solid gray bar from too many tick marks
        pixels_between_minor_ticks = self.depth_scale * minor_tick_interval
        
        if pixels_between_minor_ticks > 5.0:  # Only draw if at least 5px between minor ticks
            start_minor = np.floor(min_depth / minor_tick_interval) * minor_tick_interval
            end_minor = np.ceil(max_depth / minor_tick_interval) * minor_tick_interval
            
            current_minor = start_minor
            minor_tick_count = 0
            while current_minor <= end_minor and minor_tick_count < 500:  # Safety limit
                pass
                # Skip whole metres (already drawn as major ticks)
                if abs(current_minor % 1.0) >= 0.001:
                    y_pos = (current_minor - self.min_depth) * self.depth_scale
                    # Draw very short, thin minor tick (2px long)
                    self.scene.addLine(self.y_axis_width - 2, y_pos, self.y_axis_width, y_pos, axis_pen)
                    minor_tick_count += 1
                
                current_minor += minor_tick_interval
            
            print(f"DEBUG (StratigraphicColumn._draw_y_axis): Drew {minor_tick_count} minor ticks "
                  f"(pixels_between_minor_ticks={pixels_between_minor_ticks:.1f}px > 5px)")
        else:
            pass  # Skipping minor ticks - too dense
#             print(f"DEBUG (StratigraphicColumn._draw_y_axis): Skipping minor ticks - too dense "
#                   f"(pixels_between_minor_ticks={pixels_between_minor_ticks:.1f}px <= 5px)")
        
        print(f"DEBUG (StratigraphicColumn._draw_y_axis): Drew {end_whole_metre - start_whole_metre + 1:.0f} whole metre marks")
        
        # Draw engineering scale display (top-left corner)
        if self.show_scale_display and not self.overview_mode:
            self._draw_scale_display(y_top)
        
        # Remove the old depth labels from the units
        # The previous code for from_depth_text and to_depth_text is removed as it's replaced by the Y-axis.

        # Re-highlight the previously selected unit if data is redrawn
        if self.selected_unit_index is not None:
            self._update_highlight()

    def _draw_scale_display(self, y_top):
        """Draw engineering scale display in top-left corner."""
        # Create scale text
        scale_text = f"Scale: {self.current_scale_label}"
        
        # Create text item
        scale_font = QFont("Arial", 9, QFont.Weight.Bold)
        scale_text_item = QGraphicsTextItem(scale_text)
        scale_text_item.setFont(scale_font)
        scale_text_item.setDefaultTextColor(QColor(0, 0, 0))  # Black
        
        # Position in top-left corner with padding
        padding = 5
        scale_text_item.setPos(padding, y_top + padding)
        
        # Add to scene
        self.scene.addItem(scale_text_item)
        
#         print(f"DEBUG (StratigraphicColumn._draw_scale_display): Added scale display: {scale_text}")
    
    def _on_scale_changed(self, pixels_per_metre, scale_label):
        """Handle scale changes from converter."""
        # Update depth scale if not in overview mode with locked scale
        if not (self.overview_mode and self.overview_scale_locked):
            self.depth_scale = pixels_per_metre
            self.current_scale_label = scale_label
            print(f"DEBUG (StratigraphicColumn._on_scale_changed): Scale changed: {scale_label} ({pixels_per_metre:.1f} px/m)")
            
            # Redraw if we have data
            if self.units_dataframe is not None and not self.units_dataframe.empty:
                self.draw_column(self.units_dataframe, self.min_depth, self.max_depth)
    
    def set_engineering_scale(self, scale_label):
        """
        Set engineering scale.
        
        Args:
            scale_label: Engineering scale label (e.g., '1:50', '1:200')
        
        Returns:
            bool: True if scale was changed, False otherwise
        """
        return self.scale_converter.set_scale(scale_label)
    
    def get_engineering_scale(self):
        """Get current engineering scale information."""
        return self.scale_converter.get_scale_info()
    
    def highlight_unit(self, unit_index):
        """Highlight the specified unit by index. Pass None to clear highlighting."""
        self.selected_unit_index = unit_index
        self._update_highlight()

    def _update_highlight(self):
        """Update the highlight rectangle over the selected unit."""
        # Remove existing highlight
        if self.highlight_rect_item is not None:
            self.scene.removeItem(self.highlight_rect_item)
            self.highlight_rect_item = None

        # Add new highlight if a unit is selected
        if self.selected_unit_index is not None and self.units_dataframe is not None:
            if 0 <= self.selected_unit_index < len(self.units_dataframe):
                unit = self.units_dataframe.iloc[self.selected_unit_index]

                from_depth = unit['from_depth']
                to_depth = unit['to_depth']
                thickness = unit[RECOVERED_THICKNESS_COLUMN]

                # Calculate position and size
                y_start = (from_depth - self.min_depth) * self.depth_scale
                rect_height = thickness * self.depth_scale

                # Apply minimum display height for very thin units
                if rect_height > 0 and rect_height < self.min_display_height_pixels:
                    rect_height = self.min_display_height_pixels

                if rect_height <= 0:
                    return

                # Create highlight rectangle (slightly larger than unit for visibility)
                highlight_rect = QGraphicsRectItem(
                    self.y_axis_width - 2, y_start - 1,
                    self.column_width + 4, rect_height + 2
                )

                # Set highlight style - thick yellow border
                highlight_pen = QPen(QColor(255, 255, 0))  # Yellow
                highlight_pen.setWidth(3)
                highlight_rect.setPen(highlight_pen)
                highlight_rect.setBrush(QBrush(Qt.BrushStyle.NoBrush))  # No fill

                # Add to scene and store reference
                self.scene.addItem(highlight_rect)
                self.highlight_rect_item = highlight_rect

    def mousePressEvent(self, event):
        """Handle mouse clicks to select units."""
        pos = self.mapToScene(event.pos())
        # Find which unit was clicked
        if self.units_dataframe is not None:
            for idx, unit in self.units_dataframe.iterrows():
                from_depth = unit['from_depth']
                to_depth = unit['to_depth']
                y_start = (from_depth - self.min_depth) * self.depth_scale
                y_end = y_start + (to_depth - from_depth) * self.depth_scale
                # Check if click is within column area (x between y_axis_width and y_axis_width+column_width)
                if (self.y_axis_width <= pos.x() <= self.y_axis_width + self.column_width and
                    y_start <= pos.y() <= y_end):
                    self.selected_unit_index = idx
                    self._update_highlight()
                    self.unitClicked.emit(idx)
                    break
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        """Handle wheel events for zooming."""
        # In overview mode, ignore wheel events - overview should not zoom or scroll
        if self.overview_mode:
            pass
#             print(f"DEBUG (StratigraphicColumn.wheelEvent): Ignoring wheel event in overview mode")
            event.ignore()
            return
            
        # Allow normal wheel behavior for non-overview mode
        super().wheelEvent(event)

    def fitInView(self, rect, mode=Qt.AspectRatioMode.IgnoreAspectRatio):
        """Override fitInView to handle overview mode with padding."""
        if self.overview_mode:
            pass
            # In overview mode: Use KeepAspectRatio to maintain proper scaling
            # This ensures consistent behavior during resize events
            
            # Validate rectangle
            if rect.width() <= 0 or rect.height() <= 0:
                print(f"WARNING (StratigraphicColumn.fitInView): Invalid rectangle for overview mode: {rect.width():.1f}x{rect.height():.1f}")
                return
            
#             print(f"DEBUG (StratigraphicColumn.fitInView): Overview mode - using KeepAspectRatio with padding")
            print(f"DEBUG (StratigraphicColumn.fitInView): Viewport: {self.viewport().size().width()}x{self.viewport().size().height()}")
#             print(f"DEBUG (StratigraphicColumn.fitInView): Scene rect: {rect.width():.1f}x{rect.height():.1f}")
            
            # Use percentage-based padding that adapts to viewport size
            # 5% padding on sides, 10% padding top/bottom for better vertical fit
            viewport_width = self.viewport().size().width()
            viewport_height = self.viewport().size().height()
            
            # Calculate padding as percentage of viewport size
            width_padding_pct = 0.05  # 5% padding on sides
            height_padding_pct = 0.10  # 10% padding top/bottom
            
            width_padding = max(viewport_width * width_padding_pct, 2.0)
            height_padding = max(viewport_height * height_padding_pct, 2.0)
            
            padded_rect = rect.adjusted(-width_padding, -height_padding, width_padding, height_padding)
            
            # For overview mode with KeepAspectRatio: Calculate scale to fit within padded area
            target_width = viewport_width - (2 * width_padding)
            target_height = viewport_height - (2 * height_padding)
            target_width = max(target_width, 1.0)
            target_height = max(target_height, 1.0)
            
            if padded_rect.width() > 0 and padded_rect.height() > 0:
                pass
                # Calculate scale factors for width and height
                width_scale = target_width / padded_rect.width()
                height_scale = target_height / padded_rect.height()
                
                # For KeepAspectRatio, use the smaller scale to ensure everything fits
                scale = min(width_scale, height_scale)
                
                scaled_width = padded_rect.width() * scale
                scaled_height = padded_rect.height() * scale
                
                print(f"DEBUG (StratigraphicColumn.fitInView): KeepAspectRatio optimization:")
#                 print(f"DEBUG (StratigraphicColumn.fitInView):   Viewport: {viewport_width}x{viewport_height}px")
                print(f"DEBUG (StratigraphicColumn.fitInView):   Padding: {width_padding:.1f}px L/R, {height_padding:.1f}px T/B")
#                 print(f"DEBUG (StratigraphicColumn.fitInView):   Target area: {target_width:.1f}x{target_height:.1f}px")
                print(f"DEBUG (StratigraphicColumn.fitInView):   Padded rect: {padded_rect.width():.1f}x{padded_rect.height():.1f}px")
#                 print(f"DEBUG (StratigraphicColumn.fitInView):   Calculated scale: {scale:.4f} (width_scale={width_scale:.4f}, height_scale={height_scale:.4f})")
                print(f"DEBUG (StratigraphicColumn.fitInView):   Scaled size: {scaled_width:.1f}x{scaled_height:.1f}px")
                
                # Apply the calculated scale
                self.setTransform(QTransform.fromScale(scale, scale))
                
                # Center the view on the padded rectangle
                self.centerOn(padded_rect.center())
                
#                 print(f"DEBUG (StratigraphicColumn.fitInView): Applied transform with scale: {scale:.4f}")
                print(f"DEBUG (StratigraphicColumn.fitInView): Expected fill: {scaled_height/viewport_height*100:.1f}% vertical, {scaled_width/viewport_width*100:.1f}% horizontal")
                
                # Force immediate update
                self.viewport().update()
            else:
                # Fallback to normal fitInView with KeepAspectRatio
                super().fitInView(padded_rect, Qt.AspectRatioMode.KeepAspectRatio)
        else:
            # Allow normal fitInView behavior for non-overview mode
            super().fitInView(rect, mode)

    def resizeEvent(self, event):
        """Handle resize events to update overview scale if needed."""
        # Call parent resize event first
        super().resizeEvent(event)
        
        # If in overview mode, immediately reapply fitInView with new viewport size
        if self.overview_mode:
            pass
#             print(f"DEBUG (StratigraphicColumn.resizeEvent): === RESIZE EVENT TRIGGERED ===")
            print(f"DEBUG (StratigraphicColumn.resizeEvent): Old size: {event.oldSize().width()}x{event.oldSize().height()}")
#             print(f"DEBUG (StratigraphicColumn.resizeEvent): New size: {event.size().width()}x{event.size().height()}")
            print(f"DEBUG (StratigraphicColumn.resizeEvent): Viewport: {self.viewport().size().width()}x{self.viewport().size().height()}")
#             print(f"DEBUG (StratigraphicColumn.resizeEvent): Scene rect: {self.scene.sceneRect().width():.1f}x{self.scene.sceneRect().height():.1f}")
            
            # Always reapply fitInView for overview mode, even if we don't have data yet
            # This ensures immediate rescaling on any resize
            if not self.scene.sceneRect().isEmpty():
                print(f"DEBUG (StratigraphicColumn.resizeEvent): Reapplying fitInView with padding")
                # Force immediate update by calling our overridden fitInView
                self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
                
                # Force immediate repaint
                self.viewport().update()
#                 print(f"DEBUG (StratigraphicColumn.resizeEvent): Forced immediate update")
            else:
                print(f"DEBUG (StratigraphicColumn.resizeEvent): Scene rect is empty, cannot apply fitInView")
            
#             print(f"DEBUG (StratigraphicColumn.resizeEvent): === RESIZE COMPLETE ===")
            
            # DO NOT redraw the column - this resets the scaling
            # The fitInView call above already handles the scaling correctly
            # Redrawing would recreate the scene and lose the applied transform
            # Only update zoom overlay if needed
            if hasattr(self, 'current_zoom_min') and hasattr(self, 'current_zoom_max'):
                if self.current_zoom_min != 0.0 or self.current_zoom_max != 100.0:
                    print(f"DEBUG (StratigraphicColumn.resizeEvent): Updating zoom overlay after resize")
                    self.update_zoom_overlay(self.current_zoom_min, self.current_zoom_max)

    def scroll_to_depth(self, depth):
        """Scroll the view to make the given depth visible."""
        # In overview mode, ignore scroll commands - overview should not scroll
        if self.overview_mode:
            pass
#             print(f"DEBUG (StratigraphicColumn.scroll_to_depth): Ignoring scroll command in overview mode (depth={depth})")
            return
            
        # Add validation for depth scale
        if not hasattr(self, 'depth_scale') or self.depth_scale <= 0:
            print(f"WARNING: Invalid depth_scale in scroll_to_depth: {getattr(self, 'depth_scale', 'NOT SET')}")
            return
            
        # Add validation for depth range
        if not hasattr(self, 'min_depth') or not hasattr(self, 'max_depth'):
            print(f"WARNING: Missing depth range attributes in scroll_to_depth")
            return
        
        # Calculate y position
        y = (depth - self.min_depth) * self.depth_scale
        
        # Center the view on this y coordinate
        view_height = self.viewport().height()
        
        # Validate view height
        if view_height <= 0:
            pass
#             print(f"WARNING: Invalid view height in scroll_to_depth: {view_height}")
            return
            
        scroll_value = int(y - view_height / 2)
        
        # Clamp to valid range
        scroll_max = self.verticalScrollBar().maximum()
        scroll_value = max(0, min(scroll_value, scroll_max))
        self.verticalScrollBar().setValue(scroll_value)
    def set_overview_mode(self, enabled, hole_min_depth=0.0, hole_max_depth=500.0):
        """Enable or disable overview mode (showing entire hole)."""
#         print(f"DEBUG (StratigraphicColumn.set_overview_mode): Setting overview_mode={enabled}, hole_min_depth={hole_min_depth}, hole_max_depth={hole_max_depth}")
        
        self.overview_mode = enabled
        if enabled:
            pass
            # Store hole depth range for overview mode
            self.hole_min_depth = hole_min_depth
            self.hole_max_depth = hole_max_depth
            
            # In overview mode, we ALWAYS show the entire hole from top to bottom
            self.min_depth = hole_min_depth
            self.max_depth = hole_max_depth
            
            # For overview mode, use a smaller fixed width that fits in the pane
            # Store the original width and set a smaller width for overview
            if not hasattr(self, 'original_column_width'):
                self.original_column_width = self.column_width
            
            # Set overview width to fit pane (approximately 100px for overview)
            self.column_width = 100  # Fixed width for overview pane
            print(f"DEBUG (StratigraphicColumn.set_overview_mode): Set overview column_width={self.column_width}px (original={self.original_column_width}px)")
            
            # Don't calculate fixed scale - we'll use fitInView instead
            self.overview_scale_locked = False  # Not using manual scale anymore
            
            # Set overview engineering scale to 1:200
            self.set_engineering_scale('1:200')
#             print(f"DEBUG (StratigraphicColumn.set_overview_mode): Set overview engineering scale to 1:200")
            
            print(f"DEBUG (StratigraphicColumn.set_overview_mode): Using fitInView with padding (5% L/R, 10% T/B)")
            
            # If we already have a scene rect, immediately apply fitInView
            if not self.scene.sceneRect().isEmpty():
                pass
#                 print(f"DEBUG (StratigraphicColumn.set_overview_mode): Immediately applying fitInView")
                self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            # Disable overview mode - restore original width
            if hasattr(self, 'original_column_width'):
                self.column_width = self.original_column_width
                print(f"DEBUG (StratigraphicColumn.set_overview_mode): Restored column_width={self.column_width}px")
            self.overview_scale_locked = False
    
    def force_overview_rescale(self):
        """Force immediate rescale of overview column (call after pane/window resize)."""
        if self.overview_mode and not self.scene.sceneRect().isEmpty():
            pass
#             print(f"DEBUG (StratigraphicColumn.force_overview_rescale): === MANUAL RESCALE TRIGGERED ===")
            print(f"DEBUG (StratigraphicColumn.force_overview_rescale): Viewport: {self.viewport().size().width()}x{self.viewport().size().height()}")
#             print(f"DEBUG (StratigraphicColumn.force_overview_rescale): Scene: {self.scene.sceneRect().width():.1f}x{self.scene.sceneRect().height():.1f}")
            
            # Call fitInView to apply scaling with padding
            self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            
            # Force immediate update
            self.viewport().update()
            print(f"DEBUG (StratigraphicColumn.force_overview_rescale): === MANUAL RESCALE COMPLETE ===")
            return True
        return False
    
    def update_zoom_overlay(self, zoom_min_depth, zoom_max_depth):
        """Update the zoom overlay rectangle showing current plot view region (Subtask 3.3)."""
#         print(f"DEBUG (StratigraphicColumn.update_zoom_overlay): zoom_min={zoom_min_depth}, zoom_max={zoom_max_depth}, overview_mode={self.overview_mode}")
        
        self.current_zoom_min = zoom_min_depth
        self.current_zoom_max = zoom_max_depth
        
        if not self.overview_mode:
            print(f"DEBUG (StratigraphicColumn.update_zoom_overlay): Not in overview mode, skipping overlay")
            return  # Only show overlay in overview mode
            
        # Validate depth scale and range
        if not hasattr(self, 'depth_scale') or self.depth_scale <= 0:
            pass
#             print(f"WARNING (StratigraphicColumn.update_zoom_overlay): Invalid depth_scale: {getattr(self, 'depth_scale', 'NOT SET')}")
            return
            
        if not hasattr(self, 'min_depth'):
            print(f"WARNING (StratigraphicColumn.update_zoom_overlay): min_depth not set")
            return
            
        # Remove existing overlay
        if self.zoom_overlay_rect is not None:
            self.scene.removeItem(self.zoom_overlay_rect)
            self.zoom_overlay_rect = None
            
        # Calculate overlay position and size
        y_start = (zoom_min_depth - self.min_depth) * self.depth_scale
        overlay_height = (zoom_max_depth - zoom_min_depth) * self.depth_scale
        
#         print(f"DEBUG (StratigraphicColumn.update_zoom_overlay): y_start={y_start:.1f}, overlay_height={overlay_height:.1f}, depth_scale={self.depth_scale:.4f}")
        
        # Validate overlay position and size
        if overlay_height <= 0:
            print(f"WARNING (StratigraphicColumn.update_zoom_overlay): Invalid overlay height: {overlay_height}")
            return
            
        # Create semi-transparent overlay rectangle
        self.zoom_overlay_rect = QGraphicsRectItem(
            self.y_axis_width, y_start,
            self.column_width, overlay_height
        )
        
        # Set overlay style - semi-transparent blue with border
        overlay_pen = QPen(QColor(0, 0, 255, 200))  # Semi-transparent blue
        overlay_pen.setWidth(2)
        self.zoom_overlay_rect.setPen(overlay_pen)
        
        overlay_brush = QBrush(QColor(0, 0, 255, 50))  # Very transparent blue fill
        self.zoom_overlay_rect.setBrush(overlay_brush)
        
        # Add to scene
        self.scene.addItem(self.zoom_overlay_rect)
        
        # Ensure overlay is on top of other items
        self.zoom_overlay_rect.setZValue(100)
