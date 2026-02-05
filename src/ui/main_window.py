from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QDialog, QScrollArea, QDockWidget,
    QPushButton, QComboBox, QLabel, QGraphicsView, QFileDialog, QMessageBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QColorDialog, QGraphicsScene, QDoubleSpinBox, QCheckBox, QSlider, QSpinBox, QFrame, QSplitter, QAbstractItemView,
    QGroupBox, QGridLayout, QFormLayout, QSizePolicy,
    QMdiArea, QMdiSubWindow, QMenu,
    QTreeView, QProgressBar, QApplication, QToolBar
)
from PyQt6.QtGui import QPainter, QPixmap, QColor, QFont, QBrush, QFileSystemModel, QAction
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QGraphicsSvgItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QPointF, QTimer
import pandas as pd
import numpy as np
import os
import json
import traceback

from ..core.data_processor import DataProcessor
from ..core.analyzer import Analyzer
from ..core.workers import LASLoaderWorker, ValidationWorker
from ..core.config import DEFAULT_LITHOLOGY_RULES, DEPTH_COLUMN, DEFAULT_SEPARATOR_THICKNESS, DRAW_SEPARATOR_LINES, DEFAULT_CURVE_THICKNESS, CURVE_RANGES, INVALID_DATA_VALUE, DEFAULT_MERGE_THIN_UNITS, DEFAULT_MERGE_THRESHOLD, DEFAULT_SMART_INTERBEDDING, DEFAULT_SMART_INTERBEDDING_MAX_SEQUENCE_LENGTH, DEFAULT_SMART_INTERBEDDING_THICK_UNIT_THRESHOLD, DEFAULT_BIT_SIZE_MM, DEFAULT_SHOW_ANOMALY_HIGHLIGHTS, DEFAULT_CASING_DEPTH_ENABLED, DEFAULT_CASING_DEPTH_M, LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN, RECORD_SEQUENCE_FLAG_COLUMN, INTERRELATIONSHIP_COLUMN, LITHOLOGY_PERCENT_COLUMN, COALLOG_V31_COLUMNS
from ..core.coallog_utils import load_coallog_dictionaries
from .widgets.stratigraphic_column import StratigraphicColumn
from .widgets.svg_renderer import SvgRenderer
from .widgets.curve_plotter import CurvePlotter # Import CurvePlotter
from .widgets.pyqtgraph_curve_plotter import PyQtGraphCurvePlotter # Import PyQtGraph-based plotter
from .widgets.enhanced_range_gap_visualizer import EnhancedRangeGapVisualizer # Import enhanced widget
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
from .widgets.cross_section_window import CrossSectionWindow # Import CrossSectionWindow for Phase 5

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
        self.stratigraphicColumnView = StratigraphicColumn()
        self.editorTable = LithologyTableWidget()
        self.exportCsvButton = QPushButton("Export to CSV")
        
        # Set bit size for anomaly detection if main_window is available
        if main_window and hasattr(main_window, 'bit_size_mm') and hasattr(self.curvePlotter, 'set_bit_size'):
            self.curvePlotter.set_bit_size(main_window.bit_size_mm)
        
        # Add loading indicator
        self.loadingProgressBar = QProgressBar()
        self.loadingProgressBar.setVisible(False)
        self.loadingLabel = QLabel("Loading...")
        self.loadingLabel.setVisible(False)
        
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
        
        # Set stratigraphic column to overview mode (showing entire hole)
        self.stratigraphicColumnView.set_overview_mode(True, hole_min_depth=0.0, hole_max_depth=500.0)
        
        self.setup_ui()
        
        if file_path:
            # Load data in background
            self.load_file_background(file_path)
    
    def setup_ui(self):
        """Create the 3-pane layout with zoom controls according to roadmap: [Plot View | Data Table | Overview View]."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
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
        plot_layout.addWidget(self.curvePlotter)
        
        # Middle Container: Data Table (Lithology Editor)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add Create Interbedding button (placeholder)
        button_layout = QHBoxLayout()
        self.createInterbeddingButton = QPushButton("Create Interbedding")
        # self.createInterbeddingButton.clicked.connect(self.create_manual_interbedding)
        button_layout.addWidget(self.createInterbeddingButton)
        button_layout.addWidget(self.exportCsvButton)
        button_layout.addStretch()
        
        table_layout.addWidget(self.editorTable)
        table_layout.addLayout(button_layout)
        
        # Right Container: Overview View (Stratigraphic Column - entire hole)
        overview_container = QWidget()
        overview_layout = QVBoxLayout(overview_container)
        overview_layout.setContentsMargins(0, 0, 0, 0)
        overview_layout.addWidget(self.stratigraphicColumnView)
        
        # Add to Splitter in correct order: Plot | Table | Overview
        main_splitter.addWidget(plot_container)
        main_splitter.addWidget(table_container)
        main_splitter.addWidget(overview_container)
        main_splitter.setStretchFactor(0, 2)  # Plot view gets more space
        main_splitter.setStretchFactor(1, 3)  # Table gets most space
        main_splitter.setStretchFactor(2, 1)  # Overview gets less space
        
        # Create container for main content and zoom controls
        main_content_widget = QWidget()
        main_content_layout = QVBoxLayout(main_content_widget)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(5)
        main_content_layout.addWidget(main_splitter)
        
        # Zoom Controls
        zoom_controls_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_controls_layout.addWidget(zoom_label)
        
        self.zoomSlider = QSlider(Qt.Orientation.Horizontal)
        self.zoomSlider.setMinimum(50)
        self.zoomSlider.setMaximum(500)
        self.zoomSlider.setValue(100)
        self.zoomSlider.setSingleStep(10)
        self.zoomSlider.setPageStep(50)
        zoom_controls_layout.addWidget(self.zoomSlider)
        
        self.zoomSpinBox = QDoubleSpinBox()
        self.zoomSpinBox.setRange(50.0, 500.0)
        self.zoomSpinBox.setValue(100.0)
        self.zoomSpinBox.setSingleStep(10.0)
        self.zoomSpinBox.setSuffix("%")
        zoom_controls_layout.addWidget(self.zoomSpinBox)
        
        zoom_controls_layout.addStretch()
        
        zoom_container = QWidget()
        zoom_container.setLayout(zoom_controls_layout)
        zoom_container.setFixedHeight(40)
        main_content_layout.addWidget(zoom_container)
        
        main_layout.addWidget(main_content_widget)
        
        # Connect zoom controls
        self.zoomSlider.valueChanged.connect(self.on_zoom_changed)
        self.zoomSpinBox.valueChanged.connect(self.on_zoom_changed)
        
        # Initialize empty table
        # Note: setRowCount is not needed for QTableView with PandasModel
        # The model will handle row count automatically
        self.editorTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    
    def _on_table_row_selected(self, row):
        """Handle table row selection to highlight stratigraphic column and scroll plot view (Subtask 4.1)."""
        if row == -1:
            # No selection - clear highlight
            self.stratigraphicColumnView.highlight_unit(None)
        else:
            # Highlight the corresponding unit in stratigraphic column
            self.stratigraphicColumnView.highlight_unit(row)
            
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
            # Find the row in the table that corresponds to this depth
            dataframe = self.editorTable.current_dataframe
            if dataframe is not None and 'from_depth' in dataframe.columns and 'to_depth' in dataframe.columns:
                # Find the row where depth is between from_depth and to_depth
                for idx, row in dataframe.iterrows():
                    if row['from_depth'] <= depth <= row['to_depth']:
                        # Select the corresponding row in the table
                        self.editorTable.selectRow(idx)
                        # Scroll to make the selected row visible
                        self.editorTable.scrollTo(self.editorTable.model().index(idx, 0))
                        print(f"Plot clicked at depth: {depth}m -> Selected table row {idx}")
                        return
                
                print(f"Plot clicked at depth: {depth}m -> No matching lithology unit found")
            else:
                print(f"Plot clicked at depth: {depth}m -> No lithology data available")
    
    def _on_plot_view_range_changed(self, min_depth, max_depth):
        """Handle plot view range changes to update overview overlay (Subtask 3.3)."""
        self.stratigraphicColumnView.update_zoom_overlay(min_depth, max_depth)
    
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
            print(f"✓ Table updated successfully")
            
            # Update the curve plotter's lithology data to keep in sync
            if hasattr(self.curvePlotter, 'lithology_data') and self.curvePlotter.lithology_data is not None:
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
            
        print(f"Table data changed, updating boundary lines...")
        
        # Update curve plotter's lithology data and boundary lines
        if hasattr(self.curvePlotter, 'set_lithology_data'):
            self.curvePlotter.set_lithology_data(dataframe)
            print(f"✓ Boundary lines updated from table data")
            
        # Update stratigraphic column if needed
        if hasattr(self.stratigraphicColumnView, 'set_lithology_data'):
            self.stratigraphicColumnView.set_lithology_data(dataframe)
    
    def on_zoom_changed(self):
        """Handle zoom control changes."""
        sender = self.sender()
        if sender == self.zoomSlider:
            zoom_percentage = self.zoomSlider.value()
            self.zoomSpinBox.blockSignals(True)
            self.zoomSpinBox.setValue(zoom_percentage)
            self.zoomSpinBox.blockSignals(False)
        else:
            zoom_percentage = self.zoomSpinBox.value()
            self.zoomSlider.blockSignals(True)
            self.zoomSlider.setValue(int(zoom_percentage))
            self.zoomSlider.blockSignals(False)
        
        zoom_factor = zoom_percentage / 100.0
        self.apply_synchronized_zoom(zoom_factor)
    
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
        
        # TODO: Update curve plotter and stratigraphic column with data
        print(f"File loaded successfully: {filename} ({len(dataframe)} rows)")
        
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


class Worker(QObject):
    finished = pyqtSignal(pd.DataFrame, pd.DataFrame)
    error = pyqtSignal(str)

    def __init__(self, file_path, mnemonic_map, lithology_rules, use_researched_defaults, merge_thin_units=False, merge_threshold=0.05, smart_interbedding=False, smart_interbedding_max_sequence_length=10, smart_interbedding_thick_unit_threshold=0.5, use_fallback_classification=False):
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

    def run(self):
        try:
            data_processor = DataProcessor()
            analyzer = Analyzer()
            dataframe, _ = data_processor.load_las_file(self.file_path)
            
            # Ensure all required curve mnemonics are in the map for preprocessing
            # Add default mappings if not already present in mnemonic_map
            full_mnemonic_map = self.mnemonic_map.copy()
            if 'short_space_density' not in full_mnemonic_map:
                full_mnemonic_map['short_space_density'] = 'DENS' # Common mnemonic for short space density
            if 'long_space_density' not in full_mnemonic_map:
                full_mnemonic_map['long_space_density'] = 'LSD' # Common mnemonic for long space density

            processed_dataframe = data_processor.preprocess_data(dataframe, full_mnemonic_map)
            # Use appropriate classification method based on settings
            if hasattr(self, 'analysis_method') and self.analysis_method == "simple":
                classified_dataframe = analyzer.classify_rows_simple(processed_dataframe, self.lithology_rules, full_mnemonic_map)
            else:
                classified_dataframe = analyzer.classify_rows(processed_dataframe, self.lithology_rules, full_mnemonic_map, self.use_researched_defaults, self.use_fallback_classification)
            units_dataframe = analyzer.group_into_units(classified_dataframe, self.lithology_rules, self.smart_interbedding, self.smart_interbedding_max_sequence_length, self.smart_interbedding_thick_unit_threshold)
            if self.merge_thin_units:
                units_dataframe = analyzer.merge_thin_units(units_dataframe, self.merge_threshold)
            template_path = os.path.join(os.getcwd(), 'src', 'assets', 'TEMPLATE.xlsx')
            output_path = os.path.join(os.path.dirname(self.file_path), "output_lithology.xlsx")
            def log_progress(message):
                print(f"Worker Log: {message}")
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
                # Use default geometry centered on screen
                x = (screen_width - default_width) // 2
                y = (screen_height - default_height) // 2
                self.setGeometry(x, y, default_width, default_height)

        # Set minimum size to prevent the window from becoming unusable
        self.setMinimumSize(800, 600)

        # Load settings on startup
        app_settings = load_settings()
        self.column_visibility = app_settings.get("column_visibility", {})
        self.lithology_rules = app_settings["lithology_rules"]
        self.initial_separator_thickness = app_settings["separator_thickness"]
        self.initial_draw_separators = app_settings["draw_separator_lines"]
        self.initial_curve_inversion_settings = app_settings["curve_inversion_settings"]
        self.initial_curve_thickness = app_settings["curve_thickness"] # Load new setting
        self.use_researched_defaults = app_settings["use_researched_defaults"]
        self.analysis_method = app_settings.get("analysis_method", "standard")  # Load analysis method
        self.merge_thin_units = app_settings.get("merge_thin_units", False)
        self.merge_threshold = app_settings.get("merge_threshold", 0.05)
        self.smart_interbedding = app_settings.get("smart_interbedding", False)
        self.smart_interbedding_max_sequence_length = app_settings.get("smart_interbedding_max_sequence_length", 10)
        self.smart_interbedding_thick_unit_threshold = app_settings.get("smart_interbedding_thick_unit_threshold", 0.5)
        self.bit_size_mm = app_settings.get("bit_size_mm", 150.0)  # Load bit size in millimeters
        self.show_anomaly_highlights = app_settings.get("show_anomaly_highlights", True)  # Load anomaly highlights setting
        self.casing_depth_enabled = app_settings.get("casing_depth_enabled", False)  # Load casing depth masking enabled state
        self.casing_depth_m = app_settings.get("casing_depth_m", 0.0)  # Load casing depth in meters
        self.current_theme = app_settings.get("theme", "dark")  # Load theme preference

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
        self.settings_tab = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_tab)
        # Settings tab is NOT added to tab widget - will be used in dock widget instead
        # self.tab_widget.addTab(self.settings_tab, "Settings")
        
        # Create dock widget for settings
        self.settings_dock = QDockWidget("Settings", self)
        self.settings_dock.setWidget(self.settings_tab)
        self.settings_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.settings_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                       QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                       QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.settings_dock)
        self.settings_dock.hide()  # Initially hidden
        self.settings_dock.visibilityChanged.connect(self.update_settings_button_text)

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
        self.editorTable = self.editor_hole.editorTable
        self.exportCsvButton = self.editor_hole.exportCsvButton
        
        # Connect table row selection to stratigraphic column highlighting
        self.editorTable.rowSelectionChangedSignal.connect(self._on_table_row_selected)

        main_layout.addWidget(self.mdi_area)
        
        self.connect_signals()
        self.load_default_lithology_rules()
        self.setup_settings_tab()
        # self.setup_editor_tab()  # Not needed: hole editor has its own layout
        # self.tab_widget.currentChanged.connect(self.on_tab_changed)  # MDI removes tabs
        self._synchronize_views()
        self.create_file_menu()
        self.create_window_menu()
        self.create_view_menu()
        self.create_toolbar()

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
        """Create View menu with theme toggle and other view options."""
        view_menu = self.menuBar().addMenu("&View")
        
        # Theme submenu
        theme_menu = QMenu("Theme", self)
        view_menu.addMenu(theme_menu)
        
        # Dark theme action
        dark_theme_action = QAction("Dark", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(self.current_theme == "dark")
        dark_theme_action.triggered.connect(lambda: self.set_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Light theme action
        light_theme_action = QAction("Light", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(self.current_theme == "light")
        light_theme_action.triggered.connect(lambda: self.set_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        # Add separator
        theme_menu.addSeparator()
        
        # Toggle theme action (quick toggle)
        toggle_theme_action = QAction("Toggle Theme", self)
        toggle_theme_action.triggered.connect(self.toggle_theme)
        theme_menu.addAction(toggle_theme_action)
        
        # Theme preview dialog
        theme_menu.addSeparator()
        preview_action = QAction("Preview Theme...", self)
        preview_action.triggered.connect(self.show_theme_preview)
        theme_menu.addAction(preview_action)
        
        # Add separator in main view menu
        view_menu.addSeparator()
        
        # Show/Hide docks
        show_settings_action = QAction("Show/Hide Settings", self)
        show_settings_action.triggered.connect(self.open_settings_dialog)
        view_menu.addAction(show_settings_action)
        
        show_explorer_action = QAction("Show/Hide Project Explorer", self)
        show_explorer_action.triggered.connect(self.toggle_project_explorer)
        view_menu.addAction(show_explorer_action)

    def set_theme(self, theme_name):
        """Set a specific theme."""
        if theme_name not in ["dark", "light"]:
            return
        
        self.current_theme = theme_name
        
        # Update application property for CSS class
        app = QApplication.instance()
        if app:
            if self.current_theme == "light":
                app.setProperty("class", "light-theme")
            else:
                app.setProperty("class", "")  # Default to dark theme
        
        # Save theme preference
        self.save_theme_preference()
        
        # Update menu check states
        self.update_theme_menu_states()
        
        # Show theme change notification
        QMessageBox.information(self, "Theme Changed", 
                               f"Switched to {self.current_theme} theme. Restart the application for full effect.")
    
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

    def create_toolbar(self):
        """Create main toolbar with common actions."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setMovable(True)
        self.addToolBar(toolbar)
        
        # Add theme toggle button
        theme_action = QAction("🌓", self)  # Using emoji for theme icon
        theme_action.setToolTip("Toggle Dark/Light Theme")
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Add other common actions
        load_action = QAction("📂", self)
        load_action.setToolTip("Load LAS File")
        load_action.triggered.connect(self.load_las_file_dialog)
        toolbar.addAction(load_action)
        
        settings_action = QAction("⚙️", self)
        settings_action.setToolTip("Settings")
        settings_action.triggered.connect(self.open_settings_dialog)
        toolbar.addAction(settings_action)

    def _synchronize_views(self):
        """Connects the two views to scroll in sync with perfect 1:1 depth alignment."""
        self._is_syncing = False # A flag to prevent recursive sync
        
        # Check if both views have verticalScrollBar method (required for synchronization)
        has_curve_scrollbar = hasattr(self.curvePlotter, 'verticalScrollBar')
        has_strat_scrollbar = hasattr(self.stratigraphicColumnView, 'verticalScrollBar')
        
        if not (has_curve_scrollbar and has_strat_scrollbar):
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
            # Get the model
            model = self.editorTable.model()
            if model and 0 <= unit_index < model.rowCount():
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
            print(f"DEBUG (MainWindow): Invalid lithology_code provided: {lithology_code}")
            return None

        # Construct the base prefix for the SVG file
        base_prefix = lithology_code.upper()

        # If a qualifier is provided, try to find a combined SVG first
        if lithology_qualifier and isinstance(lithology_qualifier, str):
            combined_code = (base_prefix + lithology_qualifier.upper()).strip()
            combined_filename_prefix = combined_code + ' '
            print(f"DEBUG (MainWindow): Searching for combined SVG with prefix '{combined_filename_prefix}' in '{svg_dir}'")
            for filename in os.listdir(svg_dir):
                if filename.upper().startswith(combined_filename_prefix):
                    found_path = os.path.join(svg_dir, filename)
                    print(f"DEBUG (MainWindow): Found combined SVG: {found_path}")
                    return found_path
            print(f"DEBUG (MainWindow): No combined SVG found for prefix '{combined_filename_prefix}'")

        # If no combined SVG found or no qualifier provided, fall back to just the lithology code
        single_filename_prefix = base_prefix + ' '
        print(f"DEBUG (MainWindow): Falling back to searching for single SVG with prefix '{single_filename_prefix}' in '{svg_dir}'")
        for filename in os.listdir(svg_dir):
            if filename.upper().startswith(single_filename_prefix):
                found_path = os.path.join(svg_dir, filename)
                print(f"DEBUG (MainWindow): Found single SVG: {found_path}")
                return found_path
        
        print(f"DEBUG (MainWindow): No SVG found for lithology code '{lithology_code}' (and qualifier '{lithology_qualifier}')")
        return None

    def connect_signals(self):
        self.loadLasButton.clicked.connect(self.load_las_file_dialog)
        self.runAnalysisButton.clicked.connect(self.run_analysis)
        self.settingsButton.clicked.connect(self.open_settings_dialog)
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
                
                # Apply theme class to the application
                app = QApplication.instance()
                if app:
                    if self.current_theme == "light":
                        app.setProperty("class", "light-theme")
                    else:
                        app.setProperty("class", "")  # Default to dark theme
                
                print(f"Stylesheet loaded successfully with {self.current_theme} theme")
            else:
                print(f"Warning: Stylesheet not found at {stylesheet_path}")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        if self.current_theme == "dark":
            self.current_theme = "light"
        else:
            self.current_theme = "dark"
        
        # Update application property for CSS class
        app = QApplication.instance()
        if app:
            if self.current_theme == "light":
                app.setProperty("class", "light-theme")
            else:
                app.setProperty("class", "")  # Default to dark theme
        
        # Save theme preference
        self.save_theme_preference()
        
        # Show theme change notification
        QMessageBox.information(self, "Theme Changed", 
                               f"Switched to {self.current_theme} theme. Restart the application for full effect.")

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
            fallback_classification=app_settings.get("fallback_classification", "Unknown"),
            bit_size_mm=app_settings.get("bit_size_mm", 150.0),
            show_anomaly_highlights=app_settings.get("show_anomaly_highlights", True),
            casing_depth_enabled=app_settings.get("casing_depth_enabled", False),
            casing_depth_m=app_settings.get("casing_depth_m", 0.0),
            workspace_state=app_settings.get("workspace"),
            theme=self.current_theme,
            column_visibility=app_settings.get("column_visibility", {})
        )

    def open_settings_dialog(self):
        """Toggle visibility of settings dock widget."""
        if self.settings_dock.isVisible():
            self.settings_dock.hide()
        else:
            self.settings_dock.show()
            self.settings_dock.raise_()  # Bring to front if floating
    
    def open_session_dialog(self):
        """Open the session management dialog."""
        dialog = SessionDialog(parent=self, main_window=self)
        dialog.session_selected.connect(self.on_session_loaded)
        dialog.exec()
    
    def on_session_loaded(self, session_name):
        """Handle session loaded signal."""
        print(f"Session '{session_name}' loaded successfully")
        # Additional session loading logic can be added here if needed
    
    def open_template_dialog(self):
        """Open the template selection dialog."""
        dialog = TemplateDialog(parent=self, main_window=self)
        dialog.template_selected.connect(self.on_template_applied)
        dialog.exec()
    
    def on_template_applied(self, template_name):
        """Handle template applied signal."""
        print(f"Template '{template_name}' applied successfully")
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
    
    def update_settings_button_text(self):
        """Update settings button text based on dock visibility."""
        if self.settings_dock.isVisible():
            self.settingsButton.setText("Hide Settings")
        else:
            self.settingsButton.setText("Settings")

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
        subwindow.show()
        
        # Optionally tile windows
        # self.mdi_area.tileSubWindows()
        
        # For backward compatibility, still set global las_file_path?
        # self.las_file_path = file_path
        # But we should not call load_las_data() because it would affect the main window's widgets

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
        subwindow.show()
        
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
        print(f"Map selection changed: {len(selected_files)} holes selected")
        
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
            # Get the index for this file path
            index = self.holes_model.index(file_path)
            if index.isValid():
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
        cross_section = CrossSectionWindow(hole_file_paths)
        
        # Create MDI subwindow
        subwindow = QMdiSubWindow()
        subwindow.setWidget(cross_section)
        subwindow.setWindowTitle("Cross-Section")
        
        # Add to MDI area
        self.mdi_area.addSubWindow(subwindow)
        subwindow.show()
        
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

        self.gammaRayComboBox.addItems(mnemonics)
        self.densityComboBox.addItems(mnemonics)
        self.shortSpaceDensityComboBox.addItems(mnemonics)
        self.longSpaceDensityComboBox.addItems(mnemonics)

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

    def setup_settings_tab(self):
        # Clear existing layout (just in case)
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Create scroll area for settings with vertical-only scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Force vertical-only scrolling
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for all settings groups
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(10)
        container_layout.setContentsMargins(8, 8, 8, 8)
        
        # 1. LITHOLOGY RULES GROUP
        litho_group = QGroupBox("Lithology Rules")
        litho_layout = QVBoxLayout(litho_group)
        litho_layout.setSpacing(6)
        
        self.settings_rules_table = QTableWidget()
        self.settings_rules_table.setColumnCount(9)
        self.settings_rules_table.setHorizontalHeaderLabels([
            "Name", "Code", "Qualifier", "Gamma Range", "Density Range",
            "Visual Props", "Background", "Preview", "Actions"
        ])
        # Let columns resize to content, but set minimum widths
        header = self.settings_rules_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(60)
        header.setStretchLastSection(True)
        self.settings_rules_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        litho_layout.addWidget(self.settings_rules_table)
        
        # Add/Remove buttons
        rule_buttons_layout = QHBoxLayout()
        rule_buttons_layout.setSpacing(6)
        self.addRuleButton = QPushButton("Add Rule")
        self.removeRuleButton = QPushButton("Remove Rule")
        rule_buttons_layout.addWidget(self.addRuleButton)
        rule_buttons_layout.addWidget(self.removeRuleButton)
        rule_buttons_layout.addStretch()
        litho_layout.addLayout(rule_buttons_layout)
        
        container_layout.addWidget(litho_group)
        
        # 2. DISPLAY SETTINGS GROUP
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout(display_group)
        display_layout.setSpacing(8)
        display_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # Separator thickness
        self.separatorThicknessSpinBox = QDoubleSpinBox()
        self.separatorThicknessSpinBox.setRange(0.0, 5.0)
        self.separatorThicknessSpinBox.setSingleStep(0.1)
        self.separatorThicknessSpinBox.setMaximumWidth(100)
        display_layout.addRow("Separator Line Thickness:", self.separatorThicknessSpinBox)
        
        # Draw separators checkbox
        self.drawSeparatorsCheckBox = QCheckBox("Draw Separator Lines")
        display_layout.addRow(self.drawSeparatorsCheckBox)
        
        # Curve thickness
        self.curveThicknessSpinBox = QDoubleSpinBox()
        self.curveThicknessSpinBox.setRange(0.1, 5.0)
        self.curveThicknessSpinBox.setSingleStep(0.1)
        self.curveThicknessSpinBox.setMaximumWidth(100)
        display_layout.addRow("Curve Line Thickness:", self.curveThicknessSpinBox)
        
        # Curve inversion checkboxes
        curve_inv_widget = QWidget()
        curve_inv_layout = QVBoxLayout(curve_inv_widget)
        curve_inv_layout.setSpacing(4)
        curve_inv_layout.setContentsMargins(0, 0, 0, 0)
        self.invertGammaCheckBox = QCheckBox("Invert Gamma")
        self.invertShortSpaceDensityCheckBox = QCheckBox("Invert Short Space Density")
        self.invertLongSpaceDensityCheckBox = QCheckBox("Invert Long Space Density")
        curve_inv_layout.addWidget(self.invertGammaCheckBox)
        curve_inv_layout.addWidget(self.invertShortSpaceDensityCheckBox)
        curve_inv_layout.addWidget(self.invertLongSpaceDensityCheckBox)
        display_layout.addRow("Curve Inversion:", curve_inv_widget)
        
        container_layout.addWidget(display_group)
        
        # 3. ANALYSIS SETTINGS GROUP
        analysis_group = QGroupBox("Analysis Settings")
        analysis_layout = QVBoxLayout(analysis_group)
        analysis_layout.setSpacing(8)
        
        # Checkboxes in a grid
        check_grid = QGridLayout()
        check_grid.setSpacing(6)
        self.useResearchedDefaultsCheckBox = QCheckBox("Apply Researched Defaults for Missing Ranges")
        self.useResearchedDefaultsCheckBox.setChecked(self.use_researched_defaults)
        check_grid.addWidget(self.useResearchedDefaultsCheckBox, 0, 0, 1, 2)
        
        self.mergeThinUnitsCheckBox = QCheckBox("Merge thin lithology units (< 5cm)")
        self.mergeThinUnitsCheckBox.setChecked(self.merge_thin_units)
        check_grid.addWidget(self.mergeThinUnitsCheckBox, 1, 0, 1, 2)
        
        self.smartInterbeddingCheckBox = QCheckBox("Smart Interbedding")
        self.smartInterbeddingCheckBox.setChecked(self.smart_interbedding)
        check_grid.addWidget(self.smartInterbeddingCheckBox, 2, 0, 1, 2)
        
        self.fallbackClassificationCheckBox = QCheckBox("Enable Fallback Classification")
        self.fallbackClassificationCheckBox.setChecked(False)
        self.fallbackClassificationCheckBox.setToolTip("Apply fallback classification to reduce 'NL' (Not Logged) results")
        check_grid.addWidget(self.fallbackClassificationCheckBox, 3, 0, 1, 2)
        
        analysis_layout.addLayout(check_grid)
        
        # Smart interbedding parameters (only visible when smart interbedding is checked)
        self.interbedding_params_widget = QWidget()
        interbedding_params_layout = QHBoxLayout(self.interbedding_params_widget)
        interbedding_params_layout.setSpacing(8)
        interbedding_params_layout.addWidget(QLabel("Max Sequence Length:"))
        self.smartInterbeddingMaxSequenceSpinBox = QSpinBox()
        self.smartInterbeddingMaxSequenceSpinBox.setRange(5, 50)
        self.smartInterbeddingMaxSequenceSpinBox.setValue(self.smart_interbedding_max_sequence_length)
        interbedding_params_layout.addWidget(self.smartInterbeddingMaxSequenceSpinBox)
        
        interbedding_params_layout.addWidget(QLabel("Thick Unit Threshold (m):"))
        self.smartInterbeddingThickUnitSpinBox = QDoubleSpinBox()
        self.smartInterbeddingThickUnitSpinBox.setRange(0.1, 5.0)
        self.smartInterbeddingThickUnitSpinBox.setSingleStep(0.1)
        self.smartInterbeddingThickUnitSpinBox.setValue(self.smart_interbedding_thick_unit_threshold)
        interbedding_params_layout.addWidget(self.smartInterbeddingThickUnitSpinBox)
        interbedding_params_layout.addStretch()
        analysis_layout.addWidget(self.interbedding_params_widget)
        # Hide initially if smart interbedding is off
        self.interbedding_params_widget.setVisible(self.smart_interbedding)
        
        # Analysis method
        method_widget = QWidget()
        method_layout = QFormLayout(method_widget)
        method_layout.setSpacing(8)
        method_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        self.analysisMethodComboBox = QComboBox()
        self.analysisMethodComboBox.addItems(["Standard", "Simple"])
        if hasattr(self, 'analysis_method') and self.analysis_method == "simple":
            self.analysisMethodComboBox.setCurrentText("Simple")
        else:
            self.analysisMethodComboBox.setCurrentText("Standard")
        method_layout.addRow("Analysis Method:", self.analysisMethodComboBox)
        analysis_layout.addWidget(method_widget)
        
        # Bit size input field
        bit_size_widget = QWidget()
        bit_size_layout = QFormLayout(bit_size_widget)
        bit_size_layout.setSpacing(8)
        bit_size_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        self.bitSizeSpinBox = QDoubleSpinBox()
        self.bitSizeSpinBox.setRange(50.0, 500.0)  # Reasonable range for bit sizes in mm
        self.bitSizeSpinBox.setValue(self.bit_size_mm)
        self.bitSizeSpinBox.setSingleStep(10.0)
        self.bitSizeSpinBox.setSuffix(" mm")
        self.bitSizeSpinBox.setToolTip("Bit size in millimeters for caliper anomaly detection (CAL - BitSize > 20)")
        bit_size_layout.addRow("Bit Size:", self.bitSizeSpinBox)
        
        # Anomaly highlighting checkbox
        self.showAnomalyHighlightsCheckBox = QCheckBox("Show anomaly highlights")
        self.showAnomalyHighlightsCheckBox.setChecked(self.show_anomaly_highlights)
        self.showAnomalyHighlightsCheckBox.setToolTip("Show/hide red highlighting for caliper anomalies (CAL - BitSize > 20 mm)")
        bit_size_layout.addRow("", self.showAnomalyHighlightsCheckBox)
        
        analysis_layout.addWidget(bit_size_widget)
        
        # Casing depth masking
        casing_depth_widget = QWidget()
        casing_depth_layout = QFormLayout(casing_depth_widget)
        casing_depth_layout.setSpacing(8)
        casing_depth_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # Enable casing depth masking checkbox
        self.casingDepthEnabledCheckBox = QCheckBox("Enable Casing Depth Masking")
        self.casingDepthEnabledCheckBox.setChecked(self.casing_depth_enabled)
        self.casingDepthEnabledCheckBox.setToolTip("Mask intervals above casing depth as 'NL' (Not Logged)")
        casing_depth_layout.addRow("", self.casingDepthEnabledCheckBox)
        
        # Casing depth input (only enabled when checkbox is checked)
        self.casingDepthSpinBox = QDoubleSpinBox()
        self.casingDepthSpinBox.setRange(0.0, 5000.0)  # Reasonable range for casing depth in meters
        self.casingDepthSpinBox.setValue(self.casing_depth_m)
        self.casingDepthSpinBox.setSingleStep(1.0)
        self.casingDepthSpinBox.setSuffix(" m")
        self.casingDepthSpinBox.setToolTip("Casing depth in meters. Intervals above this depth will be masked as 'NL'")
        self.casingDepthSpinBox.setEnabled(self.casing_depth_enabled)  # Initially disabled if not checked
        casing_depth_layout.addRow("Casing Depth:", self.casingDepthSpinBox)
        
        analysis_layout.addWidget(casing_depth_widget)
        
        # NL Review button
        nl_review_widget = QWidget()
        nl_review_layout = QHBoxLayout(nl_review_widget)
        nl_review_layout.setSpacing(8)
        nl_review_layout.setContentsMargins(0, 0, 0, 0)
        
        self.nlReviewButton = QPushButton("📊 Review NL Intervals")
        self.nlReviewButton.setToolTip("Review 'NL' (Not Logged) intervals with statistics")
        self.nlReviewButton.clicked.connect(self.open_nl_review_dialog)
        nl_review_layout.addWidget(self.nlReviewButton)
        nl_review_layout.addStretch()
        
        analysis_layout.addWidget(nl_review_widget)
        
        container_layout.addWidget(analysis_group)
        
        # 4. TABLE SETTINGS GROUP
        table_group = QGroupBox("Table Settings")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(8)
        
        # Column Configurator button
        self.columnConfiguratorButton = QPushButton("⚙️ Column Configurator")
        self.columnConfiguratorButton.setToolTip("Configure visible columns in the lithology table")
        self.columnConfiguratorButton.clicked.connect(self.open_column_configurator_dialog)
        table_layout.addWidget(self.columnConfiguratorButton)
        
        container_layout.addWidget(table_group)
        
        # 5. CURVE VISIBILITY GROUP
        curve_visibility_group = QGroupBox("Curve Visibility")
        curve_visibility_layout = QVBoxLayout(curve_visibility_group)
        curve_visibility_layout.setSpacing(6)
        
        # Create checkboxes for each curve type
        self.curve_visibility_checkboxes = {}
        
        # Curve types with their display names and abbreviations
        curve_types = [
            ("SS", "Short Space Density", "short_space_density"),
            ("LS", "Long Space Density", "long_space_density"),
            ("GR", "Gamma Ray", "gamma"),
            ("CD", "Caliper", "cd"),
            ("RES", "Resistivity", "res"),
            ("CAL", "Caliper", "cal")
        ]
        
        for abbr, display_name, curve_name in curve_types:
            checkbox = QCheckBox(f"[{abbr}] {display_name}")
            checkbox.setChecked(True)  # All curves visible by default
            checkbox.curve_name = curve_name  # Store the internal curve name
            self.curve_visibility_checkboxes[curve_name] = checkbox
            curve_visibility_layout.addWidget(checkbox)
            
            # Connect checkbox state change to update curve visibility
            checkbox.stateChanged.connect(self.on_curve_visibility_changed)
        
        curve_visibility_layout.addStretch()
        container_layout.addWidget(curve_visibility_group)
        
        # 6. FILE OPERATIONS GROUP
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)
        
        # Row 1: Save/Load/Update buttons
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(6)
        self.saveAsSettingsButton = QPushButton("Save Settings As...")
        self.updateSettingsButton = QPushButton("Update Settings")
        self.loadSettingsButton = QPushButton("Load Settings...")
        self.saveAsSettingsButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.updateSettingsButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.loadSettingsButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row1_layout.addWidget(self.saveAsSettingsButton)
        row1_layout.addWidget(self.updateSettingsButton)
        row1_layout.addWidget(self.loadSettingsButton)
        file_layout.addLayout(row1_layout)
        
        # Row 2: Researched defaults, export, reset buttons
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(6)
        self.researchedDefaultsButton = QPushButton("Researched Defaults...")
        self.exportLithologyReportButton = QPushButton("Export Lithology Report")
        self.resetDefaultsButton = QPushButton("Reset to Defaults")
        self.researchedDefaultsButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.exportLithologyReportButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.resetDefaultsButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row2_layout.addWidget(self.researchedDefaultsButton)
        row2_layout.addWidget(self.exportLithologyReportButton)
        row2_layout.addWidget(self.resetDefaultsButton)
        file_layout.addLayout(row2_layout)
        
        # Row 3: Advanced settings button
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(6)
        self.advancedSettingsButton = QPushButton("Advanced Settings...")
        self.advancedSettingsButton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row3_layout.addWidget(self.advancedSettingsButton)
        file_layout.addLayout(row3_layout)
        
        container_layout.addWidget(file_group)
        
        # 7. RANGE ANALYSIS GROUP
        range_group = QGroupBox("Range Analysis")
        range_layout = QVBoxLayout(range_group)
        range_layout.setSpacing(8)
        
        self.refreshRangeAnalysisButton = QPushButton("Refresh Range Analysis")
        self.refreshRangeAnalysisButton.clicked.connect(self.refresh_range_visualization)
        range_layout.addWidget(self.refreshRangeAnalysisButton)
        
        range_layout.addWidget(self.range_visualizer)
        
        container_layout.addWidget(range_group)
        
        container_layout.addStretch()
        
        # Set container as scroll widget
        scroll.setWidget(container)
        self.settings_layout.addWidget(scroll)
        
        # Initialize connections
        self.addRuleButton.clicked.connect(self.add_settings_rule)
        self.removeRuleButton.clicked.connect(self.remove_settings_rule)
        
        self.saveAsSettingsButton.clicked.connect(self.save_settings_as_file)
        self.updateSettingsButton.clicked.connect(self.update_settings)
        self.loadSettingsButton.clicked.connect(self.load_settings_from_file)
        self.researchedDefaultsButton.clicked.connect(self.open_researched_defaults_dialog)
        self.exportLithologyReportButton.clicked.connect(self.export_lithology_report)
        self.resetDefaultsButton.clicked.connect(self.reset_settings_to_defaults)
        self.advancedSettingsButton.clicked.connect(self.open_advanced_settings_dialog)
        
        # Connect smart interbedding checkbox to toggle parameters visibility
        self.smartInterbeddingCheckBox.stateChanged.connect(self.toggle_interbedding_params_visibility)
        
        # Load current settings into controls
        self.load_settings_rules_to_table()
        self.load_separator_settings()
        self.load_curve_thickness_settings()
        self.load_curve_inversion_settings()
        self._apply_researched_defaults_if_needed()
        
        # Connect value change signals to auto-save and mark settings as dirty
        self.separatorThicknessSpinBox.valueChanged.connect(self.mark_settings_dirty)
        self.separatorThicknessSpinBox.valueChanged.connect(lambda: self.update_settings(auto_save=True))
        self.drawSeparatorsCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.drawSeparatorsCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.curveThicknessSpinBox.valueChanged.connect(self.mark_settings_dirty)
        self.curveThicknessSpinBox.valueChanged.connect(lambda: self.update_settings(auto_save=True))
        self.invertGammaCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.invertGammaCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.invertShortSpaceDensityCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.invertShortSpaceDensityCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.invertLongSpaceDensityCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.invertLongSpaceDensityCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.useResearchedDefaultsCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.useResearchedDefaultsCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.mergeThinUnitsCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.mergeThinUnitsCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.smartInterbeddingCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.smartInterbeddingCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        self.smartInterbeddingMaxSequenceSpinBox.valueChanged.connect(self.mark_settings_dirty)
        self.smartInterbeddingMaxSequenceSpinBox.valueChanged.connect(lambda: self.update_settings(auto_save=True))
        self.smartInterbeddingThickUnitSpinBox.valueChanged.connect(self.mark_settings_dirty)
        self.smartInterbeddingThickUnitSpinBox.valueChanged.connect(lambda: self.update_settings(auto_save=True))
        self.analysisMethodComboBox.currentTextChanged.connect(self.mark_settings_dirty)
        self.analysisMethodComboBox.currentTextChanged.connect(lambda: self.update_settings(auto_save=True))
        self.fallbackClassificationCheckBox.stateChanged.connect(self.mark_settings_dirty)
        self.fallbackClassificationCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
        # Connect bit size spin box if it exists
        if hasattr(self, 'bitSizeSpinBox'):
            self.bitSizeSpinBox.valueChanged.connect(self.mark_settings_dirty)
            self.bitSizeSpinBox.valueChanged.connect(lambda: self.update_settings(auto_save=True))
            self.bitSizeSpinBox.valueChanged.connect(self.update_plotter_bit_size)
        
        # Connect anomaly highlights checkbox if it exists
        if hasattr(self, 'showAnomalyHighlightsCheckBox'):
            self.showAnomalyHighlightsCheckBox.stateChanged.connect(self.mark_settings_dirty)
            self.showAnomalyHighlightsCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
            self.showAnomalyHighlightsCheckBox.stateChanged.connect(self.update_plotter_anomaly_visibility)
        
        # Connect casing depth controls if they exist
        if hasattr(self, 'casingDepthEnabledCheckBox'):
            self.casingDepthEnabledCheckBox.stateChanged.connect(self.mark_settings_dirty)
            self.casingDepthEnabledCheckBox.stateChanged.connect(lambda: self.update_settings(auto_save=True))
            self.casingDepthEnabledCheckBox.stateChanged.connect(self.toggle_casing_depth_input)
            # Connect casing depth spin box
            self.casingDepthSpinBox.valueChanged.connect(self.mark_settings_dirty)
            self.casingDepthSpinBox.valueChanged.connect(lambda: self.update_settings(auto_save=True))
        
        # Connect curve visibility checkboxes to mark settings as dirty
        for checkbox in self.curve_visibility_checkboxes.values():
            checkbox.stateChanged.connect(self.mark_settings_dirty)
        
        # Initialize range visualization
        self.refresh_range_visualization()
    
    def toggle_interbedding_params_visibility(self):
        """Show/hide smart interbedding parameters based on checkbox state."""
        visible = self.smartInterbeddingCheckBox.isChecked()
        self.interbedding_params_widget.setVisible(visible)
    
    def toggle_casing_depth_input(self):
        """Enable/disable casing depth input based on checkbox state."""
        enabled = self.casingDepthEnabledCheckBox.isChecked()
        self.casingDepthSpinBox.setEnabled(enabled)
    
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
            # Reset lithology rules to default
            self.lithology_rules = DEFAULT_LITHOLOGY_RULES.copy()
            # Reset separator settings
            self.initial_separator_thickness = DEFAULT_SEPARATOR_THICKNESS
            self.initial_draw_separators = DRAW_SEPARATOR_LINES
            # Reset curve thickness default
            self.initial_curve_thickness = DEFAULT_CURVE_THICKNESS
            # Reset curve inversion defaults
            self.initial_curve_inversion_settings = {'gamma': False, 'short_space_density': False, 'long_space_density': False}
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
            # Reset bit size and anomaly highlights
            self.bit_size_mm = DEFAULT_BIT_SIZE_MM
            self.show_anomaly_highlights = DEFAULT_SHOW_ANOMALY_HIGHLIGHTS
            # Reset casing depth settings
            self.casing_depth_enabled = DEFAULT_CASING_DEPTH_ENABLED
            self.casing_depth_m = DEFAULT_CASING_DEPTH_M
            # Update UI controls
            self.load_settings_rules_to_table()
            self.load_separator_settings()
            self.load_curve_thickness_settings()
            self.load_curve_inversion_settings()
            self.useResearchedDefaultsCheckBox.setChecked(self.use_researched_defaults)
            self.analysisMethodComboBox.setCurrentText("Standard")
            self.mergeThinUnitsCheckBox.setChecked(self.merge_thin_units)
            self.smartInterbeddingCheckBox.setChecked(self.smart_interbedding)
            self.smartInterbeddingMaxSequenceSpinBox.setValue(self.smart_interbedding_max_sequence_length)
            self.smartInterbeddingThickUnitSpinBox.setValue(self.smart_interbedding_thick_unit_threshold)
            self.fallbackClassificationCheckBox.setChecked(False)
            if hasattr(self, 'bitSizeSpinBox'):
                self.bitSizeSpinBox.setValue(self.bit_size_mm)
            if hasattr(self, 'showAnomalyHighlightsCheckBox'):
                self.showAnomalyHighlightsCheckBox.setChecked(self.show_anomaly_highlights)
            if hasattr(self, 'casingDepthEnabledCheckBox'):
                self.casingDepthEnabledCheckBox.setChecked(self.casing_depth_enabled)
                self.casingDepthSpinBox.setValue(self.casing_depth_m)
                self.casingDepthSpinBox.setEnabled(self.casing_depth_enabled)
            # Hide interbedding params if needed
            self.interbedding_params_widget.setVisible(self.smart_interbedding)
            # Save defaults
            self.update_settings(auto_save=True)
            # Clear the dirty flag since settings have been reset
            self.settings_dirty = False
            # Update the "Update Settings" button text to remove the asterisk
            if hasattr(self, 'updateSettingsButton'):
                self.updateSettingsButton.setText("Update Settings")
            QMessageBox.information(self, "Settings Reset", "All settings have been reset to defaults.")

    def load_separator_settings(self):
        self.separatorThicknessSpinBox.setValue(self.initial_separator_thickness)
        self.drawSeparatorsCheckBox.setChecked(self.initial_draw_separators)

    def load_curve_thickness_settings(self):
        self.curveThicknessSpinBox.setValue(self.initial_curve_thickness)

    def load_curve_inversion_settings(self):
        self.invertGammaCheckBox.setChecked(self.initial_curve_inversion_settings.get('gamma', False))
        self.invertShortSpaceDensityCheckBox.setChecked(self.initial_curve_inversion_settings.get('short_space_density', False))
        self.invertLongSpaceDensityCheckBox.setChecked(self.initial_curve_inversion_settings.get('long_space_density', False))

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
        self.bit_size_mm = app_settings.get("bit_size_mm", 215.9)
        self.show_anomaly_highlights = app_settings.get("show_anomaly_highlights", False)
        self.casing_depth_enabled = app_settings.get("casing_depth_enabled", False)
        self.casing_depth_m = app_settings.get("casing_depth_m", 0.0)
        
        # Update lithology rules
        self.lithology_rules = app_settings["lithology_rules"]
        
        # Call existing helper methods to update UI
        self.load_separator_settings()
        self.load_curve_thickness_settings()
        self.load_curve_inversion_settings()
        
        # Only load settings rules to table if coallog_data is available
        if self.coallog_data is not None:
            self.load_settings_rules_to_table()
        else:
            print("Warning: coallog_data not available, skipping load_settings_rules_to_table()")
        
        # Update other UI widgets that don't have helper methods
        self.useResearchedDefaultsCheckBox.setChecked(self.use_researched_defaults)
        self.analysisMethodComboBox.setCurrentText("Standard" if self.analysis_method == "standard" else "Simple")
        self.mergeThinUnitsCheckBox.setChecked(self.merge_thin_units)
        self.smartInterbeddingCheckBox.setChecked(self.smart_interbedding)
        self.smartInterbeddingMaxSequenceSpinBox.setValue(self.smart_interbedding_max_sequence_length)
        self.smartInterbeddingThickUnitSpinBox.setValue(self.smart_interbedding_thick_unit_threshold)
        self.fallbackClassificationCheckBox.setChecked(False)  # Default
        
        # Update optional widgets if they exist
        if hasattr(self, 'bitSizeSpinBox'):
            self.bitSizeSpinBox.setValue(self.bit_size_mm)
        if hasattr(self, 'showAnomalyHighlightsCheckBox'):
            self.showAnomalyHighlightsCheckBox.setChecked(self.show_anomaly_highlights)
        if hasattr(self, 'casingDepthEnabledCheckBox'):
            self.casingDepthEnabledCheckBox.setChecked(self.casing_depth_enabled)
            if hasattr(self, 'casingDepthSpinBox'):
                self.casingDepthSpinBox.setValue(self.casing_depth_m)
                self.casingDepthSpinBox.setEnabled(self.casing_depth_enabled)
        
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
                current_separator_thickness = self.separatorThicknessSpinBox.value()
                current_draw_separators = self.drawSeparatorsCheckBox.isChecked()
                current_curve_thickness = self.curveThicknessSpinBox.value() # Get new setting
                current_curve_inversion_settings = {
                    'gamma': self.invertGammaCheckBox.isChecked(),
                    'short_space_density': self.invertShortSpaceDensityCheckBox.isChecked(),
                    'long_space_density': self.invertLongSpaceDensityCheckBox.isChecked()
                }
                
                # Get current value of researched defaults checkbox
                current_use_researched_defaults = self.useResearchedDefaultsCheckBox.isChecked()

                # Get current analysis method
                current_analysis_method = self.analysisMethodComboBox.currentText().lower()
                
                # Get current merge settings
                current_merge_thin_units = self.mergeThinUnitsCheckBox.isChecked()
                current_merge_threshold = self.merge_threshold  # Keep the loaded threshold

                # Get current smart interbedding settings
                current_smart_interbedding = self.smartInterbeddingCheckBox.isChecked()
                current_smart_interbedding_max_sequence = self.smartInterbeddingMaxSequenceSpinBox.value()
                current_smart_interbedding_thick_unit = self.smartInterbeddingThickUnitSpinBox.value()
                
                # Get current bit size
                current_bit_size_mm = self.bitSizeSpinBox.value() if hasattr(self, 'bitSizeSpinBox') else self.bit_size_mm
                
                # Get current anomaly highlights setting
                current_show_anomaly_highlights = self.showAnomalyHighlightsCheckBox.isChecked() if hasattr(self, 'showAnomalyHighlightsCheckBox') else self.show_anomaly_highlights

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
                    bit_size_mm=current_bit_size_mm,
                    show_anomaly_highlights=current_show_anomaly_highlights,
                    column_visibility=self.column_visibility,
                    file_path=file_path
                )
                QMessageBox.information(self, "Settings Saved", f"Settings saved to {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def get_current_settings(self):
        """Return current settings as a dictionary compatible with SettingsDialog."""
        # Ensure rules are saved from table
        self.save_settings_rules_from_table(show_message=False)
        
        # Gather settings from UI controls
        current_separator_thickness = self.separatorThicknessSpinBox.value()
        current_draw_separators = self.drawSeparatorsCheckBox.isChecked()
        current_curve_thickness = self.curveThicknessSpinBox.value()
        current_curve_inversion_settings = {
            'gamma': self.invertGammaCheckBox.isChecked(),
            'short_space_density': self.invertShortSpaceDensityCheckBox.isChecked(),
            'long_space_density': self.invertLongSpaceDensityCheckBox.isChecked()
        }
        
        current_use_researched_defaults = self.useResearchedDefaultsCheckBox.isChecked()
        current_analysis_method = self.analysisMethodComboBox.currentText().lower()
        current_merge_thin_units = self.mergeThinUnitsCheckBox.isChecked()
        current_merge_threshold = self.merge_threshold  # Keep the loaded threshold
        current_smart_interbedding = self.smartInterbeddingCheckBox.isChecked()
        current_smart_interbedding_max_sequence = self.smartInterbeddingMaxSequenceSpinBox.value()
        current_smart_interbedding_thick_unit = self.smartInterbeddingThickUnitSpinBox.value()
        current_fallback_classification = self.fallbackClassificationCheckBox.isChecked()
        current_bit_size_mm = self.bitSizeSpinBox.value() if hasattr(self, 'bitSizeSpinBox') else self.bit_size_mm
        
        # Build settings dict matching SettingsDialog expectations
        settings = {
            'lithology_rules': self.lithology_rules,
            'separator_thickness': current_separator_thickness,
            'draw_separators': current_draw_separators,
            'curve_thickness': current_curve_thickness,
            'invert_gamma': current_curve_inversion_settings['gamma'],
            'invert_short_space_density': current_curve_inversion_settings['short_space_density'],
            'invert_long_space_density': current_curve_inversion_settings['long_space_density'],
            'use_researched_defaults': current_use_researched_defaults,
            'analysis_method': current_analysis_method,
            'merge_thin_units': current_merge_thin_units,
            'smart_interbedding': current_smart_interbedding,
            'fallback_classification': current_fallback_classification,
            'smart_interbedding_max_sequence_length': current_smart_interbedding_max_sequence,
            'smart_interbedding_thick_unit_threshold': current_smart_interbedding_thick_unit,
            'bit_size_mm': current_bit_size_mm
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
            'long_space_density': settings.get('invert_long_space_density', False)
        }
        self.use_researched_defaults = settings.get('use_researched_defaults', self.use_researched_defaults)
        self.analysis_method = settings.get('analysis_method', self.analysis_method)
        self.merge_thin_units = settings.get('merge_thin_units', self.merge_thin_units)
        self.smart_interbedding = settings.get('smart_interbedding', self.smart_interbedding)
        self.smart_interbedding_max_sequence_length = settings.get('smart_interbedding_max_sequence_length', self.smart_interbedding_max_sequence_length)
        self.smart_interbedding_thick_unit_threshold = settings.get('smart_interbedding_thick_unit_threshold', self.smart_interbedding_thick_unit_threshold)
        self.use_fallback_classification = settings.get('fallback_classification', self.use_fallback_classification)
        self.bit_size_mm = settings.get('bit_size_mm', self.bit_size_mm)
        # Update UI controls
        self.load_settings_rules_to_table()
        self.load_separator_settings()
        self.load_curve_thickness_settings()
        self.load_curve_inversion_settings()
        self.useResearchedDefaultsCheckBox.setChecked(self.use_researched_defaults)
        if hasattr(self, 'analysisMethodComboBox'):
            if self.analysis_method == "simple":
                self.analysisMethodComboBox.setCurrentText("Simple")
            else:
                self.analysisMethodComboBox.setCurrentText("Standard")
        if hasattr(self, 'bitSizeSpinBox'):
            self.bitSizeSpinBox.setValue(self.bit_size_mm)
    
    def update_settings_from_template(self, template):
        """Update settings from a template object."""
        from ..core.template_manager import ProjectTemplate
        
        if not isinstance(template, ProjectTemplate):
            print(f"Error: Expected ProjectTemplate, got {type(template)}")
            return
        
        print(f"Updating settings from template: {template.name}")
        
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
        self.mergeThinUnitsCheckBox.setChecked(self.merge_thin_units)
        self.smartInterbeddingCheckBox.setChecked(self.smart_interbedding)
        self.smartInterbeddingMaxSequenceSpinBox.setValue(self.smart_interbedding_max_sequence_length)
        self.smartInterbeddingThickUnitSpinBox.setValue(self.smart_interbedding_thick_unit_threshold)
        self.fallbackClassificationCheckBox.setChecked(self.use_fallback_classification)
        if hasattr(self, 'bitSizeSpinBox'):
            self.bitSizeSpinBox.setValue(self.bit_size_mm)
        # Refresh range visualization
        self.refresh_range_visualization()
        # Save to disk
        self.update_settings(auto_save=True)

    def update_settings(self, auto_save=False):
        # This method will be called when any setting changes or when "Update Settings" is clicked
        # It gathers all current settings and saves them to the default settings file
        self.save_settings_rules_from_table(show_message=False) # Save rules first

        current_separator_thickness = self.separatorThicknessSpinBox.value()
        current_draw_separators = self.drawSeparatorsCheckBox.isChecked()
        current_curve_thickness = self.curveThicknessSpinBox.value() # Get new setting
        current_curve_inversion_settings = {
            'gamma': self.invertGammaCheckBox.isChecked(),
            'short_space_density': self.invertShortSpaceDensityCheckBox.isChecked(),
            'long_space_density': self.invertLongSpaceDensityCheckBox.isChecked()
        }
        
        current_use_researched_defaults = self.useResearchedDefaultsCheckBox.isChecked()
        current_analysis_method = self.analysisMethodComboBox.currentText().lower()
        current_merge_thin_units = self.mergeThinUnitsCheckBox.isChecked()
        current_merge_threshold = self.merge_threshold  # Keep the loaded threshold
        current_smart_interbedding = self.smartInterbeddingCheckBox.isChecked()
        current_smart_interbedding_max_sequence = self.smartInterbeddingMaxSequenceSpinBox.value()
        current_smart_interbedding_thick_unit = self.smartInterbeddingThickUnitSpinBox.value()
        current_bit_size_mm = self.bitSizeSpinBox.value() if hasattr(self, 'bitSizeSpinBox') else self.bit_size_mm
        current_show_anomaly_highlights = self.showAnomalyHighlightsCheckBox.isChecked() if hasattr(self, 'showAnomalyHighlightsCheckBox') else self.show_anomaly_highlights
        current_casing_depth_enabled = self.casingDepthEnabledCheckBox.isChecked() if hasattr(self, 'casingDepthEnabledCheckBox') else self.casing_depth_enabled
        current_casing_depth_m = self.casingDepthSpinBox.value() if hasattr(self, 'casingDepthSpinBox') else self.casing_depth_m
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
            bit_size_mm=current_bit_size_mm,
            show_anomaly_highlights=current_show_anomaly_highlights,
            casing_depth_enabled=current_casing_depth_enabled,
            casing_depth_m=current_casing_depth_m,
            column_visibility=self.column_visibility
        )

        # Update instance variables to ensure smart interbedding uses current values
        self.smart_interbedding = current_smart_interbedding
        self.smart_interbedding_max_sequence_length = current_smart_interbedding_max_sequence
        self.smart_interbedding_thick_unit_threshold = current_smart_interbedding_thick_unit
        self.bit_size_mm = current_bit_size_mm
        self.show_anomaly_highlights = current_show_anomaly_highlights
        self.casing_depth_enabled = current_casing_depth_enabled
        self.casing_depth_m = current_casing_depth_m

        if not auto_save: # Only show message if triggered by the "Update Settings" button
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
            self.useResearchedDefaultsCheckBox.setChecked(self.use_researched_defaults)
            self.analysis_method = app_settings.get("analysis_method", "standard")
            if hasattr(self, 'analysisMethodComboBox'):
                if self.analysis_method == "simple":
                    self.analysisMethodComboBox.setCurrentText("Simple")
                else:
                    self.analysisMethodComboBox.setCurrentText("Standard")
            self.bit_size_mm = app_settings.get("bit_size_mm", 150.0)
            if hasattr(self, 'bitSizeSpinBox'):
                self.bitSizeSpinBox.setValue(self.bit_size_mm)
            self.casing_depth_enabled = app_settings.get("casing_depth_enabled", False)
            self.casing_depth_m = app_settings.get("casing_depth_m", 0.0)
            if hasattr(self, 'casingDepthEnabledCheckBox'):
                self.casingDepthEnabledCheckBox.setChecked(self.casing_depth_enabled)
                self.casingDepthSpinBox.setValue(self.casing_depth_m)
                self.casingDepthSpinBox.setEnabled(self.casing_depth_enabled)
            self.load_settings_rules_to_table()
            self.load_separator_settings()
            self.load_curve_thickness_settings() # Reload new setting
            self.load_curve_inversion_settings()
            # Update smart interbedding UI elements to reflect reloaded settings
            self.smartInterbeddingCheckBox.setChecked(self.smart_interbedding)
            self.smartInterbeddingMaxSequenceSpinBox.setValue(self.smart_interbedding_max_sequence_length)
            self.smartInterbeddingThickUnitSpinBox.setValue(self.smart_interbedding_thick_unit_threshold)


    def load_settings_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Settings", "", "JSON Files (*.json);;All Files (*)")
        if file_path:
            try:
                loaded_settings = load_settings(file_path) # Pass file_path to load_settings
                self.lithology_rules = loaded_settings["lithology_rules"]
                self.initial_separator_thickness = loaded_settings["separator_thickness"]
                self.initial_draw_separators = loaded_settings["draw_separator_lines"]
                self.initial_curve_inversion_settings = loaded_settings["curve_inversion_settings"] # Load new setting
                self.initial_curve_thickness = loaded_settings["curve_thickness"] # Load new setting
                self.use_researched_defaults = loaded_settings["use_researched_defaults"]
                self.useResearchedDefaultsCheckBox.setChecked(self.use_researched_defaults)
                self.bit_size_mm = loaded_settings.get("bit_size_mm", 150.0)
                if hasattr(self, 'bitSizeSpinBox'):
                    self.bitSizeSpinBox.setValue(self.bit_size_mm)
                self.show_anomaly_highlights = loaded_settings.get("show_anomaly_highlights", True)
                if hasattr(self, 'showAnomalyHighlightsCheckBox'):
                    self.showAnomalyHighlightsCheckBox.setChecked(self.show_anomaly_highlights)
                self.casing_depth_enabled = loaded_settings.get("casing_depth_enabled", False)
                self.casing_depth_m = loaded_settings.get("casing_depth_m", 0.0)
                if hasattr(self, 'casingDepthEnabledCheckBox'):
                    self.casingDepthEnabledCheckBox.setChecked(self.casing_depth_enabled)
                    self.casingDepthSpinBox.setValue(self.casing_depth_m)
                    self.casingDepthSpinBox.setEnabled(self.casing_depth_enabled)
                self.column_visibility = loaded_settings.get("column_visibility", {})
                self.apply_column_visibility(self.column_visibility)

                self.load_settings_rules_to_table()
                self.load_separator_settings()
                self.load_curve_thickness_settings() # Reload new setting
                self.load_curve_inversion_settings() # Load new setting
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
        if hasattr(self, 'bitSizeSpinBox'):
            bit_size_mm = self.bitSizeSpinBox.value()
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
        if hasattr(self, 'showAnomalyHighlightsCheckBox'):
            show_anomaly = self.showAnomalyHighlightsCheckBox.isChecked()
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
        # Remove redundant save when switching tabs
        # if self.tab_widget.tabText(index) != "Settings":
        #     self.save_settings_rules_from_table()
        pass # No automatic saving on tab change anymore

    def load_settings_rules_to_table(self):
        self.settings_rules_table.setRowCount(len(self.lithology_rules))
        for row_idx, rule in enumerate(self.lithology_rules):
            # Column 0: Name (QComboBox)
            litho_desc_combo = QComboBox()
            litho_desc_combo.addItems(self.coallog_data['Litho_Type']['Description'].tolist())
            if rule.get('name', '') in self.coallog_data['Litho_Type']['Description'].tolist():
                litho_desc_combo.setCurrentText(rule.get('name', ''))
            self.settings_rules_table.setCellWidget(row_idx, 0, litho_desc_combo)
            litho_desc_combo.currentTextChanged.connect(self.update_litho_code)
            litho_desc_combo.currentTextChanged.connect(lambda _, r=row_idx: self.update_rule_preview(r))
            litho_desc_combo.currentTextChanged.connect(lambda text, r=row_idx: self.update_qualifier_dropdown(r, text))
            litho_desc_combo.currentTextChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed

            # Column 1: Code (read-only QLabel)
            self.settings_rules_table.setItem(row_idx, 1, QTableWidgetItem(str(rule.get('code', ''))))
            self.settings_rules_table.item(row_idx, 1).setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)

            # Column 2: Qualifier (QComboBox)
            qual_combo = QComboBox()
            self.settings_rules_table.setCellWidget(row_idx, 2, qual_combo)
            qual_combo.currentTextChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed

            # Column 3: Gamma Range (CompactRangeWidget)
            gamma_widget = CompactRangeWidget()
            gamma_widget.set_values(rule.get('gamma_min', 0.0), rule.get('gamma_max', 0.0))
            gamma_widget.valuesChanged.connect(lambda min_val, max_val, r=row_idx: self.update_range_values(r, 'gamma', min_val, max_val))
            gamma_widget.valuesChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed
            self.settings_rules_table.setCellWidget(row_idx, 3, gamma_widget)

            # Column 4: Density Range (CompactRangeWidget)
            density_widget = CompactRangeWidget()
            density_widget.set_values(rule.get('density_min', 0.0), rule.get('density_max', 0.0))
            density_widget.valuesChanged.connect(lambda min_val, max_val, r=row_idx: self.update_range_values(r, 'density', min_val, max_val))
            density_widget.valuesChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed
            self.settings_rules_table.setCellWidget(row_idx, 4, density_widget)

            # Column 5: Visual Props (MultiAttributeWidget)
            visual_widget = MultiAttributeWidget(coallog_data=self.coallog_data)
            visual_widget.set_properties({
                'shade': rule.get('shade', ''),
                'hue': rule.get('hue', ''),
                'colour': rule.get('colour', ''),
                'weathering': rule.get('weathering', ''),
                'strength': rule.get('strength', '')
            })
            visual_widget.propertiesChanged.connect(lambda props, r=row_idx: self.update_visual_properties(r, props))
            visual_widget.propertiesChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed
            self.settings_rules_table.setCellWidget(row_idx, 5, visual_widget)

            # Column 6: Background (QPushButton for color picker)
            color_button = QPushButton()
            color_hex = rule.get('background_color', '#FFFFFF')
            color_button.setStyleSheet(f"background-color: {color_hex}")
            color_button.clicked.connect(lambda _, r=row_idx: self.open_color_picker(r))
            self.settings_rules_table.setCellWidget(row_idx, 6, color_button)

            # Column 7: Preview (EnhancedPatternPreview)
            preview_widget = EnhancedPatternPreview()
            self.settings_rules_table.setCellWidget(row_idx, 7, preview_widget)
            self.update_rule_preview(row_idx)

            # Column 8: Actions (QWidget with buttons)
            actions_widget = self.create_actions_widget(row_idx)
            self.settings_rules_table.setCellWidget(row_idx, 8, actions_widget)

            # Dynamically populate qualifiers and set the saved value
            self.update_qualifier_dropdown(row_idx, litho_desc_combo.currentText())
            saved_qualifier = rule.get('qualifier', '')
            # Find the index of the saved qualifier code and set it
            index = qual_combo.findData(saved_qualifier, Qt.ItemDataRole.UserRole)
            if index != -1:
                qual_combo.setCurrentIndex(index)
            else:
                qual_combo.setCurrentIndex(0) # Select the blank item if not found

    def save_settings_rules_from_table(self, show_message=True):
        rules = []
        for row_idx in range(self.settings_rules_table.rowCount()):
            rule = {}

            # Column 0: Name (QComboBox)
            rule['name'] = self.settings_rules_table.cellWidget(row_idx, 0).currentText()

            # Column 1: Code (read-only item)
            rule['code'] = self.settings_rules_table.item(row_idx, 1).text() if self.settings_rules_table.item(row_idx, 1) else ''

            # Column 2: Qualifier (QComboBox)
            rule['qualifier'] = self.settings_rules_table.cellWidget(row_idx, 2).currentData(Qt.ItemDataRole.UserRole)

            # Column 3: Gamma Range (CompactRangeWidget)
            gamma_widget = self.settings_rules_table.cellWidget(row_idx, 3)
            if isinstance(gamma_widget, CompactRangeWidget):
                gamma_min, gamma_max = gamma_widget.get_values()
                rule['gamma_min'] = gamma_min
                rule['gamma_max'] = gamma_max
            else:
                rule['gamma_min'] = INVALID_DATA_VALUE
                rule['gamma_max'] = INVALID_DATA_VALUE

            # Column 4: Density Range (CompactRangeWidget)
            density_widget = self.settings_rules_table.cellWidget(row_idx, 4)
            if isinstance(density_widget, CompactRangeWidget):
                density_min, density_max = density_widget.get_values()
                rule['density_min'] = density_min
                rule['density_max'] = density_max
            else:
                rule['density_min'] = INVALID_DATA_VALUE
                rule['density_max'] = INVALID_DATA_VALUE

            # Column 5: Visual Props (MultiAttributeWidget)
            visual_widget = self.settings_rules_table.cellWidget(row_idx, 5)
            if isinstance(visual_widget, MultiAttributeWidget):
                visual_props = visual_widget.get_properties()
                rule.update(visual_props)
            else:
                # Fallback to empty strings if widget not available
                rule['shade'] = ''
                rule['hue'] = ''
                rule['colour'] = ''
                rule['weathering'] = ''
                rule['strength'] = ''

            # Column 6: Background (QPushButton)
            color_button = self.settings_rules_table.cellWidget(row_idx, 6)
            if color_button:
                try:
                    rule['background_color'] = QColor(color_button.styleSheet().split(':')[-1].strip()).name()
                except:
                    rule['background_color'] = '#FFFFFF'
            else:
                rule['background_color'] = '#FFFFFF'

            # Find and store the absolute path to the SVG file directly in the rule, using qualifier
            rule['svg_path'] = self.find_svg_file(rule['code'], rule['qualifier'])

            rules.append(rule)
        self.lithology_rules = rules
        # Only show message if explicitly called, not on every tab change or auto-save
        if show_message:
            QMessageBox.information(self, "Settings Saved", "Lithology rules updated.")

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

        # Column 0: Name (QComboBox)
        litho_desc_combo = QComboBox()
        litho_desc_combo.addItems(self.coallog_data['Litho_Type']['Description'].tolist())
        self.settings_rules_table.setCellWidget(row_position, 0, litho_desc_combo)
        litho_desc_combo.currentTextChanged.connect(self.update_litho_code)
        litho_desc_combo.currentTextChanged.connect(lambda _, r=row_position: self.update_rule_preview(r))
        litho_desc_combo.currentTextChanged.connect(lambda text, r=row_position: self.update_qualifier_dropdown(r, text))
        litho_desc_combo.currentTextChanged.connect(self.mark_settings_dirty)  # Mark as dirty when changed

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

    def update_litho_code(self, text):
        sender = self.sender()
        if sender:
            row = self.settings_rules_table.indexAt(sender.pos()).row()
            litho_code = self.coallog_data['Litho_Type'].loc[self.coallog_data['Litho_Type']['Description'] == text, 'Code'].iloc[0]
            self.settings_rules_table.setItem(row, 1, QTableWidgetItem(litho_code))

    def update_qualifier_dropdown(self, row, selected_litho_name):
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

        current_qualifier_code = qual_combo.currentData(Qt.ItemDataRole.UserRole) # Get the currently selected code
        qual_combo.clear()

        qual_combo.addItem("", "") # Add a blank option with empty code
        
        if litho_code:
            litho_info = self.lithology_qualifier_map.get(litho_code, {})
            qualifiers = litho_info.get('qualifiers', {})
            if qualifiers:
                # Qualifiers are a dict of {code: description}
                for code, description in qualifiers.items():
                    qual_combo.addItem(description, code) # Display description, store code as UserRole data
        
        # Try to restore the previous selection by code
        index = qual_combo.findData(current_qualifier_code, Qt.ItemDataRole.UserRole)
        if index != -1:
            qual_combo.setCurrentIndex(index)
        else:
            qual_combo.setCurrentIndex(0) # Select the blank item if not found

    def remove_settings_rule(self):
        current_row = self.settings_rules_table.currentRow()
        if current_row >= 0:
            self.settings_rules_table.removeRow(current_row)
            self.mark_settings_dirty()  # Mark as dirty when rule is removed
        self.save_settings_rules_from_table()

    def open_color_picker(self, row):
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

        # 4. Right Container (Editor Table + Export)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        # Add Create Interbedding button
        button_layout = QHBoxLayout()
        self.createInterbeddingButton = QPushButton("Create Interbedding")
        self.createInterbeddingButton.clicked.connect(self.create_manual_interbedding)
        button_layout.addWidget(self.createInterbeddingButton)
        button_layout.addWidget(self.exportCsvButton)
        button_layout.addStretch()

        table_layout.addWidget(self.editorTable)
        table_layout.addLayout(button_layout)

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

        # 7. Zoom Controls (affects both curve and strat views)
        zoom_controls_layout = QHBoxLayout()

        zoom_label = QLabel("Zoom:")
        zoom_controls_layout.addWidget(zoom_label)

        self.zoomSlider = QSlider(Qt.Orientation.Horizontal)
        self.zoomSlider.setMinimum(50)  # 50% zoom
        self.zoomSlider.setMaximum(500)  # 500% zoom
        self.zoomSlider.setValue(100)  # Default 100% zoom
        self.zoomSlider.setSingleStep(10)
        self.zoomSlider.setPageStep(50)
        zoom_controls_layout.addWidget(self.zoomSlider)

        self.zoomSpinBox = QDoubleSpinBox()
        self.zoomSpinBox.setRange(50.0, 500.0)
        self.zoomSpinBox.setValue(100.0)
        self.zoomSpinBox.setSingleStep(10.0)
        self.zoomSpinBox.setSuffix("%")
        zoom_controls_layout.addWidget(self.zoomSpinBox)

        zoom_controls_layout.addStretch()  # Push controls to the left

        # Add zoom controls to content layout with fixed height
        zoom_container = QWidget()
        zoom_container.setLayout(zoom_controls_layout)
        zoom_container.setFixedHeight(40)  # Fixed height for zoom controls
        main_content_layout.addWidget(zoom_container)

        # Add the main content widget to the editor tab layout
        self.editor_tab_layout.addWidget(main_content_widget)

        # Connect zoom controls to synchronize between curve and strat views
        self.zoomSlider.valueChanged.connect(self.on_zoom_changed)
        self.zoomSpinBox.valueChanged.connect(self.on_zoom_changed)

        # Initialize empty table
        # Note: setRowCount is not needed for QTableView with PandasModel
        # The model will handle row count automatically
        self.editorTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def on_zoom_changed(self):
        """Handle zoom control changes and apply synchronized zoom to both views."""
        # Get zoom value from the sender to avoid recursive calls
        sender = self.sender()
        if sender == self.zoomSlider:
            zoom_percentage = self.zoomSlider.value()
            self.zoomSpinBox.blockSignals(True)  # Prevent recursive call
            self.zoomSpinBox.setValue(zoom_percentage)
            self.zoomSpinBox.blockSignals(False)
        else:
            zoom_percentage = self.zoomSpinBox.value()
            self.zoomSlider.blockSignals(True)  # Prevent recursive call
            self.zoomSlider.setValue(int(zoom_percentage))
            self.zoomSlider.blockSignals(False)

        # Apply zoom to both views
        zoom_factor = zoom_percentage / 100.0  # Convert percentage to factor (1.0 = 100%)
        self.apply_synchronized_zoom(zoom_factor)

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
                # Apply changes: save settings and clear dirty flag
                self.update_settings(auto_save=False)
            elif reply == QMessageBox.StandardButton.Discard:
                # Discard changes: revert to saved settings
                self.revert_to_saved_settings()
            elif reply == QMessageBox.StandardButton.Cancel:
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
            'long_space_density': self.longSpaceDensityComboBox.currentText()
        }
        if not mnemonic_map['gamma'] or not mnemonic_map['density']:
            QMessageBox.warning(self, "Missing Curve Mapping", "Please select both Gamma Ray and Density curves.")
            return
        # Ensure lithology rules are up-to-date from the settings table before running analysis
        self.save_settings_rules_from_table(show_message=False)

        self.thread = QThread()
        # Pass mnemonic_map to the Worker
        use_fallback_classification = self.fallbackClassificationCheckBox.isChecked()
        self.worker = Worker(self.las_file_path, mnemonic_map, self.lithology_rules, self.use_researched_defaults, self.merge_thin_units, self.merge_threshold, self.smart_interbedding, self.smart_interbedding_max_sequence_length, self.smart_interbedding_thick_unit_threshold, use_fallback_classification)
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
        self.runAnalysisButton.setEnabled(True)

        # Store recent analysis results for reporting
        self.last_classified_dataframe = classified_dataframe.copy()
        self.last_units_dataframe = units_dataframe.copy()
        self.last_analysis_file = self.las_file_path
        self.last_analysis_timestamp = pd.Timestamp.now()

        # Check for smart interbedding suggestions if enabled
        print(f"DEBUG: Smart interbedding enabled check: {self.smart_interbedding}")
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
            return
        
        column_names = model._dataframe.columns.tolist()
        
        # Map internal names to column indices
        for internal_name, is_visible in visibility_map.items():
            if internal_name in column_names:
                col_index = column_names.index(internal_name)
                table.setColumnHidden(col_index, not is_visible)
            else:
                # Try to find by display name (replace underscores with spaces)
                display_name = internal_name.replace('_', ' ').title()
                for idx, col in enumerate(column_names):
                    if col == internal_name or col == display_name:
                        table.setColumnHidden(idx, not is_visible)
                        break
    
    def refresh_range_visualization(self):
        """Refresh the range gap visualization with current lithology rules"""
        # Get current rules from the table
        current_rules = []
        for row_idx in range(self.settings_rules_table.rowCount()):
            rule = {}
            rule['name'] = self.settings_rules_table.cellWidget(row_idx, 0).currentText()
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
                    # Filter units by both code and qualifier for unique combinations
                    mask = (units_df[LITHOLOGY_COLUMN] == rule_code)
                    if rule_qualifier and 'lithology_qualifier' in units_df.columns:
                        mask = mask & (units_df['lithology_qualifier'] == rule_qualifier)

                    matching_units = units_df[mask]
                    if not matching_units.empty:
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
        
        # Update curve plotter with lithology data for boundary lines (Phase 4)
        if hasattr(self.curvePlotter, 'set_lithology_data'):
            self.curvePlotter.set_lithology_data(editor_dataframe)

        # Update stratigraphic column
        if hasattr(self, 'stratigraphicColumnView'):
            separator_thickness = self.separatorThicknessSpinBox.value()
            draw_separators = self.drawSeparatorsCheckBox.isChecked()
            if self.last_classified_dataframe is not None:
                min_depth = self.last_classified_dataframe[DEPTH_COLUMN].min()
                max_depth = self.last_classified_dataframe[DEPTH_COLUMN].max()
                self.stratigraphicColumnView.draw_column(updated_df, min_depth, max_depth, separator_thickness, draw_separators)

        QMessageBox.information(self, "Interbedding Created", f"Successfully created interbedding with {len(new_rows)} components.")

    def _check_smart_interbedding_suggestions(self, units_dataframe, classified_dataframe):
        """Check for smart interbedding suggestions and show dialog if found."""
        try:
            # Debug: Method Entry
            print("DEBUG: _check_smart_interbedding_suggestions method called")
            print(f"DEBUG: Smart interbedding enabled: {self.smart_interbedding}")
            print(f"DEBUG: Max sequence length: {self.smart_interbedding_max_sequence_length}")
            print(f"DEBUG: Thick unit threshold: {self.smart_interbedding_thick_unit_threshold}")

            # Debug: Input Validation
            print(f"DEBUG: Units dataframe shape: {units_dataframe.shape if hasattr(units_dataframe, 'shape') else 'No shape'}")
            print(f"DEBUG: Units dataframe columns: {list(units_dataframe.columns) if hasattr(units_dataframe, 'columns') else 'No columns'}")
            print(f"DEBUG: First 5 units: {units_dataframe.head() if hasattr(units_dataframe, 'head') else 'No head method'}")
            print(f"DEBUG: Classified dataframe shape: {classified_dataframe.shape if hasattr(classified_dataframe, 'shape') else 'No shape'}")

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

            print(f"DEBUG: Found {len(candidates) if candidates else 0} interbedding candidates")

            if candidates:
                print("DEBUG: Candidates found, creating SmartInterbeddingSuggestionsDialog")
                # Debug: Show candidate details
                for i, candidate in enumerate(candidates):
                    print(f"DEBUG: Candidate {i}: from_depth={candidate.get('from_depth')}, to_depth={candidate.get('to_depth')}, lithologies={len(candidate.get('lithologies', []))}")

                # Show suggestions dialog
                from .dialogs.smart_interbedding_suggestions_dialog import SmartInterbeddingSuggestionsDialog
                dialog = SmartInterbeddingSuggestionsDialog(candidates, self)
                print("DEBUG: SmartInterbeddingSuggestionsDialog created")

                dialog_result = dialog.exec()
                print(f"DEBUG: Dialog exec() returned: {dialog_result}")

                if dialog_result:
                    print("DEBUG: Dialog accepted, getting selected candidates")
                    # Apply selected suggestions
                    selected_indices = dialog.get_selected_candidates()
                    print(f"DEBUG: Selected candidate indices: {selected_indices}")

                    if selected_indices:
                        print("DEBUG: Applying interbedding candidates")
                        updated_units_df = analyzer.apply_interbedding_candidates(
                            units_dataframe, candidates, selected_indices, self.lithology_rules
                        )
                        # Update stored dataframe
                        self.last_units_dataframe = updated_units_df
                        print(f"DEBUG: Updated units dataframe shape: {updated_units_df.shape if hasattr(updated_units_df, 'shape') else 'No shape'}")
                    else:
                        print("DEBUG: No candidates selected")
                else:
                    print("DEBUG: Dialog rejected")

                # Continue to finalize display regardless of user choice
                print("DEBUG: Finalizing analysis display with updated dataframe")
                self._finalize_analysis_display(self.last_units_dataframe, classified_dataframe)
            else:
                print("DEBUG: No candidates found, proceeding with normal display")
                # No candidates found, proceed normally
                self._finalize_analysis_display(units_dataframe, classified_dataframe)

        except Exception as e:
            # Log error and continue with normal display
            print(f"DEBUG: Exception in smart interbedding suggestions: {e}")
            import traceback
            traceback.print_exc()
            self._finalize_analysis_display(units_dataframe, classified_dataframe)

    def _finalize_analysis_display(self, units_dataframe, classified_dataframe):
        """Finalize the analysis display after all processing is complete."""
        # Get separator settings from UI controls
        separator_thickness = self.separatorThicknessSpinBox.value()
        draw_separators = self.drawSeparatorsCheckBox.isChecked()

        # Calculate overall min and max depth from the classified_dataframe
        # This ensures both plots use the same consistent depth scale
        min_overall_depth = classified_dataframe[DEPTH_COLUMN].min()
        max_overall_depth = classified_dataframe[DEPTH_COLUMN].max()

        # Pass the overall depth range to the stratigraphic column
        self.stratigraphicColumnView.draw_column(units_dataframe, min_overall_depth, max_overall_depth, separator_thickness, draw_separators)

        # Prepare curve configurations for the single CurvePlotter
        curve_configs = []
        curve_inversion_settings = {
            'gamma': self.invertGammaCheckBox.isChecked(),
            'short_space_density': self.invertShortSpaceDensityCheckBox.isChecked(),
            'long_space_density': self.invertLongSpaceDensityCheckBox.isChecked()
        }
        current_curve_thickness = self.curveThicknessSpinBox.value()

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

        # Update the single curve plotter and set its depth range
        self.curvePlotter.set_curve_configs(curve_configs)
        self.curvePlotter.set_data(classified_dataframe)
        self.curvePlotter.set_depth_range(min_overall_depth, max_overall_depth)
        
        # Set bit size for anomaly detection
        if hasattr(self.curvePlotter, 'set_bit_size'):
            current_bit_size_mm = self.bitSizeSpinBox.value() if hasattr(self, 'bitSizeSpinBox') else self.bit_size_mm
            self.curvePlotter.set_bit_size(current_bit_size_mm)

        # Use 37-column schema for editor display
        # First ensure all columns are present
        for col in COALLOG_V31_COLUMNS:
            if col not in units_dataframe.columns:
                units_dataframe[col] = ''
        
        # Use the full 37-column schema
        editor_dataframe = units_dataframe[COALLOG_V31_COLUMNS]
        self.editorTable.load_data(editor_dataframe)
        
        # Set lithology data on curve plotter for boundary lines (Phase 4)
        if hasattr(self.curvePlotter, 'set_lithology_data'):
            self.curvePlotter.set_lithology_data(editor_dataframe)
        
        # Activate the editor subwindow in MDI area
        if hasattr(self, 'mdi_area') and hasattr(self, 'editor_subwindow'):
            self.mdi_area.setActiveSubWindow(self.editor_subwindow)
            self.editor_subwindow.show()
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
            # Log error but don't crash the application
            print(f"Error updating gap visualization: {e}")
            import traceback
            traceback.print_exc()
