"""
Curve Display Modes for Earthworm - 1Point-style curve display options.

This module provides multiple curve display modes matching 1Point functionality:
1. Overlaid Curves: Curves plotted on top of each other (1Point default)
2. Stacked Curves: Curves plotted side-by-side (1Point Stacked Layout)
3. Side-by-Side: Each curve in separate track
4. Histogram Mode: Histogram display for selected curves

Each mode provides different visualization strategies for geological analysis.
"""

from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QPen
import numpy as np
import pyqtgraph as pg
from typing import Dict, List, Any, Optional, Tuple


class CurveDisplayMode:
    """Base class for curve display modes."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.supported_features = []
        
    def configure_plot(self, plot_widget, curve_configs: List[Dict]) -> None:
        """Configure the plot widget for this display mode."""
        raise NotImplementedError("Subclasses must implement configure_plot")
    
    def draw_curves(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Draw curves according to this display mode."""
        raise NotImplementedError("Subclasses must implement draw_curves")
    
    def get_mode_info(self) -> Dict[str, Any]:
        """Get information about this display mode."""
        return {
            'name': self.name,
            'description': self.description,
            'supported_features': self.supported_features
        }


class OverlaidCurveMode(CurveDisplayMode):
    """Overlaid curves mode - curves plotted on top of each other (1Point default)."""
    
    def __init__(self):
        super().__init__(
            name="overlaid",
            description="Curves plotted on top of each other (1Point default)"
        )
        self.supported_features = ['dual_axis', 'curve_colors', 'line_styles', 'transparency']
        
    def configure_plot(self, plot_widget, curve_configs: List[Dict]) -> None:
        """Configure plot for overlaid curves."""
        # Clear existing plots
        plot_widget.clear()
        
        # Set up dual Y-axes if needed
        has_left_axis = any(cfg.get('y_axis', 'left') == 'left' for cfg in curve_configs)
        has_right_axis = any(cfg.get('y_axis', 'left') == 'right' for cfg in curve_configs)
        
        if has_left_axis and has_right_axis:
            # Create dual Y-axes
            plot_widget.setLabel('left', 'Left Axis')
            plot_widget.setLabel('right', 'Right Axis')
            plot_widget.showAxis('right')
        elif has_left_axis:
            plot_widget.setLabel('left', 'Value')
            plot_widget.hideAxis('right')
        elif has_right_axis:
            plot_widget.setLabel('right', 'Value')
            plot_widget.hideAxis('left')
            
        # Set X-axis label
        plot_widget.setLabel('bottom', 'Depth')
        
        # Enable auto-range
        plot_widget.enableAutoRange(axis='x')
        plot_widget.enableAutoRange(axis='y')
        
    def draw_curves(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Draw overlaid curves."""
        if data is None or depth_column not in data.columns:
            return
            
        depth_data = data[depth_column].values
        
        for cfg in curve_configs:
            curve_name = cfg.get('name', '')
            column_name = cfg.get('column', '')
            color = cfg.get('color', QColor(0, 0, 255))
            y_axis = cfg.get('y_axis', 'left')
            line_style = cfg.get('line_style', 'solid')
            line_width = cfg.get('line_width', 1.0)
            visible = cfg.get('visible', True)
            
            if not visible or column_name not in data.columns:
                continue
                
            curve_data = data[column_name].values
            
            # Create pen based on style
            pen = self._create_pen(color, line_style, line_width)
            
            # Plot curve
            if y_axis == 'right':
                # Plot on right axis
                plot_item = plot_widget.plot(depth_data, curve_data, pen=pen, name=curve_name)
                # Note: PyQtGraph doesn't natively support dual Y-axes on same plot item
                # This would need additional configuration
            else:
                # Plot on left axis (default)
                plot_item = plot_widget.plot(depth_data, curve_data, pen=pen, name=curve_name)
    
    def _create_pen(self, color: QColor, style: str, width: float) -> pg.mkPen:
        """Create pen based on style specification."""
        if style == 'dotted':
            return pg.mkPen(color, width=width, style=Qt.PenStyle.DotLine)
        elif style == 'dashed':
            return pg.mkPen(color, width=width, style=Qt.PenStyle.DashLine)
        elif style == 'dash_dot':
            return pg.mkPen(color, width=width, style=Qt.PenStyle.DashDotLine)
        else:  # solid
            return pg.mkPen(color, width=width)


class StackedCurveMode(CurveDisplayMode):
    """Stacked curves mode - curves plotted side-by-side (1Point Stacked Layout)."""
    
    def __init__(self):
        super().__init__(
            name="stacked",
            description="Curves plotted side-by-side (1Point Stacked Layout)"
        )
        self.supported_features = ['separate_tracks', 'independent_scaling', 'track_labels']
        
    def configure_plot(self, plot_widget, curve_configs: List[Dict]) -> None:
        """Configure plot for stacked curves."""
        # Clear existing plots
        plot_widget.clear()
        
        # Stacked mode requires GraphicsLayout
        # We'll create a new GraphicsLayout widget
        from pyqtgraph import GraphicsLayout
        
        # Check if we need to replace the widget
        if not isinstance(plot_widget, GraphicsLayout):
            # We need to replace the widget with GraphicsLayout
            # This would be handled by the parent widget
            pass
        
        # For now, configure as regular plot but mark for stacked layout
        plot_widget.hideAxis('left')
        plot_widget.hideAxis('right')
        plot_widget.setLabel('bottom', 'Depth')
        
    def draw_curves(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Draw stacked curves using GraphicsLayout."""
        if data is None or depth_column not in data.columns:
            return
            
        depth_data = data[depth_column].values
        
        # Create GraphicsLayout for stacked plots
        try:
            from pyqtgraph import GraphicsLayout
            
            # Clear existing content
            plot_widget.clear()
            
            # Create GraphicsLayout if not already
            if not isinstance(plot_widget, GraphicsLayout):
                # We'll create subplots within the existing widget
                # This is a simplified implementation
                self._draw_stacked_simple(plot_widget, data, depth_column, curve_configs)
                return
            
            # Get visible curves
            visible_configs = [cfg for cfg in curve_configs if cfg.get('visible', True)]
            
            if not visible_configs:
                return
                
            # Create stacked layout - one plot per curve
            for i, cfg in enumerate(visible_configs):
                curve_name = cfg.get('name', '')
                column_name = cfg.get('column', '')
                color = cfg.get('color', QColor(0, 0, 255))
                line_style = cfg.get('line_style', 'solid')
                line_width = cfg.get('line_width', 1.0)
                
                if column_name not in data.columns:
                    continue
                    
                curve_data = data[column_name].values
                
                # Create pen
                pen = self._create_pen(color, line_style, line_width)
                
                # Add plot to layout
                plot_item = plot_widget.addPlot(row=i, col=0)
                plot_item.plot(depth_data, curve_data, pen=pen, name=curve_name)
                
                # Configure axes
                plot_item.setLabel('left', curve_name)
                if i == len(visible_configs) - 1:  # Last plot shows X-axis
                    plot_item.setLabel('bottom', 'Depth')
                else:
                    plot_item.hideAxis('bottom')
                    
                # Link X-axes for synchronized scrolling
                if i > 0:
                    plot_item.setXLink(plot_widget.getItem(0, 0))
                    
        except ImportError:
            print("PyQtGraph GraphicsLayout not available, using simple stacked mode")
            self._draw_stacked_simple(plot_widget, data, depth_column, curve_configs)
    
    def _draw_stacked_simple(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Simple stacked implementation for when GraphicsLayout is not available."""
        depth_data = data[depth_column].values
        
        # Get visible curves
        visible_configs = [cfg for cfg in curve_configs if cfg.get('visible', True)]
        
        if not visible_configs:
            return
            
        # Calculate vertical offset for each curve
        vertical_offset = 0
        offset_step = 0.2  # Offset each curve by 20% of range
        
        for cfg in visible_configs:
            curve_name = cfg.get('name', '')
            column_name = cfg.get('column', '')
            color = cfg.get('color', QColor(0, 0, 255))
            line_style = cfg.get('line_style', 'solid')
            line_width = cfg.get('line_width', 1.0)
            
            if column_name not in data.columns:
                continue
                
            curve_data = data[column_name].values
            
            # Normalize curve data
            if len(curve_data) > 0:
                min_val = np.nanmin(curve_data)
                max_val = np.nanmax(curve_data)
                if max_val > min_val:
                    normalized = (curve_data - min_val) / (max_val - min_val)
                else:
                    normalized = np.zeros_like(curve_data)
            else:
                normalized = np.zeros_like(depth_data)
                
            # Apply vertical offset
            offset_data = normalized + vertical_offset
            vertical_offset += offset_step
            
            # Create pen
            pen = self._create_pen(color, line_style, line_width)
            
            # Plot curve
            plot_widget.plot(depth_data, offset_data, pen=pen, name=curve_name)


class SideBySideCurveMode(CurveDisplayMode):
    """Side-by-side mode - each curve in separate track."""
    
    def __init__(self):
        super().__init__(
            name="side_by_side",
            description="Each curve in separate track"
        )
        self.supported_features = ['independent_tracks', 'track_spacing', 'individual_legends']
        
    def configure_plot(self, plot_widget, curve_configs: List[Dict]) -> None:
        """Configure plot for side-by-side curves."""
        # Clear existing plots
        plot_widget.clear()
        
        # Side-by-side mode requires GraphicsLayout
        plot_widget.hideAxis('left')
        plot_widget.hideAxis('right')
        plot_widget.setLabel('bottom', 'Depth')
        
    def draw_curves(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Draw side-by-side curves using GraphicsLayout."""
        if data is None or depth_column not in data.columns:
            return
            
        depth_data = data[depth_column].values
        
        # Create GraphicsLayout for side-by-side plots
        try:
            from pyqtgraph import GraphicsLayout
            
            # Clear existing content
            plot_widget.clear()
            
            # Create GraphicsLayout if not already
            if not isinstance(plot_widget, GraphicsLayout):
                # We'll create a simple side-by-side visualization
                self._draw_side_by_side_simple(plot_widget, data, depth_column, curve_configs)
                return
            
            # Get visible curves
            visible_configs = [cfg for cfg in curve_configs if cfg.get('visible', True)]
            
            if not visible_configs:
                return
                
            # Create side-by-side layout - one column per curve
            num_curves = len(visible_configs)
            
            for i, cfg in enumerate(visible_configs):
                curve_name = cfg.get('name', '')
                column_name = cfg.get('column', '')
                color = cfg.get('color', QColor(0, 0, 255))
                line_style = cfg.get('line_style', 'solid')
                line_width = cfg.get('line_width', 1.0)
                
                if column_name not in data.columns:
                    continue
                    
                curve_data = data[column_name].values
                
                # Create pen
                pen = self._create_pen(color, line_style, line_width)
                
                # Add plot to layout
                plot_item = plot_widget.addPlot(row=0, col=i)
                plot_item.plot(depth_data, curve_data, pen=pen, name=curve_name)
                
                # Configure axes
                plot_item.setLabel('left', curve_name)
                plot_item.setLabel('bottom', 'Depth' if i == 0 else '')
                
                # Hide X-axis labels for non-first plots
                if i > 0:
                    plot_item.hideAxis('bottom')
                    
                # Link Y-axes for consistent scaling (optional)
                # if i > 0:
                #     plot_item.setYLink(plot_widget.getItem(0, 0))
                    
        except ImportError:
            print("PyQtGraph GraphicsLayout not available, using simple side-by-side mode")
            self._draw_side_by_side_simple(plot_widget, data, depth_column, curve_configs)
    
    def _draw_side_by_side_simple(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Simple side-by-side implementation."""
        depth_data = data[depth_column].values
        
        # Get visible curves
        visible_configs = [cfg for cfg in curve_configs if cfg.get('visible', True)]
        
        if not visible_configs:
            return
            
        # Calculate horizontal ranges for each curve
        num_curves = len(visible_configs)
        
        for i, cfg in enumerate(visible_configs):
            curve_name = cfg.get('name', '')
            column_name = cfg.get('column', '')
            color = cfg.get('color', QColor(0, 0, 255))
            line_style = cfg.get('line_style', 'solid')
            line_width = cfg.get('line_width', 1.0)
            
            if column_name not in data.columns:
                continue
                
            curve_data = data[column_name].values
            
            # Create pen
            pen = self._create_pen(color, line_style, line_width)
            
            # Plot each curve
            # Note: This simple implementation plots all curves on same plot
            # A proper side-by-side would need multiple plot widgets
            plot_widget.plot(depth_data, curve_data, pen=pen, name=curve_name)


class HistogramCurveMode(CurveDisplayMode):
    """Histogram display mode for selected curves."""
    
    def __init__(self):
        super().__init__(
            name="histogram",
            description="Histogram display for selected curves"
        )
        self.supported_features = ['histogram_bins', 'smoothing', 'statistics']
        
    def configure_plot(self, plot_widget, curve_configs: List[Dict]) -> None:
        """Configure plot for histogram display."""
        # Clear existing plots
        plot_widget.clear()
        
        plot_widget.setLabel('left', 'Frequency')
        plot_widget.setLabel('bottom', 'Value')
        plot_widget.hideAxis('right')
        
    def draw_curves(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Draw histogram for curves."""
        if data is None:
            return
            
        for cfg in curve_configs:
            curve_name = cfg.get('name', '')
            column_name = cfg.get('column', '')
            color = cfg.get('color', QColor(0, 0, 255))
            visible = cfg.get('visible', True)
            histogram_bins = cfg.get('histogram_bins', 50)
            
            if not visible or column_name not in data.columns:
                continue
                
            curve_data = data[column_name].values
            
            # Remove NaN values
            curve_data = curve_data[~np.isnan(curve_data)]
            
            if len(curve_data) == 0:
                continue
                
            # Create histogram
            hist, bins = np.histogram(curve_data, bins=histogram_bins)
            
            # Convert to curve for plotting
            bin_centers = (bins[:-1] + bins[1:]) / 2
            
            # Plot histogram as curve
            pen = pg.mkPen(color, width=2)
            plot_widget.plot(bin_centers, hist, pen=pen, name=f"{curve_name} Histogram")
            
            # Add fill under curve
            plot_widget.plot(bin_centers, hist, pen=pen, fillLevel=0, 
                           brush=pg.mkBrush(color.red(), color.green(), color.blue(), 100))


class CurveDisplayModes(QObject):
    """Manager for curve display modes."""
    
    # Signal emitted when display mode changes
    displayModeChanged = pyqtSignal(str, dict)  # mode_name, mode_info
    
    def __init__(self):
        super().__init__()
        # Available display modes
        self.modes = {
            'overlaid': OverlaidCurveMode(),
            'stacked': StackedCurveMode(),
            'side_by_side': SideBySideCurveMode(),
            'histogram': HistogramCurveMode()
        }
        
        # Current display mode
        self.current_mode = 'overlaid'
        
        # Mode settings
        self.mode_settings = {
            'overlaid': {'transparency': 0.7, 'dual_axis': True},
            'stacked': {'track_spacing': 20, 'show_track_labels': True},
            'side_by_side': {'track_width': 150, 'show_legends': True},
            'histogram': {'default_bins': 50, 'show_statistics': True}
        }
        
    def get_mode(self, mode_name: str) -> Optional[CurveDisplayMode]:
        """Get a display mode by name."""
        return self.modes.get(mode_name)
    
    def get_current_mode(self) -> CurveDisplayMode:
        """Get current display mode."""
        return self.modes.get(self.current_mode, self.modes['overlaid'])
    
    def set_mode(self, mode_name: str) -> bool:
        """Set current display mode."""
        if mode_name in self.modes and mode_name != self.current_mode:
            self.current_mode = mode_name
            mode_info = self.get_current_mode().get_mode_info()
            self.displayModeChanged.emit(mode_name, mode_info)
            return True
        return False
    
    def get_available_modes(self) -> List[str]:
        """Get list of available mode names."""
        return list(self.modes.keys())
    
    def get_mode_info(self, mode_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific mode."""
        mode = self.get_mode(mode_name)
        if mode:
            return mode.get_mode_info()
        return None
    
    def get_all_mode_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available modes."""
        return {name: mode.get_mode_info() for name, mode in self.modes.items()}
    
    def configure_plot(self, plot_widget, curve_configs: List[Dict]) -> None:
        """Configure plot for current display mode."""
        mode = self.get_current_mode()
        mode.configure_plot(plot_widget, curve_configs)
    
    def draw_curves(self, plot_widget, data, depth_column: str, curve_configs: List[Dict]) -> None:
        """Draw curves using current display mode."""
        mode = self.get_current_mode()
        mode.draw_curves(plot_widget, data, depth_column, curve_configs)
    
    def get_mode_setting(self, mode_name: str, setting_name: str, default=None) -> Any:
        """Get a setting for a specific mode."""
        mode_settings = self.mode_settings.get(mode_name, {})
        return mode_settings.get(setting_name, default)
    
    def set_mode_setting(self, mode_name: str, setting_name: str, value: Any) -> None:
        """Set a setting for a specific mode."""
        if mode_name not in self.mode_settings:
            self.mode_settings[mode_name] = {}
        self.mode_settings[mode_name][setting_name] = value
    
    def get_current_mode_settings(self) -> Dict[str, Any]:
        """Get settings for current mode."""
        return self.mode_settings.get(self.current_mode, {}).copy()


# Factory function for easy integration
def create_curve_display_modes() -> CurveDisplayModes:
    """Create and initialize curve display modes manager."""
    return CurveDisplayModes()