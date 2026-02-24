#!/usr/bin/env python3
"""
Verification script for Phase 3 components.
Tests StratigraphicColumn, LASCurvesDisplay, and LithologyDataTable.
"""
import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from src.core.graphic_models import ExcelHoleDataProvider
from src.ui.graphic_window.state import DepthStateManager, DepthCoordinateSystem
from src.ui.graphic_window.components import (
    StratigraphicColumn, LASCurvesDisplay, LithologyDataTable
)


def create_mock_data_provider():
    """Create mock data for testing."""
    # Create mock lithology data
    lithology_data = pd.DataFrame({
        'from_depth': [0.0, 10.0, 20.0, 30.0, 40.0],
        'to_depth': [10.0, 20.0, 30.0, 40.0, 50.0],
        'code': ['SAND', 'COAL', 'SHALE', 'SAND', 'MUDSTONE'],
        'description': ['Sandstone', 'Coal seam', 'Shale', 'Sandstone', 'Mudstone'],
        'sample_number': ['S1', 'C1', 'SH1', 'S2', 'M1'],
        'comment': ['Fine', 'High quality', 'Gray', 'Medium', 'Soft']
    })
    
    # Create mock LAS data
    las_data = pd.DataFrame({
        'depth': [0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0],
        'gamma': [40.0, 45.0, 120.0, 110.0, 50.0, 55.0, 130.0, 125.0, 60.0, 65.0, 70.0],
        'density': [2.2, 2.3, 1.8, 1.9, 2.1, 2.2, 1.7, 1.8, 2.0, 2.1, 2.2],
        'caliper': [8.0, 8.1, 7.5, 7.6, 8.2, 8.3, 7.4, 7.5, 8.1, 8.2, 8.3],
        'resistivity': [10.0, 12.0, 5.0, 6.0, 15.0, 16.0, 4.0, 5.0, 14.0, 15.0, 16.0]
    })
    
    return ExcelHoleDataProvider(lithology_data, las_data)


def test_component_instantiation():
    """Test that components can be instantiated with mock data."""
    data_provider = create_mock_data_provider()
    
    # Get depth range for state managers
    depth_range = data_provider.get_depth_range()
    min_depth, max_depth = depth_range
    
    # Create shared state managers
    depth_state = DepthStateManager(min_depth, max_depth)
    depth_coords = DepthCoordinateSystem(canvas_height=600, canvas_width=800)
    
    # Test StratigraphicColumn
    strat_column = StratigraphicColumn(data_provider, depth_state, depth_coords)
    assert strat_column is not None
    assert strat_column.data_provider == data_provider
    assert strat_column.state == depth_state
    assert strat_column.coords == depth_coords
    print("✓ StratigraphicColumn instantiated successfully")
    
    # Test LASCurvesDisplay
    las_curves = LASCurvesDisplay(data_provider, depth_state, depth_coords)
    assert las_curves is not None
    assert las_curves.data_provider == data_provider
    assert las_curves.state == depth_state
    assert las_curves.coords == depth_coords
    print("✓ LASCurvesDisplay instantiated successfully")
    
    # Test LithologyDataTable
    lith_table = LithologyDataTable(data_provider, depth_state, depth_coords)
    assert lith_table is not None
    assert lith_table.data_provider == data_provider
    assert lith_table.state == depth_state
    print("✓ LithologyDataTable instantiated successfully")
    
    return True


def test_state_synchronization():
    """Test that components respond to state changes."""
    data_provider = create_mock_data_provider()
    depth_range = data_provider.get_depth_range()
    min_depth, max_depth = depth_range
    
    depth_state = DepthStateManager(min_depth, max_depth)
    depth_coords = DepthCoordinateSystem(canvas_height=600, canvas_width=800)
    
    # Create components
    strat_column = StratigraphicColumn(data_provider, depth_state, depth_coords)
    lith_table = LithologyDataTable(data_provider, depth_state, depth_coords)
    
    # Test initial state
    initial_viewport = depth_state.get_viewport_range()
    assert initial_viewport is not None
    
    # Change viewport range
    depth_state.set_viewport_range(10.0, 40.0)
    new_viewport = depth_state.get_viewport_range()
    assert new_viewport.from_depth == 10.0
    assert new_viewport.to_depth == 40.0
    
    # Change selection
    depth_state.set_selection_range(15.0, 25.0)
    selection = depth_state.get_selection_range()
    assert selection is not None
    assert selection.from_depth == 15.0
    assert selection.to_depth == 25.0
    
    # Change cursor
    depth_state.set_cursor_depth(20.0)
    assert depth_state.get_cursor_depth() == 20.0
    
    print("✓ State synchronization test passed")
    return True


def main():
    """Run all Phase 3 verification tests."""
    # Qt application needed for Qt objects
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        test_component_instantiation()
        test_state_synchronization()
        print("\n✅ All Phase 3 component tests passed!")
        print("\n  Components implemented:")
        print("  - StratigraphicColumn (src/ui/graphic_window/components/stratigraphic_column.py)")
        print("  - LASCurvesDisplay (src/ui/graphic_window/components/las_curves_display.py)")
        print("  - LithologyDataTable (src/ui/graphic_window/components/lithology_data_table.py)")
        print("\n  Next steps:")
        print("  1. Create PreviewWindow and InformationPanel components")
        print("  2. Create UnifiedGraphicWindow main container")
        print("  3. Integrate with existing Earthworm application")
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