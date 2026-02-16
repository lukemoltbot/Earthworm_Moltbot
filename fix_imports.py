#!/usr/bin/env python3
"""
Fix Earthworm import issues by checking and copying missing files from archive.
"""

import os
import shutil
import sys

def find_missing_imports():
    """Find all missing imports by trying to import MainWindow."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'src'))
    
    missing_files = []
    
    # Try to import MainWindow and catch import errors
    try:
        from src.ui.main_window import MainWindow
        print("✅ All imports successful!")
        return []
    except ModuleNotFoundError as e:
        error_msg = str(e)
        # Extract module name from error message
        # Format: "No module named 'src.ui.layout_presets'"
        if "No module named '" in error_msg:
            module_name = error_msg.split("'")[1]
            missing_files.append(module_name)
        print(f"❌ Missing module: {error_msg}")
    
    return missing_files

def check_archive_for_files(missing_modules):
    """Check if missing files exist in archive."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    archive_dir = os.path.join(project_root, 'archive_layout_files')
    
    fixes = []
    
    for module in missing_modules:
        # Convert module path to file path
        # src.ui.layout_presets -> layout_presets.py
        module_parts = module.split('.')
        if len(module_parts) >= 3:
            # Get the filename (last part)
            filename = module_parts[-1] + '.py'
            
            # Check archive
            archive_file = os.path.join(archive_dir, filename)
            if os.path.exists(archive_file):
                # Determine destination
                if module_parts[0] == 'src' and module_parts[1] == 'ui':
                    dest_dir = os.path.join(project_root, 'src', 'ui')
                    dest_file = os.path.join(dest_dir, filename)
                    fixes.append((archive_file, dest_file, filename))
                elif module_parts[0] == 'src':
                    dest_dir = os.path.join(project_root, 'src')
                    dest_file = os.path.join(dest_dir, filename)
                    fixes.append((archive_file, dest_file, filename))
            else:
                print(f"⚠️  File not found in archive: {filename}")
    
    return fixes

def apply_fixes(fixes):
    """Apply the fixes by copying files."""
    for src, dst, filename in fixes:
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # Copy file
        shutil.copy2(src, dst)
        print(f"✅ Copied: {filename} to {os.path.dirname(dst)}/")

def main():
    print("🔧 Fixing Earthworm Import Issues")
    print("=" * 60)
    
    # Step 1: Find missing imports
    print("\n1️⃣  Finding missing imports...")
    missing_modules = find_missing_imports()
    
    if not missing_modules:
        print("✅ No missing imports found!")
        return
    
    print(f"   Found {len(missing_modules)} missing module(s)")
    for module in missing_modules:
        print(f"   • {module}")
    
    # Step 2: Check archive for missing files
    print("\n2️⃣  Checking archive for missing files...")
    fixes = check_archive_for_files(missing_modules)
    
    if not fixes:
        print("❌ No fixes found in archive")
        return
    
    print(f"   Found {len(fixes)} file(s) in archive")
    
    # Step 3: Apply fixes
    print("\n3️⃣  Applying fixes...")
    apply_fixes(fixes)
    
    # Step 4: Verify fixes
    print("\n4️⃣  Verifying fixes...")
    try:
        from src.ui.main_window import MainWindow
        print("✅ All imports successful after fixes!")
        print(f"   MainWindow class: {MainWindow}")
    except ImportError as e:
        print(f"❌ Still missing imports: {e}")
        # Recursively fix remaining issues
        remaining_missing = find_missing_imports()
        if remaining_missing:
            print("   Trying to fix remaining issues...")
            fixes = check_archive_for_files(remaining_missing)
            if fixes:
                apply_fixes(fixes)
    
    print("\n" + "=" * 60)
    print("IMPORT FIX COMPLETE")
    print("=" * 60)
    
    # Step 5: Create a test
    print("\n5️⃣  Creating test to verify imports...")
    test_code = '''#!/usr/bin/env python3
"""
Test Earthworm imports after fixes.
"""
import sys
import os

# Add project paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

try:
    from src.ui.main_window import MainWindow
    print("✅ Earthworm imports successful!")
    print(f"   MainWindow: {MainWindow}")
    
    # Test creating instance
    from PyQt6.QtWidgets import QApplication
    import sys as sys_module
    
    app = QApplication([])
    window = MainWindow()
    print("✅ MainWindow instance created successfully!")
    print(f"   Window title: {window.windowTitle()}")
    
    window.close()
    print("✅ Test completed successfully!")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
'''
    
    test_file = os.path.join(project_root, 'test_imports_fixed.py')
    with open(test_file, 'w') as f:
        f.write(test_code)
    
    print(f"✅ Test script created: {test_file}")
    print("\n💡 To test:")
    print(f"   cd Earthworm_Moltbot && .venv/bin/python test_imports_fixed.py")

if __name__ == "__main__":
    main()