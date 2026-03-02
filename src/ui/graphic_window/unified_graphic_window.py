"""
UnifiedGraphicWindow - Main container for graphic window components.
Replicates 1 Point Desktop layout with synchronized components.

SYSTEM A ARCHITECTURE:
- Single source of truth: DepthStateManager
- Broadcast-based signal flow: state → components
- Synchronizers prevent circular loops
- Pixel-perfect synchronization across all viewports
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter
)
from PyQt6.QtCore import Qt
from typing import Optional

from src.ui.graphic_window.state import DepthStateManager, DepthCoordinateSystem

# Feature flags for System A architecture
ENABLE_DEPTH_STATE_MANAGER = True
ENABLE_SYNCHRONIZERS = True
DISABLE_SYSTEM_B = True


class UnifiedGraphicWindow(QWidget):
    """
    Unified viewport container for System A components (Option B architecture).
    
    This container takes System A widgets (PyQtGraphCurvePlotter, EnhancedStratigraphicColumn)
    and unifies them into a single viewport with shared depth synchronization.
    
    Layout:
    ┌──────────────────────────────────────┐
    │  Strat Column  │ (seam) │  Curves   │
    │  (System A)    │        │ (System A)│
    │  EnhancedSC    │        │ PyQtGraph │
    └──────────────────────────────────────┘
    
    Architecture (System A):
    - Single DepthStateManager: Shared across all components (SINGLE SOURCE OF TRUTH)
    - No duplicate state managers
    - All widgets subscribe to signals and emit on user interaction
    - Unified depth coordinate system for pixel-perfect synchronization
    """
    
    def __init__(self, 
                 depth_state_manager: DepthStateManager,
                 curve_plotter: 'PyQtGraphCurvePlotter',
                 strat_column: 'EnhancedStratigraphicColumn',
                 hole_data_provider: Optional[object] = None):
        """
        Initialize unified viewport with System A widgets.
        
        Args:
            depth_state_manager: Shared DepthStateManager (single source of truth)
            curve_plotter: PyQtGraphCurvePlotter instance (System A widget)
            strat_column: EnhancedStratigraphicColumn instance (System A widget)
            hole_data_provider: Optional HoleDataProvider for metadata/context
        
        Architecture:
        - depth_state_manager is the SINGLE SOURCE OF TRUTH for all depth/viewport state
        - All components (curve_plotter, strat_column) already have references to this manager
        - No new DepthStateManager created here (prevents dual-manager conflict)
        - Unified container just arranges the widgets in a single viewport
        """
        super().__init__()
        
        self.depth_state_manager = depth_state_manager
        self.curve_plotter = curve_plotter
        self.strat_column = strat_column
        self.data_provider = hole_data_provider
        
        # ============================================================
        # SYSTEM A: Single Source of Truth (No duplicate state managers)
        # ============================================================
        # All state management is via self.depth_state_manager (already shared)
        # All synchronizers already initialized in DepthStateManager
        
        # Initialize coordinate system for pixel-perfect positioning
        self.depth_coords = DepthCoordinateSystem(
            canvas_height=600,  # Will be updated in resizeEvent
            canvas_width=1200
        )
        
        # Create main UI (unified layout)
        self.setup_ui()
    
    
    def setup_ui(self):
        """Create the main UI layout with unified System A components."""
        # Main layout (entire widget is the unified viewport)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ============ Component Area: Unified Viewport ============
        # Contains strat column and curves in a single splitter
        component_area = self.create_component_area()
        main_layout.addWidget(component_area)
        
        # Note: Information Panel removed for Option B (can be added back if needed)
        # If InformationPanel is still required, it would go here as a bottom panel
    
    def create_component_area(self) -> QWidget:
        """Create the unified viewport with System A components.
        
        Uses passed PyQtGraphCurvePlotter and EnhancedStratigraphicColumn widgets
        instead of creating generic components.
        
        Layout:
        ┌──────────────────────────────────────┐
        │  Strat Column  │ (seam) │  Curves   │
        │  (System A)    │        │ (System A)│
        └──────────────────────────────────────┘
        """
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ============================================================
        # Create unified splitter with System A components
        # ============================================================
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setStyleSheet("QSplitter::handle { background: #CCCCCC; width: 4px; }")
        
        # ============ LEFT: Enhanced Stratigraphic Column (System A) ============
        # This is the passed System A widget, already wired to depth_state_manager
        self.strat_column.setMinimumWidth(80)
        self.strat_column.setMaximumWidth(300)
        self.main_splitter.addWidget(self.strat_column)
        
        # ============ RIGHT: PyQtGraph Curve Plotter (System A) ============
        # This is the passed System A widget, already wired to depth_state_manager
        self.curve_plotter.setMinimumWidth(200)
        self.main_splitter.addWidget(self.curve_plotter)
        
        # Set initial splitter sizes (approximate: 25% strat column, 75% curves)
        self.main_splitter.setSizes([250, 750])
        
        # Allow users to resize the seam
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)
        
        layout.addWidget(self.main_splitter)
        return container
    
    def set_depth_range(self, min_depth: float, max_depth: float):
        """Set the visible depth range for all components.
        
        Args:
            min_depth: Minimum visible depth
            max_depth: Maximum visible depth
        """
        if self.depth_state_manager:
            self.depth_state_manager.set_viewport_range(min_depth, max_depth)
    
    def set_curve_visibility(self, curve_name: str, visible: bool):
        """Set curve visibility (proxy to curve plotter).
        
        Args:
            curve_name: Name of the curve
            visible: Whether the curve should be visible
        """
        if hasattr(self.curve_plotter, 'set_curve_visibility'):
            self.curve_plotter.set_curve_visibility(curve_name, visible)
    
    def resizeEvent(self, event):
        """Handle window resize - update coordinate system canvas size."""
        super().resizeEvent(event)
        
        # Update coordinate system canvas size based on curve plotter display size
        if hasattr(self, 'curve_plotter'):
            # Use curve plotter size for coordinate system
            self.depth_coords.canvas_height = self.curve_plotter.height()
            self.depth_coords.canvas_width = self.curve_plotter.width()
            
            # Notify depth state manager of size change
            if hasattr(self.depth_state_manager, 'viewportRangeChanged'):
                viewport_range = self.depth_state_manager.get_viewport_range()
                self.depth_state_manager.viewportRangeChanged.emit(viewport_range)