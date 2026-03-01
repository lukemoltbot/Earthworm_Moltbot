"""
DEPRECATED MODULE: ComponentAdapter

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
class ComponentConfig:
    """Configuration for component integration."""
    # Performance settings
    enable_lazy_updates: bool = True
    update_throttle_ms: int = 16  # ~60 FPS
    
    # Synchronization settings
    sync_tolerance_pixels: int = 1  # 1-pixel tolerance
    enable_bidirectional_sync: bool = True
    
    # Viewport settings
    default_viewport_width: int = 800
    default_viewport_height: int = 600


class ComponentAdapter(QObject):
    """
    DEPRECATED: Adapter for connecting scrolling synchronizer to actual components.
    
    ⚠️ This class is deprecated. System A implementations provide better integration.
    
    Handles:
    1. Signal/slot connections between components
    2. Depth/pixel coordinate conversion
    3. Performance-optimized updates
    4. Error handling and recovery
    """
    
    # Signals
    componentsConnected = pyqtSignal()
    synchronizationError = pyqtSignal(str, str)  # component, error
    performanceMetrics = pyqtSignal(dict)  # metrics dict
    
    def __init__(self, config: Optional[ComponentConfig] = None):
        """
        Initialize component adapter.
        
        ⚠️ DEPRECATED: Use System A implementations instead.
        """
        warnings.warn(
            "This component is deprecated. Use System A implementations instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__()
        
        self.config = config or ComponentConfig()
        
        # Component references
        self._curve_plotter = None
        self._strat_column = None
        self._pixel_mapper = None
        self._scrolling_synchronizer = None
        
        # State
        self._is_connected = False
        self._last_update_time = 0
        self._update_pending = False
        
        # Performance tracking
        self._update_times = []
        self._sync_errors = []
        
        logger.info("ComponentAdapter initialized")
    
    def connect_components(self, curve_plotter, strat_column, pixel_mapper, scrolling_synchronizer):
        """
        Connect all components for synchronized scrolling.
        
        Args:
            curve_plotter: PyQtGraphCurvePlotter instance
            strat_column: EnhancedStratigraphicColumn instance
            pixel_mapper: PixelDepthMapper instance
            scrolling_synchronizer: ScrollingSynchronizer instance
        """
        self._curve_plotter = curve_plotter
        self._strat_column = strat_column
        self._pixel_mapper = pixel_mapper
        self._scrolling_synchronizer = scrolling_synchronizer
        
        # Set components in scrolling synchronizer
        if self._scrolling_synchronizer:
            self._scrolling_synchronizer.set_components(
                curve_plotter, strat_column, pixel_mapper
            )
        
        # Connect signals
        self._connect_signals()
        
        self._is_connected = True
        self.componentsConnected.emit()
        
        logger.info("All components connected for synchronized scrolling")
    
    def _connect_signals(self):
        """Connect signals between components."""
        if not all([self._curve_plotter, self._strat_column, self._scrolling_synchronizer]):
            logger.error("Cannot connect signals: missing components")
            return
        
        try:
            # Connect scrolling synchronizer to components
            self._scrolling_synchronizer.scrollPositionChanged.connect(
                self._on_scroll_position_changed
            )
            
            # Connect curve plotter signals
            if hasattr(self._curve_plotter, 'viewRangeChanged'):
                self._curve_plotter.viewRangeChanged.connect(
                    self._on_curve_view_range_changed
                )
            
            # Connect strat column signals
            if hasattr(self._strat_column, 'depthClicked'):
                self._strat_column.depthClicked.connect(
                    self._on_column_depth_clicked
                )
            
            logger.debug("Component signals connected")
            
        except Exception as e:
            logger.error(f"Error connecting component signals: {e}")
            self.synchronizationError.emit("signal_connection", str(e))
    
    @pyqtSlot(float, int)
    def _on_scroll_position_changed(self, depth: float, pixel_offset: int):
        """
        Handle scroll position change from synchronizer.
        
        Updates both curve plotter and stratigraphic column.
        """
        import time
        update_start = time.time()
        
        try:
            # Update curve plotter
            if self._curve_plotter:
                self._update_curve_plotter_depth(depth)
            
            # Update stratigraphic column
            if self._strat_column:
                self._update_strat_column_depth(depth)
            
            # Track performance
            update_time = (time.time() - update_start) * 1000
            self._update_times.append(update_time)
            
            # Keep last 60 updates
            if len(self._update_times) > 60:
                self._update_times.pop(0)
            
            # Emit performance metrics
            self._emit_performance_metrics(update_time)
            
            logger.debug(f"Components updated to depth: {depth} (took {update_time:.1f}ms)")
            
        except Exception as e:
            logger.error(f"Error updating components: {e}")
            self.synchronizationError.emit("component_update", str(e))
            self._sync_errors.append(str(e))
    
    def _update_curve_plotter_depth(self, depth: float):
        """Update curve plotter to show depth."""
        if not self._curve_plotter:
            return
        
        try:
            # Check if curve plotter has set_view_range method
            if hasattr(self._curve_plotter, 'set_view_range'):
                # Calculate view range based on current zoom
                view_height = 100  # Default view height in depth units
                min_depth = depth - (view_height / 2)
                max_depth = depth + (view_height / 2)
                
                self._curve_plotter.set_view_range(min_depth, max_depth)
            
            # Alternative: Check for depth property
            elif hasattr(self._curve_plotter, 'current_depth'):
                self._curve_plotter.current_depth = depth
            
            logger.debug(f"Curve plotter updated to depth: {depth}")
            
        except Exception as e:
            logger.warning(f"Could not update curve plotter: {e}")
    
    def _update_strat_column_depth(self, depth: float):
        """Update stratigraphic column to show depth."""
        if not self._strat_column:
            return
        
        try:
            # Check if strat column has set_depth_position method
            if hasattr(self._strat_column, 'set_depth_position'):
                self._strat_column.set_depth_position(depth)
            
            # Alternative: Check for scroll_to_depth method
            elif hasattr(self._strat_column, 'scroll_to_depth'):
                self._strat_column.scroll_to_depth(depth)
            
            logger.debug(f"Strat column updated to depth: {depth}")
            
        except Exception as e:
            logger.warning(f"Could not update strat column: {e}")
    
    @pyqtSlot(float, float)
    def _on_curve_view_range_changed(self, min_depth: float, max_depth: float):
        """
        Handle view range change from curve plotter.
        
        Updates scrolling synchronizer position.
        """
        if not self._scrolling_synchronizer:
            return
        
        try:
            # Calculate center depth
            center_depth = (min_depth + max_depth) / 2
            
            # Update scrolling synchronizer
            self._scrolling_synchronizer.scroll_to_depth(center_depth)
            
            logger.debug(f"Sync updated from curve plotter range: {min_depth}-{max_depth}")
            
        except Exception as e:
            logger.error(f"Error syncing from curve plotter: {e}")
    
    @pyqtSlot(float)
    def _on_column_depth_clicked(self, depth: float):
        """
        Handle depth click from stratigraphic column.
        
        Updates scrolling synchronizer position.
        """
        if not self._scrolling_synchronizer:
            return
        
        try:
            # Update scrolling synchronizer
            self._scrolling_synchronizer.scroll_to_depth(depth)
            
            logger.debug(f"Sync updated from column click: {depth}")
            
        except Exception as e:
            logger.error(f"Error syncing from column click: {e}")
    
    def _emit_performance_metrics(self, last_update_time: float):
        """Emit performance metrics."""
        if not self._update_times:
            return
        
        metrics = {
            "avg_update_time_ms": sum(self._update_times) / len(self._update_times),
            "last_update_time_ms": last_update_time,
            "update_count": len(self._update_times),
            "sync_error_count": len(self._sync_errors),
            "components_connected": self._is_connected
        }
        
        self.performanceMetrics.emit(metrics)
    
    def get_component_status(self) -> Dict[str, Any]:
        """Get status of all connected components."""
        status = {
            "curve_plotter": {
                "connected": self._curve_plotter is not None,
                "type": type(self._curve_plotter).__name__ if self._curve_plotter else None
            },
            "strat_column": {
                "connected": self._strat_column is not None,
                "type": type(self._strat_column).__name__ if self._strat_column else None
            },
            "pixel_mapper": {
                "connected": self._pixel_mapper is not None,
                "type": type(self._pixel_mapper).__name__ if self._pixel_mapper else None
            },
            "scrolling_synchronizer": {
                "connected": self._scrolling_synchronizer is not None,
                "type": type(self._scrolling_synchronizer).__name__ if self._scrolling_synchronizer else None
            },
            "is_fully_connected": self._is_connected,
            "performance": {
                "avg_update_time_ms": sum(self._update_times) / len(self._update_times) if self._update_times else 0,
                "update_count": len(self._update_times),
                "sync_error_count": len(self._sync_errors)
            }
        }
        
        return status
    
    def disconnect_components(self):
        """Disconnect all components."""
        try:
            # Disconnect signals
            if self._scrolling_synchronizer:
                self._scrolling_synchronizer.scrollPositionChanged.disconnect()
            
            if self._curve_plotter and hasattr(self._curve_plotter, 'viewRangeChanged'):
                self._curve_plotter.viewRangeChanged.disconnect()
            
            if self._strat_column and hasattr(self._strat_column, 'depthClicked'):
                self._strat_column.depthClicked.disconnect()
            
            # Clear references
            self._curve_plotter = None
            self._strat_column = None
            self._pixel_mapper = None
            self._scrolling_synchronizer = None
            
            self._is_connected = False
            
            logger.info("All components disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting components: {e}")
    
    def test_connection(self) -> bool:
        """Test component connection and synchronization."""
        if not self._is_connected:
            logger.warning("Cannot test: components not connected")
            return False
        
        try:
            # Test with a sample depth
            test_depth = 50.0
            
            # Try to update scrolling synchronizer
            if self._scrolling_synchronizer:
                success = self._scrolling_synchronizer.scroll_to_depth(test_depth)
                if success:
                    logger.info(f"Connection test passed: scrolled to {test_depth}")
                    return True
                else:
                    logger.warning("Connection test failed: could not scroll to depth")
                    return False
            else:
                logger.warning("Connection test failed: no scrolling synchronizer")
                return False
                
        except Exception as e:
            logger.error(f"Connection test error: {e}")
            return False


# Integration test
def test_component_integration():
    """Test component integration."""
    print("🧪 Testing component integration...")
    
    # Create mock components for testing
    class MockCurvePlotter:
        viewRangeChanged = pyqtSignal(float, float)
        current_depth = 0.0
        
        def set_view_range(self, min_depth, max_depth):
            self.current_depth = (min_depth + max_depth) / 2
            print(f"  Mock curve plotter: view range {min_depth}-{max_depth}")
    
    class MockStratColumn:
        depthClicked = pyqtSignal(float)
        current_depth = 0.0
        
        def set_depth_position(self, depth):
            self.current_depth = depth
            print(f"  Mock strat column: depth position {depth}")
    
    class MockPixelMapper:
        def depth_to_pixel(self, depth):
            return int(depth * 10)  # Simple mapping
        
        def pixel_to_depth(self, pixel):
            return pixel / 10
        
        def update_viewport_size(self, width, height):
            print(f"  Mock pixel mapper: viewport {width}x{height}")
    
    # Create components
    curve_plotter = MockCurvePlotter()
    strat_column = MockStratColumn()
    pixel_mapper = MockPixelMapper()
    
    # Create adapter
    adapter = ComponentAdapter()
    
    # Create scrolling synchronizer
    from .scrolling_synchronizer import ScrollingSynchronizer, ScrollPerformanceConfig
    scroll_config = ScrollPerformanceConfig()
    scrolling_synchronizer = ScrollingSynchronizer(scroll_config)
    
    # Connect components
    adapter.connect_components(
        curve_plotter, strat_column, pixel_mapper, scrolling_synchronizer
    )
    
    # Test connection
    status = adapter.get_component_status()
    print(f"  Component status: {status['is_fully_connected']}")
    
    # Test scrolling
    test_result = adapter.test_connection()
    print(f"  Connection test: {'PASSED' if test_result else 'FAILED'}")
    
    # Cleanup
    adapter.disconnect_components()
    
    print("✅ Component integration test complete")
    return test_result


if __name__ == "__main__":
    # Run integration test
    test_component_integration()