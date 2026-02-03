"""
Theme Preview Dialog
Shows samples of the current theme for preview purposes.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QPushButton, QGroupBox, QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QSpinBox, QCheckBox, QSlider, QProgressBar,
    QTabWidget, QTextEdit, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal

class ThemePreviewDialog(QDialog):
    """Dialog showing theme preview samples."""
    
    themeChanged = pyqtSignal(str)  # Signal emitted when theme is changed
    
    def __init__(self, parent=None, current_theme="dark"):
        super().__init__(parent)
        self.current_theme = current_theme
        self.setWindowTitle("Theme Preview")
        self.setMinimumSize(600, 500)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Theme selection
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setCurrentText(self.current_theme.capitalize())
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Preview area
        preview_group = QGroupBox("Theme Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Create sample widgets
        self.create_sample_widgets(preview_layout)
        
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply Theme")
        self.apply_button.clicked.connect(self.apply_theme)
        button_layout.addWidget(self.apply_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def create_sample_widgets(self, layout):
        """Create sample widgets to demonstrate the theme."""
        
        # Sample buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(QLabel("Buttons:"))
        
        normal_button = QPushButton("Normal Button")
        button_layout.addWidget(normal_button)
        
        disabled_button = QPushButton("Disabled Button")
        disabled_button.setEnabled(False)
        button_layout.addWidget(disabled_button)
        
        layout.addLayout(button_layout)
        
        # Input fields
        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel("Input Fields:"))
        
        input_row1 = QHBoxLayout()
        input_row1.addWidget(QLabel("Text:"))
        text_edit = QTextEdit()
        text_edit.setPlainText("Sample text input")
        text_edit.setMaximumHeight(60)
        input_row1.addWidget(text_edit)
        
        input_row2 = QHBoxLayout()
        input_row2.addWidget(QLabel("Combo:"))
        combo = QComboBox()
        combo.addItems(["Option 1", "Option 2", "Option 3"])
        input_row2.addWidget(combo)
        
        input_row3 = QHBoxLayout()
        input_row3.addWidget(QLabel("Spin:"))
        spin = QSpinBox()
        spin.setValue(50)
        input_row3.addWidget(spin)
        
        input_layout.addLayout(input_row1)
        input_layout.addLayout(input_row2)
        input_layout.addLayout(input_row3)
        layout.addLayout(input_layout)
        
        # Checkboxes and radio buttons
        check_layout = QHBoxLayout()
        check_layout.addWidget(QLabel("Checkboxes:"))
        
        checkbox1 = QCheckBox("Checkbox 1")
        checkbox1.setChecked(True)
        check_layout.addWidget(checkbox1)
        
        checkbox2 = QCheckBox("Checkbox 2")
        check_layout.addWidget(checkbox2)
        
        layout.addLayout(check_layout)
        
        # Slider and progress bar
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(QLabel("Slider and Progress:"))
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setValue(75)
        slider_layout.addWidget(slider)
        
        progress = QProgressBar()
        progress.setValue(75)
        slider_layout.addWidget(progress)
        
        layout.addLayout(slider_layout)
        
        # Sample table
        table_label = QLabel("Sample Table:")
        layout.addWidget(table_label)
        
        table = QTableWidget(3, 3)
        table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        for row in range(3):
            for col in range(3):
                item = QTableWidgetItem(f"Item {row},{col}")
                table.setItem(row, col, item)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMaximumHeight(120)
        layout.addWidget(table)
        
        # Tree widget
        tree_label = QLabel("Sample Tree:")
        layout.addWidget(tree_label)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Name", "Value"])
        tree.setMaximumHeight(120)
        
        for i in range(3):
            parent = QTreeWidgetItem(tree, [f"Parent {i+1}", ""])
            for j in range(2):
                child = QTreeWidgetItem(parent, [f"Child {j+1}", f"Value {j+1}"])
        tree.expandAll()
        layout.addWidget(tree)
        
        # Status indicators
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Status Colors:"))
        
        success_label = QLabel("Success")
        success_label.setProperty("class", "success")
        status_layout.addWidget(success_label)
        
        warning_label = QLabel("Warning")
        warning_label.setProperty("class", "warning")
        status_layout.addWidget(warning_label)
        
        error_label = QLabel("Error")
        error_label.setProperty("class", "error")
        status_layout.addWidget(error_label)
        
        info_label = QLabel("Info")
        info_label.setProperty("class", "info")
        status_layout.addWidget(info_label)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
    def on_theme_changed(self, theme_name):
        """Handle theme selection change."""
        self.current_theme = theme_name.lower()
        
    def apply_theme(self):
        """Apply the selected theme."""
        self.themeChanged.emit(self.current_theme)
        self.accept()
        
    def get_selected_theme(self):
        """Get the currently selected theme."""
        return self.current_theme