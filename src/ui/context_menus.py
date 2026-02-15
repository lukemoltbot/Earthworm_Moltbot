"""
OnePoint-style Context Menus for Earthworm
Provides 1Point-style right-click context menus for curve customization and UI enhancements.
"""

from PyQt6.QtWidgets import QMenu, QColorDialog, QInputDialog, QMessageBox
from PyQt6.QtGui import QColor, QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QObject
import json
import os


class OnePointContextMenus(QObject):
    """
    Provides 1Point-style context menus for various UI elements.
    All menus are optional and configurable via settings.
    """
    
    # Signals for menu actions
    curveColorChanged = pyqtSignal(str, QColor)  # curve_name, new_color
    curveThicknessChanged = pyqtSignal(str, float)  # curve_name, new_thickness
    curveLineStyleChanged = pyqtSignal(str, str)  # curve_name, line_style
    curveInvertedChanged = pyqtSignal(str, bool)  # curve_name, inverted
    curveVisibilityChanged = pyqtSignal(str, bool)  # curve_name, visible
    curveRangeChanged = pyqtSignal(str, float, float)  # curve_name, min, max
    curveRenamed = pyqtSignal(str, str)  # old_name, new_name
    curveDeleted = pyqtSignal(str)  # curve_name
    curveDuplicated = pyqtSignal(str, str)  # source_name, new_name
    
    # UI enhancement signals
    toggleEngineeringScale = pyqtSignal(bool)  # enabled
    toggleMouseCoordinates = pyqtSignal(bool)  # enabled
    toggleDistanceDisplay = pyqtSignal(bool)  # enabled
    toggleSyncMode = pyqtSignal(bool)  # enabled
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.settings = {}
        self.load_settings()
        
        # Track curve configurations
        self.curve_configs = []
        
        # Track last selected object for distance calculation
        self.last_selected_object = None
        self.last_selected_position = None
        
    def load_settings(self):
        """Load context menu settings from configuration file."""
        try:
            settings_path = os.path.expanduser('~/earthworm_project-master/earthworm_settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    all_settings = json.load(f)
                    self.settings = all_settings.get('context_menus', {})
        except Exception as e:
            print(f"Error loading context menu settings: {e}")
            self.settings = {
                'enabled': True,
                'curve_customization': True,
                'engineering_scale': True,
                'mouse_coordinates': True,
                'distance_display': True,
                'quick_actions': True
            }
    
    def save_settings(self):
        """Save context menu settings to configuration file."""
        try:
            settings_path = os.path.expanduser('~/earthworm_project-master/earthworm_settings.json')
            all_settings = {}
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    all_settings = json.load(f)
            
            all_settings['context_menus'] = self.settings
            
            with open(settings_path, 'w') as f:
                json.dump(all_settings, f, indent=2)
        except Exception as e:
            print(f"Error saving context menu settings: {e}")
    
    def is_enabled(self):
        """Check if context menus are enabled."""
        return self.settings.get('enabled', True)
    
    def create_curve_context_menu(self, curve_name, curve_config, position):
        """
        Create a context menu for curve customization.
        
        Args:
            curve_name: Name of the curve
            curve_config: Dictionary with curve configuration
            position: Position where menu should appear (QPoint)
            
        Returns:
            QMenu or None if disabled
        """
        if not self.is_enabled() or not self.settings.get('curve_customization', True):
            return None
        
        menu = QMenu(self.parent_widget)
        menu.setTitle(f"Curve: {curve_name}")
        
        # Color action
        color_action = QAction("Change Color...", menu)
        color_action.triggered.connect(lambda: self.change_curve_color(curve_name, curve_config))
        menu.addAction(color_action)
        
        # Thickness action
        thickness_action = QAction("Change Thickness...", menu)
        thickness_action.triggered.connect(lambda: self.change_curve_thickness(curve_name, curve_config))
        menu.addAction(thickness_action)
        
        # Line style submenu
        line_style_menu = menu.addMenu("Line Style")
        
        # Solid line
        solid_action = QAction("Solid", line_style_menu)
        solid_action.setCheckable(True)
        solid_action.setChecked(curve_config.get('line_style', 'solid') == 'solid')
        solid_action.triggered.connect(lambda: self.set_curve_line_style(curve_name, 'solid'))
        line_style_menu.addAction(solid_action)
        
        # Dotted line
        dotted_action = QAction("Dotted", line_style_menu)
        dotted_action.setCheckable(True)
        dotted_action.setChecked(curve_config.get('line_style', 'solid') == 'dotted')
        dotted_action.triggered.connect(lambda: self.set_curve_line_style(curve_name, 'dotted'))
        line_style_menu.addAction(dotted_action)
        
        # Dashed line
        dashed_action = QAction("Dashed", line_style_menu)
        dashed_action.setCheckable(True)
        dashed_action.setChecked(curve_config.get('line_style', 'solid') == 'dashed')
        dashed_action.triggered.connect(lambda: self.set_curve_line_style(curve_name, 'dashed'))
        line_style_menu.addAction(dashed_action)
        
        # Dash-dot line
        dash_dot_action = QAction("Dash-Dot", line_style_menu)
        dash_dot_action.setCheckable(True)
        dash_dot_action.setChecked(curve_config.get('line_style', 'solid') == 'dash_dot')
        dash_dot_action.triggered.connect(lambda: self.set_curve_line_style(curve_name, 'dash_dot'))
        line_style_menu.addAction(dash_dot_action)
        
        # Invert action
        invert_action = QAction("Invert Curve", menu)
        invert_action.setCheckable(True)
        invert_action.setChecked(curve_config.get('inverted', False))
        invert_action.triggered.connect(lambda checked: self.toggle_curve_inversion(curve_name, checked))
        menu.addAction(invert_action)
        
        # Visibility action
        visibility_action = QAction("Show/Hide Curve", menu)
        visibility_action.setCheckable(True)
        visibility_action.setChecked(curve_config.get('visible', True))
        visibility_action.triggered.connect(lambda checked: self.toggle_curve_visibility(curve_name, checked))
        menu.addAction(visibility_action)
        
        menu.addSeparator()
        
        # Range action
        range_action = QAction("Set Range...", menu)
        range_action.triggered.connect(lambda: self.set_curve_range(curve_name, curve_config))
        menu.addAction(range_action)
        
        # Rename action
        rename_action = QAction("Rename Curve...", menu)
        rename_action.triggered.connect(lambda: self.rename_curve(curve_name))
        menu.addAction(rename_action)
        
        # Duplicate action
        duplicate_action = QAction("Duplicate Curve...", menu)
        duplicate_action.triggered.connect(lambda: self.duplicate_curve(curve_name))
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Delete Curve", menu)
        delete_action.triggered.connect(lambda: self.delete_curve(curve_name))
        menu.addAction(delete_action)
        
        return menu
    
    def create_plot_area_context_menu(self, position, has_selected_object=False):
        """
        Create a context menu for the plot area.
        
        Args:
            position: Position where menu should appear (QPoint)
            has_selected_object: Whether an object is currently selected
            
        Returns:
            QMenu or None if disabled
        """
        if not self.is_enabled() or not self.settings.get('quick_actions', True):
            return None
        
        menu = QMenu(self.parent_widget)
        menu.setTitle("Plot Area")
        
        # Engineering scale toggle
        scale_action = QAction("Show Engineering Scale", menu)
        scale_action.setCheckable(True)
        scale_action.setChecked(self.settings.get('engineering_scale_visible', True))
        scale_action.triggered.connect(lambda checked: self.toggle_engineering_scale.emit(checked))
        menu.addAction(scale_action)
        
        # Mouse coordinates toggle
        coords_action = QAction("Show Mouse Coordinates", menu)
        coords_action.setCheckable(True)
        coords_action.setChecked(self.settings.get('mouse_coordinates_visible', True))
        coords_action.triggered.connect(lambda checked: self.toggle_mouse_coordinates.emit(checked))
        menu.addAction(coords_action)
        
        # Distance display toggle (only if object is selected)
        if has_selected_object:
            distance_action = QAction("Show Distance from Selection", menu)
            distance_action.setCheckable(True)
            distance_action.setChecked(self.settings.get('distance_display_visible', True))
            distance_action.triggered.connect(lambda checked: self.toggle_distance_display.emit(checked))
            menu.addAction(distance_action)
        
        menu.addSeparator()
        
        # Sync mode toggle
        sync_action = QAction("Enable Synchronization", menu)
        sync_action.setCheckable(True)
        sync_action.setChecked(self.settings.get('sync_enabled', True))
        sync_action.triggered.connect(lambda checked: self.toggle_sync_mode.emit(checked))
        menu.addAction(sync_action)
        
        # Reset view action
        reset_action = QAction("Reset View", menu)
        reset_action.triggered.connect(self.reset_view)
        menu.addAction(reset_action)
        
        # Fit to data action
        fit_action = QAction("Fit to Data", menu)
        fit_action.triggered.connect(self.fit_to_data)
        menu.addAction(fit_action)
        
        return menu
    
    def create_workspace_context_menu(self, position):
        """
        Create a context menu for workspace management.
        
        Args:
            position: Position where menu should appear (QPoint)
            
        Returns:
            QMenu or None if disabled
        """
        if not self.is_enabled():
            return None
        
        menu = QMenu(self.parent_widget)
        menu.setTitle("Workspace")
        
        # Layout shortcuts
        layout_menu = menu.addMenu("Layout")
        
        layout_actions = [
            ("Single View (Ctrl+1)", "single"),
            ("Dual View (Ctrl+2)", "dual"),
            ("Triple View (Ctrl+3)", "triple"),
            ("Quad View (Ctrl+4)", "quad")
        ]
        
        for text, layout_type in layout_actions:
            action = QAction(text, layout_menu)
            action.triggered.connect(lambda checked, lt=layout_type: self.change_layout(lt))
            layout_menu.addAction(action)
        
        menu.addSeparator()
        
        # Workspace management
        save_ws_action = QAction("Save Workspace...", menu)
        save_ws_action.triggered.connect(self.save_workspace)
        menu.addAction(save_ws_action)
        
        load_ws_action = QAction("Load Workspace...", menu)
        load_ws_action.triggered.connect(self.load_workspace)
        menu.addAction(load_ws_action)
        
        import_ws_action = QAction("Import Workspace...", menu)
        import_ws_action.triggered.connect(self.import_workspace)
        menu.addAction(import_ws_action)
        
        export_ws_action = QAction("Export Workspace...", menu)
        export_ws_action.triggered.connect(self.export_workspace)
        menu.addAction(export_ws_action)
        
        menu.addSeparator()
        
        # Workspace templates
        templates_menu = menu.addMenu("Templates")
        
        template_actions = [
            ("Single Hole Analysis", "single_hole"),
            ("Multi-Hole Comparison", "multi_hole"),
            ("Cross-Section Analysis", "cross_section"),
            ("Full Project", "full_project")
        ]
        
        for text, template_type in template_actions:
            action = QAction(text, templates_menu)
            action.triggered.connect(lambda checked, tt=template_type: self.load_template(tt))
            templates_menu.addAction(action)
        
        return menu
    
    def change_curve_color(self, curve_name, curve_config):
        """Open color dialog to change curve color."""
        current_color = QColor(curve_config.get('color', '#000000'))
        color = QColorDialog.getColor(current_color, self.parent_widget, f"Select color for {curve_name}")
        
        if color.isValid():
            self.curveColorChanged.emit(curve_name, color)
    
    def change_curve_thickness(self, curve_name, curve_config):
        """Open dialog to change curve thickness."""
        current_thickness = curve_config.get('thickness', 1.0)
        thickness, ok = QInputDialog.getDouble(
            self.parent_widget,
            "Curve Thickness",
            f"Enter thickness for {curve_name}:",
            current_thickness,
            0.1,  # min
            10.0,  # max
            1,     # decimals
        )
        
        if ok:
            self.curveThicknessChanged.emit(curve_name, thickness)
    
    def set_curve_line_style(self, curve_name, line_style):
        """Set curve line style."""
        # Map line style names to display names
        style_display_names = {
            'solid': 'Solid',
            'dotted': 'Dotted',
            'dashed': 'Dashed',
            'dash_dot': 'Dash-Dot'
        }
        
        display_name = style_display_names.get(line_style, line_style)
        print(f"Setting curve '{curve_name}' line style to: {display_name}")
        
        # Emit signal for line style change
        self.curveLineStyleChanged.emit(curve_name, line_style)
    
    def toggle_curve_inversion(self, curve_name, inverted):
        """Toggle curve inversion."""
        self.curveInvertedChanged.emit(curve_name, inverted)
    
    def toggle_curve_visibility(self, curve_name, visible):
        """Toggle curve visibility."""
        self.curveVisibilityChanged.emit(curve_name, visible)
    
    def set_curve_range(self, curve_name, curve_config):
        """Open dialog to set curve range."""
        current_min = curve_config.get('min', 0)
        current_max = curve_config.get('max', 100)
        
        # Create a simple dialog for range input
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QDialogButtonBox
        
        dialog = QDialog(self.parent_widget)
        dialog.setWindowTitle(f"Set Range for {curve_name}")
        layout = QVBoxLayout(dialog)
        
        # Min input
        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Minimum:"))
        min_spin = QDoubleSpinBox()
        min_spin.setRange(-1000000, 1000000)
        min_spin.setValue(current_min)
        min_spin.setDecimals(3)
        min_layout.addWidget(min_spin)
        layout.addLayout(min_layout)
        
        # Max input
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Maximum:"))
        max_spin = QDoubleSpinBox()
        max_spin.setRange(-1000000, 1000000)
        max_spin.setValue(current_max)
        max_spin.setDecimals(3)
        max_layout.addWidget(max_spin)
        layout.addLayout(max_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_min = min_spin.value()
            new_max = max_spin.value()
            if new_min < new_max:
                self.curveRangeChanged.emit(curve_name, new_min, new_max)
            else:
                QMessageBox.warning(self.parent_widget, "Invalid Range", "Minimum must be less than maximum.")
    
    def rename_curve(self, curve_name):
        """Open dialog to rename curve."""
        new_name, ok = QInputDialog.getText(
            self.parent_widget,
            "Rename Curve",
            "Enter new name:",
            text=curve_name
        )
        
        if ok and new_name.strip():
            self.curveRenamed.emit(curve_name, new_name.strip())
    
    def duplicate_curve(self, curve_name):
        """Open dialog to duplicate curve."""
        new_name, ok = QInputDialog.getText(
            self.parent_widget,
            "Duplicate Curve",
            "Enter name for duplicate:",
            text=f"{curve_name}_copy"
        )
        
        if ok and new_name.strip():
            self.curveDuplicated.emit(curve_name, new_name.strip())
    
    def delete_curve(self, curve_name):
        """Confirm and delete curve."""
        reply = QMessageBox.question(
            self.parent_widget,
            "Delete Curve",
            f"Are you sure you want to delete '{curve_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.curveDeleted.emit(curve_name)
    
    def change_layout(self, layout_type):
        """Change the workspace layout."""
        # This will be connected to the main window's layout change method
        print(f"Changing layout to: {layout_type}")
        # The actual implementation will be in the main window
    
    def save_workspace(self):
        """Save current workspace configuration."""
        print("Saving workspace...")
        # The actual implementation will be in the main window
    
    def load_workspace(self):
        """Load workspace configuration."""
        print("Loading workspace...")
        # The actual implementation will be in the main window
    
    def import_workspace(self):
        """Import workspace configuration from file."""
        print("Importing workspace...")
        # The actual implementation will be in the main window
    
    def export_workspace(self):
        """Export workspace configuration to file."""
        print("Exporting workspace...")
        # The actual implementation will be in the main window
    
    def load_template(self, template_type):
        """Load a workspace template."""
        print(f"Loading template: {template_type}")
        # The actual implementation will be in the main window
    
    def reset_view(self):
        """Reset the view to default state."""
        print("Resetting view...")
        # The actual implementation will be in the main window
    
    def fit_to_data(self):
        """Fit the view to show all data."""
        print("Fitting to data...")
        # The actual implementation will be in the main window
    
    def update_last_selected(self, obj, position):
        """
        Update the last selected object for distance calculation.
        
        Args:
            obj: The selected object
            position: Position of the selection (QPointF)
        """
        self.last_selected_object = obj
        self.last_selected_position = position
    
    def calculate_distance(self, current_position):
        """
        Calculate distance from last selected object.
        
        Args:
            current_position: Current position (QPointF)
            
        Returns:
            Distance as string or None if no previous selection
        """
        if self.last_selected_position is None:
            return None
        
        dx = current_position.x() - self.last_selected_position.x()
        dy = current_position.y() - self.last_selected_position.y()
        distance = (dx**2 + dy**2)**0.5
        
        return f"{distance:.2f} units"