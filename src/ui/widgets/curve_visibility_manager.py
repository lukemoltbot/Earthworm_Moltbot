"""
CurveVisibilityManager - Manages curve visibility states with persistence and group controls.
Provides comprehensive curve visibility management for the PyQtGraphCurvePlotter.
"""

import json
import os
from typing import Dict, List, Optional, Set
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor

class CurveVisibilityManager(QObject):
    """Manages curve visibility states with persistence and group controls."""
    
    # Signal emitted when visibility changes
    visibility_changed = pyqtSignal(str, bool)  # curve_name, visible
    
    def __init__(self, curve_plotter=None):
        super().__init__()
        self.curve_plotter = curve_plotter
        
        # Visibility states for individual curves
        self.visibility_states: Dict[str, bool] = {}
        
        # Curve groups for batch operations
        self.curve_groups: Dict[str, List[str]] = {
            'gamma': [],      # Gamma ray curves
            'density': [],    # Density curves (SS, LS)
            'caliper': [],    # Caliper curves (CD, CAL)
            'resistivity': [], # Resistivity curves
            'other': []       # Other curves
        }
        
        # Curve metadata (name, display_name, color, group)
        self.curve_metadata: Dict[str, Dict] = {}
        
        # Settings file path
        self.settings_dir = os.path.expanduser("~/.earthworm")
        self.settings_file = os.path.join(self.settings_dir, "curve_visibility.json")
        
        # Ensure settings directory exists
        os.makedirs(self.settings_dir, exist_ok=True)
        
        # Default visibility for curve types
        self.default_visibility = {
            'gamma': True,
            'density': True,
            'caliper': True,
            'resistivity': True,
            'other': True
        }
    
    def register_curve(self, curve_name: str, display_name: str = None, 
                      color: str = None, group: str = None):
        """
        Register a curve with the visibility manager.
        
        Args:
            curve_name: Internal curve name (e.g., 'GR', 'SS', 'LS')
            display_name: User-friendly display name (e.g., 'Gamma Ray')
            color: Curve color in hex format
            group: Curve group ('gamma', 'density', 'caliper', 'resistivity', 'other')
        """
        if display_name is None:
            display_name = curve_name
            
        if group is None:
            # Auto-detect group based on curve name
            group = self._detect_curve_group(curve_name)
            
        # Store metadata
        self.curve_metadata[curve_name] = {
            'display_name': display_name,
            'color': color,
            'group': group,
            'visible': True  # Default to visible
        }
        
        # Add to group
        if group in self.curve_groups:
            if curve_name not in self.curve_groups[group]:
                self.curve_groups[group].append(curve_name)
        
        # Set default visibility
        self.visibility_states[curve_name] = True
    
    def _detect_curve_group(self, curve_name: str) -> str:
        """Detect curve group based on curve name patterns."""
        curve_lower = curve_name.lower()
        
        # Gamma ray patterns
        gamma_patterns = ['gamma', 'gr', 'gammaray']
        if any(pattern in curve_lower for pattern in gamma_patterns):
            return 'gamma'
        
        # Density patterns
        density_patterns = ['density', 'den', 'rhob', 'ss', 'ls', 'short', 'long']
        if any(pattern in curve_lower for pattern in density_patterns):
            return 'density'
        
        # Caliper patterns
        caliper_patterns = ['caliper', 'cal', 'cd', 'diameter']
        if any(pattern in curve_lower for pattern in caliper_patterns):
            return 'caliper'
        
        # Resistivity patterns
        resistivity_patterns = ['resistivity', 'res', 'rt', 'ild']
        if any(pattern in curve_lower for pattern in resistivity_patterns):
            return 'resistivity'
        
        # Default to other
        return 'other'
    
    def set_curve_visibility(self, curve_name: str, visible: bool, 
                           update_plotter: bool = True):
        """
        Set visibility for a specific curve.
        
        Args:
            curve_name: Curve name to toggle
            visible: True to show, False to hide
            update_plotter: Whether to update the curve plotter immediately
        """
        if curve_name not in self.curve_metadata:
            print(f"Warning: Curve '{curve_name}' not registered")
            return
        
        # Update visibility state
        self.visibility_states[curve_name] = visible
        self.curve_metadata[curve_name]['visible'] = visible
        
        # Update curve plotter if available
        if update_plotter and self.curve_plotter:
            if hasattr(self.curve_plotter, 'set_curve_visibility'):
                self.curve_plotter.set_curve_visibility(curve_name, visible)
            elif hasattr(self.curve_plotter, 'curve_items'):
                # Direct access to curve items
                if curve_name in self.curve_plotter.curve_items:
                    curve_item = self.curve_plotter.curve_items[curve_name]
                    curve_item.setVisible(visible)
        
        # Emit signal
        self.visibility_changed.emit(curve_name, visible)
    
    def toggle_curve(self, curve_name: str, update_plotter: bool = True):
        """
        Toggle visibility for a specific curve.
        
        Args:
            curve_name: Curve name to toggle
            update_plotter: Whether to update the curve plotter immediately
        """
        if curve_name not in self.visibility_states:
            # Default to True if not set
            current = True
        else:
            current = self.visibility_states[curve_name]
        
        self.set_curve_visibility(curve_name, not current, update_plotter)
    
    def set_group_visibility(self, group_name: str, visible: bool, 
                           update_plotter: bool = True):
        """
        Set visibility for an entire group of curves.
        
        Args:
            group_name: Group name ('gamma', 'density', 'caliper', 'resistivity', 'other')
            visible: True to show, False to hide
            update_plotter: Whether to update the curve plotter immediately
        """
        if group_name not in self.curve_groups:
            print(f"Warning: Group '{group_name}' not found")
            return
        
        # Update all curves in the group
        for curve_name in self.curve_groups[group_name]:
            self.set_curve_visibility(curve_name, visible, update_plotter)
    
    def toggle_group(self, group_name: str, update_plotter: bool = True):
        """
        Toggle visibility for an entire group of curves.
        
        Args:
            group_name: Group name to toggle
            update_plotter: Whether to update the curve plotter immediately
        """
        if group_name not in self.curve_groups:
            print(f"Warning: Group '{group_name}' not found")
            return
        
        # Determine if all curves in group are currently visible
        all_visible = True
        for curve_name in self.curve_groups[group_name]:
            if curve_name in self.visibility_states:
                if not self.visibility_states[curve_name]:
                    all_visible = False
                    break
            else:
                # Curve not in visibility states, assume visible
                pass
        
        # Toggle to opposite state
        self.set_group_visibility(group_name, not all_visible, update_plotter)
    
    def show_all(self, update_plotter: bool = True):
        """Show all curves."""
        for curve_name in self.curve_metadata.keys():
            self.set_curve_visibility(curve_name, True, update_plotter)
    
    def hide_all(self, update_plotter: bool = True):
        """Hide all curves."""
        for curve_name in self.curve_metadata.keys():
            self.set_curve_visibility(curve_name, False, update_plotter)
    
    def reset_to_defaults(self, update_plotter: bool = True):
        """Reset all curves to default visibility based on their groups."""
        for curve_name, metadata in self.curve_metadata.items():
            group = metadata.get('group', 'other')
            default_visible = self.default_visibility.get(group, True)
            self.set_curve_visibility(curve_name, default_visible, update_plotter)
    
    def get_visible_curves(self) -> List[str]:
        """Get list of currently visible curves."""
        return [name for name, visible in self.visibility_states.items() 
                if visible and name in self.curve_metadata]
    
    def get_hidden_curves(self) -> List[str]:
        """Get list of currently hidden curves."""
        return [name for name, visible in self.visibility_states.items() 
                if not visible and name in self.curve_metadata]
    
    def get_curve_info(self, curve_name: str) -> Optional[Dict]:
        """Get metadata for a specific curve."""
        return self.curve_metadata.get(curve_name)
    
    def get_group_curves(self, group_name: str) -> List[str]:
        """Get all curves in a specific group."""
        return self.curve_groups.get(group_name, [])
    
    def save_states(self):
        """Save visibility states to user preferences file."""
        try:
            # Prepare data for saving
            save_data = {
                'visibility_states': self.visibility_states,
                'curve_metadata': self.curve_metadata,
                'curve_groups': self.curve_groups,
                'default_visibility': self.default_visibility
            }
            
            # Write to file
            with open(self.settings_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            print(f"Curve visibility states saved to {self.settings_file}")
            return True
            
        except Exception as e:
            print(f"Error saving curve visibility states: {e}")
            return False
    
    def load_states(self):
        """Load visibility states from user preferences file."""
        try:
            if not os.path.exists(self.settings_file):
                print(f"No saved curve visibility states found at {self.settings_file}")
                return False
            
            # Read from file
            with open(self.settings_file, 'r') as f:
                load_data = json.load(f)
            
            # Restore data
            self.visibility_states = load_data.get('visibility_states', {})
            self.curve_metadata = load_data.get('curve_metadata', {})
            self.curve_groups = load_data.get('curve_groups', self.curve_groups)
            self.default_visibility = load_data.get('default_visibility', self.default_visibility)
            
            print(f"Curve visibility states loaded from {self.settings_file}")
            return True
            
        except Exception as e:
            print(f"Error loading curve visibility states: {e}")
            return False
    
    def auto_register_from_plotter(self):
        """Automatically register curves from the curve plotter."""
        if not self.curve_plotter:
            return
        
        print(f"DEBUG (auto_register_from_plotter): Checking curve_plotter.curve_items")
        
        # Try to get curves from curve_items dictionary
        if hasattr(self.curve_plotter, 'curve_items'):
            print(f"DEBUG (auto_register_from_plotter): curve_items has {len(self.curve_plotter.curve_items)} items")
            for curve_name, curve_item in self.curve_plotter.curve_items.items():
                # Debug: check curve_name type
                if not isinstance(curve_name, str):
                    print(f"ERROR (auto_register_from_plotter): curve_name is {type(curve_name)}, not string: {curve_name}")
                    print(f"ERROR (auto_register_from_plotter): curve_item type: {type(curve_item)}")
                    # Try to get string representation
                    try:
                        print(f"ERROR (auto_register_from_plotter): curve_name repr: {repr(curve_name)}")
                    except:
                        pass
                    
                    # Try to extract string name from curve_item
                    if hasattr(curve_item, 'name'):
                        try:
                            # Call the name method if it's callable
                            if callable(curve_item.name):
                                curve_name = curve_item.name()
                            else:
                                curve_name = str(curve_item.name)
                            print(f"DEBUG (auto_register_from_plotter): Extracted curve name: {curve_name}")
                        except Exception as e:
                            print(f"ERROR (auto_register_from_plotter): Failed to extract name: {e}")
                            continue
                    else:
                        continue
                    
                # Try to get color from curve item
                color = None
                if hasattr(curve_item, 'opts'):
                    pen_opts = curve_item.opts.get('pen', {})
                    if isinstance(pen_opts, dict) and 'color' in pen_opts:
                        color = pen_opts['color']
                
                # Register curve
                self.register_curve(
                    curve_name=curve_name,
                    display_name=curve_name,
                    color=color
                )
        
        # Also check gamma_curves and density_curves
        if hasattr(self.curve_plotter, 'gamma_curves'):
            for curve in self.curve_plotter.gamma_curves:
                if hasattr(curve, 'name'):
                    self.register_curve(
                        curve_name=curve.name,
                        display_name=curve.name,
                        color='#8b008b',  # Purple for gamma
                        group='gamma'
                    )
        
        if hasattr(self.curve_plotter, 'density_curves'):
            for curve in self.curve_plotter.density_curves:
                if hasattr(curve, 'name'):
                    self.register_curve(
                        curve_name=curve.name,
                        display_name=curve.name,
                        color='#0000ff',  # Blue for density
                        group='density'
                    )
    
    def apply_states_to_plotter(self):
        """Apply current visibility states to the curve plotter."""
        if not self.curve_plotter:
            return
        
        for curve_name, visible in self.visibility_states.items():
            if hasattr(self.curve_plotter, 'set_curve_visibility'):
                self.curve_plotter.set_curve_visibility(curve_name, visible)