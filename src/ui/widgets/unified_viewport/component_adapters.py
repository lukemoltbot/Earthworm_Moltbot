"""
DEPRECATED MODULE: ComponentAdapters

⚠️ WARNING: This module is part of System B (deprecated) and is maintained for backward compatibility only.

System A implementations should be used instead. See src/ui/graphic_window/ for System A components.
"""

import logging
import warnings
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


@dataclass
class ComponentViewState:
    """View state for a component."""
    min_depth: float = 0.0
    max_depth: float = 100.0
    visible_min_depth: float = 0.0
    visible_max_depth: float = 100.0
    current_depth: float = 0.0
    viewport_height: int = 600
    depth_scale: float = 10.0  # pixels per depth unit


class CurvePlotterAdapter(QObject):
    """
    DEPRECATED: Adapter for curve plotter component.
    
    ⚠️ This class is deprecated. System A implementations provide better integration.
    
    Provides standardized interface for scrolling synchronizer.
    """
    
    # Signals
    viewRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth
    depthPositionChanged = pyqtSignal(float)  # current_depth
    
    def __init__(self, curve_plotter):
        """
        Initialize adapter with curve plotter instance.
        
        ⚠️ DEPRECATED: Use System A implementations instead.
        """
        warnings.warn(
            "This component is deprecated. Use System A implementations instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()
        self._curve_plotter = curve_plotter
        self._state = ComponentViewState()
        
        # Extract state from curve plotter
        self._update_state_from_plotter()
        
        logger.debug("CurvePlotterAdapter initialized")
    
    def _update_state_from_plotter(self):
        """Update state from curve plotter."""
        if hasattr(self._curve_plotter, 'min_depth'):
            self._state.min_depth = self._curve_plotter.min_depth
        
        if hasattr(self._curve_plotter, 'max_depth'):
            self._state.max_depth = self._curve_plotter.max_depth
        
        if hasattr(self._curve_plotter, 'depth_scale'):
            self._state.depth_scale = self._curve_plotter.depth_scale
        
        # Get viewport height
        if self._curve_plotter.viewport():
            self._state.viewport_height = self._curve_plotter.viewport().height()
    
    def scroll_to_depth(self, depth: float) -> bool:
        """
        Scroll curve plotter to specific depth.
        
        Args:
            depth: Depth to scroll to
            
        Returns:
            True if successful
        """
        try:
            if hasattr(self._curve_plotter, 'scroll_to_depth'):
                self._curve_plotter.scroll_to_depth(depth)
                
                # Update state
                self._state.current_depth = depth
                
                # Calculate visible range
                viewport_height = self._state.viewport_height
                visible_range_depth = viewport_height / self._state.depth_scale
                
                self._state.visible_min_depth = max(
                    self._state.min_depth,
                    depth - (visible_range_depth / 2)
                )
                self._state.visible_max_depth = min(
                    self._state.max_depth,
                    depth + (visible_range_depth / 2)
                )
                
                # Emit signals
                self.depthPositionChanged.emit(depth)
                self.viewRangeChanged.emit(
                    self._state.visible_min_depth,
                    self._state.visible_max_depth
                )
                
                logger.debug(f"Curve plotter scrolled to depth: {depth}")
                return True
            else:
                logger.warning("Curve plotter doesn't have scroll_to_depth method")
                return False
        except Exception as e:
            logger.error(f"Error scrolling curve plotter: {e}")
            return False
    
    def set_view_range(self, min_depth: float, max_depth: float) -> bool:
        """
        Set visible view range.
        
        Args:
            min_depth: Minimum visible depth
            max_depth: Maximum visible depth
            
        Returns:
            True if successful
        """
        try:
            # Calculate center depth
            center_depth = (min_depth + max_depth) / 2
            
            # Scroll to center
            return self.scroll_to_depth(center_depth)
        except Exception as e:
            logger.error(f"Error setting curve plotter view range: {e}")
            return False
    
    def get_view_state(self) -> ComponentViewState:
        """Get current view state."""
        self._update_state_from_plotter()
        return self._state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "component_type": "curve_plotter",
            "min_depth": self._state.min_depth,
            "max_depth": self._state.max_depth,
            "current_depth": self._state.current_depth,
            "depth_scale": self._state.depth_scale,
            "viewport_height": self._state.viewport_height
        }


class StratigraphicColumnAdapter(QObject):
    """
    DEPRECATED: Adapter for stratigraphic column component.
    
    ⚠️ This class is deprecated. System A implementations provide better integration.
    
    Provides standardized interface for scrolling synchronizer.
    """
    
    # Signals
    viewRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth
    depthPositionChanged = pyqtSignal(float)  # current_depth
    
    def __init__(self, strat_column):
        """
        Initialize adapter with stratigraphic column instance.
        
        ⚠️ DEPRECATED: Use System A implementations instead.
        """
        warnings.warn(
            "This component is deprecated. Use System A implementations instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()
        self._strat_column = strat_column
        self._state = ComponentViewState()
        
        # Extract state from strat column
        self._update_state_from_column()
        
        logger.debug("StratigraphicColumnAdapter initialized")
    
    def _update_state_from_column(self):
        """Update state from stratigraphic column."""
        if hasattr(self._strat_column, 'min_depth'):
            self._state.min_depth = self._strat_column.min_depth
        
        if hasattr(self._strat_column, 'max_depth'):
            self._state.max_depth = self._strat_column.max_depth
        
        if hasattr(self._strat_column, 'default_view_range'):
            self._state.depth_scale = 1.0  # Default, will be calculated
        
        # Get viewport height
        if hasattr(self._strat_column, 'viewport'):
            if self._strat_column.viewport():
                self._state.viewport_height = self._strat_column.viewport().height()
    
    def scroll_to_depth(self, depth: float) -> bool:
        """
        Scroll stratigraphic column to specific depth.
        
        Args:
            depth: Depth to scroll to
            
        Returns:
            True if successful
        """
        try:
            # Check for scroll method
            if hasattr(self._strat_column, 'scroll_to_depth'):
                self._strat_column.scroll_to_depth(depth)
            elif hasattr(self._strat_column, 'set_visible_range'):
                # Calculate visible range based on default_view_range
                if hasattr(self._strat_column, 'default_view_range'):
                    view_range = self._strat_column.default_view_range
                    min_depth = max(self._state.min_depth, depth - (view_range / 2))
                    max_depth = min(self._state.max_depth, depth + (view_range / 2))
                    self._strat_column.set_visible_range(min_depth, max_depth)
            
            # Update state
            self._state.current_depth = depth
            
            # Emit signals
            self.depthPositionChanged.emit(depth)
            
            logger.debug(f"Stratigraphic column scrolled to depth: {depth}")
            return True
        except Exception as e:
            logger.error(f"Error scrolling stratigraphic column: {e}")
            return False
    
    def set_view_range(self, min_depth: float, max_depth: float) -> bool:
        """
        Set visible view range.
        
        Args:
            min_depth: Minimum visible depth
            max_depth: Maximum visible depth
            
        Returns:
            True if successful
        """
        try:
            # Calculate center depth
            center_depth = (min_depth + max_depth) / 2
            
            # Scroll to center
            return self.scroll_to_depth(center_depth)
        except Exception as e:
            logger.error(f"Error setting strat column view range: {e}")
            return False
    
    def get_view_state(self) -> ComponentViewState:
        """Get current view state."""
        self._update_state_from_column()
        return self._state
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "component_type": "stratigraphic_column",
            "min_depth": self._state.min_depth,
            "max_depth": self._state.max_depth,
            "current_depth": self._state.current_depth,
            "viewport_height": self._state.viewport_height
        }


class UnifiedComponentManager(QObject):
    """
    DEPRECATED: Manager for unified component integration.
    
    ⚠️ This class is deprecated. System A implementations provide better integration.
    
    Coordinates between scrolling synchronizer and component adapters.
    """
    
    # Signals
    componentsSynchronized = pyqtSignal(float)  # synchronized_depth
    synchronizationError = pyqtSignal(str)  # error_message
    
    def __init__(self):
        """
        Initialize component manager.
        
        ⚠️ DEPRECATED: Use System A implementations instead.
        """
        warnings.warn(
            "This component is deprecated. Use System A implementations instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()
        
        self._curve_adapter = None
        self._strat_adapter = None
        self._pixel_mapper = None
        
        self._synchronization_enabled = True
        
        logger.debug("UnifiedComponentManager initialized")
    
    def set_components(self, curve_plotter, strat_column, pixel_mapper):
        """Set components and create adapters."""
        try:
            # Create adapters
            self._curve_adapter = CurvePlotterAdapter(curve_plotter)
            self._strat_adapter = StratigraphicColumnAdapter(strat_column)
            self._pixel_mapper = pixel_mapper
            
            # Connect signals
            if self._curve_adapter:
                self._curve_adapter.viewRangeChanged.connect(
                    self._on_curve_view_range_changed
                )
                self._curve_adapter.depthPositionChanged.connect(
                    self._on_curve_depth_changed
                )
            
            if self._strat_adapter:
                self._strat_adapter.viewRangeChanged.connect(
                    self._on_strat_view_range_changed
                )
                self._strat_adapter.depthPositionChanged.connect(
                    self._on_strat_depth_changed
                )
            
            logger.info("Components set and adapters created")
            return True
        except Exception as e:
            logger.error(f"Error setting components: {e}")
            return False
    
    def synchronize_to_depth(self, depth: float) -> bool:
        """
        Synchronize all components to specific depth.
        
        Args:
            depth: Depth to synchronize to
            
        Returns:
            True if successful
        """
        if not self._synchronization_enabled:
            return False
        
        try:
            success = True
            
            # Synchronize curve plotter
            if self._curve_adapter:
                if not self._curve_adapter.scroll_to_depth(depth):
                    success = False
                    logger.warning(f"Failed to synchronize curve plotter to depth {depth}")
            
            # Synchronize stratigraphic column
            if self._strat_adapter:
                if not self._strat_adapter.scroll_to_depth(depth):
                    success = False
                    logger.warning(f"Failed to synchronize strat column to depth {depth}")
            
            if success:
                self.componentsSynchronized.emit(depth)
                logger.debug(f"Components synchronized to depth: {depth}")
            else:
                self.synchronizationError.emit(f"Partial synchronization to depth {depth}")
            
            return success
        except Exception as e:
            error_msg = f"Error synchronizing components: {e}"
            logger.error(error_msg)
            self.synchronizationError.emit(error_msg)
            return False
    
    def get_component_states(self) -> Dict[str, Any]:
        """Get states of all components."""
        states = {}
        
        if self._curve_adapter:
            states["curve_plotter"] = self._curve_adapter.get_view_state()
        
        if self._strat_adapter:
            states["stratigraphic_column"] = self._strat_adapter.get_view_state()
        
        return states
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report from all components."""
        report = {
            "synchronization_enabled": self._synchronization_enabled,
            "components": {}
        }
        
        if self._curve_adapter:
            report["components"]["curve_plotter"] = self._curve_adapter.get_performance_metrics()
        
        if self._strat_adapter:
            report["components"]["stratigraphic_column"] = self._strat_adapter.get_performance_metrics()
        
        return report
    
    def enable_synchronization(self, enabled: bool = True):
        """Enable or disable synchronization."""
        self._synchronization_enabled = enabled
        logger.debug(f"Component synchronization {'enabled' if enabled else 'disabled'}")
    
    # Signal handlers
    def _on_curve_view_range_changed(self, min_depth: float, max_depth: float):
        """Handle curve plotter view range change."""
        logger.debug(f"Curve plotter view range changed: {min_depth}-{max_depth}")
        
        # Optionally synchronize strat column
        if self._synchronization_enabled and self._strat_adapter:
            center_depth = (min_depth + max_depth) / 2
            self._strat_adapter.scroll_to_depth(center_depth)
    
    def _on_strat_view_range_changed(self, min_depth: float, max_depth: float):
        """Handle strat column view range change."""
        logger.debug(f"Strat column view range changed: {min_depth}-{max_depth}")
        
        # Optionally synchronize curve plotter
        if self._synchronization_enabled and self._curve_adapter:
            center_depth = (min_depth + max_depth) / 2
            self._curve_adapter.scroll_to_depth(center_depth)
    
    def _on_curve_depth_changed(self, depth: float):
        """Handle curve plotter depth change."""
        logger.debug(f"Curve plotter depth changed: {depth}")
        
        # Synchronize if enabled
        if self._synchronization_enabled and self._strat_adapter:
            self._strat_adapter.scroll_to_depth(depth)
    
    def _on_strat_depth_changed(self, depth: float):
        """Handle strat column depth change."""
        logger.debug(f"Strat column depth changed: {depth}")
        
        # Synchronize if enabled
        if self._synchronization_enabled and self._curve_adapter:
            self._curve_adapter.scroll_to_depth(depth)


# Factory function for easy integration
def create_unified_component_manager(curve_plotter=None, strat_column=None, pixel_mapper=None):
    """Create and configure unified component manager."""
    manager = UnifiedComponentManager()
    
    if curve_plotter and strat_column and pixel_mapper:
        manager.set_components(curve_plotter, strat_column, pixel_mapper)
    
    return manager