"""
LAS point data model.
Represents a single depth sample of LAS curve data.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class LASPoint:
    """
    Represents a single depth sample of LAS curve data.
    
    LAS (Log ASCII Standard) files contain geophysical measurements
    at various depths. Each point has multiple curve values.
    """
    depth: float                    # Depth in meters
    curves: Dict[str, float]        # {curve_name: value}
    # Common curves:
    # - gamma: Gamma Ray API units
    # - density: Bulk Density g/cm³
    # - resistivity: Resistivity ohm-m
    # - caliper: Caliper mm
    # - porosity: Porosity %
    
    def get_curve_value(self, curve_name: str, default: float = None) -> float:
        """Get value for specific curve, return default if missing."""
        return self.curves.get(curve_name, default)
    
    def has_curve(self, curve_name: str) -> bool:
        """Check if curve exists."""
        return curve_name in self.curves