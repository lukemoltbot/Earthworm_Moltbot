"""
CurveVisibilityToolbar - A toolbar widget for controlling curve visibility.
Provides quick-access controls for toggling curve visibility with color-coded indicators.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QToolBar, QPushButton, 
    QCheckBox, QLabel, QFrame, QMenu, QAction, QSizePolicy
)
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QActionGroup
from PyQt6.QtCore import Qt, pyqtSignal, QSize

class CurveVisibilityToolbar(QToolBar):
    """A toolbar widget for controlling curve visibility with color-coded indicators."""
    
    # Signal emitted when curve visibility changes
    curve_visibility_changed = pyqtSignal(str, bool)  # curve_name, visible
    group_visibility_changed = pyqtSignal(str, bool)  # group_name, visible
    
    def __init__(self, parent=None, visibility_manager=None):
        super().__init__("Curve Visibility", parent)
        self.visibility_manager = visibility_manager
        
        # Set toolbar properties
        self.setMovable(True)
        self.setFloatable(True)
        self.setIconSize(QSize(16, 16))
        
        # Curve checkboxes dictionary
        self.curve_checkboxes = {}
        
        # Group buttons dictionary
        self.group_buttons = {}
        
        # Setup UI
        self.setup_ui()
        
        # Connect to visibility manager if provided
        if self.visibility_manager:
            self.visibility_manager.visibility_changed.connect(self.on_visibility_changed)
    
    def setup_ui(self):
        """Setup the toolbar UI with curve controls and group buttons."""
        # Add separator
        self.addSeparator()
        
        # Add title label
        title_label = QLabel("Curves:")
        title_label.setStyleSheet("font-weight: bold; padding: 0 5px;")
        self.addWidget(title_label)
        
        # Add separator
        self.addSeparator()
        
        # Create default curve checkboxes (will be updated when curves are registered)
        self.create_default_curve_controls()
        
        # Add separator
        self.addSeparator()
        
        # Add group controls
        self.create_group_controls()
        
        # Add separator
        self.addSeparator()
        
        # Add reset button
        reset_button = QPushButton("Reset All")
        reset_button.setToolTip("Reset all curves to default visibility")
        reset_button.clicked.connect(self.on_reset_all)
        self.addWidget(reset_button)
    
    def create_default_curve_controls(self):
        """Create default curve checkboxes for common curve types."""
        # Common curve types with their colors and display names
        default_curves = [
            {
                'name': 'gamma',
                'display_name': 'Gamma Ray',
                'color': '#8b008b',  # Purple
                'abbreviation': 'GR',
                'default_visible': True
            },
            {
                'name': 'short_space_density',
                'display_name': 'Short Space',
                'color': '#0000ff',  # Blue
                'abbreviation': 'SS',
                'default_visible': True
            },
            {
                'name': 'long_space_density',
                'display_name': 'Long Space',
                'color': '#008000',  # Green
                'abbreviation': 'LS',
                'default_visible': True
            },
            {
                'name': 'cd',
                'display_name': 'Caliper',
                'color': '#ff8c00',  # Dark orange
                'abbreviation': 'CD',
                'default_visible': True
            },
            {
                'name': 'res',
                'display_name': 'Resistivity',
                'color': '#ff0000',  # Red
                'abbreviation': 'RES',
                'default_visible': True
            }
        ]
        
        for curve_info in default_curves:
            self.add_curve_checkbox(
                curve_info['name'],
                curve_info['display_name'],
                curve_info['color'],
                curve_info['abbreviation'],
                curve_info['default_visible']
            )
    
    def add_curve_checkbox(self, curve_name: str, display_name: str, 
                          color: str, abbreviation: str = None, 
                          default_visible: bool = True):
        """
        Add a checkbox for controlling a specific curve's visibility.
        
        Args:
            curve_name: Internal curve name
            display_name: User-friendly display name
            color: Curve color in hex format
            abbreviation: Short abbreviation (e.g., 'GR', 'SS')
            default_visible: Default visibility state
        """
        # Create checkbox with color indicator
        checkbox_widget = ColorCheckbox(
            text=f"{abbreviation if abbreviation else ''} {display_name}",
            color=color,
            parent=self
        )
        
        # Set initial state
        checkbox_widget.setChecked(default_visible)
        
        # Store curve name as property
        checkbox_widget.curve_name = curve_name
        
        # Connect signal
        checkbox_widget.toggled.connect(
            lambda checked, cn=curve_name: self.on_curve_toggled(cn, checked)
        )
        
        # Add to toolbar
        self.addWidget(checkbox_widget)
        
        # Store reference
        self.curve_checkboxes[curve_name] = checkbox_widget
        
        # Set tooltip
        tooltip = f"Toggle {display_name} visibility"
        if abbreviation:
            tooltip += f" ({abbreviation})"
        checkbox_widget.setToolTip(tooltip)
    
    def create_group_controls(self):
        """Create group control buttons."""
        # Add group label
        group_label = QLabel("Groups:")
        group_label.setStyleSheet("font-weight: bold; padding: 0 5px;")
        self.addWidget(group_label)
        
        # Group definitions
        groups = [
            {
                'name': 'gamma',
                'display_name': 'All Gamma',
                'color': '#8b008b',
                'tooltip': 'Show/hide all gamma ray curves'
            },
            {
                'name': 'density',
                'display_name': 'All Density',
                'color': '#0000ff',
                'tooltip': 'Show/hide all density curves'
            },
            {
                'name': 'all',
                'display_name': 'All Curves',
                'color': '#666666',
                'tooltip': 'Show/hide all curves'
            }
        ]
        
        for group_info in groups:
            # Create group button
            button = QPushButton(group_info['display_name'])
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {group_info['color']};
                    color: white;
                    border: 1px solid #333;
                    padding: 3px 8px;
                    border-radius: 3px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {self._lighten_color(group_info['color'])};
                }}
                QPushButton:pressed {{
                    background-color: {self._darken_color(group_info['color'])};
                }}
            """)
            
            button.setToolTip(group_info['tooltip'])
            button.setFixedHeight(24)
            
            # Connect signal
            button.clicked.connect(
                lambda checked, gn=group_info['name']: self.on_group_clicked(gn)
            )
            
            # Add to toolbar
            self.addWidget(button)
            
            # Store reference
            self.group_buttons[group_info['name']] = button
    
    def _lighten_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Lighten a hex color by a factor."""
        color = QColor(hex_color)
        return color.lighter(int(100 + factor * 100)).name()
    
    def _darken_color(self, hex_color: str, factor: float = 0.2) -> str:
        """Darken a hex color by a factor."""
        color = QColor(hex_color)
        return color.darker(int(100 + factor * 100)).name()
    
    def on_curve_toggled(self, curve_name: str, visible: bool):
        """Handle curve checkbox toggled."""
        # Update visibility manager if available
        if self.visibility_manager:
            self.visibility_manager.set_curve_visibility(curve_name, visible)
        
        # Emit signal
        self.curve_visibility_changed.emit(curve_name, visible)
    
    def on_group_clicked(self, group_name: str):
        """Handle group button click."""
        # Determine current state of the group
        all_visible = True
        any_visible = False
        
        # Check curves in this group
        if self.visibility_manager:
            # Use visibility manager to determine group state
            group_curves = self.visibility_manager.get_group_curves(group_name)
            for curve_name in group_curves:
                if curve_name in self.curve_checkboxes:
                    if self.curve_checkboxes[curve_name].isChecked():
                        any_visible = True
                    else:
                        all_visible = False
        else:
            # Fallback: check all checkboxes for patterns
            for curve_name, checkbox in self.curve_checkboxes.items():
                curve_name_lower = curve_name.lower()
                
                # Check if curve belongs to group
                if group_name == 'gamma' and 'gamma' in curve_name_lower:
                    if checkbox.isChecked():
                        any_visible = True
                    else:
                        all_visible = False
                elif group_name == 'density' and ('density' in curve_name_lower or 'ss' in curve_name_lower or 'ls' in curve_name_lower):
                    if checkbox.isChecked():
                        any_visible = True
                    else:
                        all_visible = False
                elif group_name == 'all':
                    if checkbox.isChecked():
                        any_visible = True
                    else:
                        all_visible = False
        
        # Toggle to opposite of all_visible (if all are visible, hide all; otherwise show all)
        new_visible = not all_visible
        
        # Update curves
        if self.visibility_manager:
            self.visibility_manager.set_group_visibility(group_name, new_visible)
        else:
            # Fallback: update checkboxes directly
            for curve_name, checkbox in self.curve_checkboxes.items():
                curve_name_lower = curve_name.lower()
                
                # Check if curve belongs to group
                if group_name == 'gamma' and 'gamma' in curve_name_lower:
                    checkbox.setChecked(new_visible)
                    self.on_curve_toggled(curve_name, new_visible)
                elif group_name == 'density' and ('density' in curve_name_lower or 'ss' in curve_name_lower or 'ls' in curve_name_lower):
                    checkbox.setChecked(new_visible)
                    self.on_curve_toggled(curve_name, new_visible)
                elif group_name == 'all':
                    checkbox.setChecked(new_visible)
                    self.on_curve_toggled(curve_name, new_visible)
        
        # Emit signal
        self.group_visibility_changed.emit(group_name, new_visible)
    
    def on_reset_all(self):
        """Handle reset all button click."""
        # Reset to default visibility
        if self.visibility_manager:
            self.visibility_manager.reset_to_defaults()
        else:
            # Fallback: set all checkboxes to True
            for curve_name, checkbox in self.curve_checkboxes.items():
                checkbox.setChecked(True)
                self.on_curve_toggled(curve_name, True)
    
    def on_visibility_changed(self, curve_name: str, visible: bool):
        """Update checkbox state when visibility changes externally."""
        if curve_name in self.curve_checkboxes:
            # Block signals to prevent recursive updates
            checkbox = self.curve_checkboxes[curve_name]
            checkbox.blockSignals(True)
            checkbox.setChecked(visible)
            checkbox.blockSignals(False)
    
    def update_from_visibility_manager(self):
        """Update checkboxes from visibility manager states."""
        if not self.visibility_manager:
            return
        
        # Block signals during update
        for checkbox in self.curve_checkboxes.values():
            checkbox.blockSignals(True)
        
        # Update each checkbox
        for curve_name, checkbox in self.curve_checkboxes.items():
            if curve_name in self.visibility_manager.visibility_states:
                visible = self.visibility_manager.visibility_states[curve_name]
                checkbox.setChecked(visible)
        
        # Unblock signals
        for checkbox in self.curve_checkboxes.values():
            checkbox.blockSignals(False)
    
    def register_curves_from_manager(self):
        """Register curves from visibility manager."""
        if not self.visibility_manager:
            return
        
        # Clear existing checkboxes
        for checkbox in self.curve_checkboxes.values():
            self.removeWidget(checkbox)
            checkbox.deleteLater()
        self.curve_checkboxes.clear()
        
        # Add checkboxes for each curve in the manager
        for curve_name, metadata in self.visibility_manager.curve_metadata.items():
            display_name = metadata.get('display_name', curve_name)
            color = metadata.get('color', '#666666')
            abbreviation = self._get_abbreviation(curve_name)
            
            self.add_curve_checkbox(
                curve_name,
                display_name,
                color,
                abbreviation,
                metadata.get('visible', True)
            )
    
    def _get_abbreviation(self, curve_name: str) -> str:
        """Get abbreviation for a curve name."""
        curve_lower = curve_name.lower()
        
        if 'gamma' in curve_lower or 'gr' in curve_lower:
            return 'GR'
        elif 'short' in curve_lower or 'ss' in curve_lower:
            return 'SS'
        elif 'long' in curve_lower or 'ls' in curve_lower:
            return 'LS'
        elif 'caliper' in curve_lower or 'cd' in curve_lower or 'cal' in curve_lower:
            return 'CD'
        elif 'resistivity' in curve_lower or 'res' in curve_lower:
            return 'RES'
        elif 'neutron' in curve_lower:
            return 'NEUT'
        elif 'sonic' in curve_lower:
            return 'DT'
        elif 'sp' in curve_lower:
            return 'SP'
        else:
            # Use first 3-4 characters as abbreviation
            return curve_name[:4].upper()


class ColorCheckbox(QCheckBox):
    """A checkbox with a colored indicator."""
    
    def __init__(self, text="", color="#666666", parent=None):
        super().__init__(text, parent)
        self.color = QColor(color)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
    
    def paintEvent(self, event):
        """Custom paint event to draw colored indicator."""
        # Call parent paint event first
        super().paintEvent(event)
        
        # Draw custom colored indicator
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate indicator position
        indicator_rect = self.style().subElementRect(
            self.style().SubElement.SE_CheckBoxIndicator, 
            self
        )
        
        # Draw colored circle
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(indicator_rect.center(), 6, 6)
        
        # Draw check mark if checked
        if self.isChecked():
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.drawLine(
                indicator_rect.center().x() - 3,
                indicator_rect.center().y(),
                indicator_rect.center().x() - 1,
                indicator_rect.center().y() + 3
            )
            painter.drawLine(
                indicator_rect.center().x() - 1,
                indicator_rect.center().y() + 3,
                indicator_rect.center().x() + 4,
                indicator_rect.center().y() - 2
            )