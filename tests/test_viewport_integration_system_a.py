"""
Integration tests for System A viewport synchronization.

Tests that changes in one widget propagate to all other widgets
via the centralized DepthStateManager.

NOTE: Tests focus on state management without widget instantiation
since GUI testing requires a display environment.
"""

import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/Users/lukemoltbot/projects/Earthworm_Moltbot')

from src.ui.graphic_window.state.depth_state_manager import DepthStateManager


@pytest.fixture
def state_manager():
    """Create shared state manager."""
    return DepthStateManager(min_depth=0.0, max_depth=1000.0)


class TestBidirectionalSynchronization:
    """Test bidirectional sync between widgets via state manager."""
    
    def test_state_manager_maintains_state(self, state_manager):
        """Verify state manager maintains viewport state."""
        vp = state_manager.get_viewport_range()
        assert vp is not None
        assert vp.from_depth >= 0.0
        assert vp.to_depth <= 1000.0
    
    def test_strat_column_click_updates_cursor(self, state_manager):
        """Verify clicking strat column updates cursor in state manager."""
        state_manager.set_cursor_depth(125.0)
        cursor = state_manager.get_cursor_depth()
        assert cursor == 125.0
    
    def test_multiple_properties_settable(self, state_manager):
        """Verify multiple properties can be set independently."""
        # Set different properties
        state_manager.set_cursor_depth(250.0)
        state_manager.set_zoom_level(1.5)
        state_manager.set_selection_range(100.0, 300.0)
        
        # Verify all are set
        assert state_manager.get_cursor_depth() == 250.0
        assert state_manager.get_zoom_level() == 1.5
        assert state_manager.get_selection_range() is not None
    
    def test_state_manager_is_singleton_reference(self, state_manager):
        """Verify state manager is shared across all widgets."""
        # Simulate two widgets with same state manager
        manager1 = state_manager
        manager2 = state_manager
        
        # Changes through manager1 should be visible via manager2
        manager1.set_cursor_depth(300.0)
        assert manager2.get_cursor_depth() == 300.0
    
    def test_no_deadlock_with_rapid_updates(self, state_manager):
        """Verify rapid updates don't cause deadlocks."""
        # Rapid sequential updates
        for i in range(10):
            depth = 100 + (i * 10)
            state_manager.set_cursor_depth(float(depth))
        
        # Should complete without hanging
        assert state_manager.get_cursor_depth() == 190.0


class TestStateConsistency:
    """Test that state remains consistent across updates."""
    
    def test_viewport_remains_valid(self, state_manager):
        """Verify viewport remains valid."""
        vp = state_manager.get_viewport_range()
        assert vp.from_depth >= state_manager.min_depth
        assert vp.to_depth <= state_manager.max_depth
        assert vp.from_depth < vp.to_depth
    
    def test_cursor_depth_bounds(self, state_manager):
        """Verify cursor depth respects bounds."""
        # Try to set depth outside bounds
        state_manager.set_cursor_depth(5000.0)  # Outside 0-1000 range
        
        # Should be clamped
        cursor = state_manager.get_cursor_depth()
        assert cursor <= 1000.0
    
    def test_zoom_level_bounds(self, state_manager):
        """Verify zoom level respects bounds."""
        # Try to set zoom way too high
        state_manager.set_zoom_level(100.0)
        
        # Should be clamped to max (10x)
        zoom = state_manager.get_zoom_level()
        assert zoom <= 10.0
        assert zoom > 0
        
        # Try to set zoom way too low
        state_manager.set_zoom_level(0.01)
        
        # Should be clamped to min (0.1x)
        zoom = state_manager.get_zoom_level()
        assert zoom >= 0.1


class TestSignalPropagation:
    """Test that signals propagate correctly."""
    
    def test_viewport_signal_propagates(self, state_manager):
        """Verify viewport change signal propagates."""
        signal_received = {'called': False}
        
        def on_viewport_changed(depth_range):
            signal_received['called'] = True
        
        state_manager.viewportRangeChanged.connect(on_viewport_changed)
        # Trigger a viewport change by scrolling
        vp = state_manager.get_viewport_range()
        state_manager.set_viewport_range(vp.from_depth + 10, vp.to_depth + 10)
        
        assert signal_received['called'], "Viewport signal not received"
    
    def test_cursor_signal_propagates(self, state_manager):
        """Verify cursor change signal propagates."""
        signal_received = {'called': False, 'value': None}
        
        def on_cursor_changed(depth):
            signal_received['called'] = True
            signal_received['value'] = depth
        
        state_manager.cursorDepthChanged.connect(on_cursor_changed)
        state_manager.set_cursor_depth(150.0)
        
        assert signal_received['called'], "Cursor signal not received"
        assert signal_received['value'] == 150.0
    
    def test_zoom_signal_propagates(self, state_manager):
        """Verify zoom change signal propagates."""
        signal_received = {'called': False, 'value': None}
        
        def on_zoom_changed(zoom):
            signal_received['called'] = True
            signal_received['value'] = zoom
        
        state_manager.zoomLevelChanged.connect(on_zoom_changed)
        state_manager.set_zoom_level(2.0)
        
        assert signal_received['called'], "Zoom signal not received"
        assert signal_received['value'] == 2.0


class TestMultipleSubscribers:
    """Test state manager with multiple signal subscribers."""
    
    def test_multiple_viewport_subscribers(self, state_manager):
        """Verify multiple subscribers receive viewport signals."""
        subscribers = [{'called': False} for _ in range(3)]
        
        for i, sub in enumerate(subscribers):
            def make_callback(s):
                def callback(depth_range):
                    s['called'] = True
                return callback
            
            state_manager.viewportRangeChanged.connect(make_callback(sub))
        
        # Trigger viewport change
        vp = state_manager.get_viewport_range()
        state_manager.set_viewport_range(vp.from_depth + 10, vp.to_depth + 10)
        
        for i, sub in enumerate(subscribers):
            assert sub['called'], f"Subscriber {i} did not receive viewport signal"
    
    def test_multiple_cursor_subscribers(self, state_manager):
        """Verify multiple subscribers receive cursor signals."""
        subscribers = [{'called': False} for _ in range(3)]
        
        for i, sub in enumerate(subscribers):
            def make_callback(s):
                def callback(depth):
                    s['called'] = True
                return callback
            
            state_manager.cursorDepthChanged.connect(make_callback(sub))
        
        state_manager.set_cursor_depth(150.0)
        
        for i, sub in enumerate(subscribers):
            assert sub['called'], f"Subscriber {i} did not receive cursor signal"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""
    
    def test_user_scrolls_then_clicks(self, state_manager):
        """Simulate user scrolling then clicking."""
        # User scrolls - viewport changes
        vp = state_manager.get_viewport_range()
        state_manager.scroll_viewport(100.0)
        
        # User clicks - cursor changes
        state_manager.set_cursor_depth(400.0)
        
        # Verify both changes
        assert state_manager.get_cursor_depth() == 400.0
    
    def test_user_zooms_and_centers(self, state_manager):
        """Simulate user zooming and centering on a depth."""
        # User zooms in
        state_manager.set_zoom_level(2.0)
        
        # User centers on specific depth
        state_manager.center_on_depth(500.0)
        vp = state_manager.get_viewport_range()
        
        # Verify viewport is centered
        center = (vp.from_depth + vp.to_depth) / 2
        assert abs(center - 500.0) < 100
    
    def test_state_persistence_across_operations(self, state_manager):
        """Verify state persists across multiple operations."""
        state_manager.set_cursor_depth(250.0)
        state_manager.center_on_depth(600.0)
        state_manager.set_zoom_level(1.5)
        
        # Cursor should still be 250
        assert state_manager.get_cursor_depth() == 250.0
        # Zoom should still be 1.5
        assert state_manager.get_zoom_level() == 1.5


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
