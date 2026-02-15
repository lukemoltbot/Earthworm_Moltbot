"""
Scale Keyboard Controls - Handles CTRL+wheel scale adjustment for engineering scales.

This module provides:
1. ScaleKeyboardControls class for handling keyboard/mouse events
2. CTRL+wheel scale adjustment integration
3. Keyboard shortcuts for scale presets
4. Integration with EngineeringScaleConverter
"""

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent, QWheelEvent
from .scale_converter import EngineeringScaleConverter


class ScaleKeyboardControls(QObject):
    """
    Handles keyboard and mouse wheel events for scale adjustment.
    
    Features:
    - CTRL+wheel: Adjust engineering scale (zoom in/out)
    - Keyboard shortcuts: 1-6 for scale presets
    - Integration with EngineeringScaleConverter
    - Event filtering for parent widgets
    """
    
    # Signals
    scaleAdjusted = pyqtSignal(float, str)  # pixels_per_metre, scale_label
    scalePresetSelected = pyqtSignal(str)  # scale_label
    
    # Keyboard shortcuts for scale presets
    SCALE_SHORTCUTS = {
        Qt.Key.Key_1: '1:10',
        Qt.Key.Key_2: '1:20',
        Qt.Key.Key_3: '1:50',
        Qt.Key.Key_4: '1:100',
        Qt.Key.Key_5: '1:200',
        Qt.Key.Key_6: '1:500',
    }
    
    def __init__(self, parent=None, scale_converter=None):
        """
        Initialize scale keyboard controls.
        
        Args:
            parent: Parent widget for event filtering
            scale_converter: EngineeringScaleConverter instance (optional)
        """
        super().__init__(parent)
        
        # Scale converter
        if scale_converter is None:
            self.scale_converter = EngineeringScaleConverter()
        else:
            self.scale_converter = scale_converter
        
        # Connect scale converter signals
        self.scale_converter.scaleChanged.connect(self._on_scale_changed)
        
        # Event filtering
        self._parent_widget = parent
        if parent:
            parent.installEventFilter(self)
        
        # Scale adjustment enabled
        self._enabled = True
        
        # Debug logging
        self._debug = False
    
    def set_enabled(self, enabled):
        """Enable or disable scale keyboard controls."""
        self._enabled = enabled
    
    def is_enabled(self):
        """Check if scale keyboard controls are enabled."""
        return self._enabled
    
    def set_scale_converter(self, scale_converter):
        """Set the scale converter instance."""
        if self.scale_converter:
            self.scale_converter.scaleChanged.disconnect(self._on_scale_changed)
        
        self.scale_converter = scale_converter
        if scale_converter:
            scale_converter.scaleChanged.connect(self._on_scale_changed)
    
    def eventFilter(self, obj, event):
        """
        Filter events for scale adjustment.
        
        Handles:
        - Wheel events with CTRL modifier
        - Key press events for scale presets
        """
        if not self._enabled:
            return False
        
        # Handle wheel events with CTRL modifier
        if event.type() == event.Type.Wheel:
            wheel_event = QWheelEvent(event)
            modifiers = wheel_event.modifiers()
            
            # Check if CTRL is pressed
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                # Get wheel delta
                delta = wheel_event.angleDelta().y()
                
                # Adjust scale
                if self.scale_converter.adjust_scale(delta, ctrl_pressed=True):
                    if self._debug:
                        print(f"Scale adjusted: CTRL+wheel delta={delta}")
                    return True  # Event handled
        
        # Handle key press events for scale presets
        elif event.type() == event.Type.KeyPress:
            key_event = QKeyEvent(event)
            key = key_event.key()
            
            # Check for scale preset shortcuts (1-6)
            if key in self.SCALE_SHORTCUTS:
                scale_label = self.SCALE_SHORTCUTS[key]
                if self.scale_converter.set_scale(scale_label):
                    if self._debug:
                        print(f"Scale preset selected: {scale_label}")
                    self.scalePresetSelected.emit(scale_label)
                    return True  # Event handled
        
        return False  # Event not handled
    
    def _on_scale_changed(self, pixels_per_metre, scale_label):
        """Handle scale change from converter."""
        self.scaleAdjusted.emit(pixels_per_metre, scale_label)
    
    def handle_wheel_event(self, wheel_event):
        """
        Handle wheel event directly (alternative to event filtering).
        
        Args:
            wheel_event: QWheelEvent
        
        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self._enabled:
            return False
        
        modifiers = wheel_event.modifiers()
        
        # Check if CTRL is pressed
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            # Get wheel delta
            delta = wheel_event.angleDelta().y()
            
            # Adjust scale
            if self.scale_converter.adjust_scale(delta, ctrl_pressed=True):
                if self._debug:
                    print(f"Scale adjusted via handle_wheel_event: CTRL+wheel delta={delta}")
                return True
        
        return False
    
    def handle_key_event(self, key_event):
        """
        Handle key event directly (alternative to event filtering).
        
        Args:
            key_event: QKeyEvent
        
        Returns:
            bool: True if event was handled, False otherwise
        """
        if not self._enabled:
            return False
        
        # Check for scale preset shortcuts (1-6)
        key = key_event.key()
        if key in self.SCALE_SHORTCUTS:
            scale_label = self.SCALE_SHORTCUTS[key]
            if self.scale_converter.set_scale(scale_label):
                if self._debug:
                    print(f"Scale preset selected via handle_key_event: {scale_label}")
                self.scalePresetSelected.emit(scale_label)
                return True
        
        return False
    
    def get_current_scale(self):
        """Get current scale from converter."""
        return self.scale_converter.get_current_scale()
    
    def get_scale_label(self):
        """Get current scale label."""
        return self.scale_converter.get_scale_label()
    
    def get_pixels_per_metre(self):
        """Get current pixels per metre."""
        return self.scale_converter.get_pixels_per_metre()
    
    def set_scale(self, scale_label):
        """Set scale via converter."""
        return self.scale_converter.set_scale(scale_label)
    
    def zoom_in(self):
        """Zoom in via converter."""
        return self.scale_converter.zoom_in()
    
    def zoom_out(self):
        """Zoom out via converter."""
        return self.scale_converter.zoom_out()
    
    def enable_debug_logging(self, enabled):
        """Enable or disable debug logging."""
        self._debug = enabled
    
    def get_scale_info(self):
        """Get scale information from converter."""
        return self.scale_converter.get_scale_info()


# Factory function for easy integration
def create_scale_keyboard_controls(parent_widget, scale_converter=None):
    """
    Create and install scale keyboard controls on a widget.
    
    Args:
        parent_widget: Widget to install event filter on
        scale_converter: EngineeringScaleConverter instance (optional)
    
    Returns:
        ScaleKeyboardControls: The created controls instance
    """
    controls = ScaleKeyboardControls(parent_widget, scale_converter)
    return controls