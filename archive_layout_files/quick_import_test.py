#!/usr/bin/env python3
"""Quick import test for layout system."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test all imports
try:
    from src.ui.layout_presets import OnePointLayoutPresets, LayoutManager
    print("✅ layout_presets imports OK")
    
    from src.ui.widgets.layout_toolbar import LayoutToolbar
    print("✅ layout_toolbar imports OK")
    
    from src.ui.dialogs.layout_manager_dialog import LayoutManagerDialog
    print("✅ layout_manager_dialog imports OK")
    
    from src.ui.dialogs.save_layout_dialog import SaveLayoutDialog
    print("✅ save_layout_dialog imports OK")
    
    # Test creating instances
    manager = LayoutManager()
    print("✅ LayoutManager instance created")
    
    presets = OnePointLayoutPresets.get_all_presets()
    print(f"✅ Got {len(presets)} presets")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)