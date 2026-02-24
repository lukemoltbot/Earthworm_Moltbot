"""
Abstract interface for accessing hole data.
Allows different data sources without coupling UI to specific data store.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .lithology_interval import LithologyInterval
from .las_point import LASPoint


class HoleDataProvider(ABC):
    """
    Abstract interface for accessing hole data.
    Allows different data sources (database, file, memory) without
    coupling the UI to any specific data store.
    """
    
    @abstractmethod
    def get_lithology_intervals(self) -> List[LithologyInterval]:
        """Get all lithology intervals for this hole."""
        pass
    
    @abstractmethod
    def get_lithology_for_depth(self, depth: float) -> Optional[LithologyInterval]:
        """Get lithology interval containing this depth."""
        pass
    
    @abstractmethod
    def get_las_points(self, curve_names: List[str] = None) -> List[LASPoint]:
        """Get LAS curve data points."""
        pass
    
    @abstractmethod
    def get_depth_range(self) -> tuple:
        """Get (min_depth, max_depth) for the hole."""
        pass
    
    @abstractmethod
    def get_available_curves(self) -> List[str]:
        """Get list of available curve names."""
        pass
    
    def get_depth_bounds(self) -> dict:
        """Get depth information dict."""
        min_depth, max_depth = self.get_depth_range()
        return {
            'min': min_depth,
            'max': max_depth,
            'range': max_depth - min_depth
        }