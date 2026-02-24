"""
Core data structures for geological data.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class LithologyInterval:
    """Single lithology layer."""
    from_depth: float
    to_depth: float
    code: str
    description: str
    color: Tuple[int, int, int] = (128, 128, 128)
    thickness: float = None
    
    def __post_init__(self):
        self.thickness = self.to_depth - self.from_depth
    
    def contains_depth(self, depth: float) -> bool:
        return self.from_depth <= depth <= self.to_depth


@dataclass
class LASPoint:
    """Single geophysical curve data point."""
    depth: float
    curves: Dict[str, float]  # {curve_name: value}
    
    def get_curve_value(self, curve_name: str, default: float = None) -> float:
        return self.curves.get(curve_name, default)
    
    def has_curve(self, curve_name: str) -> bool:
        return curve_name in self.curves