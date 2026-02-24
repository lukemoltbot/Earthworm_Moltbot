"""
InformationPanel component - tabbed panel showing info about selected interval.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QTextEdit
from PyQt6.QtCore import Qt
from typing import Optional
from src.ui.graphic_window.state import DepthStateManager, DepthRange


class InformationPanel(QWidget):
    """
    Bottom panel: Tabbed information display.
    
    Tabs:
    1. Info - Selected interval details
    2. Core Photo - Placeholder for core photos
    3. Quality - Quality control information
    4. Validation - Validation results
    """
    
    def __init__(self, depth_state_manager: DepthStateManager,
                 depth_coord_system=None):  # depth_coord_system not used but kept for consistency
        super().__init__()
        
        self.state = depth_state_manager
        
        self.setMinimumHeight(150)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.info_tab = self.create_info_tab()
        self.core_photo_tab = self.create_core_photo_tab()
        self.quality_tab = self.create_quality_tab()
        self.validation_tab = self.create_validation_tab()
        
        # Add tabs
        self.tab_widget.addTab(self.info_tab, "Info")
        self.tab_widget.addTab(self.core_photo_tab, "Core Photo")
        self.tab_widget.addTab(self.quality_tab, "Quality")
        self.tab_widget.addTab(self.validation_tab, "Validation")
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tab_widget)
        
        # Subscribe to state changes
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        
        self.selected_range: Optional[DepthRange] = None
        self.cursor_depth: Optional[float] = None
    
    def create_info_tab(self) -> QWidget:
        """Create Info tab with selected interval details."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("Select an interval to see details...")
        
        layout.addWidget(self.info_text)
        return tab
    
    def create_core_photo_tab(self) -> QWidget:
        """Create Core Photo tab (placeholder)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel("Core Photo Viewer\n\n"
                      "This area will display core photos when available.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        return tab
    
    def create_quality_tab(self) -> QWidget:
        """Create Quality tab (placeholder)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel("Quality Control Information\n\n"
                      "Quality metrics and validation results will appear here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        return tab
    
    def create_validation_tab(self) -> QWidget:
        """Create Validation tab (placeholder)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        label = QLabel("Validation Results\n\n"
                      "Validation checks and results will appear here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(label)
        return tab
    
    def on_selection_changed(self, depth_range: Optional[DepthRange]):
        """Selection changed - update info tab."""
        self.selected_range = depth_range
        self.update_info_tab()
    
    def on_cursor_changed(self, depth: float):
        """Cursor changed - update info tab."""
        self.cursor_depth = depth
        self.update_info_tab()
    
    def update_info_tab(self):
        """Update info tab with current selection and cursor info."""
        if self.selected_range is None:
            self.info_text.setPlainText("No interval selected.")
            return
        
        text = f"""SELECTED INTERVAL
From: {self.selected_range.from_depth:.2f} m
To: {self.selected_range.to_depth:.2f} m
Thickness: {self.selected_range.range_size:.2f} m

"""
        
        if self.cursor_depth is not None:
            text += f"CURSOR DEPTH: {self.cursor_depth:.2f} m\n"
        
        self.info_text.setPlainText(text)