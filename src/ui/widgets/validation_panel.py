"""
Validation Panel Widget for displaying validation results.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QTextEdit,
    QSplitter, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon

from ...core.validation import ValidationResult, ValidationIssue, ValidationSeverity


class ValidationPanel(QWidget):
    """Panel for displaying validation results."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_result: Optional[ValidationResult] = None
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with summary
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        header_layout = QHBoxLayout(self.header_frame)
        
        self.summary_label = QLabel("No validation performed")
        self.summary_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(self.summary_label)
        
        header_layout.addStretch()
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear)
        header_layout.addWidget(self.clear_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_requested)
        header_layout.addWidget(self.refresh_button)
        
        layout.addWidget(self.header_frame)
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # List view tab
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tab_widget.addTab(self.list_widget, "List View")
        
        # Tree view tab
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Severity", "Location", "Message"])
        self.tree_widget.setColumnWidth(0, 80)
        self.tree_widget.setColumnWidth(1, 120)
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.tab_widget.addTab(self.tree_widget, "Tree View")
        
        # Details tab
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.tab_widget.addTab(self.details_text, "Details")
        
        layout.addWidget(self.tab_widget)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def display_result(self, result: ValidationResult):
        """Display validation result."""
        self.current_result = result
        self.update_display()
    
    def update_display(self):
        """Update all display elements."""
        if not self.current_result:
            self.summary_label.setText("No validation performed")
            self.list_widget.clear()
            self.tree_widget.clear()
            self.details_text.clear()
            self.status_label.setText("Ready")
            return
        
        # Update summary
        errors = len(self.current_result.get_errors())
        warnings = len(self.current_result.get_warnings())
        
        if errors == 0 and warnings == 0:
            self.summary_label.setText("✓ Valid")
            self.summary_label.setStyleSheet("color: green; font-weight: bold; font-size: 12pt;")
        elif errors > 0:
            self.summary_label.setText(f"⚠ {errors} error(s), {warnings} warning(s)")
            self.summary_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        else:
            self.summary_label.setText(f"⚠ {warnings} warning(s)")
            self.summary_label.setStyleSheet("color: orange; font-weight: bold; font-size: 12pt;")
        
        # Update list view
        self.list_widget.clear()
        for issue in self.current_result.issues:
            item = QListWidgetItem(self.format_issue(issue))
            self.color_item(item, issue.severity)
            item.setData(Qt.ItemDataRole.UserRole, issue)
            self.list_widget.addItem(item)
        
        # Update tree view
        self.tree_widget.clear()
        
        # Group by severity
        error_item = QTreeWidgetItem(self.tree_widget, ["ERRORS", "", ""])
        warning_item = QTreeWidgetItem(self.tree_widget, ["WARNINGS", "", ""])
        info_item = QTreeWidgetItem(self.tree_widget, ["INFO", "", ""])
        
        for issue in self.current_result.issues:
            if issue.severity == ValidationSeverity.ERROR:
                parent = error_item
            elif issue.severity == ValidationSeverity.WARNING:
                parent = warning_item
            else:
                parent = info_item
            
            location = ""
            if issue.row_index is not None:
                location = f"Row {issue.row_index}"
                if issue.column:
                    location += f", Col {issue.column}"
            
            child = QTreeWidgetItem(parent, [
                issue.severity.value.upper(),
                location,
                issue.message
            ])
            child.setData(0, Qt.ItemDataRole.UserRole, issue)
        
        # Expand all items
        self.tree_widget.expandAll()
        
        # Update details
        self.details_text.setPlainText(str(self.current_result))
        
        # Update status
        self.status_label.setText(f"Total issues: {len(self.current_result.issues)}")
    
    def format_issue(self, issue: ValidationIssue) -> str:
        """Format issue for display in list."""
        location = ""
        if issue.row_index is not None:
            location = f"[Row {issue.row_index}"
            if issue.column:
                location += f", {issue.column}"
            location += "] "
        
        return f"{issue.severity.value.upper()}: {location}{issue.message}"
    
    def color_item(self, item: QListWidgetItem, severity: ValidationSeverity):
        """Color item based on severity."""
        if severity == ValidationSeverity.ERROR:
            item.setForeground(QColor(200, 0, 0))  # Red
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        elif severity == ValidationSeverity.WARNING:
            item.setForeground(QColor(180, 120, 0))  # Orange
        else:
            item.setForeground(QColor(0, 100, 0))  # Green
    
    def on_item_double_clicked(self, item):
        """Handle double-click on list item."""
        issue = item.data(Qt.ItemDataRole.UserRole)
        if issue and issue.row_index is not None:
            self.navigate_to_row_requested.emit(issue.row_index)
    
    def on_tree_item_double_clicked(self, item, column):
        """Handle double-click on tree item."""
        issue = item.data(0, Qt.ItemDataRole.UserRole)
        if issue and issue.row_index is not None:
            self.navigate_to_row_requested.emit(issue.row_index)
    
    def clear(self):
        """Clear the display."""
        self.current_result = None
        self.update_display()
    
    def refresh_requested(self):
        """Emit refresh signal."""
        self.refresh_requested_signal.emit()


class CompactValidationWidget(QWidget):
    """Compact validation widget for status bar or small spaces."""
    
    navigate_to_row_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.current_result: Optional[ValidationResult] = None
    
    def setup_ui(self):
        """Set up compact UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(20, 20)
        layout.addWidget(self.icon_label)
        
        self.summary_label = QLabel("Ready")
        self.summary_label.setStyleSheet("font-size: 9pt;")
        layout.addWidget(self.summary_label)
        
        self.details_button = QPushButton("...")
        self.details_button.setFixedSize(20, 20)
        self.details_button.clicked.connect(self.show_details)
        layout.addWidget(self.details_button)
        
        # Set initial state
        self.set_valid_state()
    
    def set_result(self, result: ValidationResult):
        """Set validation result."""
        self.current_result = result
        self.update_display()
    
    def update_display(self):
        """Update compact display."""
        if not self.current_result:
            self.set_ready_state()
            return
        
        errors = len(self.current_result.get_errors())
        warnings = len(self.current_result.get_warnings())
        
        if errors == 0 and warnings == 0:
            self.set_valid_state()
            self.summary_label.setText("Valid")
        elif errors > 0:
            self.set_error_state()
            self.summary_label.setText(f"{errors} error(s)")
        else:
            self.set_warning_state()
            self.summary_label.setText(f"{warnings} warning(s)")
    
    def set_ready_state(self):
        """Set ready state (no validation)."""
        self.icon_label.setText("○")
        self.icon_label.setStyleSheet("color: gray; font-weight: bold;")
        self.summary_label.setText("Ready")
    
    def set_valid_state(self):
        """Set valid state."""
        self.icon_label.setText("✓")
        self.icon_label.setStyleSheet("color: green; font-weight: bold;")
    
    def set_error_state(self):
        """Set error state."""
        self.icon_label.setText("✗")
        self.icon_label.setStyleSheet("color: red; font-weight: bold;")
    
    def set_warning_state(self):
        """Set warning state."""
        self.icon_label.setText("!")
        self.icon_label.setStyleSheet("color: orange; font-weight: bold;")
    
    def show_details(self):
        """Show detailed validation dialog."""
        if not self.current_result:
            return
        
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Validation Details")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setPlainText(str(self.current_result))
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.exec()
    
    def clear(self):
        """Clear the display."""
        self.current_result = None
        self.set_ready_state()


# Signals for the panels
ValidationPanel.navigate_to_row_requested = pyqtSignal(int)
ValidationPanel.refresh_requested_signal = pyqtSignal()