#!/usr/bin/env python3
"""
Test script for Earthworm UI redesign.
This script attempts to import and instantiate the MainWindow class
to verify the UI changes don't break initialization.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_main_window_initialization():
    """Test that MainWindow can be initialized without errors."""
    print("Testing Earthworm MainWindow initialization...")
    
    try:
        # Import required modules
        from PyQt6.QtWidgets import QApplication
        print("✓ PyQt6.QtWidgets imported successfully")
        
        # Initialize QApplication (required for any Qt widgets)
        # Use 'headless' flag if available, but simple instantiation should work
        # We'll create a minimal QApplication instance
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            print("✓ QApplication created")
        
        # Now import and instantiate MainWindow
        from src.ui.main_window import MainWindow
        print("✓ MainWindow imported successfully")
        
        window = MainWindow()
        print("✓ MainWindow instantiated successfully")
        
        # Check that settings button exists
        if hasattr(window, 'settingsButton'):
            print(f"✓ Settings button found: {window.settingsButton.text()}")
        else:
            print("✗ Settings button NOT found!")
            return False
        
        # Check that settings tab is not in tab widget
        if hasattr(window, 'tab_widget'):
            tab_count = window.tab_widget.count()
            tab_names = [window.tab_widget.tabText(i) for i in range(tab_count)]
            print(f"✓ Tab widget has {tab_count} tabs: {tab_names}")
            
            if "Settings" in tab_names:
                print("✗ 'Settings' tab still present in tab widget!")
                return False
            else:
                print("✓ 'Settings' tab not in tab widget (as expected)")
        else:
            print("✗ Tab widget not found!")
            return False
        
        # Test settings dialog method exists
        if hasattr(window, 'open_settings_dialog'):
            print("✓ open_settings_dialog method exists")
        else:
            print("✗ open_settings_dialog method missing!")
            return False
        
        print("\n✅ All UI redesign checks passed!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_main_window_initialization()
    sys.exit(0 if success else 1)