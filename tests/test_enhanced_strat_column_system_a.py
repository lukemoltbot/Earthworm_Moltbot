"""
Unit tests for EnhancedStratigraphicColumn System A integration.

Tests that the widget properly receives DepthStateManager signals
and synchronizes viewport changes.

NOTE: These tests focus on state management without widget instantiation
since GUI testing requires a display environment.
"""

import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/Users/lukemoltbot/projects/Earthworm_Moltbot')

from src.ui.graphic_window.state.depth_state_manager import DepthStateManager
from src.ui.graphic_window.state.depth_range import DepthRange


@pytest.fixture
def state_manager():
    """Create DepthStateManager instance."""
    return DepthStateManager(min_depth=0.0, max_depth=1000.0)


class TestEnhancedStratigraphicColumnStateManagement:
    """Test state management for stratigraphic column."""
    
    def test_state_manager_can_be_created(self, state_manager):
        """Verify state manager can be created and accessed."""
        assert state_manager is not None
        assert state_manager.min_depth == 0.0
        assert state_manager.max_depth == 1000.0
    
    def test_receives_cursor_depth_signal(self, state_manager):
        """Verify state manager handles cursor depth changes."""
        state_manager.set_cursor_depth(125.0)
        cursor = state_manager.get_cursor_depth()
        assert cursor == 125.0
    
    def test_receives_zoom_level_signal(self, state_manager):
        """Verify state manager handles zoom level changes."""
        state_manager.set_zoom_level(2.0)
        zoom = state_manager.get_zoom_level()
        assert zoom == 2.0
    
    def test_state_manager_signals_emitted(self, state_manager):
        """Verify state manager signals are properly connected."""
        signal_received = {'cursor': False, 'zoom': False}
        
        def on_cursor_changed(depth):
            signal_received['cursor'] = True
        
        def on_zoom_changed(zoom):
            signal_received['zoom'] = True
        
        state_manager.cursorDepthChanged.connect(on_cursor_changed)
        state_manager.zoomLevelChanged.connect(on_zoom_changed)
        
        state_manager.set_cursor_depth(125.0)
        state_manager.set_zoom_level(2.0)
        
        assert signal_received['cursor']
        assert signal_received['zoom']


class TestStateManagerBasicFunctionality:
    """Test basic DepthStateManager functionality."""
    
    def test_viewport_range_initial_value(self, state_manager):
        """Verify viewport range has initial value."""
        vp = state_manager.get_viewport_range()
        assert vp is not None
        assert vp.from_depth >= 0.0
        assert vp.to_depth <= 1000.0
        assert vp.to_depth > vp.from_depth
    
    def test_cursor_depth_setting(self, state_manager):
        """Verify cursor depth can be set and retrieved."""
        state_manager.set_cursor_depth(150.0)
        cursor = state_manager.get_cursor_depth()
        assert cursor == 150.0
    
    def test_zoom_level_setting(self, state_manager):
        """Verify zoom level can be set and retrieved."""
        state_manager.set_zoom_level(1.5)
        zoom = state_manager.get_zoom_level()
        assert zoom == 1.5
    
    def test_cursor_depth_clamping_high(self, state_manager):
        """Verify cursor depth is clamped to max."""
        state_manager.set_cursor_depth(5000.0)
        cursor = state_manager.get_cursor_depth()
        assert cursor <= 1000.0
    
    def test_cursor_depth_clamping_low(self, state_manager):
        """Verify cursor depth is clamped to min."""
        state_manager.set_cursor_depth(-100.0)
        cursor = state_manager.get_cursor_depth()
        assert cursor >= 0.0
    
    def test_zoom_level_clamping_high(self, state_manager):
        """Verify zoom level is clamped to max."""
        state_manager.set_zoom_level(100.0)
        zoom = state_manager.get_zoom_level()
        assert 0.1 <= zoom <= 10.0
    
    def test_zoom_level_clamping_low(self, state_manager):
        """Verify zoom level is clamped to min."""
        state_manager.set_zoom_level(0.01)
        zoom = state_manager.get_zoom_level()
        assert 0.1 <= zoom <= 10.0


class TestViewportManagement:
    """Test viewport management in state manager."""
    
    def test_viewport_bounds_valid(self, state_manager):
        """Verify viewport always has valid bounds."""
        for _ in range(5):
            vp = state_manager.get_viewport_range()
            assert vp.from_depth >= state_manager.min_depth
            assert vp.to_depth <= state_manager.max_depth
            assert vp.from_depth < vp.to_depth
    
    def test_center_on_depth_centers_viewport(self, state_manager):
        """Verify centering on depth positions viewport correctly."""
        state_manager.center_on_depth(500.0)
        vp = state_manager.get_viewport_range()
        
        # Center should be close to 500
        center = (vp.from_depth + vp.to_depth) / 2
        assert 400 < center < 600
    
    def test_reset_to_defaults(self, state_manager):
        """Verify reset clears all state to defaults."""
        state_manager.set_cursor_depth(500.0)
        state_manager.set_zoom_level(2.0)
        state_manager.reset_to_defaults()
        
        # Check reset values
        assert state_manager.get_cursor_depth() == 0.0
        assert state_manager.get_zoom_level() == 1.0


class TestStateConsistency:
    """Test state consistency across multiple operations."""
    
    def test_multiple_sequential_updates(self, state_manager):
        """Verify multiple updates maintain consistency."""
        state_manager.set_cursor_depth(125.0)
        state_manager.set_zoom_level(1.5)
        
        # Verify both persisted
        assert state_manager.get_cursor_depth() == 125.0
        assert state_manager.get_zoom_level() == 1.5
    
    def test_state_dict_representation(self, state_manager):
        """Verify state dictionary representation is complete."""
        state_manager.set_cursor_depth(150.0)
        state_manager.set_zoom_level(1.5)
        
        state_dict = state_manager.get_state_dict()
        
        assert 'viewport' in state_dict
        assert 'cursor' in state_dict
        assert 'zoom' in state_dict
        assert state_dict['cursor'] == 150.0
        assert state_dict['zoom'] == 1.5
    
    def test_selection_management(self, state_manager):
        """Verify selection range can be managed."""
        state_manager.set_selection_range(100.0, 200.0)
        selection = state_manager.get_selection_range()
        
        assert selection is not None
        assert selection.from_depth == 100.0
        assert selection.to_depth == 200.0
        
        state_manager.clear_selection()
        assert state_manager.get_selection_range() is None


class TestSignalConnectivity:
    """Test that signals can be connected and emitted."""
    
    def test_can_connect_to_viewport_signal(self, state_manager):
        """Verify viewport signal can be connected."""
        called = [False]
        
        def callback(dr):
            called[0] = True
        
        state_manager.viewportRangeChanged.connect(callback)
        # Trigger a viewport change
        vp = state_manager.get_viewport_range()
        state_manager.set_viewport_range(vp.from_depth + 10, vp.to_depth + 10)
        
        assert called[0]
    
    def test_can_connect_to_cursor_signal(self, state_manager):
        """Verify cursor signal can be connected."""
        called = [False]
        
        def callback(depth):
            called[0] = True
        
        state_manager.cursorDepthChanged.connect(callback)
        state_manager.set_cursor_depth(500.0)
        
        assert called[0]
    
    def test_can_connect_to_zoom_signal(self, state_manager):
        """Verify zoom signal can be connected."""
        called = [False]
        
        def callback(zoom):
            called[0] = True
        
        state_manager.zoomLevelChanged.connect(callback)
        state_manager.set_zoom_level(2.0)
        
        assert called[0]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
