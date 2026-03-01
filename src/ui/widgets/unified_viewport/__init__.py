"""
DEPRECATED: System B viewport components.

⚠️ WARNING: This package is deprecated.

Use src/ui/graphic_window/ instead for System A architecture.
See DEPRECATION_NOTICE.md in this directory for migration guide.
"""

import warnings

warnings.warn(
    "src.ui.widgets.unified_viewport is deprecated. "
    "Use src.ui.graphic_window instead.",
    DeprecationWarning,
    stacklevel=2
)

# Keep imports for backward compatibility, but they will trigger deprecation warnings
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