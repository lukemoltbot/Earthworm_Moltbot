"""
Excel-based hole data provider.
Provides hole data from Earthworm Excel format (.xlsx).
"""

import pandas as pd
from typing import List, Optional
from .hole_data_provider import HoleDataProvider
from .lithology_interval import LithologyInterval
from .las_point import LASPoint


class ExcelHoleDataProvider(HoleDataProvider):
    """
    Provides hole data from Earthworm Excel format (.xlsx).
    Reads lithology from one sheet, LAS from another.
    """
    
    def __init__(self, lithology_df: pd.DataFrame, las_df: pd.DataFrame):
        """
        Args:
            lithology_df: DataFrame with columns [from_depth, to_depth, code, description, ...]
            las_df: DataFrame with columns [depth, gamma, density, ...]
        """
        self.lithology_df = lithology_df.sort_values('from_depth')
        self.las_df = las_df.sort_values('depth')
        self._lithology_cache = None
        self._las_cache = None
    
    def get_lithology_intervals(self) -> List[LithologyInterval]:
        """Load and cache lithology intervals."""
        if self._lithology_cache is not None:
            return self._lithology_cache
        
        intervals = []
        for _, row in self.lithology_df.iterrows():
            interval = LithologyInterval(
                from_depth=row['from_depth'],
                to_depth=row['to_depth'],
                code=row.get('code', 'UNKNOWN'),
                description=row.get('description', ''),
                color=self._get_color_for_code(row.get('code')),
                sample_number=row.get('sample_number'),
                comment=row.get('comment', '')
            )
            intervals.append(interval)
        
        self._lithology_cache = intervals
        return intervals
    
    def get_lithology_for_depth(self, depth: float) -> Optional[LithologyInterval]:
        """Get lithology containing specific depth."""
        for interval in self.get_lithology_intervals():
            if interval.contains_depth(depth):
                return interval
        return None
    
    def get_las_points(self, curve_names: List[str] = None) -> List[LASPoint]:
        """Get LAS points for specified curves."""
        if self._las_cache is not None and curve_names is None:
            return self._las_cache
        
        if curve_names is None:
            curve_names = self.get_available_curves()
        
        points = []
        for _, row in self.las_df.iterrows():
            point = LASPoint(
                depth=row['depth'],
                curves={name: row.get(name, None) for name in curve_names}
            )
            points.append(point)
        
        if curve_names is None:
            self._las_cache = points
        
        return points
    
    def get_depth_range(self) -> tuple:
        """Get min/max depths from lithology."""
        lith = self.get_lithology_intervals()
        if not lith:
            return (0, 100)
        return (lith[0].from_depth, lith[-1].to_depth)
    
    def get_available_curves(self) -> List[str]:
        """Get all curve names from LAS data."""
        # Exclude 'depth' column
        return [col for col in self.las_df.columns if col != 'depth']
    
    def _get_color_for_code(self, code: str) -> tuple:
        """Get RGB color for lithology code."""
        color_map = {
            'SAND': (255, 215, 0),
            'COAL': (0, 0, 0),
            'SHALE': (169, 169, 169),
            'SILT': (210, 180, 140),
            'MUDSTONE': (128, 128, 128),
        }
        return color_map.get(code, (128, 128, 128))