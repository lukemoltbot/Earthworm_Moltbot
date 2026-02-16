"""
Scale Converter - Converts between engineering scales (1:50, 1:200) and pixel-based scaling.

This module provides:
1. EngineeringScaleConverter class for DPI-based scale calculations
2. Conversion between pixels/metre and engineering scales
3. Standard engineering scale presets (1:10, 1:20, 1:50, 1:100, 1:200, 1:500)
4. Keyboard scale adjustment with CTRL+wheel support
5. Backward compatibility with existing pixel-based scaling
"""

import math
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QGuiApplication


class EngineeringScaleConverter(QObject):
    """
    Converts between engineering scales and pixel-based scaling.
    
    Engineering scales (e.g., 1:50) represent the ratio between:
    - 1 unit on the drawing (e.g., 1mm on screen)
    - 50 units in real world (e.g., 50mm = 0.05m)
    
    For display purposes, we convert to pixels per metre based on screen DPI.
    """
    
    # Signal emitted when scale changes
    scaleChanged = pyqtSignal(float, str)  # pixels_per_metre, scale_label
    
    # Standard engineering scales for borehole logging
    STANDARD_SCALES = {
        '1:10': 10,      # Very detailed view
        '1:20': 20,      # Detailed view
        '1:50': 50,      # Standard detailed view (default)
        '1:100': 100,    # Intermediate view
        '1:200': 200,    # Overview view (default overview)
        '1:500': 500,    # Very wide overview
    }
    
    # Scale display names
    SCALE_DISPLAY_NAMES = {
        '1:10': '1:10',
        '1:20': '1:20',
        '1:50': '1:50',
        '1:100': '1:100',
        '1:200': '1:200',
        '1:500': '1:500',
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Screen DPI (default to 96 DPI if not available)
        self._screen_dpi = self._get_screen_dpi()
        
        # Current scale state
        self._current_scale = '1:50'  # Default detailed view
        self._pixels_per_metre = self._calculate_pixels_per_metre(self._current_scale)
        
        # Scale adjustment step (for CTRL+wheel)
        self._scale_step = 0.1  # 10% adjustment per wheel tick
        
        # Backward compatibility mode
        self._compatibility_mode = True  # Maintain pixel-based scaling
        
    def _get_screen_dpi(self):
        """Get the screen DPI for accurate scale calculations."""
        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                # Get physical DPI (not logical DPI which can be scaled)
                physical_dpi = screen.physicalDotsPerInch()
                if physical_dpi > 0:
                    return physical_dpi
        except:
            pass
        
        # Fallback to standard 96 DPI
        return 96.0
    
    def _calculate_pixels_per_metre(self, scale_label):
        """
        Calculate pixels per metre for a given engineering scale.
        
        Formula:
        - 1:scale means 1mm on drawing = scale mm in real world
        - So 1mm on screen = scale mm in real world
        - Convert to metres: 1mm = scale/1000 metres
        - Pixels per metre = (pixels per mm) * (1000 / scale)
        - Pixels per mm = DPI / 25.4 (since 1 inch = 25.4mm)
        
        Final formula: pixels_per_metre = (DPI / 25.4) * (1000 / scale)
        """
        if scale_label not in self.STANDARD_SCALES:
            raise ValueError(f"Unknown scale: {scale_label}")
        
        scale = self.STANDARD_SCALES[scale_label]
        
        # Calculate pixels per metre
        pixels_per_mm = self._screen_dpi / 25.4
        pixels_per_metre = pixels_per_mm * (1000.0 / scale)
        
        return pixels_per_metre
    
    def get_current_scale(self):
        """Get current scale as (scale_label, pixels_per_metre)."""
        return self._current_scale, self._pixels_per_metre
    
    def get_scale_label(self):
        """Get current scale label (e.g., '1:50')."""
        return self._current_scale
    
    def get_pixels_per_metre(self):
        """Get current pixels per metre value."""
        return self._pixels_per_metre
    
    def get_display_name(self):
        """Get display name for current scale."""
        return self.SCALE_DISPLAY_NAMES.get(self._current_scale, self._current_scale)
    
    def set_scale(self, scale_label):
        """
        Set the engineering scale.
        
        Args:
            scale_label: One of the STANDARD_SCALES keys (e.g., '1:50')
        
        Returns:
            bool: True if scale was changed, False otherwise
        """
        if scale_label not in self.STANDARD_SCALES:
            return False
        
        if scale_label != self._current_scale:
            self._current_scale = scale_label
            self._pixels_per_metre = self._calculate_pixels_per_metre(scale_label)
            self.scaleChanged.emit(self._pixels_per_metre, self.get_display_name())
            return True
        
        return False
    
    def set_pixels_per_metre(self, pixels_per_metre):
        """
        Set scale based on pixels per metre (backward compatibility).
        
        Args:
            pixels_per_metre: Pixels per metre value
        
        Returns:
            bool: True if scale was changed, False otherwise
        """
        # Find the closest standard scale
        closest_scale = None
        min_diff = float('inf')
        
        for scale_label, scale_value in self.STANDARD_SCALES.items():
            calculated_ppm = self._calculate_pixels_per_metre(scale_label)
            diff = abs(calculated_ppm - pixels_per_metre)
            
            if diff < min_diff:
                min_diff = diff
                closest_scale = scale_label
        
        # Only change if we found a reasonably close match
        if closest_scale and min_diff < (pixels_per_metre * 0.1):  # Within 10%
            return self.set_scale(closest_scale)
        
        # If no close match, keep current scale but update pixels_per_metre
        # (for backward compatibility with custom scaling)
        self._pixels_per_metre = pixels_per_metre
        self.scaleChanged.emit(pixels_per_metre, f"Custom ({pixels_per_metre:.1f} px/m)")
        return True
    
    def zoom_in(self):
        """Zoom in to next larger scale (more detail)."""
        scale_order = list(self.STANDARD_SCALES.keys())
        current_index = scale_order.index(self._current_scale) if self._current_scale in scale_order else 2  # Default to 1:50
        
        if current_index > 0:
            return self.set_scale(scale_order[current_index - 1])
        
        return False
    
    def zoom_out(self):
        """Zoom out to next smaller scale (less detail)."""
        scale_order = list(self.STANDARD_SCALES.keys())
        current_index = scale_order.index(self._current_scale) if self._current_scale in scale_order else 2  # Default to 1:50
        
        if current_index < len(scale_order) - 1:
            return self.set_scale(scale_order[current_index + 1])
        
        return False
    
    def adjust_scale(self, delta, ctrl_pressed=True):
        """
        Adjust scale using mouse wheel with CTRL modifier.
        
        Args:
            delta: Mouse wheel delta (positive = zoom in, negative = zoom out)
            ctrl_pressed: Whether CTRL key is pressed
        
        Returns:
            bool: True if scale was adjusted, False otherwise
        """
        if not ctrl_pressed:
            return False
        
        # Normalize delta (typically ±120 per wheel tick)
        if delta > 0:
            return self.zoom_in()
        else:
            return self.zoom_out()
    
    def get_scale_info(self):
        """Get comprehensive scale information."""
        return {
            'scale_label': self._current_scale,
            'scale_value': self.STANDARD_SCALES[self._current_scale],
            'pixels_per_metre': self._pixels_per_metre,
            'display_name': self.get_display_name(),
            'screen_dpi': self._screen_dpi,
            'compatibility_mode': self._compatibility_mode
        }
    
    def get_available_scales(self):
        """Get list of available scale labels."""
        return list(self.STANDARD_SCALES.keys())
    
    def get_scale_for_view_type(self, view_type):
        """
        Get recommended scale for different view types.
        
        Args:
            view_type: 'detailed', 'overview', or 'wide'
        
        Returns:
            str: Scale label
        """
        if view_type == 'detailed':
            return '1:50'
        elif view_type == 'overview':
            return '1:200'
        elif view_type == 'wide':
            return '1:500'
        else:
            return '1:50'  # Default
    
    def calculate_metres_per_pixel(self):
        """Calculate metres per pixel (inverse of pixels per metre)."""
        if self._pixels_per_metre > 0:
            return 1.0 / self._pixels_per_metre
        return 0.0
    
    def calculate_screen_metres(self, screen_pixels):
        """
        Calculate real-world metres represented by screen pixels.
        
        Args:
            screen_pixels: Number of screen pixels
        
        Returns:
            float: Real-world metres
        """
        return screen_pixels * self.calculate_metres_per_pixel()
    
    def calculate_screen_pixels(self, real_world_metres):
        """
        Calculate screen pixels needed to represent real-world metres.
        
        Args:
            real_world_metres: Real-world distance in metres
        
        Returns:
            float: Screen pixels
        """
        return real_world_metres * self._pixels_per_metre


# Utility functions for backward compatibility
def pixels_per_metre_to_scale(pixels_per_metre, screen_dpi=96.0):
    """
    Convert pixels per metre to closest engineering scale.
    
    Args:
        pixels_per_metre: Pixels per metre value
        screen_dpi: Screen DPI (default 96)
    
    Returns:
        tuple: (scale_label, scale_value, display_name) or None if no close match
    """
    converter = EngineeringScaleConverter()
    
    # Temporarily set screen DPI
    converter._screen_dpi = screen_dpi
    
    # Try to find matching scale
    for scale_label in converter.STANDARD_SCALES.keys():
        calculated_ppm = converter._calculate_pixels_per_metre(scale_label)
        if abs(calculated_ppm - pixels_per_metre) < (pixels_per_metre * 0.1):  # Within 10%
            return scale_label, converter.STANDARD_SCALES[scale_label], converter.SCALE_DISPLAY_NAMES[scale_label]
    
    return None


def scale_to_pixels_per_metre(scale_label, screen_dpi=96.0):
    """
    Convert engineering scale to pixels per metre.
    
    Args:
        scale_label: Engineering scale label (e.g., '1:50')
        screen_dpi: Screen DPI (default 96)
    
    Returns:
        float: Pixels per metre
    """
    converter = EngineeringScaleConverter()
    converter._screen_dpi = screen_dpi
    
    if scale_label in converter.STANDARD_SCALES:
        return converter._calculate_pixels_per_metre(scale_label)
    
    raise ValueError(f"Unknown scale: {scale_label}")