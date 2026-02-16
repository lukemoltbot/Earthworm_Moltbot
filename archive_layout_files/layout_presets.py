"""
Layout Presets System for Earthworm - 1Point-style layout presets.

This module provides predefined layout presets for common geological logging workflows:
1. Graphic Log (1:50) - Detailed view for core logging
2. Strat Log (1:200) - Standard stratigraphic logging view
3. Stacked (1:200) - Multiple curves stacked view
4. Data Entry - Focused on data entry with minimal visualization

Each preset defines:
- Splitter sizes and positions
- Widget visibility states
- Scale settings (depth scale)
- Toolbar configurations
- Default zoom levels
"""

from PyQt6.QtCore import QObject, pyqtSignal, QSettings
from PyQt6.QtWidgets import QSplitter
import json
from typing import Dict, Any, Optional, List


class LayoutPreset:
    """Represents a single layout preset configuration."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.splitter_sizes = []  # List of sizes for each splitter section
        self.widget_visibility = {}  # Dict of widget_name: is_visible
        self.depth_scale = 10.0  # Pixels per metre
        self.default_zoom = 1.0  # Default zoom factor
        self.toolbar_config = {}  # Toolbar button states
        self.metadata = {}  # Additional metadata
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'splitter_sizes': self.splitter_sizes,
            'widget_visibility': self.widget_visibility,
            'depth_scale': self.depth_scale,
            'default_zoom': self.default_zoom,
            'toolbar_config': self.toolbar_config,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayoutPreset':
        """Create preset from dictionary."""
        preset = cls(data.get('name', ''), data.get('description', ''))
        preset.splitter_sizes = data.get('splitter_sizes', [])
        preset.widget_visibility = data.get('widget_visibility', {})
        preset.depth_scale = data.get('depth_scale', 10.0)
        preset.default_zoom = data.get('default_zoom', 1.0)
        preset.toolbar_config = data.get('toolbar_config', {})
        preset.metadata = data.get('metadata', {})
        return preset


class OnePointLayoutPresets:
    """Collection of 1Point-style layout presets for Earthworm."""
    
    @staticmethod
    def get_graphic_log_preset() -> LayoutPreset:
        """Graphic Log (1:50) - Detailed view for core logging."""
        preset = LayoutPreset(
            name="Graphic Log (1:50)",
            description="Detailed view for core logging and high-resolution analysis. "
                       "Optimized for 1:50 scale with emphasis on visual detail."
        )
        
        # Splitter sizes (plot | enhanced column | table | overview)
        # Graphic log gives more space to visual components
        preset.splitter_sizes = [400, 300, 500, 80]  # More space for plot and column
        
        # Widget visibility
        preset.widget_visibility = {
            'plot_container': True,
            'enhanced_column_container': True,
            'table_container': True,
            'overview_container': True,
            'curve_visibility_toolbar': True,
            'zoom_controls': True
        }
        
        # Scale settings (1:50 = 50 pixels per metre for detailed view)
        preset.depth_scale = 50.0  # 50 pixels per metre for 1:50 scale
        preset.default_zoom = 0.2  # More zoomed in for detail
        
        # Toolbar configuration
        preset.toolbar_config = {
            'show_curve_tools': True,
            'show_zoom_tools': True,
            'show_measurement_tools': True,
            'show_annotation_tools': True
        }
        
        # Metadata
        preset.metadata = {
            'scale': '1:50',
            'category': 'visual',
            'icon': 'graphic_log',
            'keyboard_shortcut': 'Ctrl+1'
        }
        
        return preset
    
    @staticmethod
    def get_strat_log_preset() -> LayoutPreset:
        """Strat Log (1:200) - Standard stratigraphic logging view."""
        preset = LayoutPreset(
            name="Strat Log (1:200)",
            description="Standard view for stratigraphic logging and interpretation. "
                       "Balanced layout for routine logging work."
        )
        
        # Splitter sizes - balanced layout
        preset.splitter_sizes = [300, 250, 600, 100]
        
        # Widget visibility
        preset.widget_visibility = {
            'plot_container': True,
            'enhanced_column_container': True,
            'table_container': True,
            'overview_container': True,
            'curve_visibility_toolbar': True,
            'zoom_controls': True
        }
        
        # Scale settings (1:200 = 5 pixels per metre)
        preset.depth_scale = 5.0  # 5 pixels per metre for 1:200 scale
        preset.default_zoom = 1.0  # Standard zoom
        
        # Toolbar configuration
        preset.toolbar_config = {
            'show_curve_tools': True,
            'show_zoom_tools': True,
            'show_measurement_tools': True,
            'show_annotation_tools': False
        }
        
        # Metadata
        preset.metadata = {
            'scale': '1:200',
            'category': 'standard',
            'icon': 'strat_log',
            'keyboard_shortcut': 'Ctrl+2'
        }
        
        return preset
    
    @staticmethod
    def get_stacked_preset() -> LayoutPreset:
        """Stacked (1:200) - Multiple curves stacked view."""
        preset = LayoutPreset(
            name="Stacked (1:200)",
            description="Multiple curves stacked vertically for comparison. "
                       "Optimized for curve analysis and correlation."
        )
        
        # Splitter sizes - more space for plot, less for table
        preset.splitter_sizes = [500, 300, 400, 80]
        
        # Widget visibility - hide table for more visual space
        preset.widget_visibility = {
            'plot_container': True,
            'enhanced_column_container': True,
            'table_container': False,  # Hidden for more visual space
            'overview_container': True,
            'curve_visibility_toolbar': True,
            'zoom_controls': True
        }
        
        # Scale settings (1:200 = 5 pixels per metre)
        preset.depth_scale = 5.0  # 5 pixels per metre for 1:200 scale
        preset.default_zoom = 1.0  # Standard zoom
        
        # Toolbar configuration - focus on curve tools
        preset.toolbar_config = {
            'show_curve_tools': True,
            'show_zoom_tools': True,
            'show_measurement_tools': True,
            'show_annotation_tools': False,
            'show_curve_stack_tools': True
        }
        
        # Metadata
        preset.metadata = {
            'scale': '1:200',
            'category': 'analysis',
            'icon': 'stacked',
            'keyboard_shortcut': 'Ctrl+3'
        }
        
        return preset
    
    @staticmethod
    def get_data_entry_preset() -> LayoutPreset:
        """Data Entry - Focused on data entry with minimal visualization."""
        preset = LayoutPreset(
            name="Data Entry",
            description="Maximizes table space for data entry and editing. "
                       "Minimal visualization for focused data work."
        )
        
        # Splitter sizes - most space for table
        preset.splitter_sizes = [200, 150, 800, 60]
        
        # Widget visibility - hide some visual components
        preset.widget_visibility = {
            'plot_container': False,  # Hidden for data entry
            'enhanced_column_container': True,  # Keep for reference
            'table_container': True,
            'overview_container': False,  # Hidden
            'curve_visibility_toolbar': False,
            'zoom_controls': False
        }
        
        # Scale settings - standard
        preset.depth_scale = 10.0
        preset.default_zoom = 1.0
        
        # Toolbar configuration - minimal
        preset.toolbar_config = {
            'show_curve_tools': False,
            'show_zoom_tools': False,
            'show_measurement_tools': False,
            'show_annotation_tools': False,
            'show_data_entry_tools': True
        }
        
        # Metadata
        preset.metadata = {
            'scale': 'N/A',
            'category': 'data',
            'icon': 'data_entry',
            'keyboard_shortcut': 'Ctrl+4'
        }
        
        return preset
    
    @staticmethod
    def get_all_presets() -> Dict[str, LayoutPreset]:
        """Get all available presets."""
        return {
            'graphic_log': OnePointLayoutPresets.get_graphic_log_preset(),
            'strat_log': OnePointLayoutPresets.get_strat_log_preset(),
            'stacked': OnePointLayoutPresets.get_stacked_preset(),
            'data_entry': OnePointLayoutPresets.get_data_entry_preset()
        }
    
    @staticmethod
    def get_preset_by_name(name: str) -> Optional[LayoutPreset]:
        """Get preset by name."""
        presets = OnePointLayoutPresets.get_all_presets()
        for preset in presets.values():
            if preset.name == name:
                return preset
        return None


class LayoutManager(QObject):
    """Manages layout presets and custom layouts."""
    
    # Signals
    layoutChanged = pyqtSignal(str)  # Emitted when layout changes (preset_name)
    presetApplied = pyqtSignal(LayoutPreset)  # Emitted when a preset is applied
    customLayoutSaved = pyqtSignal(str)  # Emitted when custom layout is saved
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("Earthworm", "LayoutPresets")
        self.current_preset = None
        self.custom_layouts = {}
        self.load_custom_layouts()
        
    def apply_preset(self, preset: LayoutPreset, target_window) -> bool:
        """
        Apply a layout preset to a target window.
        
        Args:
            preset: The layout preset to apply
            target_window: The HoleEditorWindow to apply the preset to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"Applying layout preset: {preset.name}")
            
            # Store current preset
            self.current_preset = preset
            
            # Apply splitter sizes if window has splitters
            if hasattr(target_window, 'main_splitter') and preset.splitter_sizes:
                self._apply_splitter_sizes(target_window.main_splitter, preset.splitter_sizes)
            
            # Apply widget visibility
            for widget_name, is_visible in preset.widget_visibility.items():
                self._set_widget_visibility(target_window, widget_name, is_visible)
            
            # Apply depth scale to zoom state manager
            if hasattr(target_window, 'zoom_state_manager'):
                target_window.zoom_state_manager.set_depth_scale(preset.depth_scale)
            
            # Apply default zoom
            if hasattr(target_window, 'zoom_state_manager') and preset.default_zoom:
                target_window.zoom_state_manager.zoom_factor = preset.default_zoom
                target_window.zoom_state_manager.zoomLevelChanged.emit(preset.default_zoom)
            
            # Emit signals
            self.layoutChanged.emit(preset.name)
            self.presetApplied.emit(preset)
            
            # Save last used preset
            self.settings.setValue("last_preset", preset.name)
            
            print(f"Successfully applied preset: {preset.name}")
            return True
            
        except Exception as e:
            print(f"Error applying preset {preset.name}: {e}")
            return False
    
    def save_custom_layout(self, name: str, description: str, target_window) -> bool:
        """
        Save current window layout as a custom preset.
        
        Args:
            name: Name for the custom layout
            description: Description of the layout
            target_window: The HoleEditorWindow to save layout from
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            preset = LayoutPreset(name, description)
            
            # Capture splitter sizes
            if hasattr(target_window, 'main_splitter'):
                preset.splitter_sizes = target_window.main_splitter.sizes()
            
            # Capture widget visibility
            preset.widget_visibility = self._capture_widget_visibility(target_window)
            
            # Capture depth scale
            if hasattr(target_window, 'zoom_state_manager'):
                preset.depth_scale = target_window.zoom_state_manager.depth_scale
            
            # Capture zoom factor
            if hasattr(target_window, 'zoom_state_manager'):
                preset.default_zoom = target_window.zoom_state_manager.zoom_factor
            
            # Add to custom layouts
            self.custom_layouts[name] = preset.to_dict()
            
            # Save to settings
            self.settings.setValue("custom_layouts", json.dumps(self.custom_layouts))
            
            # Emit signal
            self.customLayoutSaved.emit(name)
            
            print(f"Saved custom layout: {name}")
            return True
            
        except Exception as e:
            print(f"Error saving custom layout: {e}")
            return False
    
    def get_custom_layout(self, name: str) -> Optional[LayoutPreset]:
        """Get a custom layout by name."""
        if name in self.custom_layouts:
            return LayoutPreset.from_dict(self.custom_layouts[name])
        return None
    
    def delete_custom_layout(self, name: str) -> bool:
        """Delete a custom layout."""
        if name in self.custom_layouts:
            del self.custom_layouts[name]
            self.settings.setValue("custom_layouts", json.dumps(self.custom_layouts))
            return True
        return False
    
    def get_all_presets(self) -> Dict[str, LayoutPreset]:
        """Get all presets (built-in + custom)."""
        all_presets = OnePointLayoutPresets.get_all_presets()
        
        # Add custom layouts
        for name, data in self.custom_layouts.items():
            all_presets[f"custom_{name}"] = LayoutPreset.from_dict(data)
        
        return all_presets
    
    def get_last_used_preset(self) -> Optional[str]:
        """Get the name of the last used preset."""
        return self.settings.value("last_preset", None)
    
    def load_custom_layouts(self):
        """Load custom layouts from settings."""
        custom_layouts_json = self.settings.value("custom_layouts", "{}")
        try:
            self.custom_layouts = json.loads(custom_layouts_json)
        except json.JSONDecodeError:
            self.custom_layouts = {}
    
    def _apply_splitter_sizes(self, splitter: QSplitter, sizes: List[int]):
        """Apply sizes to a splitter."""
        if splitter and sizes and len(sizes) == splitter.count():
            splitter.setSizes(sizes)
    
    def _set_widget_visibility(self, window, widget_name: str, is_visible: bool):
        """Set visibility of a widget by name."""
        widget = getattr(window, widget_name, None)
        if widget:
            widget.setVisible(is_visible)
    
    def _capture_widget_visibility(self, window) -> Dict[str, bool]:
        """Capture visibility state of all relevant widgets."""
        visibility = {}
        widget_names = [
            'plot_container', 'enhanced_column_container', 
            'table_container', 'overview_container'
        ]
        
        for name in widget_names:
            widget = getattr(window, name, None)
            if widget:
                visibility[name] = widget.isVisible()
        
        return visibility