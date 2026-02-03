"""
Session Manager for Earthworm Moltbot
Handles saving, loading, and managing named workspace sessions.
"""
import json
import os
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from PyQt6.QtCore import QByteArray

from .settings_manager import serialize_qbytearray, deserialize_qbytearray


class Session:
    """Represents a saved workspace session."""
    
    def __init__(self, name: str, description: str = "", workspace_state: Dict = None, 
                 timestamp: Optional[datetime] = None):
        self.name = name
        self.description = description
        self.workspace_state = workspace_state or {}
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "workspace_state": self.workspace_state,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create session from dictionary."""
        timestamp_str = data.get("timestamp")
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now()
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            workspace_state=data.get("workspace_state", {}),
            timestamp=timestamp
        )
    
    def __str__(self) -> str:
        return f"Session(name='{self.name}', description='{self.description}', timestamp={self.timestamp})"


class SessionManager:
    """Manages workspace sessions."""
    
    def __init__(self, settings_file_path: Optional[str] = None):
        from .settings_manager import DEFAULT_SETTINGS_FILE
        self.settings_file_path = settings_file_path or DEFAULT_SETTINGS_FILE
        self.sessions: Dict[str, Session] = {}  # name -> Session
        self._load_sessions()
    
    def _load_sessions(self):
        """Load sessions from settings file."""
        if not os.path.exists(self.settings_file_path):
            return
        
        try:
            with open(self.settings_file_path, 'r') as f:
                settings = json.load(f)
            
            sessions_data = settings.get("sessions", {})
            for session_name, session_data in sessions_data.items():
                try:
                    session = Session.from_dict(session_data)
                    self.sessions[session_name] = session
                except Exception as e:
                    print(f"Warning: Failed to load session '{session_name}': {e}")
        except Exception as e:
            print(f"Warning: Failed to load sessions from {self.settings_file_path}: {e}")
    
    def _save_sessions(self):
        """Save sessions to settings file."""
        try:
            # Load existing settings
            if os.path.exists(self.settings_file_path):
                with open(self.settings_file_path, 'r') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # Convert sessions to dict
            sessions_dict = {}
            for name, session in self.sessions.items():
                sessions_dict[name] = session.to_dict()
            
            # Update settings
            settings["sessions"] = sessions_dict
            
            # Save back to file
            os.makedirs(os.path.dirname(self.settings_file_path), exist_ok=True)
            with open(self.settings_file_path, 'w') as f:
                json.dump(settings, f, indent=4)
                
        except Exception as e:
            print(f"Error: Failed to save sessions to {self.settings_file_path}: {e}")
            raise
    
    def get_session(self, name: str) -> Optional[Session]:
        """Get a session by name."""
        return self.sessions.get(name)
    
    def get_all_sessions(self) -> List[Session]:
        """Get all sessions sorted by timestamp (newest first)."""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda s: s.timestamp, reverse=True)
        return sessions
    
    def save_session(self, name: str, description: str = "", workspace_state: Dict = None) -> Session:
        """
        Save a new session or update existing one.
        
        Args:
            name: Session name (must be unique)
            description: Optional description
            workspace_state: Workspace state dictionary
        
        Returns:
            The saved Session object
        """
        session = Session(name, description, workspace_state)
        self.sessions[name] = session
        self._save_sessions()
        return session
    
    def delete_session(self, name: str) -> bool:
        """
        Delete a session by name.
        
        Returns:
            True if session was deleted, False if not found
        """
        if name in self.sessions:
            del self.sessions[name]
            self._save_sessions()
            return True
        return False
    
    def rename_session(self, old_name: str, new_name: str) -> bool:
        """
        Rename a session.
        
        Returns:
            True if renamed successfully, False if old_name not found or new_name already exists
        """
        if old_name not in self.sessions:
            return False
        
        if new_name in self.sessions:
            return False
        
        session = self.sessions[old_name]
        del self.sessions[old_name]
        session.name = new_name
        self.sessions[new_name] = session
        self._save_sessions()
        return True
    
    def update_session_description(self, name: str, description: str) -> bool:
        """
        Update session description.
        
        Returns:
            True if updated, False if session not found
        """
        if name not in self.sessions:
            return False
        
        self.sessions[name].description = description
        self._save_sessions()
        return True
    
    def update_session_workspace(self, name: str, workspace_state: Dict) -> bool:
        """
        Update session workspace state.
        
        Returns:
            True if updated, False if session not found
        """
        if name not in self.sessions:
            return False
        
        self.sessions[name].workspace_state = workspace_state
        self.sessions[name].timestamp = datetime.now()  # Update timestamp
        self._save_sessions()
        return True
    
    def session_exists(self, name: str) -> bool:
        """Check if a session with given name exists."""
        return name in self.sessions
    
    def get_session_count(self) -> int:
        """Get total number of saved sessions."""
        return len(self.sessions)


# Helper functions for workspace state serialization

def serialize_main_window_state(main_window) -> Dict:
    """Serialize main window state for session storage."""
    from ..ui.main_window import MainWindow
    
    if not isinstance(main_window, MainWindow):
        raise TypeError("Expected MainWindow instance")
    
    state = {
        "type": "MainWindow",
        "geometry": {
            'x': main_window.geometry().x(),
            'y': main_window.geometry().y(),
            'width': main_window.geometry().width(),
            'height': main_window.geometry().height(),
            'maximized': main_window.isMaximized()
        },
        "window_state": serialize_qbytearray(main_window.saveState()),
        "dock_widgets": {},
        "toolbars": {},
        "mdi_area": {
            "view_mode": main_window.mdi_area.viewMode().name if hasattr(main_window, 'mdi_area') else "SubWindowView"
        }
    }
    
    # Save dock widget states
    if hasattr(main_window, 'settings_dock'):
        state["dock_widgets"]["settings_dock"] = {
            "visible": main_window.settings_dock.isVisible(),
            "floating": main_window.settings_dock.isFloating(),
            "area": main_window.settings_dock.dockWidgetArea(main_window.settings_dock).name if main_window.settings_dock.parent() else "floating"
        }
    
    if hasattr(main_window, 'holes_dock'):
        state["dock_widgets"]["holes_dock"] = {
            "visible": main_window.holes_dock.isVisible(),
            "floating": main_window.holes_dock.isFloating(),
            "area": main_window.holes_dock.dockWidgetArea(main_window.holes_dock).name if main_window.holes_dock.parent() else "floating"
        }
    
    # Save toolbar states
    if hasattr(main_window, 'toolbar'):
        state["toolbars"]["main_toolbar"] = {
            "visible": main_window.toolbar.isVisible(),
            "area": main_window.toolbar.area().name if hasattr(main_window.toolbar, 'area') else "TopToolBarArea"
        }
    
    return state


def deserialize_main_window_state(main_window, state: Dict):
    """Deserialize and apply main window state."""
    if not state:
        return
    
    # Restore geometry
    geometry = state.get("geometry", {})
    if geometry:
        x = geometry.get('x', 50)
        y = geometry.get('y', 50)
        width = geometry.get('width', 800)
        height = geometry.get('height', 600)
        maximized = geometry.get('maximized', False)
        
        main_window.setGeometry(x, y, width, height)
        if maximized:
            main_window.showMaximized()
    
    # Restore window state
    window_state = state.get("window_state")
    if window_state:
        qbytearray = deserialize_qbytearray(window_state)
        main_window.restoreState(qbytearray)
    
    # Restore MDI area view mode
    mdi_state = state.get("mdi_area", {})
    if mdi_state and hasattr(main_window, 'mdi_area'):
        view_mode = mdi_state.get("view_mode", "SubWindowView")
        # Note: View mode restoration would need to be implemented in MainWindow


def serialize_subwindow_state(subwindow) -> Dict:
    """Serialize MDI subwindow state for session storage."""
    from ..ui.main_window import HoleEditorWindow
    from ..ui.widgets.map_window import MapWindow
    from ..ui.widgets.cross_section_window import CrossSectionWindow
    
    state = {
        "geometry": {
            'x': subwindow.geometry().x(),
            'y': subwindow.geometry().y(),
            'width': subwindow.geometry().width(),
            'height': subwindow.geometry().height()
        },
        "title": subwindow.windowTitle()
    }
    
    # Window-specific state
    if isinstance(subwindow.widget(), HoleEditorWindow):
        hole_window = subwindow.widget()
        state["type"] = "HoleEditorWindow"
        state["file_path"] = getattr(hole_window, 'file_path', None)
        # Add more hole window specific state as needed
        
    elif isinstance(subwindow.widget(), MapWindow):
        map_window = subwindow.widget()
        state["type"] = "MapWindow"
        # Add map window specific state as needed
        
    elif isinstance(subwindow.widget(), CrossSectionWindow):
        cross_section_window = subwindow.widget()
        state["type"] = "CrossSectionWindow"
        # Add cross section window specific state as needed
    
    return state


def create_workspace_state(main_window) -> Dict:
    """
    Create a complete workspace state from the current application state.
    
    Args:
        main_window: The main application window
    
    Returns:
        Dictionary containing complete workspace state
    """
    state = {
        "main_window": serialize_main_window_state(main_window),
        "subwindows": [],
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"  # For future compatibility
    }
    
    # Serialize all MDI subwindows
    if hasattr(main_window, 'mdi_area'):
        for subwindow in main_window.mdi_area.subWindowList():
            subwindow_state = serialize_subwindow_state(subwindow)
            state["subwindows"].append(subwindow_state)
    
    return state


def restore_workspace_state(main_window, workspace_state: Dict) -> bool:
    """
    Restore workspace state to main window.
    
    Args:
        main_window: The main application window
        workspace_state: Workspace state dictionary
    
    Returns:
        True if restoration was successful, False otherwise
    """
    try:
        # Restore main window state
        main_window_state = workspace_state.get("main_window", {})
        deserialize_main_window_state(main_window, main_window_state)
        
        # Clear existing subwindows
        if hasattr(main_window, 'mdi_area'):
            for subwindow in main_window.mdi_area.subWindowList():
                subwindow.close()
        
        # Restore subwindows
        subwindows = workspace_state.get("subwindows", [])
        for subwindow_state in subwindows:
            window_type = subwindow_state.get("type")
            file_path = subwindow_state.get("file_path")
            
            if window_type == "HoleEditorWindow" and file_path:
                # Open the hole file
                try:
                    if os.path.exists(file_path):
                        # Use the main window's open_hole method
                        main_window.open_hole(file_path)
                    else:
                        print(f"Warning: File not found: {file_path}")
                except Exception as e:
                    print(f"Error opening hole file {file_path}: {e}")
            
            elif window_type == "MapWindow":
                # Open a map window
                try:
                    main_window.open_map_window()
                except Exception as e:
                    print(f"Error opening map window: {e}")
            
            elif window_type == "CrossSectionWindow":
                # Open a cross-section window
                try:
                    main_window.open_cross_section_window()
                except Exception as e:
                    print(f"Error opening cross-section window: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error restoring workspace state: {e}")
        return False