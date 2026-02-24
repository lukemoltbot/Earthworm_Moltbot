#!/usr/bin/env python3
"""
Verification script for Phase 1 foundation.
Tests DepthStateManager and DepthCoordinateSystem functionality.
"""
import sys
from PyQt6.QtWidgets import QApplication
from src.ui.graphic_window.state.depth_state_manager import DepthStateManager, DepthRange
from src.ui.graphic_window.state.depth_coordinate_system import DepthCoordinateSystem

def test_depth_range():
    """Test DepthRange dataclass."""
    dr = DepthRange(0.0, 100.0)
    assert dr.range_size == 100.0
    assert dr.contains(50.0) == True
    assert dr.contains(150.0) == False
    print("✓ DepthRange tests passed")

def test_depth_state_manager():
    """Test DepthStateManager basic functionality."""
    manager = DepthStateManager(0.0, 200.0)
    
    # Initial viewport range
    viewport = manager.get_viewport_range()
    assert viewport.from_depth == 0.0
    assert viewport.to_depth == 100.0  # default initial range (window_size / 2)
    
    # Set viewport range
    manager.set_viewport_range(10.0, 50.0)
    viewport = manager.get_viewport_range()
    assert viewport.from_depth == 10.0
    assert viewport.to_depth == 50.0
    
    # Scroll viewport
    manager.scroll_viewport(20.0)
    viewport = manager.get_viewport_range()
    assert viewport.from_depth == 30.0
    assert viewport.to_depth == 70.0
    
    # Cursor depth
    manager.set_cursor_depth(40.0)
    assert manager.get_cursor_depth() == 40.0
    
    # Selection range
    manager.set_selection_range(35.0, 45.0)
    selection = manager.get_selection_range()
    assert selection is not None
    assert selection.from_depth == 35.0
    assert selection.to_depth == 45.0
    
    manager.clear_selection()
    assert manager.get_selection_range() is None
    
    print("✓ DepthStateManager tests passed")

def test_depth_coordinate_system():
    """Test DepthCoordinateSystem transformations."""
    coords = DepthCoordinateSystem(canvas_height=800, canvas_width=1200)
    coords.set_depth_range(0.0, 100.0)
    
    # Test depth to screen Y
    y_top = coords.depth_to_screen_y(0.0)
    y_bottom = coords.depth_to_screen_y(100.0)
    # With default padding top=20, bottom=20, usable height = 800-40 = 760
    # y_top should be 20, y_bottom should be 780
    assert abs(y_top - 20.0) < 0.001
    assert abs(y_bottom - 780.0) < 0.001
    
    # Test middle
    y_mid = coords.depth_to_screen_y(50.0)
    assert abs(y_mid - 400.0) < 0.001  # 20 + 760/2 = 400
    
    # Test inverse screen Y to depth
    depth = coords.screen_y_to_depth(400.0)
    assert abs(depth - 50.0) < 0.001
    
    # Test thickness to pixel height
    pixel_height = coords.depth_thickness_to_pixel_height(10.0)  # 10 meters
    # 10/100 * 760 = 76 pixels
    assert abs(pixel_height - 76.0) < 0.001
    
    # Test pixels per meter
    ppm = coords.get_pixels_per_meter()
    assert abs(ppm - 7.6) < 0.001  # 760/100 = 7.6
    
    # Test usable canvas area
    left, top, right, bottom = coords.get_usable_canvas_area()
    assert left == 50.0
    assert top == 20.0
    assert right == 1150.0  # 1200 - 50
    assert bottom == 780.0
    
    print("✓ DepthCoordinateSystem tests passed")

def main():
    """Run all verification tests."""
    # Qt application needed for signals
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        test_depth_range()
        test_depth_state_manager()
        test_depth_coordinate_system()
        print("\n✅ All Phase 1 foundation tests passed!")
        return 0
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())