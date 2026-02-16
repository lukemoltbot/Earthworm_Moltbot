"""
Save Layout Dialog - Save current window layout as a custom preset.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit, 
    QTextEdit, QDialogButtonBox, QMessageBox, QGroupBox, QFormLayout,
    QCheckBox, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ...ui.layout_presets import LayoutPreset


class SaveLayoutDialog(QDialog):
    """Dialog for saving current layout as a custom preset."""
    
    def __init__(self, parent=None, existing_layouts=None):
        super().__init__(parent)
        self.existing_layouts = existing_layouts or []
        
        self.setWindowTitle("Save Custom Layout")
        self.setMinimumWidth(400)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Save your current window layout as a custom preset. "
            "You can apply this layout later from the Layout toolbar."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Form group
        form_group = QGroupBox("Layout Details")
        form_layout = QFormLayout(form_group)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter layout name")
        self.name_edit.textChanged.connect(self._validate_name)
        form_layout.addRow("Name:", self.name_edit)
        
        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe this layout...")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.include_scale_checkbox = QCheckBox("Include current depth scale")
        self.include_scale_checkbox.setChecked(True)
        self.include_scale_checkbox.setToolTip("Save the current depth scale (pixels per metre)")
        options_layout.addWidget(self.include_scale_checkbox)
        
        self.include_zoom_checkbox = QCheckBox("Include current zoom level")
        self.include_zoom_checkbox.setChecked(True)
        self.include_zoom_checkbox.setToolTip("Save the current zoom factor")
        options_layout.addWidget(self.include_zoom_checkbox)
        
        self.include_widget_visibility_checkbox = QCheckBox("Include widget visibility")
        self.include_widget_visibility_checkbox.setChecked(True)
        self.include_widget_visibility_checkbox.setToolTip("Save which widgets are visible/hidden")
        options_layout.addWidget(self.include_widget_visibility_checkbox)
        
        self.include_splitter_sizes_checkbox = QCheckBox("Include splitter sizes")
        self.include_splitter_sizes_checkbox.setChecked(True)
        self.include_splitter_sizes_checkbox.setToolTip("Save the current splitter positions")
        options_layout.addWidget(self.include_splitter_sizes_checkbox)
        
        form_layout.addRow(options_group)
        
        layout.addWidget(form_group)
        
        # Dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        
        # Initially disable save button
        self.save_button = self.button_box.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setEnabled(False)
        
        layout.addWidget(self.button_box)
    
    def _validate_name(self):
        """Validate the layout name."""
        name = self.name_edit.text().strip()
        
        if not name:
            self.save_button.setEnabled(False)
            return
        
        # Check if name already exists
        if name in self.existing_layouts:
            self.save_button.setEnabled(False)
            self.name_edit.setStyleSheet("border: 1px solid red;")
            return
        else:
            self.name_edit.setStyleSheet("")
        
        self.save_button.setEnabled(True)
    
    def _validate_and_accept(self):
        """Validate input and accept dialog."""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a layout name.")
            return
        
        if name in self.existing_layouts:
            QMessageBox.warning(
                self, "Name Exists", 
                f"A layout named '{name}' already exists. Please choose a different name."
            )
            return
        
        self.accept()
    
    def get_layout_name(self) -> str:
        """Get the entered layout name."""
        return self.name_edit.text().strip()
    
    def get_layout_description(self) -> str:
        """Get the entered layout description."""
        return self.description_edit.toPlainText().strip()
    
    def get_options(self) -> dict:
        """Get the selected options."""
        return {
            'include_scale': self.include_scale_checkbox.isChecked(),
            'include_zoom': self.include_zoom_checkbox.isChecked(),
            'include_widget_visibility': self.include_widget_visibility_checkbox.isChecked(),
            'include_splitter_sizes': self.include_splitter_sizes_checkbox.isChecked()
        }
    
    def set_existing_layouts(self, layouts):
        """Set the list of existing layout names."""
        self.existing_layouts = layouts
        self._validate_name()