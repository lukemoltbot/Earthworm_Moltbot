"""
Pixel alignment tests for System A architecture.

Verifies that depth-to-pixel mapping is pixel-perfect across components.
Target: <1px deviation between components at any depth.
"""

import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/Users/lukemoltbot/projects/Earthworm_Moltbot')

from src.ui.graphic_window.state.depth_coordinate_system import DepthCoordinateSystem
from src.ui.graphic_window.state.depth_state_manager import DepthStateManager


class TestPixelAlignment:
    """Test pixel-perfect depth mapping."""
    
    def test_depth_to_pixel_round_trip(self):
        """Verify depth → pixel → depth round-trip accuracy."""
        coords = DepthCoordinateSystem(
            canvas_height=500,
            canvas_width=1000,
            padding_top=20,
            padding_bottom=20,
            padding_left=50,
            padding_right=50
        )
        coords.set_depth_range(0, 1000)
        
        test_depths = [0, 50, 100, 200, 500, 750, 999]
        max_error = 0
        errors = []
        
        for depth in test_depths:
            # Convert depth to pixel
            pixel_pos = coords.depth_to_screen_y(depth)
            
            # Convert back to depth
            recovered_depth = coords.screen_y_to_depth(pixel_pos)
            
            # Calculate error
            error = abs(recovered_depth - depth)
            max_error = max(max_error, error)
            errors.append((depth, pixel_pos, recovered_depth, error))
            
            # Each depth should round-trip with <0.5 depth unit error
            assert error < 0.5, f"Round-trip error at depth {depth}: {error}"
        
        print(f"\n✅ Depth round-trip test passed")
        print(f"   Max error: {max_error:.6f} depth units")
        for depth, pixel, recovered, error in errors:
            print(f"   Depth {depth:6.1f} → Pixel {pixel:7.2f} → Depth {recovered:6.1f} (error: {error:.6f})")
    
    def test_depth_range_mapping(self):
        """Verify depth range maps correctly to screen."""
        coords = DepthCoordinateSystem(
            canvas_height=500,
            canvas_width=1000,
            padding_top=20,
            padding_bottom=20
        )
        coords.set_depth_range(100, 200)
        
        # Top of viewport should be at padding_top
        top_pixel = coords.depth_to_screen_y(100)
        assert top_pixel == 20, f"Top pixel should be 20, got {top_pixel}"
        
        # Bottom of viewport should be at canvas_height - padding_bottom
        bottom_pixel = coords.depth_to_screen_y(200)
        assert bottom_pixel == 480, f"Bottom pixel should be 480, got {bottom_pixel}"
        
        # Middle depth should map to middle pixel
        mid_pixel = coords.depth_to_screen_y(150)
        expected_mid = 20 + (480 - 20) / 2  # 250
        assert abs(mid_pixel - expected_mid) < 1, f"Mid pixel off by more than 1px"
        
        print(f"\n✅ Depth range mapping test passed")
        print(f"   Depth 100 → Pixel {top_pixel}")
        print(f"   Depth 150 → Pixel {mid_pixel}")
        print(f"   Depth 200 → Pixel {bottom_pixel}")
    
    def test_pixels_per_meter(self):
        """Verify pixels-per-meter calculation."""
        coords = DepthCoordinateSystem(
            canvas_height=500,
            canvas_width=1000,
            padding_top=20,
            padding_bottom=20
        )
        coords.set_depth_range(0, 1000)
        
        ppm = coords.get_pixels_per_meter()
        expected_ppm = (500 - 20 - 20) / 1000  # 0.46 px/m
        
        assert abs(ppm - expected_ppm) < 0.001, f"PPM calculation off"
        
        print(f"\n✅ Pixels-per-meter test passed")
        print(f"   Pixels per meter: {ppm:.3f}")
    
    def test_depth_thickness_to_pixel_height(self):
        """Verify depth thickness converts correctly to pixel height."""
        coords = DepthCoordinateSystem(
            canvas_height=500,
            canvas_width=1000,
            padding_top=20,
            padding_bottom=20
        )
        coords.set_depth_range(0, 1000)
        
        # 100m thickness should map to (100/1000) * 460 = 46 pixels
        height = coords.depth_thickness_to_pixel_height(100)
        expected_height = (100 / 1000) * 460
        
        assert abs(height - expected_height) < 0.01, f"Thickness conversion off"
        
        print(f"\n✅ Depth thickness test passed")
        print(f"   100m thickness → {height:.1f} pixels (expected {expected_height:.1f})")
    
    def test_usable_canvas_area(self):
        """Verify usable canvas area calculation."""
        coords = DepthCoordinateSystem(
            canvas_height=500,
            canvas_width=1000,
            padding_top=20,
            padding_bottom=20,
            padding_left=50,
            padding_right=50
        )
        
        left, top, right, bottom = coords.get_usable_canvas_area()
        
        assert left == 50
        assert top == 20
        assert right == 950
        assert bottom == 480
        
        print(f"\n✅ Usable canvas area test passed")
        print(f"   Area: ({left}, {top}, {right}, {bottom})")
    
    def test_multiple_coordinate_systems_consistency(self):
        """Verify multiple instances produce consistent results."""
        # Create two coordinate systems with same parameters
        coords1 = DepthCoordinateSystem(500, 1000, 20, 20, 50, 50)
        coords2 = DepthCoordinateSystem(500, 1000, 20, 20, 50, 50)
        
        coords1.set_depth_range(0, 1000)
        coords2.set_depth_range(0, 1000)
        
        # Test depths
        test_depths = [100, 250, 500, 750]
        
        for depth in test_depths:
            pixel1 = coords1.depth_to_screen_y(depth)
            pixel2 = coords2.depth_to_screen_y(depth)
            
            assert pixel1 == pixel2, f"Inconsistent pixel mapping for depth {depth}"
        
        print(f"\n✅ Multiple coordinate systems consistency test passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
