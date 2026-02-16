"""
Layout Toolbar - Provides quick access to layout presets.

This toolbar provides:
1. Buttons for each layout preset
2. Save custom layout button
3. Layout management dropdown
4. Visual feedback for current layout
"""

from PyQt6.QtWidgets import (
    QToolBar, QToolButton, QWidget, QHBoxLayout, QPushButton, 
    QMenu, QLabel, QSizePolicy, QFrame
)
from PyQt6.QtGui import QIcon, QFont, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from ..layout_presets import OnePointLayoutPresets, LayoutManager


class LayoutToolbar(QToolBar):
    """Toolbar for layout preset switching."""
    
    # Signals
    presetSelected = pyqtSignal(str)  # Emitted when a preset is selected
    saveCustomLayout = pyqtSignal()  # Emitted when save custom layout is requested
    manageLayouts = pyqtSignal()  # Emitted when manage layouts is requested
    
    def __init__(self, parent=None, layout_manager: LayoutManager = None):
        super().__init__("Layout Presets", parent)
        self.layout_manager = layout_manager or LayoutManager()
        self.current_preset = None
        
        # Set toolbar properties
        self.setMovable(True)
        self.setFloatable(True)
        self.setIconSize(QSize(24, 24))
        
        # Create toolbar widgets
        self._create_toolbar()
        
        # Load last used preset
        self._load_last_preset()
    
    def _create_toolbar(self):
        """Create toolbar widgets and layout."""
        # Add label
        layout_label = QLabel("Layout:")
        layout_label.setStyleSheet("font-weight: bold; padding: 0 5px;")
        self.addWidget(layout_label)
        
        # Add separator
        self.addSeparator()
        
        # Create preset buttons
        self._create_preset_buttons()
        
        # Add separator
        self.addSeparator()
        
        # Create custom layout button
        self._create_custom_layout_button()
        
        # Add stretch to push everything to the left
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)
    
    def _create_preset_buttons(self):
        """Create buttons for each preset."""
        presets = OnePointLayoutPresets.get_all_presets()
        
        for key, preset in presets.items():
            button = QToolButton()
            button.setText(preset.name)
            button.setToolTip(f"{preset.name}\n{preset.description}")
            button.setCheckable(True)
            button.setAutoExclusive(True)  # Only one button can be checked at a time
            
            # Set icon if available
            icon_name = preset.metadata.get('icon', '')
            if icon_name:
                # TODO: Load actual icons when available
                button.setIcon(QIcon())
            
            # Connect signal
            button.clicked.connect(
                lambda checked, p=preset.name: self._on_preset_button_clicked(p)
            )
            
            # Store reference
            setattr(self, f"{key}_button", button)
            self.addWidget(button)
            
            # Add small separator between buttons (except after last)
            if key != list(presets.keys())[-1]:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setFrameShadow(QFrame.Shadow.Sunken)
                sep.setStyleSheet("color: #cccccc; margin: 2px 5px;")
                self.addWidget(sep)
    
    def _create_custom_layout_button(self):
        """Create button for custom layout management."""
        # Custom layout button with dropdown
        self.custom_layout_button = QToolButton()
        self.custom_layout_button.setText("Custom Layouts")
        self.custom_layout_button.setToolTip("Save current layout or manage custom layouts")
        self.custom_layout_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        # Create dropdown menu
        custom_menu = QMenu(self.custom_layout_button)
        
        # Save current layout action
        save_action = QAction("Save Current Layout...", self)
        save_action.triggered.connect(self.saveCustomLayout.emit)
        custom_menu.addAction(save_action)
        
        # Manage layouts action
        manage_action = QAction("Manage Layouts...", self)
        manage_action.triggered.connect(self.manageLayouts.emit)
        custom_menu.addAction(manage_action)
        
        # Add separator
        custom_menu.addSeparator()
        
        # Load custom layouts
        self._populate_custom_layouts_menu(custom_menu)
        
        self.custom_layout_button.setMenu(custom_menu)
        self.addWidget(self.custom_layout_button)
    
    def _populate_custom_layouts_menu(self, menu: QMenu):
        """Populate menu with custom layouts."""
        custom_layouts = self.layout_manager.custom_layouts
        
        if not custom_layouts:
            no_layouts_action = QAction("No custom layouts saved", self)
            no_layouts_action.setEnabled(False)
            menu.addAction(no_layouts_action)
            return
        
        for name, data in custom_layouts.items():
            action = QAction(name, self)
            action.setToolTip(f"Apply custom layout: {name}")
            action.triggered.connect(
                lambda checked, n=name: self._on_custom_layout_selected(n)
            )
            menu.addAction(action)
    
    def _load_last_preset(self):
        """Load and select the last used preset."""
        last_preset = self.layout_manager.get_last_used_preset()
        if last_preset:
            self.select_preset(last_preset)
    
    def select_preset(self, preset_name: str):
        """Select a preset by name."""
        # Find and check the corresponding button
        presets = OnePointLayoutPresets.get_all_presets()
        
        for key, preset in presets.items():
            if preset.name == preset_name:
                button = getattr(self, f"{key}_button", None)
                if button:
                    button.setChecked(True)
                    self.current_preset = preset_name
                    break
        
        # Also check custom layouts
        if preset_name in self.layout_manager.custom_layouts:
            self.current_preset = preset_name
    
    def _on_preset_button_clicked(self, preset_name: str):
        """Handle preset button click."""
        self.current_preset = preset_name
        self.presetSelected.emit(preset_name)
        
        # Save as last used
        self.layout_manager.settings.setValue("last_preset", preset_name)
    
    def _on_custom_layout_selected(self, layout_name: str):
        """Handle custom layout selection from menu."""
        self.current_preset = layout_name
        self.presetSelected.emit(layout_name)
        
        # Save as last used
        self.layout_manager.settings.setValue("last_preset", layout_name)
    
    def update_custom_layouts_menu(self):
        """Update the custom layouts menu."""
        if hasattr(self, 'custom_layout_button') and self.custom_layout_button.menu():
            menu = self.custom_layout_button.menu()
            
            # Clear existing custom layout actions (keep first 2 actions: Save and Manage)
            actions = menu.actions()
            if len(actions) > 2:
                # Remove all actions after the separator (which is at index 2)
                for action in actions[2:]:
                    menu.removeAction(action)
            
            # Re-populate custom layouts
            self._populate_custom_layouts_menu(menu)
    
    def set_layout_manager(self, layout_manager: LayoutManager):
        """Set the layout manager and update UI."""
        self.layout_manager = layout_manager
        self.update_custom_layouts_menu()
        
        # Reload last preset
        self._load_last_preset()
    
    def get_current_preset(self) -> str:
        """Get the name of the currently selected preset."""
        return self.current_preset