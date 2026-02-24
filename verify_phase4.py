#!/usr/bin/env python3
"""
Verification script for Phase 4 integration.
Tests UnifiedGraphicWindow with all components.
"""
import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from src.core.graphic_models import ExcelHoleDataProvider
from src.ui.graphic_window.unified_graphic_window import UnifiedGraphicWindow


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


def test_window_creation():
    """Test that UnifiedGraphicWindow can be created with mock data."""
    data_provider = create_mock_data_provider()
    
    # Create application instance
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Create window
    window = UnifiedGraphicWindow(data_provider)
    
    # Verify window properties
    assert window is not None
    assert window.data_provider == data_provider
    assert window.depth_state is not None
    assert window.depth_coords is not None
    
    # Verify components are created
    assert hasattr(window, 'preview_window')
    assert hasattr(window, 'strat_column')
    assert hasattr(window, 'las_curves')
    assert hasattr(window, 'lithology_table')
    assert hasattr(window, 'info_panel')
    
    print("✓ UnifiedGraphicWindow created successfully with all components")
    
    # Test state initialization
    viewport = window.depth_state.get_viewport_range()
    assert viewport is not None
    print(f"  - Initial viewport: {viewport.from_depth:.1f}m to {viewport.to_depth:.1f}m")
    
    return window


def test_component_integration():
    """Test that components are properly integrated."""
    data_provider = create_mock_data_provider()
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = UnifiedGraphicWindow(data_provider)
    
    # Test that all components share the same state manager
    assert window.strat_column.state == window.depth_state
    assert window.las_curves.state == window.depth_state
    assert window.lithology_table.state == window.depth_state
    assert window.preview_window.state == window.depth_state
    assert window.info_panel.state == window.depth_state
    
    print("✓ All components share the same DepthStateManager")
    
    # Test that visualization components share the same coordinate system
    assert window.strat_column.coords == window.depth_coords
    assert window.las_curves.coords == window.depth_coords
    assert window.preview_window.coords == window.depth_coords
    
    print("✓ Visualization components share the same DepthCoordinateSystem")
    
    return True


def main():
    """Run all Phase 4 verification tests."""
    print("Phase 4: Integration Testing")
    print("=" * 50)
    
    # Qt application needed
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        test_window_creation()
        test_component_integration()
        
        print("\n✅ All Phase 4 integration tests passed!")
        print("\n  Integration completed:")
        print("  - UnifiedGraphicWindow created (src/ui/graphic_window/unified_graphic_window.py)")
        print("  - All components wired together with shared state")
        print("  - Splitter-based layout implemented")
        print("  - PreviewWindow and InformationPanel added")
        print("\n  Architecture summary:")
        print("  - SINGLE DepthStateManager shared by all components")
        print("  - SINGLE DepthCoordinateSystem for pixel-perfect alignment")
        print("  - Signal/slot connections for automatic synchronization")
        print("\n  Next steps:")
        print("  1. Add menu bar and toolbar")
        print("  2. Implement synchronizers (scroll, selection, depth)")
        print("  3. Add styling (QSS)")
        print("  4. Integrate with Earthworm main application")
        
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