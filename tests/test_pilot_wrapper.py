#!/usr/bin/env python3
"""
test_pilot_wrapper.py - Crash-resistant test wrapper for Earthworm
Initializes QApplication with QT_QPA_PLATFORM=offscreen and runs a 5-second smoke test.
Catches sys.exit and reports errors instead of crashing.
"""

import sys
import os
import time
import traceback
import signal
from typing import Optional

# Set headless mode BEFORE importing Qt
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

class PilotWrapper:
    """Crash-resistant test wrapper for Earthworm components."""
    
    def __init__(self):
        self.app = None
        self.error_message = None
        self.crash_detected = False
        self.original_exit = sys.exit
        
    def handle_exit(self, code=0):
        """Intercept sys.exit calls to prevent test crashes."""
        self.error_message = f"sys.exit({code}) was called"
        self.crash_detected = True
        raise SystemExit(f"Intercepted sys.exit({code})")
    
    def signal_handler(self, signum, frame):
        """Handle segmentation faults and other signals."""
        signal_names = {
            signal.SIGSEGV: "SIGSEGV (Segmentation Fault)",
            signal.SIGABRT: "SIGABRT (Abort)",
            signal.SIGFPE: "SIGFPE (Floating Point Exception)",
            signal.SIGILL: "SIGILL (Illegal Instruction)",
            signal.SIGBUS: "SIGBUS (Bus Error)"
        }
        sig_name = signal_names.get(signum, f"Signal {signum}")
        self.error_message = f"{sig_name} detected during test"
        self.crash_detected = True
        print(f"\n⚠️  {self.error_message}")
        traceback.print_stack(frame)
    
    def initialize_qt(self):
        """Initialize QApplication with crash protection."""
        try:
            # Intercept sys.exit
            sys.exit = self.handle_exit
            
            # Install signal handlers
            signal.signal(signal.SIGSEGV, self.signal_handler)
            signal.signal(signal.SIGABRT, self.signal_handler)
            signal.signal(signal.SIGFPE, self.signal_handler)
            signal.signal(signal.SIGILL, self.signal_handler)
            
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import QTimer
            
            # Create or get QApplication
            self.app = QApplication.instance() or QApplication([])
            print("✅ QApplication initialized in headless mode")
            
            # Set application name for debugging
            self.app.setApplicationName("Earthworm Pilot Test")
            
            return True
            
        except Exception as e:
            self.error_message = f"Qt initialization failed: {e}"
            traceback.print_exc()
            return False
    
    def import_main_components(self):
        """Import Earthworm main components with error handling."""
        components = {}
        
        # Add project root to Python path
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        component_list = [
            ("MainWindow", "src.ui.main_window"),
            ("HoleEditorWindow", "src.ui.main_window"),  # Same module as MainWindow
            ("GeologicalAnalysisViewport", "src.ui.widgets.unified_viewport.geological_analysis_viewport"),
            ("UnifiedDepthScaleManager", "src.ui.widgets.unified_viewport.unified_depth_scale_manager"),
            ("ZoomStateManager", "src.ui.widgets.zoom_state_manager"),
        ]
        
        for name, module_path in component_list:
            try:
                module = __import__(module_path, fromlist=[name])
                component_class = getattr(module, name)
                components[name] = component_class
                print(f"✅ Imported {name}")
            except ImportError as e:
                print(f"⚠️  Failed to import {name}: {e}")
                components[name] = None
            except AttributeError as e:
                print(f"⚠️  {name} not found in {module_path}: {e}")
                components[name] = None
        
        return components
    
    def create_smoke_test_objects(self, components):
        """Create test objects for smoke testing."""
        test_objects = {}
        
        try:
            # Create GeologicalAnalysisViewport
            if components.get("GeologicalAnalysisViewport"):
                viewport = components["GeologicalAnalysisViewport"]()
                test_objects["viewport"] = viewport
                print("✅ Created GeologicalAnalysisViewport")
                
                # Note: set_geological_configuration doesn't exist, skipping configuration
                # We'll configure in simulate_loading_and_scrolling using actual methods
                
            # Create UnifiedDepthScaleManager
            if components.get("UnifiedDepthScaleManager"):
                depth_manager = components["UnifiedDepthScaleManager"]()
                test_objects["depth_manager"] = depth_manager
                print("✅ Created UnifiedDepthScaleManager")
                
            # Create ZoomStateManager
            if components.get("ZoomStateManager"):
                zoom_manager = components["ZoomStateManager"]()
                test_objects["zoom_manager"] = zoom_manager
                print("✅ Created ZoomStateManager")
                
        except Exception as e:
            self.error_message = f"Failed to create test objects: {e}"
            traceback.print_exc()
        
        return test_objects
    
    def simulate_loading_and_scrolling(self, test_objects):
        """Simulate file loading and scrolling operations."""
        try:
            print("\n🧪 Simulating geological workflow...")
            
            viewport = test_objects.get("viewport")
            depth_manager = test_objects.get("depth_manager")
            zoom_manager = test_objects.get("zoom_manager")
            
            # Step 1: Test basic viewport functionality
            print("  1. Testing basic viewport methods...")
            if viewport:
                # Test set_depth_range (actual method)
                viewport.set_depth_range(0, 500)
                print("    ✅ set_depth_range(0, 500) called")
                
                # Test set_curve_visibility if available
                if hasattr(viewport, 'set_curve_visibility'):
                    viewport.set_curve_visibility("gamma", True)
                    print("    ✅ set_curve_visibility(gamma, True) called")
                
                # Test set_current_depth if available
                if hasattr(viewport, 'set_current_depth'):
                    viewport.set_current_depth(250.0)
                    print("    ✅ set_current_depth(250.0) called")
            
            # Step 2: Simulate scrolling
            print("  2. Simulating scrolling operations...")
            if viewport:
                # Scroll through different depth ranges using actual method
                test_ranges = [(0, 100), (50, 150), (100, 200), (150, 250)]
                for i, (start, end) in enumerate(test_ranges):
                    print(f"    Scroll {i+1}: {start}-{end}m")
                    viewport.set_depth_range(start, end)
                    if hasattr(self.app, 'processEvents'):
                        self.app.processEvents()
                    time.sleep(0.1)  # Brief pause
            
            # Step 3: Test zoom manager if available
            print("  3. Testing zoom operations...")
            if zoom_manager and hasattr(zoom_manager, 'set_zoom_level'):
                zoom_levels = [1.0, 2.0, 0.5, 1.5]
                for level in zoom_levels:
                    print(f"    Zoom to {level}x")
                    zoom_manager.set_zoom_level(level)
                    if hasattr(self.app, 'processEvents'):
                        self.app.processEvents()
                    time.sleep(0.1)
            
            # Step 4: Check component states using available properties
            print("  4. Checking component states...")
            if viewport:
                # Use depth_range property if available
                if hasattr(viewport, 'depth_range'):
                    current_range = viewport.depth_range
                    print(f"    Current depth range: {current_range}")
                elif hasattr(viewport, 'get_current_depth_range'):
                    current_range = viewport.get_current_depth_range()
                    print(f"    Current depth range: {current_range}")
                else:
                    print("    ℹ️  No depth range accessor available")
            
            print("✅ Smoke test simulation completed")
            return True
            
        except Exception as e:
            self.error_message = f"Smoke test failed: {e}"
            traceback.print_exc()
            return False
    
    def run_smoke_test(self, duration_seconds=5):
        """Run the complete smoke test."""
        print("="*80)
        print("🚀 EARTHWORM PILOT WRAPPER - Smoke Test")
        print("="*80)
        
        start_time = time.time()
        
        try:
            # Step 1: Initialize Qt
            if not self.initialize_qt():
                print(f"❌ Failed to initialize Qt: {self.error_message}")
                return False
            
            # Step 2: Import components
            components = self.import_main_components()
            
            # Step 3: Create test objects
            test_objects = self.create_smoke_test_objects(components)
            
            if not test_objects:
                print("⚠️  No test objects created, continuing with basic validation")
            
            # Step 4: Run simulation
            print(f"\n⏱️  Running {duration_seconds}-second smoke test...")
            
            test_passed = self.simulate_loading_and_scrolling(test_objects)
            
            # Let Qt event loop run for remaining time
            elapsed = time.time() - start_time
            remaining = max(0, duration_seconds - elapsed)
            
            if remaining > 0:
                print(f"\n⏳ Running event loop for {remaining:.1f} seconds...")
                if self.app:
                    # Start timer to quit
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(int(remaining * 1000), self.app.quit)
                    self.app.exec()
            
            # Cleanup
            self.cleanup(test_objects)
            
            elapsed_total = time.time() - start_time
            
            if self.crash_detected:
                print(f"\n❌ TEST CRASHED: {self.error_message}")
                return False
            elif not test_passed:
                print(f"\n❌ TEST FAILED: {self.error_message}")
                return False
            else:
                print(f"\n✅ SMOKE TEST PASSED in {elapsed_total:.1f}s")
                print("="*80)
                return True
                
        except SystemExit as e:
            print(f"\n⚠️  SystemExit intercepted: {e}")
            return False
        except Exception as e:
            self.error_message = f"Unexpected error: {e}"
            traceback.print_exc()
            print(f"\n❌ UNEXPECTED ERROR: {self.error_message}")
            return False
    
    def cleanup(self, test_objects):
        """Clean up test objects."""
        print("\n🧹 Cleaning up test objects...")
        
        try:
            # Close any widgets
            for name, obj in test_objects.items():
                if hasattr(obj, 'close'):
                    obj.close()
                if hasattr(obj, 'deleteLater'):
                    obj.deleteLater()
            
            # Process events
            if self.app and hasattr(self.app, 'processEvents'):
                self.app.processEvents()
            
            print("✅ Cleanup complete")
            
        except Exception as e:
            print(f"⚠️  Cleanup error (non-fatal): {e}")


def main():
    """Main entry point for standalone execution."""
    wrapper = PilotWrapper()
    success = wrapper.run_smoke_test(duration_seconds=5)
    
    # Restore sys.exit
    sys.exit = wrapper.original_exit
    
    if success:
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print(f"FAILURE DETAILS: {wrapper.error_message}")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    main()