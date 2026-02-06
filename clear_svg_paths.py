#!/usr/bin/env python3
"""
Script to clear SVG paths from Earthworm settings file.
Sets all svg_path values to null in the lithology rules.
"""
import json
import os

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".earthworm_settings.json")

def clear_svg_paths():
    """Clear all svg_path entries from the settings file."""
    if not os.path.exists(SETTINGS_FILE):
        print(f"Settings file not found: {SETTINGS_FILE}")
        return False
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        
        if 'lithology_rules' not in settings:
            print("No lithology rules found in settings file.")
            return False
        
        cleared_count = 0
        for rule in settings['lithology_rules']:
            if 'svg_path' in rule:
                rule['svg_path'] = None
                cleared_count += 1
        
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        
        print(f"Cleared {cleared_count} svg_path entries from settings file.")
        return True
        
    except Exception as e:
        print(f"Error processing settings file: {e}")
        return False

if __name__ == "__main__":
    if clear_svg_paths():
        print("SVG paths cleared successfully.")
    else:
        print("Failed to clear SVG paths.")