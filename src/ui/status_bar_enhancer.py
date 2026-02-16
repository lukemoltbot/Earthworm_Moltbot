"""
Status Bar Enhancer for Earthworm
Provides enhanced status bar with engineering scale, mouse coordinates, and distance display.
"""

from PyQt6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPointF
import json
import os


class StatusBarEnhancer(QObject):
    """
    Enhances the status bar with 1Point-style features.
    All enhancements are optional and configurable via settings.
    """
    
    # Signals for status updates
    statusMessageChanged = pyqtSignal(str)  # General status message
    engineeringScaleChanged = pyqtSignal(str)  # Engineering scale display
    mouseCoordinatesChanged = pyqtSignal(str)  # Mouse coordinates display
    distanceDisplayChanged = pyqtSignal(str)  # Distance display
    
    def __init__(self, status_bar, parent=None):
        super().__init__(parent)
        self.status_bar = status_bar
        self.parent_widget = parent
        
        # Load settings
        self.settings = {}
        self.load_settings()
        
        # Timer for updating mouse coordinates
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.update_mouse_position)
        self.mouse_timer.setInterval(100)  # Update every 100ms
        
        # Create enhanced widgets
        self.create_enhanced_widgets()
        
        # Current mouse position
        self.current_mouse_pos = None
        
        # Last selected position for distance calculation
        self.last_selected_pos = None
        
        # Engineering scale
        self.current_scale = "1:100"
        self.scale_factors = {
            "1:20": 20,
            "1:50": 50,
            "1:100": 100,
            "1:200": 200,
            "1:500": 500,
            "1:1000": 1000
        }
        
        # Unit system
        self.use_metric = True  # True for metric, False for imperial
        
    def load_settings(self):
        """Load status bar settings from configuration file."""
        try:
            settings_path = os.path.expanduser('~/earthworm_project-master/earthworm_settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    all_settings = json.load(f)
                    self.settings = all_settings.get('status_bar', {})
        except Exception as e:
            print(f"Error loading status bar settings: {e}")
            self.settings = {
                'enabled': True,
                'show_engineering_scale': True,
                'show_mouse_coordinates': True,
                'show_distance': True,
                'show_units': True,
                'auto_update': True,
                'scale_precision': 2,
                'coordinate_precision': 2,
                'distance_precision': 2
            }
    
    def save_settings(self):
        """Save status bar settings to configuration file."""
        try:
            settings_path = os.path.expanduser('~/earthworm_project-master/earthworm_settings.json')
            all_settings = {}
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    all_settings = json.load(f)
            
            all_settings['status_bar'] = self.settings
            
            with open(settings_path, 'w') as f:
                json.dump(all_settings, f, indent=2)
        except Exception as e:
            print(f"Error saving status bar settings: {e}")
    
    def create_enhanced_widgets(self):
        """Create enhanced status bar widgets."""
        if not self.settings.get('enabled', True):
            return
        
        # Remove existing permanent widgets
        self.status_bar.clearMessage()
        
        # Create container widget for enhanced status bar
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Engineering scale label
        if self.settings.get('show_engineering_scale', True):
            self.scale_label = QLabel("Scale: 1:100")
            self.scale_label.setStyleSheet("QLabel { padding: 2px 5px; border: 1px solid #ccc; border-radius: 3px; }")
            self.scale_label.setToolTip("Current engineering scale")
            layout.addWidget(self.scale_label)
        
        # Mouse coordinates label
        if self.settings.get('show_mouse_coordinates', True):
            self.coords_label = QLabel("X: 0.00, Y: 0.00")
            self.coords_label.setStyleSheet("QLabel { padding: 2px 5px; border: 1px solid #ccc; border-radius: 3px; }")
            self.coords_label.setToolTip("Mouse coordinates")
            layout.addWidget(self.coords_label)
        
        # Distance label
        if self.settings.get('show_distance', True):
            self.distance_label = QLabel("Distance: -")
            self.distance_label.setStyleSheet("QLabel { padding: 2px 5px; border: 1px solid #ccc; border-radius: 3px; }")
            self.distance_label.setToolTip("Distance from last selected object")
            layout.addWidget(self.distance_label)
        
        # Units label
        if self.settings.get('show_units', True):
            self.units_label = QLabel("Units: Metric")
            self.units_label.setStyleSheet("QLabel { padding: 2px 5px; border: 1px solid #ccc; border-radius: 3px; }")
            self.units_label.setToolTip("Current unit system")
            layout.addWidget(self.units_label)
        
        # Add stretch to push widgets to the right
        layout.addStretch()
        
        # Add container to status bar
        self.status_bar.addPermanentWidget(container)
        
        # Start mouse tracking if enabled
        if self.settings.get('show_mouse_coordinates', True) and self.settings.get('auto_update', True):
            self.start_mouse_tracking()
    
    def start_mouse_tracking(self):
        """Start tracking mouse position."""
        if self.parent_widget:
            self.parent_widget.setMouseTracking(True)
            self.mouse_timer.start()
    
    def stop_mouse_tracking(self):
        """Stop tracking mouse position."""
        self.mouse_timer.stop()
    
    def update_mouse_position(self):
        """Update mouse position display."""
        if not self.settings.get('show_mouse_coordinates', True) or not self.current_mouse_pos:
            return
        
        precision = self.settings.get('coordinate_precision', 2)
        
        if self.use_metric:
            x_str = f"{self.current_mouse_pos.x():.{precision}f}m"
            y_str = f"{self.current_mouse_pos.y():.{precision}f}m"
        else:
            # Convert to feet (1m = 3.28084ft)
            x_ft = self.current_mouse_pos.x() * 3.28084
            y_ft = self.current_mouse_pos.y() * 3.28084
            x_str = f"{x_ft:.{precision}f}ft"
            y_str = f"{y_ft:.{precision}f}ft"
        
        self.coords_label.setText(f"X: {x_str}, Y: {y_str}")
        
        # Update distance if we have a last selected position
        self.update_distance_display()
    
    def update_distance_display(self):
        """Update distance display."""
        if not self.settings.get('show_distance', True):
            return
        
        if self.last_selected_pos and self.current_mouse_pos:
            dx = self.current_mouse_pos.x() - self.last_selected_pos.x()
            dy = self.current_mouse_pos.y() - self.last_selected_pos.y()
            distance = (dx**2 + dy**2)**0.5
            
            precision = self.settings.get('distance_precision', 2)
            
            if self.use_metric:
                distance_str = f"{distance:.{precision}f}m"
            else:
                distance_ft = distance * 3.28084
                distance_str = f"{distance_ft:.{precision}f}ft"
            
            self.distance_label.setText(f"Distance: {distance_str}")
        else:
            self.distance_label.setText("Distance: -")
    
    def set_mouse_position(self, pos):
        """Set current mouse position."""
        self.current_mouse_pos = pos
    
    def set_last_selected_position(self, pos):
        """Set last selected position for distance calculation."""
        self.last_selected_pos = pos
        self.update_distance_display()
    
    def set_engineering_scale(self, scale):
        """
        Set engineering scale.
        
        Args:
            scale: Scale string (e.g., "1:100") or scale factor (e.g., 100)
        """
        if isinstance(scale, str):
            if scale in self.scale_factors:
                self.current_scale = scale
            else:
                # Try to parse custom scale
                try:
                    if scale.startswith("1:"):
                        factor = float(scale[2:])
                        self.current_scale = scale
                        self.scale_factors[scale] = factor
                except:
                    pass
        elif isinstance(scale, (int, float)):
            # Find closest standard scale
            closest = min(self.scale_factors.items(), key=lambda x: abs(x[1] - scale))
            self.current_scale = closest[0]
        
        if hasattr(self, 'scale_label'):
            self.scale_label.setText(f"Scale: {self.current_scale}")
        
        self.engineeringScaleChanged.emit(self.current_scale)
    
    def toggle_engineering_scale(self, visible):
        """Toggle engineering scale display."""
        if hasattr(self, 'scale_label'):
            self.scale_label.setVisible(visible)
        self.settings['show_engineering_scale'] = visible
        self.save_settings()
    
    def toggle_mouse_coordinates(self, visible):
        """Toggle mouse coordinates display."""
        if hasattr(self, 'coords_label'):
            self.coords_label.setVisible(visible)
        
        if visible and self.settings.get('auto_update', True):
            self.start_mouse_tracking()
        else:
            self.stop_mouse_tracking()
        
        self.settings['show_mouse_coordinates'] = visible
        self.save_settings()
    
    def toggle_distance_display(self, visible):
        """Toggle distance display."""
        if hasattr(self, 'distance_label'):
            self.distance_label.setVisible(visible)
        self.settings['show_distance'] = visible
        self.save_settings()
    
    def toggle_units_display(self, visible):
        """Toggle units display."""
        if hasattr(self, 'units_label'):
            self.units_label.setVisible(visible)
        self.settings['show_units'] = visible
        self.save_settings()
    
    def toggle_unit_system(self, use_metric=None):
        """Toggle between metric and imperial units."""
        if use_metric is not None:
            self.use_metric = use_metric
        else:
            self.use_metric = not self.use_metric
        
        if hasattr(self, 'units_label'):
            self.units_label.setText(f"Units: {'Metric' if self.use_metric else 'Imperial'}")
        
        # Update displays
        self.update_mouse_position()
    
    def set_scale_precision(self, precision):
        """Set precision for scale display."""
        self.settings['scale_precision'] = max(0, min(6, precision))
        self.save_settings()
    
    def set_coordinate_precision(self, precision):
        """Set precision for coordinate display."""
        self.settings['coordinate_precision'] = max(0, min(6, precision))
        self.save_settings()
        self.update_mouse_position()
    
    def set_distance_precision(self, precision):
        """Set precision for distance display."""
        self.settings['distance_precision'] = max(0, min(6, precision))
        self.save_settings()
        self.update_distance_display()
    
    def show_status_message(self, message, timeout=0):
        """
        Show a status message.
        
        Args:
            message: Message to display
            timeout: Time in milliseconds before clearing (0 = permanent)
        """
        self.status_bar.showMessage(message, timeout)
        self.statusMessageChanged.emit(message)
    
    def clear_status_message(self):
        """Clear the status message."""
        self.status_bar.clearMessage()
    
    def update_from_zoom(self, zoom_factor):
        """
        Update engineering scale based on zoom factor.
        
        Args:
            zoom_factor: Current zoom factor
        """
        # Calculate appropriate scale based on zoom
        # This is a simplified calculation - adjust based on your actual scale logic
        base_scale = 100  # 1:100 at zoom 1.0
        calculated_scale = base_scale / zoom_factor
        
        # Round to nearest standard scale
        standard_scales = list(self.scale_factors.values())
        closest_scale = min(standard_scales, key=lambda x: abs(x - calculated_scale))
        
        # Find scale string
        for scale_str, scale_val in self.scale_factors.items():
            if scale_val == closest_scale:
                self.set_engineering_scale(scale_str)
                break
    
    def handle_keyboard_shortcut(self, event):
        """
        Handle keyboard shortcuts for status bar features.
        
        Args:
            event: Key event
            
        Returns:
            True if shortcut was handled, False otherwise
        """
        # Ctrl+wheel for scale adjustment
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if hasattr(event, 'angleDelta'):  # Mouse wheel event
                delta = event.angleDelta().y()
                if delta > 0:
                    # Zoom in - decrease scale factor
                    self.adjust_scale(-1)
                else:
                    # Zoom out - increase scale factor
                    self.adjust_scale(1)
                return True
        
        # Shift for sync toggle (placeholder)
        elif event.key() == Qt.Key.Key_Shift:
            # This would toggle sync mode
            # Implementation depends on main application
            pass
        
        # Alt+wheel for optional zoom (placeholder)
        elif event.modifiers() == Qt.KeyboardModifier.AltModifier:
            if hasattr(event, 'angleDelta'):  # Mouse wheel event
                # Optional zoom implementation
                pass
        
        return False
    
    def adjust_scale(self, direction):
        """
        Adjust engineering scale.
        
        Args:
            direction: 1 for larger scale (more detail), -1 for smaller scale (less detail)
        """
        scale_keys = list(self.scale_factors.keys())
        current_index = scale_keys.index(self.current_scale) if self.current_scale in scale_keys else 2
        
        new_index = current_index + direction
        if 0 <= new_index < len(scale_keys):
            self.set_engineering_scale(scale_keys[new_index])