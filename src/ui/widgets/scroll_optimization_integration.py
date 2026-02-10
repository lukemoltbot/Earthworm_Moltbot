"""
ScrollOptimizationIntegration - Integrates ScrollOptimizer with existing plotter widgets.

This class provides:
1. Integration of ScrollOptimizer with PyQtGraphCurvePlotter
2. Integration of ScrollOptimizer with EnhancedStratigraphicColumn
3. Coordinated predictive rendering between widgets
4. Performance monitoring and adaptive optimization
"""

import time
from typing import Optional, Dict, Any
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget

from .scroll_optimizer import ScrollOptimizer
from .viewport_cache_manager import ViewportCacheManager
from .pyqtgraph_curve_plotter import PyQtGraphCurvePlotter
from .enhanced_stratigraphic_column import EnhancedStratigraphicColumn


class ScrollOptimizationIntegration(QObject):
    """
    Integrates scroll optimization with existing plotter widgets.
    """
    
    # Signals
    optimizationEnabled = pyqtSignal()
    optimizationDisabled = pyqtSignal()
    performanceStatsUpdated = pyqtSignal(dict)  # Performance statistics
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the ScrollOptimizationIntegration.
        
        Args:
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # Optimization components
        self.scroll_optimizer = None
        self.viewport_cache_manager = None
        
        # Widget references
        self.curve_plotter = None
        self.strat_column = None
        
        # Integration state
        self.is_initialized = False
        self.is_enabled = False
        
        # Performance monitoring
        self.performance_stats_timer = QTimer(self)
        self.performance_stats_timer.timeout.connect(self._update_performance_stats)
        
        # Configuration
        self.config = {
            'target_fps': 60,
            'max_cache_size_mb': 50.0,
            'enable_predictive_rendering': True,
            'enable_inertial_scrolling': True,
            'enable_adaptive_quality': True,
            'predictive_range_multiplier': 1.5,
            'inertial_deceleration': 0.95
        }
    
    def initialize(self, curve_plotter: PyQtGraphCurvePlotter, 
                   strat_column: EnhancedStratigraphicColumn):
        """
        Initialize optimization with the plotter widgets.
        
        Args:
            curve_plotter: PyQtGraphCurvePlotter instance
            strat_column: EnhancedStratigraphicColumn instance
        """
        if self.is_initialized:
            return
        
        self.curve_plotter = curve_plotter
        self.strat_column = strat_column
        
        # Create optimization components
        self.scroll_optimizer = ScrollOptimizer(
            target_fps=self.config['target_fps'],
            parent=self
        )
        
        self.viewport_cache_manager = ViewportCacheManager(
            max_cache_size_mb=self.config['max_cache_size_mb'],
            parent=self
        )
        
        # Configure scroll optimizer
        self._configure_scroll_optimizer()
        
        # Configure viewport cache manager
        self._configure_viewport_cache_manager()
        
        # Connect signals
        self._connect_signals()
        
        # Start performance monitoring
        self.performance_stats_timer.start(1000)  # Update every second
        
        self.is_initialized = True
        print("Scroll optimization initialized")
    
    def _configure_scroll_optimizer(self):
        """Configure the scroll optimizer."""
        if not self.scroll_optimizer:
            return
        
        # Set integration points
        self.scroll_optimizer.set_viewport_cache_manager(self.viewport_cache_manager)
        self.scroll_optimizer.set_curve_plotter(self.curve_plotter)
        
        # Configure based on settings
        self.scroll_optimizer.inertial_deceleration = self.config['inertial_deceleration']
        self.scroll_optimizer.predictive_range_multiplier = self.config['predictive_range_multiplier']
        self.scroll_optimizer.adaptive_quality = self.config['enable_adaptive_quality']
        
        # Connect optimizer signals
        self.scroll_optimizer.renderRequested.connect(self._on_render_requested)
        self.scroll_optimizer.viewChanged.connect(self._on_view_changed)
        self.scroll_optimizer.scrollVelocityChanged.connect(self._on_scroll_velocity_changed)
    
    def _configure_viewport_cache_manager(self):
        """Configure the viewport cache manager."""
        if not self.viewport_cache_manager:
            return
        
        # Set render callback
        self.viewport_cache_manager.set_render_callback(self._render_viewport)
        
        # Set quality adjustment callback
        self.viewport_cache_manager.set_quality_adjustment_callback(
            self._adjust_rendering_quality
        )
        
        # Connect cache manager signals
        self.viewport_cache_manager.cacheUpdated.connect(self._on_cache_updated)
        self.viewport_cache_manager.renderCompleted.connect(self._on_render_completed)
        self.viewport_cache_manager.memoryWarning.connect(self._on_memory_warning)
    
    def _connect_signals(self):
        """Connect signals between widgets and optimizer."""
        if not self.curve_plotter or not self.scroll_optimizer:
            return
        
        # Intercept wheel events from curve plotter
        original_wheel_event = self.curve_plotter.wheelEvent
        
        def optimized_wheel_event(event):
            if self.is_enabled and self.scroll_optimizer:
                # Let scroll optimizer handle the event
                if self.scroll_optimizer.process_scroll_event(event):
                    return  # Event handled by optimizer
            
            # Fall back to original wheel event
            if original_wheel_event:
                original_wheel_event(event)
        
        self.curve_plotter.wheelEvent = optimized_wheel_event
        
        # Connect view range changes for synchronization
        if hasattr(self.curve_plotter, 'viewRangeChanged'):
            self.curve_plotter.viewRangeChanged.connect(self._on_curve_plotter_view_changed)
        
        # Connect strat column scroll signals
        if self.strat_column and hasattr(self.strat_column, 'depthScrolled'):
            self.strat_column.depthScrolled.connect(self._on_strat_column_scrolled)
    
    def _render_viewport(self, view_range: tuple, quality: float) -> Any:
        """
        Render a viewport range at specified quality.
        
        Args:
            view_range: (min_depth, max_depth) to render
            quality: Render quality (0.0-1.0)
            
        Returns:
            Rendered data (image or other representation)
        """
        if not self.curve_plotter:
            return None
        
        # Apply quality settings to curve plotter
        self._apply_quality_to_plotter(quality)
        
        # Render the view range
        # Note: This is a simplified implementation
        # In a full implementation, we would:
        # 1. Temporarily set the view range
        # 2. Render to an off-screen buffer
        # 3. Restore original view range
        # 4. Return the rendered image
        
        # For now, return a placeholder
        return {
            'view_range': view_range,
            'quality': quality,
            'timestamp': time.time()
        }
    
    def _apply_quality_to_plotter(self, quality: float):
        """Apply quality settings to the curve plotter."""
        if not self.curve_plotter:
            return
        
        # Adjust curve resolution based on quality
        if quality < 0.5:
            # Low quality: reduce curve resolution
            if hasattr(self.curve_plotter, 'set_curve_resolution'):
                self.curve_plotter.set_curve_resolution(0.5)
        elif quality < 0.8:
            # Medium quality
            if hasattr(self.curve_plotter, 'set_curve_resolution'):
                self.curve_plotter.set_curve_resolution(0.8)
        else:
            # High quality: full resolution
            if hasattr(self.curve_plotter, 'set_curve_resolution'):
                self.curve_plotter.set_curve_resolution(1.0)
    
    def _adjust_rendering_quality(self, quality: float):
        """Adjust rendering quality based on performance."""
        self._apply_quality_to_plotter(quality)
    
    def _on_render_requested(self):
        """Handle render request from scroll optimizer."""
        # Trigger rendering in curve plotter
        if self.curve_plotter:
            self.curve_plotter.update()
    
    def _on_view_changed(self, min_depth: float, max_depth: float):
        """Handle view change from scroll optimizer."""
        # Update curve plotter view
        if self.curve_plotter and hasattr(self.curve_plotter, 'set_view_range'):
            self.curve_plotter.set_view_range(min_depth, max_depth)
        
        # Update strat column view
        if self.strat_column and hasattr(self.strat_column, 'scroll_to_depth'):
            center_depth = (min_depth + max_depth) / 2
            self.strat_column.scroll_to_depth(center_depth)
    
    def _on_scroll_velocity_changed(self, velocity: float):
        """Handle scroll velocity change."""
        # Update predictive rendering based on velocity
        if abs(velocity) > 50:  # pixels per second threshold
            self._trigger_predictive_rendering()
    
    def _on_curve_plotter_view_changed(self, min_depth: float, max_depth: float):
        """Handle view change from curve plotter."""
        if self.scroll_optimizer and self.is_enabled:
            # Update scroll optimizer's view
            self.scroll_optimizer.current_view_range = (min_depth, max_depth)
    
    def _on_strat_column_scrolled(self, center_depth: float):
        """Handle scroll from strat column."""
        if self.scroll_optimizer and self.is_enabled:
            # Calculate view range from center depth
            if hasattr(self.strat_column, 'viewport'):
                viewport = self.strat_column.viewport()
                if viewport:
                    view_height = viewport.height()
                    depth_range = view_height / self.strat_column.depth_scale
                    
                    min_depth = center_depth - depth_range / 2
                    max_depth = center_depth + depth_range / 2
                    
                    # Update scroll optimizer's view
                    self.scroll_optimizer.current_view_range = (min_depth, max_depth)
    
    def _on_cache_updated(self, cache_key: str):
        """Handle cache update."""
        # Cache was updated - could trigger UI updates if needed
        pass
    
    def _on_render_completed(self, cache_key: str, result: Any):
        """Handle render completion."""
        # Render completed - could update display if using cached renders
        pass
    
    def _on_memory_warning(self, usage_percentage: float):
        """Handle memory warning."""
        print(f"Memory warning: Cache usage at {usage_percentage:.1f}%")
        
        # Reduce cache size if memory is high
        if usage_percentage > 90:
            self.viewport_cache_manager._cleanup_cache(0.3)
    
    def _trigger_predictive_rendering(self):
        """Trigger predictive rendering based on current state."""
        if not self.scroll_optimizer or not self.viewport_cache_manager:
            return
        
        # Get predicted views from scroll optimizer
        predicted_views = self.scroll_optimizer.predict_next_view(
            self.scroll_optimizer.current_view_range,
            self.scroll_optimizer.scroll_velocity
        )
        
        # Request predictive rendering
        for view_range in predicted_views:
            # Determine priority based on scroll velocity
            priority = 1 if abs(self.scroll_optimizer.scroll_velocity) > 100 else 0
            
            # Determine quality based on velocity (faster scrolling = lower quality)
            velocity_factor = min(1.0, abs(self.scroll_optimizer.scroll_velocity) / 200.0)
            quality = max(0.3, 1.0 - velocity_factor * 0.5)
            
            self.viewport_cache_manager.request_predictive_render(
                view_range, 
                priority=priority,
                quality=quality
            )
    
    def _update_performance_stats(self):
        """Update and emit performance statistics."""
        if not self.is_enabled or not self.scroll_optimizer:
            return
        
        # Get stats from components
        optimizer_stats = self.scroll_optimizer.get_performance_stats()
        cache_stats = self.viewport_cache_manager.get_cache_stats() if self.viewport_cache_manager else {}
        
        # Combine stats
        stats = {
            **optimizer_stats,
            **cache_stats,
            'enabled': self.is_enabled,
            'predictive_rendering_enabled': self.config['enable_predictive_rendering'],
            'inertial_scrolling_enabled': self.config['enable_inertial_scrolling'],
            'adaptive_quality_enabled': self.config['enable_adaptive_quality']
        }
        
        # Emit stats
        self.performanceStatsUpdated.emit(stats)
    
    def enable(self):
        """Enable scroll optimization."""
        if not self.is_initialized:
            print("Cannot enable: Optimization not initialized")
            return
        
        if self.is_enabled:
            return
        
        self.is_enabled = True
        
        # Update viewport parameters
        self._update_viewport_parameters()
        
        # Start optimization components
        # Scroll optimizer doesn't need explicit start
        # Viewport cache manager is always running
        
        self.optimizationEnabled.emit()
        print("Scroll optimization enabled")
    
    def disable(self):
        """Disable scroll optimization."""
        if not self.is_enabled:
            return
        
        self.is_enabled = False
        
        # Stop optimization components
        if self.scroll_optimizer:
            self.scroll_optimizer.stop()
        
        if self.viewport_cache_manager:
            self.viewport_cache_manager.stop()
        
        self.optimizationDisabled.emit()
        print("Scroll optimization disabled")
    
    def _update_viewport_parameters(self):
        """Update viewport parameters in scroll optimizer."""
        if not self.scroll_optimizer or not self.curve_plotter:
            return
        
        # Get viewport parameters from curve plotter
        viewport_height = 500  # Default
        depth_scale = 10.0  # Default
        data_min_depth = 0.0
        data_max_depth = 100.0
        
        if hasattr(self.curve_plotter, 'viewport'):
            viewport = self.curve_plotter.viewport()
            if viewport:
                viewport_height = viewport.height()
        
        if hasattr(self.curve_plotter, 'depth_scale'):
            depth_scale = self.curve_plotter.depth_scale
        
        if hasattr(self.curve_plotter, 'data'):
            if self.curve_plotter.data is not None and not self.curve_plotter.data.empty:
                if hasattr(self.curve_plotter, 'depth_column'):
                    depth_col = self.curve_plotter.depth_column
                    if depth_col in self.curve_plotter.data.columns:
                        data_min_depth = self.curve_plotter.data[depth_col].min()
                        data_max_depth = self.curve_plotter.data[depth_col].max()
        
        # Set parameters in scroll optimizer
        self.scroll_optimizer.set_viewport_parameters(
            viewport_height, depth_scale, data_min_depth, data_max_depth
        )
    
    def update_config(self, config_updates: Dict[str, Any]):
        """
        Update optimization configuration.
        
        Args:
            config_updates: Dictionary of configuration updates
        """
        self.config.update(config_updates)
        
        # Apply updates to components
        if self.scroll_optimizer:
            if 'target_fps' in config_updates:
                self.scroll_optimizer.target_fps = config_updates['target_fps']
                self.scroll_optimizer.target_frame_time = 1000.0 / config_updates['target_fps']
            
            if 'inertial_deceleration' in config_updates:
                self.scroll_optimizer.inertial_deceleration = config_updates['inertial_deceleration']
            
            if 'predictive_range_multiplier' in config_updates:
                self.scroll_optimizer.predictive_range_multiplier = config_updates['predictive_range_multiplier']
            
            if 'enable_adaptive_quality' in config_updates:
                self.scroll_optimizer.adaptive_quality = config_updates['enable_adaptive_quality']
        
        if self.viewport_cache_manager and 'max_cache_size_mb' in config_updates:
            self.viewport_cache_manager.max_cache_size_bytes = (
                config_updates['max_cache_size_mb'] * 1024 * 1024
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        return {
            'initialized': self.is_initialized,
            'enabled': self.is_enabled,
            'curve_plotter_connected': self.curve_plotter is not None,
            'strat_column_connected': self.strat_column is not None,
            'scroll_optimizer_active': self.scroll_optimizer is not None,
            'cache_manager_active': self.viewport_cache_manager is not None
        }
    
    def cleanup(self):
        """Clean up resources."""
        self.disable()
        
        if self.scroll_optimizer:
            self.scroll_optimizer.deleteLater()
        
        if self.viewport_cache_manager:
            self.viewport_cache_manager.deleteLater()
        
        self.performance_stats_timer.stop()
        
        self.is_initialized = False
        print("Scroll optimization cleaned up")