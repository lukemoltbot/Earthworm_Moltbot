#!/usr/bin/env python3
"""
Enhanced Stratigraphic Column Demo

This script demonstrates the enhanced stratigraphic column with real-time
synchronization to a mock curve plotter.
"""

import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from src.ui.widgets.enhanced_stratigraphic_column import EnhancedStratigraphicColumn
from src.core.config import LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN


class MockCurvePlotter:
    """Mock curve plotter for demonstration."""
    
    def __init__(self):
        self.view_range_changed_callbacks = []
        self.last_y_range = (0.0, 100.0)
        self.plot_widget = self  # For compatibility
        
    def viewRangeChanged(self):
        """Return a mock signal connector."""
        return self
        
    def connect(self, callback):
        """Connect a callback to viewRangeChanged signal."""
        self.view_range_changed_callbacks.append(callback)
        
    def setYRange(self, y_min, y_max):
        """Mock setYRange method."""
        self.last_y_range = (y_min, y_max)
        print(f"Mock plotter: Y range set to {y_min:.1f}-{y_max:.1f}m")
        
    def viewRange(self):
        """Mock viewRange method."""
        return [(0, 1), self.last_y_range]
        
    def emit_view_range_changed(self, min_depth, max_depth):
        """Emit view range changed signal."""
        print(f"Mock plotter: Emitting view range changed {min_depth:.1f}-{max_depth:.1f}m")
        for callback in self.view_range_changed_callbacks:
            callback(min_depth, max_depth)


class DemoWindow(QMainWindow):
    """Demo window showing enhanced stratigraphic column features."""
    
    def __init__(self):
        super().__init__()
        
        # Create sample lithology data
        self.sample_data = pd.DataFrame({
            'from_depth': [0.0, 5.0, 12.0, 18.0, 25.0, 32.0, 40.0, 48.0],
            'to_depth': [5.0, 12.0, 18.0, 25.0, 32.0, 40.0, 48.0, 55.0],
            RECOVERED_THICKNESS_COLUMN: [5.0, 7.0, 6.0, 7.0, 7.0, 8.0, 8.0, 7.0],
            LITHOLOGY_COLUMN: [1, 2, 3, 4, 5, 6, 7, 8],
            'lithology_qualifier': [
                'Sandstone', 'Shale', 'Coal', 'Limestone',
                'Sandstone', 'Shale', 'Coal', 'Limestone'
            ],
            'background_color': [
                '#FFCCCC', '#CCFFCC', '#CCCCFF', '#FFFFCC',
                '#FFCCCC', '#CCFFCC', '#CCCCFF', '#FFFFCC'
            ],
            'svg_path': ['', '', '', '', '', '', '', '']
        })
        
        # Create widgets
        self.strat_column = EnhancedStratigraphicColumn()
        self.mock_plotter = MockCurvePlotter()
        
        # Set up synchronization
        self.strat_column.sync_with_curve_plotter(self.mock_plotter)
        
        # Create control widgets
        self.setup_controls()
        
        # Set up UI
        self.setup_ui()
        
        # Draw initial column
        self.strat_column.draw_column(self.sample_data, 0.0, 55.0)
        
        # Set window properties
        self.setWindowTitle("Enhanced Stratigraphic Column Demo")
        self.setGeometry(100, 100, 1200, 800)
        
    def setup_controls(self):
        """Create control widgets for the demo."""
        # Sync controls
        self.sync_checkbox = QCheckBox("Enable Synchronization")
        self.sync_checkbox.setChecked(True)
        self.sync_checkbox.stateChanged.connect(self.on_sync_changed)
        
        # Label controls
        self.labels_checkbox = QCheckBox("Show Detailed Labels")
        self.labels_checkbox.setChecked(True)
        self.labels_checkbox.stateChanged.connect(self.on_labels_changed)
        
        self.codes_checkbox = QCheckBox("Show Lithology Codes")
        self.codes_checkbox.setChecked(True)
        self.codes_checkbox.stateChanged.connect(self.on_codes_changed)
        
        self.thickness_checkbox = QCheckBox("Show Thickness Values")
        self.thickness_checkbox.setChecked(True)
        self.thickness_checkbox.stateChanged.connect(self.on_thickness_changed)
        
        self.qualifiers_checkbox = QCheckBox("Show Qualifiers")
        self.qualifiers_checkbox.setChecked(True)
        self.qualifiers_checkbox.stateChanged.connect(self.on_qualifiers_changed)
        
        # Gradient controls
        self.gradient_checkbox = QCheckBox("Enable Gradient Highlighting")
        self.gradient_checkbox.setChecked(True)
        self.gradient_checkbox.stateChanged.connect(self.on_gradient_changed)
        
        # Scroll controls
        self.scroll_label = QLabel("Scroll to Depth (m):")
        self.scroll_spinbox = QDoubleSpinBox()
        self.scroll_spinbox.setRange(0.0, 55.0)
        self.scroll_spinbox.setValue(27.5)
        self.scroll_spinbox.setSingleStep(5.0)
        self.scroll_button = QPushButton("Scroll")
        self.scroll_button.clicked.connect(self.on_scroll_clicked)
        
        # Mock plotter controls
        self.plotter_label = QLabel("Mock Plotter Range (m):")
        self.plotter_min_spinbox = QDoubleSpinBox()
        self.plotter_min_spinbox.setRange(0.0, 50.0)
        self.plotter_min_spinbox.setValue(10.0)
        self.plotter_max_spinbox = QDoubleSpinBox()
        self.plotter_max_spinbox.setRange(5.0, 55.0)
        self.plotter_max_spinbox.setValue(35.0)
        self.plotter_button = QPushButton("Update Plotter")
        self.plotter_button.clicked.connect(self.on_plotter_updated)
        
        # Unit selection
        self.unit_label = QLabel("Select Unit (0-7):")
        self.unit_spinbox = QSpinBox()
        self.unit_spinbox.setRange(0, 7)
        self.unit_spinbox.setValue(0)
        self.unit_button = QPushButton("Select Unit")
        self.unit_button.clicked.connect(self.on_unit_selected)
        
        # Status label
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        
    def setup_ui(self):
        """Set up the UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Add stratigraphic column
        main_layout.addWidget(self.strat_column, 3)
        
        # Create control panels
        controls_layout = QHBoxLayout()
        
        # Sync controls group
        sync_group = QGroupBox("Synchronization")
        sync_layout = QVBoxLayout()
        sync_layout.addWidget(self.sync_checkbox)
        sync_layout.addStretch()
        sync_group.setLayout(sync_layout)
        controls_layout.addWidget(sync_group)
        
        # Label controls group
        label_group = QGroupBox("Label Display")
        label_layout = QVBoxLayout()
        label_layout.addWidget(self.labels_checkbox)
        label_layout.addWidget(self.codes_checkbox)
        label_layout.addWidget(self.thickness_checkbox)
        label_layout.addWidget(self.qualifiers_checkbox)
        label_group.setLayout(label_layout)
        controls_layout.addWidget(label_group)
        
        # Visualization group
        viz_group = QGroupBox("Visualization")
        viz_layout = QVBoxLayout()
        viz_layout.addWidget(self.gradient_checkbox)
        viz_group.setLayout(viz_layout)
        controls_layout.addWidget(viz_group)
        
        # Scroll controls group
        scroll_group = QGroupBox("Scroll Control")
        scroll_layout = QVBoxLayout()
        scroll_row = QHBoxLayout()
        scroll_row.addWidget(self.scroll_label)
        scroll_row.addWidget(self.scroll_spinbox)
        scroll_row.addWidget(self.scroll_button)
        scroll_layout.addLayout(scroll_row)
        scroll_group.setLayout(scroll_layout)
        controls_layout.addWidget(scroll_group)
        
        # Plotter controls group
        plotter_group = QGroupBox("Mock Plotter Control")
        plotter_layout = QVBoxLayout()
        plotter_row1 = QHBoxLayout()
        plotter_row1.addWidget(self.plotter_label)
        plotter_layout.addLayout(plotter_row1)
        plotter_row2 = QHBoxLayout()
        plotter_row2.addWidget(QLabel("Min:"))
        plotter_row2.addWidget(self.plotter_min_spinbox)
        plotter_row2.addWidget(QLabel("Max:"))
        plotter_row2.addWidget(self.plotter_max_spinbox)
        plotter_row2.addWidget(self.plotter_button)
        plotter_layout.addLayout(plotter_row2)
        plotter_group.setLayout(plotter_layout)
        controls_layout.addWidget(plotter_group)
        
        # Unit selection group
        unit_group = QGroupBox("Unit Selection")
        unit_layout = QVBoxLayout()
        unit_row = QHBoxLayout()
        unit_row.addWidget(self.unit_label)
        unit_row.addWidget(self.unit_spinbox)
        unit_row.addWidget(self.unit_button)
        unit_layout.addLayout(unit_row)
        unit_group.setLayout(unit_layout)
        controls_layout.addWidget(unit_group)
        
        main_layout.addLayout(controls_layout)
        
        # Add status label
        main_layout.addWidget(self.status_label)
        
        # Connect enhanced signals for status updates
        self.strat_column.depthScrolled.connect(self.on_depth_scrolled)
        self.strat_column.unitSelected.connect(self.on_enhanced_unit_selected)
        self.strat_column.depthRangeChanged.connect(self.on_depth_range_changed)
        
    def on_sync_changed(self, state):
        """Handle sync checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.strat_column.set_sync_enabled(enabled)
        self.status_label.setText(f"Status: Synchronization {'enabled' if enabled else 'disabled'}")
        
    def on_labels_changed(self, state):
        """Handle labels checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.strat_column.set_detailed_labels_enabled(enabled)
        self.redraw_column()
        
    def on_codes_changed(self, state):
        """Handle codes checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.strat_column.set_lithology_codes_enabled(enabled)
        self.redraw_column()
        
    def on_thickness_changed(self, state):
        """Handle thickness checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.strat_column.set_thickness_values_enabled(enabled)
        self.redraw_column()
        
    def on_qualifiers_changed(self, state):
        """Handle qualifiers checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.strat_column.set_qualifiers_enabled(enabled)
        self.redraw_column()
        
    def on_gradient_changed(self, state):
        """Handle gradient checkbox change."""
        enabled = state == Qt.CheckState.Checked.value
        self.strat_column.set_highlight_gradient_enabled(enabled)
        self.redraw_column()
        
    def on_scroll_clicked(self):
        """Handle scroll button click."""
        depth = self.scroll_spinbox.value()
        self.strat_column.scroll_to_depth(depth)
        self.status_label.setText(f"Status: Scrolled to {depth:.1f}m")
        
    def on_plotter_updated(self):
        """Handle plotter update button click."""
        min_depth = self.plotter_min_spinbox.value()
        max_depth = self.plotter_max_spinbox.value()
        self.mock_plotter.emit_view_range_changed(min_depth, max_depth)
        self.status_label.setText(f"Status: Plotter range updated to {min_depth:.1f}-{max_depth:.1f}m")
        
    def on_unit_selected(self):
        """Handle unit selection button click."""
        unit_index = self.unit_spinbox.value()
        self.strat_column.highlight_unit(unit_index)
        self.status_label.setText(f"Status: Unit {unit_index} selected")
        
    def on_depth_scrolled(self, center_depth):
        """Handle depth scrolled signal."""
        self.status_label.setText(f"Status: Column scrolled to {center_depth:.1f}m (center)")
        
    def on_enhanced_unit_selected(self, unit_index):
        """Handle enhanced unit selected signal."""
        self.unit_spinbox.setValue(unit_index)
        self.status_label.setText(f"Status: Unit {unit_index} selected via click")
        
    def on_depth_range_changed(self, min_depth, max_depth):
        """Handle depth range changed signal."""
        # Update scroll spinbox to show center
        center_depth = (min_depth + max_depth) / 2
        self.scroll_spinbox.setValue(center_depth)
        
    def redraw_column(self):
        """Redraw the column with current settings."""
        self.strat_column.draw_column(self.sample_data, 0.0, 55.0)
        self.status_label.setText("Status: Column redrawn with current settings")


def main():
    """Main function to run the demo."""
    app = QApplication(sys.argv)
    
    # Create and show demo window
    window = DemoWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    print("Enhanced Stratigraphic Column Demo")
    print("==================================")
    print("Features demonstrated:")
    print("1. Real-time synchronization with mock curve plotter")
    print("2. Detailed lithology unit labels")
    print("3. Configurable display options")
    print("4. Unit selection highlighting")
    print("5. Depth synchronization signals")
    print()
    
    main()