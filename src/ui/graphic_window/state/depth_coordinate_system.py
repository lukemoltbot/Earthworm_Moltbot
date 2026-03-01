"""
DepthCoordinateSystem - Shared coordinate system for depth-to-pixel transformations.

CRITICAL: This MUST be the ONLY coordinate system used.
All components share the same instance.
All coordinate transformations use these identical functions.
This is what ensures perfect alignment!
"""

from typing import Tuple


class DepthCoordinateSystem:
    """
    Transforms between model depth (meters) and screen coordinates (pixels).
    
    CRITICAL: This MUST be the ONLY coordinate system used.
    All components share the same instance.
    All coordinate transformations use these identical functions.
    This is what ensures perfect alignment!
    """
    
    def __init__(self, canvas_height: float, canvas_width: float,
                 padding_top: float = 20, padding_bottom: float = 20,
                 padding_left: float = 50, padding_right: float = 50):
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom
        self.padding_left = padding_left
        self.padding_right = padding_right
        
        # Current depth range
        self.min_depth = 0.0
        self.max_depth = 100.0
        self.zoom_level = 1.0
    
    def set_depth_range(self, min_depth: float, max_depth: float):
        """Set the depth range being displayed."""
        self.min_depth = min_depth
        self.max_depth = max_depth
    
    # ===== THE MOST IMPORTANT FUNCTIONS =====
    # These MUST be used by ALL components for vertical positioning
    
    def depth_to_screen_y(self, depth: float) -> float:
        """
        Convert depth (meters) to screen Y coordinate (pixels).
        
        This is THE CRITICAL FUNCTION.
        Every component must use this for vertical positioning.
        """
        total_depth = self.max_depth - self.min_depth
        
        if total_depth <= 0:
            return self.padding_top
        
        # Calculate depth ratio
        depth_ratio = (depth - self.min_depth) / total_depth
        
        # Map to screen
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        screen_y = self.padding_top + (depth_ratio * usable_height)
        
        return screen_y
    
    def screen_y_to_depth(self, screen_y: float) -> float:
        """
        Inverse: Convert screen Y back to depth.
        Used when processing clicks.
        """
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        
        if usable_height <= 0:
            return self.min_depth
        
        # Calculate screen ratio
        screen_ratio = (screen_y - self.padding_top) / usable_height
        
        # Map back to depth
        total_depth = self.max_depth - self.min_depth
        depth = self.min_depth + (screen_ratio * total_depth)
        
        return depth
    
    def depth_thickness_to_pixel_height(self, thickness: float) -> float:
        """Convert depth thickness to pixel height."""
        total_depth = self.max_depth - self.min_depth
        
        if total_depth <= 0:
            return 0
        
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        pixel_height = (thickness / total_depth) * usable_height
        
        return pixel_height
    
    def get_pixels_per_meter(self) -> float:
        """Get scale: pixels per meter."""
        total_depth = self.max_depth - self.min_depth
        if total_depth <= 0:
            return 0
        
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        return usable_height / total_depth
    
    def get_usable_canvas_area(self) -> Tuple[float, float, float, float]:
        """Get (left, top, right, bottom) of usable drawing area."""
        left = self.padding_left
        top = self.padding_top
        right = self.canvas_width - self.padding_right
        bottom = self.canvas_height - self.padding_bottom
        return (left, top, right, bottom)
    
    # ===== BACKWARD COMPATIBILITY =====
    # These aliases exist for backward compatibility with System B
    # Prefer depth_to_screen_y and screen_y_to_depth for new code
    
    def depth_to_pixel(self, depth: float) -> int:
        """
        DEPRECATED ALIAS: Use depth_to_screen_y() instead.
        
        Convert depth value to pixel position.
        
        Args:
            depth: Depth value in meters
            
        Returns:
            Pixel position on screen (0 = top)
        """
        return int(self.depth_to_screen_y(depth))
    
    def pixel_to_depth(self, pixel: float) -> float:
        """
        DEPRECATED ALIAS: Use screen_y_to_depth() instead.
        
        Convert pixel position back to depth value.
        
        Args:
            pixel: Pixel position on screen
            
        Returns:
            Depth value in meters
        """
        return self.screen_y_to_depth(pixel)
    
    def depth_to_screen_y_int(self, depth: float) -> int:
        """
        Convert depth to screen Y coordinate as integer pixels.
        Alias for depth_to_pixel for code clarity.
        """
        return int(self.depth_to_screen_y(depth))