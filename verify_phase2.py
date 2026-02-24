#!/usr/bin/env python3
"""
Verification script for Phase 2 data models.
Tests LithologyInterval, LASPoint, HoleDataProvider, and ExcelHoleDataProvider.
"""
import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication
from src.core.graphic_models import (
    LithologyCode, LithologyInterval, LASPoint, 
    HoleDataProvider, ExcelHoleDataProvider
)


def test_lithology_interval():
    """Test LithologyInterval data model."""
    interval = LithologyInterval(
        from_depth=10.0,
        to_depth=20.0,
        code="COAL",
        description="Coal seam",
        color=(0, 0, 0),
        sample_number="C1",
        comment="High quality"
    )
    
    assert interval.from_depth == 10.0
    assert interval.to_depth == 20.0
    assert interval.code == "COAL"
    assert interval.description == "Coal seam"
    assert interval.thickness == 10.0  # Calculated in __post_init__
    assert interval.contains_depth(15.0) == True
    assert interval.contains_depth(5.0) == False
    assert interval.get_depth_ratio(15.0) == 0.5
    
    print("✓ LithologyInterval tests passed")


def test_las_point():
    """Test LASPoint data model."""
    point = LASPoint(
        depth=50.0,
        curves={'gamma': 120.5, 'density': 2.65, 'resistivity': 15.0}
    )
    
    assert point.depth == 50.0
    assert point.get_curve_value('gamma') == 120.5
    assert point.get_curve_value('nonexistent', default=0.0) == 0.0
    assert point.has_curve('density') == True
    assert point.has_curve('porosity') == False
    
    print("✓ LASPoint tests passed")


def test_hole_data_provider_abstract():
    """Test that HoleDataProvider is abstract."""
    try:
        provider = HoleDataProvider()  # Should raise TypeError
        print("❌ HoleDataProvider should be abstract")
        return False
    except TypeError:
        print("✓ HoleDataProvider is abstract (as expected)")
        return True


def test_excel_hole_data_provider():
    """Test ExcelHoleDataProvider with mock data."""
    # Create mock DataFrames
    lithology_data = pd.DataFrame({
        'from_depth': [0.0, 10.0, 20.0],
        'to_depth': [10.0, 20.0, 30.0],
        'code': ['SAND', 'COAL', 'SHALE'],
        'description': ['Sandstone', 'Coal seam', 'Shale'],
        'sample_number': ['S1', 'C1', 'SH1'],
        'comment': ['Fine', 'High quality', 'Gray']
    })
    
    las_data = pd.DataFrame({
        'depth': [0.0, 5.0, 10.0, 15.0, 20.0],
        'gamma': [40.0, 45.0, 120.0, 110.0, 50.0],
        'density': [2.2, 2.3, 1.8, 1.9, 2.1],
        'resistivity': [10.0, 12.0, 5.0, 6.0, 15.0]
    })
    
    provider = ExcelHoleDataProvider(lithology_data, las_data)
    
    # Test lithology intervals
    intervals = provider.get_lithology_intervals()
    assert len(intervals) == 3
    assert intervals[0].code == "SAND"
    assert intervals[1].code == "COAL"
    assert intervals[2].code == "SHALE"
    
    # Test lithology for depth
    lith_at_15 = provider.get_lithology_for_depth(15.0)
    assert lith_at_15 is not None
    assert lith_at_15.code == "COAL"  # 10-20 range
    
    # Test LAS points
    points = provider.get_las_points(['gamma', 'density'])
    assert len(points) == 5
    assert points[0].depth == 0.0
    assert points[2].get_curve_value('gamma') == 120.0
    
    # Test depth range
    depth_range = provider.get_depth_range()
    assert depth_range[0] == 0.0
    assert depth_range[1] == 30.0
    
    # Test available curves
    curves = provider.get_available_curves()
    assert 'gamma' in curves
    assert 'density' in curves
    assert 'resistivity' in curves
    assert 'depth' not in curves
    
    # Test depth bounds
    bounds = provider.get_depth_bounds()
    assert bounds['min'] == 0.0
    assert bounds['max'] == 30.0
    assert bounds['range'] == 30.0
    
    print("✓ ExcelHoleDataProvider tests passed")
    return True


def test_lithology_code_enum():
    """Test LithologyCode enumeration."""
    assert LithologyCode.SAND.value == "SAND"
    assert LithologyCode.COAL.value == "COAL"
    assert LithologyCode.SHALE.value == "SHALE"
    print("✓ LithologyCode enum tests passed")


def main():
    """Run all Phase 2 verification tests."""
    # Qt application needed for any Qt dependencies
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    try:
        test_lithology_code_enum()
        test_lithology_interval()
        test_las_point()
        test_hole_data_provider_abstract()
        test_excel_hole_data_provider()
        print("\n✅ All Phase 2 data model tests passed!")
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