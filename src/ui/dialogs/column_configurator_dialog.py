"""
Column Configurator Dialog for Earthworm Moltbot
Allows user to hide/show columns in the lithology table.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QGroupBox, QMessageBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
try:
    from coallog_37_column_schema import COALLOG_V31_COLUMNS
except ImportError:
    # Fallback to config.py if schema file not available
    from ...core.config import COALLOG_V31_COLUMNS
    # Create display names from internal names
    COALLOG_V31_COLUMNS = [(col, col.replace('_', ' ').title()) for col in COALLOG_V31_COLUMNS]


class ColumnConfiguratorDialog(QDialog):
    """Dialog for configuring column visibility in the lithology table."""
    
    # Signal emitted when column visibility changes
    visibility_changed = pyqtSignal(dict)  # dict mapping column internal name -> bool (visible)
    
    def __init__(self, parent=None, main_window=None, current_visibility=None):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent widget
            main_window: Reference to main window (for accessing settings)
            current_visibility: Dict mapping column internal names to bool (True=visible)
                               If None, all columns assumed visible.
        """
        super().__init__(parent)
        self.main_window = main_window
        self.current_visibility = current_visibility or {}
        
        self.setWindowTitle("Column Configurator")
        self.setGeometry(100, 100, 500, 600)
        self.setMinimumSize(400, 400)
        
        self.setup_ui()
        self.load_columns()
        
        # Connect signals
        self.select_all_button.clicked.connect(self.select_all)
        self.deselect_all_button.clicked.connect(self.deselect_all)
        self.filter_edit.textChanged.connect(self.filter_columns)
    
    def setup_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Title
        title_label = QLabel("Column Configurator")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(
            "Check columns to make them visible, uncheck to hide.\n"
            "Changes take effect immediately after clicking Apply."
        )
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Type to filter columns...")
        filter_layout.addWidget(self.filter_edit)
        main_layout.addLayout(filter_layout)
        
        # Column list group
        list_group = QGroupBox("Columns (37 total)")
        list_layout = QVBoxLayout(list_group)
        
        # Column list
        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.column_list.setAlternatingRowColors(True)
        list_layout.addWidget(self.column_list)
        
        # Selection buttons
        selection_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Select All")
        self.deselect_all_button = QPushButton("Deselect All")
        selection_layout.addWidget(self.select_all_button)
        selection_layout.addWidget(self.deselect_all_button)
        selection_layout.addStretch()
        list_layout.addLayout(selection_layout)
        
        main_layout.addWidget(list_group)
        
        # Status label
        self.status_label = QLabel("37 columns available")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Button group
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self.apply_changes)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def load_columns(self):
        """Load all 37 columns into the list with checkboxes."""
        self.column_list.clear()
        
        # Load column definitions
        try:
            # Try to import from schema file
            from coallog_37_column_schema import COALLOG_V31_COLUMNS as column_defs
            columns = column_defs
        except ImportError:
            # Fallback to config.py internal names
            from ...core.config import COALLOG_V31_COLUMNS as internal_names
            columns = [(name, name.replace('_', ' ').title()) for name in internal_names]
        
        self.column_definitions = columns
        
        for internal_name, display_name in columns:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, internal_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # Determine initial checked state
            if internal_name in self.current_visibility:
                is_visible = self.current_visibility[internal_name]
            else:
                # Default to visible if not specified
                is_visible = True
            
            item.setCheckState(Qt.CheckState.Checked if is_visible else Qt.CheckState.Unchecked)
            self.column_list.addItem(item)
        
        self.update_status()
    
    def filter_columns(self):
        """Filter columns based on search text."""
        filter_text = self.filter_edit.text().lower()
        
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            item_text = item.text().lower()
            item.setHidden(filter_text not in item_text)
        
        self.update_status()
    
    def update_status(self):
        """Update status label with visible/total count."""
        total = self.column_list.count()
        visible = 0
        hidden = 0
        
        for i in range(total):
            item = self.column_list.item(i)
            if not item.isHidden():
                if item.checkState() == Qt.CheckState.Checked:
                    visible += 1
                else:
                    hidden += 1
        
        self.status_label.setText(f"Visible: {visible}, Hidden: {hidden}, Filtered: {total - (visible + hidden)}")
    
    def select_all(self):
        """Select (check) all visible columns."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
        
        self.update_status()
    
    def deselect_all(self):
        """Deselect (uncheck) all visible columns."""
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            if not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)
        
        self.update_status()
    
    def get_visibility_map(self):
        """Get current visibility mapping from the list."""
        visibility = {}
        
        for i in range(self.column_list.count()):
            item = self.column_list.item(i)
            internal_name = item.data(Qt.ItemDataRole.UserRole)
            is_visible = item.checkState() == Qt.CheckState.Checked
            visibility[internal_name] = is_visible
        
        return visibility
    
    def apply_changes(self):
        """Apply visibility changes and close dialog."""
        visibility_map = self.get_visibility_map()
        
        # Count how many columns are visible
        visible_count = sum(1 for v in visibility_map.values() if v)
        hidden_count = len(visibility_map) - visible_count
        
        if visible_count == 0:
            reply = QMessageBox.question(
                self, "No Visible Columns",
                "You have hidden all columns. The table will be empty.\n"
                "Are you sure you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Emit signal with visibility map
        self.visibility_changed.emit(visibility_map)
        
        # Show confirmation
        QMessageBox.information(
            self, "Changes Applied",
            f"Column visibility updated:\n"
            f"• {visible_count} columns visible\n"
            f"• {hidden_count} columns hidden\n\n"
            f"Changes have been applied to the table."
        )
        
        self.accept()
    
    def get_selected_columns(self):
        """Get list of column internal names that are checked (visible)."""
        return [item.data(Qt.ItemDataRole.UserRole) 
                for i in range(self.column_list.count())
                for item in [self.column_list.item(i)]
                if item.checkState() == Qt.CheckState.Checked]
    
    def get_hidden_columns(self):
        """Get list of column internal names that are unchecked (hidden)."""
        return [item.data(Qt.ItemDataRole.UserRole) 
                for i in range(self.column_list.count())
                for item in [self.column_list.item(i)]
                if item.checkState() == Qt.CheckState.Unchecked]