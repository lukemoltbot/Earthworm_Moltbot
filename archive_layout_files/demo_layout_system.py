#!/usr/bin/env python3
"""
Demonstration of the Layout Presets System for Earthworm.

This script demonstrates:
1. The 4 built-in layout presets
2. Custom layout saving and management
3. Layout toolbar functionality
4. Integration with Earthworm's MDI system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from src.ui.layout_presets import OnePointLayoutPresets, LayoutManager
from src.ui.widgets.layout_toolbar import LayoutToolbar
from src.ui.dialogs.layout_manager_dialog import LayoutManagerDialog
from src.ui.dialogs.save_layout_dialog import SaveLayoutDialog


class DemoWindow(QMainWindow):
    """Demo window to show layout presets system."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Earthworm Layout Presets Demo")
        self.setGeometry(100, 100, 800, 600)
        
        # Create layout manager
        self.layout_manager = LayoutManager()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create layout toolbar
        self.layout_toolbar = LayoutToolbar(self, self.layout_manager)
        self.layout_toolbar.presetSelected.connect(self._on_preset_selected)
        self.layout_toolbar.saveCustomLayout.connect(self._on_save_layout)
        self.layout_toolbar.manageLayouts.connect(self._on_manage_layouts)
        
        # Add toolbar to window
        self.addToolBar(self.layout_toolbar)
        
        # Create demo content
        self.content_area = QTextEdit()
        self.content_area.setReadOnly(True)
        self.content_area.setHtml("""
        <h2>Earthworm Layout Presets System Demo</h2>
        <p>This demo shows the 1Point-style layout presets system for Earthworm.</p>
        <p><b>Available Presets:</b></p>
        <ul>
            <li><b>Graphic Log (1:50)</b> - Detailed view for core logging</li>
            <li><b>Strat Log (1:200)</b> - Standard stratigraphic logging view</li>
            <li><b>Stacked (1:200)</b> - Multiple curves stacked view</li>
            <li><b>Data Entry</b> - Focused on data entry with minimal visualization</li>
        </ul>
        <p>Use the layout toolbar above to switch between presets, save custom layouts, or manage layouts.</p>
        <p>Each preset defines:</p>
        <ul>
            <li>Splitter sizes and positions</li>
            <li>Widget visibility states</li>
            <li>Scale settings (depth scale)</li>
            <li>Toolbar configurations</li>
            <li>Default zoom levels</li>
        </ul>
        """)
        
        layout.addWidget(self.content_area)
        
        # Create control buttons
        control_layout = QHBoxLayout()
        
        self.info_button = QPushButton("Show Preset Info")
        self.info_button.clicked.connect(self._show_preset_info)
        control_layout.addWidget(self.info_button)
        
        self.test_button = QPushButton("Test Custom Layout")
        self.test_button.clicked.connect(self._test_custom_layout)
        control_layout.addWidget(self.test_button)
        
        self.clear_button = QPushButton("Clear Custom Layouts")
        self.clear_button.clicked.connect(self._clear_custom_layouts)
        control_layout.addWidget(self.clear_button)
        
        layout.addLayout(control_layout)
        
        # Status label
        self.status_label = QTextEdit()
        self.status_label.setMaximumHeight(100)
        self.status_label.setReadOnly(True)
        layout.addWidget(self.status_label)
        
        self._log("Demo window initialized. Ready to test layout presets.")
    
    def _log(self, message):
        """Add message to status log."""
        self.status_label.append(f"• {message}")
    
    def _on_preset_selected(self, preset_name):
        """Handle preset selection."""
        self._log(f"Preset selected: {preset_name}")
        
        # Get preset details
        preset = OnePointLayoutPresets.get_preset_by_name(preset_name)
        if not preset:
            preset = self.layout_manager.get_custom_layout(preset_name)
        
        if preset:
            self._log(f"  • Description: {preset.description}")
            self._log(f"  • Depth scale: {preset.depth_scale} px/m")
            self._log(f"  • Default zoom: {preset.default_zoom}x")
            self._log(f"  • Splitter sizes: {preset.splitter_sizes}")
            
            # Show widget visibility
            visible = [w for w, v in preset.widget_visibility.items() if v]
            hidden = [w for w, v in preset.widget_visibility.items() if not v]
            self._log(f"  • Visible widgets: {len(visible)}")
            self._log(f"  • Hidden widgets: {len(hidden)}")
    
    def _on_save_layout(self):
        """Handle save layout request."""
        self._log("Save custom layout requested")
        
        # In a real application, this would capture the current window layout
        # For demo purposes, we'll create a mock layout
        dialog = SaveLayoutDialog(self, list(self.layout_manager.custom_layouts.keys()))
        if dialog.exec() == QDialog.DialogCode.Accepted:
            layout_name = dialog.get_layout_name()
            self._log(f"Would save layout: {layout_name}")
            self._log("(In real app, this would capture current window state)")
    
    def _on_manage_layouts(self):
        """Handle manage layouts request."""
        self._log("Opening layout manager...")
        dialog = LayoutManagerDialog(self, self.layout_manager)
        dialog.exec()
    
    def _show_preset_info(self):
        """Show information about all presets."""
        self._log("\n=== Preset Information ===")
        
        presets = OnePointLayoutPresets.get_all_presets()
        for key, preset in presets.items():
            self._log(f"\n{preset.name}:")
            self._log(f"  • {preset.description}")
            self._log(f"  • Scale: {preset.metadata.get('scale', 'N/A')}")
            self._log(f"  • Category: {preset.metadata.get('category', 'N/A')}")
            self._log(f"  • Shortcut: {preset.metadata.get('keyboard_shortcut', 'None')}")
        
        self._log("\n=== End Preset Information ===")
    
    def _test_custom_layout(self):
        """Test creating and managing a custom layout."""
        self._log("\n=== Testing Custom Layout ===")
        
        # Create a test custom layout
        test_layout = {
            'name': 'Test Custom Layout',
            'description': 'A test custom layout for demonstration',
            'splitter_sizes': [250, 250, 250, 250],
            'widget_visibility': {
                'plot_container': True,
                'enhanced_column_container': True,
                'table_container': False,
                'overview_container': True
            },
            'depth_scale': 15.0,
            'default_zoom': 0.5,
            'toolbar_config': {},
            'metadata': {'category': 'test', 'icon': 'test'}
        }
        
        # Add to layout manager
        self.layout_manager.custom_layouts['Test Custom Layout'] = test_layout
        
        # Update toolbar
        self.layout_toolbar.update_custom_layouts_menu()
        
        self._log("Created test custom layout: 'Test Custom Layout'")
        self._log("Check the 'Custom Layouts' menu in the layout toolbar!")
    
    def _clear_custom_layouts(self):
        """Clear all custom layouts."""
        self.layout_manager.custom_layouts.clear()
        self.layout_toolbar.update_custom_layouts_menu()
        self._log("Cleared all custom layouts")


def main():
    """Run the demo."""
    app = QApplication([])
    
    # Create and show demo window
    window = DemoWindow()
    window.show()
    
    # Print console instructions
    print("=" * 60)
    print("Earthworm Layout Presets System Demo")
    print("=" * 60)
    print("\nInstructions:")
    print("1. Use the layout toolbar to switch between presets")
    print("2. Click 'Show Preset Info' to see details of all presets")
    print("3. Click 'Test Custom Layout' to create a test custom layout")
    print("4. Use the 'Custom Layouts' dropdown to manage layouts")
    print("5. Check the status area at the bottom for feedback")
    print("\nThe demo shows the layout system without requiring Earthworm.")
    print("In the actual Earthworm application, layouts would control:")
    print("  • Splitter positions between plot, column, table, and overview")
    print("  • Widget visibility (show/hide panels)")
    print("  • Depth scale (pixels per metre)")
    print("  • Zoom levels")
    print("=" * 60)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()