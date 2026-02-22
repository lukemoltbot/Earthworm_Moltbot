from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QScrollArea, QDockWidget,
    QPushButton, QComboBox, QLabel, QGraphicsView, QFileDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QColorDialog, QGraphicsScene, QDoubleSpinBox, QCheckBox, QSlider, QSpinBox, QFrame, QSplitter, QAbstractItemView,
    QGroupBox, QGridLayout, QFormLayout, QSizePolicy,
    QMdiArea, QMdiSubWindow, QMenu,
    QTreeView, QProgressBar, QApplication, QToolBar, QToolButton,
    QTextBrowser, QListWidget, QLineEdit, QListWidgetItem
)
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QBrush, QFileSystemModel, QAction, QIcon
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QPointF, QTimer
import pandas as pd
import numpy as np
import os
import json
import traceback
import webbrowser

from ..core.data_processor import DataProcessor
from ..core.analyzer import Analyzer
from ..core.workers import LASLoaderWorker, ValidationWorker
from ..core.config import DEFAULT_LITHOLOGY_RULES, DEPTH_COLUMN, DEFAULT_SEPARATOR_THICKNESS, DRAW_SEPARATOR_LINES, DEFAULT_CURVE_THICKNESS, CURVE_RANGES, INVALID_DATA_VALUE, DEFAULT_MERGE_THIN_UNITS, DEFAULT_MERGE_THRESHOLD, DEFAULT_SMART_INTERBEDDING, DEFAULT_SMART_INTERBEDDING_MAX_SEQUENCE_LENGTH, DEFAULT_SMART_INTERBEDDING_THICK_UNIT_THRESHOLD, DEFAULT_FALLBACK_CLASSIFICATION, DEFAULT_BIT_SIZE_MM, DEFAULT_SHOW_ANOMALY_HIGHLIGHTS, DEFAULT_CASING_DEPTH_ENABLED, DEFAULT_CASING_DEPTH_M, LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN, RECORD_SEQUENCE_FLAG_COLUMN, INTERRELATIONSHIP_COLUMN, LITHOLOGY_PERCENT_COLUMN, COALLOG_V31_COLUMNS
from ..core.coallog_utils import load_coallog_dictionaries
from .widgets.stratigraphic_column import StratigraphicColumn
from .widgets.enhanced_stratigraphic_column import EnhancedStratigraphicColumn
from .widgets.svg_renderer import SvgRenderer
from .widgets.curve_plotter import CurvePlotter # Import CurvePlotter
from .widgets.pyqtgraph_curve_plotter import PyQtGraphCurvePlotter # Import PyQtGraph-based plotter
from .widgets.unified_viewport.geological_analysis_viewport import GeologicalAnalysisViewport # Import unified geological viewport
from .widgets.unified_viewport.unified_depth_scale_manager import UnifiedDepthScaleManager, DepthScaleConfig, DepthScaleMode
from .widgets.unified_viewport.pixel_depth_mapper import PixelDepthMapper, PixelMappingConfig
from .widgets.enhanced_range_gap_visualizer import EnhancedRangeGapVisualizer # Import enhanced widget
from .widgets.curve_visibility_manager import CurveVisibilityManager # Import curve visibility manager
from .widgets.curve_visibility_toolbar import CurveVisibilityToolbar # Import curve visibility toolbar
from .widgets.curve_display_modes import CurveDisplayModes, create_curve_display_modes # Import curve display modes
from .widgets.curve_display_mode_switcher import create_display_mode_switcher, create_display_mode_menu # Import display mode switcher
from .widgets.cross_hole_sync_manager import create_cross_hole_sync_manager, CrossHoleSyncSettings # Import cross-hole sync manager
from .widgets.curve_export_manager import create_curve_export_manager # Import curve export manager
from .widgets.curve_analysis_manager import create_curve_analysis_manager # Import curve analysis manager
from ..core.settings_manager import load_settings, save_settings
from .dialogs.researched_defaults_dialog import ResearchedDefaultsDialog # Import new dialog
from .dialogs.column_configurator_dialog import ColumnConfiguratorDialog # Import column configurator dialog
from .dialogs.settings_dialog import SettingsDialog # Import settings dialog
from .dialogs.session_dialog import SessionDialog # Import session dialog
from .dialogs.template_dialog import TemplateDialog # Import template dialog
from .dialogs.nl_review_dialog import NLReviewDialog # Import NL review dialog
from ..utils.range_analyzer import RangeAnalyzer # Import range analyzer
from .widgets.compact_range_widget import CompactRangeWidget # Import compact widgets
from .widgets.multi_attribute_widget import MultiAttributeWidget
from .widgets.enhanced_pattern_preview import EnhancedPatternPreview
from .widgets.lithology_table import LithologyTableWidget
from .widgets.map_window import MapWindow # Import MapWindow for Phase 5
from .context_menus import OnePointContextMenus # Import 1Point-style context menus
from .status_bar_enhancer import StatusBarEnhancer # Import enhanced status bar
from .widgets.cross_section_window import CrossSectionWindow # Import CrossSectionWindow for Phase 5

# Layout presets system
from .layout_presets import OnePointLayoutPresets, LayoutManager
from .widgets.layout_toolbar import LayoutToolbar
from .dialogs.layout_manager_dialog import LayoutManagerDialog
from .dialogs.save_layout_dialog import SaveLayoutDialog

# Icon loader for unique, visible icons
from .icon_loader import (
    get_add_icon, get_save_icon, get_open_icon, get_settings_icon,
    get_folder_icon, get_chart_icon, get_layers_icon, 
    get_table_icon, get_overview_icon
)

class SvgPreviewWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 50)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.svg_renderer = SvgRenderer()

    def update_preview(self, svg_path, color):
        self.scene.clear()
        # Safety check to prevent drawing on a zero-size widget
        if self.width() <= 0 or self.height() <= 0:
            return
        pixmap = self.svg_renderer.render_svg(svg_path, self.width(), self.height(), color)
        if pixmap is not None:
            self.scene.addPixmap(pixmap)
        else:
            self.scene.setBackgroundBrush(QColor(color))
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


class HoleEditorWindow(QWidget):
    """A self-contained window for editing a single drill hole."""

    def __init__(self, parent=None, coallog_data=None, file_path=None, main_window=None):
        super().__init__(parent)
        self.coallog_data = coallog_data
        self.file_path = file_path
        self.main_window = main_window
        self.dataframe = None
        self.file_metadata = None

        # Create widgets - using PyQtGraphCurvePlotter for better performance
        self.curvePlotter = PyQtGraphCurvePlotter()
        self.stratigraphicColumnView = StratigraphicColumn()  # Overview column (entire hole)
        self.enhancedStratColumnView = EnhancedStratigraphicColumn()  # Enhanced column (detailed, synchronized)
        
        # Create unified geological analysis viewport (Phase 4)
        # Configure depth scale manager for pixel-perfect synchronization
        depth_config = DepthScaleConfig(
            mode=DepthScaleMode.PIXEL_PERFECT,
            pixel_tolerance=1,
            min_depth=0.0,
            max_depth=10000.0,
            default_view_range=(0.0, 1000.0)
        )
        self.unified_depth_manager = UnifiedDepthScaleManager(depth_config)
        
        # Configure pixel mapper with default viewport size (will be updated on resize)
        pixel_config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=1000.0,
            viewport_width=800,
            viewport_height=600,
            vertical_padding=2,
            pixel_tolerance=1
        )
        self.unified_pixel_mapper = PixelDepthMapper(pixel_config)
        
        # Create the unified viewport
        self.unifiedViewport = GeologicalAnalysisViewport()
        self.unifiedViewport.set_components(
            self.curvePlotter,
            self.enhancedStratColumnView,
            self.unified_depth_manager,
            self.unified_pixel_mapper
        )
        self.editorTable = LithologyTableWidget()
        
        # Create icon buttons for actions
        self.createInterbeddingIconButton = QToolButton()
        self.createInterbeddingIconButton.setIcon(get_add_icon())
        self.createInterbeddingIconButton.setToolTip("Create Interbedding")
        self.createInterbeddingIconButton.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        
        self.exportCsvIconButton = QToolButton()
        self.exportCsvIconButton.setIcon(get_save_icon())
        self.exportCsvIconButton.setToolTip("Export to CSV")
        self.exportCsvIconButton.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        
        # Create zoom state manager for synchronization
        from .widgets.zoom_state_manager import ZoomStateManager
        from .widgets.scale_keyboard_controls import ScaleKeyboardControls
        
        self.zoom_state_manager = ZoomStateManager(self)
        self.zoom_state_manager.set_widgets(self.enhancedStratColumnView, self.curvePlotter)
        
        # Connect engineering scale signal
        self.zoom_state_manager.engineeringScaleChanged.connect(self._on_engineering_scale_changed)
        
        # Connect zoom signals to unified viewport (Phase 4)
        if hasattr(self, 'unifiedViewport'):
            # Zoom state changed (center, min, max) -> set depth range on unified viewport
            self.zoom_state_manager.zoomStateChanged.connect(
                lambda center, min_depth, max_depth: self.unifiedViewport.set_depth_range(min_depth, max_depth)
            )
            # Zoom level changed -> set zoom level on unified viewport
            self.zoom_state_manager.zoomLevelChanged.connect(self.unifiedViewport.set_zoom_level)
            
            # Connect unified viewport signals back to zoom manager
            self.unifiedViewport.viewRangeChanged.connect(self.zoom_state_manager.zoom_to_range)
            # Note: zoomLevelChanged from unified viewport is already connected via depth manager
        
        # Create scale keyboard controls
        self.scale_keyboard_controls = ScaleKeyboardControls(self, self.zoom_state_manager.scale_converter)
        self.scale_keyboard_controls.scaleAdjusted.connect(self._on_scale_adjusted)
        
        # Set default engineering scales
        # Detailed view: 1:50, Overview: 1:200
        self.zoom_state_manager.set_engineering_scale('1:50')  # Default detailed view
#         print(f"DEBUG (MainWindow): Set default engineering scale: 1:50 for detailed view")
        
        # Set overview scale to 1:200
        # Note: Overview scale is handled separately in stratigraphic_column.py
        # We'll update the stratigraphic column to use engineering scales

        # Create curve visibility manager
        self.curve_visibility_manager = CurveVisibilityManager(self.curvePlotter)
        
        # Create curve visibility toolbar
        self.curve_visibility_toolbar = CurveVisibilityToolbar(self, self.curve_visibility_manager)
        
        # Connect curve visibility changes to unified viewport
        if hasattr(self.curve_visibility_manager, 'visibility_changed'):
            self.curve_visibility_manager.visibility_changed.connect(
                self.unifiedViewport.set_curve_visibility
            )
        
        # Create curve display modes manager
        self.curve_display_modes_manager = create_curve_display_modes()
        
        # Create display mode switcher toolbar
        self.display_mode_switcher = create_display_mode_switcher(self, self.curve_display_modes_manager)
        
        # Connect display mode changes to update curve plotter
        self.display_mode_switcher.displayModeChanged.connect(self._on_display_mode_changed)
        self.curve_display_modes_manager.displayModeChanged.connect(self._on_display_mode_changed)
        
        # Create cross-hole synchronization manager
        self.cross_hole_sync_manager = create_cross_hole_sync_manager(self)
        
        # Connect cross-hole sync signals
        self.cross_hole_sync_manager.curveSelectionSynced.connect(self._on_cross_hole_curve_selection_synced)
        self.cross_hole_sync_manager.curveSettingsSynced.connect(self._on_cross_hole_curve_settings_synced)
        self.cross_hole_sync_manager.syncEnabledChanged.connect(self._on_cross_hole_sync_enabled_changed)
        self.cross_hole_sync_manager.holeRegistered.connect(self._on_hole_registered)
        self.cross_hole_sync_manager.holeUnregistered.connect(self._on_hole_unregistered)
        
        # Initial sync status update
        self.update_sync_status_indicator()
        
        # Create curve export manager
        self.curve_export_manager = create_curve_export_manager(self)
        self.curve_export_manager.exportProgress.connect(self._on_export_progress)
        self.curve_export_manager.exportFinished.connect(self._on_export_finished)
        
        # Create curve analysis manager
        self.curve_analysis_manager = create_curve_analysis_manager(self)
        self.curve_analysis_manager.analysisComplete.connect(self._on_analysis_complete)
        self.curve_analysis_manager.analysisError.connect(self._on_analysis_error)

        # Set bit size for anomaly detection if main_window is available
        if main_window and hasattr(main_window, 'bit_size_mm') and hasattr(self.curvePlotter, 'set_bit_size'):
            self.curvePlotter.set_bit_size(main_window.bit_size_mm)

        # Add loading indicator
        self.loadingProgressBar = QProgressBar()
        self.loadingProgressBar.setVisible(False)
        self.loadingLabel = QLabel("Loading...")
        self.loadingLabel.setVisible(False)

        # Initialize cross-widget sync attributes (same as MainWindow)
        self._cross_widget_sync_in_progress = False
        self._cross_widget_sync_lock_time = 0

        # Connect table row selection to stratigraphic column highlighting
        self.editorTable.rowSelectionChangedSignal.connect(self._on_table_row_selected)

        # Connect PyQtGraph plotter click signal for synchronization
        self.curvePlotter.pointClicked.connect(self._on_plot_point_clicked)

        # Connect plotter view range changes to update overview overlay
        self.curvePlotter.viewRangeChanged.connect(self._on_plot_view_range_changed)

        # Connect boundary drag signal for depth correction (Phase 4)
        self.curvePlotter.boundaryDragged.connect(self._on_boundary_dragged)

        # Connect table data changes to update boundary lines (bidirectional sync)
        self.editorTable.dataChangedSignal.connect(self._on_table_data_changed)

        # Connect icon buttons to their methods
        if self.main_window and hasattr(self.main_window, 'create_manual_interbedding'):
            self.createInterbeddingIconButton.clicked.connect(self.main_window.create_manual_interbedding)
        else:
            # Fallback: connect to a local method that shows a message
            self.createInterbeddingIconButton.clicked.connect(self._create_interbedding_fallback)
        
        self.exportCsvIconButton.clicked.connect(self.export_editor_data_to_csv)

        # Set stratigraphic column to overview mode (showing entire hole)
        self.stratigraphicColumnView.set_overview_mode(True, hole_min_depth=0.0, hole_max_depth=500.0)

        # Set up synchronization between curve plotter and enhanced stratigraphic column
        self._setup_enhanced_column_sync()

        self.setup_ui()
        self.setup_ui_enhancements()

        if file_path:
            pass
            # Load data in background
            self.load_file_background(file_path)

    def setup_ui_enhancements(self):
        """Setup UI enhancements like tooltips, styles, and additional features."""
        # This method is called after setup_ui() to add polish and enhancements
        # For now, just log that it was called
        print("DEBUG (HoleEditorWindow): UI enhancements setup (placeholder)")
        
        # Add any UI enhancements here
        # Example: tooltips, styles, additional widgets, etc.
    
    def setup_ui(self):
        """Create the 4-pane layout with zoom controls: [Plot View | Enhanced Strat Column | Data Table | Overview View]."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Add curve visibility toolbar at the top
        main_layout.addWidget(self.curve_visibility_toolbar)
        
        # Add display mode switcher toolbar
        main_layout.addWidget(self.display_mode_switcher)
        
        # Add loading indicator at the top (hidden by default)
        loading_layout = QHBoxLayout()
        loading_layout.addWidget(self.loadingLabel)
        loading_layout.addWidget(self.loadingProgressBar)
        loading_layout.addStretch()
        main_layout.addLayout(loading_layout)

        # 1. Create the Splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Container: Plot View (PyQtGraph Curves)
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(5)
        
        # Add curve plotter - use all available space
        plot_layout.addWidget(self.curvePlotter)

        # Second Container: Enhanced Stratigraphic Column (detailed, synchronized)
        enhanced_column_container = QWidget()
        enhanced_column_layout = QVBoxLayout(enhanced_column_container)
        enhanced_column_layout.setContentsMargins(0, 0, 0, 0)
        enhanced_column_layout.addWidget(self.enhancedStratColumnView)

        # Third Container: Data Table (Lithology Editor)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        # Add icon buttons for actions
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.createInterbeddingIconButton)
        button_layout.addWidget(self.exportCsvIconButton)
        button_layout.addStretch()

        table_layout.addWidget(self.editorTable)
        table_layout.addLayout(button_layout)

        # Right Container: Overview View (Stratigraphic Column - entire hole)
        overview_container = QWidget()
        overview_container.setObjectName("overview_container")  # Make it findable
        overview_layout = QVBoxLayout(overview_container)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.addWidget(self.stratigraphicColumnView)
        
        # Assign containers to self for pane toggling functionality
        self.plot_container = plot_container
        self.enhanced_column_container = enhanced_column_container
        self.table_container = table_container
        self.overview_container = overview_container

        # Create unified viewport container (replaces plot + enhanced column)
        unified_container = QWidget()
        unified_layout = QVBoxLayout(unified_container)
        unified_layout.setContentsMargins(0, 0, 0, 0)
        unified_layout.setSpacing(5)
        unified_layout.addWidget(self.unifiedViewport)

        # Create a splitter for the first 2 widgets (Unified Viewport | Table)
        # Overview will be a fixed-width sidebar (NO SPLITTER)
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.addWidget(unified_container)
        main_splitter.addWidget(table_container)
        main_splitter.setStretchFactor(0, 4)  # Unified viewport gets more space
        main_splitter.setStretchFactor(1, 3)  # Table gets less space
        
        # FIX: Make overview width proportional to window size instead of fixed
        # Use 5% of window width, with reasonable min/max bounds
        overview_container.setMinimumWidth(40)   # Minimum width for readability
        overview_container.setMaximumWidth(120)  # Maximum width to prevent taking too much space
        
        # Set size policy to allow expansion
        overview_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Connect splitter move event to force overview rescale
        # Use lambda to ensure correct self reference
        main_splitter.splitterMoved.connect(
            lambda pos, index: self._on_splitter_moved(pos, index)
        )
        
#         print(f"DEBUG (MainWindow): Set overview pane to proportional width (5% of window, min 40px, max 120px)")

        # Create container for main content and zoom controls
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout(main_content_widget)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(5)
        
        # Create horizontal layout: [3-widget splitter] + [fixed-width overview sidebar]
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)  # No spacing between splitter and overview
        
        # Add splitter (takes most space)
        horizontal_layout.addWidget(main_splitter)
        
        # Add overview as proportional sidebar (takes 5% of available space)
        horizontal_layout.addWidget(overview_container, 1)  # Stretch factor 1 (splitter gets stretch factor 4)
        
        # Add the horizontal layout to main content
        main_content_layout.addLayout(horizontal_layout)

        main_layout.addWidget(main_content_widget)

        # Initialize empty table
        # Note: setRowCount is not needed for QTableView with PandasModel
        # The model will handle row count automatically
        self.editorTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _setup_enhanced_column_sync(self):
        """Set up synchronization between curve plotter and enhanced stratigraphic column."""
        # Set up zoom state manager
        if hasattr(self, 'zoom_state_manager'):
            self.enhancedStratColumnView.set_zoom_state_manager(self.zoom_state_manager)
            self.curvePlotter.set_zoom_state_manager(self.zoom_state_manager)
            print("DEBUG (main_window): Zoom state manager connected to widgets")
        
        # Connect curve plotter signals to enhanced column
        # Note: viewRangeChanged is already connected at line 199 to _on_plot_view_range_changed
        # which now handles both overview overlay AND enhanced column sync
        # Note: pointClicked is already connected at line 196 to _on_plot_point_clicked
        # which already handles enhanced column scrolling
        
        # Connect enhanced column signals to curve plotter
        self.enhancedStratColumnView.depthScrolled.connect(self._on_enhanced_column_scrolled)
        self.enhancedStratColumnView.syncRequested.connect(self._on_enhanced_sync_requested)
        
        # Connect zoom level changed signals
        if hasattr(self.enhancedStratColumnView, 'zoomLevelChanged'):
            self.enhancedStratColumnView.zoomLevelChanged.connect(self._on_zoom_level_changed)
        
        if hasattr(self.curvePlotter, 'zoomLevelChanged'):
            self.curvePlotter.zoomLevelChanged.connect(self._on_zoom_level_changed)
        
        # Set enhanced column to show detailed view (not overview)
        self.enhancedStratColumnView.set_overview_mode(False)
        
        # Store reference to curve plotter in enhanced column for direct sync
        self.enhancedStratColumnView.sync_curve_plotter = self.curvePlotter
        
        # Set up bidirectional synchronization using the enhanced column's method
        self.enhancedStratColumnView.sync_with_curve_plotter(self.curvePlotter)

    # Note: _on_plot_view_range_changed_for_enhanced removed - functionality merged into _on_plot_view_range_changed

    # Note: _on_plot_point_clicked_for_enhanced removed - functionality merged into _on_plot_point_clicked

    def _on_enhanced_column_scrolled(self, center_depth):
        """Handle enhanced column scrolling to sync curve plotter."""
        # Check cross-widget sync lock to prevent infinite loops
        if not self._should_cross_widget_sync():
            print(f"DEBUG (_on_enhanced_column_scrolled): Cross-widget sync blocked")
            return
            
        self._begin_cross_widget_sync()
        
        try:
            if hasattr(self, 'curvePlotter') and self.enhancedStratColumnView.sync_enabled:
                if hasattr(self, 'zoom_state_manager'):
                    # Get current visible range from enhanced column
                    min_depth, max_depth = self.enhancedStratColumnView.get_visible_depth_range()
                    # Use zoom state manager for synchronization
                    self.zoom_state_manager.sync_from_enhanced_column(center_depth, min_depth, max_depth)
                else:
                    # Fallback to direct sync
                    self.curvePlotter.scroll_to_depth(center_depth)
        finally:
            self._end_cross_widget_sync()

    def _on_enhanced_sync_requested(self):
        """Handle sync request from enhanced column."""
        # Trigger full synchronization
        if hasattr(self, 'curvePlotter') and hasattr(self.curvePlotter, 'get_view_range'):
            x_range, y_range = self.curvePlotter.get_view_range()
            if y_range:
                min_depth, max_depth = y_range
                if hasattr(self, 'zoom_state_manager'):
                    pass
                    # Use zoom state manager for synchronization
                    self.zoom_state_manager.sync_from_curve_plotter(min_depth, max_depth)
                else:
                    # Fallback to direct sync
                    self.enhancedStratColumnView._on_curve_plotter_scrolled(min_depth, max_depth)
                    
    def _on_zoom_level_changed(self, zoom_factor):
        """Handle zoom level changes from either widget."""
#         print(f"DEBUG (main_window): Zoom level changed: {zoom_factor:.2f}")
        # Update any UI elements that show zoom level
        if hasattr(self, 'statusBar'):
            pass
            # Get engineering scale info if available
            scale_text = f"Zoom: {zoom_factor:.1f}x"
            if hasattr(self, 'zoom_state_manager'):
                scale_info = self.zoom_state_manager.get_engineering_scale()
                if scale_info:
                    scale_text = f"Scale: {scale_info.get('display_name', '1:50')} | Zoom: {zoom_factor:.1f}x"
            
            self.statusBar().showMessage(scale_text, 2000)
    
    def _on_engineering_scale_changed(self, scale_label, pixels_per_metre):
        """Handle engineering scale changes."""
        print(f"DEBUG (main_window): Engineering scale changed: {scale_label} ({pixels_per_metre:.1f} px/m)")
        
        # Update status bar
        if hasattr(self, 'statusBar'):
            pass
            # Get current zoom factor if available
            zoom_text = ""
            if hasattr(self, 'zoom_state_manager'):
                zoom_state = self.zoom_state_manager.get_zoom_state()
                zoom_factor = zoom_state.get('zoom_factor', 1.0)
                zoom_text = f" | Zoom: {zoom_factor:.1f}x"
            
            self.statusBar().showMessage(f"Scale: {scale_label}{zoom_text}", 2000)
    
    def _on_display_mode_changed(self, mode_name, mode_info):
        """Handle curve display mode changes."""
#         print(f"DEBUG (main_window): Display mode changed: {mode_name}")
        
        # Update curve plotter with new display mode
        if hasattr(self, 'curvePlotter') and self.curvePlotter:
            pass
            # Use the curve plotter's built-in display mode support
            if hasattr(self.curvePlotter, 'set_display_mode'):
                success = self.curvePlotter.set_display_mode(mode_name)
                if success:
                    print(f"DEBUG (main_window): Curve plotter display mode updated to: {mode_name}")
                else:
                    print(f"DEBUG (main_window): Failed to update curve plotter display mode")
        
        # Update status bar
        if hasattr(self, 'statusBar'):
            display_name = mode_info.get('name', mode_name)
            self.statusBar().showMessage(f"Display mode: {display_name}", 2000)
    
    def _update_curve_config(self, curve_name, key, value):
        """Update a curve configuration and redraw."""
        if not hasattr(self, 'curvePlotter') or not self.curvePlotter:
            pass
#             print(f"DEBUG (main_window): No curve plotter available")
            return False
            
        # Get current curve configurations
        if not hasattr(self.curvePlotter, 'curve_configs'):
            pass
#             print(f"DEBUG (main_window): Curve plotter has no curve_configs")
            return False
            
        # Find and update the curve configuration
        updated = False
        for config in self.curvePlotter.curve_configs:
            if config.get('name') == curve_name:
                config[key] = value
                updated = True
                break
        
        if updated:
            pass
            # Redraw curves with updated configuration
            self.curvePlotter.draw_curves()
            print(f"DEBUG (main_window): Updated curve '{curve_name}' {key} = {value}")
            return True
        else:
            print(f"DEBUG (main_window): Curve '{curve_name}' not found in configurations")
            return False
    
    def _on_curve_color_changed(self, curve_name, color):
        """Handle curve color changes from context menu."""
#         print(f"DEBUG (main_window): Curve color changed: {curve_name} = {color.name()}")
        # Convert QColor to hex string
        hex_color = color.name()
        self._update_curve_config(curve_name, 'color', hex_color)
        
    def _on_curve_thickness_changed(self, curve_name, thickness):
        """Handle curve thickness changes from context menu."""
#         print(f"DEBUG (main_window): Curve thickness changed: {curve_name} = {thickness}")
        self._update_curve_config(curve_name, 'thickness', thickness)
        
    def _on_curve_line_style_changed(self, curve_name, line_style):
        """Handle curve line style changes from context menu."""
        print(f"DEBUG (main_window): Curve line style changed: {curve_name} = {line_style}")
        self._update_curve_config(curve_name, 'line_style', line_style)
        
    def _on_curve_inverted_changed(self, curve_name, inverted):
        """Handle curve inversion changes from context menu."""
#         print(f"DEBUG (main_window): Curve inverted changed: {curve_name} = {inverted}")
        self._update_curve_config(curve_name, 'inverted', inverted)
        
    def _on_curve_visibility_changed(self, curve_name, visible):
        """Handle curve visibility changes from context menu."""
        print(f"DEBUG (main_window): Curve visibility changed: {curve_name} = {visible}")
        # Update curve visibility manager if available
        if hasattr(self, 'curve_visibility_manager'):
            self.curve_visibility_manager.set_curve_visibility(curve_name, visible)
        # Also update curve configuration
        self._update_curve_config(curve_name, 'visible', visible)
    
    def _on_export_curve_settings(self):
        """Handle export curve settings request."""
#         print("DEBUG (main_window): Export curve settings requested")
        # TODO: Implement export functionality
        # This would save current curve configurations to a JSON file
        
    def _on_import_curve_settings(self):
        """Handle import curve settings request."""
        print("DEBUG (main_window): Import curve settings requested")
        # TODO: Implement import functionality
        # This would load curve configurations from a JSON file
    
    def _on_cross_hole_curve_selection_synced(self, curve_names):
        """Handle cross-hole curve selection synchronization."""
#         print(f"DEBUG (main_window): Cross-hole curve selection synced: {len(curve_names)} curves")
        # Update current hole with synced curve selection
        if hasattr(self, 'curvePlotter') and self.curvePlotter:
            pass
            # TODO: Implement curve selection update
            pass
    
    def _on_cross_hole_curve_settings_synced(self, curve_settings):
        """Handle cross-hole curve settings synchronization."""
        print(f"DEBUG (main_window): Cross-hole curve settings synced: {len(curve_settings)} curves")
        # Update current hole with synced curve settings
        if hasattr(self, 'curvePlotter') and self.curvePlotter:
            pass
            # Update each curve configuration
            for curve_name, settings in curve_settings.items():
                for key, value in settings.items():
                    self._update_curve_config(curve_name, key, value)
    
    def _on_cross_hole_sync_enabled_changed(self, enabled):
        """Handle cross-hole sync enabled/disabled changes."""
#         print(f"DEBUG (main_window): Cross-hole sync enabled: {enabled}")
        # Update UI to reflect sync status
        if hasattr(self, 'statusBar'):
            status = "ON" if enabled else "OFF"
            self.statusBar().showMessage(f"Cross-hole sync: {status}", 2000)
        
        # Update sync status indicator
        self.update_sync_status_indicator()
    
    def update_sync_status_indicator(self):
        """Update the sync status indicator in toolbar."""
        if hasattr(self, 'display_mode_switcher') and hasattr(self, 'cross_hole_sync_manager'):
            hole_count = self.cross_hole_sync_manager.get_open_hole_count()
            sync_active = self.cross_hole_sync_manager.is_sync_active()
            self.display_mode_switcher.update_sync_status(sync_active, hole_count)
    
    def _on_sync_settings_requested(self):
        """Handle sync settings request from toolbar."""
        print("DEBUG (main_window): Sync settings requested")
        self.open_sync_settings_dialog()
    
    def open_sync_settings_dialog(self):
        """Open cross-hole sync settings dialog."""
        from .dialogs.sync_settings_dialog import create_sync_settings_dialog
        
        # Get current settings from sync manager
        current_settings = {}
        if hasattr(self, 'cross_hole_sync_manager'):
            current_settings = self.cross_hole_sync_manager.get_settings()
        
        # Create dialog
        dialog = create_sync_settings_dialog(self, current_settings)
        
        # Update dialog status
        hole_count = 0
        sync_active = False
        if hasattr(self, 'cross_hole_sync_manager'):
            hole_count = self.cross_hole_sync_manager.get_open_hole_count()
            sync_active = self.cross_hole_sync_manager.is_sync_active()
        
        dialog.update_status(hole_count, sync_active)
        
        # Connect settings changed signal
        dialog.settingsChanged.connect(self._on_sync_settings_changed)
        
        # Show dialog
        dialog.exec()
    
    def _on_sync_settings_changed(self, settings):
        """Handle sync settings changes from dialog."""
#         print("DEBUG (main_window): Sync settings changed")
        
        # Update sync manager
        if hasattr(self, 'cross_hole_sync_manager'):
            self.cross_hole_sync_manager.set_settings(settings)
            self.cross_hole_sync_manager.save_settings()
            
            # Update sync status
            self.cross_hole_sync_manager.set_sync_enabled(settings.get('sync_enabled', True))
    
    def _on_hole_registered(self, hole_window):
        """Handle hole registration with sync manager."""
        print(f"DEBUG (main_window): Hole registered: {hole_window}")
        self.update_sync_status_indicator()
    
    def _on_hole_unregistered(self, hole_window):
        """Handle hole unregistration from sync manager."""
#         print(f"DEBUG (main_window): Hole unregistered: {hole_window}")
        self.update_sync_status_indicator()
    
    def open_curve_templates_dialog(self):
        """Open curve settings templates dialog."""
        print("DEBUG (main_window): Opening curve templates dialog")
        # TODO: Implement curve templates dialog
        # For now, show a message
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Curve Settings Templates",
            "Curve settings templates feature is available via the Export/Import buttons in the display mode toolbar.\n\n"
            "Full template management dialog will be implemented in a future update."
        )
    
    def _on_export_progress(self, percent, message):
        """Handle export progress updates."""
#         print(f"DEBUG (main_window): Export progress: {percent}% - {message}")
        # TODO: Update UI with progress (progress bar, status message)
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(f"Export: {message}", 1000)
    
    def _on_export_finished(self, success, message):
        """Handle export completion."""
        print(f"DEBUG (main_window): Export finished: success={success}, message={message}")
        
        from PyQt6.QtWidgets import QMessageBox
        
        if success:
            QMessageBox.information(self, "Export Complete", message)
        else:
            QMessageBox.warning(self, "Export Failed", message)
        
        # Clear status message
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
    
    def _on_analysis_complete(self, analysis_type, results):
        """Handle analysis completion."""
#         print(f"DEBUG (main_window): Analysis complete: {analysis_type}")
        print(f"DEBUG (main_window): Results: {results}")
        
        # TODO: Display analysis results in UI
        # For now, just show a message
        from PyQt6.QtWidgets import QMessageBox
        
        if analysis_type == 'statistics':
            curve_count = len(results)
            QMessageBox.information(
                self, 
                "Analysis Complete", 
                f"Statistical analysis complete for {curve_count} curves.\n\n"
                "Results available in console output."
            )
        elif analysis_type == 'correlation':
            QMessageBox.information(
                self,
                "Correlation Analysis",
                "Correlation matrix calculated.\n\n"
                "Results available in console output."
            )
        
        # Clear status message
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
    
    def _on_analysis_error(self, error_message):
        """Handle analysis errors."""
        print(f"DEBUG (main_window): Analysis error: {error_message}")
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Analysis Error", error_message)
        
        # Clear status message
        if hasattr(self, 'statusBar'):
            self.statusBar().clearMessage()
    
    def export_curves_dialog(self):
        """Open dialog to export curves to various formats."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QFileDialog
        
        # Check if we have curve data
        if not hasattr(self, 'curvePlotter') or not self.curvePlotter:
            QMessageBox.warning(self, "No Data", "No curve data available to export")
            return
        
        # Get curve data and configurations
        curve_data = self.curvePlotter.data if hasattr(self.curvePlotter, 'data') else None
        curve_configs = self.curvePlotter.curve_configs if hasattr(self.curvePlotter, 'curve_configs') else []
        
        if curve_data is None or curve_data.empty:
            QMessageBox.warning(self, "No Data", "No curve data available to export")
            return
        
        if not curve_configs:
            QMessageBox.warning(self, "No Curves", "No curve configurations available")
            return
        
        # Create export dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Export Curves")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Export Format:"))
        
        format_combo = QComboBox()
        supported_formats = self.curve_export_manager.get_supported_formats()
        for fmt in supported_formats:
            format_combo.addItem(fmt['name'], fmt['id'])
        format_layout.addWidget(format_combo)
        layout.addLayout(format_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        export_button = QPushButton("Export...")
        cancel_button = QPushButton("Cancel")
        
        export_button.clicked.connect(lambda: self._perform_export(
            dialog, curve_data, curve_configs, format_combo.currentData()
        ))
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(export_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _perform_export(self, dialog, curve_data, curve_configs, format_type):
        """Perform the export operation."""
        from PyQt6.QtWidgets import QFileDialog
        
        # Get file filter for selected format
        supported_formats = self.curve_export_manager.get_supported_formats()
        format_info = next((f for f in supported_formats if f['id'] == format_type), None)
        
        if not format_info:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Unsupported format: {format_type}")
            return
        
        # Get save file path
        file_filter = f"{format_info['name']} ({format_info['extension']})"
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            f"Export Curves as {format_info['name']}",
            "",
            file_filter
        )
        
        if not file_path:
            return  # User cancelled
        
        # Ensure correct file extension
        if not file_path.lower().endswith(format_info['extension'].replace('*.', '')):
            file_path += format_info['extension'].replace('*', '')
        
        # Get default options
        options = self.curve_export_manager.get_default_options(format_type)
        options['version'] = '1.0'  # TODO: Get actual version
        
        # Perform export
        self.curve_export_manager.export_curves(
            curve_data, curve_configs, file_path, format_type, options
        )
        
        dialog.accept()
    
    def curve_analysis_dialog(self):
        """Open dialog for advanced curve analysis tools."""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QComboBox, QPushButton, QGroupBox, QFormLayout,
                                   QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit,
                                   QTabWidget, QWidget, QMessageBox)
        
        # Check if we have curve data
        if not hasattr(self, 'curvePlotter') or not self.curvePlotter:
            QMessageBox.warning(self, "No Data", "No curve data available for analysis")
            return
        
        # Get curve data and configurations
        curve_data = self.curvePlotter.data if hasattr(self.curvePlotter, 'data') else None
        curve_configs = self.curvePlotter.curve_configs if hasattr(self.curvePlotter, 'curve_configs') else []
        
        if curve_data is None or curve_data.empty:
            QMessageBox.warning(self, "No Data", "No curve data available for analysis")
            return
        
        if not curve_configs:
            QMessageBox.warning(self, "No Curves", "No curve configurations available")
            return
        
        # Get curve names
        curve_names = [config.get('name', '') for config in curve_configs if config.get('name')]
        if not curve_names:
            QMessageBox.warning(self, "No Curves", "No valid curve names found")
            return
        
        # Create analysis dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Curve Analysis Tools")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(500)
        
        layout = QVBoxLayout()
        
        # Create tab widget for different analysis types
        tab_widget = QTabWidget()
        
        # Tab 1: Statistical Analysis
        stats_tab = QWidget()
        stats_layout = QVBoxLayout()
        
        # Curve selection
        curve_selection_group = QGroupBox("Curve Selection")
        curve_selection_layout = QFormLayout()
        
        curve_combo = QComboBox()
        curve_combo.addItems(curve_names)
        curve_selection_layout.addRow(QLabel("Select Curve:"), curve_combo)
        
        # Depth range
        depth_range_group = QGroupBox("Depth Range (Optional)")
        depth_range_layout = QFormLayout()
        
        depth_min_spin = QDoubleSpinBox()
        depth_min_spin.setRange(0, 10000)
        depth_min_spin.setDecimals(2)
        depth_min_spin.setSpecialValueText("Auto")
        
        depth_max_spin = QDoubleSpinBox()
        depth_max_spin.setRange(0, 10000)
        depth_max_spin.setDecimals(2)
        depth_max_spin.setSpecialValueText("Auto")
        
        depth_range_layout.addRow(QLabel("Min Depth:"), depth_min_spin)
        depth_range_layout.addRow(QLabel("Max Depth:"), depth_max_spin)
        depth_range_group.setLayout(depth_range_layout)
        
        stats_layout.addWidget(curve_selection_group)
        stats_layout.addWidget(depth_range_group)
        
        # Results display
        results_text = QTextEdit()
        results_text.setReadOnly(True)
        results_text.setPlaceholderText("Analysis results will appear here...")
        stats_layout.addWidget(QLabel("Results:"))
        stats_layout.addWidget(results_text)
        
        # Analyze button
        analyze_button = QPushButton("Analyze Statistics")
        analyze_button.clicked.connect(lambda: self._perform_statistical_analysis(
            dialog, curve_data, curve_names, curve_combo.currentText(),
            depth_min_spin.value(), depth_max_spin.value(), results_text
        ))
        stats_layout.addWidget(analyze_button)
        
        stats_tab.setLayout(stats_layout)
        tab_widget.addTab(stats_tab, "Statistics")
        
        # Tab 2: Filtering
        filter_tab = QWidget()
        filter_layout = QVBoxLayout()
        
        # Filter type selection
        filter_type_group = QGroupBox("Filter Settings")
        filter_type_layout = QFormLayout()
        
        filter_type_combo = QComboBox()
        filter_type_combo.addItems(["Moving Average", "Gaussian", "Median", "Savitzky-Golay"])
        filter_type_layout.addRow(QLabel("Filter Type:"), filter_type_combo)
        
        window_size_spin = QSpinBox()
        window_size_spin.setRange(3, 101)
        window_size_spin.setValue(5)
        window_size_spin.setSingleStep(2)
        filter_type_layout.addRow(QLabel("Window Size:"), window_size_spin)
        
        filter_type_group.setLayout(filter_type_layout)
        filter_layout.addWidget(filter_type_group)
        
        # Apply filter button
        apply_filter_button = QPushButton("Apply Filter")
        apply_filter_button.clicked.connect(lambda: self._apply_curve_filter(
            dialog, curve_data, curve_names, curve_combo.currentText(),
            filter_type_combo.currentText().lower().replace(' ', '_').replace('-', '_'),
            window_size_spin.value()
        ))
        filter_layout.addWidget(apply_filter_button)
        
        filter_tab.setLayout(filter_layout)
        tab_widget.addTab(filter_tab, "Filtering")
        
        # Tab 3: Correlation Analysis
        correlation_tab = QWidget()
        correlation_layout = QVBoxLayout()
        
        # Curve selection for correlation
        correlation_group = QGroupBox("Curve Selection")
        correlation_form = QFormLayout()
        
        x_curve_combo = QComboBox()
        x_curve_combo.addItems(curve_names)
        correlation_form.addRow(QLabel("X-axis Curve:"), x_curve_combo)
        
        y_curve_combo = QComboBox()
        y_curve_combo.addItems(curve_names)
        correlation_form.addRow(QLabel("Y-axis Curve:"), y_curve_combo)
        
        correlation_group.setLayout(correlation_form)
        correlation_layout.addWidget(correlation_group)
        
        # Correlation button
        correlation_button = QPushButton("Calculate Correlation")
        correlation_button.clicked.connect(lambda: self._perform_correlation_analysis(
            dialog, curve_data, x_curve_combo.currentText(), y_curve_combo.currentText()
        ))
        correlation_layout.addWidget(correlation_button)
        
        correlation_tab.setLayout(correlation_layout)
        tab_widget.addTab(correlation_tab, "Correlation")
        
        layout.addWidget(tab_widget)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _perform_statistical_analysis(self, dialog, curve_data, curve_names, selected_curve,
                                     min_depth, max_depth, results_text):
        """Perform statistical analysis on selected curve."""
        if selected_curve not in curve_data.columns:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Error", f"Curve '{selected_curve}' not found in data")
            return
        
        # Prepare depth range
        depth_range = None
        if min_depth > 0 and max_depth > 0 and max_depth > min_depth:
            depth_range = (min_depth, max_depth)
        
        # Perform analysis
        try:
            results = self.curve_analysis_manager.analyze_statistics(
                curve_data, [selected_curve], depth_range
            )
            
            if selected_curve in results:
                stats = results[selected_curve]
                
                # Format results
                result_text = f"Statistical Analysis: {selected_curve}\n"
                result_text += "=" * 50 + "\n\n"
                
                if 'error' in stats:
                    result_text += f"Error: {stats['error']}\n"
                else:
                    result_text += f"Data Points: {stats['count']}\n"
                    result_text += f"Depth Range: {depth_range if depth_range else 'Full dataset'}\n\n"
                    
                    result_text += "Basic Statistics:\n"
                    result_text += f"  Mean: {stats['mean']:.4f}\n"
                    result_text += f"  Median: {stats['median']:.4f}\n"
                    result_text += f"  Min: {stats['min']:.4f}\n"
                    result_text += f"  Max: {stats['max']:.4f}\n"
                    result_text += f"  Range: {stats['range']:.4f}\n"
                    result_text += f"  Std Dev: {stats['std']:.4f}\n"
                    result_text += f"  Variance: {stats['variance']:.4f}\n\n"
                    
                    result_text += "Percentiles:\n"
                    result_text += f"  10th: {stats['percentile_10']:.4f}\n"
                    result_text += f"  25th: {stats['percentile_25']:.4f}\n"
                    result_text += f"  50th: {stats['percentile_50']:.4f}\n"
                    result_text += f"  75th: {stats['percentile_75']:.4f}\n"
                    result_text += f"  90th: {stats['percentile_90']:.4f}\n\n"
                    
                    if stats.get('skewness') is not None:
                        result_text += f"Skewness: {stats['skewness']:.4f}\n"
                    if stats.get('kurtosis') is not None:
                        result_text += f"Kurtosis: {stats['kurtosis']:.4f}\n"
                
                results_text.setPlainText(result_text)
            else:
                results_text.setPlainText(f"No results returned for curve: {selected_curve}")
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Analysis Error", f"Statistical analysis failed: {str(e)}")
    
    def _apply_curve_filter(self, dialog, curve_data, curve_names, selected_curve,
                           filter_type, window_size):
        """Apply filter to selected curve."""
        if selected_curve not in curve_data.columns:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Error", f"Curve '{selected_curve}' not found in data")
            return
        
        try:
            # Apply filter
            filtered_data = self.curve_analysis_manager.apply_filter(
                curve_data[selected_curve],
                filter_type=filter_type,
                window_size=window_size
            )
            
            # Update curve plotter with filtered data
            # TODO: Implement visualization of filtered curve
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                dialog, 
                "Filter Applied", 
                f"{filter_type.replace('_', ' ').title()} filter applied to '{selected_curve}'.\n"
                f"Window size: {window_size}\n\n"
                "Note: Visualization of filtered curves will be implemented in future update."
            )
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Filter Error", f"Filter application failed: {str(e)}")
    
    def _perform_correlation_analysis(self, dialog, curve_data, x_curve, y_curve):
        """Perform correlation analysis between two curves."""
        if x_curve not in curve_data.columns or y_curve not in curve_data.columns:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Error", f"Curves not found: '{x_curve}' or '{y_curve}'")
            return
        
        if x_curve == y_curve:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Error", "Cannot correlate a curve with itself")
            return
        
        try:
            # Calculate correlation
            correlation_matrix = self.curve_analysis_manager.calculate_correlation(
                curve_data, [x_curve, y_curve]
            )
            
            if not correlation_matrix.empty:
                correlation_value = correlation_matrix.loc[x_curve, y_curve]
                
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(
                    dialog,
                    "Correlation Results",
                    f"Correlation between '{x_curve}' and '{y_curve}':\n\n"
                    f"Correlation Coefficient: {correlation_value:.4f}\n\n"
                    f"Interpretation:\n"
                    f"{self._interpret_correlation(correlation_value)}"
                )
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(dialog, "Analysis Error", "Could not calculate correlation")
                
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(dialog, "Analysis Error", f"Correlation analysis failed: {str(e)}")
    
    def _interpret_correlation(self, r_value):
        """Interpret correlation coefficient value."""
        abs_r = abs(r_value)
        
        if abs_r >= 0.9:
            strength = "Very strong"
        elif abs_r >= 0.7:
            strength = "Strong"
        elif abs_r >= 0.5:
            strength = "Moderate"
        elif abs_r >= 0.3:
            strength = "Weak"
        else:
            strength = "Very weak or no"
        
        direction = "positive" if r_value > 0 else "negative" if r_value < 0 else "no"
        
        return f"{strength} {direction} correlation"
    
    def _on_scale_adjusted(self, pixels_per_metre, scale_label):
        """Handle scale adjustment from keyboard controls."""
#         print(f"DEBUG (main_window): Scale adjusted via keyboard: {scale_label} ({pixels_per_metre:.1f} px/m)")
        
        # Update zoom state manager
        if hasattr(self, 'zoom_state_manager'):
            self.zoom_state_manager.set_engineering_scale(scale_label)

    # Note: _on_splitter_moved method is defined later in the file
    # This placeholder was removed to avoid duplicate method definition

    def _on_table_row_selected(self, row):
        """Handle table row selection to highlight stratigraphic column and scroll plot view (Subtask 4.1)."""
        if row == -1:
            pass
            # No selection - clear highlight
            self.stratigraphicColumnView.highlight_unit(None)
            if hasattr(self, 'enhancedStratColumnView'):
                self.enhancedStratColumnView.highlight_unit(None)
        else:
            # Highlight the corresponding unit in both stratigraphic columns
            self.stratigraphicColumnView.highlight_unit(row)
            if hasattr(self, 'enhancedStratColumnView'):
                self.enhancedStratColumnView.highlight_unit(row)

            # Scroll plot view to the selected unit's depth (Subtask 4.1)
            # Get depth information from the table's dataframe
            if hasattr(self, 'editorTable') and self.editorTable is not None:
                dataframe = self.editorTable.current_dataframe
                if dataframe is not None and 'from_depth' in dataframe.columns and 'to_depth' in dataframe.columns:
                    if 0 <= row < len(dataframe):
                        unit = dataframe.iloc[row]
                        center_depth = (unit['from_depth'] + unit['to_depth']) / 2
                        self.curvePlotter.scroll_to_depth(center_depth)

    def _on_plot_point_clicked(self, depth):
        """Handle plot point clicks to select corresponding table row (Subtask 4.2)."""
        if hasattr(self, 'editorTable') and self.editorTable is not None:
            pass
            # Find the row in the table that corresponds to this depth
            dataframe = self.editorTable.current_dataframe
            if dataframe is not None and 'from_depth' in dataframe.columns and 'to_depth' in dataframe.columns:
                pass
                # Find the row where depth is between from_depth and to_depth
                for idx, row in dataframe.iterrows():
                    if row['from_depth'] <= depth <= row['to_depth']:
                        pass
                        # Select the corresponding row in the table
                        self.editorTable.selectRow(idx)
                        # Scroll to make the selected row visible
                        self.editorTable.scrollTo(self.editorTable.model().index(idx, 0))
                        # Highlight the unit in both stratigraphic columns
                        self.stratigraphicColumnView.highlight_unit(idx)
                        if hasattr(self, 'enhancedStratColumnView'):
                            self.enhancedStratColumnView.highlight_unit(idx)
#                         print(f"Plot clicked at depth: {depth}m -> Selected table row {idx}")
                        return

                print(f"Plot clicked at depth: {depth}m -> No matching lithology unit found")
            else:
                pass  # No lithology data available
#                 print(f"Plot clicked at depth: {depth}m -> No lithology data available")

    def _on_plot_view_range_changed(self, min_depth, max_depth):
        """
        Handle plot view range changes for ALL synchronized widgets.
        
        This single handler replaces both:
        1. _on_plot_view_range_changed (overview overlay)
        2. _on_plot_view_range_changed_for_enhanced (enhanced column sync)
        """
        # Check cross-widget sync lock to prevent infinite loops
        if not self._should_cross_widget_sync():
            print(f"DEBUG (_on_plot_view_range_changed): Cross-widget sync blocked")
            return
            
        self._begin_cross_widget_sync()
        
        try:
            # 1. Update overview overlay (static, non-scrollable column)
            self.stratigraphicColumnView.update_zoom_overlay(min_depth, max_depth)
            
            # 2. Sync enhanced column if enabled
            if hasattr(self, 'enhancedStratColumnView') and self.enhancedStratColumnView.sync_enabled:
                # Use zoom state manager for synchronization if available
                if hasattr(self, 'zoom_state_manager'):
                    self.zoom_state_manager.sync_from_curve_plotter(min_depth, max_depth)
                else:
                    # Fallback to direct sync
                    self.enhancedStratColumnView._on_curve_plotter_scrolled(min_depth, max_depth)
        finally:
            self._end_cross_widget_sync()

    def _on_boundary_dragged(self, row_index, boundary_type, new_depth):
        """
        Handle boundary drag events for depth correction (Phase 4).

        Args:
            row_index: Row index in lithology table (0-based)
            boundary_type: 'top' for From_Depth, 'bottom' for To_Depth
            new_depth: New depth value after dragging
        """
        print(f"Boundary dragged: Row {row_index}, {boundary_type} boundary moved to {new_depth:.2f}m")

        # Update the lithology table
        success = self.editorTable.update_depth_value(row_index, boundary_type, new_depth)

        if success:
            pass
#             print(f"✓ Table updated successfully")

            # Update the curve plotter's lithology data to keep in sync
            if hasattr(self.curvePlotter, 'lithology_data') and self.curvePlotter.lithology_data is not None:
                pass
                # Get updated data from table
                updated_data = self.editorTable.current_dataframe
                if updated_data is not None:
                    self.curvePlotter.lithology_data = updated_data.copy()
                    # Update all boundary lines to reflect changes
                    self.curvePlotter.update_all_boundary_lines()

            # Update stratigraphic column if it has lithology data
            if hasattr(self.stratigraphicColumnView, 'set_lithology_data'):
                updated_data = self.editorTable.current_dataframe
                if updated_data is not None:
                    self.stratigraphicColumnView.set_lithology_data(updated_data)
        else:
            print(f"✗ Failed to update table")

    def _on_table_data_changed(self, dataframe):
        """
        Handle table data changes to update boundary lines (bidirectional sync).

        Args:
            dataframe: Updated dataframe from the lithology table
        """
        if dataframe is None:
            return

#         print(f"Table data changed, updating boundary lines...")

        # Update curve plotter's lithology data and boundary lines
        if hasattr(self.curvePlotter, 'set_lithology_data'):
            self.curvePlotter.set_lithology_data(dataframe)
            print(f"✓ Boundary lines updated from table data")

        # Update stratigraphic column if needed
        if hasattr(self.stratigraphicColumnView, 'set_lithology_data'):
            self.stratigraphicColumnView.set_lithology_data(dataframe)

    def apply_synchronized_zoom(self, zoom_factor):
        """Apply zoom factor to both curve plotter and stratigraphic column."""
        self.curvePlotter.set_zoom_level(zoom_factor)
        self.stratigraphicColumnView.set_zoom_level(zoom_factor)

    def load_data(self, dataframe):
        """Load and display data in the editor."""
        self.dataframe = dataframe
        self.populate_editor_table(dataframe)
        # TODO: Update curve plotter and strat column

    def populate_editor_table(self, dataframe):
        """Populate the editor table with dataframe content."""
        # Use the LithologyTableWidget's load_data method which now uses PandasModel
        self.editorTable.load_data(dataframe)
        # Apply column visibility settings if main_window is available
        if self.main_window and hasattr(self.main_window, 'column_visibility'):
            self.main_window.apply_column_visibility(self.main_window.column_visibility)

    def set_window_title(self, title):
        """Set window title for MDI subwindow."""
        if self.parent() and hasattr(self.parent(), 'setWindowTitle'):
            self.parent().setWindowTitle(title)
        else:
            self.setWindowTitle(title)

    def set_file_path(self, file_path):
        """Set the file path for this hole and update window title."""
        self.file_path = file_path
        if file_path:
            filename = os.path.basename(file_path)
            self.set_window_title(filename)

    def load_file_background(self, file_path: str):
        """Load file in background thread using appropriate worker."""
        self.file_path = file_path
        filename = os.path.basename(file_path)
        self.set_window_title(f"Loading {filename}...")

        # Show loading indicator
        self.loadingProgressBar.setVisible(True)
        self.loadingLabel.setVisible(True)
        self.loadingProgressBar.setValue(0)

        # Determine file type and use appropriate worker
        if file_path.lower().endswith('.las'):
            self._load_las_file_background(file_path)
        elif file_path.lower().endswith('.csv') or file_path.lower().endswith('.xlsx'):
            pass
            # For CSV/Excel files, we can load directly since they're usually smaller
            # But we should still do it in background for consistency
            self._load_csv_excel_background(file_path)
        else:
            QMessageBox.warning(self, "Unsupported Format",
                               f"Cannot load {filename}: Unsupported file format.")

    def _load_las_file_background(self, file_path: str):
        """Load LAS file using background worker."""
        # Create worker and thread
        self.las_worker = LASLoaderWorker(file_path)
        self.las_thread = QThread()

        # Move worker to thread
        self.las_worker.moveToThread(self.las_thread)

        # Connect signals
        self.las_thread.started.connect(self.las_worker.run)
        self.las_worker.progress.connect(self._on_file_loading_progress)
        self.las_worker.finished.connect(self._on_las_loading_complete)
        self.las_worker.error.connect(self._on_file_loading_error)

        # Cleanup connections
        self.las_worker.finished.connect(self.las_thread.quit)
        self.las_worker.finished.connect(self.las_worker.deleteLater)
        self.las_thread.finished.connect(self.las_thread.deleteLater)

        # Start thread
        self.las_thread.start()

    def _load_csv_excel_background(self, file_path: str):
        """Load CSV or Excel file in background (simplified version)."""
        # For simplicity, we'll use a QTimer to simulate background loading
        # In a real implementation, we'd use a proper worker thread
        self.loadingProgressBar.setValue(50)
        self.loadingLabel.setText(f"Loading {os.path.basename(file_path)}...")

        # Use QTimer to load in next event loop iteration (non-blocking)
        QTimer.singleShot(100, lambda: self._load_csv_excel_direct(file_path))

    def _load_csv_excel_direct(self, file_path: str):
        """Load CSV or Excel file directly (called from timer)."""
        try:
            if file_path.lower().endswith('.csv'):
                dataframe = pd.read_csv(file_path)
            else:  # .xlsx
                dataframe = pd.read_excel(file_path)

            # Update UI
            self.loadingProgressBar.setValue(100)
            self._on_file_loading_complete(dataframe, {}, file_path)

        except Exception as e:
            self._on_file_loading_error(f"Failed to load file: {str(e)}", file_path)

    def _on_file_loading_progress(self, percent: int, message: str):
        """Handle file loading progress updates."""
        self.loadingProgressBar.setValue(percent)
        self.loadingLabel.setText(message)

    def _on_las_loading_complete(self, dataframe: pd.DataFrame, metadata: dict, file_path: str):
        """Handle successful LAS file loading."""
        self._on_file_loading_complete(dataframe, metadata, file_path)

    def _on_file_loading_complete(self, dataframe: pd.DataFrame, metadata: dict, file_path: str):
        """Handle successful file loading."""
        # Hide loading indicator
        self.loadingProgressBar.setVisible(False)
        self.loadingLabel.setVisible(False)

        # Store data
        self.dataframe = dataframe
        self.file_metadata = metadata

        # Update window title
        filename = os.path.basename(file_path)
        self.set_window_title(filename)

        # Load data into table
        self.editorTable.load_data(dataframe)

        # Apply column visibility settings if main_window is available
        if self.main_window and hasattr(self.main_window, 'column_visibility'):
            self.main_window.apply_column_visibility(self.main_window.column_visibility)

        # TODO: Update curve plotter and stratigraphic column with data
#         print(f"File loaded successfully: {filename} ({len(dataframe)} rows)")

        # Run initial validation in background
        self.editorTable.run_validation()

    def _on_file_loading_error(self, error_msg: str, file_path: str):
        """Handle file loading errors."""
        # Hide loading indicator
        self.loadingProgressBar.setVisible(False)
        self.loadingLabel.setVisible(False)

        # Show error
        filename = os.path.basename(file_path)
        QMessageBox.critical(self, "Error Loading File",
                            f"Failed to load {filename}:\n\n{error_msg}")

        # Reset window title
        self.set_window_title("Untitled Hole")
    
    def force_overview_rescale(self):
        """Force overview column to rescale after window/splitter resize."""
        if hasattr(self, 'stratigraphicColumnView') and self.stratigraphicColumnView:
            print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Forcing overview rescale")
            # Check if overview mode is enabled
            if hasattr(self.stratigraphicColumnView, 'overview_mode') and self.stratigraphicColumnView.overview_mode:
                pass
#                 print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Overview mode is enabled")
                print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Widget size: {self.stratigraphicColumnView.size().width()}x{self.stratigraphicColumnView.size().height()}")
#                 print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Viewport size: {self.stratigraphicColumnView.viewport().size().width()}x{self.stratigraphicColumnView.viewport().size().height()}")
                
                # Check if the widget has a valid size
                if self.stratigraphicColumnView.size().height() <= 0:
                    print(f"WARNING (HoleEditorWindow.force_overview_rescale): Widget has invalid height: {self.stratigraphicColumnView.size().height()}")
                
                # Directly call fitInView with current scene rectangle
                # This is more reliable than creating dummy resize events
                if hasattr(self.stratigraphicColumnView.scene, 'sceneRect'):
                    scene_rect = self.stratigraphicColumnView.scene.sceneRect()
                    if not scene_rect.isEmpty():
                        pass
#                         print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Calling fitInView with scene rect: {scene_rect.width():.1f}x{scene_rect.height():.1f}")
                        print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Viewport: {self.stratigraphicColumnView.viewport().size().width()}x{self.stratigraphicColumnView.viewport().size().height()}")
                        
                        # Calculate what scale should be applied
                        viewport_height = self.stratigraphicColumnView.viewport().size().height()
                        scene_height = scene_rect.height()
                        if scene_height > 0:
                            required_scale = (viewport_height - 4.0) / scene_height  # Minus 4px padding
#                             print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Required scale: {required_scale:.4f} (viewport={viewport_height}px, scene={scene_height:.1f}px)")
                        
                        self.stratigraphicColumnView.fitInView(
                            scene_rect, 
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding
                        )
                    else:
                        print(f"WARNING (HoleEditorWindow.force_overview_rescale): Scene rect is empty!")
                        # Try to trigger a redraw of the column
                        if hasattr(self.stratigraphicColumnView, 'draw_column') and hasattr(self, 'units_dataframe'):
                            pass  # This would require having min/max depth values stored
#                             print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Attempting to redraw column")
                
                # Also ensure the overview column's own resizeEvent is called
                # This handles any internal logic that fitInView might not cover
                from PyQt6.QtGui import QResizeEvent
                from PyQt6.QtCore import QSize
                current_size = self.stratigraphicColumnView.size()
                # Use a slightly different size to ensure event is processed
                dummy_event = QResizeEvent(current_size, QSize(current_size.width(), current_size.height() - 1))
                self.stratigraphicColumnView.resizeEvent(dummy_event)
                
                # Force immediate repaint
                self.stratigraphicColumnView.viewport().update()
                print(f"DEBUG (HoleEditorWindow.force_overview_rescale): Rescale complete")
            else:
                pass  # Overview mode is NOT enabled
#                 print(f"WARNING (HoleEditorWindow.force_overview_rescale): Overview mode is NOT enabled!")
        else:
            print(f"WARNING (HoleEditorWindow.force_overview_rescale): stratigraphicColumnView not found!")

    def toggle_pane_visibility(self, pane_name, visible):
        """Toggle visibility of a specific pane in this hole editor window."""
        # Store references to pane containers for easy access
        pane_containers = {
            "las_curves": self.plot_container,
            "enhanced_stratigraphic": self.enhanced_column_container,
            "data_editor": self.table_container,
            "overview_stratigraphic": self.overview_container
        }
        
        if pane_name in pane_containers:
            container = pane_containers[pane_name]
            if container:
                container.setVisible(visible)
                # Update layout to account for hidden/shown pane
                self.update_layout_for_pane_toggle()
    
    def update_layout_for_pane_toggle(self):
        """Update the layout when panes are toggled to ensure proper spacing."""
        # This method will be called after pane visibility changes
        # to ensure the layout adjusts properly
        if hasattr(self, 'main_splitter'):
            pass
            # Force splitter to update its sizes
            self.main_splitter.update()
            # Update the parent widget
            self.update()
    
    def _create_interbedding_fallback(self):
        """Fallback method when main_window.create_manual_interbedding is not available."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Create Interbedding", 
                               "Interbedding functionality requires connection to main window.\n"
                               "Please use the Create Interbedding button in the main toolbar.")
    
    def export_editor_data_to_csv(self):
        """Export the editor table data to CSV file."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os
        
        if not hasattr(self, 'editorTable') or self.editorTable.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data to export in this editor window.")
            return
        
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv);;All Files (*)")
        
        if file_path:
            try:
                # Get data from the editor table
                df_to_export = self.editorTable.get_dataframe()
                if df_to_export is None or df_to_export.empty:
                    QMessageBox.warning(self, "Export Error", "No data to export.")
                    return
                
                df_to_export.to_csv(file_path, index=False)
                QMessageBox.information(self, "Export Successful", 
                                       f"Data exported to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")
    
    def _should_cross_widget_sync(self):
        """Check if cross-widget synchronization should proceed (HoleEditorWindow version)."""
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        
        if self._cross_widget_sync_in_progress:
            print(f"DEBUG (HoleEditorWindow): Cross-widget sync blocked - already in progress")
            return False
            
        # Check debounce time (50ms same as SyncStateTracker)
        time_since_last = current_time - self._cross_widget_sync_lock_time
        if time_since_last < 50:
            print(f"DEBUG (HoleEditorWindow): Cross-widget sync debouncing - {time_since_last:.1f}ms since last sync")
            return False
            
        return True
        
    def _begin_cross_widget_sync(self):
        """Mark the beginning of cross-widget synchronization (HoleEditorWindow version)."""
        import time
        self._cross_widget_sync_in_progress = True
        self._cross_widget_sync_lock_time = time.time() * 1000
        print(f"DEBUG (HoleEditorWindow): Beginning cross-widget sync")
        
    def _end_cross_widget_sync(self):
        """Mark the end of cross-widget synchronization (HoleEditorWindow version)."""
        self._cross_widget_sync_in_progress = False
        print(f"DEBUG (HoleEditorWindow): Ending cross-widget sync")
    
    def _on_splitter_moved(self, pos, index):
        """Handle splitter movement in HoleEditorWindow (stub method to prevent errors)."""
        # This is a stub method to prevent AttributeError
        # The actual splitter handling is in MainWindow
        pass


class Worker(QObject):
    finished = pyqtSignal(pd.DataFrame, pd.DataFrame)
    error = pyqtSignal(str)

    def __init__(self, file_path, mnemonic_map, lithology_rules, use_researched_defaults, merge_thin_units=False, merge_threshold=0.05, smart_interbedding=False, smart_interbedding_max_sequence_length=10, smart_interbedding_thick_unit_threshold=0.5, use_fallback_classification=False, analysis_method="standard", casing_depth_enabled=False, casing_depth_m=0.0):
        super().__init__()
        self.file_path = file_path
        self.mnemonic_map = mnemonic_map
        self.lithology_rules = lithology_rules
        self.use_researched_defaults = use_researched_defaults
        self.merge_thin_units = merge_thin_units
        self.merge_threshold = merge_threshold
        self.smart_interbedding = smart_interbedding
        self.smart_interbedding_max_sequence_length = smart_interbedding_max_sequence_length
        self.smart_interbedding_thick_unit_threshold = smart_interbedding_thick_unit_threshold
        self.use_fallback_classification = use_fallback_classification
        self.analysis_method = analysis_method
        self.casing_depth_enabled = casing_depth_enabled
        self.casing_depth_m = casing_depth_m

    def run(self):
        try:
            print(f"DEBUG (Worker): run() started with file={self.file_path}")
            print(f"DEBUG (Worker): lithology_rules count={len(self.lithology_rules)}")
            data_processor = DataProcessor()
            analyzer = Analyzer()
            dataframe, _, units = data_processor.load_las_file(self.file_path)

            # Ensure all required curve mnemonics are in the map for preprocessing
            # Add default mappings if not already present in mnemonic_map
            full_mnemonic_map = self.mnemonic_map.copy()
            if 'short_space_density' not in full_mnemonic_map:
                full_mnemonic_map['short_space_density'] = 'DENS' # Common mnemonic for short space density
            if 'long_space_density' not in full_mnemonic_map:
                full_mnemonic_map['long_space_density'] = 'LSD' # Common mnemonic for long space density

            processed_dataframe = data_processor.preprocess_data(dataframe, full_mnemonic_map, units)
            # Use appropriate classification method based on settings
            if self.analysis_method == "simple":
                classified_dataframe = analyzer.classify_rows_simple(processed_dataframe, self.lithology_rules, full_mnemonic_map, self.casing_depth_enabled, self.casing_depth_m)
            else:
                print(f"DEBUG (Worker): Calling classify_rows with use_researched_defaults={self.use_researched_defaults}")
                classified_dataframe = analyzer.classify_rows(processed_dataframe, self.lithology_rules, full_mnemonic_map, self.use_researched_defaults, self.use_fallback_classification, self.casing_depth_enabled, self.casing_depth_m)
            # Debug: print lithology rules being passed
            print(f"DEBUG (Worker): lithology_rules count = {len(self.lithology_rules)}")
            for idx, rule in enumerate(self.lithology_rules):
                print(f"  [{idx}] code={rule.get('code', 'N/A')}, name={rule.get('name', 'N/A')}, background_color={rule.get('background_color', 'MISSING')}, svg_path={rule.get('svg_path', 'MISSING')}")
            units_dataframe = analyzer.group_into_units(classified_dataframe, self.lithology_rules, self.smart_interbedding, self.smart_interbedding_max_sequence_length, self.smart_interbedding_thick_unit_threshold)
            print(f"DEBUG (Worker): units_dataframe columns: {list(units_dataframe.columns)}")
            print(f"DEBUG (Worker): background_color in columns? {'background_color' in units_dataframe.columns}")
            print(f"DEBUG (Worker): svg_path in columns? {'svg_path' in units_dataframe.columns}")
            if not units_dataframe.empty:
                print(f"DEBUG (Worker): First unit background_color: {units_dataframe.iloc[0].get('background_color', 'MISSING')}")
                print(f"DEBUG (Worker): First unit svg_path: {units_dataframe.iloc[0].get('svg_path', 'MISSING')}")
            if self.merge_thin_units:
                units_dataframe = analyzer.merge_thin_units(units_dataframe, self.merge_threshold)
            template_path = os.path.join(os.getcwd(), 'src', 'assets', 'TEMPLATE.xlsx')
            output_path = os.path.join(os.path.dirname(self.file_path), "output_lithology.xlsx")
            def log_progress(message):
                pass  # Log progress
#                 print(f"Worker Log: {message}")
            success = analyzer.save_to_template(classified_dataframe, template_path, output_path, callback=log_progress, units=units_dataframe)
            if not success:
                raise Exception("Failed to save results to Excel template.")
            self.finished.emit(units_dataframe, classified_dataframe)
        except Exception as e:
            full_traceback = traceback.format_exc()
            self.error.emit(f"Analysis failed: {str(e)}\n\nTraceback:\n{full_traceback}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Earthworm Borehole Logger")

        # Load window geometry from settings or use defaults
        self.load_window_geometry()
        self.las_file_path = None
        self.las_metadata = None
        
        # Cross-widget synchronization lock to prevent infinite loops
        # When one widget is syncing, others should wait
        self._cross_widget_sync_in_progress = False
        self._cross_widget_sync_lock_time = 0

    def load_window_geometry(self):
        """Load window size and position from settings or set reasonable defaults based on screen size."""
        from PyQt6.QtGui import QGuiApplication
        from PyQt6.QtCore import QRect

        # Get the primary screen
        screen = QGuiApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            # Set reasonable default size (80% of screen size, but not larger than 1400x900)
            default_width = min(int(screen_width * 0.8), 1400)
            default_height = min(int(screen_height * 0.8), 900)

            # Try to load saved geometry from settings
            app_settings = load_settings()
            saved_geometry = app_settings.get("window_geometry")

            if saved_geometry and isinstance(saved_geometry, dict):
                pass
                # Restore saved geometry if it exists
                x = saved_geometry.get('x', 50)
                y = saved_geometry.get('y', 50)
                width = saved_geometry.get('width', default_width)
                height = saved_geometry.get('height', default_height)
                maximized = saved_geometry.get('maximized', False)

                # Ensure the window fits within the current screen
                if width > screen_width:
                    width = screen_width - 100
                if height > screen_height:
                    height = screen_height - 100
                if x + width > screen_width:
                    x = max(0, screen_width - width - 50)
                if y + height > screen_height:
                    y = max(0, screen_height - height - 50)

                self.setGeometry(x, y, width, height)

                if maximized:
                    self.showMaximized()
            else:
                # DEFAULT TO MAXIMIZED WINDOW
                # Use default geometry but show maximized
                x = (screen_width - default_width) // 2
                y = (screen_height - default_height) // 2
                self.setGeometry(x, y, default_width, default_height)
                self.showMaximized()  # Default to maximized window

        # Set minimum size to prevent the window from becoming unusable
        self.setMinimumSize(800, 600)

        # Load settings on startup
        app_settings = load_settings()
        self.column_visibility = app_settings.get("column_visibility", {})
        self.curve_visibility = app_settings.get("curve_visibility", {})
        self.lithology_rules = app_settings["lithology_rules"]
#         print(f"DEBUG (MainWindow): Loaded {len(self.lithology_rules)} lithology rules from settings")
        for idx, rule in enumerate(self.lithology_rules):
            print(f"  [{idx}] code={rule.get('code', 'N/A')}, background_color={rule.get('background_color', 'MISSING')}, svg_path={rule.get('svg_path', 'MISSING')}")
        self.initial_separator_thickness = app_settings["separator_thickness"]
        self.initial_draw_separators = app_settings["draw_separator_lines"]
        self.initial_curve_inversion_settings = app_settings["curve_inversion_settings"]
        self.initial_curve_thickness = app_settings["curve_thickness"] # Load new setting
        self.use_researched_defaults = app_settings["use_researched_defaults"]
#         print(f"DEBUG (MainWindow.__init__): Loaded use_researched_defaults={self.use_researched_defaults}")
        self.analysis_method = app_settings.get("analysis_method", "standard")  # Load analysis method
        self.merge_thin_units = app_settings.get("merge_thin_units", False)
        self.merge_threshold = app_settings.get("merge_threshold", 0.05)
        self.smart_interbedding = app_settings.get("smart_interbedding", False)
        self.smart_interbedding_max_sequence_length = app_settings.get("smart_interbedding_max_sequence_length", 10)
        self.smart_interbedding_thick_unit_threshold = app_settings.get("smart_interbedding_thick_unit_threshold", 0.5)
        self.use_fallback_classification = app_settings.get("fallback_classification", DEFAULT_FALLBACK_CLASSIFICATION)
        self.bit_size_mm = app_settings.get("bit_size_mm", 150.0)  # Load bit size in millimeters
        self.show_anomaly_highlights = app_settings.get("show_anomaly_highlights", True)  # Load anomaly highlights setting
        self.casing_depth_enabled = app_settings.get("casing_depth_enabled", False)  # Load casing depth masking enabled state
        self.casing_depth_m = app_settings.get("casing_depth_m", 0.0)  # Load casing depth in meters
        self.avg_executable_path = app_settings.get("avg_executable_path", "")  # Load AVG executable path
        self.svg_directory_path = app_settings.get("svg_directory_path", "")  # Load SVG directory path
        self.disable_svg = app_settings.get("disable_svg", False)  # Load SVG disable setting
        self.current_theme = app_settings.get("theme", "light")  # Load theme preference
        self.pane_visibility = app_settings.get("pane_visibility", {  # Load pane visibility settings
            "file_explorer": True,
            "las_curves": True,
            "enhanced_stratigraphic": True,
            "data_editor": True,
            "overview_stratigraphic": True
        })
        
        # Phase 4: UI Enhancements
        # Initialize 1Point-style context menus
        self.context_menus = OnePointContextMenus(self)
        
        # Connect context menu signals for curve customization
        # Connect context menu signals with error handling
        try:
            self.context_menus.curveColorChanged.connect(self._on_curve_color_changed)
            self.context_menus.curveThicknessChanged.connect(self._on_curve_thickness_changed)
            self.context_menus.curveLineStyleChanged.connect(self._on_curve_line_style_changed)
            self.context_menus.curveInvertedChanged.connect(self._on_curve_inverted_changed)
            self.context_menus.curveVisibilityChanged.connect(self._on_curve_visibility_changed)
        except AttributeError as e:
            print(f"DEBUG (main_window): Context menu signal connection failed: {e}")
#             print("DEBUG (main_window): This may happen during testing")
        
        # Connect display mode switcher signals
        if hasattr(self, 'display_mode_switcher'):
            self.display_mode_switcher.exportCurveSettingsRequested.connect(self._on_export_curve_settings)
            self.display_mode_switcher.importCurveSettingsRequested.connect(self._on_import_curve_settings)
            self.display_mode_switcher.syncSettingsRequested.connect(self._on_sync_settings_requested)
        
        # Initialize enhanced status bar
        self.status_bar_enhancer = StatusBarEnhancer(self.statusBar(), self)
        
        # Load UI enhancement settings
        self.ui_enhancement_settings = app_settings.get("ui_enhancements", {
            'context_menus_enabled': True,
            'engineering_scale_enabled': True,
            'mouse_coordinates_enabled': True,
            'distance_display_enabled': True,
            'keyboard_shortcuts_enabled': True,
            'workspace_management_enabled': True
        })

        self.lithology_qualifier_map = self.load_lithology_qualifier_map()
        self.coallog_data = self.load_coallog_data()

        # Store most recent analysis results for reporting
        self.last_classified_dataframe = None
        self.last_units_dataframe = None
        self.last_analysis_file = None
        self.last_analysis_timestamp = None

        # Initialize range analyzer and visualizer
        self.range_analyzer = RangeAnalyzer()
        self.range_visualizer = EnhancedRangeGapVisualizer()
        self.range_visualizer.set_range_analyzer(self.range_analyzer)

        # Initialize debouncing timer for gap visualization updates
        self.gap_update_timer = QTimer(self)
        self.gap_update_timer.setSingleShot(True)
        self.gap_update_timer.timeout.connect(self._perform_gap_visualization_update)

        # Settings dirty flag for safety workflow (Phase 5 Task 5.2)
        self.settings_dirty = False

        # Layout presets system
        self.layout_manager = LayoutManager()
        self.layout_toolbar = None  # Will be created in create_toolbar()

        # MDI area will replace tab widget (1PD UI/UX Phase 1)
        # Create central widget with vertical layout: control panel at top, MDI area below
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Control panel (load LAS, curve selection, run analysis)
        self.control_panel_layout = QHBoxLayout()
        self.loadLasButton = QPushButton("Load LAS File")
        self.control_panel_layout.addWidget(self.loadLasButton)
        self.control_panel_layout.addWidget(QLabel("Gamma Ray Curve:"))
        self.gammaRayComboBox = QComboBox()
        self.control_panel_layout.addWidget(self.gammaRayComboBox)

        # Add density curves (Short Space Density maps to both density fields)
        self.control_panel_layout.addWidget(QLabel("Short Space Density:"))
        self.shortSpaceDensityComboBox = QComboBox()
        self.control_panel_layout.addWidget(self.shortSpaceDensityComboBox)
        # Hidden combo box for backward compatibility with density field mapping
        self.densityComboBox = QComboBox()
        self.control_panel_layout.addWidget(QLabel("Long Space Density:"))
        self.longSpaceDensityComboBox = QComboBox()
        self.control_panel_layout.addWidget(self.longSpaceDensityComboBox)

        self.control_panel_layout.addWidget(QLabel("Caliper Curve:"))
        self.caliperComboBox = QComboBox()
        self.control_panel_layout.addWidget(self.caliperComboBox)

        self.control_panel_layout.addWidget(QLabel("Resistivity Curve:"))
        self.resistivityComboBox = QComboBox()
        self.control_panel_layout.addWidget(self.resistivityComboBox)

        self.runAnalysisButton = QPushButton("Run Analysis")
        self.control_panel_layout.addWidget(self.runAnalysisButton)

        # Settings button to open settings dialog (replaces Settings tab)
        self.settingsButton = QPushButton("Settings")
        self.control_panel_layout.addWidget(self.settingsButton)

        main_layout.addLayout(self.control_panel_layout)

        # Tab widget for Settings and Editor (Editor will be the default)
        # Note: Settings tab will be created but not added to tab widget
        # It will be used in a dialog instead
        # MDI area for multiple hole windows (1PD UI/UX Phase 1)
        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)
        # Settings dock has been removed per user request - only SettingsDialog remains

        # Create dock widget for holes list (Phase 1, Task 2)
        self.holes_dock = QDockWidget("Project Explorer", self)
        self.holes_tree = QTreeView()
        self.holes_model = QFileSystemModel()
        self.holes_model.setRootPath(os.getcwd())  # Start at current directory
        self.holes_model.setNameFilters(["*.csv", "*.xlsx", "*.las", "*.LAS"])
        self.holes_model.setNameFilterDisables(False)
        self.holes_tree.setModel(self.holes_model)
        self.holes_tree.setRootIndex(self.holes_model.index(os.getcwd()))  # Show current directory initially
        self.holes_tree.doubleClicked.connect(self.on_hole_double_clicked)
        # Connect selection changed signal for map synchronization
        self.holes_tree.selectionModel().selectionChanged.connect(self.on_holes_tree_selection_changed)
        self.holes_dock.setWidget(self.holes_tree)
        self.holes_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.holes_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                       QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                       QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.holes_dock)
        self.holes_dock.show()  # Show by default

        # Create first hole editor window
        self.editor_hole = HoleEditorWindow(coallog_data=self.coallog_data, main_window=self)
        self.editor_tab = self.editor_hole  # Backward compatibility

        # Create editor subwindow for the first hole
        self.editor_subwindow = QMdiSubWindow()
        self.editor_subwindow.setWidget(self.editor_hole)
        self.editor_subwindow.setWindowTitle("Editor")
        self.mdi_area.addSubWindow(self.editor_subwindow)

        # Keep references to widgets for backward compatibility with existing methods
        self.curvePlotter = self.editor_hole.curvePlotter
        self.stratigraphicColumnView = self.editor_hole.stratigraphicColumnView
        self.enhancedStratColumnView = self.editor_hole.enhancedStratColumnView
        self.editorTable = self.editor_hole.editorTable
        self.exportCsvButton = self.editor_hole.exportCsvIconButton  # Renamed to exportCsvIconButton
        self.createInterbeddingIconButton = self.editor_hole.createInterbeddingIconButton
        self.exportCsvIconButton = self.editor_hole.exportCsvIconButton
        self.curve_visibility_manager = self.editor_hole.curve_visibility_manager
        self.curve_visibility_toolbar = self.editor_hole.curve_visibility_toolbar

        # Connect table row selection to stratigraphic column highlighting
        self.editorTable.rowSelectionChangedSignal.connect(self._on_table_row_selected)

        main_layout.addWidget(self.mdi_area)

        self.connect_signals()
        self.load_default_lithology_rules()
        # self.setup_settings_tab()  # Settings dock removed per user request
        # self.setup_editor_tab()  # Not needed: hole editor has its own layout
        # self.tab_widget.currentChanged.connect(self.on_tab_changed)  # MDI removes tabs
        self._synchronize_views()
        self.create_file_menu()
        self.create_tools_menu()
        self.create_window_menu()
        self.create_view_menu()
        self.create_help_menu()
        self.create_toolbar()

    def _should_cross_widget_sync(self):
        """Check if cross-widget synchronization should proceed."""
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        
        if self._cross_widget_sync_in_progress:
            print(f"DEBUG (MainWindow): Cross-widget sync blocked - already in progress")
            return False
            
        # Check debounce time (50ms same as SyncStateTracker)
        time_since_last = current_time - self._cross_widget_sync_lock_time
        if time_since_last < 50:
            print(f"DEBUG (MainWindow): Cross-widget sync debouncing - {time_since_last:.1f}ms since last sync")
            return False
            
        return True
        
    def _begin_cross_widget_sync(self):
        """Mark the beginning of cross-widget synchronization."""
        import time
        self._cross_widget_sync_in_progress = True
        self._cross_widget_sync_lock_time = time.time() * 1000
        print(f"DEBUG (MainWindow): Beginning cross-widget sync")
        
    def _end_cross_widget_sync(self):
        """Mark the end of cross-widget synchronization."""
        self._cross_widget_sync_in_progress = False
        print(f"DEBUG (MainWindow): Ending cross-widget sync")

    def create_file_menu(self):
        """Create File menu with session management and file operations."""
        file_menu = self.menuBar().addMenu("&File")

        # New from template action
        new_from_template_action = QAction("New from Template...", self)
        new_from_template_action.triggered.connect(self.open_template_dialog)
        new_from_template_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_from_template_action)

        file_menu.addSeparator()

        # Session management actions
        session_management_action = QAction("Session Management...", self)
        session_management_action.triggered.connect(self.open_session_dialog)
        session_management_action.setShortcut("Ctrl+S")
        file_menu.addAction(session_management_action)

        file_menu.addSeparator()

        # Load LAS file action (existing functionality)
        load_las_action = QAction("Load LAS File...", self)
        load_las_action.triggered.connect(self.load_las_file_dialog)
        load_las_action.setShortcut("Ctrl+O")
        file_menu.addAction(load_las_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)

    def create_tools_menu(self):
        """Create Tools menu with settings and utilities."""
        tools_menu = self.menuBar().addMenu("&Tools")
        
        # Settings submenu
        settings_menu = tools_menu.addMenu("Settings")
        
        # LAS Settings submenu
        las_settings_menu = settings_menu.addMenu("LAS")
        
        # Sync LAS Curves action
        sync_las_curves_action = QAction("Sync LAS Curves...", self)
        sync_las_curves_action.triggered.connect(self.open_sync_settings_dialog)
        sync_las_curves_action.setToolTip("Configure cross-hole curve synchronization settings")
        las_settings_menu.addAction(sync_las_curves_action)
        
        # Add separator
        tools_menu.addSeparator()
        
        # Curve Settings Templates action
        curve_templates_action = QAction("Curve Settings Templates...", self)
        curve_templates_action.triggered.connect(self.open_curve_templates_dialog)
        curve_templates_action.setToolTip("Manage curve settings templates")
        tools_menu.addAction(curve_templates_action)
        
        # Add separator
        tools_menu.addSeparator()
        
        # Export Curves action
        export_curves_action = QAction("Export Curves...", self)
        export_curves_action.triggered.connect(self.export_curves_dialog)
        export_curves_action.setToolTip("Export curves to various formats (CSV, Excel, etc.)")
        export_curves_action.setShortcut("Ctrl+E")
        tools_menu.addAction(export_curves_action)
        
        # Add separator
        tools_menu.addSeparator()
        
        # Curve Analysis action
        curve_analysis_action = QAction("Curve Analysis...", self)
        curve_analysis_action.triggered.connect(self.curve_analysis_dialog)
        curve_analysis_action.setToolTip("Advanced curve analysis tools (statistics, filtering, etc.)")
        curve_analysis_action.setShortcut("Ctrl+A")
        tools_menu.addAction(curve_analysis_action)

    def create_window_menu(self):
        """Create Window menu with tile, cascade, close actions."""
        window_menu = self.menuBar().addMenu("&Window")

        # New window actions
        new_map_action = QAction("New Map Window", self)
        new_map_action.triggered.connect(self.open_map_window)
        window_menu.addAction(new_map_action)

        new_cross_section_action = QAction("New Cross-Section Window", self)
        new_cross_section_action.triggered.connect(self.open_cross_section_window)
        window_menu.addAction(new_cross_section_action)

        window_menu.addSeparator()

        # Window arrangement actions
        tile_action = QAction("Tile", self)
        tile_action.triggered.connect(self.mdi_area.tileSubWindows)
        window_menu.addAction(tile_action)

        cascade_action = QAction("Cascade", self)
        cascade_action.triggered.connect(self.mdi_area.cascadeSubWindows)
        window_menu.addAction(cascade_action)

        window_menu.addSeparator()

        close_all_action = QAction("Close All", self)
        close_all_action.triggered.connect(self.mdi_area.closeAllSubWindows)
        window_menu.addAction(close_all_action)

    def create_view_menu(self):
        """Create View menu with view options."""
        view_menu = self.menuBar().addMenu("&View")

        # Layout presets submenu
        layout_menu = view_menu.addMenu("&Layout Presets")
        
        # Add built-in presets
        presets = OnePointLayoutPresets.get_all_presets()
        for key, preset in presets.items():
            action = QAction(preset.name, self)
            action.setToolTip(preset.description)
            shortcut = preset.metadata.get('keyboard_shortcut', '')
            if shortcut:
                action.setShortcut(shortcut)
            action.triggered.connect(
                lambda checked, p=preset.name: self._on_layout_preset_selected(p)
            )
            layout_menu.addAction(action)
        
        # Add separator
        layout_menu.addSeparator()
        
        # Add custom layouts if any
        custom_layouts = self.layout_manager.custom_layouts
        if custom_layouts:
            custom_menu = layout_menu.addMenu("Custom Layouts")
            for name in sorted(custom_layouts.keys()):
                action = QAction(name, self)
                action.triggered.connect(
                    lambda checked, n=name: self._on_layout_preset_selected(n)
                )
                custom_menu.addAction(action)
        
        # Add separator
        layout_menu.addSeparator()
        
        # Save current layout
        save_layout_action = QAction("Save Current Layout...", self)
        save_layout_action.triggered.connect(self._on_save_custom_layout)
        layout_menu.addAction(save_layout_action)
        
        # Manage layouts
        manage_layouts_action = QAction("Manage Custom Layouts...", self)
        manage_layouts_action.triggered.connect(self._on_manage_layouts)
        layout_menu.addAction(manage_layouts_action)

        # Add separator
        view_menu.addSeparator()

        # Show/Hide docks
        show_settings_action = QAction("Advanced Settings", self)
        show_settings_action.triggered.connect(self.open_advanced_settings_dialog)
        view_menu.addAction(show_settings_action)

        show_explorer_action = QAction("Show/Hide Project Explorer", self)
        show_explorer_action.triggered.connect(self.toggle_project_explorer)
        view_menu.addAction(show_explorer_action)

    def set_theme(self, theme_name):
        """Set theme (only light theme supported)."""
        # Only light theme is supported
        self.current_theme = "light"

        # Update application property for CSS class (empty string for default light theme)
        app = QApplication.instance()
        if app:
            app.setProperty("class", "")

        # Save theme preference
        self.save_theme_preference()

        # No need to update menu check states (theme menu removed)
        # No notification since theme is fixed

    def show_theme_preview(self):
        """Show theme preview dialog."""
        from .dialogs.theme_preview_dialog import ThemePreviewDialog

        dialog = ThemePreviewDialog(self, self.current_theme)
        dialog.themeChanged.connect(self.set_theme)
        dialog.exec()

    def update_theme_menu_states(self):
        """Update theme menu item check states."""
        # This would update menu check states if we had references to them
        # For now, we'll just print a message
        print(f"Theme updated to {self.current_theme}")

    def toggle_project_explorer(self):
        """Toggle visibility of project explorer dock."""
        if self.holes_dock.isVisible():
            self.holes_dock.hide()
        else:
            self.holes_dock.show()
            self.holes_dock.raise_()

    def create_help_menu(self):
        """Create Help menu with user guide and about information."""
        help_menu = self.menuBar().addMenu("&Help")

        # User Guide action
        user_guide_action = QAction("User Guide", self)
        user_guide_action.triggered.connect(self.open_user_guide)
        user_guide_action.setShortcut("F1")
        help_menu.addAction(user_guide_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction("About Earthworm", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def open_user_guide(self):
        """Open the user guide in a dialog within the application."""
        import os
        
        # Get the path to the user guide
        user_guide_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "User_Guide.md")
        
        if os.path.exists(user_guide_path):
            try:
                # Create and show the user guide dialog
                dialog = UserGuideDialog(user_guide_path, self)
                dialog.exec()
            except Exception as e:
                QMessageBox.warning(self, "Error", 
                    f"Could not open user guide: {str(e)}\n\n"
                    f"Manual location: {user_guide_path}")
        else:
            QMessageBox.warning(self, "User Guide Not Found", 
                f"User guide file not found at: {user_guide_path}\n\n"
                "Please check the documentation directory.")

    def show_about_dialog(self):
        """Show about dialog with application information."""
        about_text = """
        <h2>Earthworm Borehole Logger</h2>
        <p><b>Version:</b> 1.0</p>
        <p><b>Description:</b> Professional geological software for processing, 
        analyzing, and visualizing borehole data.</p>
        
        <h3>Features:</h3>
        <ul>
            <li>Multi-format support (LAS, CSV, Excel)</li>
            <li>Automated lithology classification</li>
            <li>Interactive stratigraphic visualization</li>
            <li>Advanced analysis tools</li>
            <li>Project session management</li>
        </ul>
        
        <h3>System Requirements:</h3>
        <ul>
            <li>Python 3.8 or higher</li>
            <li>8GB RAM minimum (16GB recommended)</li>
            <li>500MB disk space</li>
        </ul>
        
        <p><b>GitHub Repository:</b> https://github.com/lukemoltbot/Earthworm_openclaw</p>
        <p><b>Documentation:</b> See Help → User Guide</p>
        
        <p style="margin-top: 20px;"><i>© 2024 Earthworm Development Team</i></p>
        """
        
        QMessageBox.about(self, "About Earthworm", about_text)

    def create_toolbar(self):
        """Create main toolbar with common actions and dedicated icon area."""
        # Create main toolbar
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(True)
        self.addToolBar(toolbar)

        # Add common actions
        load_action = QAction(get_open_icon(), "Load LAS File", self)
        load_action.setToolTip("Load LAS File")
        load_action.triggered.connect(self.load_las_file_dialog)
        toolbar.addAction(load_action)

        # Add separator
        toolbar.addSeparator()

        # Create layout toolbar
        self._create_layout_toolbar()

        # Add separator
        toolbar.addSeparator()

        # Create pane toggle toolbar section
        self.create_pane_toggle_toolbar(toolbar)

        # Add separator
        toolbar.addSeparator()

        # Create dedicated icon area container
        icon_area_widget = QWidget()
        icon_area_layout = QHBoxLayout(icon_area_widget)
        icon_area_layout.setContentsMargins(5, 0, 5, 0)
        icon_area_layout.setSpacing(5)

        # Settings icon button
        settings_icon_button = QToolButton()
        settings_icon_button.setIcon(get_settings_icon())
        settings_icon_button.setToolTip("Settings")
        settings_icon_button.clicked.connect(self.open_advanced_settings_dialog)
        settings_icon_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        icon_area_layout.addWidget(settings_icon_button)

        # Add separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        separator1.setStyleSheet("color: #cccccc;")
        icon_area_layout.addWidget(separator1)

        # Create Interbedding icon button
        create_interbedding_icon_button = QToolButton()
        create_interbedding_icon_button.setIcon(get_add_icon())
        create_interbedding_icon_button.setToolTip("Create Interbedding")
        create_interbedding_icon_button.clicked.connect(self.create_manual_interbedding)
        create_interbedding_icon_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        icon_area_layout.addWidget(create_interbedding_icon_button)

        # Export CSV icon button
        export_csv_icon_button = QToolButton()
        export_csv_icon_button.setIcon(get_save_icon())
        export_csv_icon_button.setToolTip("Export to CSV")
        export_csv_icon_button.clicked.connect(self.export_editor_data_to_csv)
        export_csv_icon_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        icon_area_layout.addWidget(export_csv_icon_button)

        # Add the icon area widget to the toolbar
        toolbar.addWidget(icon_area_widget)

        # Store references for potential updates
        self.settings_icon_button = settings_icon_button
        self.create_interbedding_icon_button = create_interbedding_icon_button
        self.export_csv_icon_button = export_csv_icon_button
    
    def _create_layout_toolbar(self):
        """Create and add layout toolbar."""
        self.layout_toolbar = LayoutToolbar(self, self.layout_manager)
        self.layout_toolbar.presetSelected.connect(self._on_layout_preset_selected)
        self.layout_toolbar.saveCustomLayout.connect(self._on_save_custom_layout)
        self.layout_toolbar.manageLayouts.connect(self._on_manage_layouts)
        
        # Add layout toolbar to main window
        self.addToolBar(self.layout_toolbar)

    def create_pane_toggle_toolbar(self, parent_toolbar):
        """Create pane toggle buttons in the toolbar."""
        # Create container for pane toggle buttons
        pane_toggle_widget = QWidget()
        pane_toggle_layout = QHBoxLayout(pane_toggle_widget)
        pane_toggle_layout.setContentsMargins(5, 0, 5, 0)
        pane_toggle_layout.setSpacing(5)

        # Create pane toggle buttons
        self.pane_toggle_buttons = {}
        
        # File Explorer Pane Toggle
        file_explorer_button = QToolButton()
        file_explorer_button.setIcon(get_folder_icon())
        file_explorer_button.setToolTip("Toggle File Explorer Pane")
        file_explorer_button.setCheckable(True)
        file_explorer_button.setChecked(self.pane_visibility.get("file_explorer", True))
        file_explorer_button.clicked.connect(lambda checked: self.toggle_pane_visibility("file_explorer", checked))
        file_explorer_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        pane_toggle_layout.addWidget(file_explorer_button)
        self.pane_toggle_buttons["file_explorer"] = file_explorer_button

        # LAS Curves Pane Toggle
        las_curves_button = QToolButton()
        las_curves_button.setIcon(get_chart_icon())
        las_curves_button.setToolTip("Toggle LAS Curves Pane")
        las_curves_button.setCheckable(True)
        las_curves_button.setChecked(self.pane_visibility.get("las_curves", True))
        las_curves_button.clicked.connect(lambda checked: self.toggle_pane_visibility("las_curves", checked))
        las_curves_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        pane_toggle_layout.addWidget(las_curves_button)
        self.pane_toggle_buttons["las_curves"] = las_curves_button

        # Enhanced Stratigraphic Pane Toggle
        enhanced_strat_button = QToolButton()
        enhanced_strat_button.setIcon(get_layers_icon())
        enhanced_strat_button.setToolTip("Toggle Enhanced Stratigraphic Pane")
        enhanced_strat_button.setCheckable(True)
        enhanced_strat_button.setChecked(self.pane_visibility.get("enhanced_stratigraphic", True))
        enhanced_strat_button.clicked.connect(lambda checked: self.toggle_pane_visibility("enhanced_stratigraphic", checked))
        enhanced_strat_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        pane_toggle_layout.addWidget(enhanced_strat_button)
        self.pane_toggle_buttons["enhanced_stratigraphic"] = enhanced_strat_button

        # Data Editor Pane Toggle
        data_editor_button = QToolButton()
        data_editor_button.setIcon(get_table_icon())
        data_editor_button.setToolTip("Toggle Data Editor Pane")
        data_editor_button.setCheckable(True)
        data_editor_button.setChecked(self.pane_visibility.get("data_editor", True))
        data_editor_button.clicked.connect(lambda checked: self.toggle_pane_visibility("data_editor", checked))
        data_editor_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        pane_toggle_layout.addWidget(data_editor_button)
        self.pane_toggle_buttons["data_editor"] = data_editor_button

        # Overview Stratigraphic Pane Toggle
        overview_strat_button = QToolButton()
        overview_strat_button.setIcon(get_overview_icon())
        overview_strat_button.setToolTip("Toggle Overview Stratigraphic Pane")
        overview_strat_button.setCheckable(True)
        overview_strat_button.setChecked(self.pane_visibility.get("overview_stratigraphic", True))
        overview_strat_button.clicked.connect(lambda checked: self.toggle_pane_visibility("overview_stratigraphic", checked))
        overview_strat_button.setStyleSheet("QToolButton { padding: 5px; border: none; }")
        pane_toggle_layout.addWidget(overview_strat_button)
        self.pane_toggle_buttons["overview_stratigraphic"] = overview_strat_button

        # Add pane toggle widget to parent toolbar
        parent_toolbar.addWidget(pane_toggle_widget)

    def toggle_pane_visibility(self, pane_name, visible):
        """Toggle visibility of a specific pane."""
        # Update pane visibility setting
        self.pane_visibility[pane_name] = visible
        
        # Apply visibility to all open hole editor windows
        for subwindow in self.mdi_area.subWindowList():
            widget = subwindow.widget()
            if isinstance(widget, HoleEditorWindow):
                widget.toggle_pane_visibility(pane_name, visible)
        
        # Apply visibility to main window components
        if pane_name == "file_explorer":
            if visible:
                self.holes_dock.show()
            else:
                self.holes_dock.hide()
        
        # Save settings
        self.update_settings(auto_save=True)
    
    def _on_layout_preset_selected(self, preset_name: str):
        """Handle layout preset selection from toolbar."""
#         print(f"Layout preset selected: {preset_name}")
        
        # Get the active hole editor window
        active_window = self._get_active_hole_editor()
        if not active_window:
            QMessageBox.warning(self, "No Active Window", "Please open a hole editor window first.")
            return
        
        # Get the preset
        preset = OnePointLayoutPresets.get_preset_by_name(preset_name)
        if not preset:
            pass
            # Check if it's a custom layout
            preset = self.layout_manager.get_custom_layout(preset_name)
        
        if preset:
            pass
            # Apply the preset
            success = self.layout_manager.apply_preset(preset, active_window)
            if success:
                print(f"Applied layout preset: {preset_name}")
            else:
                QMessageBox.warning(self, "Apply Failed", f"Failed to apply layout preset: {preset_name}")
        else:
            QMessageBox.warning(self, "Preset Not Found", f"Layout preset not found: {preset_name}")
    
    def _on_save_custom_layout(self):
        """Handle save custom layout request."""
#         print("Save custom layout requested")
        
        # Get the active hole editor window
        active_window = self._get_active_hole_editor()
        if not active_window:
            QMessageBox.warning(self, "No Active Window", "Please open a hole editor window first.")
            return
        
        # Get existing layout names
        existing_layouts = list(self.layout_manager.custom_layouts.keys())
        
        # Show save dialog
        dialog = SaveLayoutDialog(self, existing_layouts)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            layout_name = dialog.get_layout_name()
            layout_description = dialog.get_layout_description()
            options = dialog.get_options()
            
            # Save the layout
            success = self.layout_manager.save_custom_layout(
                layout_name, layout_description, active_window
            )
            
            if success:
                pass
                # Update toolbar menu
                if self.layout_toolbar:
                    self.layout_toolbar.update_custom_layouts_menu()
                
                QMessageBox.information(
                    self, "Layout Saved", 
                    f"Custom layout '{layout_name}' saved successfully."
                )
            else:
                QMessageBox.warning(
                    self, "Save Failed", 
                    f"Failed to save custom layout '{layout_name}'."
                )
    
    def _on_manage_layouts(self):
        """Handle manage layouts request."""
        print("Manage layouts requested")
        
        # Show layout manager dialog
        dialog = LayoutManagerDialog(self, self.layout_manager)
        dialog.layoutRenamed.connect(self._on_layout_renamed)
        dialog.layoutDeleted.connect(self._on_layout_deleted)
        dialog.layoutApplied.connect(self._on_layout_preset_selected)
        
        dialog.exec()
    
    def _on_layout_renamed(self, old_name: str, new_name: str):
        """Handle layout renamed event."""
#         print(f"Layout renamed: {old_name} -> {new_name}")
        
        # Update toolbar menu
        if self.layout_toolbar:
            self.layout_toolbar.update_custom_layouts_menu()
    
    def _on_layout_deleted(self, layout_name: str):
        """Handle layout deleted event."""
        print(f"Layout deleted: {layout_name}")
        
        # Update toolbar menu
        if self.layout_toolbar:
            self.layout_toolbar.update_custom_layouts_menu()
    
    def _get_active_hole_editor(self):
        """Get the currently active hole editor window."""
        active_subwindow = self.mdi_area.activeSubWindow()
        if active_subwindow:
            widget = active_subwindow.widget()
            if isinstance(widget, HoleEditorWindow):
                return widget
        return None

    def _synchronize_views(self):
        """Connects the two views to scroll in sync with perfect 1:1 depth alignment."""
        self._is_syncing = False # A flag to prevent recursive sync

        # Check if both views have verticalScrollBar method (required for synchronization)
        has_curve_scrollbar = hasattr(self.curvePlotter, 'verticalScrollBar')
        has_strat_scrollbar = hasattr(self.stratigraphicColumnView, 'verticalScrollBar')

        if not (has_curve_scrollbar and has_strat_scrollbar):
            pass
            # One or both views don't support scrollbar synchronization
            # This can happen with PyQtGraphCurvePlotter which uses a different scrolling mechanism
            print("Warning: Skipping view synchronization - missing verticalScrollBar on one or both views")
            return

        def sync_from(source_view, target_view, include_table=False):
            def on_scroll():
                if self._is_syncing:
                    return
                self._is_syncing = True

                # Get the visible depth range from the source view
                source_viewport = source_view.viewport()
                source_scene_rect = source_view.scene.sceneRect()

                # Map viewport corners to scene coordinates
                top_left = source_view.mapToScene(source_viewport.rect().topLeft())
                bottom_left = source_view.mapToScene(source_viewport.rect().bottomLeft())

                # Calculate visible depth range in scene coordinates
                source_min_depth = source_scene_rect.top() / source_view.depth_scale
                visible_top_depth = top_left.y() / source_view.depth_scale + source_min_depth
                visible_bottom_depth = bottom_left.y() / source_view.depth_scale + source_min_depth

                # Calculate the center depth
                center_depth = (visible_top_depth + visible_bottom_depth) / 2

                # Get target view's scene information
                target_scene_rect = target_view.scene.sceneRect()
                target_min_depth = target_scene_rect.top() / target_view.depth_scale

                # Calculate target scene position for the center depth
                target_center_y = (center_depth - target_min_depth) * target_view.depth_scale

                # Center the target view on the same depth
                target_view.centerOn(QPointF(target_view.viewport().width() / 2, target_center_y))

                # If requested, also sync table to show corresponding rows
                if include_table and self.last_units_dataframe is not None and not self.last_units_dataframe.empty:
                    self._sync_table_to_depth(center_depth)

                self._is_syncing = False
            return on_scroll

        # Connect curve plotter and strat column for mutual scrolling with table sync
        self.curvePlotter.verticalScrollBar().valueChanged.connect(
            sync_from(self.curvePlotter, self.stratigraphicColumnView, include_table=True)
        )
        self.stratigraphicColumnView.verticalScrollBar().valueChanged.connect(
            sync_from(self.stratigraphicColumnView, self.curvePlotter, include_table=True)
        )

    def _sync_table_to_depth(self, center_depth):
        """Scroll the lithology table to show rows near the given depth."""
        if self.last_units_dataframe is None or self.last_units_dataframe.empty:
            return

        # Find the row in units dataframe closest to center_depth
        units_df = self.last_units_dataframe
        if 'from_depth' not in units_df.columns or 'to_depth' not in units_df.columns:
            return

        # Find units that contain the center depth
        containing_units = units_df[
            (units_df['from_depth'] <= center_depth) &
            (units_df['to_depth'] >= center_depth)
        ]

        if not containing_units.empty:
            pass
            # Get the index of the first matching unit
            row_index = containing_units.index[0]
            # Scroll to make this row visible
            index = self.editorTable.model().index(row_index, 0)
            self.editorTable.scrollTo(
                index,
                QAbstractItemView.ScrollHint.PositionAtCenter
            )

    def _on_table_row_selected(self, row_index):
        """Handle table row selection and highlight corresponding stratigraphic unit."""
        if row_index == -1:
            pass
            # No selection - clear highlight
            self.stratigraphicColumnView.highlight_unit(None)
        else:
            # Highlight the corresponding unit in stratigraphic column
            self.stratigraphicColumnView.highlight_unit(row_index)
            # Scroll both views to the selected unit's depth
            if hasattr(self.stratigraphicColumnView, 'units_dataframe') and self.stratigraphicColumnView.units_dataframe is not None:
                if 0 <= row_index < len(self.stratigraphicColumnView.units_dataframe):
                    unit = self.stratigraphicColumnView.units_dataframe.iloc[row_index]
                    center_depth = (unit['from_depth'] + unit['to_depth']) / 2
                    self.stratigraphicColumnView.scroll_to_depth(center_depth)
                    self.curvePlotter.scroll_to_depth(center_depth)

    def _on_unit_clicked(self, unit_index):
        """Handle click on a stratigraphic column unit."""
        # Select the corresponding row in the editor table
        if hasattr(self, 'editorTable') and self.editorTable is not None:
            pass
            # Get the model
            model = self.editorTable.model()
            if model and 0 <= unit_index < model.rowCount():
                pass
                # Select the row in the table
                self.editorTable.selectRow(unit_index)
                # Scroll the table to make the row visible
                index = model.index(unit_index, 0)
                self.editorTable.scrollTo(index)
                # Note: The selectionChanged signal will be emitted automatically,
                # which will trigger _on_table_row_selected to scroll the plot

    def find_svg_file(self, lithology_code, lithology_qualifier=''):
        svg_dir = os.path.join(os.getcwd(), 'src', 'assets', 'svg')

        if not isinstance(lithology_code, str) or not lithology_code:
            pass
#             print(f"DEBUG (MainWindow): Invalid lithology_code provided: {lithology_code}")
            return None

        # Construct the base prefix for the SVG file
        base_prefix = lithology_code.upper()

        # If a qualifier is provided, try to find a combined SVG first
        if lithology_qualifier and isinstance(lithology_qualifier, str):
            combined_code = (base_prefix + lithology_qualifier.upper()).strip()
            combined_filename_prefix = combined_code + ' '
#             print(f"DEBUG (MainWindow): Searching for combined SVG with prefix '{combined_filename_prefix}' in '{svg_dir}'")
            for filename in os.listdir(svg_dir):
                if filename.upper().startswith(combined_filename_prefix):
                    found_path = os.path.join(svg_dir, filename)
                    print(f"DEBUG (MainWindow): Found combined SVG: {found_path}")
                    return found_path
#             print(f"DEBUG (MainWindow): No combined SVG found for prefix '{combined_filename_prefix}'")

        # If no combined SVG found or no qualifier provided, fall back to just the lithology code
        single_filename_prefix = base_prefix + ' '
        print(f"DEBUG (MainWindow): Falling back to searching for single SVG with prefix '{single_filename_prefix}' in '{svg_dir}'")
        for filename in os.listdir(svg_dir):
            if filename.upper().startswith(single_filename_prefix):
                found_path = os.path.join(svg_dir, filename)
#                 print(f"DEBUG (MainWindow): Found single SVG: {found_path}")
                return found_path

        print(f"DEBUG (MainWindow): No SVG found for lithology code '{lithology_code}' (and qualifier '{lithology_qualifier}')")
        return None

    def connect_signals(self):
        self.loadLasButton.clicked.connect(self.load_las_file_dialog)
        self.runAnalysisButton.clicked.connect(self.run_analysis)
        self.settingsButton.clicked.connect(self.open_advanced_settings_dialog)
        # Connect icon buttons (text button kept for backward compatibility)
        if hasattr(self, 'exportCsvIconButton'):
            self.exportCsvIconButton.clicked.connect(self.export_editor_data_to_csv)
        else:
            self.exportCsvButton.clicked.connect(self.export_editor_data_to_csv)
        # self.tab_widget.currentChanged.connect(self.on_tab_changed)  # MDI removes tabs
        # Connect stratigraphic column unit clicks
        if hasattr(self, 'stratigraphicColumnView'):
            self.stratigraphicColumnView.unitClicked.connect(self._on_unit_clicked)

        # Load and apply stylesheet with current theme
        self.load_stylesheet()

    def load_stylesheet(self):
        """Load and apply the QSS stylesheet with current theme."""
        try:
            # Get the path to the styles.qss file
            styles_dir = os.path.join(os.path.dirname(__file__), "styles")
            stylesheet_path = os.path.join(styles_dir, "styles.qss")

            if os.path.exists(stylesheet_path):
                with open(stylesheet_path, 'r') as f:
                    stylesheet = f.read()

                # Apply the stylesheet
                self.setStyleSheet(stylesheet)

                # Apply theme class to the application (empty string for default light theme)
                app = QApplication.instance()
                if app:
                    app.setProperty("class", "")  # Use :root (light theme)

#                 print("Stylesheet loaded successfully with light theme")
            else:
                print(f"Warning: Stylesheet not found at {stylesheet_path}")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    def toggle_theme(self):
        """Toggle theme (only light theme supported)."""
        # Only light theme is supported, so just ensure light theme is set
        self.set_theme("light")

    def save_theme_preference(self):
        """Save theme preference to settings."""
        # Load current settings
        app_settings = load_settings()

        # Update theme in settings
        app_settings["theme"] = self.current_theme

        # Save all settings
        save_settings(
            lithology_rules=app_settings["lithology_rules"],
            separator_thickness=app_settings["separator_thickness"],
            draw_separator_lines=app_settings["draw_separator_lines"],
            curve_inversion_settings=app_settings["curve_inversion_settings"],
            curve_thickness=app_settings.get("curve_thickness", 2),
            use_researched_defaults=app_settings.get("use_researched_defaults", True),
            analysis_method=app_settings.get("analysis_method", "standard"),
            merge_thin_units=app_settings.get("merge_thin_units", False),
            merge_threshold=app_settings.get("merge_threshold", 0.05),
            smart_interbedding=app_settings.get("smart_interbedding", False),
            smart_interbedding_max_sequence_length=app_settings.get("smart_interbedding_max_sequence_length", 10),
            smart_interbedding_thick_unit_threshold=app_settings.get("smart_interbedding_thick_unit_threshold", 0.5),
            fallback_classification=app_settings.get("fallback_classification", DEFAULT_FALLBACK_CLASSIFICATION),
            bit_size_mm=app_settings.get("bit_size_mm", 150.0),
            show_anomaly_highlights=app_settings.get("show_anomaly_highlights", True),
            casing_depth_enabled=app_settings.get("casing_depth_enabled", False),
            casing_depth_m=app_settings.get("casing_depth_m", 0.0),
            disable_svg=app_settings.get("disable_svg", False),
            avg_executable_path=app_settings.get("avg_executable_path", ""),
            svg_directory_path=app_settings.get("svg_directory_path", ""),
            workspace_state=app_settings.get("workspace"),
            theme=self.current_theme,
            curve_visibility=app_settings.get("curve_visibility", {}),
            column_visibility=app_settings.get("column_visibility", {})
        )

    def open_session_dialog(self):
        """Open the session management dialog."""
        dialog = SessionDialog(parent=self, main_window=self)
        dialog.session_selected.connect(self.on_session_loaded)
        dialog.exec()

    def on_session_loaded(self, session_name):
        """Handle session loaded signal."""
#         print(f"Session '{session_name}' loaded successfully")
        # Additional session loading logic can be added here if needed

    def open_template_dialog(self):
        """Open the template selection dialog."""
        dialog = TemplateDialog(parent=self, main_window=self)
        dialog.template_selected.connect(self.on_template_applied)
        dialog.exec()

    def on_template_applied(self, template_name):
        """Handle template applied signal."""
#         print(f"Template '{template_name}' applied successfully")
        # Refresh settings in UI if needed
        self.refresh_settings_from_disk()

    def refresh_settings_from_disk(self):
        """Refresh settings from disk and update UI."""
        try:
            from ..core.settings_manager import load_settings
            settings = load_settings()
            # Update UI components with new settings if needed
            print("Settings refreshed from disk")
        except Exception as e:
            print(f"Error refreshing settings: {e}")

    def open_advanced_settings_dialog(self):
        """Open the advanced settings dialog (modal)."""
        # Gather current settings from the dock panel
        current_settings = self.get_current_settings()
        dialog = SettingsDialog(parent=self, current_settings=current_settings)
        dialog.settings_updated.connect(self.update_settings_from_dialog)
        dialog.exec()
    
    def open_sync_settings_dialog(self):
        """Open cross-hole sync settings dialog."""
        from .dialogs.sync_settings_dialog import create_sync_settings_dialog
        
        # Get current settings from sync manager
        current_settings = {}
        if hasattr(self, 'cross_hole_sync_manager'):
            current_settings = self.cross_hole_sync_manager.get_settings()
        
        # Create dialog
        dialog = create_sync_settings_dialog(self, current_settings)
        
        # Update dialog status
        hole_count = 0
        sync_active = False
        if hasattr(self, 'cross_hole_sync_manager'):
            hole_count = self.cross_hole_sync_manager.get_open_hole_count()
            sync_active = self.cross_hole_sync_manager.is_sync_active()
        
        dialog.update_status(hole_count, sync_active)
        
        # Connect settings changed signal
        dialog.settingsChanged.connect(self._on_sync_settings_changed)
        
        # Show dialog
        dialog.exec()
    
    def _on_sync_settings_changed(self, settings):
        """Handle sync settings changes from dialog."""
#         print("DEBUG (main_window): Sync settings changed")
        # Apply settings to sync manager
        if hasattr(self, 'cross_hole_sync_manager'):
            self.cross_hole_sync_manager.apply_settings(settings)
            # Update sync status indicator
            self.update_sync_status_indicator()
    
    def update_sync_status_indicator(self):
        """Update the sync status indicator in toolbar."""
        if hasattr(self, 'display_mode_switcher') and hasattr(self, 'cross_hole_sync_manager'):
            hole_count = self.cross_hole_sync_manager.get_open_hole_count()
            sync_active = self.cross_hole_sync_manager.is_sync_active()
            self.display_mode_switcher.update_sync_status(sync_active, hole_count)
    
    def _on_sync_settings_requested(self):
        """Handle sync settings request from toolbar."""
#         print("DEBUG (main_window): Sync settings requested")
        self.open_sync_settings_dialog()
    
    def open_curve_templates_dialog(self):
        """Open curve settings templates dialog."""
        print("DEBUG (main_window): Opening curve templates dialog")
        # TODO: Implement curve templates dialog
        # For now, show a message
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Curve Settings Templates",
            "Curve settings templates feature is available via the Export/Import buttons in the display mode toolbar.\n\n"
            "Full template management dialog will be implemented in a future update."
        )
    
    def export_curves_dialog(self):
        """Open dialog to export curves to various formats (simplified for testing)."""
#         print("DEBUG (main_window): Export curves dialog requested")
        # Simplified version for testing
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Export Curves",
            "Curve export functionality is available in the full Earthworm application.\n\n"
            "For testing purposes, this is a placeholder dialog."
        )
    
    def curve_analysis_dialog(self):
        """Open dialog for advanced curve analysis tools (simplified for testing)."""
        print("DEBUG (main_window): Curve analysis dialog requested")
        # Simplified version for testing
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Curve Analysis",
            "Advanced curve analysis tools are available in the full Earthworm application.\n\n"
            "For testing purposes, this is a placeholder dialog."
        )

    def on_hole_double_clicked(self, index):
        """Handle double-click on a file in the project explorer tree."""
        if self.holes_model.isDir(index):
            return  # Don't open directories
        file_path = self.holes_model.filePath(index)
        # Check if it's a supported file type
        if file_path.lower().endswith(('.csv', '.xlsx', '.las')):
            self.open_hole(file_path)

    def open_hole(self, file_path):
        """Open a hole file in a new MDI subwindow (Phase 1, Task 2)."""
        # Create a new hole editor window
        hole_editor = HoleEditorWindow(coallog_data=self.coallog_data, main_window=self)
        hole_editor.set_file_path(file_path)

        # Create MDI subwindow
        subwindow = QMdiSubWindow()
        subwindow.setWidget(hole_editor)
        subwindow.setWindowTitle(os.path.basename(file_path))

        # Add to MDI area
        self.mdi_area.addSubWindow(subwindow)
        subwindow.showMaximized()

        # Register hole with cross-hole sync manager
        if hasattr(self, 'cross_hole_sync_manager'):
            self.cross_hole_sync_manager.register_hole(hole_editor)
        
        # Connect hole signals for sync updates
        self._connect_hole_to_sync_manager(hole_editor)

        # Optionally tile windows
        # self.mdi_area.tileSubWindows()

        # For backward compatibility, still set global las_file_path?
        # self.las_file_path = file_path
        # But we should not call load_las_data() because it would affect the main window's widgets
    
    def _connect_hole_to_sync_manager(self, hole_editor):
        """Connect a hole editor to the cross-hole sync manager."""
        if not hasattr(self, 'cross_hole_sync_manager'):
            return
        
        # TODO: Connect hole editor signals to sync manager
        # When hole editor curve selection changes, update sync manager
        # When hole editor curve settings change, update sync manager
        
#         print(f"DEBUG (main_window): Connected hole to sync manager: {hole_editor.current_file_path}")

    def open_map_window(self):
        """Open a new map window (Phase 5, Task 8)."""
        # Create a new map window
        map_window = MapWindow()

        # Create MDI subwindow
        subwindow = QMdiSubWindow()
        subwindow.setWidget(map_window)
        subwindow.setWindowTitle("Map")

        # Add to MDI area
        self.mdi_area.addSubWindow(subwindow)
        subwindow.showMaximized()

        # Connect selection changed signal to sync with holes list
        map_window.selectionChanged.connect(self.on_map_selection_changed)

        # Load existing holes from the project explorer into the map
        self.load_holes_into_map(map_window)

        return map_window

    def load_holes_into_map(self, map_window):
        """Load holes from project explorer into map window."""
        # Get all files from the holes model
        root_index = self.holes_model.index(os.getcwd())

        # Walk through the model to find all files
        files_to_process = []
        stack = [root_index]

        while stack:
            index = stack.pop()
            if self.holes_model.isDir(index):
                pass
                # Add child directories to stack
                for row in range(self.holes_model.rowCount(index)):
                    child_index = self.holes_model.index(row, 0, index)
                    stack.append(child_index)
            else:
                # It's a file
                file_path = self.holes_model.filePath(index)
                if file_path.lower().endswith(('.csv', '.xlsx', '.las')):
                    files_to_process.append(file_path)

        # Process each file
        for file_path in files_to_process:
            hole_info = map_window.extract_coordinates_from_file(file_path)
            if hole_info:
                map_window.add_hole(file_path, hole_info)

        if files_to_process:
            print(f"Loaded {len(files_to_process)} files into map window")

    def on_map_selection_changed(self, selected_files):
        """Handle map selection changes to sync with holes list sidebar."""
#         print(f"Map selection changed: {len(selected_files)} holes selected")

        # Convert to set for efficient lookup
        selected_set = set(selected_files)

        # Get selection model
        selection_model = self.holes_tree.selectionModel()
        if not selection_model:
            return

        # Clear current selection
        selection_model.clear()

        # Select items in the tree that match the selected files
        for file_path in selected_files:
            pass
            # Get the index for this file path
            index = self.holes_model.index(file_path)
            if index.isValid():
                pass
                # Select the item
                selection_model.select(index, selection_model.SelectionFlag.Select)

        # If we have selections, ensure they're visible
        if selected_files:
            first_index = self.holes_model.index(selected_files[0])
            if first_index.isValid():
                self.holes_tree.scrollTo(first_index)

    def open_cross_section_window(self, hole_file_paths=None):
        """Open a new cross-section window (Phase 5, Task 9)."""
        # Get selected holes if not provided
        if hole_file_paths is None:
            pass
            # Get selected files from holes tree
            selected_indexes = self.holes_tree.selectionModel().selectedIndexes()
            hole_file_paths = []
            for index in selected_indexes:
                if index.column() == 0:
                    file_path = self.holes_model.filePath(index)
                    if file_path.lower().endswith(('.csv', '.xlsx', '.las')):
                        hole_file_paths.append(file_path)

        # Need at least 2 holes for a cross-section, but 3+ is better
        if len(hole_file_paths) < 2:
            QMessageBox.warning(self, "Insufficient Holes",
                              "Please select at least 2 holes for a cross-section.")
            return

        # Create cross-section window
        cross_section = CrossSectionWindow(hole_file_paths, use_researched_defaults=self.use_researched_defaults)

        # Create MDI subwindow
        subwindow = QMdiSubWindow()
        subwindow.setWidget(cross_section)
        subwindow.setWindowTitle("Cross-Section")

        # Add to MDI area
        self.mdi_area.addSubWindow(subwindow)
        subwindow.showMaximized()

        return cross_section

    def on_holes_tree_selection_changed(self, selected, deselected):
        """Handle holes tree selection changes to sync with map window."""
        # Find active map window
        map_window = self.find_active_map_window()
        if not map_window:
            return

        # Get selected file paths
        selected_indexes = self.holes_tree.selectionModel().selectedIndexes()
        selected_files = []

        for index in selected_indexes:
            if index.column() == 0:  # Only process first column
                file_path = self.holes_model.filePath(index)
                if file_path.lower().endswith(('.csv', '.xlsx', '.las')):
                    selected_files.append(file_path)

        # Update map window selection
        map_window.set_selected_holes(selected_files)

    def find_active_map_window(self):
        """Find the active map window among MDI subwindows."""
        active_subwindow = self.mdi_area.activeSubWindow()
        if active_subwindow:
            widget = active_subwindow.widget()
            if isinstance(widget, MapWindow):
                return widget

        # If no active subwindow, look for any map window
        for subwindow in self.mdi_area.subWindowList():
            widget = subwindow.widget()
            if isinstance(widget, MapWindow):
                return widget

        return None

    def load_las_file_dialog(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open LAS File", "", "LAS Files (*.las);;All Files (*)")
        if file_path:
            self.las_file_path = file_path
            self.load_las_data()

    def load_coallog_data(self):
        try:
            coallog_path = os.path.join(os.getcwd(), 'src', 'assets', 'CoalLog v3.1 Dictionaries.xlsx')
            return load_coallog_dictionaries(coallog_path)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", f"Failed to load CoalLog dictionaries: {e}")
            return None

    def load_lithology_qualifier_map(self):
        try:
            qualifier_map_path = os.path.join(os.getcwd(), 'src', 'assets', 'litho_lithoQuals.json')
            with open(qualifier_map_path, 'r') as f:
                data = json.load(f)
                return data.get("lithology_qualifiers", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            QMessageBox.critical(self, "Error", f"Failed to load lithology qualifier map: {e}")
            return {}

    def load_las_data(self):
        """Load LAS file using background worker thread."""
        if not self.las_file_path:
            return

        # Disable UI during loading
        self.loadLasButton.setEnabled(False)
        self.loadLasButton.setText("Loading...")

        # Create worker and thread
        self.las_worker = LASLoaderWorker(self.las_file_path)
        self.las_thread = QThread()

        # Move worker to thread
        self.las_worker.moveToThread(self.las_thread)

        # Connect signals
        self.las_thread.started.connect(self.las_worker.run)
        self.las_worker.progress.connect(self._on_las_loading_progress)
        self.las_worker.finished.connect(self._on_las_loading_finished)
        self.las_worker.error.connect(self._on_las_loading_error)

        # Cleanup connections
        self.las_worker.finished.connect(self.las_thread.quit)
        self.las_worker.finished.connect(self.las_worker.deleteLater)
        self.las_thread.finished.connect(self.las_thread.deleteLater)

        # Start thread
        self.las_thread.start()

    def _on_las_loading_progress(self, percent: int, message: str):
        """Handle progress updates from LAS loader worker."""
        self.loadLasButton.setText(f"Loading... {percent}%")
        # Could update status bar here if available
        print(f"LAS Loading: {percent}% - {message}")

    def _on_las_loading_finished(self, dataframe: pd.DataFrame, metadata: dict, file_path: str):
        """Handle successful LAS file loading."""
        # Update UI
        self.loadLasButton.setEnabled(True)
        self.loadLasButton.setText("Load LAS File")

        # Extract mnemonics from dataframe columns
        mnemonics = list(dataframe.columns)

        # Update combo boxes with available mnemonics
        self.gammaRayComboBox.clear()
        self.densityComboBox.clear()
        self.shortSpaceDensityComboBox.clear()
        self.longSpaceDensityComboBox.clear()
        self.caliperComboBox.clear()
        self.resistivityComboBox.clear()

        self.gammaRayComboBox.addItem("--- None ---")
        self.gammaRayComboBox.addItems(mnemonics)
        self.densityComboBox.addItem("--- None ---")
        self.densityComboBox.addItems(mnemonics)
        self.shortSpaceDensityComboBox.addItem("--- None ---")
        self.shortSpaceDensityComboBox.addItems(mnemonics)
        self.longSpaceDensityComboBox.addItem("--- None ---")
        self.longSpaceDensityComboBox.addItems(mnemonics)
        self.caliperComboBox.addItem("--- None ---")
        self.caliperComboBox.addItems(mnemonics)
        self.resistivityComboBox.addItem("--- None ---")
        self.resistivityComboBox.addItems(mnemonics)

        # Set default selections
        if 'GR' in mnemonics:
            self.gammaRayComboBox.setCurrentText('GR')
        # Both density combo boxes get the same default selection
        if 'RHOB' in mnemonics:
            self.densityComboBox.setCurrentText('RHOB')
            self.shortSpaceDensityComboBox.setCurrentText('RHOB')
        if 'DENS' in mnemonics: # Assuming 'DENS' for short space density
            self.densityComboBox.setCurrentText('DENS')
            self.shortSpaceDensityComboBox.setCurrentText('DENS')
        if 'LSD' in mnemonics: # Assuming 'LSD' for long space density
            self.longSpaceDensityComboBox.setCurrentText('LSD')
        # Caliper default selection
        for cal_name in ['CAL', 'cal', 'caliper', 'CD', 'cd']:
            if cal_name in mnemonics:
                self.caliperComboBox.setCurrentText(cal_name)
                break
        # Resistivity default selection
        for res_name in ['RES', 'resistivity', 'RT', 'ILD', 'ild']:
            if res_name in mnemonics:
                self.resistivityComboBox.setCurrentText(res_name)
                break

        # Store metadata for potential use
        self.las_metadata = metadata

        QMessageBox.information(self, "LAS File Loaded",
                               f"Successfully loaded {os.path.basename(file_path)}")

    def _on_las_loading_error(self, error_msg: str, file_path: str):
        """Handle LAS loading errors."""
        # Re-enable UI
        self.loadLasButton.setEnabled(True)
        self.loadLasButton.setText("Load LAS File")

        # Show error message
        QMessageBox.critical(self, "Error Loading LAS File",
                            f"Failed to load {os.path.basename(file_path)}:\n\n{error_msg}")
        self.las_file_path = None

    def load_default_lithology_rules(self):
        self.lithology_rules = DEFAULT_LITHOLOGY_RULES

    # Tab widget removed in MDI refactoring - method kept for compatibility

    # Methods removed - settings UI widgets only exist in SettingsDialog
    # toggle_interbedding_params_visibility() and toggle_casing_depth_input() were part of removed settings dock

    def on_curve_visibility_changed(self):
        """Handle curve visibility checkbox state changes."""
        # Get the checkbox that triggered the signal
        checkbox = self.sender()
        if not hasattr(checkbox, 'curve_name'):
            return

        curve_name = checkbox.curve_name
        visible = checkbox.isChecked()

        # Update curve visibility in all open hole editors
        for subwindow in self.mdi_area.subWindowList():
            hole_editor = subwindow.widget()
            if hasattr(hole_editor, 'curvePlotter') and hasattr(hole_editor.curvePlotter, 'set_curve_visibility'):
                hole_editor.curvePlotter.set_curve_visibility(curve_name, visible)

    def mark_settings_dirty(self):
        """Mark settings as dirty when any setting is modified (Phase 5 Task 5.2)."""
        self.settings_dirty = True
        # Update the "Update Settings" button text to indicate unsaved changes
        if hasattr(self, 'updateSettingsButton'):
            self.updateSettingsButton.setText("Update Settings *")

    def reset_settings_to_defaults(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(self, "Reset Settings",
                                     "Are you sure you want to reset all settings to defaults?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            pass
            # Reset lithology rules to default
            self.lithology_rules = DEFAULT_LITHOLOGY_RULES.copy()
            # Reset separator settings
            self.initial_separator_thickness = DEFAULT_SEPARATOR_THICKNESS
            self.initial_draw_separators = DRAW_SEPARATOR_LINES
            # Reset curve thickness default
            self.initial_curve_thickness = DEFAULT_CURVE_THICKNESS
            # Reset curve inversion defaults
            self.initial_curve_inversion_settings = {'gamma': False, 'short_space_density': False, 'long_space_density': False, 'caliper': False, 'resistivity': False}
            # Reset researched defaults
            self.use_researched_defaults = False
            # Reset analysis method
            self.analysis_method = "standard"
            # Reset merge settings
            self.merge_thin_units = DEFAULT_MERGE_THIN_UNITS
            self.merge_threshold = DEFAULT_MERGE_THRESHOLD
            # Reset smart interbedding settings
            self.smart_interbedding = DEFAULT_SMART_INTERBEDDING
            self.smart_interbedding_max_sequence_length = DEFAULT_SMART_INTERBEDDING_MAX_SEQUENCE_LENGTH
            self.smart_interbedding_thick_unit_threshold = DEFAULT_SMART_INTERBEDDING_THICK_UNIT_THRESHOLD
            # Reset fallback classification
            self.use_fallback_classification = DEFAULT_FALLBACK_CLASSIFICATION
            # Reset bit size and anomaly highlights
            self.bit_size_mm = DEFAULT_BIT_SIZE_MM
            self.show_anomaly_highlights = DEFAULT_SHOW_ANOMALY_HIGHLIGHTS
            # Reset casing depth settings
            self.casing_depth_enabled = DEFAULT_CASING_DEPTH_ENABLED
            self.casing_depth_m = DEFAULT_CASING_DEPTH_M
            # Update UI controls
            self.load_settings_rules_to_table()
            # self.# load_separator_settings()  # Removed - legacy code  # Removed - legacy code
            # self.# load_curve_thickness_settings()  # Removed - legacy code  # Removed - legacy code
            # self.# load_curve_inversion_settings()  # Removed - legacy code  # Removed - legacy code
            # use_researched_defaults is already set to False above
            # Note: Settings UI widgets (checkboxes, spinboxes, comboboxes) only exist in SettingsDialog
            # The values are stored in attributes and will be used when SettingsDialog is opened
            # Save defaults
            self.update_settings(auto_save=True)
            # Clear the dirty flag since settings have been reset
            self.settings_dirty = False
            # Update the "Update Settings" button text to remove the asterisk
            if hasattr(self, 'updateSettingsButton'):
                self.updateSettingsButton.setText("Update Settings")
            QMessageBox.information(self, "Settings Reset", "All settings have been reset to defaults.")

    def revert_to_saved_settings(self):
        """Revert UI to last saved settings from disk (Phase 5 Task 5.2.4)."""
        # Load saved settings from disk
        app_settings = load_settings()

        # Update instance variables from saved settings
        self.initial_separator_thickness = app_settings["separator_thickness"]
        self.initial_draw_separators = app_settings["draw_separator_lines"]
        self.initial_curve_inversion_settings = app_settings["curve_inversion_settings"]
        self.initial_curve_thickness = app_settings["curve_thickness"]
        self.use_researched_defaults = app_settings["use_researched_defaults"]
        self.analysis_method = app_settings.get("analysis_method", "standard")
        self.merge_thin_units = app_settings.get("merge_thin_units", False)
        self.merge_threshold = app_settings.get("merge_threshold", 0.05)
        self.smart_interbedding = app_settings.get("smart_interbedding", False)
        self.smart_interbedding_max_sequence_length = app_settings.get("smart_interbedding_max_sequence_length", 10)
        self.smart_interbedding_thick_unit_threshold = app_settings.get("smart_interbedding_thick_unit_threshold", 0.5)
        self.use_fallback_classification = app_settings.get("fallback_classification", DEFAULT_FALLBACK_CLASSIFICATION)
        self.bit_size_mm = app_settings.get("bit_size_mm", 215.9)
        self.show_anomaly_highlights = app_settings.get("show_anomaly_highlights", False)
        self.casing_depth_enabled = app_settings.get("casing_depth_enabled", False)
        self.casing_depth_m = app_settings.get("casing_depth_m", 0.0)

        # Update lithology rules
        self.lithology_rules = app_settings["lithology_rules"]

        # Call existing helper methods to update UI
        # self.# load_separator_settings()  # Removed - legacy code  # Removed - legacy code
        # self.# load_curve_thickness_settings()  # Removed - legacy code  # Removed - legacy code
        # self.# load_curve_inversion_settings()  # Removed - legacy code  # Removed - legacy code

        # Only load settings rules to table if coallog_data is available
        if self.coallog_data is not None:
            self.load_settings_rules_to_table()
        else:
            pass  # coallog_data not available
#             print("Warning: coallog_data not available, skipping load_settings_rules_to_table()")

        # Update other UI widgets that don't have helper methods
        # use_researched_defaults is managed as an attribute, not a UI widget in main window
        # Note: Settings UI widgets (checkboxes, spinboxes, comboboxes) only exist in SettingsDialog
        # The values are stored in attributes and will be used when SettingsDialog is opened

        # Clear dirty flag and update button text
        self.settings_dirty = False
        if hasattr(self, 'updateSettingsButton'):
            self.updateSettingsButton.setText("Update Settings")

    def save_settings_as_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Settings As", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                # Ensure current UI settings are reflected in self.lithology_rules before saving
                self.save_settings_rules_from_table(show_message=False)
                # Settings UI widgets only exist in SettingsDialog, use attribute values directly
                current_separator_thickness = self.initial_separator_thickness
                current_draw_separators = self.initial_draw_separators
                current_curve_thickness = self.initial_curve_thickness
                current_curve_inversion_settings = self.initial_curve_inversion_settings

                # Get current value of researched defaults setting
                current_use_researched_defaults = self.use_researched_defaults

                # Get current analysis method
                current_analysis_method = self.analysis_method

                # Get current merge settings
                current_merge_thin_units = self.merge_thin_units
                current_merge_threshold = self.merge_threshold  # Keep the loaded threshold

                # Get current smart interbedding settings
                current_smart_interbedding = self.smart_interbedding
                current_smart_interbedding_max_sequence = self.smart_interbedding_max_sequence_length
                current_smart_interbedding_thick_unit = self.smart_interbedding_thick_unit_threshold
                current_fallback_classification = self.use_fallback_classification

                # Get current bit size
                current_bit_size_mm = self.bit_size_mm

                # Get current anomaly highlights setting
                current_show_anomaly_highlights = self.show_anomaly_highlights

                # Get current casing depth settings
                current_casing_depth_enabled = self.casingDepthEnabledCheckBox.isChecked() if hasattr(self, 'casingDepthEnabledCheckBox') else self.casing_depth_enabled
                current_casing_depth_m = self.casingDepthSpinBox.value() if hasattr(self, 'casingDepthSpinBox') else self.casing_depth_m

                # Get current curve visibility
                current_curve_visibility = {}
                if hasattr(self, 'curve_visibility_checkboxes'):
                    for curve_name, checkbox in self.curve_visibility_checkboxes.items():
                        current_curve_visibility[curve_name] = checkbox.isChecked()
                else:
                    current_curve_visibility = self.curve_visibility

                # Get current workspace state
                workspace_state = self.workspace if hasattr(self, 'workspace') else None

                # Call save_settings with the chosen file path
                save_settings(
                    lithology_rules=self.lithology_rules,
                    separator_thickness=current_separator_thickness,
                    draw_separator_lines=current_draw_separators,
                    curve_inversion_settings=current_curve_inversion_settings,
                    curve_thickness=current_curve_thickness,
                    use_researched_defaults=current_use_researched_defaults,
                    analysis_method=current_analysis_method,
                    merge_thin_units=current_merge_thin_units,
                    merge_threshold=current_merge_threshold,
                    smart_interbedding=current_smart_interbedding,
                    smart_interbedding_max_sequence_length=current_smart_interbedding_max_sequence,
                    smart_interbedding_thick_unit_threshold=current_smart_interbedding_thick_unit,
                    fallback_classification=current_fallback_classification,
                    bit_size_mm=current_bit_size_mm,
                    disable_svg=self.disable_svg,
                    show_anomaly_highlights=current_show_anomaly_highlights,
                    casing_depth_enabled=current_casing_depth_enabled,
                    casing_depth_m=current_casing_depth_m,
                    avg_executable_path=self.avg_executable_path,
                    svg_directory_path=self.svg_directory_path,
                    workspace_state=workspace_state,
                    theme=self.current_theme,
                    column_visibility=self.column_visibility,
                    curve_visibility=current_curve_visibility,
                    pane_visibility=self.pane_visibility,
                    file_path=file_path
                )
                QMessageBox.information(self, "Settings Saved", f"Settings saved to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def get_current_settings(self):
        """Return current settings as a dictionary compatible with SettingsDialog."""
        # Settings dock has been removed - use instance variables instead of UI controls
        # Note: lithology rules are already saved in self.lithology_rules
        
        # Get settings from instance variables (set by update_settings_from_dialog)
        current_separator_thickness = self.initial_separator_thickness
        current_draw_separators = self.initial_draw_separators
        current_curve_thickness = self.initial_curve_thickness
        current_curve_inversion_settings = self.initial_curve_inversion_settings

        current_use_researched_defaults = self.use_researched_defaults
        current_analysis_method = self.analysis_method
        current_merge_thin_units = self.merge_thin_units
        current_merge_threshold = self.merge_threshold  # Keep the loaded threshold
        current_smart_interbedding = self.smart_interbedding
        current_smart_interbedding_max_sequence = self.smart_interbedding_max_sequence_length
        current_smart_interbedding_thick_unit = self.smart_interbedding_thick_unit_threshold
        current_fallback_classification = self.use_fallback_classification
        current_bit_size_mm = self.bit_size_mm
        current_disable_svg = self.disable_svg

        # Build settings dict matching SettingsDialog expectations
        settings = {
            'lithology_rules': self.lithology_rules,
            'separator_thickness': current_separator_thickness,
            'draw_separators': current_draw_separators,
            'curve_thickness': current_curve_thickness,
            'invert_gamma': current_curve_inversion_settings['gamma'],
            'invert_short_space_density': current_curve_inversion_settings['short_space_density'],
            'invert_long_space_density': current_curve_inversion_settings['long_space_density'],
            'invert_caliper': current_curve_inversion_settings['caliper'],
            'invert_resistivity': current_curve_inversion_settings['resistivity'],
            'use_researched_defaults': current_use_researched_defaults,
            'analysis_method': current_analysis_method,
            'merge_thin_units': current_merge_thin_units,
            'smart_interbedding': current_smart_interbedding,
            'fallback_classification': current_fallback_classification,
            'smart_interbedding_max_sequence_length': current_smart_interbedding_max_sequence,
            'smart_interbedding_thick_unit_threshold': current_smart_interbedding_thick_unit,
            'bit_size_mm': current_bit_size_mm,
            'disable_svg': current_disable_svg,
            'avg_executable_path': self.avg_executable_path,
            'svg_directory_path': self.svg_directory_path,
            'column_visibility': self.column_visibility,
            'curve_visibility': self.curve_visibility,
            'pane_visibility': self.pane_visibility
        }
        return settings

    def update_settings_from_dialog(self, settings):
        """Update settings from a dictionary (e.g., from SettingsDialog)."""
        # Update internal variables from settings dict
        self.lithology_rules = settings.get('lithology_rules', self.lithology_rules)
        self.initial_separator_thickness = settings.get('separator_thickness', self.initial_separator_thickness)
        self.initial_draw_separators = settings.get('draw_separators', self.initial_draw_separators)
        self.initial_curve_thickness = settings.get('curve_thickness', self.initial_curve_thickness)
        self.initial_curve_inversion_settings = {
            'gamma': settings.get('invert_gamma', False),
            'short_space_density': settings.get('invert_short_space_density', False),
            'long_space_density': settings.get('invert_long_space_density', False),
            'caliper': settings.get('invert_caliper', False),
            'resistivity': settings.get('invert_resistivity', False)
        }
        self.use_researched_defaults = settings.get('use_researched_defaults', self.use_researched_defaults)
        self.analysis_method = settings.get('analysis_method', self.analysis_method)
        self.merge_thin_units = settings.get('merge_thin_units', self.merge_thin_units)
        self.smart_interbedding = settings.get('smart_interbedding', self.smart_interbedding)
        self.smart_interbedding_max_sequence_length = settings.get('smart_interbedding_max_sequence_length', self.smart_interbedding_max_sequence_length)
        self.smart_interbedding_thick_unit_threshold = settings.get('smart_interbedding_thick_unit_threshold', self.smart_interbedding_thick_unit_threshold)
        self.use_fallback_classification = settings.get('fallback_classification', self.use_fallback_classification)
        self.bit_size_mm = settings.get('bit_size_mm', self.bit_size_mm)
        self.avg_executable_path = settings.get('avg_executable_path', self.avg_executable_path)
        self.disable_svg = settings.get('disable_svg', self.disable_svg)
        self.svg_directory_path = settings.get('svg_directory_path', self.svg_directory_path)
        self.column_visibility = settings.get('column_visibility', self.column_visibility)
        self.curve_visibility = settings.get('curve_visibility', self.curve_visibility)
        self.pane_visibility = settings.get('pane_visibility', self.pane_visibility)
        # UI controls removed (settings dock no longer exists)
        # Save updated settings to disk
        self.update_settings(auto_save=True)

    def update_settings_from_template(self, template):
        """Update settings from a template object."""
        from ..core.template_manager import ProjectTemplate

        if not isinstance(template, ProjectTemplate):
            print(f"Error: Expected ProjectTemplate, got {type(template)}")
            return

#         print(f"Updating settings from template: {template.name}")

        # Update lithology rules from template
        self.lithology_rules = template.lithology_rules

        # Update other settings from template defaults
        if template.default_settings:
            for key, value in template.default_settings.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                    print(f"  Set {key} = {value}")

        # Update UI controls
        self.load_settings_rules_to_table()

        # Show notification
        QMessageBox.information(
            self,
            "Template Applied",
            f"Template '{template.name}' has been applied.\n\n"
            f"Lithology rules and settings have been updated."
        )
        # Note: Settings UI widgets only exist in SettingsDialog
        # The values are stored in attributes and will be used when SettingsDialog is opened
        # Refresh range visualization
        self.refresh_range_visualization()
        # Save to disk
        self.update_settings(auto_save=True)

    def update_settings(self, auto_save=False):
        pass
        # This method will be called when any setting changes or when "Update Settings" is clicked
        # It gathers all current settings and saves them to the default settings file
        self.save_settings_rules_from_table(show_message=False) # Save rules first

        # Settings UI widgets only exist in SettingsDialog, use attribute values directly
        current_separator_thickness = self.initial_separator_thickness
        current_draw_separators = self.initial_draw_separators
        current_curve_thickness = self.initial_curve_thickness
        current_curve_inversion_settings = self.initial_curve_inversion_settings

        current_use_researched_defaults = self.use_researched_defaults
        current_analysis_method = self.analysis_method
        current_merge_thin_units = self.merge_thin_units
        current_merge_threshold = self.merge_threshold  # Keep the loaded threshold
        current_smart_interbedding = self.smartInterbeddingCheckBox.isChecked() if hasattr(self, 'smartInterbeddingCheckBox') else self.smart_interbedding
        current_smart_interbedding_max_sequence = self.smartInterbeddingMaxSequenceSpinBox.value() if hasattr(self, 'smartInterbeddingMaxSequenceSpinBox') else self.smart_interbedding_max_sequence_length
        current_smart_interbedding_thick_unit = self.smartInterbeddingThickUnitSpinBox.value() if hasattr(self, 'smartInterbeddingThickUnitSpinBox') else self.smart_interbedding_thick_unit_threshold
        current_fallback_classification = self.fallbackClassificationCheckBox.isChecked() if hasattr(self, 'fallbackClassificationCheckBox') else self.use_fallback_classification
        current_bit_size_mm = self.bitSizeSpinBox.value() if hasattr(self, 'bitSizeSpinBox') else self.bit_size_mm
        current_show_anomaly_highlights = self.showAnomalyHighlightsCheckBox.isChecked() if hasattr(self, 'showAnomalyHighlightsCheckBox') else self.show_anomaly_highlights
        current_casing_depth_enabled = self.casingDepthEnabledCheckBox.isChecked() if hasattr(self, 'casingDepthEnabledCheckBox') else self.casing_depth_enabled
        current_casing_depth_m = self.casingDepthSpinBox.value() if hasattr(self, 'casingDepthSpinBox') else self.casing_depth_m
        current_curve_visibility = self.curve_visibility
        workspace_state = self.workspace if hasattr(self, 'workspace') else None

        save_settings(
            lithology_rules=self.lithology_rules,
            separator_thickness=current_separator_thickness,
            draw_separator_lines=current_draw_separators,
            curve_inversion_settings=current_curve_inversion_settings,
            curve_thickness=current_curve_thickness,
            use_researched_defaults=current_use_researched_defaults,
            analysis_method=current_analysis_method,
            merge_thin_units=current_merge_thin_units,
            merge_threshold=current_merge_threshold,
            smart_interbedding=current_smart_interbedding,
            smart_interbedding_max_sequence_length=current_smart_interbedding_max_sequence,
            smart_interbedding_thick_unit_threshold=current_smart_interbedding_thick_unit,
            fallback_classification=current_fallback_classification,
            bit_size_mm=current_bit_size_mm,
            show_anomaly_highlights=current_show_anomaly_highlights,
            casing_depth_enabled=current_casing_depth_enabled,
            casing_depth_m=current_casing_depth_m,
            disable_svg=self.disable_svg,
            avg_executable_path=self.avg_executable_path,
            svg_directory_path=self.svg_directory_path,
            workspace_state=workspace_state,
            theme=self.current_theme,
            column_visibility=self.column_visibility,
            curve_visibility=current_curve_visibility,
            pane_visibility=self.pane_visibility
        )

        # Update instance variables to ensure smart interbedding uses current values
        self.smart_interbedding = current_smart_interbedding
        self.smart_interbedding_max_sequence_length = current_smart_interbedding_max_sequence
        self.smart_interbedding_thick_unit_threshold = current_smart_interbedding_thick_unit
        self.use_fallback_classification = current_fallback_classification
        self.bit_size_mm = current_bit_size_mm
        self.show_anomaly_highlights = current_show_anomaly_highlights
        self.casing_depth_enabled = current_casing_depth_enabled
        self.casing_depth_m = current_casing_depth_m

        if not auto_save: # Only show message if triggered by the "Update Settings" button
            pass
            # Clear the dirty flag since settings have been saved
            self.settings_dirty = False
            # Update the "Update Settings" button text to remove the asterisk
            if hasattr(self, 'updateSettingsButton'):
                self.updateSettingsButton.setText("Update Settings")

            QMessageBox.information(self, "Settings Updated", "All settings have been updated and saved.")

            # Reload settings to ensure UI reflects saved state (only for manual updates)
            app_settings = load_settings()
            self.lithology_rules = app_settings["lithology_rules"]
            self.initial_separator_thickness = app_settings["separator_thickness"]
            self.initial_draw_separators = app_settings["draw_separator_lines"]
            self.initial_curve_inversion_settings = app_settings["curve_inversion_settings"]
            self.initial_curve_thickness = app_settings["curve_thickness"] # Reload new setting
            self.use_researched_defaults = app_settings["use_researched_defaults"]
            # useResearchedDefaultsCheckBox only exists in SettingsDialog, not MainWindow
            self.analysis_method = app_settings.get("analysis_method", "standard")
            self.bit_size_mm = app_settings.get("bit_size_mm", 150.0)
            self.casing_depth_enabled = app_settings.get("casing_depth_enabled", False)
            self.casing_depth_m = app_settings.get("casing_depth_m", 0.0)
            self.load_settings_rules_to_table()
            # self.# load_separator_settings()  # Removed - legacy code  # Removed - legacy code
            # self.# load_curve_thickness_settings()  # Removed - legacy code  # Removed - legacy code # Reload new setting
            # self.# load_curve_inversion_settings()  # Removed - legacy code  # Removed - legacy code
            # Note: Settings UI widgets only exist in SettingsDialog
            # The values are stored in attributes and will be used when SettingsDialog is opened


    def load_settings_from_file(self):
        pass
#         print(f"[DEBUG] MainWindow.load_settings_from_file called")
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Settings", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            print(f"[DEBUG] Loading settings from {file_path}")
            try:
                loaded_settings = load_settings(file_path) # Pass file_path to load_settings
#                 print(f"[DEBUG] Loaded settings keys: {list(loaded_settings.keys())}")
                self.lithology_rules = loaded_settings["lithology_rules"]
                self.initial_separator_thickness = loaded_settings["separator_thickness"]
                self.initial_draw_separators = loaded_settings["draw_separator_lines"]
                self.initial_curve_inversion_settings = loaded_settings["curve_inversion_settings"] # Load new setting
                self.initial_curve_thickness = loaded_settings["curve_thickness"] # Load new setting
                self.use_researched_defaults = loaded_settings["use_researched_defaults"]
                # Load additional settings
                self.analysis_method = loaded_settings.get("analysis_method", "standard")
                self.merge_thin_units = loaded_settings.get("merge_thin_units", False)
                self.merge_threshold = loaded_settings.get("merge_threshold", 0.05)
                self.smart_interbedding = loaded_settings.get("smart_interbedding", False)
                self.smart_interbedding_max_sequence_length = loaded_settings.get("smart_interbedding_max_sequence_length", 10)
                self.smart_interbedding_thick_unit_threshold = loaded_settings.get("smart_interbedding_thick_unit_threshold", 0.5)
                self.use_fallback_classification = loaded_settings.get("fallback_classification", DEFAULT_FALLBACK_CLASSIFICATION)
                self.bit_size_mm = loaded_settings.get("bit_size_mm", 150.0)
                self.show_anomaly_highlights = loaded_settings.get("show_anomaly_highlights", True)
                self.casing_depth_enabled = loaded_settings.get("casing_depth_enabled", False)
                self.casing_depth_m = loaded_settings.get("casing_depth_m", 0.0)
                self.column_visibility = loaded_settings.get("column_visibility", {})
                self.curve_visibility = loaded_settings.get("curve_visibility", {})
                self.pane_visibility = loaded_settings.get("pane_visibility", {
                    "file_explorer": True,
                    "las_curves": True,
                    "enhanced_stratigraphic": True,
                    "data_editor": True,
                    "overview_stratigraphic": True
                })
                self.disable_svg = loaded_settings.get("disable_svg", False)
                self.avg_executable_path = loaded_settings.get("avg_executable_path", "")
                self.svg_directory_path = loaded_settings.get("svg_directory_path", "")

                # Update UI controls
                # useResearchedDefaultsCheckBox only exists in SettingsDialog, not MainWindow
                # Note: Settings UI widgets only exist in SettingsDialog
                # The values are stored in attributes and will be used when SettingsDialog is opened
                self.apply_column_visibility(self.column_visibility)

                self.load_settings_rules_to_table()
                # self.# load_separator_settings()  # Removed - legacy code  # Removed - legacy code
                # self.# load_curve_thickness_settings()  # Removed - legacy code  # Removed - legacy code # Reload new setting
                # self.# load_curve_inversion_settings()  # Removed - legacy code  # Removed - legacy code # Load new setting
                self._apply_researched_defaults_if_needed() # Call new method after loading settings
                # Update plotter with new bit size and anomaly visibility
                self.update_plotter_bit_size()
                self.update_plotter_anomaly_visibility()
                # Clear the dirty flag since we just loaded fresh settings
                self.settings_dirty = False
                # Update the "Update Settings" button text to remove the asterisk
                if hasattr(self, 'updateSettingsButton'):
                    self.updateSettingsButton.setText("Update Settings")
                QMessageBox.information(self, "Settings Loaded", f"Settings loaded from {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load settings: {e}")

    def update_plotter_bit_size(self):
        """Update plotter with current bit size for anomaly detection."""
        # Settings UI widgets only exist in SettingsDialog, use attribute value directly
        bit_size_mm = self.bit_size_mm
        # Update plotter if it exists
        if hasattr(self, 'curvePlotter') and hasattr(self.curvePlotter, 'set_bit_size'):
            self.curvePlotter.set_bit_size(bit_size_mm)
        # Also update any hole editor plotters
        if hasattr(self, 'mdi_area'):
            for subwindow in self.mdi_area.subWindowList():
                widget = subwindow.widget()
                if hasattr(widget, 'curvePlotter') and hasattr(widget.curvePlotter, 'set_bit_size'):
                    widget.curvePlotter.set_bit_size(bit_size_mm)

    def update_plotter_anomaly_visibility(self):
        """Update plotter with current anomaly visibility setting."""
        # Settings UI widgets only exist in SettingsDialog, use attribute value directly
        show_anomaly = self.show_anomaly_highlights
        # Update plotter if it exists and has the method
        if hasattr(self, 'curvePlotter') and hasattr(self.curvePlotter, 'set_anomaly_highlight_visible'):
            self.curvePlotter.set_anomaly_highlight_visible(show_anomaly)
        # Also update any hole editor plotters
        if hasattr(self, 'mdi_area'):
            for subwindow in self.mdi_area.subWindowList():
                widget = subwindow.widget()
                if hasattr(widget, 'curvePlotter') and hasattr(widget.curvePlotter, 'set_anomaly_highlight_visible'):
                    widget.curvePlotter.set_anomaly_highlight_visible(show_anomaly)

    def closeEvent(self, event):
        pass
        # Save window geometry and settings automatically when the application closes
        self.save_window_geometry()
        self.update_settings(auto_save=True)
        super().closeEvent(event)

    def save_window_geometry(self):
        """Save current window size and position to settings."""
        from PyQt6.QtCore import QRect

        # Get current window geometry
        geometry = self.geometry()
        is_maximized = self.isMaximized()

        # Prepare geometry data
        geometry_data = {
            'x': geometry.x(),
            'y': geometry.y(),
            'width': geometry.width(),
            'height': geometry.height(),
            'maximized': is_maximized
        }

        # Load current settings and add geometry
        try:
            app_settings = load_settings()
            app_settings['window_geometry'] = geometry_data

            # Save updated settings
            from ..core.settings_manager import DEFAULT_SETTINGS_FILE
            import json
            os.makedirs(os.path.dirname(DEFAULT_SETTINGS_FILE), exist_ok=True)
            with open(DEFAULT_SETTINGS_FILE, 'w') as f:
                json.dump(app_settings, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save window geometry: {e}")

    def on_tab_changed(self, index):
        pass
        # Remove redundant save when switching tabs
        # if self.tab_widget.tabText(index) != "Settings":
        #     self.save_settings_rules_from_table()
        pass # No automatic saving on tab change anymore

    def load_settings_rules_to_table(self):
        """Settings dock removed - lithology rules are managed by SettingsDialog."""
        # No-op: rules are already stored in self.lithology_rules
        pass

    def save_settings_rules_from_table(self, show_message=True):
        """Settings dock removed - lithology rules are managed by SettingsDialog."""
        # No-op: rules are already stored in self.lithology_rules
        pass

    def create_actions_widget(self, row):
        """Create a widget with edit/delete buttons for the Actions column."""
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

        actions_widget = QWidget()
        layout = QHBoxLayout(actions_widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Edit button (could be used for advanced editing)
        edit_button = QPushButton("✏")
        edit_button.setFixedSize(20, 20)
        edit_button.setToolTip("Edit rule details")
        edit_button.clicked.connect(lambda: self.edit_rule(row))
        layout.addWidget(edit_button)

        # Delete button
        delete_button = QPushButton("🗑")
        delete_button.setFixedSize(20, 20)
        delete_button.setToolTip("Delete this rule")
        delete_button.clicked.connect(lambda: self.remove_settings_rule())
        layout.addWidget(delete_button)

        # Status indicator (could show validation status)
        status_label = QLabel("✓")
        status_label.setFixedSize(20, 20)
        status_label.setStyleSheet("color: green; font-weight: bold;")
        status_label.setToolTip("Rule is valid")
        layout.addWidget(status_label)

        return actions_widget

    def update_range_values(self, row, range_type, min_val, max_val):
        """Update range values from CompactRangeWidget signals and trigger visualization refresh."""
        # This method handles the signals from CompactRangeWidget
        # The actual value extraction happens in save_settings_rules_from_table

        # Trigger real-time gap visualization update with debouncing
        self._schedule_gap_visualization_update()

    def update_visual_properties(self, row, properties):
        """Update visual properties from MultiAttributeWidget signals."""
        # This method handles the signals from MultiAttributeWidget
        # The actual value extraction happens in save_settings_rules_from_table
        pass  # Values will be retrieved when saving

    def edit_rule(self, row):
        """Handle advanced editing of a rule (placeholder for future expansion)."""
        # Could open a comprehensive rule editor dialog
        QMessageBox.information(self, "Edit Rule", f"Advanced editing for rule {row + 1} (feature coming soon)")

    def add_dropdown_to_table(self, row, col, items, current_text=''):
        combo = QComboBox()
        combo.addItems(items)
        if current_text in items:
            combo.setCurrentText(current_text)
        self.settings_rules_table.setCellWidget(row, col, combo)

    def add_settings_rule(self):
        row_position = self.settings_rules_table.rowCount()
        self.settings_rules_table.insertRow(row_position)

        # Column 0: Name (editable text)
        name_item = QTableWidgetItem("")
        self.settings_rules_table.setItem(row_position, 0, name_item)

        # Column 1: Code (read-only)
        self.settings_rules_table.setItem(row_position, 1, QTableWidgetItem(""))
        self.settings_rules_table.item(row_position, 1).setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

        # Column 2: Qualifier (QComboBox)
        qual_combo = QComboBox()
        self.settings_rules_table.setCellWidget(row_position, 2, qual_combo)
        qual_combo.currentTextChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed

        # Column 3: Gamma Range (CompactRangeWidget)
        gamma_widget = CompactRangeWidget()
        gamma_widget.set_values(0.0, 0.0)
        gamma_widget.valuesChanged.connect(lambda min_val, max_val, r=row_position: self.update_range_values(r, 'gamma', min_val, max_val))
        gamma_widget.valuesChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed
        self.settings_rules_table.setCellWidget(row_position, 3, gamma_widget)

        # Column 4: Density Range (CompactRangeWidget)
        density_widget = CompactRangeWidget()
        density_widget.set_values(0.0, 0.0)
        density_widget.valuesChanged.connect(lambda min_val, max_val, r=row_position: self.update_range_values(r, 'density', min_val, max_val))
        density_widget.valuesChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed
        self.settings_rules_table.setCellWidget(row_position, 4, density_widget)

        # Column 5: Visual Props (MultiAttributeWidget)
        visual_widget = MultiAttributeWidget(coallog_data=self.coallog_data)
        visual_widget.set_properties({
            'shade': '',
            'hue': '',
            'colour': '',
            'weathering': '',
            'strength': ''
        })
        visual_widget.propertiesChanged.connect(lambda props, r=row_position: self.update_visual_properties(r, props))
        visual_widget.propertiesChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed
        self.settings_rules_table.setCellWidget(row_position, 5, visual_widget)

        # Column 6: Background (QPushButton)
        color_button = QPushButton()
        color_button.setStyleSheet("background-color: #FFFFFF")
        color_button.clicked.connect(lambda _, r=row_position: self.open_color_picker(r))
        self.settings_rules_table.setCellWidget(row_position, 6, color_button)

        # Column 7: Preview (EnhancedPatternPreview)
        preview_widget = EnhancedPatternPreview()
        self.settings_rules_table.setCellWidget(row_position, 7, preview_widget)

        # Column 8: Actions (QWidget with buttons)
        actions_widget = self.create_actions_widget(row_position)
        self.settings_rules_table.setCellWidget(row_position, 8, actions_widget)

    def on_settings_cell_changed(self, row, column):
        """Handle cell changes in the settings rules table."""
        if column == 0:  # Name column changed
            item = self.settings_rules_table.item(row, column)
            if not item:
                return
            name = item.text().strip()
            
            # Block signals to prevent recursion
            self.settings_rules_table.blockSignals(True)
            
            # Update lithology code based on name
            matches = self.coallog_data['Litho_Type'].loc[self.coallog_data['Litho_Type']['Description'] == name, 'Code']
            if not matches.empty:
                litho_code = matches.iloc[0]
                self.settings_rules_table.setItem(row, 1, QTableWidgetItem(litho_code))
            else:
                # Clear code if description not found
                self.settings_rules_table.setItem(row, 1, QTableWidgetItem(""))
            
            # Restore signals
            self.settings_rules_table.blockSignals(False)
            
            # Update qualifier dropdown
            # Get current qualifier code from column 2 combobox
            qual_combo = self.settings_rules_table.cellWidget(row, 2)
            current_qualifier = None
            if isinstance(qual_combo, QComboBox):
                current_qualifier = qual_combo.currentData(Qt.ItemDataRole.UserRole)
                if current_qualifier is None:
                    current_qualifier = qual_combo.currentText()
            self.update_qualifier_dropdown(row, name, current_qualifier)
            
            # Update rule preview
            self.update_rule_preview(row)
            
            # Mark settings as dirty
            self.mark_settings_dirty()

    def update_litho_code(self, text):
        sender = self.sender()
        if sender:
            row = self.settings_rules_table.indexAt(sender.pos()).row()
            # Look up lithology code from description
            matches = self.coallog_data['Litho_Type'].loc[self.coallog_data['Litho_Type']['Description'] == text, 'Code']
            if not matches.empty:
                litho_code = matches.iloc[0]
                self.settings_rules_table.setItem(row, 1, QTableWidgetItem(litho_code))
            else:
                # Clear code if description not found
                self.settings_rules_table.setItem(row, 1, QTableWidgetItem(""))

    def update_qualifier_dropdown(self, row, selected_litho_name, current_qualifier_code=None):
        pass
        # Find the corresponding litho code
        litho_code = None
        litho_type_df = self.coallog_data.get('Litho_Type')
        if litho_type_df is not None:
            match = litho_type_df[litho_type_df['Description'] == selected_litho_name]
            if not match.empty:
                litho_code = match['Code'].iloc[0]

        qual_combo = self.settings_rules_table.cellWidget(row, 2)
        if not isinstance(qual_combo, QComboBox):
            return
        
        # Ensure combobox is editable so we can show code instead of description
        if not qual_combo.isEditable():
            qual_combo.setEditable(True)

        # Use provided qualifier code or current selection
        if current_qualifier_code is None:
            current_qualifier_code = qual_combo.currentData(Qt.ItemDataRole.UserRole) # Get the currently selected code
        
        qual_combo.clear()

        qual_combo.addItem("", "") # Add a blank option with empty code

        if litho_code:
            litho_info = self.lithology_qualifier_map.get(litho_code, {})
            qualifiers = litho_info.get('qualifiers', {})
            if qualifiers:
                pass
                # Qualifiers are a dict of {code: description}
                for code, description in qualifiers.items():
                    qual_combo.addItem(description, code) # Display description, store code as UserRole data

        # Try to restore the previous selection by code
        index = qual_combo.findData(current_qualifier_code, Qt.ItemDataRole.UserRole)
        if index != -1:
            qual_combo.setCurrentIndex(index)
            qual_combo.setEditText(current_qualifier_code)  # Show code, not description
        else:
            qual_combo.setCurrentIndex(0) # Select the blank item if not found
            if current_qualifier_code:
                qual_combo.setEditText(current_qualifier_code)  # Show custom qualifier
        
        # Connect index change to update edit text
        # Disconnect existing connections to avoid duplicates
        try:
            qual_combo.currentIndexChanged.disconnect()
        except:
            pass
        qual_combo.currentIndexChanged.connect(lambda idx, r=row, c=qual_combo: self.on_qualifier_index_changed(r, c))
    
    def on_qualifier_index_changed(self, row, combo):
        """Update combobox edit text to show code, not description."""
        current_data = combo.currentData()
        if current_data is not None:
            combo.setEditText(current_data)

    def remove_settings_rule(self):
        current_row = self.settings_rules_table.currentRow()
        if current_row >= 0:
            self.settings_rules_table.removeRow(current_row)
            self.mark_settings_dirty()  # Mark as dirty when rule is removed
        self.save_settings_rules_from_table()

    def open_color_picker(self, row):
        pass
        # Column 6: Background color button
        button = self.settings_rules_table.cellWidget(row, 6)
        initial_color = QColor(button.styleSheet().split(':')[-1].strip())
        color = QColorDialog.getColor(initial_color, self)
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")
            self.update_rule_preview(row)
            self.mark_settings_dirty()  # Mark as dirty when color is changed

    def update_rule_preview(self, row):
        litho_code_item = self.settings_rules_table.item(row, 1)
        if not litho_code_item:
            return
        litho_code = litho_code_item.text()

        qual_combo = self.settings_rules_table.cellWidget(row, 2)
        litho_qualifier = qual_combo.currentData(Qt.ItemDataRole.UserRole) if isinstance(qual_combo, QComboBox) else ''

        svg_file = self.find_svg_file(litho_code, litho_qualifier)
        # Column 6: Background color button
        color_button = self.settings_rules_table.cellWidget(row, 6)
        color = QColor(color_button.styleSheet().split(':')[-1].strip()) if color_button else QColor('#FFFFFF')
        # Column 7: Preview widget
        preview_widget = self.settings_rules_table.cellWidget(row, 7)
        if preview_widget and hasattr(preview_widget, 'update_preview'):
            preview_widget.update_preview(svg_path=svg_file, background_color=color.name())

    def setup_editor_tab(self):
        self.editor_tab_layout = QVBoxLayout(self.editor_tab)

        # 1. Create the Splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 2. Left Container (LAS/Gamma Ray Curves)
        curves_container = QWidget()
        curves_layout = QVBoxLayout(curves_container)
        curves_layout.setContentsMargins(0, 0, 0, 0)
        curves_layout.addWidget(self.curvePlotter)

        # 3. Middle Container (Stratigraphic Column)
        strat_container = QWidget()
        strat_layout = QVBoxLayout(strat_container)
        strat_layout.setContentsMargins(0, 0, 0, 0)
        strat_layout.addWidget(self.stratigraphicColumnView)

        # 4. Right Container (Editor Table)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.addWidget(self.editorTable)

        # 5. Add to Splitter & Set defaults (3 adjacent panels)
        self.main_splitter.addWidget(curves_container)
        self.main_splitter.addWidget(strat_container)
        self.main_splitter.addWidget(table_container)
        self.main_splitter.setStretchFactor(0, 1) # Curves area
        self.main_splitter.setStretchFactor(1, 1) # Strat column area
        self.main_splitter.setStretchFactor(2, 1) # Table area

        # 6. Create a container for the main content and zoom controls
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout(main_content_widget)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(5)

        # Add Splitter to the content layout
        main_content_layout.addWidget(self.main_splitter)

        # Add the main content widget to the editor tab layout
        self.editor_tab_layout.addWidget(main_content_widget)

        # Initialize empty table
        # Note: setRowCount is not needed for QTableView with PandasModel
        # The model will handle row count automatically
        self.editorTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def apply_synchronized_zoom(self, zoom_factor):
        """Apply the same zoom factor to both curve plotter and stratigraphic column."""
        self.curvePlotter.set_zoom_level(zoom_factor)
        self.stratigraphicColumnView.set_zoom_level(zoom_factor)

    def populate_editor_table(self, dataframe):
        """Populate the editor table with dataframe content."""
        # Use the LithologyTableWidget's load_data method which now uses PandasModel
        self.editorTable.load_data(dataframe)
        # Apply column visibility settings
        self.apply_column_visibility(self.column_visibility)

    def export_editor_data_to_csv(self):
        if self.editorTable.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No data to export in the editor tab.")
            return
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv);;All Files (*)")
        if file_path:
            try:
                # Get data directly from the model's dataframe
                df_to_export = self.editorTable.get_dataframe()
                if df_to_export is None:
                    QMessageBox.warning(self, "Export Error", "No data to export.")
                    return
                df_to_export.to_csv(file_path, index=False)
                QMessageBox.information(self, "Export Successful", f"Data exported to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data: {e}")

    def run_analysis(self):
        print(f"DEBUG (run_analysis): starting analysis for {self.las_file_path}")
        if not self.las_file_path:
            QMessageBox.warning(self, "No LAS File", "Please load an LAS file first.")
            return
        if not self.lithology_rules:
            QMessageBox.warning(self, "No Lithology Rules", "Please define lithology rules in settings first.")
            return

        # Check if settings are dirty and prompt user (Phase 5 Task 5.2.3)
        if hasattr(self, 'settings_dirty') and self.settings_dirty:
            reply = QMessageBox.question(
                self,
                "Unsaved Settings",
                "Settings have been modified but not saved. Apply changes before running analysis?",
                QMessageBox.StandardButton.Apply | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Apply
            )

            if reply == QMessageBox.StandardButton.Apply:
                pass
                # Apply changes: save settings and clear dirty flag
                self.update_settings(auto_save=False)
            elif reply == QMessageBox.StandardButton.Discard:
                pass
                # Discard changes: revert to saved settings
                self.revert_to_saved_settings()
            elif reply == QMessageBox.StandardButton.Cancel:
                pass
                # Cancel analysis
                return
            # If user clicked Apply or Discard, continue with analysis
        # Short Space Density selection maps to both density fields
        density_selection = self.shortSpaceDensityComboBox.currentText()
        # Keep hidden combo box synchronized for backward compatibility
        self.densityComboBox.setCurrentText(density_selection)

        mnemonic_map = {
            'gamma': self.gammaRayComboBox.currentText(),
            'density': density_selection,  # Use Short Space Density selection
            'short_space_density': density_selection,  # Same as density
            'long_space_density': self.longSpaceDensityComboBox.currentText(),
            'caliper': self.caliperComboBox.currentText(),
            'resistivity': self.resistivityComboBox.currentText()
        }
        # Allow empty/None selection for curves
        # if not mnemonic_map['gamma'] or not mnemonic_map['density']:
        #     QMessageBox.warning(self, "Missing Curve Mapping", "Please select both Gamma Ray and Density curves.")
        #     return
        # Ensure lithology rules are up-to-date from the settings table before running analysis
        self.save_settings_rules_from_table(show_message=False)

        self.thread = QThread()
        # Pass mnemonic_map to the Worker
        # Settings UI widgets only exist in SettingsDialog, use attribute values directly
        use_fallback_classification = self.use_fallback_classification
        analysis_method = self.analysis_method
        casing_depth_enabled = self.casing_depth_enabled
        casing_depth_m = self.casing_depth_m

        self.worker = Worker(self.las_file_path, mnemonic_map, self.lithology_rules, self.use_researched_defaults, self.merge_thin_units, self.merge_threshold, self.smart_interbedding, self.smart_interbedding_max_sequence_length, self.smart_interbedding_thick_unit_threshold, use_fallback_classification, analysis_method, casing_depth_enabled, casing_depth_m)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.error.connect(self.analysis_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.runAnalysisButton.setEnabled(False)
        QMessageBox.information(self, "Analysis Started", "Running analysis in background...")
        self.thread.start()

    def analysis_finished(self, units_dataframe, classified_dataframe):
        print(f"DEBUG (analysis_finished): called with units shape {units_dataframe.shape}, classified shape {classified_dataframe.shape}")
        self.runAnalysisButton.setEnabled(True)

        # Store recent analysis results for reporting
        self.last_classified_dataframe = classified_dataframe.copy()
        self.last_units_dataframe = units_dataframe.copy()
        self.last_analysis_file = self.las_file_path
        self.last_analysis_timestamp = pd.Timestamp.now()

        # Debug: check columns
        print(f"DEBUG (analysis_finished): units_dataframe columns: {list(units_dataframe.columns)}")
        print(f"DEBUG (analysis_finished): background_color in columns? {'background_color' in units_dataframe.columns}")
        print(f"DEBUG (analysis_finished): svg_path in columns? {'svg_path' in units_dataframe.columns}")
        print(f"DEBUG (analysis_finished): units_dataframe shape: {units_dataframe.shape}")
        print(f"DEBUG (analysis_finished): classified_dataframe shape: {classified_dataframe.shape}")
        if not units_dataframe.empty:
            print(f"DEBUG (analysis_finished): First few units:")
            for idx in range(min(5, len(units_dataframe))):
                unit = units_dataframe.iloc[idx]
                print(f"  [{idx}] lithology={unit.get(LITHOLOGY_COLUMN, 'N/A')}, background_color={unit.get('background_color', 'MISSING')}, svg_path={unit.get('svg_path', 'MISSING')}")
        else:
            print(f"DEBUG (analysis_finished): units_dataframe is EMPTY!")

        # Check for smart interbedding suggestions if enabled
#         print(f"DEBUG: Smart interbedding enabled check: {self.smart_interbedding}")
        if self.smart_interbedding:
            self._check_smart_interbedding_suggestions(units_dataframe, classified_dataframe)
        else:
            self._finalize_analysis_display(units_dataframe, classified_dataframe)

    def analysis_error(self, message):
        self.runAnalysisButton.setEnabled(True)
        QMessageBox.critical(self, "Analysis Error", message)

    def _apply_researched_defaults_if_needed(self):
        """
        Checks lithology rules for zero/blank gamma/density ranges and prompts the user
        to apply researched defaults if available. Updates self.lithology_rules and
        refreshes the settings table.
        Respects the use_researched_defaults setting.
        """
        if not self.use_researched_defaults:
            return  # Skip applying defaults if user has disabled this feature

        from ..core.config import RESEARCHED_LITHOLOGY_DEFAULTS

        rules_updated = False
        for rule_idx, rule in enumerate(self.lithology_rules):
            code = rule.get('code')

            # Check if this lithology code has researched defaults
            if code in RESEARCHED_LITHOLOGY_DEFAULTS:
                researched_defaults = RESEARCHED_LITHOLOGY_DEFAULTS[code]

                # Check gamma ranges - zeros or missing
                gamma_missing = (rule.get('gamma_min', INVALID_DATA_VALUE) == INVALID_DATA_VALUE and
                                rule.get('gamma_max', INVALID_DATA_VALUE) == INVALID_DATA_VALUE) or \
                               (rule.get('gamma_min', 0.0) == 0.0 and rule.get('gamma_max', 0.0) == 0.0)

                # Check density ranges - zeros or missing
                density_missing = (rule.get('density_min', INVALID_DATA_VALUE) == INVALID_DATA_VALUE and
                                  rule.get('density_max', INVALID_DATA_VALUE) == INVALID_DATA_VALUE) or \
                                 (rule.get('density_min', 0.0) == 0.0 and rule.get('density_max', 0.0) == 0.0)

                # Determine if we need to prompt user
                gamma_prompt = gamma_missing and 'gamma_min' in researched_defaults and 'gamma_max' in researched_defaults
                density_prompt = density_missing and 'density_min' in researched_defaults and 'density_max' in researched_defaults

                if gamma_prompt or density_prompt:
                    pass
                    # Build prompt message
                    prompt_text = f"The ranges for '{rule.get('name', code)}' are currently zero/blank.\n"
                    prompt_text += "Would you like to apply researched default ranges?\n\n"

                    if gamma_prompt:
                        prompt_text += f"Gamma: {researched_defaults.get('gamma_min', 'N/A')} - {researched_defaults.get('gamma_max', 'N/A')}\n"
                    if density_prompt:
                        prompt_text += f"Density: {researched_defaults.get('density_min', 'N/A')} - {researched_defaults.get('density_max', 'N/A')}\n"

                    reply = QMessageBox.question(self, "Apply Researched Defaults", prompt_text,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                    if reply == QMessageBox.StandardButton.Yes:
                        if gamma_missing and gamma_prompt:
                            rule['gamma_min'] = researched_defaults['gamma_min']
                            rule['gamma_max'] = researched_defaults['gamma_max']
                        if density_missing and density_prompt:
                            rule['density_min'] = researched_defaults['density_min']
                            rule['density_max'] = researched_defaults['density_max']
                        rules_updated = True

        if rules_updated:
            self.load_settings_rules_to_table() # Refresh the table to show updated values
            self.update_settings(auto_save=True) # Save the updated settings to file
            QMessageBox.information(self, "Defaults Applied", "Researched default ranges have been applied and saved.")

    def open_researched_defaults_dialog(self):
        """Opens a dialog to display researched default lithology ranges."""
        dialog = ResearchedDefaultsDialog(self)
        dialog.exec()

    def open_column_configurator_dialog(self):
        """Open the column configurator dialog to hide/show columns."""
        dialog = ColumnConfiguratorDialog(self, main_window=self, current_visibility=self.column_visibility)
        dialog.visibility_changed.connect(self.on_column_visibility_changed)
        dialog.exec()

    def open_nl_review_dialog(self):
        """Open the NL review dialog to analyze 'Not Logged' intervals."""
        dialog = NLReviewDialog(self, main_window=self)
        dialog.exec()

    def on_column_visibility_changed(self, visibility_map):
        """Handle column visibility changes from configurator dialog."""
        print(f"DEBUG: on_column_visibility_changed called with {len(visibility_map)} columns")
        # Update stored visibility
        self.column_visibility = visibility_map

        # Apply visibility to table
        self.apply_column_visibility(visibility_map)

        # Save settings with updated column visibility
        self.update_settings(auto_save=True)

        # Show confirmation
        visible_count = sum(1 for v in visibility_map.values() if v)
        hidden_count = len(visibility_map) - visible_count
        QMessageBox.information(
            self,
            "Columns Updated",
            f"Column visibility applied:\n"
            f"• {visible_count} columns visible\n"
            f"• {hidden_count} columns hidden\n\n"
            f"Changes have been saved to settings."
        )

    def apply_column_visibility(self, visibility_map):
        """Apply column visibility mapping to all lithology tables."""
#         print(f"DEBUG: apply_column_visibility called, editorTable exists? {hasattr(self, 'editorTable')}, model? {self.editorTable.model() if hasattr(self, 'editorTable') else None}")
        # Apply to main editor table (first hole)
        if hasattr(self, 'editorTable') and self.editorTable.model() is not None:
            self._apply_visibility_to_table(self.editorTable, visibility_map)

        # Apply to all hole editor windows in MDI area
        if hasattr(self, 'mdi_area'):
            for subwindow in self.mdi_area.subWindowList():
                widget = subwindow.widget()
                if hasattr(widget, 'editorTable') and widget.editorTable.model() is not None:
                    self._apply_visibility_to_table(widget.editorTable, visibility_map)

    def _apply_visibility_to_table(self, table, visibility_map):
        """Apply visibility mapping to a specific table."""
        model = table.model()
        if not hasattr(model, '_dataframe'):
            print(f"DEBUG: model has no _dataframe attribute")
            return

        column_names = model._dataframe.columns.tolist()
#         print(f"DEBUG: column_names ({len(column_names)}): {column_names}")

        # Check if table has col_map (LithologyTableWidget mapping)
        col_map = getattr(table, 'col_map', None)
        if col_map:
            print(f"DEBUG: table has col_map with {len(col_map)} entries")

        # Map internal names to column indices
        for internal_name, is_visible in visibility_map.items():
            col_index = None

            # 1. Try direct column name match
            if internal_name in column_names:
                col_index = column_names.index(internal_name)
#                 print(f"DEBUG: column '{internal_name}' found at index {col_index}")

            # 2. Try col_map if available
            if col_index is None and col_map and internal_name in col_map:
                col_index = col_map[internal_name]
                print(f"DEBUG: column '{internal_name}' mapped via col_map to index {col_index}")

            # 3. Try display name (replace underscores with spaces)
            if col_index is None:
                display_name = internal_name.replace('_', ' ').title()
                print(f"DEBUG: column '{internal_name}' not found, trying display name '{display_name}'")
                for idx, col in enumerate(column_names):
                    if col == internal_name or col == display_name:
                        col_index = idx
#                         print(f"DEBUG: matched column '{col}' at index {idx}")
                        break

            if col_index is not None:
                pass
                # Ensure column index is within table column count
                if 0 <= col_index < table.model().columnCount():
                    pass
#                     print(f"DEBUG: hiding column '{internal_name}' (index {col_index})? {not is_visible}")
                    table.setColumnHidden(col_index, not is_visible)
                else:
                    print(f"DEBUG: column index {col_index} out of range (0-{table.model().columnCount()-1})")
            else:
                print(f"DEBUG: column '{internal_name}' not found in table")

    def refresh_range_visualization(self):
        """Refresh the range gap visualization with current lithology rules"""
        # Get current rules from the table
        current_rules = []
        for row_idx in range(self.settings_rules_table.rowCount()):
            rule = {}
            name_item = self.settings_rules_table.item(row_idx, 0)
            rule['name'] = name_item.text() if name_item else ''
            rule['code'] = self.settings_rules_table.item(row_idx, 1).text() if self.settings_rules_table.item(row_idx, 1) else ''

            # Get gamma range from CompactRangeWidget (column 3)
            gamma_widget = self.settings_rules_table.cellWidget(row_idx, 3)
            if isinstance(gamma_widget, CompactRangeWidget):
                rule['gamma_min'], rule['gamma_max'] = gamma_widget.get_values()
            else:
                rule['gamma_min'], rule['gamma_max'] = 0.0, 0.0

            # Get density range from CompactRangeWidget (column 4)
            density_widget = self.settings_rules_table.cellWidget(row_idx, 4)
            if isinstance(density_widget, CompactRangeWidget):
                rule['density_min'], rule['density_max'] = density_widget.get_values()
            else:
                rule['density_min'], rule['density_max'] = 0.0, 0.0

            # Get background color for visualization (column 6)
            color_button = self.settings_rules_table.cellWidget(row_idx, 6)
            if color_button:
                rule['background_color'] = QColor(color_button.styleSheet().split(':')[-1].strip()).name()
            else:
                rule['background_color'] = '#FFFFFF'

            current_rules.append(rule)

        # Analyze ranges and update visualization with overlapping support
        gamma_covered, gamma_gaps = self.range_analyzer.analyze_gamma_ranges_with_overlaps(current_rules)
        density_covered, density_gaps = self.range_analyzer.analyze_density_ranges_with_overlaps(current_rules)

        self.range_visualizer.update_ranges(gamma_covered, gamma_gaps, density_covered, density_gaps, use_overlaps=True, lithology_rules=current_rules)

    def export_lithology_report(self):
        """Export a comprehensive lithology report with density statistics."""
        # Check if we have recent analysis data
        if self.last_classified_dataframe is None:
            QMessageBox.warning(self, "No Recent Analysis", "No recent analysis data available. Please run an analysis first.")
            return

        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "Export Lithology Report", "", "CSV Files (*.csv);;All Files (*)")
        if not file_path:
            return

        try:
            # Get current lithology rules from the table
            self.save_settings_rules_from_table(show_message=False)  # Ensure rules are current

            # Filter out NL from rules for reporting
            rules = [rule for rule in self.lithology_rules if rule.get('code', '').upper() != 'NL']

            # DataFrames for analysis
            classified_df = self.last_classified_dataframe.copy()
            units_df = self.last_units_dataframe.copy() if self.last_units_dataframe is not None else None

            # Calculate total rows for percentage calculations
            total_rows = len(classified_df)

            # Prepare report data
            report_data = []

            for rule in rules:
                rule_code = rule.get('code', '')
                rule_name = rule.get('name', '')
                rule_qualifier = rule.get('qualifier', '')

                # Use units dataframe to get more complete data if available
                classification_count = 0
                if units_df is not None and not units_df.empty:
                    pass
                    # Filter units by both code and qualifier for unique combinations
                    mask = (units_df[LITHOLOGY_COLUMN] == rule_code)
                    if rule_qualifier and 'lithology_qualifier' in units_df.columns:
                        mask = mask & (units_df['lithology_qualifier'] == rule_qualifier)

                    matching_units = units_df[mask]
                    if not matching_units.empty:
                        pass
                        # Calculate total thickness for this rule combination
                        thickness_col = RECOVERED_THICKNESS_COLUMN if RECOVERED_THICKNESS_COLUMN in matching_units.columns else ('thickness' if 'thickness' in matching_units.columns else None)
                        classification_count = matching_units.shape[0]  # Count of units, not rows
                    else:
                        # Fallback: check classified dataframe
                        classified_mask = (classified_df[LITHOLOGY_COLUMN] == rule_code)
                        classification_count = classified_mask.sum()
                else:
                    # Fallback: use classified dataframe only
                    classified_mask = (classified_df[LITHOLOGY_COLUMN] == rule_code)
                    classification_count = classified_mask.sum()

                classification_percentage = (classification_count / total_rows * 100) if total_rows > 0 else 0

                # Get density statistics by filtering classified dataframe
                density_stats = {}
                if 'short_space_density' in classified_df.columns:
                    pass
                    # Filter rows that match this rule's classification
                    density_mask = (classified_df[LITHOLOGY_COLUMN] == rule_code)
                    # Note: We can't easily filter by qualifier in classified dataframe since qualifier column doesn't exist there

                    densities = classified_df.loc[density_mask, 'short_space_density'].dropna()
                    if len(densities) > 0:
                        density_stats['associated_ssd_min'] = densities.min()
                        density_stats['associated_ssd_max'] = densities.max()
                        density_stats['associated_ssd_mean'] = densities.mean()
                        density_stats['associated_ssd_median'] = densities.median()
                    else:
                        density_stats['associated_ssd_min'] = None
                        density_stats['associated_ssd_max'] = None
                        density_stats['associated_ssd_mean'] = None
                        density_stats['associated_ssd_median'] = None

                # Build report row
                row = {
                    'lithology_name': rule_name,
                    'lithology_code': rule_code,
                    'lithology_qualifier': rule_qualifier if rule_qualifier else '',
                    'gamma_min': rule.get('gamma_min', None),
                    'gamma_max': rule.get('gamma_max', None),
                    'density_min': rule.get('density_min', None),
                    'density_max': rule.get('density_max', None),
                    'classification_count': classification_count,
                    'classification_percentage': round(classification_percentage, 2),
                    'associated_ssd_min': density_stats.get('associated_ssd_min'),
                    'associated_ssd_max': density_stats.get('associated_ssd_max'),
                    'associated_ssd_mean': round(density_stats.get('associated_ssd_mean'), 4) if density_stats.get('associated_ssd_mean') is not None else None,
                    'associated_ssd_median': round(density_stats.get('associated_ssd_median'), 4) if density_stats.get('associated_ssd_median') is not None else None,
                }

                report_data.append(row)

            # Enhanced NL Analysis Section
            nl_count = (classified_df[LITHOLOGY_COLUMN] == 'NL').sum()
            nl_percentage = (nl_count / total_rows * 100) if total_rows > 0 else 0

            if nl_count > 0:
                pass
                # Calculate density stats for NL classifications
                nl_densities = classified_df.loc[classified_df[LITHOLOGY_COLUMN] == 'NL', 'short_space_density'].dropna() if 'short_space_density' in classified_df.columns else pd.Series()

                nl_stats = {
                    'associated_ssd_min': nl_densities.min() if len(nl_densities) > 0 else None,
                    'associated_ssd_max': nl_densities.max() if len(nl_densities) > 0 else None,
                    'associated_ssd_mean': round(nl_densities.mean(), 4) if len(nl_densities) > 0 else None,
                    'associated_ssd_median': round(nl_densities.median(), 4) if len(nl_densities) > 0 else None,
                }

                # Add gamma stats for NL classifications
                nl_gammas = classified_df.loc[classified_df[LITHOLOGY_COLUMN] == 'NL', 'gamma'].dropna() if 'gamma' in classified_df.columns else pd.Series()
                if len(nl_gammas) > 0:
                    nl_stats.update({
                        'gamma_min': nl_gammas.min(),
                        'gamma_max': nl_gammas.max(),
                        'gamma_mean': round(nl_gammas.mean(), 4),
                        'gamma_median': round(nl_gammas.median(), 4),
                    })
                else:
                    nl_stats.update({
                        'gamma_min': None,
                        'gamma_max': None,
                        'gamma_mean': None,
                        'gamma_median': None,
                    })

                nl_row = {
                    'lithology_name': 'No Lithology (NL) - INVESTIGATE',
                    'lithology_code': 'NL',
                    'lithology_qualifier': 'N/A',
                    'gamma_min': 'See NL Analysis Section',
                    'gamma_max': 'See NL Analysis Section',
                    'density_min': nl_stats.get('associated_ssd_min'),
                    'density_max': nl_stats.get('associated_ssd_max'),
                    'classification_count': nl_count,
                    'classification_percentage': round(nl_percentage, 2),
                    'associated_ssd_min': nl_stats.get('associated_ssd_min'),
                    'associated_ssd_max': nl_stats.get('associated_ssd_max'),
                    'associated_ssd_mean': nl_stats.get('associated_ssd_mean'),
                    'associated_ssd_median': nl_stats.get('associated_ssd_median'),
                }
                report_data.append(nl_row)

                # Add NL Analysis Header
                nl_header_row = {
                    'lithology_name': '=== NL ANALYSIS SECTION ===',
                    'lithology_code': f'NL Count: {nl_count}',
                    'lithology_qualifier': f'NL %: {round(nl_percentage, 2)}%',
                    'gamma_min': f'Gamma Range: {nl_stats.get("gamma_min"):.1f} - {nl_stats.get("gamma_max"):.1f}' if nl_stats.get("gamma_min") is not None else 'Gamma Range: N/A',
                    'gamma_max': f'Mean: {nl_stats.get("gamma_mean"):.1f}' if nl_stats.get("gamma_mean") is not None else 'Mean: N/A',
                    'density_min': f'Density Range: {nl_stats.get("associated_ssd_min"):.3f} - {nl_stats.get("associated_ssd_max"):.3f}' if nl_stats.get("associated_ssd_min") is not None else 'Density Range: N/A',
                    'density_max': f'Mean: {nl_stats.get("associated_ssd_mean"):.3f}' if nl_stats.get("associated_ssd_mean") is not None else 'Mean: N/A',
                    'classification_count': 'Individual NL Data Points Below',
                    'classification_percentage': '',
                    'associated_ssd_min': '',
                    'associated_ssd_max': '',
                    'associated_ssd_mean': '',
                    'associated_ssd_median': '',
                }
                report_data.append(nl_header_row)

                # Add Column Headers for NL Data Points
                nl_data_header_row = {
                    'lithology_name': '=== INDIVIDUAL NL DATA POINTS ===',
                    'lithology_code': 'Row #',
                    'lithology_qualifier': 'Depth',
                    'gamma_min': 'Gamma (API)',
                    'gamma_max': 'Density (g/cc)',
                    'density_min': 'Lithology Code',
                    'density_max': '',
                    'classification_count': '',
                    'classification_percentage': '',
                    'associated_ssd_min': '',
                    'associated_ssd_max': '',
                    'associated_ssd_mean': '',
                    'associated_ssd_median': '',
                }
                report_data.append(nl_data_header_row)

                # Get NL rows with their data
                nl_rows = classified_df.loc[classified_df[LITHOLOGY_COLUMN] == 'NL'].copy()

                # Process NL rows in batches to show individual data points
                nl_batch_size = min(50, len(nl_rows))  # Show up to 50 individual NL points to keep report manageable

                for idx in range(min(nl_batch_size, len(nl_rows))):
                    row = nl_rows.iloc[idx]
                    nl_data_row = {
                        'lithology_name': f'NL_Data_Point_{idx+1}',
                        'lithology_code': str(idx+1),
                        'lithology_qualifier': round(float(row[DEPTH_COLUMN]), 3),
                        'gamma_min': round(float(row['gamma']), 2) if 'gamma' in row and pd.notna(row['gamma']) else 'N/A',
                        'gamma_max': round(float(row['short_space_density']), 4) if 'short_space_density' in row and pd.notna(row['short_space_density']) else 'N/A',
                        'density_min': 'NL',
                        'density_max': '',
                        'classification_count': '',
                        'classification_percentage': '',
                        'associated_ssd_min': '',
                        'associated_ssd_max': '',
                        'associated_ssd_mean': '',
                        'associated_ssd_median': '',
                    }
                    report_data.append(nl_data_row)

                # If there are more NL points than shown, add a summary
                if len(nl_rows) > nl_batch_size:
                    summary_row = {
                        'lithology_name': f'... and {len(nl_rows) - nl_batch_size} more NL data points',
                        'lithology_code': '',
                        'lithology_qualifier': '',
                        'gamma_min': '',
                        'gamma_max': '',
                        'density_min': '',
                        'density_max': '',
                        'classification_count': '',
                        'classification_percentage': '',
                        'associated_ssd_min': '',
                        'associated_ssd_max': '',
                        'associated_ssd_mean': '',
                        'associated_ssd_median': '',
                    }
                    report_data.append(summary_row)
            else:
                # No NL classifications - add standard NL row
                nl_row = {
                    'lithology_name': 'No Lithology (NL)',
                    'lithology_code': 'NL',
                    'lithology_qualifier': 'N/A',
                    'gamma_min': 'N/A',
                    'gamma_max': 'N/A',
                    'density_min': 'N/A',
                    'density_max': 'N/A',
                    'classification_count': 0,
                    'classification_percentage': 0.0,
                    'associated_ssd_min': None,
                    'associated_ssd_max': None,
                    'associated_ssd_mean': None,
                    'associated_ssd_median': None,
                }
                report_data.append(nl_row)

            # Add header row with metadata
            header_row = {
                'lithology_name': f'Report generated: {self.last_analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.last_analysis_timestamp else "Unknown"}',
                'lithology_code': f'Source file: {os.path.basename(self.last_analysis_file) if self.last_analysis_file else "Unknown"}',
                'lithology_qualifier': f'Total rows analyzed: {total_rows}',
                'gamma_min': '',
                'gamma_max': '',
                'density_min': '',
                'density_max': '',
                'classification_count': '',
                'classification_percentage': '',
                'associated_ssd_min': '',
                'associated_ssd_max': '',
                'associated_ssd_mean': '',
                'associated_ssd_median': '',
            }
            report_data.insert(0, header_row)

            # Convert to DataFrame and export
            report_df = pd.DataFrame(report_data)
            report_df.to_csv(file_path, index=False)

            QMessageBox.information(self, "Report Exported",
                f"Lithology report exported successfully!\n\n"
                f"File: {os.path.basename(file_path)}\n"
                f"Rules analyzed: {len(rules)}\n"
                f"Total classifications: {total_rows}\n\n"
                f"The report includes density statistics from the most recent analysis.")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export lithology report: {str(e)}")
            import traceback
            traceback.print_exc()

    def create_manual_interbedding(self):
        """Handle manual interbedding creation from selected table rows."""
        if self.last_units_dataframe is None or self.last_units_dataframe.empty:
            QMessageBox.warning(self, "No Data", "No lithology units available. Please run an analysis first.")
            return

        # Get selected rows from the table
        selected_rows = set()
        for index in self.editorTable.selectionModel().selectedIndexes():
            selected_rows.add(index.row())

        if len(selected_rows) < 2:
            QMessageBox.warning(self, "Selection Required", "Please select at least 2 consecutive lithology units to create interbedding.")
            return

        # Sort selected rows
        selected_rows = sorted(list(selected_rows))

        # Check if selected rows are consecutive
        if not self._are_rows_consecutive(selected_rows):
            QMessageBox.warning(self, "Invalid Selection", "Selected rows must be consecutive for interbedding.")
            return

        # Get the unit data for selected rows
        selected_units = []
        for row_idx in selected_rows:
            if row_idx < len(self.last_units_dataframe):
                unit_data = self.last_units_dataframe.iloc[row_idx].to_dict()
                selected_units.append(unit_data)

        # Open the interbedding dialog
        from .dialogs.interbedding_dialog import InterbeddingDialog
        dialog = InterbeddingDialog(selected_units, self)

        if dialog.exec():
            pass
            # Apply the interbedding changes
            interbedding_data = dialog.get_interbedding_data()
            self._apply_manual_interbedding(selected_rows, interbedding_data)

    def _are_rows_consecutive(self, row_indices):
        """Check if the given row indices are consecutive."""
        if not row_indices:
            return False

        sorted_indices = sorted(row_indices)
        for i in range(1, len(sorted_indices)):
            if sorted_indices[i] != sorted_indices[i-1] + 1:
                return False
        return True

    def _apply_manual_interbedding(self, selected_rows, interbedding_data):
        """Apply manual interbedding changes to the units dataframe."""
        if self.last_units_dataframe is None:
            return

        # Create a copy of the dataframe
        updated_df = self.last_units_dataframe.copy()

        # Remove the selected rows
        updated_df = updated_df.drop(selected_rows)

        # Reset index
        updated_df = updated_df.reset_index(drop=True)

        # Find insertion point (where the first selected row was)
        insert_idx = selected_rows[0]

        # Create new interbedded rows
        new_rows = []
        for lith in interbedding_data['lithologies']:
            pass
            # Find the rule for this lithology - ensure each lithology gets its own visual properties
            rule = None
            lith_code = lith['code'].upper() if lith['code'] else ''  # Normalize to uppercase
            for r in self.lithology_rules:
                rule_code = r.get('code', '').upper() if r.get('code') else ''  # Normalize to uppercase
                if rule_code == lith_code:
                    rule = r
                    break

            # If no rule found, create a default rule with basic properties
            if not rule:
                rule = {
                    'qualifier': '',
                    'shade': '',
                    'hue': '',
                    'colour': '',
                    'weathering': '',
                    'strength': '',
                    'background_color': '#FFFFFF',
                    'svg_path': self.find_svg_file(lith_code, '')
                }

            # Only the dominant lithology (sequence 1) gets the full thickness
            # Subordinate lithologies get 0 thickness since they're mixed in
            thickness = (interbedding_data['to_depth'] - interbedding_data['from_depth']) if lith['sequence'] == 1 else 0.0

            new_row = {
                'from_depth': interbedding_data['from_depth'],
                'to_depth': interbedding_data['to_depth'],
                'thickness': thickness,
                LITHOLOGY_COLUMN: lith['code'],
                'lithology_qualifier': rule.get('qualifier', ''),
                'shade': rule.get('shade', ''),
                'hue': rule.get('hue', ''),
                'colour': rule.get('colour', ''),
                'weathering': rule.get('weathering', ''),
                'estimated_strength': rule.get('strength', ''),
                'background_color': rule.get('background_color', '#FFFFFF'),
                'svg_path': rule.get('svg_path', self.find_svg_file(lith['code'], '')),
                RECORD_SEQUENCE_FLAG_COLUMN: lith['sequence'],
                INTERRELATIONSHIP_COLUMN: interbedding_data['interrelationship_code'] if lith['sequence'] == 1 else '',
                LITHOLOGY_PERCENT_COLUMN: lith['percentage']
            }
            new_rows.append(new_row)

        # Insert new rows at the correct position
        if insert_idx >= len(updated_df):
            pass
            # Append to end
            for new_row in new_rows:
                updated_df = updated_df.append(new_row, ignore_index=True)
        else:
            # Split dataframe and insert
            before = updated_df.iloc[:insert_idx]
            after = updated_df.iloc[insert_idx:]
            middle = pd.DataFrame(new_rows)
            updated_df = pd.concat([before, middle, after], ignore_index=True)

        # Update the stored dataframe
        self.last_units_dataframe = updated_df

        # Refresh the display - use 37-column schema
        # First ensure all columns are present
        for col in COALLOG_V31_COLUMNS:
            if col not in updated_df.columns:
                updated_df[col] = ''

        # Use the full 37-column schema
        editor_dataframe = updated_df[COALLOG_V31_COLUMNS]
        self.editorTable.load_data(editor_dataframe)
        # Apply column visibility settings
        self.apply_column_visibility(self.column_visibility)

        # Update curve plotter with lithology data for boundary lines (Phase 4)
        if hasattr(self.curvePlotter, 'set_lithology_data'):
            self.curvePlotter.set_lithology_data(editor_dataframe)

        # Update stratigraphic column
        if hasattr(self, 'stratigraphicColumnView'):
            pass
            # Settings UI widgets only exist in SettingsDialog, use attribute values directly
            separator_thickness = self.initial_separator_thickness
            draw_separators = self.initial_draw_separators
            if self.last_classified_dataframe is not None:
                min_depth = self.last_classified_dataframe[DEPTH_COLUMN].min()
                max_depth = self.last_classified_dataframe[DEPTH_COLUMN].max()
                self.stratigraphicColumnView.draw_column(updated_df, min_depth, max_depth, separator_thickness, draw_separators, disable_svg=self.disable_svg)
                if hasattr(self, 'enhancedStratColumnView'):
                    pass
                    # Set classified data for curve values in tooltips
                    self.enhancedStratColumnView.set_classified_data(self.last_classified_dataframe)
                    self.enhancedStratColumnView.draw_column(updated_df, min_depth, max_depth, separator_thickness, draw_separators, disable_svg=self.disable_svg)

        QMessageBox.information(self, "Interbedding Created", f"Successfully created interbedding with {len(new_rows)} components.")

    def _check_smart_interbedding_suggestions(self, units_dataframe, classified_dataframe):
        """Check for smart interbedding suggestions and show dialog if found."""
        try:
            # Debug: Method Entry
#             print("DEBUG: _check_smart_interbedding_suggestions method called")
            print(f"DEBUG: Smart interbedding enabled: {self.smart_interbedding}")
#             print(f"DEBUG: Max sequence length: {self.smart_interbedding_max_sequence_length}")
            print(f"DEBUG: Thick unit threshold: {self.smart_interbedding_thick_unit_threshold}")

            # Debug: Input Validation
            print(f"DEBUG: Units dataframe shape: {units_dataframe.shape if hasattr(units_dataframe, 'shape') else 'No shape'}")
#             print(f"DEBUG: Units dataframe columns: {list(units_dataframe.columns) if hasattr(units_dataframe, 'columns') else 'No columns'}")
            print(f"DEBUG: First 5 units: {units_dataframe.head() if hasattr(units_dataframe, 'head') else 'No head method'}")
#             print(f"DEBUG: Classified dataframe shape: {classified_dataframe.shape if hasattr(classified_dataframe, 'shape') else 'No shape'}")

            # Create analyzer instance for post-processing
            analyzer = Analyzer()

            # Find interbedding candidates
            max_sequence_length = self.smart_interbedding_max_sequence_length
            thick_unit_threshold = self.smart_interbedding_thick_unit_threshold

            print(f"DEBUG: Calling find_interbedding_candidates with max_sequence_length={max_sequence_length}, thick_unit_threshold={thick_unit_threshold}")
            candidates = analyzer.find_interbedding_candidates(
                units_dataframe,
                max_sequence_length=max_sequence_length,
                thick_unit_threshold=thick_unit_threshold
            )

#             print(f"DEBUG: Found {len(candidates) if candidates else 0} interbedding candidates")

            if candidates:
                print("DEBUG: Candidates found, creating SmartInterbeddingSuggestionsDialog")
                # Debug: Show candidate details
                for i, candidate in enumerate(candidates):
                    print(f"DEBUG: Candidate {i}: from_depth={candidate.get('from_depth')}, to_depth={candidate.get('to_depth')}, lithologies={len(candidate.get('lithologies', []))}")

                # Show suggestions dialog
                from .dialogs.smart_interbedding_suggestions_dialog import SmartInterbeddingSuggestionsDialog
                dialog = SmartInterbeddingSuggestionsDialog(candidates, self)
#                 print("DEBUG: SmartInterbeddingSuggestionsDialog created")

                dialog_result = dialog.exec()
                print(f"DEBUG: Dialog exec() returned: {dialog_result}")

                if dialog_result:
                    pass
#                     print("DEBUG: Dialog accepted, getting selected candidates")
                    # Apply selected suggestions
                    selected_indices = dialog.get_selected_candidates()
                    print(f"DEBUG: Selected candidate indices: {selected_indices}")

                    if selected_indices:
                        pass
#                         print("DEBUG: Applying interbedding candidates")
                        updated_units_df = analyzer.apply_interbedding_candidates(
                            units_dataframe, candidates, selected_indices, self.lithology_rules
                        )
                        # Update stored dataframe
                        self.last_units_dataframe = updated_units_df
                        print(f"DEBUG: Updated units dataframe shape: {updated_units_df.shape if hasattr(updated_units_df, 'shape') else 'No shape'}")
                    else:
                        pass  # No candidates selected
#                         print("DEBUG: No candidates selected")
                else:
                    print("DEBUG: Dialog rejected")

                # Continue to finalize display regardless of user choice
#                 print("DEBUG: Finalizing analysis display with updated dataframe")
                self._finalize_analysis_display(self.last_units_dataframe, classified_dataframe)
            else:
                print("DEBUG: No candidates found, proceeding with normal display")
                # No candidates found, proceed normally
                self._finalize_analysis_display(units_dataframe, classified_dataframe)

        except Exception as e:
            pass
            # Log error and continue with normal display
            print(f"DEBUG: Exception in smart interbedding suggestions: {e}")
            import traceback
            traceback.print_exc()
            self._finalize_analysis_display(units_dataframe, classified_dataframe)

    def _finalize_analysis_display(self, units_dataframe, classified_dataframe):
        """Finalize the analysis display after all processing is complete."""
        print(f"DEBUG (_finalize_analysis_display): called with units shape {units_dataframe.shape}, classified shape {classified_dataframe.shape}")
        # Settings UI widgets only exist in SettingsDialog, use attribute values directly
        if hasattr(self, 'unifiedViewport'):
            print(f"DEBUG (_finalize_analysis_display): unifiedViewport visible={self.unifiedViewport.isVisible()}, size={self.unifiedViewport.size().width()}x{self.unifiedViewport.size().height()}")
        separator_thickness = self.initial_separator_thickness
        draw_separators = self.initial_draw_separators

        # Calculate overall min and max depth from the classified_dataframe
        # This ensures both plots use the same consistent depth scale
        min_overall_depth = classified_dataframe[DEPTH_COLUMN].min()
        max_overall_depth = classified_dataframe[DEPTH_COLUMN].max()

        # Update zoom state manager with hole depth range
        if hasattr(self, 'zoom_state_manager'):
            self.zoom_state_manager.set_hole_depth_range(min_overall_depth, max_overall_depth)
#             print(f"DEBUG (_finalize_analysis_display): Updated zoom state manager with hole depth range: "
#                   f"{min_overall_depth:.2f} - {max_overall_depth:.2f}")

        # Pass the overall depth range to both stratigraphic columns
#         print(f"DEBUG (_finalize_analysis_display): Drawing overview column")
        self.stratigraphicColumnView.draw_column(units_dataframe, min_overall_depth, max_overall_depth, separator_thickness, draw_separators, disable_svg=self.disable_svg)
        if hasattr(self, 'enhancedStratColumnView'):
            print(f"DEBUG (_finalize_analysis_display): Drawing enhanced column, hasattr: {hasattr(self, 'enhancedStratColumnView')}")
            # Set classified data for curve values in tooltips
            self.enhancedStratColumnView.set_classified_data(classified_dataframe)
            self.enhancedStratColumnView.draw_column(units_dataframe, min_overall_depth, max_overall_depth, separator_thickness, draw_separators, disable_svg=self.disable_svg)
        else:
            print(f"DEBUG (_finalize_analysis_display): enhancedStratColumnView not found!")

        # Prepare curve configurations for the single CurvePlotter
        curve_configs = []
        curve_inversion_settings = self.initial_curve_inversion_settings
        current_curve_thickness = self.initial_curve_thickness

        if 'gamma' in classified_dataframe.columns:
            curve_configs.append({
                'name': 'gamma',
                'min': CURVE_RANGES['gamma']['min'],
                'max': CURVE_RANGES['gamma']['max'],
                'color': CURVE_RANGES['gamma']['color'],
                'inverted': curve_inversion_settings.get('gamma', False),
                'thickness': current_curve_thickness
            })
        if 'short_space_density' in classified_dataframe.columns:
            curve_configs.append({
                'name': 'short_space_density',
                'min': CURVE_RANGES['short_space_density']['min'],
                'max': CURVE_RANGES['short_space_density']['max'],
                'color': CURVE_RANGES['short_space_density']['color'],
                'inverted': curve_inversion_settings.get('short_space_density', False),
                'thickness': current_curve_thickness
            })
        if 'long_space_density' in classified_dataframe.columns:
            curve_configs.append({
                'name': 'long_space_density',
                'min': CURVE_RANGES['long_space_density']['min'],
                'max': CURVE_RANGES['long_space_density']['max'],
                'color': CURVE_RANGES['long_space_density']['color'],
                'inverted': curve_inversion_settings.get('long_space_density', False),
                'thickness': current_curve_thickness
            })
        if 'caliper' in classified_dataframe.columns:
            curve_configs.append({
                'name': 'caliper',
                'min': CURVE_RANGES['caliper']['min'],
                'max': CURVE_RANGES['caliper']['max'],
                'color': CURVE_RANGES['caliper']['color'],
                'inverted': curve_inversion_settings.get('caliper', False),
                'thickness': current_curve_thickness
            })
        if 'resistivity' in classified_dataframe.columns:
            curve_configs.append({
                'name': 'resistivity',
                'min': CURVE_RANGES['resistivity']['min'],
                'max': CURVE_RANGES['resistivity']['max'],
                'color': CURVE_RANGES['resistivity']['color'],
                'inverted': curve_inversion_settings.get('resistivity', False),
                'thickness': current_curve_thickness
            })

        # Update the single curve plotter and set its depth range
        print(f"DEBUG (_finalize_analysis_display): curve_configs count = {len(curve_configs)}")
        self.curvePlotter.set_curve_configs(curve_configs)
        self.curvePlotter.set_data(classified_dataframe)
        self.curvePlotter.set_depth_range(min_overall_depth, max_overall_depth)

        # Set bit size for anomaly detection
        if hasattr(self.curvePlotter, 'set_bit_size'):
            pass
            # Settings UI widgets only exist in SettingsDialog, use attribute value directly
            current_bit_size_mm = self.bit_size_mm
            self.curvePlotter.set_bit_size(current_bit_size_mm)

        # Use 37-column schema for editor display
        # First ensure all columns are present
        for col in COALLOG_V31_COLUMNS:
            if col not in units_dataframe.columns:
                units_dataframe[col] = ''

        # Use the full 37-column schema
        editor_dataframe = units_dataframe[COALLOG_V31_COLUMNS]
        self.editorTable.load_data(editor_dataframe)
        # Apply column visibility settings
        self.apply_column_visibility(self.column_visibility)

        # Set lithology data on curve plotter for boundary lines (Phase 4)
        if hasattr(self.curvePlotter, 'set_lithology_data'):
            self.curvePlotter.set_lithology_data(editor_dataframe)
        
        # Register curves with visibility manager
        self._register_curves_with_visibility_manager()

        # Activate the editor subwindow in MDI area
        if hasattr(self, 'mdi_area') and hasattr(self, 'editor_subwindow'):
            self.mdi_area.setActiveSubWindow(self.editor_subwindow)
            self.editor_subwindow.showMaximized()
        QMessageBox.information(self, "Analysis Complete", "Borehole analysis finished successfully!")

    def _schedule_gap_visualization_update(self):
        """Schedule a debounced update of the gap visualization to prevent excessive updates during rapid user input."""
        # Start or restart the timer with 500ms delay
        self.gap_update_timer.start(500)

    def _perform_gap_visualization_update(self):
        """Perform the actual gap visualization update after debounce delay."""
        try:
            self.refresh_range_visualization()
        except Exception as e:
            pass
            # Log error but don't crash the application
            print(f"Error updating gap visualization: {e}")
            import traceback
            traceback.print_exc()
    
    def _register_curves_with_visibility_manager(self):
        """
        Register all plotted curves with the visibility manager.
        This should be called after curves are drawn on the plotter.
        """
        try:
            # Auto-register curves from the plotter
            self.curve_visibility_manager.auto_register_from_plotter()
            
            # Apply saved visibility states
            self.curve_visibility_manager.load_states()
            self.curve_visibility_manager.apply_states_to_plotter()
            
            # Update UI controls
            self.curve_visibility_toolbar.register_curves_from_manager()
            self.curve_visibility_toolbar.update_from_visibility_manager()
            
#             print(f"Registered {len(self.curve_visibility_manager.curve_metadata)} curves with visibility manager")
            
        except Exception as e:
            print(f"Error registering curves with visibility manager: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_curve_visibility_states(self):
        """Save curve visibility states to user preferences."""
        try:
            self.curve_visibility_manager.save_states()
        except Exception as e:
            print(f"Error saving curve visibility states: {e}")
    
    def _force_overview_rescale(self):
        """Force overview column to rescale after window/splitter resize."""
        # The overview column is inside editor_hole (HoleEditorWindow)
        # Call the HoleEditorWindow's method instead
        if hasattr(self, 'editor_hole') and self.editor_hole:
            pass
#             print(f"DEBUG (MainWindow._force_overview_rescale): Calling editor_hole.force_overview_rescale()")
#             print(f"DEBUG (MainWindow._force_overview_rescale): Main window size: {self.size().width()}x{self.size().height()}")
#             print(f"DEBUG (MainWindow._force_overview_rescale): Main window maximized: {self.isMaximized()}")
            self.editor_hole.force_overview_rescale()
    
        
    def _update_overview_width(self):
        """Update overview width based on current window size (called on resize)."""
        if hasattr(self, 'editor_hole') and self.editor_hole:
            pass
            # Find the overview container
            for child in self.editor_hole.findChildren(QWidget):
                if child.objectName() == "overview_container" or "overview" in str(type(child)).lower():
                    pass
                    # Calculate proportional width (5% of window width)
                    window_width = self.width()
                    proportional_width = max(40, min(120, int(window_width * 0.05)))
                    
                    # Update width constraints
                    child.setMinimumWidth(proportional_width)
                    child.setMaximumWidth(proportional_width)
                    
#                     print(f"DEBUG (MainWindow._update_overview_width): Updated overview width to {proportional_width}px (5% of {window_width}px window)")
    
    def _on_splitter_moved(self, pos, index):
        """Handle splitter movement to update overview column."""
        print(f"DEBUG (MainWindow._on_splitter_moved): Splitter moved: pos={pos}, index={index}")
        if index == 2 or index == 3:  # Table or overview pane moved
            pass
#             print(f"DEBUG (MainWindow._on_splitter_moved): Overview pane might need rescale")
            # Schedule a delayed update to ensure geometry is settled
        # Guard against recursive resize calls
            QTimer.singleShot(50, self._force_overview_rescale)
    
    def resizeEvent(self, event):
        """Handle main window resize to update overview column."""
        super().resizeEvent(event)
        old_size = event.oldSize()
        new_size = event.size()
        print(f"DEBUG (MainWindow.resizeEvent): Window resized from {old_size.width()}x{old_size.height()} to {new_size.width()}x{new_size.height()}")
#         print(f"DEBUG (MainWindow.resizeEvent): Is maximized: {self.isMaximized()}")
        
        # Schedule overview rescale after geometry is settled
        # Use shorter delay for maximize events
        delay = 50 if self.isMaximized() else 100
        
        # Also update overview width proportionally
        self._update_overview_width()
        print(f"DEBUG (MainWindow.resizeEvent): Scheduling rescale in {delay}ms")
        QTimer.singleShot(delay, self._force_overview_rescale)


class UserGuideDialog(QDialog):
    """Dialog to display the user guide within the application."""
    
    def __init__(self, user_guide_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Earthworm Borehole Logger - User Guide")
        self.setGeometry(100, 100, 900, 700)
        self.setMinimumSize(800, 600)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create toolbar with navigation buttons
        toolbar = QHBoxLayout()
        
        # Table of contents button
        self.toc_button = QPushButton("Table of Contents")
        self.toc_button.clicked.connect(self.show_table_of_contents)
        toolbar.addWidget(self.toc_button)
        
        # Search box
        toolbar.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search user guide...")
        self.search_box.textChanged.connect(self.search_content)
        toolbar.addWidget(self.search_box)
        
        # Navigation buttons
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.clicked.connect(self.navigate_previous)
        toolbar.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.clicked.connect(self.navigate_next)
        toolbar.addWidget(self.next_button)
        
        toolbar.addStretch()
        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        toolbar.addWidget(self.close_button)
        
        main_layout.addLayout(toolbar)
        
        # Create splitter for table of contents and content
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Table of contents panel (initially hidden)
        self.toc_panel = QWidget()
        self.toc_layout = QVBoxLayout(self.toc_panel)
        self.toc_list = QListWidget()
        self.toc_list.itemClicked.connect(self.navigate_to_section)
        self.toc_layout.addWidget(QLabel("Table of Contents"))
        self.toc_layout.addWidget(self.toc_list)
        self.toc_panel.setVisible(False)
        self.toc_panel.setMaximumWidth(300)
        
        # Content panel
        self.content_panel = QWidget()
        content_layout = QVBoxLayout(self.content_panel)
        
        # Text browser for content
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.text_browser.anchorClicked.connect(self.handle_anchor_click)
        content_layout.addWidget(self.text_browser)
        
        # Add panels to splitter
        self.splitter.addWidget(self.toc_panel)
        self.splitter.addWidget(self.content_panel)
        self.splitter.setSizes([200, 700])
        
        main_layout.addWidget(self.splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Load the user guide
        self.user_guide_path = user_guide_path
        self.sections = []
        self.current_section_index = 0
        self.search_history = []
        self.load_user_guide()
        
    def load_user_guide(self):
        """Load and parse the user guide markdown file."""
        try:
            with open(self.user_guide_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse markdown and extract sections
            self.parse_markdown(content)
            
            # Display first section
            if self.sections:
                self.display_section(0)
                self.build_table_of_contents()
            
            self.status_label.setText(f"Loaded: {os.path.basename(self.user_guide_path)}")
            
        except Exception as e:
            self.text_browser.setHtml(f"""
            <h2>Error Loading User Guide</h2>
            <p>Could not load user guide from: {self.user_guide_path}</p>
            <p>Error: {str(e)}</p>
            <p>Please ensure the user guide file exists in the docs directory.</p>
            """)
    
    def parse_markdown(self, content):
        """Parse markdown content and extract sections."""
        lines = content.split('\n')
        current_section = {'title': '', 'level': 0, 'content': []}
        in_code_block = False
        code_block_language = ''
        
        for line in lines:
            pass
            # Check for code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                if in_code_block:
                    code_block_language = line.strip()[3:] or ''
                current_section['content'].append(line)
                continue
            
            # Check for headers
            if not in_code_block and line.startswith('#'):
                pass
                # Save previous section if it has content
                if current_section['title'] or current_section['content']:
                    self.sections.append(current_section.copy())
                
                # Determine header level
                level = 0
                while level < len(line) and line[level] == '#':
                    level += 1
                
                # Start new section
                current_section = {
                    'title': line[level:].strip(),
                    'level': level,
                    'content': [line]
                }
            else:
                current_section['content'].append(line)
        
        # Add the last section
        if current_section['title'] or current_section['content']:
            self.sections.append(current_section)
    
    def build_table_of_contents(self):
        """Build table of contents from sections."""
        self.toc_list.clear()
        for i, section in enumerate(self.sections):
            if section['level'] > 0:  # Only include headers
                indent = "  " * (section['level'] - 1)
                item = QListWidgetItem(f"{indent}• {section['title']}")
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.toc_list.addItem(item)
    
    def display_section(self, section_index):
        """Display a specific section."""
        if 0 <= section_index < len(self.sections):
            self.current_section_index = section_index
            section = self.sections[section_index]
            
            # Convert markdown to HTML
            html_content = self.markdown_to_html('\n'.join(section['content']))
            
            # Display with navigation
            nav_html = ""
            if section_index > 0:
                prev_title = self.sections[section_index - 1]['title']
                nav_html += f'<p><a href="prev://{section_index - 1}">◀ Previous: {prev_title}</a></p>'
            
            nav_html += f'<h{section["level"]}>{section["title"]}</h{section["level"]}>'
            
            if section_index < len(self.sections) - 1:
                next_title = self.sections[section_index + 1]['title']
                nav_html += f'<p style="text-align: right;"><a href="next://{section_index + 1}">Next: {next_title} ▶</a></p>'
            
            full_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                    h1, h2, h3, h4, h5, h6 {{ color: #2c3e50; margin-top: 24px; margin-bottom: 16px; }}
                    h1 {{ font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                    h2 {{ font-size: 1.5em; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
                    h3 {{ font-size: 1.25em; }}
                    code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
                    pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow: auto; font-family: 'Courier New', monospace; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    a {{ color: #3498db; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    .nav {{ margin: 20px 0; padding: 10px; background: #f9f9f9; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <div class="nav">
                    {nav_html}
                </div>
                {html_content}
            </body>
            </html>
            """
            
            self.text_browser.setHtml(full_html)
            self.update_navigation_buttons()
    
    def markdown_to_html(self, markdown):
        """Convert markdown to HTML (simplified version)."""
        html = markdown
        
        # Convert headers
        for i in range(6, 0, -1):
            html = html.replace('\n' + '#' * i + ' ', f'\n<h{i}>')
            html = html.replace('\n' + '#' * i, f'\n<h{i}>')
            html = html.replace(f'<h{i}>', f'<h{i}>', html.count(f'<h{i}>'))
            # Close headers at end of line
            lines = html.split('\n')
            for j, line in enumerate(lines):
                if line.startswith(f'<h{i}>') and not line.endswith(f'</h{i}>'):
                    lines[j] = line + f'</h{i}>'
            html = '\n'.join(lines)
        
        # Convert code blocks
        import re
        html = re.sub(r'```(\w*)\n(.*?)\n```', r'<pre><code class="\1">\2</code></pre>', html, flags=re.DOTALL)
        
        # Convert inline code
        html = html.replace('`', '<code>')
        # Simple fix: replace every other <code> with </code>
        parts = html.split('<code>')
        for i in range(1, len(parts), 2):
            parts[i] = parts[i].replace('<code>', '</code>', 1)
        html = '<code>'.join(parts)
        
        # Convert bold and italic (simplified)
        html = html.replace('**', '<strong>')
        html = html.replace('__', '<strong>')
        parts = html.split('<strong>')
        for i in range(1, len(parts), 2):
            parts[i] = parts[i].replace('<strong>', '</strong>', 1)
        html = '<strong>'.join(parts)
        
        html = html.replace('*', '<em>')
        html = html.replace('_', '<em>')
        parts = html.split('<em>')
        for i in range(1, len(parts), 2):
            parts[i] = parts[i].replace('<em>', '</em>', 1)
        html = '<em>'.join(parts)
        
        # Convert lists
        lines = html.split('\n')
        in_list = False
        for i, line in enumerate(lines):
            if line.strip().startswith('- ') or line.strip().startswith('* '):
                if not in_list:
                    lines[i] = '<ul>\n<li>' + line.strip()[2:] + '</li>'
                    in_list = True
                else:
                    lines[i] = '<li>' + line.strip()[2:] + '</li>'
            elif in_list and line.strip() == '':
                lines[i] = '</ul>\n'
                in_list = False
            elif in_list and not (line.strip().startswith('- ') or line.strip().startswith('* ')):
                lines[i] = '</ul>\n' + line
                in_list = False
        if in_list:
            lines.append('</ul>')
        html = '\n'.join(lines)
        
        # Convert links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        return html
    
    def show_table_of_contents(self):
        """Toggle table of contents panel visibility."""
        self.toc_panel.setVisible(not self.toc_panel.isVisible())
    
    def navigate_to_section(self, item):
        """Navigate to section when clicked in table of contents."""
        section_index = item.data(Qt.ItemDataRole.UserRole)
        self.display_section(section_index)
    
    def navigate_previous(self):
        """Navigate to previous section."""
        if self.current_section_index > 0:
            self.display_section(self.current_section_index - 1)
    
    def navigate_next(self):
        """Navigate to next section."""
        if self.current_section_index < len(self.sections) - 1:
            self.display_section(self.current_section_index + 1)
    
    def update_navigation_buttons(self):
        """Update navigation button states."""
        self.prev_button.setEnabled(self.current_section_index > 0)
        self.next_button.setEnabled(self.current_section_index < len(self.sections) - 1)
    
    def search_content(self, query):
        """Search content for query."""
        if not query.strip():
            return
        
        # Simple search implementation
        query_lower = query.lower()
        for i, section in enumerate(self.sections):
            content_lower = '\n'.join(section['content']).lower()
            if query_lower in content_lower:
                self.display_section(i)
                self.status_label.setText(f"Found '{query}' in section: {section['title']}")
                return
        
        self.status_label.setText(f"No results found for '{query}'")
    
    def handle_anchor_click(self, url):
        """Handle anchor clicks for navigation."""
        url_str = url.toString()
        if url_str.startswith('prev://'):
            section_index = int(url_str.split('://')[1])
            self.display_section(section_index)
        elif url_str.startswith('next://'):
            section_index = int(url_str.split('://')[1])
            self.display_section(section_index)
        else:
            # Open external links in default browser
            webbrowser.open(url_str)
