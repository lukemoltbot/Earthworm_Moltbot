"""
SyncSettingsDialog - Dialog for configuring cross-hole synchronization settings.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QPushButton, QGroupBox, QFormLayout, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal


class SyncSettingsDialog(QDialog):
    """Dialog for configuring cross-hole synchronization settings."""
    
    settingsChanged = pyqtSignal(dict)  # Emitted when settings are changed
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        
        self.setWindowTitle("Cross-hole Synchronization Settings")
        self.setGeometry(100, 100, 500, 400)
        self.setMinimumSize(400, 300)
        
        # Store current settings
        self.current_settings = current_settings or {}
        
        # Setup UI
        self.setup_ui()
        
        # Load current settings
        self.load_settings()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Sync settings group
        sync_group = QGroupBox("Synchronization Settings")
        sync_layout = QFormLayout()
        
        # Enable sync checkbox
        self.enable_sync_checkbox = QCheckBox("Enable cross-hole synchronization")
        self.enable_sync_checkbox.setToolTip("Enable synchronization of curve settings across all open holes")
        sync_layout.addRow(self.enable_sync_checkbox)
        
        # Sync options (only enabled when sync is enabled)
        self.sync_curve_selection_checkbox = QCheckBox("Sync curve selection")
        self.sync_curve_selection_checkbox.setToolTip("Synchronize which curves are selected across holes")
        sync_layout.addRow(self.sync_curve_selection_checkbox)
        
        self.sync_display_settings_checkbox = QCheckBox("Sync display settings")
        self.sync_display_settings_checkbox.setToolTip("Synchronize curve colors, line styles, and thickness")
        sync_layout.addRow(self.sync_display_settings_checkbox)
        
        self.sync_visibility_checkbox = QCheckBox("Sync curve visibility")
        self.sync_visibility_checkbox.setToolTip("Synchronize curve show/hide states")
        sync_layout.addRow(self.sync_visibility_checkbox)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # SHIFT key override group
        shift_group = QGroupBox("SHIFT Key Override")
        shift_layout = QFormLayout()
        
        self.shift_override_checkbox = QCheckBox("Enable SHIFT key override")
        self.shift_override_checkbox.setToolTip("Hold SHIFT key to temporarily disable synchronization")
        shift_layout.addRow(self.shift_override_checkbox)
        
        # Override timeout
        timeout_layout = QHBoxLayout()
        self.shift_timeout_spinbox = QSpinBox()
        self.shift_timeout_spinbox.setRange(1000, 30000)  # 1-30 seconds
        self.shift_timeout_spinbox.setSingleStep(1000)
        self.shift_timeout_spinbox.setSuffix(" ms")
        self.shift_timeout_spinbox.setToolTip("How long SHIFT override remains active after key release")
        timeout_layout.addWidget(QLabel("Override timeout:"))
        timeout_layout.addWidget(self.shift_timeout_spinbox)
        timeout_layout.addStretch()
        shift_layout.addRow(timeout_layout)
        
        shift_group.setLayout(shift_layout)
        layout.addWidget(shift_group)
        
        # Auto-sync option
        self.auto_sync_checkbox = QCheckBox("Auto-sync new holes")
        self.auto_sync_checkbox.setToolTip("Automatically apply sync settings to newly opened holes")
        layout.addWidget(self.auto_sync_checkbox)
        
        # Status info
        status_label = QLabel("Status: Sync is OFF")
        status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(status_label)
        
        # Connect enable sync checkbox to enable/disable other options
        self.enable_sync_checkbox.toggled.connect(self.on_enable_sync_toggled)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def on_enable_sync_toggled(self, enabled):
        """Enable/disable sync options based on main sync checkbox."""
        self.sync_curve_selection_checkbox.setEnabled(enabled)
        self.sync_display_settings_checkbox.setEnabled(enabled)
        self.sync_visibility_checkbox.setEnabled(enabled)
        self.shift_override_checkbox.setEnabled(enabled)
        self.shift_timeout_spinbox.setEnabled(enabled)
        self.auto_sync_checkbox.setEnabled(enabled)
    
    def load_settings(self):
        """Load current settings into UI."""
        settings = self.current_settings
        
        # Main sync settings
        self.enable_sync_checkbox.setChecked(settings.get('sync_enabled', True))
        self.sync_curve_selection_checkbox.setChecked(settings.get('sync_curve_selection', True))
        self.sync_display_settings_checkbox.setChecked(settings.get('sync_display_settings', True))
        self.sync_visibility_checkbox.setChecked(settings.get('sync_visibility', True))
        
        # SHIFT override settings
        self.shift_override_checkbox.setChecked(settings.get('shift_override_enabled', True))
        self.shift_timeout_spinbox.setValue(settings.get('shift_override_timeout_ms', 5000))
        
        # Auto-sync
        self.auto_sync_checkbox.setChecked(settings.get('auto_sync_new_holes', True))
        
        # Enable/disable options based on main sync
        self.on_enable_sync_toggled(self.enable_sync_checkbox.isChecked())
    
    def get_settings(self):
        """Get settings from UI."""
        return {
            'sync_enabled': self.enable_sync_checkbox.isChecked(),
            'sync_curve_selection': self.sync_curve_selection_checkbox.isChecked(),
            'sync_display_settings': self.sync_display_settings_checkbox.isChecked(),
            'sync_visibility': self.sync_visibility_checkbox.isChecked(),
            'shift_override_enabled': self.shift_override_checkbox.isChecked(),
            'shift_override_timeout_ms': self.shift_timeout_spinbox.value(),
            'auto_sync_new_holes': self.auto_sync_checkbox.isChecked()
        }
    
    def save_settings(self):
        """Save settings and close dialog."""
        self.apply_settings()
        self.accept()
    
    def apply_settings(self):
        """Apply settings without closing dialog."""
        settings = self.get_settings()
        self.settingsChanged.emit(settings)
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Settings Applied",
            "Cross-hole synchronization settings have been applied.",
            QMessageBox.StandardButton.Ok
        )
    
    def update_status(self, hole_count: int, sync_active: bool):
        """Update status display."""
        status_text = f"Status: Sync is {'ON' if sync_active else 'OFF'}"
        if hole_count > 0:
            status_text += f" ({hole_count} hole{'s' if hole_count != 1 else ''} open)"
        
        # Find and update status label
        for i in range(self.layout().count()):
            widget = self.layout().itemAt(i).widget()
            if isinstance(widget, QLabel) and widget.text().startswith("Status:"):
                widget.setText(status_text)
                
                # Update color
                if sync_active:
                    widget.setStyleSheet("color: #0a0; font-weight: bold;")
                else:
                    widget.setStyleSheet("color: #666; font-style: italic;")
                break


# Factory function
def create_sync_settings_dialog(parent=None, current_settings=None):
    """Create and initialize a sync settings dialog."""
    dialog = SyncSettingsDialog(parent, current_settings)
    return dialog