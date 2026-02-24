"""
Depth module - core classes for depth state management and coordinate transformation.
Re-exports from graphic window state for backward compatibility.
"""

from src.ui.graphic_window.state.depth_state_manager import DepthStateManager, DepthRange
from src.ui.graphic_window.state.depth_coordinate_system import DepthCoordinateSystem
from .data_structures import LithologyInterval, LASPoint

__all__ = [
    'DepthStateManager', 
    'DepthRange', 
    'DepthCoordinateSystem',
    'LithologyInterval',
    'LASPoint'
]