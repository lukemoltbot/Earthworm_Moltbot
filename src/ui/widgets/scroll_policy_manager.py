"""
ScrollPolicyManager - Utility class for managing scroll policies in Earthworm Moltbot.

This class provides static methods to configure scrolling behavior for different
widget types, specifically designed to disable horizontal scrolling while maintaining
vertical scrolling for geological curve displays.

Features:
- Disable horizontal scrolling for PyQtGraph PlotWidget
- Disable horizontal scrolling for QGraphicsView
- Configure vertical-only scrolling for touchpad and mouse wheel
- Fixed-width constraint for geological curve displays
"""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtCore import Qt
import pyqtgraph as pg


class ScrollPolicyManager:
    """Utility class for managing scroll policies in Earthworm Moltbot."""
    
    @staticmethod
    def disable_horizontal_scrolling(widget):
        """
        Disable horizontal scrolling for a widget.
        
        Args:
            widget: A QGraphicsView or PyQtGraph PlotWidget
        """
        if isinstance(widget, QGraphicsView):
            ScrollPolicyManager._disable_horizontal_scrolling_qgraphicsview(widget)
        elif isinstance(widget, pg.PlotWidget):
            ScrollPolicyManager._disable_horizontal_scrolling_pyqtgraph(widget)
        else:
            print(f"Warning: Unsupported widget type for scroll policy: {type(widget)}")
    
    @staticmethod
    def enable_vertical_only(widget):
        """
        Configure vertical-only scrolling for a widget.
        
        Args:
            widget: A QGraphicsView or PyQtGraph PlotWidget
        """
        if isinstance(widget, QGraphicsView):
            ScrollPolicyManager._enable_vertical_only_qgraphicsview(widget)
        elif isinstance(widget, pg.PlotWidget):
            ScrollPolicyManager._enable_vertical_only_pyqtgraph(widget)
        else:
            print(f"Warning: Unsupported widget type for scroll policy: {type(widget)}")
    
    @staticmethod
    def _disable_horizontal_scrolling_qgraphicsview(view):
        """
        Disable horizontal scrolling for QGraphicsView.
        
        Implementation:
        1. Set horizontal scroll bar policy to always off
        2. Set drag mode to prevent horizontal drag
        3. Override wheel event to ignore horizontal wheel movement
        """
        # Set scroll bar policies
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Set drag mode to prevent horizontal dragging
        # Use NoDrag mode and handle vertical-only dragging manually if needed
        view.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # Store original wheel event for potential override
        if not hasattr(view, '_original_wheel_event'):
            view._original_wheel_event = view.wheelEvent
        
        # Override wheel event to ignore horizontal wheel
        def custom_wheel_event(event):
            # Only process vertical wheel events
            if event.angleDelta().x() == 0:  # Vertical wheel movement
                view._original_wheel_event(event)
            # Horizontal wheel events are ignored
        
        view.wheelEvent = custom_wheel_event
        
        # Ensure fitInView maintains fixed width
        original_fit_in_view = view.fitInView
        
        def custom_fit_in_view(rect, mode=Qt.AspectRatioMode.KeepAspectRatio):
            # Maintain fixed width constraint
            scene_rect = view.scene().sceneRect() if view.scene() else rect
            fixed_width = scene_rect.width()
            
            # Create a new rect with fixed width
            fixed_rect = QRectF(rect.x(), rect.y(), fixed_width, rect.height())
            
            # Call original fitInView with fixed width
            return original_fit_in_view(fixed_rect, mode)
        
        view.fitInView = custom_fit_in_view
    
    @staticmethod
    def _disable_horizontal_scrolling_pyqtgraph(plot_widget):
        """
        Disable horizontal scrolling for PyQtGraph PlotWidget.
        
        Implementation:
        1. Disable mouse interaction on X-axis
        2. Set fixed X-axis range constraints
        3. Configure touchpad/mouse wheel for vertical-only scrolling
        """
        # Disable mouse interaction on X-axis
        plot_widget.setMouseEnabled(x=False, y=True)
        
        # Disable horizontal panning
        plot_widget.plotItem.vb.setMouseEnabled(x=False, y=True)
        
        # Store original wheel event for potential override
        if not hasattr(plot_widget, '_original_wheel_event'):
            plot_widget._original_wheel_event = plot_widget.wheelEvent
        
        # Override wheel event to ignore horizontal wheel
        def custom_wheel_event(event):
            # Only process vertical wheel events
            if event.angleDelta().x() == 0:  # Vertical wheel movement
                plot_widget._original_wheel_event(event)
            # Horizontal wheel events are ignored
        
        plot_widget.wheelEvent = custom_wheel_event
        
        # Configure for vertical-only touchpad scrolling
        # PyQtGraph handles touchpad through mouse events, so disabling X mouse is sufficient
    
    @staticmethod
    def _enable_vertical_only_qgraphicsview(view):
        """
        Configure vertical-only scrolling for QGraphicsView.
        
        This is a more comprehensive version that ensures only vertical scrolling works.
        """
        # Apply all horizontal scrolling disable methods
        ScrollPolicyManager._disable_horizontal_scrolling_qgraphicsview(view)
        
        # Additionally, ensure vertical scroll bar is always on
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Configure for touchpad two-finger scrolling (vertical only)
        # This is handled by the wheel event override in _disable_horizontal_scrolling_qgraphicsview
    
    @staticmethod
    def _enable_vertical_only_pyqtgraph(plot_widget):
        """
        Configure vertical-only scrolling for PyQtGraph PlotWidget.
        
        This is a more comprehensive version that ensures only vertical scrolling works.
        """
        # Apply all horizontal scrolling disable methods
        ScrollPolicyManager._disable_horizontal_scrolling_pyqtgraph(plot_widget)
        
        # Configure plot item for vertical-only interaction
        plot_item = plot_widget.plotItem
        
        # Ensure Y-axis mouse interaction is enabled
        plot_item.vb.setMouseEnabled(x=False, y=True)
        
        # Set Y-axis range padding to prevent accidental horizontal movement
        # This helps maintain fixed X-axis view
        
        # Configure for touchpad two-finger scrolling
        # PyQtGraph's mouse handling should respect the x=False setting
    
    @staticmethod
    def apply_fixed_width_constraint(widget, fixed_width):
        """
        Apply fixed width constraint to a widget.
        
        Args:
            widget: A QGraphicsView or PyQtGraph PlotWidget
            fixed_width: The fixed width to maintain
        """
        if isinstance(widget, QGraphicsView):
            ScrollPolicyManager._apply_fixed_width_qgraphicsview(widget, fixed_width)
        elif isinstance(widget, pg.PlotWidget):
            ScrollPolicyManager._apply_fixed_width_pyqtgraph(widget, fixed_width)
    
    @staticmethod
    def _apply_fixed_width_qgraphicsview(view, fixed_width):
        """
        Apply fixed width constraint to QGraphicsView.
        """
        # Store the fixed width
        view.fixed_width = fixed_width
        
        # Override resize event to maintain fixed width
        original_resize_event = view.resizeEvent
        
        def custom_resize_event(event):
            # Call original resize event
            if original_resize_event:
                original_resize_event(event)
            
            # Set fixed width
            view.setFixedWidth(fixed_width)
            
            # Update scene rect if scene exists
            if view.scene():
                scene_rect = view.scene().sceneRect()
                if scene_rect.width() != fixed_width:
                    new_rect = QRectF(scene_rect.x(), scene_rect.y(), fixed_width, scene_rect.height())
                    view.scene().setSceneRect(new_rect)
        
        view.resizeEvent = custom_resize_event
        
        # Set initial fixed width
        view.setFixedWidth(fixed_width)
    
    @staticmethod
    def _apply_fixed_width_pyqtgraph(plot_widget, fixed_width):
        """
        Apply fixed width constraint to PyQtGraph PlotWidget.
        """
        # Set fixed width
        plot_widget.setFixedWidth(fixed_width)
        
        # Configure plot item to maintain aspect ratio
        plot_item = plot_widget.plotItem
        
        # Disable auto-range on X-axis to maintain fixed view
        plot_item.vb.disableAutoRange(axis=pg.ViewBox.XAxis)
        
        # Store original width for reference
        plot_widget.fixed_width = fixed_width
        
        # Override resize event to maintain fixed width
        original_resize_event = plot_widget.resizeEvent
        
        def custom_resize_event(event):
            # Call original resize event
            if original_resize_event:
                original_resize_event(event)
            
            # Maintain fixed width
            plot_widget.setFixedWidth(fixed_width)
            
            # Update plot item layout if needed
            plot_item.layout.setColumnFixedWidth(0, fixed_width)
        
        plot_widget.resizeEvent = custom_resize_event