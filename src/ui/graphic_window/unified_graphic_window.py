"""
UnifiedGraphicWindow - Main container for graphic window components.
Replicates 1 Point Desktop layout with synchronized components.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt
from src.core.graphic_models import HoleDataProvider
from src.ui.graphic_window.state import DepthStateManager, DepthCoordinateSystem
from src.ui.graphic_window.components import (
    PreviewWindow, StratigraphicColumn, LASCurvesDisplay, 
    LithologyDataTable, InformationPanel
)


class UnifiedGraphicWindow(QMainWindow):
    """
    Main graphic window replicating 1 Point Desktop layout.
    This is the PRIMARY container for all graphic window components.
    
    Layout:
    ┌─────────────────────────────────────────────────────────┐
    │ Preview │ Strat Column │ LAS Curves │ Lithology Table   │
    │ Window  │              │            │                   │
    │         │              │            │                   │
    │         │              │            │                   │
    ├─────────────────────────────────────────────────────────┤
    │ Information Panel (tabs: Info, Core Photo, Quality...) │
    └─────────────────────────────────────────────────────────┘
    """
    
    def __init__(self, hole_data_provider: HoleDataProvider):
        super().__init__()
        
        self.setWindowTitle("Unified Graphic Window - Earthworm")
        self.setGeometry(100, 100, 1600, 900)
        
        self.data_provider = hole_data_provider
        
        # Get hole depth range for state managers
        min_depth, max_depth = hole_data_provider.get_depth_range()
        
        # Initialize SHARED state managers (SINGLE INSTANCES)
        self.depth_state = DepthStateManager(min_depth, max_depth, data_provider=hole_data_provider)
        self.depth_coords = DepthCoordinateSystem(
            canvas_height=600,  # Will be updated in resize
            canvas_width=1200
        )
        
        # Create main UI
        self.setup_ui()
        
        # Initialize viewport to show first 10 meters
        self.depth_state.set_viewport_range(min_depth, min(max_depth, min_depth + 10))
    
    def setup_ui(self):
        """Create the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main vertical layout (top: components, bottom: info panel)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # ============ TOP: Component Area ============
        component_area = self.create_component_area()
        main_layout.addWidget(component_area, stretch=3)
        
        # ============ BOTTOM: Information Panel ============
        self.info_panel = InformationPanel(self.depth_state, self.depth_coords)
        main_layout.addWidget(self.info_panel, stretch=1)
    
    def create_component_area(self) -> QWidget:
        """Create the main component area with splitters."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create horizontal splitter for flexible resizing
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("QSplitter::handle { background: #CCCCCC; width: 4px; }")
        
        # ============ LEFT: Preview Window ============
        self.preview_window = PreviewWindow(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.preview_window.setMaximumWidth(150)
        main_splitter.addWidget(self.preview_window)
        
        # ============ CENTER: Main Visualization Area ============
        # This uses another splitter for strat column, LAS curves, and table
        visualization_splitter = QSplitter(Qt.Orientation.Horizontal)
        visualization_splitter.setStyleSheet("QSplitter::handle { background: #DDDDDD; width: 3px; }")
        
        # --- Stratigraphic Column ---
        self.strat_column = StratigraphicColumn(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.strat_column.setMinimumWidth(100)
        visualization_splitter.addWidget(self.strat_column)
        
        # --- LAS Curves Display ---
        self.las_curves = LASCurvesDisplay(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.las_curves.setMinimumWidth(400)
        visualization_splitter.addWidget(self.las_curves)
        
        # --- Lithology Data Table ---
        self.lithology_table = LithologyDataTable(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.lithology_table.setMinimumWidth(200)
        visualization_splitter.addWidget(self.lithology_table)
        
        # Set initial splitter sizes (approximate percentages)
        visualization_splitter.setSizes([150, 700, 300])
        
        # Add visualization splitter to main splitter
        main_splitter.addWidget(visualization_splitter)
        
        # Set main splitter sizes
        main_splitter.setSizes([150, 1150])  # Preview: 150px, Visualization: rest
        
        layout.addWidget(main_splitter)
        return container
    
    def resizeEvent(self, event):
        """Handle window resize - update coordinate system canvas size."""
        super().resizeEvent(event)
        
        # Update coordinate system canvas size based on LAS curves display size
        if hasattr(self, 'las_curves'):
            # Use LAS curves display size for coordinate system
            self.depth_coords.canvas_height = self.las_curves.height()
            self.depth_coords.canvas_width = self.las_curves.width()
            
            # Trigger repaint of all components
            self.depth_state.viewportRangeChanged.emit(self.depth_state.get_viewport_range())