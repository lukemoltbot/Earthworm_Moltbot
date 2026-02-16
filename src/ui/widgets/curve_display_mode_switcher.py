"""
Curve Display Mode Switcher - UI controls for switching between curve display modes.

Provides toolbar buttons, context menus, and keyboard shortcuts for switching between:
1. Overlaid Curves (1Point default)
2. Stacked Curves (1Point Stacked Layout)
3. Side-by-Side Curves
4. Histogram Mode
"""

from PyQt6.QtWidgets import (
    QWidget, QToolBar, QPushButton, QMenu,
    QLabel, QComboBox, QHBoxLayout, QVBoxLayout, QSizePolicy
)
from PyQt6.QtGui import QIcon, QFont, QKeySequence, QAction, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal, QSize
import os


class CurveDisplayModeSwitcher(QToolBar):
    """
    Toolbar for switching between curve display modes.
    Integrates with CurveDisplayModes manager.
    """
    
    # Signal emitted when display mode changes
    displayModeChanged = pyqtSignal(str, dict)  # mode_name, mode_info
    
    # Signals for curve settings export/import
    exportCurveSettingsRequested = pyqtSignal()
    importCurveSettingsRequested = pyqtSignal()
    syncSettingsRequested = pyqtSignal()
    
    def __init__(self, parent=None, display_modes_manager=None):
        super().__init__("Display Mode", parent)
        
        # Display modes manager
        self.display_modes_manager = display_modes_manager
        
        # Current mode
        self.current_mode = 'overlaid'
        
        # Setup toolbar
        self.setup_toolbar()
        
        # Connect to display modes manager if provided
        if self.display_modes_manager:
            self.display_modes_manager.displayModeChanged.connect(self.on_display_mode_changed)
            self.current_mode = self.display_modes_manager.current_mode
    
    def setup_toolbar(self):
        """Setup the display mode switcher toolbar."""
        self.setMovable(True)
        self.setFloatable(True)
        self.setIconSize(QSize(24, 24))
        
        # Add title
        self.addWidget(QLabel("Display:"))
        
        # Create action group for mutually exclusive mode selection
        self.mode_action_group = QActionGroup(self)
        self.mode_action_group.setExclusive(True)
        
        # Create mode actions
        self.create_mode_actions()
        
        # Add separator
        self.addSeparator()
        
        # Add mode description label
        self.mode_description_label = QLabel("Overlaid curves (1Point default)")
        self.mode_description_label.setStyleSheet("color: #666; font-style: italic;")
        self.mode_description_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(self.mode_description_label)
        
        # Add separator
        self.addSeparator()
        
        # Add curve settings export/import buttons
        self.add_curve_settings_buttons()
        
        # Add separator
        self.addSeparator()
        
        # Add cross-hole sync status indicator
        self.add_sync_status_indicator()
    
    def create_mode_actions(self):
        """Create toolbar actions for each display mode."""
        # Overlaid mode (default)
        overlaid_action = QAction("Overlaid", self)
        overlaid_action.setCheckable(True)
        overlaid_action.setChecked(True)
        overlaid_action.setToolTip("Overlaid Curves (1Point default)\nCurves plotted on top of each other")
        overlaid_action.triggered.connect(lambda: self.set_display_mode('overlaid'))
        overlaid_action.setShortcut(QKeySequence("Ctrl+1"))
        self.mode_action_group.addAction(overlaid_action)
        self.addAction(overlaid_action)
        
        # Stacked mode
        stacked_action = QAction("Stacked", self)
        stacked_action.setCheckable(True)
        stacked_action.setToolTip("Stacked Curves (1Point Stacked Layout)\nCurves plotted side-by-side")
        stacked_action.triggered.connect(lambda: self.set_display_mode('stacked'))
        stacked_action.setShortcut(QKeySequence("Ctrl+2"))
        self.mode_action_group.addAction(stacked_action)
        self.addAction(stacked_action)
        
        # Side-by-side mode
        side_by_side_action = QAction("Side-by-Side", self)
        side_by_side_action.setCheckable(True)
        side_by_side_action.setToolTip("Side-by-Side Curves\nEach curve in separate track")
        side_by_side_action.triggered.connect(lambda: self.set_display_mode('side_by_side'))
        side_by_side_action.setShortcut(QKeySequence("Ctrl+3"))
        self.mode_action_group.addAction(side_by_side_action)
        self.addAction(side_by_side_action)
        
        # Histogram mode
        histogram_action = QAction("Histogram", self)
        histogram_action.setCheckable(True)
        histogram_action.setToolTip("Histogram Mode\nHistogram display for selected curves")
        histogram_action.triggered.connect(lambda: self.set_display_mode('histogram'))
        histogram_action.setShortcut(QKeySequence("Ctrl+4"))
        self.mode_action_group.addAction(histogram_action)
        self.addAction(histogram_action)
    
    def set_display_mode(self, mode_name):
        """Set the display mode."""
        if mode_name != self.current_mode:
            self.current_mode = mode_name
            
            # Update UI
            self.update_mode_description(mode_name)
            
            # Emit signal
            mode_info = self.get_mode_info(mode_name)
            self.displayModeChanged.emit(mode_name, mode_info)
            
            # Update display modes manager if connected
            if self.display_modes_manager:
                self.display_modes_manager.set_mode(mode_name)
    
    def update_mode_description(self, mode_name):
        """Update the mode description label."""
        descriptions = {
            'overlaid': 'Overlaid curves (1Point default)',
            'stacked': 'Stacked curves (1Point Stacked Layout)',
            'side_by_side': 'Side-by-side curves',
            'histogram': 'Histogram display mode'
        }
        
        description = descriptions.get(mode_name, 'Unknown display mode')
        self.mode_description_label.setText(description)
        
        # Update action checked state
        for action in self.mode_action_group.actions():
            action_text = action.text().lower().replace('-', '_').replace(' ', '_')
            if action_text == mode_name:
                action.setChecked(True)
                break
    
    def get_mode_info(self, mode_name):
        """Get information about a display mode."""
        mode_info = {
            'overlaid': {
                'name': 'Overlaid',
                'description': 'Curves plotted on top of each other (1Point default)',
                'key_shortcut': 'Ctrl+1'
            },
            'stacked': {
                'name': 'Stacked',
                'description': 'Curves plotted side-by-side (1Point Stacked Layout)',
                'key_shortcut': 'Ctrl+2'
            },
            'side_by_side': {
                'name': 'Side-by-Side',
                'description': 'Each curve in separate track',
                'key_shortcut': 'Ctrl+3'
            },
            'histogram': {
                'name': 'Histogram',
                'description': 'Histogram display for selected curves',
                'key_shortcut': 'Ctrl+4'
            }
        }
        
        return mode_info.get(mode_name, {})
    
    def on_display_mode_changed(self, mode_name, mode_info):
        """Handle display mode changes from the manager."""
        if mode_name != self.current_mode:
            self.current_mode = mode_name
            self.update_mode_description(mode_name)
    
    def set_display_modes_manager(self, manager):
        """Set the display modes manager."""
        if self.display_modes_manager:
            self.display_modes_manager.displayModeChanged.disconnect(self.on_display_mode_changed)
        
        self.display_modes_manager = manager
        if manager:
            manager.displayModeChanged.connect(self.on_display_mode_changed)
            self.current_mode = manager.current_mode
            self.update_mode_description(self.current_mode)
    
    def get_current_mode(self):
        """Get current display mode."""
        return self.current_mode
    
    def add_curve_settings_buttons(self):
        """Add curve settings export/import buttons to the toolbar."""
        # Export button
        export_action = QAction("Export Settings", self)
        export_action.setToolTip("Export curve settings to file")
        export_action.triggered.connect(self.export_curve_settings)
        self.addAction(export_action)
        
        # Import button
        import_action = QAction("Import Settings", self)
        import_action.setToolTip("Import curve settings from file")
        import_action.triggered.connect(self.import_curve_settings)
        self.addAction(import_action)
    
    def export_curve_settings(self):
        """Export current curve settings to a file."""
        print("DEBUG: Export curve settings requested")
        self.exportCurveSettingsRequested.emit()
        
    def import_curve_settings(self):
        """Import curve settings from a file."""
        print("DEBUG: Import curve settings requested")
        self.importCurveSettingsRequested.emit()
    
    def add_sync_status_indicator(self):
        """Add cross-hole sync status indicator to toolbar."""
        # Sync status label
        self.sync_status_label = QLabel("Sync: OFF")
        self.sync_status_label.setStyleSheet("color: #999; font-style: italic;")
        self.sync_status_label.setToolTip("Cross-hole synchronization status\nClick to configure sync settings")
        
        # Make it clickable
        self.sync_status_label.mousePressEvent = self.on_sync_status_clicked
        
        self.addWidget(self.sync_status_label)
    
    def on_sync_status_clicked(self, event):
        """Handle click on sync status indicator."""
        print("DEBUG: Sync status clicked - opening sync settings")
        self.syncSettingsRequested.emit()
    
    def update_sync_status(self, enabled: bool, hole_count: int = 0):
        """Update sync status indicator."""
        if enabled:
            self.sync_status_label.setText(f"Sync: ON ({hole_count} holes)")
            self.sync_status_label.setStyleSheet("color: #0a0; font-weight: bold;")
        else:
            self.sync_status_label.setText("Sync: OFF")
            self.sync_status_label.setStyleSheet("color: #999; font-style: italic;")


class CurveDisplayModeMenu(QMenu):
    """Context menu for curve display mode selection."""
    
    # Signal emitted when display mode changes
    displayModeChanged = pyqtSignal(str, dict)  # mode_name, mode_info
    
    def __init__(self, parent=None, display_modes_manager=None):
        super().__init__("Display Mode", parent)
        
        # Display modes manager
        self.display_modes_manager = display_modes_manager
        
        # Current mode
        self.current_mode = 'overlaid'
        
        # Setup menu
        self.setup_menu()
        
        # Connect to display modes manager if provided
        if self.display_modes_manager:
            self.display_modes_manager.displayModeChanged.connect(self.on_display_mode_changed)
            self.current_mode = self.display_modes_manager.current_mode
    
    def setup_menu(self):
        """Setup the display mode menu."""
        # Create action group for mutually exclusive selection
        self.mode_action_group = QActionGroup(self)
        self.mode_action_group.setExclusive(True)
        
        # Add mode actions
        self.add_mode_action("Overlaid", "overlaid", "Ctrl+1", 
                            "Curves plotted on top of each other (1Point default)")
        
        self.addSeparator()
        
        self.add_mode_action("Stacked", "stacked", "Ctrl+2",
                            "Curves plotted side-by-side (1Point Stacked Layout)")
        
        self.add_mode_action("Side-by-Side", "side_by_side", "Ctrl+3",
                            "Each curve in separate track")
        
        self.addSeparator()
        
        self.add_mode_action("Histogram", "histogram", "Ctrl+4",
                            "Histogram display for selected curves")
    
    def add_mode_action(self, text, mode_name, shortcut, tooltip):
        """Add a display mode action to the menu."""
        action = QAction(text, self)
        action.setCheckable(True)
        action.setChecked(mode_name == self.current_mode)
        action.setShortcut(QKeySequence(shortcut))
        action.setToolTip(tooltip)
        action.triggered.connect(lambda: self.set_display_mode(mode_name))
        
        self.mode_action_group.addAction(action)
        self.addAction(action)
        
        return action
    
    def set_display_mode(self, mode_name):
        """Set the display mode."""
        if mode_name != self.current_mode:
            self.current_mode = mode_name
            
            # Update action checked state
            for action in self.mode_action_group.actions():
                action_text = action.text().lower().replace('-', '_').replace(' ', '_')
                if action_text == mode_name:
                    action.setChecked(True)
                    break
            
            # Emit signal
            mode_info = self.get_mode_info(mode_name)
            self.displayModeChanged.emit(mode_name, mode_info)
            
            # Update display modes manager if connected
            if self.display_modes_manager:
                self.display_modes_manager.set_mode(mode_name)
    
    def get_mode_info(self, mode_name):
        """Get information about a display mode."""
        # Same as in CurveDisplayModeSwitcher
        mode_info = {
            'overlaid': {
                'name': 'Overlaid',
                'description': 'Curves plotted on top of each other (1Point default)',
                'key_shortcut': 'Ctrl+1'
            },
            'stacked': {
                'name': 'Stacked',
                'description': 'Curves plotted side-by-side (1Point Stacked Layout)',
                'key_shortcut': 'Ctrl+2'
            },
            'side_by_side': {
                'name': 'Side-by-Side',
                'description': 'Each curve in separate track',
                'key_shortcut': 'Ctrl+3'
            },
            'histogram': {
                'name': 'Histogram',
                'description': 'Histogram display for selected curves',
                'key_shortcut': 'Ctrl+4'
            }
        }
        
        return mode_info.get(mode_name, {})
    
    def on_display_mode_changed(self, mode_name, mode_info):
        """Handle display mode changes from the manager."""
        if mode_name != self.current_mode:
            self.current_mode = mode_name
            
            # Update action checked state
            for action in self.mode_action_group.actions():
                action_text = action.text().lower().replace('-', '_').replace(' ', '_')
                if action_text == mode_name:
                    action.setChecked(True)
                    break
# Factory function for easy integration
def create_display_mode_switcher(parent=None, display_modes_manager=None):
    """Create and initialize a display mode switcher toolbar."""
    switcher = CurveDisplayModeSwitcher(parent, display_modes_manager)
    return switcher


def create_display_mode_menu(parent=None, display_modes_manager=None):
    """Create and initialize a display mode context menu."""
    menu = CurveDisplayModeMenu(parent, display_modes_manager)
    return menu