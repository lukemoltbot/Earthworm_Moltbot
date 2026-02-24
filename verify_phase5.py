#!/usr/bin/env python3
"""
Verification script for Phase 5 synchronizers.
Tests ScrollSynchronizer, SelectionSynchronizer, and DepthSynchronizer.
"""
import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from src.core.graphic_models import ExcelHoleDataProvider
from src.ui.graphic_window.synchronizers import (
    ScrollSynchronizer, SelectionSynchronizer, DepthSynchronizer
)
from src.ui.graphic_window.state import DepthRange


def create_mock_data_provider():
    """Create mock data for testing."""
    # Create mock lithology data
    lithology_data = pd.DataFrame({
        'from_depth': [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0],
        'to_depth': [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
        'code': ['SAND', 'COAL', 'SHALE', 'SAND', 'MUDSTONE', 
                'SILT', 'COAL', 'SHALE', 'SAND', 'MUDSTONE'],
        'description': ['Sandstone', 'Coal seam', 'Shale', 'Sandstone', 'Mudstone',
                       'Silt', 'Coal seam', 'Shale', 'Sandstone', 'Mudstone'],
        'sample_number': ['S1', 'C1', 'SH1', 'S2', 'M1', 'SI1', 'C2', 'SH2', 'S3', 'M2'],
        'comment': ['Fine', 'High quality', 'Gray', 'Medium', 'Soft',
                   'Fine', 'Medium quality', 'Dark gray', 'Coarse', 'Hard']
    })
    
    # Create mock LAS data
    las_data = pd.DataFrame({
        'depth': [float(i) for i in range(0, 101, 5)],  # 0, 5, 10, ..., 100
        'gamma': [40.0 + (i * 0.5) for i in range(21)],
        'density': [2.0 + (i * 0.02) for i in range(21)],
        'caliper': [8.0 + (i * 0.1) for i in range(21)],
        'resistivity': [10.0 + (i * 0.5) for i in range(21)]
    })
    
    return ExcelHoleDataProvider(lithology_data, las_data)


def test_scroll_synchronizer():
    """Test ScrollSynchronizer."""
    print("Testing ScrollSynchronizer...")
    
    scroll_sync = ScrollSynchronizer(min_depth=0.0, max_depth=100.0, viewport_height=10.0)
    
    # Test initial state
    assert scroll_sync.min_depth == 0.0
    assert scroll_sync.max_depth == 100.0
    assert scroll_sync.viewport_height == 10.0
    
    # Test setting viewport range
    scroll_sync.set_viewport_range(10.0, 20.0)
    assert scroll_sync.current_depth_range is not None
    assert abs(scroll_sync.current_depth_range.from_depth - 10.0) < 0.001
    assert abs(scroll_sync.current_depth_range.to_depth - 20.0) < 0.001
    
    # Test scroll up
    scroll_sync.scroll_up(5.0)
    assert abs(scroll_sync.current_depth_range.from_depth - 5.0) < 0.001
    assert abs(scroll_sync.current_depth_range.to_depth - 15.0) < 0.001
    
    # Test scroll down
    scroll_sync.scroll_down(10.0)
    assert abs(scroll_sync.current_depth_range.from_depth - 15.0) < 0.001
    assert abs(scroll_sync.current_depth_range.to_depth - 25.0) < 0.001
    
    # Test scroll position
    scroll_sync.set_scroll_position(0.5)
    assert 0.49 < scroll_sync.scroll_position < 0.51
    
    print("  ✓ ScrollSynchronizer tests passed")
    return True


def test_selection_synchronizer():
    """Test SelectionSynchronizer."""
    print("Testing SelectionSynchronizer...")
    
    selection_sync = SelectionSynchronizer()
    
    # Test single selection
    success, msg = selection_sync.set_selection(10.0, 20.0)
    assert success
    assert selection_sync.get_selection() is not None
    assert abs(selection_sync.get_selection().from_depth - 10.0) < 0.001
    assert abs(selection_sync.get_selection().to_depth - 20.0) < 0.001
    
    # Test selection validation (too thin)
    success, msg = selection_sync.set_selection(10.0, 10.001)  # 1mm thick
    assert not success
    assert "too thin" in msg
    
    # Test multiple selection mode
    selection_sync.set_selection_mode("multiple")
    selection_sync.set_selection(10.0, 20.0)
    selection_sync.set_selection(30.0, 40.0)
    assert len(selection_sync.get_all_selections()) == 2
    
    # Test clear selection
    selection_sync.clear_selection()
    assert selection_sync.get_selection() is None
    assert len(selection_sync.get_all_selections()) == 0
    
    print("  ✓ SelectionSynchronizer tests passed")
    return True


def test_depth_synchronizer():
    """Test DepthSynchronizer."""
    print("Testing DepthSynchronizer...")
    
    data_provider = create_mock_data_provider()
    depth_sync = DepthSynchronizer(data_provider)
    
    # Test setting cursor depth without snapping
    depth_sync.set_cursor_depth(15.0, snap=False)
    assert depth_sync.current_depth is not None
    assert abs(depth_sync.current_depth - 15.0) < 0.001
    
    # Test snapping (should snap to LAS point at 15.0)
    depth_sync.set_cursor_depth(14.9, snap=True)  # 14.9 is within 0.1 of 15.0
    # With tolerance 0.1, 14.9 should snap to 15.0 (LAS point)
    assert abs(depth_sync.current_depth - 15.0) < 0.001
    
    # Test depth markers
    depth_sync.add_depth_marker(25.0, "Test Marker")
    markers = depth_sync.get_depth_markers()
    assert len(markers) == 1
    assert abs(markers[0][0] - 25.0) < 0.001
    assert markers[0][1] == "Test Marker"
    
    # Test data at depth
    data = depth_sync.get_data_at_depth(15.0)
    assert data['depth'] == 15.0
    assert 'las_values' in data
    assert 'gamma' in data['las_values']
    
    print("  ✓ DepthSynchronizer tests passed")
    return True


def test_synchronizer_integration():
    """Test that synchronizers work together."""
    print("Testing synchronizer integration...")
    
    data_provider = create_mock_data_provider()
    
    # Create all synchronizers
    scroll_sync = ScrollSynchronizer(min_depth=0.0, max_depth=100.0, viewport_height=10.0)
    selection_sync = SelectionSynchronizer()
    depth_sync = DepthSynchronizer(data_provider)
    
    # Set up a scenario
    scroll_sync.set_viewport_range(10.0, 20.0)
    selection_sync.set_selection(12.0, 18.0)
    depth_sync.set_cursor_depth(15.0, snap=False)
    
    # Verify they work independently
    assert scroll_sync.current_depth_range is not None
    assert selection_sync.get_selection() is not None
    assert depth_sync.current_depth is not None
    
    # Test interaction: scroll to selection
    selection = selection_sync.get_selection()
    if selection:
        center_depth = (selection.from_depth + selection.to_depth) / 2
        scroll_sync.scroll_to_depth(center_depth)
        
        # Viewport should now be centered on selection
        viewport = scroll_sync.current_depth_range
        assert viewport is not None
        assert viewport.contains(center_depth)
    
    print("  ✓ Synchronizer integration tests passed")
    return True


def main():
    """Run all Phase 5 verification tests."""
    print("Phase 5: Synchronizer Testing")
    print("=" * 50)
    
    # Qt application needed for some tests
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        test_scroll_synchronizer()
        test_selection_synchronizer()
        test_depth_synchronizer()
        test_synchronizer_integration()
        
        print("\n✅ All Phase 5 synchronizer tests passed!")
        print("\n  Synchronizers implemented:")
        print("  - ScrollSynchronizer: Handles scroll calculations and smooth scrolling")
        print("  - SelectionSynchronizer: Manages selection logic and validation")
        print("  - DepthSynchronizer: Handles cursor snapping and depth markers")
        print("\n  Architecture summary:")
        print("  - Each synchronizer handles a specific synchronization concern")
        print("  - Can be used independently or integrated with DepthStateManager")
        print("  - Provides advanced features beyond basic state management")
        print("\n  Next steps (Phase 6):")
        print("  1. Unit tests for state manager and coordinate system")
        print("  2. Integration tests for components")
        print("  3. Alignment verification tests")
        print("  4. Performance benchmarking")
        
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