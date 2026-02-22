"""
Test pixel alignment validation for unified viewport.

Tests that depth-to-pixel mapping maintains ≤1 pixel drift.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set QT_QPA_PLATFORM to offscreen for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from src.ui.widgets.unified_viewport.pixel_depth_mapper import PixelDepthMapper, PixelMappingConfig


class TestPixelAlignment:
    """Test pixel alignment validation."""
    
    def test_basic_pixel_mapping(self):
        """Test basic depth to pixel mapping."""
        config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=100.0,
            viewport_width=800,
            viewport_height=600,
            vertical_padding=2,
            pixel_tolerance=1
        )
        
        mapper = PixelDepthMapper(config)
        
        # Test depth → pixel mapping
        assert mapper.depth_to_pixel(0.0) == 2  # Top with padding
        
        # Bottom pixel calculation: viewport_height - vertical_padding - 1
        # 600 - 2 - 1 = 597
        bottom_pixel = mapper.depth_to_pixel(100.0)
        assert bottom_pixel == 597, f"Expected bottom pixel 597, got {bottom_pixel}"
        
        # Test pixel → depth mapping
        assert mapper.pixel_to_depth(2) == pytest.approx(0.0, abs=0.01)
        
        # Bottom pixel to depth may have small floating point error
        bottom_depth = mapper.pixel_to_depth(597)
        assert bottom_depth == pytest.approx(100.0, abs=0.2), \
            f"Bottom depth {bottom_depth} not close to 100.0"
    
    def test_pixel_alignment_validation(self):
        """Test pixel alignment validation passes with ≤1 pixel drift."""
        config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=100.0,
            viewport_width=800,
            viewport_height=600,
            vertical_padding=2,
            pixel_tolerance=1
        )
        
        mapper = PixelDepthMapper(config)
        
        # Run validation
        validation = mapper.validate_pixel_alignment()
        
        # Check validation passed
        assert validation['validation_passed'] == True, \
            f"Pixel alignment validation failed: {validation}"
        
        # Check max pixel drift ≤ tolerance
        assert validation['max_pixel_drift'] <= config.pixel_tolerance, \
            f"Max pixel drift {validation['max_pixel_drift']}px exceeds tolerance {config.pixel_tolerance}px"
        
        # Check no pixel drift exceeded
        assert not validation['pixel_drift_exceeded'], \
            f"Pixel drift exceeded tolerance: {validation}"
        
        print(f"Pixel alignment validation passed with max drift {validation['max_pixel_drift']}px")
    
    def test_pixel_alignment_with_different_configurations(self):
        """Test pixel alignment with various configurations."""
        test_configs = [
            # Small viewport
            PixelMappingConfig(
                min_depth=0.0,
                max_depth=50.0,
                viewport_width=400,
                viewport_height=300,
                vertical_padding=1,
                pixel_tolerance=1
            ),
            # Large viewport
            PixelMappingConfig(
                min_depth=100.0,
                max_depth=1000.0,
                viewport_width=1200,
                viewport_height=800,
                vertical_padding=5,
                pixel_tolerance=1
            ),
            # Narrow depth range
            PixelMappingConfig(
                min_depth=500.0,
                max_depth=510.0,
                viewport_width=800,
                viewport_height=600,
                vertical_padding=2,
                pixel_tolerance=1
            ),
        ]
        
        for i, config in enumerate(test_configs):
            mapper = PixelDepthMapper(config)
            validation = mapper.validate_pixel_alignment()
            
            assert validation['validation_passed'] == True, \
                f"Config {i} failed: {validation}"
            
            assert validation['max_pixel_drift'] <= config.pixel_tolerance, \
                f"Config {i}: Max pixel drift {validation['max_pixel_drift']}px exceeds tolerance {config.pixel_tolerance}px"
            
            print(f"Config {i} passed with max drift {validation['max_pixel_drift']}px")
    
    def test_edge_cases(self):
        """Test edge cases in pixel alignment."""
        config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=100.0,
            viewport_width=800,
            viewport_height=600,
            vertical_padding=2,
            pixel_tolerance=1
        )
        
        mapper = PixelDepthMapper(config)
        
        # Test depths at boundaries
        test_depths = [
            0.0,  # Minimum
            0.001,  # Just above minimum
            99.999,  # Just below maximum
            100.0,  # Maximum
        ]
        
        validation = mapper.validate_pixel_alignment(test_depths)
        
        assert validation['validation_passed'] == True, \
            f"Edge case validation failed: {validation}"
        
        # Check all test points are within tolerance
        for detail in validation['details']:
            if 'pixel_drift' in detail and detail['pixel_drift'] is not None:
                assert detail['pixel_drift'] <= config.pixel_tolerance, \
                    f"Edge case {detail['depth']} has drift {detail['pixel_drift']}px > {config.pixel_tolerance}px"
        
        print(f"Edge cases passed with max drift {validation['max_pixel_drift']}px")
    
    def test_pixel_range_mapping(self):
        """Test pixel range to depth range mapping."""
        config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=100.0,
            viewport_width=800,
            viewport_height=600,
            vertical_padding=2,
            pixel_tolerance=1
        )
        
        mapper = PixelDepthMapper(config)
        
        # Test depth range → pixel range
        min_pixel, max_pixel = mapper.get_pixel_range_for_depth_range(25.0, 75.0)
        
        # Verify pixels are within bounds
        assert min_pixel >= config.vertical_padding
        assert max_pixel < config.viewport_height - config.vertical_padding
        assert min_pixel <= max_pixel
        
        # Test pixel range → depth range
        min_depth, max_depth = mapper.get_depth_range_for_pixel_range(min_pixel, max_pixel)
        
        # Verify depths are within range
        assert min_depth >= config.min_depth
        assert max_depth <= config.max_depth
        assert min_depth <= max_depth
        
        # Verify round-trip consistency
        round_trip_min_pixel, round_trip_max_pixel = mapper.get_pixel_range_for_depth_range(min_depth, max_depth)
        
        assert abs(round_trip_min_pixel - min_pixel) <= config.pixel_tolerance, \
            f"Min pixel round-trip drift: {abs(round_trip_min_pixel - min_pixel)}px"
        assert abs(round_trip_max_pixel - max_pixel) <= config.pixel_tolerance, \
            f"Max pixel round-trip drift: {abs(round_trip_max_pixel - max_pixel)}px"
        
        print(f"Pixel range mapping: depth [{25.0}, {75.0}] → pixel [{min_pixel}, {max_pixel}]")
        print(f"Round-trip drift: min={abs(round_trip_min_pixel - min_pixel)}px, "
              f"max={abs(round_trip_max_pixel - max_pixel)}px")
    
    def test_cache_performance(self):
        """Test caching improves performance."""
        config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=100.0,
            viewport_width=800,
            viewport_height=600,
            vertical_padding=2,
            pixel_tolerance=1,
            enable_caching=True
        )
        
        mapper = PixelDepthMapper(config)
        
        # Initial mapping (cache miss)
        stats_before = mapper.get_cache_stats()
        assert stats_before['hits'] == 0
        assert stats_before['misses'] == 0
        
        # Map some depths
        test_depths = [0.0, 25.0, 50.0, 75.0, 100.0]
        for depth in test_depths:
            mapper.depth_to_pixel(depth)
        
        stats_after_first = mapper.get_cache_stats()
        assert stats_after_first['misses'] == len(test_depths)
        
        # Map same depths again (cache hits)
        for depth in test_depths:
            mapper.depth_to_pixel(depth)
        
        stats_after_second = mapper.get_cache_stats()
        assert stats_after_second['hits'] == len(test_depths)
        
        hit_rate = stats_after_second['hit_rate']
        assert hit_rate > 0.4, f"Hit rate too low: {hit_rate:.1%}"
        
        print(f"Cache performance: {stats_after_second['hits']} hits, "
              f"{stats_after_second['misses']} misses, "
              f"hit rate: {hit_rate:.1%}")


def run_pixel_alignment_tests():
    """Run pixel alignment tests and report results."""
    print("Running pixel alignment validation tests...")
    print("=" * 60)
    
    test_results = []
    
    # Create test instance
    tester = TestPixelAlignment()
    
    # Run each test
    tests = [
        ("Basic pixel mapping", tester.test_basic_pixel_mapping),
        ("Pixel alignment validation", tester.test_pixel_alignment_validation),
        ("Different configurations", tester.test_pixel_alignment_with_different_configurations),
        ("Edge cases", tester.test_edge_cases),
        ("Pixel range mapping", tester.test_pixel_range_mapping),
        ("Cache performance", tester.test_cache_performance),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
            test_results.append((test_name, "PASSED"))
            print(f"✓ {test_name}: PASSED")
        except AssertionError as e:
            test_results.append((test_name, f"FAILED: {str(e)}"))
            print(f"✗ {test_name}: FAILED - {str(e)}")
        except Exception as e:
            test_results.append((test_name, f"ERROR: {str(e)}"))
            print(f"✗ {test_name}: ERROR - {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("-" * 60)
    
    passed = sum(1 for _, status in test_results if "PASSED" in status)
    failed = sum(1 for _, status in test_results if "FAILED" in status)
    errors = sum(1 for _, status in test_results if "ERROR" in status)
    
    for test_name, status in test_results:
        print(f"  {test_name:30} {status}")
    
    print("-" * 60)
    print(f"Total: {len(test_results)} tests, {passed} passed, {failed} failed, {errors} errors")
    
    # Overall validation
    if failed == 0 and errors == 0:
        print("\n✅ All pixel alignment tests passed!")
        return True
    else:
        print(f"\n❌ Pixel alignment validation failed: {failed} tests failed, {errors} errors")
        return False


if __name__ == "__main__":
    # Run tests
    success = run_pixel_alignment_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)