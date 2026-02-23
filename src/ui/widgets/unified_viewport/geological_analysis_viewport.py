"""
GeologicalAnalysisViewport - Main unified viewport widget.

Provides pixel-perfect synchronized display of LAS curves and
stratigraphic column in a single viewport.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QRect, QPoint
from PyQt6.QtGui import QPaintEvent, QResizeEvent, QWheelEvent, QMouseEvent

# Local imports
from .scrolling_synchronizer import ScrollingSynchronizer, ScrollPerformanceConfig
from .pixel_depth_mapper import PixelDepthMapper, PixelMappingConfig
from .unified_depth_scale_manager import UnifiedDepthScaleManager, DepthScaleConfig
from .component_adapters import (
    UnifiedComponentManager, 
    create_unified_component_manager
)
from .component_adapter import ComponentAdapter, ComponentConfig

logger = logging.getLogger(__name__)

@dataclass
class ViewportConfig:
    """Configuration for GeologicalAnalysisViewport."""
    # Width ratios (from unification plan)
    curve_width_ratio: float = 0.68  # 68% for curves
    column_width_ratio: float = 0.32  # 32% for strat column
    
    # Minimum widths (from unification plan)
    min_curve_width: int = 350  # pixels
    min_column_width: int = 220  # pixels
    
    # Synchronization tolerance
    pixel_tolerance: int = 1  # 1-pixel tolerance target
    
    # Performance settings
    enable_viewport_caching: bool = True
    cache_size_mb: int = 50
    
    # Visual settings
    background_color: str = "#FFFFFF"
    grid_line_color: str = "#E0E0E0"
    grid_line_width: int = 1
    
    # Geological color palette (from TODO.md)
    geological_colors: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize default geological colors if not provided."""
        if self.geological_colors is None:
            self.geological_colors = {
                'gamma': '#8b008b',      # Purple
                'density': '#0066cc',     # Blue
                'caliper': '#ffa500',     # Orange
                'resistivity': '#ff0000', # Red
                'background': '#FFFFFF',  # White
                'grid': '#E0E0E0',        # Light gray
                'text': '#000000',        # Black
                'highlight': '#FFFF00',   # Yellow for highlights
            }
    
    def get_geological_color(self, curve_type: str) -> str:
        """
        Get color for a geological curve type.
        
        Args:
            curve_type: Type of curve (gamma, density, caliper, resistivity, etc.)
            
        Returns:
            Hex color code, or default black if not found
        """
        curve_type_lower = curve_type.lower()
        return self.geological_colors.get(curve_type_lower, '#000000')
    
    # Typography settings (from TODO.md: "Consistent font family, 9pt axis labels")
    font_family: str = "Sans Serif"
    axis_label_size: int = 9  # points
    title_size: int = 11  # points
    tick_label_size: int = 8  # points
    
    def get_typography_css(self) -> str:
        """Get CSS for typography settings."""
        return f"""
            font-family: {self.font_family};
            font-size: {self.axis_label_size}pt;
        """


class GeologicalAnalysisViewport(QWidget):
    """
    Unified viewport for geological analysis.
    
    Combines LAS curve display and stratigraphic column display
    with pixel-perfect synchronization.
    
    Architecture:
        ┌─────────────────────────────────────────────┐
        │ GeologicalAnalysisViewport                  │
        │ ┌─────────────┬──────────────────────────┐ │
        │ │             │                          │ │
        │ │  Strat      │       LAS Curves         │ │
        │ │  Column     │                          │ │
        │ │  (32%)      │        (68%)             │ │
        │ │             │                          │ │
        │ └─────────────┴──────────────────────────┘ │
        │          Unified Scroll/Depth              │
        └─────────────────────────────────────────────┘
    """
    
    # Signals
    depthChanged = pyqtSignal(float)  # Current depth position changed
    viewRangeChanged = pyqtSignal(float, float)  # Visible depth range changed
    zoomLevelChanged = pyqtSignal(float)  # Zoom level changed
    pointClicked = pyqtSignal(float, dict)  # Point clicked (depth, data)
    boundaryDragged = pyqtSignal(int, str, float)  # Boundary dragged (row_index, boundary_type, new_depth)
    curveVisibilityChanged = pyqtSignal(str, bool)  # Curve visibility changed (curve_name, visible)
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the unified viewport."""
        super().__init__(parent)
        
        # Configuration
        self.config = ViewportConfig()
        
        # State
        self._depth_range: Optional[Tuple[float, float]] = None
        self._current_depth: Optional[float] = None
        self._zoom_level: float = 1.0
        
        # Component references (will be set by set_components)
        self._curve_plotter = None
        self._strat_column = None
        self._depth_manager = None
        self._pixel_mapper = None
        
        # Scrolling synchronization
        self._scrolling_synchronizer = None
        self._component_adapter = None
        self._setup_scrolling_synchronizer()
        self._setup_component_adapter()
        
        # Setup UI
        self._setup_ui()
        self._setup_connections()
        
        logger.info("GeologicalAnalysisViewport initialized")
    
    def _setup_scrolling_synchronizer(self) -> None:
        """Setup scrolling synchronization engine."""
        # Create scrolling performance configuration
        scroll_config = ScrollPerformanceConfig(
            target_fps=60,  # 60+ FPS target from Phase 3
            max_response_time_ms=100,  # < 100ms response
            max_memory_mb=50,  # < 50MB additional memory
            max_data_points=10000,  # Target for 10,000 data points
            enable_smooth_scrolling=True,
            scroll_sensitivity=1.0
        )
        
        # Create scrolling synchronizer
        self._scrolling_synchronizer = ScrollingSynchronizer(scroll_config)
        
        # Connect signals
        self._scrolling_synchronizer.scrollPositionChanged.connect(
            self._on_scroll_position_changed
        )
        self._scrolling_synchronizer.fpsUpdated.connect(
            self._on_fps_updated
        )
        self._scrolling_synchronizer.performanceAlert.connect(
            self._on_performance_alert
        )
        
        logger.debug("Scrolling synchronizer setup complete")
    
    def _setup_component_adapter(self) -> None:
        """Setup component adapter for integration."""
        # Create component configuration
        component_config = ComponentConfig(
            enable_lazy_updates=True,
            update_throttle_ms=16,  # ~60 FPS
            sync_tolerance_pixels=1,
            enable_bidirectional_sync=True
        )
        
        # Create component adapter
        self._component_adapter = ComponentAdapter(component_config)
        
        # Connect adapter signals
        self._component_adapter.componentsConnected.connect(
            self._on_components_connected
        )
        self._component_adapter.synchronizationError.connect(
            self._on_synchronization_error
        )
        self._component_adapter.performanceMetrics.connect(
            self._on_performance_metrics
        )
        
        logger.debug("Component adapter setup complete")
    
    def _setup_ui(self) -> None:
        """Setup the viewport UI layout."""
        # Main layout
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        
        # Create splitter for curves/column
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setChildrenCollapsible(False)
        self.layout().addWidget(self._splitter)
        
        # Create containers for components
        self._column_container = QFrame()
        self._column_container.setFrameStyle(QFrame.Shape.StyledPanel)
        self._column_container.setLayout(QVBoxLayout())
        self._column_container.layout().setContentsMargins(0, 0, 0, 0)
        
        self._curve_container = QFrame()
        self._curve_container.setFrameStyle(QFrame.Shape.StyledPanel)
        self._curve_container.setLayout(QVBoxLayout())
        self._curve_container.layout().setContentsMargins(0, 0, 0, 0)
        
        # Add to splitter
        self._splitter.addWidget(self._column_container)
        self._splitter.addWidget(self._curve_container)
        
        # Set initial sizes based on ratios
        total_width = 1000  # Default for initialization
        column_width = int(total_width * self.config.column_width_ratio)
        curve_width = int(total_width * self.config.curve_width_ratio)
        
        self._splitter.setSizes([column_width, curve_width])
        
        # Set size policies
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Apply geological styling
        self._apply_geological_styling()
        
        logger.debug("Viewport UI setup complete")
    
    def _apply_geological_styling(self) -> None:
        """Apply professional geological styling to the viewport."""
        # Apply background color
        self.setStyleSheet(f"""
            GeologicalAnalysisViewport {{
                background-color: {self.config.background_color};
            }}
            
            QFrame {{
                {self.config.get_typography_css()}
            }}
        """)
        
        # Apply specific styling to containers
        column_stylesheet = f"""
            QFrame {{
                border: 1px solid {self.config.grid_line_color};
                background-color: {self.config.background_color};
            }}
        """
        
        curve_stylesheet = f"""
            QFrame {{
                border: 1px solid {self.config.grid_line_color};
                background-color: {self.config.background_color};
            }}
        """
        
        self._column_container.setStyleSheet(column_stylesheet)
        self._curve_container.setStyleSheet(curve_stylesheet)
        
        # Log geological colors availability
        logger.debug(f"Geological colors configured: {list(self.config.geological_colors.keys())}")
        logger.debug(f"Typography: {self.config.font_family}, axis labels: {self.config.axis_label_size}pt")
    
    def _setup_connections(self) -> None:
        """Setup internal signal connections."""
        # Splitter size changes
        self._splitter.splitterMoved.connect(self._on_splitter_moved)
        
        logger.debug("Internal connections setup complete")
    
    def set_components(self, curve_plotter, strat_column, depth_manager, pixel_mapper) -> None:
        """
        Set the component widgets and managers.
        
        Args:
            curve_plotter: PyQtGraphCurvePlotter instance
            strat_column: EnhancedStratigraphicColumn instance  
            depth_manager: UnifiedDepthScaleManager instance
            pixel_mapper: PixelDepthMapper instance
        """
        self._curve_plotter = curve_plotter
        self._strat_column = strat_column
        self._depth_manager = depth_manager
        self._pixel_mapper = pixel_mapper
        
        # DEBUG: print component sizes
        print(f"DEBUG (GeologicalAnalysisViewport.set_components):")
        print(f"  - self.size() = {self.size()}")
        print(f"  - _column_container size = {self._column_container.size()}")
        print(f"  - _curve_container size = {self._curve_container.size()}")
        print(f"  - _splitter sizes = {self._splitter.sizes()}")
        
        # Ensure components have proper size policies for expansion
        if self._strat_column:
            self._strat_column.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            print(f"  - Adding strat_column to _column_container, parent = {self._strat_column.parent()}")
            self._column_container.layout().addWidget(self._strat_column)
            print(f"  - After add, strat_column parent = {self._strat_column.parent()}")
        
        if self._curve_plotter:
            self._curve_plotter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            print(f"  - Adding curve_plotter to _curve_container, parent = {self._curve_plotter.parent()}")
            self._curve_container.layout().addWidget(self._curve_plotter)
            print(f"  - After add, curve_plotter parent = {self._curve_plotter.parent()}")
        
        # Ensure containers are visible and have minimum size
        self._column_container.setMinimumSize(100, 100)
        self._curve_container.setMinimumSize(100, 100)
        
        # DEBUG: update splitter sizes to match actual width
        if self._splitter.width() > 0:
            column_width = int(self._splitter.width() * self.config.column_width_ratio)
            curve_width = int(self._splitter.width() * self.config.curve_width_ratio)
            self._splitter.setSizes([column_width, curve_width])
            print(f"  - Updated splitter sizes: {self._splitter.sizes()} (total width {self._splitter.width()})")
        
        # Connect components via adapter for synchronized scrolling
        if self._component_adapter:
            self._component_adapter.connect_components(
                curve_plotter, strat_column, pixel_mapper, self._scrolling_synchronizer
            )
        
        # Connect component signals for other interactions
        self._connect_component_signals()
        
        logger.info("Components set for unified viewport")
        print(f"DEBUG (GeologicalAnalysisViewport.set_components): Components added successfully")
    
    def set_curve_visibility(self, curve_name: str, visible: bool) -> None:
        """
        Set visibility of a curve in the unified viewport.
        
        Args:
            curve_name: Name of the curve (e.g., 'gamma', 'short_space_density')
            visible: Whether the curve should be visible
        """
        if self._curve_plotter and hasattr(self._curve_plotter, 'set_curve_visibility'):
            self._curve_plotter.set_curve_visibility(curve_name, visible)
            logger.debug(f"Set curve visibility: {curve_name} = {visible}")
        
        # Emit signal for external listeners
        self.curveVisibilityChanged.emit(curve_name, visible)
    
    def _connect_component_signals(self) -> None:
        """Connect signals from component widgets."""
        if not all([self._curve_plotter, self._strat_column, self._depth_manager]):
            logger.warning("Cannot connect signals - components not set")
            return
        
        # Connect curve plotter signals
        if hasattr(self._curve_plotter, 'pointClicked'):
            # Adapt signal signature: PyQtGraphCurvePlotter emits float only,
            # but our slot expects (float, dict). Provide empty dict.
            self._curve_plotter.pointClicked.connect(
                lambda depth: self._on_curve_point_clicked(depth, {})
            )
        
        if hasattr(self._curve_plotter, 'viewRangeChanged'):
            self._curve_plotter.viewRangeChanged.connect(self._on_curve_view_range_changed)
        
        if hasattr(self._curve_plotter, 'boundaryDragged'):
            # Connect boundary drag signal (signatures now match)
            self._curve_plotter.boundaryDragged.connect(self._on_boundary_dragged)
        
        # Connect strat column signals
        if hasattr(self._strat_column, 'depthClicked'):
            self._strat_column.depthClicked.connect(self._on_column_depth_clicked)
        
        if hasattr(self._strat_column, 'viewRangeChanged'):
            self._strat_column.viewRangeChanged.connect(self._on_column_view_range_changed)
        
        # Connect depth manager signals
        if hasattr(self._depth_manager, 'depthChanged'):
            self._depth_manager.depthChanged.connect(self.depthChanged)
        
        if hasattr(self._depth_manager, 'viewRangeChanged'):
            self._depth_manager.viewRangeChanged.connect(self.viewRangeChanged)
        
        if hasattr(self._depth_manager, 'zoomLevelChanged'):
            self._depth_manager.zoomLevelChanged.connect(self.zoomLevelChanged)
        
        logger.debug("Component signals connected")
    
    # Public API Methods
    
    def set_depth_range(self, min_depth: float, max_depth: float) -> None:
        """
        Set the depth range for the viewport.
        
        Args:
            min_depth: Minimum depth value
            max_depth: Maximum depth value
        """
        print(f"DEBUG (GeologicalAnalysisViewport.set_depth_range): Setting range {min_depth:.2f}-{max_depth:.2f}")
        self._depth_range = (min_depth, max_depth)
        
        # Set depth manager
        if self._depth_manager:
            self._depth_manager.set_view_range(min_depth, max_depth, emit_signal=False)
            print(f"DEBUG (GeologicalAnalysisViewport.set_depth_range): Depth manager updated")
        
        # Also set the curve plotter and strat column directly
        if self._curve_plotter and hasattr(self._curve_plotter, 'set_depth_range'):
            self._curve_plotter.set_depth_range(min_depth, max_depth)
            print(f"DEBUG (GeologicalAnalysisViewport.set_depth_range): Curve plotter range set")
        
        if self._strat_column and hasattr(self._strat_column, 'set_depth_range'):
            self._strat_column.set_depth_range(min_depth, max_depth)
            print(f"DEBUG (GeologicalAnalysisViewport.set_depth_range): Strat column range set")
        
        logger.debug(f"Depth range set: {min_depth:.2f} - {max_depth:.2f}")
    
    def set_current_depth(self, depth: float) -> None:
        """
        Set the current depth position.
        
        Args:
            depth: Depth value to set
        """
        self._current_depth = depth
        
        if self._depth_manager:
            self._depth_manager.set_depth(depth, emit_signal=False)
        
        self.depthChanged.emit(depth)
        
        logger.debug(f"Current depth set: {depth:.2f}")
    
    def set_zoom_level(self, zoom: float) -> None:
        """
        Set the zoom level.
        
        Args:
            zoom: Zoom level (1.0 = 100%)
        """
        self._zoom_level = zoom
        
        if self._depth_manager:
            self._depth_manager.set_zoom_level(zoom)
        
        self.zoomLevelChanged.emit(zoom)
        
        logger.debug(f"Zoom level set: {zoom:.2f}")
    
    def get_viewport_rect(self) -> QRect:
        """
        Get the viewport rectangle in widget coordinates.
        
        Returns:
            QRect: Viewport rectangle
        """
        return self.rect()
    
    def get_pixel_for_depth(self, depth: float) -> Optional[int]:
        """
        Convert depth to pixel position.
        
        Args:
            depth: Depth value
            
        Returns:
            int: Pixel position or None if not mapped
        """
        if self._pixel_mapper:
            return self._pixel_mapper.depth_to_pixel(depth)
        return None
    
    def get_depth_for_pixel(self, pixel: int) -> Optional[float]:
        """
        Convert pixel position to depth.
        
        Args:
            pixel: Pixel position
            
        Returns:
            float: Depth value or None if not mapped
        """
        if self._pixel_mapper:
            return self._pixel_mapper.pixel_to_depth(pixel)
        return None
    
    def check_synchronization(self) -> Dict[str, Any]:
        """
        Check synchronization accuracy between components.
        
        Returns:
            Dict with synchronization metrics
        """
        if not all([self._curve_plotter, self._strat_column, self._pixel_mapper]):
            return {"error": "Components not available"}
        
        metrics = {
            "pixel_tolerance": self.config.pixel_tolerance,
            "components_ready": True,
            "synchronization_checks": []
        }
        
        # Check pixel mapping consistency
        if self._depth_range:
            min_depth, max_depth = self._depth_range
            test_depths = [
                min_depth,
                (min_depth + max_depth) / 2,
                max_depth
            ]
            
            for depth in test_depths:
                pixel = self.get_pixel_for_depth(depth)
                if pixel is not None:
                    metrics["synchronization_checks"].append({
                        "depth": depth,
                        "pixel": pixel,
                        "status": "mapped"
                    })
        
        logger.debug(f"Synchronization check: {len(metrics['synchronization_checks'])} points")
        return metrics
    
    # Event Handlers
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle resize events."""
        super().resizeEvent(event)
        
        # Update pixel mapper with new size
        if self._pixel_mapper:
            self._pixel_mapper.update_viewport_size(self.width(), self.height())
        
        logger.debug(f"Viewport resized to {self.width()}x{self.height()}")
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Custom painting for viewport background and grid."""
        super().paintEvent(event)
        # Background painting handled by stylesheet
    
    # Event Handlers
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel events for scrolling."""
        if self._scrolling_synchronizer:
            if self._scrolling_synchronizer.handle_wheel_event(event):
                return
        
        # Fall back to default handling
        super().wheelEvent(event)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for drag scrolling."""
        self._drag_start_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move for drag scrolling."""
        if hasattr(self, '_drag_start_pos') and self._scrolling_synchronizer:
            if self._scrolling_synchronizer.handle_mouse_drag(
                self._drag_start_pos, event.pos()
            ):
                self._drag_start_pos = event.pos()
                return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release."""
        if hasattr(self, '_drag_start_pos'):
            delattr(self, '_drag_start_pos')
        super().mouseReleaseEvent(event)
    
    # Component adapter signal handlers
    def _on_components_connected(self):
        """Handle components connected via adapter."""
        logger.info("Components connected via adapter for synchronized scrolling")
        
        # Get component status
        if self._component_adapter:
            status = self._component_adapter.get_component_status()
            logger.debug(f"Component status: {status}")
    
    def _on_synchronization_error(self, component: str, error: str):
        """Handle synchronization error from adapter."""
        logger.error(f"Synchronization error in {component}: {error}")
        # Could show user notification or trigger recovery
    
    def _on_performance_metrics(self, metrics: dict):
        """Handle performance metrics from adapter."""
        # Log performance metrics periodically
        avg_update_time = metrics.get('avg_update_time_ms', 0)
        if avg_update_time > 50:  # >50ms is slow
            logger.warning(f"Slow component updates: {avg_update_time:.1f}ms")
    
    # Scrolling synchronizer signal handlers
    def _on_scroll_position_changed(self, depth: float, pixel_offset: int) -> None:
        """Handle scroll position change from synchronizer."""
        self._current_depth = depth
        self.depthChanged.emit(depth)
        
        # Update components (now handled by adapter)
        # self._synchronize_components_to_depth(depth)
        
        logger.debug(f"Scroll position changed: depth={depth}, pixel_offset={pixel_offset}")
    
    def _on_fps_updated(self, fps: float) -> None:
        """Handle FPS update from synchronizer."""
        # Could update a status bar or log performance
        if fps < 50:  # Warning threshold
            logger.warning(f"Low FPS: {fps:.1f}")
    
    def _on_performance_alert(self, alert_type: str, value: float) -> None:
        """Handle performance alert from synchronizer."""
        logger.warning(f"Performance alert: {alert_type}={value}")
        # Could trigger optimization or user notification
    
    def _synchronize_components_to_depth(self, depth: float) -> None:
        """Synchronize all components to the given depth."""
        if self._curve_plotter:
            # Update curve plotter view
            pass
        
        if self._strat_column:
            # Update strat column view
            pass
        
        logger.debug(f"Components synchronized to depth: {depth}")
    
    # Slot Methods
    
    @pyqtSlot(int, int)
    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Handle splitter movement."""
        sizes = self._splitter.sizes()
        total = sum(sizes)
        
        if total > 0 and len(sizes) == 2:
            actual_ratio = sizes[0] / total
            target_ratio = self.config.column_width_ratio
            
            # Log ratio deviation
            deviation = abs(actual_ratio - target_ratio)
            if deviation > 0.05:  # More than 5% deviation
                logger.debug(f"Splitter ratio deviation: {deviation:.3f}")
    
    @pyqtSlot(float, dict)
    def _on_curve_point_clicked(self, depth: float, data: dict) -> None:
        """Forward curve point clicks."""
        self.pointClicked.emit(depth, data)
    
    @pyqtSlot(float, float)
    def _on_curve_view_range_changed(self, min_depth: float, max_depth: float) -> None:
        """Forward curve view range changes."""
        self.viewRangeChanged.emit(min_depth, max_depth)
    
    @pyqtSlot(int, str, float)
    def _on_boundary_dragged(self, row_index: int, boundary_type: str, new_depth: float) -> None:
        """Forward boundary drag events."""
        self.boundaryDragged.emit(row_index, boundary_type, new_depth)
    
    @pyqtSlot(float)
    def _on_column_depth_clicked(self, depth: float) -> None:
        """Forward column depth clicks."""
        self.pointClicked.emit(depth, {"source": "strat_column"})
    
    @pyqtSlot(float, float)
    def _on_column_view_range_changed(self, min_depth: float, max_depth: float) -> None:
        """Forward column view range changes."""
        self.viewRangeChanged.emit(min_depth, max_depth)
    
    # Properties
    
    @property
    def depth_range(self) -> Optional[Tuple[float, float]]:
        """Get current depth range."""
        return self._depth_range
    
    @property
    def current_depth(self) -> Optional[float]:
        """Get current depth position."""
        return self._current_depth
    
    @property
    def zoom_level(self) -> float:
        """Get current zoom level."""
        return self._zoom_level
    
    @property
    def curve_width(self) -> int:
        """Get current curve area width in pixels."""
        if self._splitter and self._splitter.count() > 1:
            return self._splitter.sizes()[1]
        return 0
    
    @property
    def column_width(self) -> int:
        """Get current column area width in pixels."""
        if self._splitter and self._splitter.count() > 0:
            return self._splitter.sizes()[0]
        return 0
    
    def showEvent(self, event):
        """Handle show event to debug visibility."""
        super().showEvent(event)
        print(f"DEBUG (GeologicalAnalysisViewport.showEvent):")
        print(f"  - isVisible = {self.isVisible()}")
        print(f"  - size = {self.size()}")
        print(f"  - splitter sizes = {self._splitter.sizes()}")
        print(f"  - column_container size = {self._column_container.size()}")
        print(f"  - curve_container size = {self._curve_container.size()}")
        if self._strat_column:
            print(f"  - strat_column parent = {self._strat_column.parent()}, visible = {self._strat_column.isVisible()}")
        if self._curve_plotter:
            print(f"  - curve_plotter parent = {self._curve_plotter.parent()}, visible = {self._curve_plotter.isVisible()}")
    
    def resizeEvent(self, event):
        """Handle resize event to update splitter sizes."""
        super().resizeEvent(event)
        if self._splitter and self._splitter.width() > 0:
            column_width = int(self._splitter.width() * self.config.column_width_ratio)
            curve_width = int(self._splitter.width() * self.config.curve_width_ratio)
            self._splitter.setSizes([column_width, curve_width])
            print(f"DEBUG (GeologicalAnalysisViewport.resizeEvent):")
            print(f"  - new size = {self.size()}")
            print(f"  - splitter sizes = {self._splitter.sizes()}")


# Simple test function
def test_viewport_creation():
    """Test function for GeologicalAnalysisViewport."""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication([])
    viewport = GeologicalAnalysisViewport()
    viewport.show()
    
    print(f"Viewport created: {viewport.width()}x{viewport.height()}")
    print(f"Config: {viewport.config}")
    
    return app.exec()


if __name__ == "__main__":
    test_viewport_creation()