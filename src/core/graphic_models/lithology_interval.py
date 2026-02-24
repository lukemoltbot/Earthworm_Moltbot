"""
Lithology interval data model.
Represents a single lithology interval in a borehole.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class LithologyCode(Enum):
    """Lithology classification codes."""
    SAND = "SAND"
    SILT = "SILT"
    COAL = "COAL"
    SHALE = "SHALE"
    MUDSTONE = "MUDSTONE"
    # ... add all codes from CoalLog dictionary


@dataclass
class LithologyInterval:
    """
    Represents a single lithology interval in a borehole.
    This is the fundamental unit of data visualization.
    """
    from_depth: float              # Depth at top of interval (meters)
    to_depth: float                # Depth at bottom of interval (meters)
    code: str                       # Lithology code (e.g., "COAL", "SAND")
    description: str               # Human-readable description
    color: tuple = (128, 128, 128) # RGB color tuple
    pattern: Optional[str] = None  # Pattern name if applicable
    thickness: float = None        # Calculated: to_depth - from_depth
    
    # Metadata
    sample_number: Optional[str] = None
    comment: str = ""
    
    # Validation
    is_valid: bool = True
    validation_messages: list = None
    
    def __post_init__(self):
        """Calculate derived fields."""
        self.thickness = self.to_depth - self.from_depth
        if self.validation_messages is None:
            self.validation_messages = []
    
    def contains_depth(self, depth: float) -> bool:
        """Check if interval contains a depth."""
        return self.from_depth <= depth <= self.to_depth
    
    def get_depth_ratio(self, depth: float) -> float:
        """Get ratio of depth within interval (0.0 to 1.0)."""
        if self.thickness == 0:
            return 0.0
        return (depth - self.from_depth) / self.thickness