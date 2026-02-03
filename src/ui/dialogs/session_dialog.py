"""
Session Management Dialog for Earthworm Moltbot
Provides UI for managing workspace sessions.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QGroupBox,
    QGridLayout, QSplitter, QMessageBox, QInputDialog, QFrame,
    QSizePolicy, QScrollArea, QDateTimeEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

import os
from datetime import datetime

from ...core.session_manager import SessionManager, create_workspace_state, restore_workspace_state


class SessionDialog(QDialog):
    """Dialog for managing workspace sessions."""
    
    session_selected = pyqtSignal(str)  # Signal emitted when a session is selected for loading
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.session_manager = SessionManager()
        
        self.setWindowTitle("Session Management")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(800, 500)
        
        self.setup_ui()
        self.load_sessions()
        
        # Connect signals
        self.session_list.itemSelectionChanged.connect(self.on_session_selected)
        self.session_list.itemDoubleClicked.connect(self.on_session_double_clicked)
    
    def setup_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top section: Title and filter
        top_layout = QHBoxLayout()
        
        title_label = QLabel("Workspace Sessions")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        filter_label = QLabel("Filter:")
        top_layout.addWidget(filter_label)
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter sessions...")
        self.filter_edit.textChanged.connect(self.filter_sessions)
        self.filter_edit.setMaximumWidth(200)
        top_layout.addWidget(self.filter_edit)
        
        main_layout.addLayout(top_layout)
        
        # Main content area
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Session list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Session list
        self.session_list = QListWidget()
        self.session_list.setAlternatingRowColors(True)
        self.session_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        left_layout.addWidget(self.session_list)
        
        # List actions
        list_actions_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_sessions)
        list_actions_layout.addWidget(self.refresh_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_selected_session)
        self.delete_button.setEnabled(False)
        list_actions_layout.addWidget(self.delete_button)
        
        list_actions_layout.addStretch()
        left_layout.addLayout(list_actions_layout)
        
        main_splitter.addWidget(left_panel)
        
        # Right panel: Session details and actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Session details group
        details_group = QGroupBox("Session Details")
        details_layout = QVBoxLayout(details_group)
        
        # Session name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter session name")
        name_layout.addWidget(self.name_edit)
        details_layout.addLayout(name_layout)
        
        # Session description
        details_layout.addWidget(QLabel("Description:"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Enter session description...")
        details_layout.addWidget(self.description_edit)
        
        # Session metadata
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QGridLayout(metadata_group)
        
        metadata_layout.addWidget(QLabel("Created:"), 0, 0)
        self.created_label = QLabel("")
        metadata_layout.addWidget(self.created_label, 0, 1)
        
        metadata_layout.addWidget(QLabel("Modified:"), 1, 0)
        self.modified_label = QLabel("")
        metadata_layout.addWidget(self.modified_label, 1, 1)
        
        metadata_layout.addWidget(QLabel("Workspace Stats:"), 2, 0)
        self.stats_label = QLabel("")
        self.stats_label.setWordWrap(True)
        metadata_layout.addWidget(self.stats_label, 2, 1)
        
        details_layout.addWidget(metadata_group)
        
        right_layout.addWidget(details_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.save_button = QPushButton("Save Current Workspace")
        self.save_button.clicked.connect(self.save_current_session)
        self.save_button.setToolTip("Save current workspace state as a new session")
        actions_layout.addWidget(self.save_button)
        
        self.update_button = QPushButton("Update Selected Session")
        self.update_button.clicked.connect(self.update_selected_session)
        self.update_button.setEnabled(False)
        self.update_button.setToolTip("Update selected session with current workspace state")
        actions_layout.addWidget(self.update_button)
        
        self.load_button = QPushButton("Load Selected Session")
        self.load_button.clicked.connect(self.load_selected_session)
        self.load_button.setEnabled(False)
        self.load_button.setToolTip("Load selected session and restore workspace")
        actions_layout.addWidget(self.load_button)
        
        self.rename_button = QPushButton("Rename Selected Session")
        self.rename_button.clicked.connect(self.rename_selected_session)
        self.rename_button.setEnabled(False)
        self.rename_button.setToolTip("Rename selected session")
        actions_layout.addWidget(self.rename_button)
        
        right_layout.addWidget(actions_group)
        
        right_layout.addStretch()
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        right_layout.addLayout(button_layout)
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(main_splitter)
    
    def load_sessions(self):
        """Load and display all sessions."""
        self.session_list.clear()
        sessions = self.session_manager.get_all_sessions()
        
        for session in sessions:
            item = QListWidgetItem(session.name)
            item.setData(Qt.ItemDataRole.UserRole, session.name)
            
            # Add timestamp as tooltip
            timestamp = session.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            item.setToolTip(f"Created: {timestamp}\nDescription: {session.description}")
            
            self.session_list.addItem(item)
        
        # Update UI state
        self.update_ui_state()
    
    def filter_sessions(self):
        """Filter sessions based on search text."""
        filter_text = self.filter_edit.text().lower()
        
        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            item_text = item.text().lower()
            item.setHidden(filter_text not in item_text)
    
    def on_session_selected(self):
        """Handle session selection."""
        selected_items = self.session_list.selectedItems()
        
        if not selected_items:
            self.clear_session_details()
            self.update_ui_state()
            return
        
        session_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        session = self.session_manager.get_session(session_name)
        
        if session:
            self.display_session_details(session)
        
        self.update_ui_state()
    
    def on_session_double_clicked(self, item):
        """Handle session double-click (load session)."""
        session_name = item.data(Qt.ItemDataRole.UserRole)
        self.load_session(session_name)
    
    def display_session_details(self, session):
        """Display session details in the details panel."""
        self.name_edit.setText(session.name)
        self.description_edit.setText(session.description)
        
        # Format timestamp
        timestamp = session.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.created_label.setText(timestamp)
        self.modified_label.setText(timestamp)
        
        # Display workspace stats
        stats_text = self.get_workspace_stats(session.workspace_state)
        self.stats_label.setText(stats_text)
    
    def clear_session_details(self):
        """Clear session details panel."""
        self.name_edit.clear()
        self.description_edit.clear()
        self.created_label.clear()
        self.modified_label.clear()
        self.stats_label.clear()
    
    def get_workspace_stats(self, workspace_state):
        """Generate workspace statistics text."""
        if not workspace_state:
            return "No workspace data"
        
        stats = []
        
        # Count subwindows
        subwindows = workspace_state.get("subwindows", [])
        stats.append(f"Open files: {len(subwindows)}")
        
        # Window state
        main_window = workspace_state.get("main_window", {})
        if main_window.get("geometry", {}).get("maximized", False):
            stats.append("Window: Maximized")
        else:
            stats.append("Window: Normal")
        
        # MDI view mode
        mdi_area = main_window.get("mdi_area", {})
        view_mode = mdi_area.get("view_mode", "SubWindowView")
        stats.append(f"MDI View: {view_mode}")
        
        return "\n".join(stats)
    
    def update_ui_state(self):
        """Update UI button states based on selection."""
        has_selection = len(self.session_list.selectedItems()) > 0
        
        self.delete_button.setEnabled(has_selection)
        self.update_button.setEnabled(has_selection)
        self.load_button.setEnabled(has_selection)
        self.rename_button.setEnabled(has_selection)
    
    def save_current_session(self):
        """Save current workspace as a new session."""
        if not self.main_window:
            QMessageBox.warning(self, "Error", "Main window reference not available.")
            return
        
        # Get session name
        name, ok = QInputDialog.getText(
            self, "Save Session", "Enter session name:",
            text=self.name_edit.text() or f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if not ok or not name:
            return
        
        # Check if session already exists
        if self.session_manager.session_exists(name):
            reply = QMessageBox.question(
                self, "Session Exists",
                f"A session named '{name}' already exists. Overwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        # Get description
        description = self.description_edit.toPlainText()
        
        # Create workspace state
        try:
            workspace_state = create_workspace_state(self.main_window)
            
            # Save session
            session = self.session_manager.save_session(name, description, workspace_state)
            
            # Refresh list and select new session
            self.load_sessions()
            
            # Select the new session
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == name:
                    self.session_list.setCurrentItem(item)
                    break
            
            QMessageBox.information(self, "Success", f"Session '{name}' saved successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save session: {str(e)}")
    
    def update_selected_session(self):
        """Update selected session with current workspace state."""
        selected_items = self.session_list.selectedItems()
        if not selected_items:
            return
        
        session_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        if not self.main_window:
            QMessageBox.warning(self, "Error", "Main window reference not available.")
            return
        
        # Get updated description
        description = self.description_edit.toPlainText()
        
        # Update session description
        self.session_manager.update_session_description(session_name, description)
        
        # Update workspace state
        try:
            workspace_state = create_workspace_state(self.main_window)
            self.session_manager.update_session_workspace(session_name, workspace_state)
            
            # Refresh session details
            session = self.session_manager.get_session(session_name)
            if session:
                self.display_session_details(session)
            
            QMessageBox.information(self, "Success", f"Session '{session_name}' updated successfully.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update session: {str(e)}")
    
    def load_selected_session(self):
        """Load selected session."""
        selected_items = self.session_list.selectedItems()
        if not selected_items:
            return
        
        session_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.load_session(session_name)
    
    def load_session(self, session_name):
        """Load a session by name."""
        session = self.session_manager.get_session(session_name)
        if not session:
            QMessageBox.warning(self, "Error", f"Session '{session_name}' not found.")
            return
        
        if not self.main_window:
            QMessageBox.warning(self, "Error", "Main window reference not available.")
            return
        
        # Confirm loading
        reply = QMessageBox.question(
            self, "Load Session",
            f"Load session '{session_name}'? This will replace the current workspace.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Restore workspace state
            success = restore_workspace_state(self.main_window, session.workspace_state)
            
            if success:
                QMessageBox.information(self, "Success", f"Session '{session_name}' loaded successfully.")
                self.session_selected.emit(session_name)
                self.accept()  # Close dialog
            else:
                QMessageBox.warning(self, "Warning", 
                    f"Session '{session_name}' loaded with some issues. Some workspace elements may not have been restored.")
                self.session_selected.emit(session_name)
                self.accept()  # Close dialog
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load session: {str(e)}")
    
    def delete_selected_session(self):
        """Delete selected session."""
        selected_items = self.session_list.selectedItems()
        if not selected_items:
            return
        
        session_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Session",
            f"Delete session '{session_name}'? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Delete session
        if self.session_manager.delete_session(session_name):
            self.load_sessions()
            self.clear_session_details()
            QMessageBox.information(self, "Success", f"Session '{session_name}' deleted successfully.")
        else:
            QMessageBox.warning(self, "Error", f"Failed to delete session '{session_name}'.")
    
    def rename_selected_session(self):
        """Rename selected session."""
        selected_items = self.session_list.selectedItems()
        if not selected_items:
            return
        
        old_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        
        # Get new name
        new_name, ok = QInputDialog.getText(
            self, "Rename Session", "Enter new session name:",
            text=old_name
        )
        
        if not ok or not new_name or new_name == old_name:
            return
        
        # Check if new name already exists
        if self.session_manager.session_exists(new_name):
            QMessageBox.warning(self, "Error", f"A session named '{new_name}' already exists.")
            return
        
        # Rename session
        if self.session_manager.rename_session(old_name, new_name):
            self.load_sessions()
            
            # Select the renamed session
            for i in range(self.session_list.count()):
                item = self.session_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == new_name:
                    self.session_list.setCurrentItem(item)
                    break
            
            QMessageBox.information(self, "Success", f"Session renamed to '{new_name}'.")
        else:
            QMessageBox.warning(self, "Error", f"Failed to rename session '{old_name}'.")