"""
CurveAlignmentEngine - Engine for aligning and scaling LAS curves.
Provides curve alignment, depth synchronization, and scaling configuration.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

class CurveAlignmentEngine(QObject):
    """Engine for aligning and scaling LAS curves with depth synchronization."""
    
    # Signals
    alignment_changed = pyqtSignal()  # Emitted when alignment settings change
    depth_scale_changed = pyqtSignal(float)  # depth_scale
    curve_scaling_changed = pyqtSignal(str, float, float)  # curve_name, min_scale, max_scale
    
    def __init__(self, curve_plotter=None):
        super().__init__()
        self.curve_plotter = curve_plotter
        
        # Alignment configuration
        self.alignment_mode = 'depth'  # 'depth', 'normalized', 'custom'
        self.depth_scale = 10.0  # Pixels per depth unit (should match stratigraphic column)
        self.reference_depth = 0.0  # Reference depth for alignment
        
        # Curve scaling configurations
        self.curve_scaling: Dict[str, Dict] = {}  # curve_name -> {min: x, max: x, auto: bool}
        
        # Depth synchronization
        self.sync_enabled = True
        self.sync_tolerance = 0.01  # Depth tolerance for synchronization
        
        # Dual-axis synchronization
        self.dual_axis_sync_enabled = True
        self.gamma_axis_range = (0, 300)  # Default gamma range (API)
        self.density_axis_range = (0, 4)   # Default density range (g/cc)
        
        # Auto-scaling configuration
        self.auto_scaling_enabled = True
        self.auto_scaling_margin = 0.1  # 10% margin for auto-scaling
        
        # Performance optimization
        self.scaling_cache = {}
        self.cache_valid = False
        
        # Setup timer for batch updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(100)  # 100ms debounce
        self.update_timer.timeout.connect(self.apply_alignment_changes)
        
        # Pending updates
        self.pending_updates = set()
    
    def register_curve(self, curve_name: str, data: np.ndarray = None, 
                      depth_data: np.ndarray = None, curve_type: str = None):
        """
        Register a curve with the alignment engine.
        
        Args:
            curve_name: Name of the curve
            data: Curve data values (optional)
            depth_data: Depth data (optional)
            curve_type: 'gamma', 'density', 'caliper', 'resistivity', 'other'
        """
        if curve_name not in self.curve_scaling:
            # Initialize with default scaling
            self.curve_scaling[curve_name] = {
                'min': 0.0,
                'max': 1.0,
                'auto': True,
                'type': curve_type,
                'data': data,
                'depth_data': depth_data
            }
            
            # Auto-detect curve type if not provided
            if curve_type is None:
                self.curve_scaling[curve_name]['type'] = self._detect_curve_type(curve_name)
            
            # Auto-scale if data is provided
            if data is not None and self.auto_scaling_enabled:
                self.auto_scale_curve(curve_name, data)
    
    def _detect_curve_type(self, curve_name: str) -> str:
        """Detect curve type based on name patterns."""
        curve_lower = curve_name.lower()
        
        if any(pattern in curve_lower for pattern in ['gamma', 'gr', 'gammaray']):
            return 'gamma'
        elif any(pattern in curve_lower for pattern in ['density', 'den', 'rhob', 'ss', 'ls']):
            return 'density'
        elif any(pattern in curve_lower for pattern in ['caliper', 'cal', 'cd', 'diameter']):
            return 'caliper'
        elif any(pattern in curve_lower for pattern in ['resistivity', 'res', 'rt', 'ild']):
            return 'resistivity'
        else:
            return 'other'
    
    def auto_scale_curve(self, curve_name: str, data: np.ndarray = None):
        """
        Automatically scale a curve based on its data.
        
        Args:
            curve_name: Name of the curve to scale
            data: Curve data (optional, uses stored data if not provided)
        """
        if curve_name not in self.curve_scaling:
            return
        
        # Get data
        if data is None:
            if 'data' in self.curve_scaling[curve_name]:
                data = self.curve_scaling[curve_name]['data']
            else:
                return
        
        # Filter out NaN values
        valid_data = data[~np.isnan(data)]
        if len(valid_data) == 0:
            return
        
        # Calculate min and max with margin
        data_min = np.min(valid_data)
        data_max = np.max(valid_data)
        data_range = data_max - data_min
        
        # Apply margin
        margin = data_range * self.auto_scaling_margin
        scaled_min = data_min - margin
        scaled_max = data_max + margin
        
        # Ensure valid range
        if scaled_min >= scaled_max:
            scaled_min = data_min - 0.1 * abs(data_min) if data_min != 0 else -0.1
            scaled_max = data_max + 0.1 * abs(data_max) if data_max != 0 else 0.1
        
        # Update scaling
        self.curve_scaling[curve_name]['min'] = float(scaled_min)
        self.curve_scaling[curve_name]['max'] = float(scaled_max)
        self.curve_scaling[curve_name]['auto'] = True
        
        # Emit signal
        self.curve_scaling_changed.emit(curve_name, scaled_min, scaled_max)
        
        # Invalidate cache
        self.cache_valid = False
    
    def set_curve_scaling(self, curve_name: str, min_value: float, max_value: float, 
                         auto: bool = False):
        """
        Manually set scaling for a curve.
        
        Args:
            curve_name: Name of the curve
            min_value: Minimum value for scaling
            max_value: Maximum value for scaling
            auto: Whether to revert to auto-scaling
        """
        if curve_name not in self.curve_scaling:
            return
        
        # Validate range
        if min_value >= max_value:
            return
        
        # Update scaling
        self.curve_scaling[curve_name]['min'] = min_value
        self.curve_scaling[curve_name]['max'] = max_value
        self.curve_scaling[curve_name]['auto'] = auto
        
        # Emit signal
        self.curve_scaling_changed.emit(curve_name, min_value, max_value)
        
        # Invalidate cache
        self.cache_valid = False
    
    def set_alignment_mode(self, mode: str):
        """
        Set alignment mode.
        
        Args:
            mode: 'depth' (align by depth), 'normalized' (normalize all curves),
                  'custom' (custom alignment)
        """
        if mode not in ['depth', 'normalized', 'custom']:
            return
        
        if self.alignment_mode != mode:
            self.alignment_mode = mode
            self.alignment_changed.emit()
            self.cache_valid = False
    
    def set_depth_scale(self, scale: float):
        """
        Set depth scale (pixels per depth unit).
        
        Args:
            scale: Depth scale value
        """
        if scale <= 0:
            return
        
        if abs(self.depth_scale - scale) > 0.001:
            self.depth_scale = scale
            self.depth_scale_changed.emit(scale)
            self.cache_valid = False
    
    def set_reference_depth(self, depth: float):
        """
        Set reference depth for alignment.
        
        Args:
            depth: Reference depth value
        """
        if abs(self.reference_depth - depth) > self.sync_tolerance:
            self.reference_depth = depth
            self.cache_valid = False
    
    def align_curves(self, curve_names: List[str] = None) -> Dict[str, Tuple[float, float]]:
        """
        Align curves based on current alignment mode.
        
        Args:
            curve_names: List of curve names to align (None for all)
            
        Returns:
            Dictionary mapping curve_name -> (min_value, max_value) for display
        """
        if curve_names is None:
            curve_names = list(self.curve_scaling.keys())
        
        result = {}
        
        if self.alignment_mode == 'depth':
            # Depth alignment: use original scaling
            for curve_name in curve_names:
                if curve_name in self.curve_scaling:
                    scaling = self.curve_scaling[curve_name]
                    result[curve_name] = (scaling['min'], scaling['max'])
        
        elif self.alignment_mode == 'normalized':
            # Normalized alignment: scale all curves to [0, 1] range
            for curve_name in curve_names:
                if curve_name in self.curve_scaling:
                    scaling = self.curve_scaling[curve_name]
                    min_val = scaling['min']
                    max_val = scaling['max']
                    
                    # Normalize to [0, 1]
                    if max_val > min_val:
                        # Already have min/max, normalization happens at display time
                        result[curve_name] = (0.0, 1.0)
                    else:
                        result[curve_name] = (min_val, max_val)
        
        elif self.alignment_mode == 'custom':
            # Custom alignment: use reference depth as alignment point
            for curve_name in curve_names:
                if curve_name in self.curve_scaling:
                    scaling = self.curve_scaling[curve_name]
                    result[curve_name] = (scaling['min'], scaling['max'])
        
        # Cache result
        self.scaling_cache = result.copy()
        self.cache_valid = True
        
        return result
    
    def get_aligned_scaling(self, curve_name: str) -> Optional[Tuple[float, float]]:
        """
        Get aligned scaling for a specific curve.
        
        Args:
            curve_name: Name of the curve
            
        Returns:
            Tuple of (min_value, max_value) or None if not found
        """
        if self.cache_valid and curve_name in self.scaling_cache:
            return self.scaling_cache[curve_name]
        
        # Recalculate if cache is invalid
        self.align_curves([curve_name])
        return self.scaling_cache.get(curve_name)
    
    def synchronize_depth(self, depth: float, curve_plotter=None):
        """
        Synchronize depth across all curves.
        
        Args:
            depth: Target depth for synchronization
            curve_plotter: Curve plotter to update (uses registered plotter if None)
        """
        if not self.sync_enabled:
            return
        
        # Update reference depth
        self.set_reference_depth(depth)
        
        # Apply to curve plotter
        plotter = curve_plotter or self.curve_plotter
        if plotter:
            # Queue update
            self.pending_updates.add('depth_sync')
            self.update_timer.start()
    
    def apply_alignment_changes(self):
        """Apply pending alignment changes to the curve plotter."""
        if not self.curve_plotter:
            return
        
        # Apply depth synchronization
        if 'depth_sync' in self.pending_updates:
            if hasattr(self.curve_plotter, 'scroll_to_depth'):
                self.curve_plotter.scroll_to_depth(self.reference_depth)
        
        # Apply scaling changes
        if 'scaling' in self.pending_updates:
            # Update curve plotter scaling
            if hasattr(self.curve_plotter, 'set_curve_configs'):
                # Get current curve configs
                if hasattr(self.curve_plotter, 'curve_configs'):
                    configs = self.curve_plotter.curve_configs.copy()
                    
                    # Update scaling in configs
                    for config in configs:
                        curve_name = config['name']
                        if curve_name in self.curve_scaling:
                            scaling = self.curve_scaling[curve_name]
                            config['min'] = scaling['min']
                            config['max'] = scaling['max']
                    
                    # Apply updated configs
                    self.curve_plotter.set_curve_configs(configs)
        
        # Clear pending updates
        self.pending_updates.clear()
    
    def enable_auto_scaling(self, enabled: bool):
        """Enable or disable auto-scaling."""
        if self.auto_scaling_enabled != enabled:
            self.auto_scaling_enabled = enabled
            
            # Re-auto-scale all curves if enabled
            if enabled:
                for curve_name in self.curve_scaling:
                    if self.curve_scaling[curve_name]['auto']:
                        self.auto_scale_curve(curve_name)
            
            self.cache_valid = False
    
    def set_dual_axis_ranges(self, gamma_range: Tuple[float, float], 
                           density_range: Tuple[float, float]):
        """
        Set dual-axis ranges for gamma and density curves.
        
        Args:
            gamma_range: (min, max) for gamma axis
            density_range: (min, max) for density axis
        """
        self.gamma_axis_range = gamma_range
        self.density_axis_range = density_range
        
        # Update gamma curve scaling
        for curve_name, scaling in self.curve_scaling.items():
            if scaling.get('type') == 'gamma':
                scaling['min'] = gamma_range[0]
                scaling['max'] = gamma_range[1]
                scaling['auto'] = False
        
        # Update density curve scaling
        for curve_name, scaling in self.curve_scaling.items():
            if scaling.get('type') == 'density':
                scaling['min'] = density_range[0]
                scaling['max'] = density_range[1]
                scaling['auto'] = False
        
        self.cache_valid = False
        self.alignment_changed.emit()
    
    def get_curve_info(self, curve_name: str) -> Optional[Dict]:
        """Get information about a curve."""
        return self.curve_scaling.get(curve_name)
    
    def get_all_curve_info(self) -> Dict[str, Dict]:
        """Get information about all curves."""
        return self.curve_scaling.copy()
    
    def reset_to_defaults(self):
        """Reset all alignment settings to defaults."""
        self.alignment_mode = 'depth'
        self.depth_scale = 10.0
        self.reference_depth = 0.0
        
        # Reset curve scaling to auto
        for curve_name in self.curve_scaling:
            self.curve_scaling[curve_name]['auto'] = True
            if 'data' in self.curve_scaling[curve_name]:
                self.auto_scale_curve(curve_name, self.curve_scaling[curve_name]['data'])
        
        self.cache_valid = False
        self.alignment_changed.emit()
    
    def update_curve_data(self, curve_name: str, data: np.ndarray, 
                         depth_data: np.ndarray = None):
        """
        Update curve data and re-auto-scale if needed.
        
        Args:
            curve_name: Name of the curve
            data: New curve data
            depth_data: New depth data (optional)
        """
        if curve_name not in self.curve_scaling:
            return
        
        # Update data
        self.curve_scaling[curve_name]['data'] = data
        if depth_data is not None:
            self.curve_scaling[curve_name]['depth_data'] = depth_data
        
        # Re-auto-scale if auto-scaling is enabled
        if self.curve_scaling[curve_name]['auto'] and self.auto_scaling_enabled:
            self.auto_scale_curve(curve_name, data)
        
        self.cache_valid = False