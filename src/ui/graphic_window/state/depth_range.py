"""
DepthRange data structure for depth intervals.
"""

from dataclasses import dataclass


@dataclass
class DepthRange:
    """Immutable depth range."""
    from_depth: float
    to_depth: float
    
    @property
    def range_size(self) -> float:
        return self.to_depth - self.from_depth
    
    def contains(self, depth: float) -> bool:
        return self.from_depth <= depth <= self.to_depth