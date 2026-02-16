#!/usr/bin/env python3
"""
Comprehensive fix for all Earthworm import issues.
"""

import os
import shutil
import sys

def get_missing_import():
    """Try to import MainWindow and return the missing module name."""
    project_root = os.getcwd()
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'src'))
    
    try:
        from src.ui.main_window import MainWindow
        return None  # No missing imports
    except ModuleNotFoundError as e:
        error_msg = str(e)
        if "No module named '" in error_msg:
            return error_msg.split("'")[1]
        return error_msg

def fix_missing_import(missing_module):
    """Fix a single missing import."""
    project_root = os.getcwd()
    archive_dir = os.path.join(project_root, 'archive_layout_files')
    
    # Convert module path to filename
    # src.ui.dialogs.layout_manager_dialog -> layout_manager_dialog.py
    module_parts = missing_module.split('.')
    if len(module_parts) < 3:
        print(f"⚠️  Cannot parse module: {missing_module}")
        return False
    
    filename = module_parts[-1] + '.py'
    
    # Check archive
    archive_file = os.path.join(archive_dir, filename)
    if not os.path.exists(archive_file):
        print(f"⚠️  File not found in archive: {filename}")
        return False
    
    # Determine destination
    if module_parts[0] == 'src' and module_parts[1] == 'ui':
        if module_parts[2] == 'dialogs':
            dest_dir = os.path.join(project_root, 'src', 'ui', 'dialogs')
        elif module_parts[2] == 'widgets':
            dest_dir = os.path.join(project_root, 'src', 'ui', 'widgets')
        else:
            dest_dir = os.path.join(project_root, 'src', 'ui')
    else:
        print(f"⚠️  Unknown module structure: {missing_module}")
        return False
    
    # Create destination directory
    os.makedirs(dest_dir, exist_ok=True)
    
    # Copy file
    dest_file = os.path.join(dest_dir, filename)
    shutil.copy2(archive_file, dest_file)
    print(f"✅ Copied: {filename} to {dest_dir}/")
    
    return True

def main():
    print("🔧 Comprehensive Earthworm Import Fix")
    print("=" * 60)
    
    fixes_applied = 0
    max_fixes = 20  # Safety limit
    
    while fixes_applied < max_fixes:
        print(f"\n🔍 Check {fixes_applied + 1}:")
        missing_module = get_missing_import()
        
        if missing_module is None:
            print("✅ All imports fixed!")
            break
        
        print(f"   Missing: {missing_module}")
        
        if fix_missing_import(missing_module):
            fixes_applied += 1
        else:
            print("❌ Could not fix this import")
            break
    
    print(f"\n📊 Applied {fixes_applied} fix(es)")
    
    # Final test
    print("\n🧪 Final test:")
    missing_module = get_missing_import()
    if missing_module is None:
        print("✅ SUCCESS: Earthworm imports fully fixed!")
        
        # Try to create MainWindow instance
        try:
            from PyQt6.QtWidgets import QApplication
            from src.ui.main_window import MainWindow
            
            app = QApplication([])
            window = MainWindow()
            print(f"✅ MainWindow instance created: {window.windowTitle()}")
            window.close()
            print("✅ Test completed successfully!")
            
        except Exception as e:
            print(f"⚠️  Instance creation issue: {e}")
    else:
        print(f"❌ Still missing: {missing_module}")
        print("   Manual intervention required")
    
    print("\n" + "=" * 60)
    print("IMPORT FIX PROCESS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()