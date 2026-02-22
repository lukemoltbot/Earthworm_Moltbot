"""
Unified Viewport Package
=======================

Provides unified display of LAS curves and stratigraphic column
with pixel-perfect synchronization.

Components:
- GeologicalAnalysisViewport: Main container widget
- UnifiedDepthScaleManager: Synchronization engine
- PixelDepthMapper: Pixel-accurate depth mapping
- Component adapters for existing widgets
"""

from .geological_analysis_viewport import GeologicalAnalysisViewport
from .pixel_depth_mapper import PixelDepthMapper
from .unified_depth_scale_manager import UnifiedDepthScaleManager, DepthScaleConfig, DepthScaleMode

__all__ = [
    'GeologicalAnalysisViewport',
    'UnifiedDepthScaleManager',
    'DepthScaleConfig',
    'DepthScaleMode',
    'PixelDepthMapper',
]

__version__ = '1.0.0-alpha'