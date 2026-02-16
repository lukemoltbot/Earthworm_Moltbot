"""
Layout Manager Dialog - Manage custom layouts.

This dialog provides:
1. List of custom layouts
2. Ability to rename layouts
3. Ability to delete layouts
4. Preview of layout settings
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QGroupBox, QFormLayout,
    QMessageBox, QDialogButtonBox, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QInputDialog
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, pyqtSignal
import json
from ...ui.layout_presets import LayoutManager, LayoutPreset


class LayoutManagerDialog(QDialog):
    """Dialog for managing custom layouts."""
    
    # Signals
    layoutRenamed = pyqtSignal(str, str)  # old_name, new_name
    layoutDeleted = pyqtSignal(str)  # layout_name
    layoutApplied = pyqtSignal(str)  # layout_name
    
    def __init__(self, parent=None, layout_manager: LayoutManager = None):
        super().__init__(parent)
        self.layout_manager = layout_manager or LayoutManager()
        self.current_layout = None
        
        self.setWindowTitle("Manage Custom Layouts")
        self.setMinimumSize(700, 500)
        
        self._create_ui()
        self._load_layouts()
    
    def _create_ui(self):
        """Create dialog UI."""
        main_layout = QVBoxLayout(self)
        
        # Create splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Layout list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # List label
        list_label = QLabel("Custom Layouts:")
        list_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        left_layout.addWidget(list_label)
        
        # Layout list
        self.layout_list = QListWidget()
        self.layout_list.itemSelectionChanged.connect(self._on_layout_selected)
        self.layout_list.itemDoubleClicked.connect(self._apply_selected_layout)
        left_layout.addWidget(self.layout_list)
        
        # List buttons
        list_buttons_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self._apply_selected_layout)
        self.apply_button.setEnabled(False)
        list_buttons_layout.addWidget(self.apply_button)
        
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self._rename_selected_layout)
        self.rename_button.setEnabled(False)
        list_buttons_layout.addWidget(self.rename_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._delete_selected_layout)
        self.delete_button.setEnabled(False)
        list_buttons_layout.addWidget(self.delete_button)
        
        left_layout.addLayout(list_buttons_layout)
        
        # Right side: Layout details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Details label
        details_label = QLabel("Layout Details:")
        details_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(details_label)
        
        # Details form
        details_group = QGroupBox("Properties")
        details_form = QFormLayout(details_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        details_form.addRow("Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setReadOnly(True)
        self.description_edit.setMaximumHeight(80)
        details_form.addRow("Description:", self.description_edit)
        
        right_layout.addWidget(details_group)
        
        # Settings table
        settings_group = QGroupBox("Layout Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        self.settings_table = QTableWidget()
        self.settings_table.setColumnCount(2)
        self.settings_table.setHorizontalHeaderLabels(["Setting", "Value"])
        self.settings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.settings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.settings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.settings_table.setAlternatingRowColors(True)
        settings_layout.addWidget(self.settings_table)
        
        right_layout.addWidget(settings_group)
        
        # Add stretch
        right_layout.addStretch()
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 450])
        
        main_layout.addWidget(splitter)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def _load_layouts(self):
        """Load custom layouts into the list."""
        self.layout_list.clear()
        
        custom_layouts = self.layout_manager.custom_layouts
        
        if not custom_layouts:
            item = QListWidgetItem("No custom layouts saved")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Disable selection
            self.layout_list.addItem(item)
            return
        
        for name in sorted(custom_layouts.keys()):
            item = QListWidgetItem(name)
            self.layout_list.addItem(item)
    
    def _on_layout_selected(self):
        """Handle layout selection change."""
        selected_items = self.layout_list.selectedItems()
        
        if not selected_items:
            self.current_layout = None
            self._clear_details()
            self.apply_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return
        
        layout_name = selected_items[0].text()
        
        # Check if it's a valid layout (not the "no layouts" placeholder)
        if layout_name == "No custom layouts saved":
            self.current_layout = None
            self._clear_details()
            self.apply_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            return
        
        # Load layout details
        preset = self.layout_manager.get_custom_layout(layout_name)
        if preset:
            self.current_layout = preset
            self._display_layout_details(preset)
            self.apply_button.setEnabled(True)
            self.rename_button.setEnabled(True)
            self.delete_button.setEnabled(True)
    
    def _clear_details(self):
        """Clear layout details display."""
        self.name_edit.clear()
        self.description_edit.clear()
        self.settings_table.setRowCount(0)
    
    def _display_layout_details(self, preset: LayoutPreset):
        """Display layout details."""
        self.name_edit.setText(preset.name)
        self.description_edit.setText(preset.description)
        
        # Display settings in table
        self.settings_table.setRowCount(0)
        
        # Add splitter sizes
        if preset.splitter_sizes:
            row = self.settings_table.rowCount()
            self.settings_table.insertRow(row)
            self.settings_table.setItem(row, 0, QTableWidgetItem("Splitter Sizes"))
            self.settings_table.setItem(row, 1, QTableWidgetItem(str(preset.splitter_sizes)))
        
        # Add widget visibility
        if preset.widget_visibility:
            row = self.settings_table.rowCount()
            self.settings_table.insertRow(row)
            self.settings_table.setItem(row, 0, QTableWidgetItem("Visible Widgets"))
            visible_widgets = [w for w, v in preset.widget_visibility.items() if v]
            hidden_widgets = [w for w, v in preset.widget_visibility.items() if not v]
            value = f"Visible: {len(visible_widgets)}, Hidden: {len(hidden_widgets)}"
            self.settings_table.setItem(row, 1, QTableWidgetItem(value))
        
        # Add scale settings
        row = self.settings_table.rowCount()
        self.settings_table.insertRow(row)
        self.settings_table.setItem(row, 0, QTableWidgetItem("Depth Scale"))
        self.settings_table.setItem(row, 1, QTableWidgetItem(f"{preset.depth_scale} px/m"))
        
        row = self.settings_table.rowCount()
        self.settings_table.insertRow(row)
        self.settings_table.setItem(row, 0, QTableWidgetItem("Default Zoom"))
        self.settings_table.setItem(row, 1, QTableWidgetItem(f"{preset.default_zoom:.2f}x"))
    
    def _apply_selected_layout(self):
        """Apply the selected layout."""
        if not self.current_layout:
            return
        
        self.layoutApplied.emit(self.current_layout.name)
        self.accept()
    
    def _rename_selected_layout(self):
        """Rename the selected layout."""
        if not self.current_layout:
            return
        
        old_name = self.current_layout.name
        
        # Get new name from user
        new_name, ok = QInputDialog.getText(
            self, "Rename Layout", "Enter new name:", 
            QLineEdit.EchoMode.Normal, old_name
        )
        
        if not ok or not new_name.strip():
            return
        
        new_name = new_name.strip()
        
        # Check if name already exists
        if new_name in self.layout_manager.custom_layouts and new_name != old_name:
            QMessageBox.warning(
                self, "Name Exists", 
                f"A layout named '{new_name}' already exists. Please choose a different name."
            )
            return
        
        # Rename layout
        if new_name != old_name:
            # Update in layout manager
            layout_data = self.layout_manager.custom_layouts.pop(old_name)
            self.layout_manager.custom_layouts[new_name] = layout_data
            self.layout_manager.settings.setValue(
                "custom_layouts", 
                json.dumps(self.layout_manager.custom_layouts)
            )
            
            # Emit signal
            self.layoutRenamed.emit(old_name, new_name)
            
            # Reload list
            self._load_layouts()
            
            # Select renamed item
            for i in range(self.layout_list.count()):
                item = self.layout_list.item(i)
                if item.text() == new_name:
                    self.layout_list.setCurrentItem(item)
                    break
    
    def _delete_selected_layout(self):
        """Delete the selected layout."""
        if not self.current_layout:
            return
        
        layout_name = self.current_layout.name
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete the layout '{layout_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete from layout manager
            self.layout_manager.delete_custom_layout(layout_name)
            
            # Emit signal
            self.layoutDeleted.emit(layout_name)
            
            # Reload list
            self._load_layouts()
            
            # Clear details
            self._clear_details()
            self.apply_button.setEnabled(False)
            self.rename_button.setEnabled(False)
            self.delete_button.setEnabled(False)
    
    def set_layout_manager(self, layout_manager: LayoutManager):
        """Set the layout manager and reload layouts."""
        self.layout_manager = layout_manager
        self._load_layouts()