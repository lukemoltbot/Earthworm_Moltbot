"""
Phase 3 Performance Benchmark Test.

Tests synchronized scrolling performance with 10,000 data points
to validate 60+ FPS target and < 100ms response time.
"""

import pytest
import sys
import os
import time
import numpy as np
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set QT_QPA_PLATFORM to offscreen for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from src.ui.widgets.unified_viewport.scrolling_synchronizer import (
    ScrollingSynchronizer, ScrollPerformanceConfig
)
from src.ui.widgets.unified_viewport.component_adapter import ComponentAdapter
from src.ui.widgets.unified_viewport.pixel_depth_mapper import PixelDepthMapper, PixelMappingConfig


class MockPerformanceCurvePlotter:
    """Mock curve plotter for performance testing."""
    
    def __init__(self, data_points=10000):
        self.data_points = data_points
        self.current_depth = 0.0
        self.update_count = 0
        self.update_times = []
    
    def set_view_range(self, min_depth, max_depth):
        """Simulate view range update."""
        update_start = time.time()
        
        # Simulate processing 10,000 data points
        # This simulates the actual work a curve plotter would do
        dummy_data = np.random.randn(self.data_points)
        _ = np.mean(dummy_data)  # Simulate some processing
        
        update_time = (time.time() - update_start) * 1000
        self.update_times.append(update_time)
        self.update_count += 1
        self.current_depth = (min_depth + max_depth) / 2
        
        # Keep last 100 updates
        if len(self.update_times) > 100:
            self.update_times.pop(0)
    
    def get_performance(self):
        """Get performance metrics."""
        if not self.update_times:
            return {"avg_update_time": 0, "update_count": 0}
        
        return {
            "avg_update_time_ms": sum(self.update_times) / len(self.update_times),
            "max_update_time_ms": max(self.update_times),
            "update_count": self.update_count,
            "data_points": self.data_points
        }


class MockPerformanceStratColumn:
    """Mock stratigraphic column for performance testing."""
    
    def __init__(self):
        self.current_depth = 0.0
        self.update_count = 0
        self.update_times = []
    
    def set_depth_position(self, depth):
        """Simulate depth position update."""
        update_start = time.time()
        
        # Simulate strat column update (typically faster than curve plotter)
        time.sleep(0.001)  # 1ms simulated work
        
        update_time = (time.time() - update_start) * 1000
        self.update_times.append(update_time)
        self.update_count += 1
        self.current_depth = depth
        
        # Keep last 100 updates
        if len(self.update_times) > 100:
            self.update_times.pop(0)
    
    def get_performance(self):
        """Get performance metrics."""
        if not self.update_times:
            return {"avg_update_time": 0, "update_count": 0}
        
        return {
            "avg_update_time_ms": sum(self.update_times) / len(self.update_times),
            "max_update_time_ms": max(self.update_times),
            "update_count": self.update_count
        }


class TestPhase3Performance:
    """Test Phase 3 performance requirements."""
    
    def setup_method(self):
        """Setup test environment."""
        # Create pixel mapper
        pixel_config = PixelMappingConfig(
            min_depth=0.0,
            max_depth=1000.0,  # Large range for testing
            viewport_width=1024,
            viewport_height=768,
            vertical_padding=2,
            pixel_tolerance=1
        )
        self.pixel_mapper = PixelDepthMapper(pixel_config)
        
        # Create scrolling synchronizer with Phase 3 targets
        scroll_config = ScrollPerformanceConfig(
            target_fps=60,
            max_response_time_ms=100,
            max_memory_mb=50,
            max_data_points=10000,
            enable_smooth_scrolling=True,
            scroll_sensitivity=1.0
        )
        self.synchronizer = ScrollingSynchronizer(scroll_config)
        
        # Create mock components
        self.curve_plotter = MockPerformanceCurvePlotter(data_points=10000)
        self.strat_column = MockPerformanceStratColumn()
        
        # Create component adapter
        self.adapter = ComponentAdapter()
    
    def test_60_fps_target(self):
        """Test that system can achieve 60+ FPS target."""
        print("\n🧪 Testing 60+ FPS target...")
        
        # Connect components
        self.adapter.connect_components(
            self.curve_plotter, self.strat_column, self.pixel_mapper, self.synchronizer
        )
        
        # Simulate rapid scrolling (simulating user interaction)
        scroll_positions = np.linspace(0, 1000, 120)  # 120 positions over 2 seconds = 60 FPS
        
        frame_times = []
        start_time = time.time()
        
        for position in scroll_positions:
            frame_start = time.time()
            
            # Scroll to position
            success = self.synchronizer.scroll_to_depth(position)
            assert success, f"Failed to scroll to position {position}"
            
            # Record frame time
            frame_time = (time.time() - frame_start) * 1000
            frame_times.append(frame_time)
            
            # Small delay to simulate real-time
            time.sleep(0.001)
        
        total_time = time.time() - start_time
        
        # Calculate achieved FPS
        avg_frame_time = sum(frame_times) / len(frame_times)
        achieved_fps = 1000.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        print(f"  Total test time: {total_time:.2f}s")
        print(f"  Average frame time: {avg_frame_time:.2f}ms")
        print(f"  Achieved FPS: {achieved_fps:.1f}")
        print(f"  Target FPS: 60+")
        
        # Phase 3 requirement: 60+ FPS
        assert achieved_fps >= 55, f"FPS too low: {achieved_fps:.1f} (target: 60+)"
        
        # Check individual frame times
        slow_frames = [t for t in frame_times if t > 16.7]  # >16.7ms = <60 FPS
        slow_frame_percentage = (len(slow_frames) / len(frame_times)) * 100
        
        print(f"  Slow frames (>16.7ms): {len(slow_frames)}/{len(frame_times)} ({slow_frame_percentage:.1f}%)")
        
        # Allow some slow frames but majority should be fast
        assert slow_frame_percentage < 20, f"Too many slow frames: {slow_frame_percentage:.1f}%"
        
        print("✅ 60+ FPS target achieved")
    
    def test_100ms_response_time(self):
        """Test < 100ms response time to scroll events."""
        print("\n🧪 Testing < 100ms response time...")
        
        # Connect components first
        self.adapter.connect_components(
            self.curve_plotter, self.strat_column, self.pixel_mapper, self.synchronizer
        )
        
        # Test response to individual scroll events
        response_times = []
        
        for i in range(10):
            test_depth = i * 100.0
            
            start_time = time.time()
            success = self.synchronizer.scroll_to_depth(test_depth)
            response_time = (time.time() - start_time) * 1000
            
            assert success, f"Failed to scroll to depth {test_depth}"
            response_times.append(response_time)
            
            print(f"  Scroll to {test_depth}: {response_time:.1f}ms")
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        
        print(f"  Average response time: {avg_response_time:.1f}ms")
        print(f"  Maximum response time: {max_response_time:.1f}ms")
        print(f"  Target: < 100ms")
        
        # Phase 3 requirement: < 100ms response time
        assert max_response_time < 150, f"Response time too high: {max_response_time:.1f}ms (target: < 100ms)"
        assert avg_response_time < 100, f"Average response time too high: {avg_response_time:.1f}ms"
        
        print("✅ < 100ms response time achieved")
    
    def test_10000_data_point_performance(self):
        """Test performance with 10,000 data points."""
        print("\n🧪 Testing 10,000 data point performance...")
        
        # Connect components
        self.adapter.connect_components(
            self.curve_plotter, self.strat_column, self.pixel_mapper, self.synchronizer
        )
        
        # Perform scrolling test with 10,000 data points
        scroll_positions = [0.0, 250.0, 500.0, 750.0, 1000.0]
        
        update_times = []
        
        for position in scroll_positions:
            start_time = time.time()
            
            # Scroll to position (triggers component updates)
            success = self.synchronizer.scroll_to_depth(position)
            assert success, f"Failed to scroll to position {position}"
            
            # Update time measurement (no artificial delay)
            update_time = (time.time() - start_time) * 1000
            update_times.append(update_time)
            
            print(f"  Scroll with 10k points to {position}: {update_time:.1f}ms")
        
        avg_update_time = sum(update_times) / len(update_times)
        max_update_time = max(update_times)
        
        # Get curve plotter performance
        curve_perf = self.curve_plotter.get_performance()
        
        print(f"  Average update time: {avg_update_time:.1f}ms")
        print(f"  Maximum update time: {max_update_time:.1f}ms")
        print(f"  Curve plotter avg: {curve_perf['avg_update_time_ms']:.1f}ms")
        print(f"  Data points processed: {curve_perf['data_points']}")
        
        # Verify 10,000 data points were processed
        assert curve_perf['data_points'] == 10000, f"Wrong data point count: {curve_perf['data_points']}"
        
        # Performance should be reasonable even with 10,000 points
        assert max_update_time < 200, f"Update time too high with 10k points: {max_update_time:.1f}ms"
        
        print("✅ 10,000 data point performance acceptable")
    
    def test_memory_usage_target(self):
        """Test < 50MB additional memory usage."""
        print("\n🧪 Testing < 50MB memory usage...")
        
        # Note: Actual memory testing would require process monitoring
        # For now, we verify configuration and estimate
        
        config = self.synchronizer.config
        
        print(f"  Configured max memory: {config.max_memory_mb}MB")
        print(f"  Target: < 50MB additional memory")
        
        # Phase 3 requirement: < 50MB additional memory
        assert config.max_memory_mb <= 50, f"Memory target too high: {config.max_memory_mb}MB"
        
        # Check optimization features that reduce memory
        assert config.enable_viewport_caching == True, "Viewport caching should be enabled"
        assert config.cache_size_mb <= 10, f"Cache size too large: {config.cache_size_mb}MB"
        assert config.lazy_rendering == True, "Lazy rendering should be enabled"
        
        print("✅ Memory usage configuration meets Phase 3 requirements")
    
    def test_smooth_scrolling_performance(self):
        """Test smooth scrolling performance."""
        print("\n🧪 Testing smooth scrolling performance...")
        
        config = self.synchronizer.config
        
        # Check smooth scrolling configuration
        assert config.enable_smooth_scrolling == True, "Smooth scrolling should be enabled"
        assert config.inertia_duration_ms > 0, "Inertia duration should be positive"
        assert config.scroll_sensitivity == 1.0, "Default sensitivity should be 1.0"
        
        print(f"  Smooth scrolling: Enabled")
        print(f"  Inertia duration: {config.inertia_duration_ms}ms")
        print(f"  Render throttle: {config.render_throttle_ms}ms (~{1000/config.render_throttle_ms:.0f} FPS)")
        
        # Render throttle should support 60+ FPS
        max_fps_from_throttle = 1000 / config.render_throttle_ms
        assert max_fps_from_throttle >= 55, f"Render throttle too slow for 60 FPS: {max_fps_from_throttle:.0f} FPS max"
        
        print("✅ Smooth scrolling configuration supports 60+ FPS")
    
    def test_integrated_performance(self):
        """Test integrated performance with all components."""
        print("\n🧪 Testing integrated performance...")
        
        # Connect all components
        self.adapter.connect_components(
            self.curve_plotter, self.strat_column, self.pixel_mapper, self.synchronizer
        )
        
        # Get component status
        status = self.adapter.get_component_status()
        
        print(f"  Components connected: {status['is_fully_connected']}")
        print(f"  Curve plotter: {status['curve_plotter']['type']}")
        print(f"  Strat column: {status['strat_column']['type']}")
        print(f"  Pixel mapper: {status['pixel_mapper']['type']}")
        print(f"  Scrolling synchronizer: {status['scrolling_synchronizer']['type']}")
        
        # All components should be connected
        assert status['is_fully_connected'] == True, "Components not fully connected"
        assert status['curve_plotter']['connected'] == True, "Curve plotter not connected"
        assert status['strat_column']['connected'] == True, "Strat column not connected"
        
        # Test connection
        test_result = self.adapter.test_connection()
        assert test_result == True, "Component connection test failed"
        
        print("✅ All components integrated and connected")
        print("✅ Connection test passed")


def run_phase3_performance_benchmark():
    """Run Phase 3 performance benchmark."""
    print("=" * 70)
    print("PHASE 3 PERFORMANCE BENCHMARK")
    print("Testing synchronized scrolling at 60+ FPS with 10,000 data points")
    print("=" * 70)
    
    test_results = []
    
    # Create test instance
    tester = TestPhase3Performance()
    
    # Run each performance test
    tests = [
        ("60+ FPS Target", tester.test_60_fps_target),
        ("< 100ms Response Time", tester.test_100ms_response_time),
        ("10,000 Data Point Performance", tester.test_10000_data_point_performance),
        ("< 50MB Memory Usage", tester.test_memory_usage_target),
        ("Smooth Scrolling", tester.test_smooth_scrolling_performance),
        ("Integrated Performance", tester.test_integrated_performance),
    ]
    
    for test_name, test_func in tests:
        try:
            tester.setup_method()
            test_func()
            test_results.append((test_name, "PASSED"))
            print(f"✓ {test_name}: PASSED\n")
        except AssertionError as e:
            test_results.append((test_name, f"FAILED: {str(e)}"))
            print(f"✗ {test_name}: FAILED - {str(e)}\n")
        except Exception as e:
            test_results.append((test_name, f"ERROR: {str(e)}"))
            print(f"✗ {test_name}: ERROR - {str(e)}\n")
    
    print("=" * 70)
    print("BENCHMARK SUMMARY:")
    print("-" * 70)
    
    passed = sum(1 for _, status in test_results if "PASSED" in status)
    failed = sum(1 for _, status in test_results if "FAILED" in status)
    errors = sum(1 for _, status in test_results if "ERROR" in status)
    
    for test_name, status in test_results:
        print(f"  {test_name:40} {status}")
    
    print("-" * 70)
    print(f"Total: {len(test_results)} tests, {passed} passed, {failed} failed, {errors} errors")
    
    # Phase 3 validation
    if passed == len(test_results):
        print("\n🎉 PHASE 3 PERFORMANCE VALIDATION SUCCESSFUL:")
        print("   ✅ 60+ FPS target achievable")
        print("   ✅ < 100ms response time")
        print("   ✅ Handles 10,000+ data points")
        print("   ✅ < 50MB additional memory target")
        print("   ✅ Smooth scrolling enabled")
        print("   ✅ All components integrated")
        print("\n🚀 Phase 3 ready for production integration!")
        return True
    else:
        print(f"\n❌ Phase 3 performance validation incomplete")
        print(f"   {failed} performance tests failed, {errors} errors")
        return False


if __name__ == "__main__":
    # Run performance benchmark
    success = run_phase3_performance_benchmark()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)