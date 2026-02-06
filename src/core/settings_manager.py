import json
import os
import base64
from PyQt6.QtCore import QByteArray
from .config import DEFAULT_LITHOLOGY_RULES, DEFAULT_SEPARATOR_THICKNESS, DRAW_SEPARATOR_LINES, CURVE_INVERSION_DEFAULTS, DEFAULT_CURVE_THICKNESS, DEFAULT_MERGE_THIN_UNITS, DEFAULT_MERGE_THRESHOLD, DEFAULT_SMART_INTERBEDDING, DEFAULT_SMART_INTERBEDDING_MAX_SEQUENCE_LENGTH, DEFAULT_SMART_INTERBEDDING_THICK_UNIT_THRESHOLD, DEFAULT_FALLBACK_CLASSIFICATION, DEFAULT_BIT_SIZE_MM, DEFAULT_SHOW_ANOMALY_HIGHLIGHTS, DEFAULT_CASING_DEPTH_ENABLED, DEFAULT_CASING_DEPTH_M, DISABLE_SVG_DEFAULT

USE_RESEARCHED_DEFAULTS_DEFAULT = True  # Default to maintaining backward compatibility

DEFAULT_SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".earthworm_settings.json")

def load_settings(file_path=None):
    """Loads application settings from a JSON file, or returns defaults if not found/invalid."""
    if file_path is None:
        file_path = DEFAULT_SETTINGS_FILE

    settings = {
        "lithology_rules": DEFAULT_LITHOLOGY_RULES,
        "separator_thickness": DEFAULT_SEPARATOR_THICKNESS,
        "draw_separator_lines": DRAW_SEPARATOR_LINES,
        "curve_inversion_settings": CURVE_INVERSION_DEFAULTS,
        "curve_thickness": DEFAULT_CURVE_THICKNESS,  # Add new setting
        "use_researched_defaults": USE_RESEARCHED_DEFAULTS_DEFAULT,
        "analysis_method": "standard",  # Default analysis method
        "merge_thin_units": DEFAULT_MERGE_THIN_UNITS,
        "merge_threshold": DEFAULT_MERGE_THRESHOLD,
        "smart_interbedding": DEFAULT_SMART_INTERBEDDING,
        "smart_interbedding_max_sequence_length": DEFAULT_SMART_INTERBEDDING_MAX_SEQUENCE_LENGTH,
        "smart_interbedding_thick_unit_threshold": DEFAULT_SMART_INTERBEDDING_THICK_UNIT_THRESHOLD,
        "fallback_classification": DEFAULT_FALLBACK_CLASSIFICATION,
        "bit_size_mm": DEFAULT_BIT_SIZE_MM,  # Default bit size in millimeters
        "show_anomaly_highlights": DEFAULT_SHOW_ANOMALY_HIGHLIGHTS,  # Show anomaly highlights
        "casing_depth_enabled": DEFAULT_CASING_DEPTH_ENABLED,  # Whether casing depth masking is enabled
        "casing_depth_m": DEFAULT_CASING_DEPTH_M,  # Casing depth in meters
        "disable_svg": DISABLE_SVG_DEFAULT,  # Whether to disable SVG patterns and use solid colors only
        "avg_executable_path": "",  # Path to AVG executable (empty by default)
        "workspace": None,  # Default to no workspace state
        "theme": "dark",  # Default theme (dark/light)
        "column_visibility": {}  # Mapping column internal name -> bool (True = visible)
    }
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                loaded_settings = json.load(f)
                # Update default settings with loaded ones, ensuring all keys are present
                # For nested dictionaries like curve_inversion_settings, update them individually
                if "curve_inversion_settings" in loaded_settings and isinstance(loaded_settings["curve_inversion_settings"], dict):
                    settings["curve_inversion_settings"].update(loaded_settings["curve_inversion_settings"])
                    del loaded_settings["curve_inversion_settings"] # Remove to avoid overwriting the updated dict
                settings.update(loaded_settings)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {file_path}. Using default settings.")
        except Exception as e:
            print(f"Warning: Error loading settings from {file_path}: {e}. Using default settings.")
    return settings

def save_settings(lithology_rules, separator_thickness, draw_separator_lines, curve_inversion_settings, curve_thickness, use_researched_defaults, analysis_method="standard", merge_thin_units=False, merge_threshold=0.05, smart_interbedding=False, smart_interbedding_max_sequence_length=10, smart_interbedding_thick_unit_threshold=0.5, fallback_classification=DEFAULT_FALLBACK_CLASSIFICATION, bit_size_mm=DEFAULT_BIT_SIZE_MM, show_anomaly_highlights=DEFAULT_SHOW_ANOMALY_HIGHLIGHTS, casing_depth_enabled=DEFAULT_CASING_DEPTH_ENABLED, casing_depth_m=DEFAULT_CASING_DEPTH_M, disable_svg=DISABLE_SVG_DEFAULT, avg_executable_path="", workspace_state=None, theme="dark", column_visibility=None, file_path=None):
    """Saves application settings to a JSON file."""
    if file_path is None:
        file_path = DEFAULT_SETTINGS_FILE

    settings = {
        "lithology_rules": lithology_rules,
        "separator_thickness": separator_thickness,
        "draw_separator_lines": draw_separator_lines,
        "curve_inversion_settings": curve_inversion_settings,
        "curve_thickness": curve_thickness,  # Save new setting
        "use_researched_defaults": use_researched_defaults,
        "analysis_method": analysis_method,  # Save analysis method
        "merge_thin_units": merge_thin_units,
        "merge_threshold": merge_threshold,
        "smart_interbedding": smart_interbedding,
        "smart_interbedding_max_sequence_length": smart_interbedding_max_sequence_length,
        "smart_interbedding_thick_unit_threshold": smart_interbedding_thick_unit_threshold,
        "fallback_classification": fallback_classification,
        "bit_size_mm": bit_size_mm,  # Save bit size in millimeters
        "show_anomaly_highlights": show_anomaly_highlights,  # Save anomaly highlights setting
        "casing_depth_enabled": casing_depth_enabled,  # Save casing depth masking enabled state
        "casing_depth_m": casing_depth_m,  # Save casing depth in meters
        "disable_svg": disable_svg,  # Save SVG disable setting
        "avg_executable_path": avg_executable_path,  # Save AVG executable path
        "workspace": workspace_state,  # Save workspace state
        "theme": theme,  # Save theme preference
        "column_visibility": column_visibility or {}  # Save column visibility mapping
    }
    try:
        # Ensure the directory exists before writing
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error: Could not save settings to {file_path}: {e}")


# Workspace serialization helper functions

def serialize_qbytearray(qbytearray):
    """Convert QByteArray to base64 string for JSON serialization."""
    if qbytearray is None:
        return None
    return base64.b64encode(qbytearray.data()).decode('utf-8')

def deserialize_qbytearray(base64_str):
    """Convert base64 string back to QByteArray."""
    if base64_str is None:
        return QByteArray()
    data = base64.b64decode(base64_str)
    return QByteArray(data)

def serialize_window_geometry(window):
    """Serialize window geometry to dict."""
    geometry = window.geometry()
    return {
        'x': geometry.x(),
        'y': geometry.y(),
        'width': geometry.width(),
        'height': geometry.height(),
        'maximized': window.isMaximized()
    }

def deserialize_window_geometry(geometry_dict, window):
    """Apply saved geometry to window."""
    if not geometry_dict:
        return
    
    x = geometry_dict.get('x', 50)
    y = geometry_dict.get('y', 50)
    width = geometry_dict.get('width', 800)
    height = geometry_dict.get('height', 600)
    maximized = geometry_dict.get('maximized', False)
    
    window.setGeometry(x, y, width, height)
    if maximized:
        window.showMaximized()
