"""
DepthSynchronizer - Handles cursor depth synchronization across components.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, List, Tuple
from src.core.graphic_models import HoleDataProvider, LithologyInterval, LASPoint


class DepthSynchronizer(QObject):
    """
    Handles cursor depth synchronization across all graphic window components.
    
    Responsibilities:
    1. Snap cursor to nearest data point
    2. Maintain cursor visibility within viewport
    3. Handle depth markers and annotations
    4. Coordinate depth display across components
    """
    
    # Signals
    cursorDepthChanged = pyqtSignal(float)
    cursorSnapped = pyqtSignal(float, str)  # (snapped_depth, snap_type)
    depthMarkerAdded = pyqtSignal(float, str)  # (depth, label)
    
    def __init__(self, data_provider: HoleDataProvider):
        super().__init__()
        
        self.data_provider = data_provider
        self.current_depth: Optional[float] = None
        
        # Snap settings
        self.snap_enabled = True
        self.snap_tolerance = 0.1  # Meters
        self.snap_to_lithology = True
        self.snap_to_las = True
        
        # Depth markers
        self.depth_markers: List[Tuple[float, str]] = []  # (depth, label)
        
        # Cursor visibility
        self.keep_cursor_visible = True
    
    def set_cursor_depth(self, depth: float, snap: bool = True):
        """
        Set cursor depth.
        
        Args:
            depth: Target depth
            snap: Whether to snap to nearest data point
        """
        original_depth = depth
        
        # Snap if enabled
        if snap and self.snap_enabled:
            depth = self.snap_to_nearest(depth)
        
        # Validate depth is within hole range
        min_depth, max_depth = self.data_provider.get_depth_range()
        depth = max(min_depth, min(depth, max_depth))
        
        self.current_depth = depth
        self.cursorDepthChanged.emit(depth)
        
        # Emit snap signal if depth changed
        if abs(depth - original_depth) > 0.001:
            snap_type = self._get_snap_type(depth, original_depth)
            self.cursorSnapped.emit(depth, snap_type)
        
        # Ensure cursor stays visible if enabled
        if self.keep_cursor_visible:
            self.ensure_cursor_visible()
    
    def snap_to_nearest(self, depth: float) -> float:
        """
        Snap depth to nearest data point.
        
        Args:
            depth: Input depth
            
        Returns:
            Snapped depth
        """
        candidates = []
        
        # Snap to lithology interval boundaries
        if self.snap_to_lithology:
            intervals = self.data_provider.get_lithology_intervals()
            for interval in intervals:
                candidates.append(float(interval.from_depth))
                candidates.append(float(interval.to_depth))
        
        # Snap to LAS data points
        if self.snap_to_las:
            las_points = self.data_provider.get_las_points()
            for point in las_points:
                candidates.append(float(point.depth))
        
        # Add depth markers
        for marker_depth, _ in self.depth_markers:
            candidates.append(float(marker_depth))
        
        if not candidates:
            return depth
        
        # Find closest candidate within tolerance
        closest = None
        min_distance = float('inf')
        
        for candidate in candidates:
            distance = abs(candidate - depth)
            if distance < min_distance and distance <= self.snap_tolerance:
                min_distance = distance
                closest = candidate
        
        return closest if closest is not None else depth
    
    def _get_snap_type(self, snapped_depth: float, original_depth: float) -> str:
        """Determine what type of snap occurred."""
        # Check lithology intervals
        intervals = self.data_provider.get_lithology_intervals()
        for interval in intervals:
            if abs(interval.from_depth - snapped_depth) < 0.001:
                return f"lithology_top:{interval.code}"
            if abs(interval.to_depth - snapped_depth) < 0.001:
                return f"lithology_bottom:{interval.code}"
        
        # Check LAS points
        las_points = self.data_provider.get_las_points()
        for point in las_points:
            if abs(point.depth - snapped_depth) < 0.001:
                return "las_point"
        
        # Check depth markers
        for marker_depth, label in self.depth_markers:
            if abs(marker_depth - snapped_depth) < 0.001:
                return f"marker:{label}"
        
        return "unknown"
    
    def ensure_cursor_visible(self):
        """Ensure cursor is within current viewport (to be called by viewport)."""
        # This method should be called by the viewport component
        # when the viewport changes. It would check if cursor is
        # visible and adjust viewport if needed.
        # Implementation depends on viewport integration.
        pass
    
    def add_depth_marker(self, depth: float, label: str = ""):
        """
        Add a depth marker.
        
        Args:
            depth: Marker depth
            label: Optional label
        """
        self.depth_markers.append((depth, label))
        self.depthMarkerAdded.emit(depth, label)
    
    def remove_depth_marker(self, depth: float):
        """
        Remove depth marker at specified depth.
        
        Args:
            depth: Marker depth to remove
        """
        self.depth_markers = [(d, l) for d, l in self.depth_markers if abs(d - depth) > 0.001]
    
    def clear_depth_markers(self):
        """Clear all depth markers."""
        self.depth_markers.clear()
    
    def get_depth_markers(self) -> List[Tuple[float, str]]:
        """Get all depth markers."""
        return self.depth_markers.copy()
    
    def get_data_at_depth(self, depth: float) -> dict:
        """
        Get all data at a specific depth.
        
        Args:
            depth: Target depth
            
        Returns:
            Dictionary with lithology, LAS values, etc.
        """
        result = {
            'depth': depth,
            'lithology': None,
            'las_values': {},
            'markers': []
        }
        
        # Find lithology interval
        intervals = self.data_provider.get_lithology_intervals()
        for interval in intervals:
            if interval.contains_depth(depth):
                result['lithology'] = {
                    'code': interval.code,
                    'description': interval.description,
                    'from_depth': interval.from_depth,
                    'to_depth': interval.to_depth,
                    'thickness': interval.thickness,
                    'sample_number': interval.sample_number,
                    'comment': interval.comment
                }
                break
        
        # Get LAS values
        las_points = self.data_provider.get_las_points()
        for point in las_points:
            if abs(point.depth - depth) < 0.001:
                result['las_values'] = point.curves.copy()
                break
        
        # Get markers at this depth
        for marker_depth, label in self.depth_markers:
            if abs(marker_depth - depth) < 0.001:
                result['markers'].append(label)
        
        return result
    
    def find_next_data_point(self, depth: float, direction: str = "down") -> Optional[float]:
        """
        Find next data point in specified direction.
        
        Args:
            depth: Starting depth
            direction: "up" (shallower) or "down" (deeper)
            
        Returns:
            Depth of next data point, or None
        """
        all_points = []
        
        # Collect all data points
        intervals = self.data_provider.get_lithology_intervals()
        for interval in intervals:
            all_points.append(interval.from_depth)
            all_points.append(interval.to_depth)
        
        las_points = self.data_provider.get_las_points()
        for point in las_points:
            all_points.append(point.depth)
        
        for marker_depth, _ in self.depth_markers:
            all_points.append(marker_depth)
        
        # Remove duplicates and sort
        all_points = sorted(set(all_points))
        
        if direction == "down":
            # Find next deeper point
            for point in all_points:
                if point > depth + 0.001:  # Small epsilon
                    return point
        else:  # "up"
            # Find next shallower point
            for point in reversed(all_points):
                if point < depth - 0.001:  # Small epsilon
                    return point
        
        return None
    
    def toggle_snap(self):
        """Toggle snap on/off."""
        self.snap_enabled = not self.snap_enabled
    
    def set_snap_settings(self, snap_to_lithology: bool, snap_to_las: bool, tolerance: float):
        """
        Configure snap settings.
        
        Args:
            snap_to_lithology: Snap to lithology boundaries
            snap_to_las: Snap to LAS data points
            tolerance: Snap tolerance in meters
        """
        self.snap_to_lithology = snap_to_lithology
        self.snap_to_las = snap_to_las
        self.snap_tolerance = max(0.001, tolerance)