"""
CrossHoleSyncManager - Manages synchronization of curve settings across multiple open holes.

Provides 1Point-style cross-hole synchronization features:
1. Sync curve selection across all open holes
2. Sync display settings (colors, styles, visibility)
3. SHIFT key toggle for temporary sync override
4. Settings integration: Tools → Settings → LAS → SyncLASCurves
"""

import json
import os
from typing import Dict, List, Set, Optional, Any
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication


class CrossHoleSyncManager(QObject):
    """
    Manages synchronization of curve settings across multiple open holes.
    
    Features:
    1. Central registry of all open holes
    2. Curve selection synchronization
    3. Display settings synchronization (colors, styles, visibility)
    4. SHIFT key temporary override
    5. Settings persistence
    """
    
    # Signals
    syncEnabledChanged = pyqtSignal(bool)  # sync enabled/disabled
    curveSelectionSynced = pyqtSignal(list)  # list of curve names
    curveSettingsSynced = pyqtSignal(dict)  # curve_name -> settings dict
    holeRegistered = pyqtSignal(object)  # hole window object
    holeUnregistered = pyqtSignal(object)  # hole window object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Sync settings (defaults)
        self.sync_enabled = True  # Global sync enabled/disabled
        self.sync_curve_selection = True  # Sync which curves are selected
        self.sync_display_settings = True  # Sync colors, styles, etc.
        self.sync_visibility = True  # Sync curve visibility
        self.shift_override_enabled = True  # Enable SHIFT key override
        self.shift_override_timeout_ms = 5000  # 5 seconds timeout
        self.auto_sync_new_holes = True  # Auto-sync new holes
        
        # Temporary override with SHIFT key
        self.shift_override_active = False
        
        # Registry of open holes
        self.open_holes: Dict[str, Any] = {}  # hole_id -> hole_window
        
        # Current synchronized state
        self.synced_curve_selection: List[str] = []
        self.synced_curve_settings: Dict[str, Dict] = {}
        
        # Settings file
        self.settings_dir = os.path.expanduser("~/.earthworm")
        self.settings_file = os.path.join(self.settings_dir, "cross_hole_sync.json")
        os.makedirs(self.settings_dir, exist_ok=True)
        
        # Load settings
        self.load_settings()
        
        # Install event filter for SHIFT key detection
        if QApplication.instance():
            QApplication.instance().installEventFilter(self)
    
    def eventFilter(self, obj, event):
        """Detect SHIFT key for temporary sync override."""
        if isinstance(event, QKeyEvent) and self.shift_override_enabled:
            # Check for SHIFT key press/release
            if event.key() == Qt.Key.Key_Shift:
                if event.type() == QKeyEvent.Type.KeyPress:
                    self.activate_shift_override()
                elif event.type() == QKeyEvent.Type.KeyRelease:
                    self.deactivate_shift_override()
        
        return super().eventFilter(obj, event)
    
    def activate_shift_override(self):
        """Activate temporary sync override with SHIFT key."""
        if not self.shift_override_active:
            self.shift_override_active = True
            print("DEBUG (CrossHoleSyncManager): SHIFT override activated - sync temporarily disabled")
    
    def deactivate_shift_override(self):
        """Deactivate temporary sync override."""
        if self.shift_override_active:
            self.shift_override_active = False
            print("DEBUG (CrossHoleSyncManager): SHIFT override deactivated - sync restored")
    
    def is_sync_active(self) -> bool:
        """Check if synchronization is currently active."""
        return self.sync_enabled and not (self.shift_override_enabled and self.shift_override_active)
    
    def register_hole(self, hole_window, hole_id: Optional[str] = None):
        """Register an open hole window."""
        if hole_id is None:
            hole_id = self._generate_hole_id(hole_window)
        
        if hole_id not in self.open_holes:
            self.open_holes[hole_id] = {
                'window': hole_window,
                'curves': [],
                'settings': {}
            }
            print(f"DEBUG (CrossHoleSyncManager): Registered hole: {hole_id}")
            self.holeRegistered.emit(hole_window)
            
            # Apply current sync state to new hole
            if self.is_sync_active():
                self._apply_sync_to_hole(hole_id)
    
    def unregister_hole(self, hole_id: str):
        """Unregister a hole window (when closed)."""
        if hole_id in self.open_holes:
            hole_window = self.open_holes[hole_id]['window']
            del self.open_holes[hole_id]
            print(f"DEBUG (CrossHoleSyncManager): Unregistered hole: {hole_id}")
            self.holeUnregistered.emit(hole_window)
    
    def update_hole_curves(self, hole_id: str, curves: List[str]):
        """Update curve list for a hole."""
        if hole_id in self.open_holes:
            self.open_holes[hole_id]['curves'] = curves.copy()
            
            # If sync is active and this is the active hole, sync to others
            if self.is_sync_active() and self.sync_curve_selection:
                self.sync_curve_selection_to_all(curves)
    
    def update_hole_settings(self, hole_id: str, curve_settings: Dict[str, Dict]):
        """Update curve settings for a hole."""
        if hole_id in self.open_holes:
            self.open_holes[hole_id]['settings'] = curve_settings.copy()
            
            # If sync is active and this is the active hole, sync to others
            if self.is_sync_active() and self.sync_display_settings:
                self.sync_curve_settings_to_all(curve_settings)
    
    def sync_curve_selection_to_all(self, curves: List[str]):
        """Sync curve selection to all open holes."""
        if not self.is_sync_active() or not self.sync_curve_selection:
            return
        
        self.synced_curve_selection = curves.copy()
        
        # Apply to all registered holes
        for hole_id in self.open_holes:
            self._apply_curve_selection_to_hole(hole_id, curves)
        
        # Emit signal
        self.curveSelectionSynced.emit(curves)
        print(f"DEBUG (CrossHoleSyncManager): Synced curve selection: {len(curves)} curves")
    
    def sync_curve_settings_to_all(self, curve_settings: Dict[str, Dict]):
        """Sync curve settings to all open holes."""
        if not self.is_sync_active() or not self.sync_display_settings:
            return
        
        self.synced_curve_settings = curve_settings.copy()
        
        # Apply to all registered holes
        for hole_id in self.open_holes:
            self._apply_curve_settings_to_hole(hole_id, curve_settings)
        
        # Emit signal
        self.curveSettingsSynced.emit(curve_settings)
        print(f"DEBUG (CrossHoleSyncManager): Synced curve settings: {len(curve_settings)} curves")
    
    def _apply_sync_to_hole(self, hole_id: str):
        """Apply current sync state to a hole."""
        if self.sync_curve_selection and self.synced_curve_selection:
            self._apply_curve_selection_to_hole(hole_id, self.synced_curve_selection)
        
        if self.sync_display_settings and self.synced_curve_settings:
            self._apply_curve_settings_to_hole(hole_id, self.synced_curve_settings)
    
    def _apply_curve_selection_to_hole(self, hole_id: str, curves: List[str]):
        """Apply curve selection to a specific hole."""
        if hole_id not in self.open_holes:
            return
        
        hole_data = self.open_holes[hole_id]
        hole_window = hole_data['window']
        
        # Try to call set_curve_selection method if it exists
        if hasattr(hole_window, 'set_curve_selection'):
            hole_window.set_curve_selection(curves)
        elif hasattr(hole_window, 'curvePlotter') and hasattr(hole_window.curvePlotter, 'set_curve_selection'):
            hole_window.curvePlotter.set_curve_selection(curves)
    
    def _apply_curve_settings_to_hole(self, hole_id: str, curve_settings: Dict[str, Dict]):
        """Apply curve settings to a specific hole."""
        if hole_id not in self.open_holes:
            return
        
        hole_data = self.open_holes[hole_id]
        hole_window = hole_data['window']
        
        # Try to call update_curve_settings method if it exists
        if hasattr(hole_window, 'update_curve_settings'):
            hole_window.update_curve_settings(curve_settings)
        elif hasattr(hole_window, 'curvePlotter') and hasattr(hole_window.curvePlotter, 'update_curve_settings'):
            hole_window.curvePlotter.update_curve_settings(curve_settings)
    
    def _generate_hole_id(self, hole_window) -> str:
        """Generate a unique ID for a hole window."""
        # Use file path if available, otherwise use object id
        if hasattr(hole_window, 'current_file_path') and hole_window.current_file_path:
            return f"hole_{os.path.basename(hole_window.current_file_path)}_{id(hole_window)}"
        else:
            return f"hole_{id(hole_window)}"
    
    def set_sync_enabled(self, enabled: bool):
        """Enable or disable synchronization."""
        if self.sync_enabled != enabled:
            self.sync_enabled = enabled
            self.syncEnabledChanged.emit(enabled)
            print(f"DEBUG (CrossHoleSyncManager): Sync enabled: {enabled}")
    
    def set_sync_curve_selection(self, enabled: bool):
        """Enable or disable curve selection synchronization."""
        self.sync_curve_selection = enabled
    
    def set_sync_display_settings(self, enabled: bool):
        """Enable or disable display settings synchronization."""
        self.sync_display_settings = enabled
    
    def set_sync_visibility(self, enabled: bool):
        """Enable or disable visibility synchronization."""
        self.sync_visibility = enabled
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current sync settings."""
        return {
            'sync_enabled': self.sync_enabled,
            'sync_curve_selection': self.sync_curve_selection,
            'sync_display_settings': self.sync_display_settings,
            'sync_visibility': self.sync_visibility,
            'shift_override_enabled': self.shift_override_enabled,
            'shift_override_timeout_ms': self.shift_override_timeout_ms,
            'auto_sync_new_holes': self.auto_sync_new_holes
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        """Apply sync settings."""
        self.sync_enabled = settings.get('sync_enabled', self.sync_enabled)
        self.sync_curve_selection = settings.get('sync_curve_selection', self.sync_curve_selection)
        self.sync_display_settings = settings.get('sync_display_settings', self.sync_display_settings)
        self.sync_visibility = settings.get('sync_visibility', self.sync_visibility)
        self.shift_override_enabled = settings.get('shift_override_enabled', self.shift_override_enabled)
        self.shift_override_timeout_ms = settings.get('shift_override_timeout_ms', self.shift_override_timeout_ms)
        self.auto_sync_new_holes = settings.get('auto_sync_new_holes', self.auto_sync_new_holes)
    
    def save_settings(self):
        """Save sync settings to file."""
        try:
            settings = self.get_settings()
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print(f"DEBUG (CrossHoleSyncManager): Settings saved to {self.settings_file}")
        except Exception as e:
            print(f"ERROR (CrossHoleSyncManager): Failed to save settings: {e}")
    
    def load_settings(self):
        """Load sync settings from file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                self.set_settings(settings)
                print(f"DEBUG (CrossHoleSyncManager): Settings loaded from {self.settings_file}")
            except Exception as e:
                print(f"ERROR (CrossHoleSyncManager): Failed to load settings: {e}")
    
    def get_open_hole_count(self) -> int:
        """Get number of open holes."""
        return len(self.open_holes)
    
    def get_open_hole_ids(self) -> List[str]:
        """Get IDs of all open holes."""
        return list(self.open_holes.keys())
    
    def get_hole_info(self, hole_id: str) -> Optional[Dict]:
        """Get information about a specific hole."""
        return self.open_holes.get(hole_id)
    
    def broadcast_to_all_holes(self, signal_name: str, *args, **kwargs):
        """Broadcast a signal to all open holes."""
        for hole_data in self.open_holes.values():
            hole_window = hole_data['window']
            if hasattr(hole_window, signal_name):
                signal = getattr(hole_window, signal_name)
                if callable(signal):
                    signal(*args, **kwargs)


# Factory function
def create_cross_hole_sync_manager(parent=None) -> CrossHoleSyncManager:
    """Create and initialize a cross-hole synchronization manager."""
    manager = CrossHoleSyncManager(parent)
    return manager


# Settings dialog integration
class CrossHoleSyncSettings:
    """Settings structure for cross-hole synchronization."""
    
    DEFAULT_SETTINGS = {
        'sync_enabled': True,
        'sync_curve_selection': True,
        'sync_display_settings': True,
        'sync_visibility': True,
        'shift_override_enabled': True,
        'shift_override_timeout_ms': 5000,
        'auto_sync_new_holes': True
    }
    
    @classmethod
    def get_settings_schema(cls) -> Dict[str, Any]:
        """Get settings schema for UI generation."""
        return {
            'sync_enabled': {
                'type': 'bool',
                'label': 'Enable Cross-hole Synchronization',
                'default': True,
                'tooltip': 'Enable synchronization of curve settings across all open holes'
            },
            'sync_curve_selection': {
                'type': 'bool',
                'label': 'Sync Curve Selection',
                'default': True,
                'tooltip': 'Synchronize which curves are selected across holes'
            },
            'sync_display_settings': {
                'type': 'bool',
                'label': 'Sync Display Settings',
                'default': True,
                'tooltip': 'Synchronize curve colors, line styles, and thickness'
            },
            'sync_visibility': {
                'type': 'bool',
                'label': 'Sync Curve Visibility',
                'default': True,
                'tooltip': 'Synchronize curve show/hide states'
            },
            'shift_override_enabled': {
                'type': 'bool',
                'label': 'Enable SHIFT Key Override',
                'default': True,
                'tooltip': 'Hold SHIFT key to temporarily disable synchronization'
            },
            'shift_override_timeout_ms': {
                'type': 'int',
                'label': 'Override Timeout (ms)',
                'default': 5000,
                'min': 1000,
                'max': 30000,
                'tooltip': 'How long SHIFT override remains active after key release'
            },
            'auto_sync_new_holes': {
                'type': 'bool',
                'label': 'Auto-sync New Holes',
                'default': True,
                'tooltip': 'Automatically apply sync settings to newly opened holes'
            }
        }