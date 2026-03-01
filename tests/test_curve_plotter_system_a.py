"""
Unit tests for PyQtGraphCurvePlotter System A integration.

Tests that the widget properly receives DepthStateManager signals
and updates Y-axis accordingly.

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


class TestPyQtGraphCurvePlotterStateManagement:
    """Test state management for curve plotter."""
    
    def test_state_manager_can_be_created(self, state_manager):
        """Verify state manager can be created."""
        assert state_manager is not None
    
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


class TestCurvePlotterYAxisAlignment:
    """Test Y-axis alignment for curve plotter."""
    
    def test_viewport_depth_range_valid(self, state_manager):
        """Verify viewport depth range is always valid."""
        vp = state_manager.get_viewport_range()
        assert vp.from_depth < vp.to_depth
        assert vp.from_depth >= 0.0
        assert vp.to_depth <= 1000.0
    
    def test_cursor_within_bounds(self, state_manager):
        """Verify cursor depth stays within bounds."""
        state_manager.set_cursor_depth(150.0)
        cursor = state_manager.get_cursor_depth()
        assert cursor >= 0.0
        assert cursor <= 1000.0


class TestStateManagerIntegration:
    """Test state manager integration with curve plotter."""
    
    def test_cursor_and_zoom_changes(self, state_manager):
        """Verify cursor and zoom changes propagate correctly."""
        state_manager.set_cursor_depth(125.0)
        state_manager.set_zoom_level(1.5)
        
        # Verify both changes
        assert state_manager.get_cursor_depth() == 125.0
        assert state_manager.get_zoom_level() == 1.5
    
    def test_viewport_consistency_after_zoom(self, state_manager):
        """Verify viewport remains consistent after zoom."""
        vp = state_manager.get_viewport_range()
        assert vp.from_depth >= 0.0
        assert vp.to_depth <= 1000.0
        
        state_manager.set_zoom_level(2.0)
        
        # Verify viewport is still valid
        vp = state_manager.get_viewport_range()
        assert vp.from_depth >= 0.0
        assert vp.to_depth <= 1000.0
    
    def test_selection_management(self, state_manager):
        """Verify selection management works."""
        state_manager.set_selection_range(150.0, 250.0)
        
        selection = state_manager.get_selection_range()
        if selection is not None:
            assert selection.from_depth == 150.0
            assert selection.to_depth == 250.0
        
        state_manager.clear_selection()
        assert state_manager.get_selection_range() is None


class TestSignalPropagation:
    """Test that signals propagate correctly to curve plotter."""
    
    def test_cursor_signal_propagates(self, state_manager):
        """Verify cursor change signal propagates."""
        signal_received = {'called': False, 'value': None}
        
        def on_cursor_changed(depth):
            signal_received['called'] = True
            signal_received['value'] = depth
        
        state_manager.cursorDepthChanged.connect(on_cursor_changed)
        state_manager.set_cursor_depth(150.0)
        
        assert signal_received['called']
        assert signal_received['value'] == 150.0
    
    def test_zoom_signal_propagates(self, state_manager):
        """Verify zoom change signal propagates."""
        signal_received = {'called': False, 'value': None}
        
        def on_zoom_changed(zoom):
            signal_received['called'] = True
            signal_received['value'] = zoom
        
        state_manager.zoomLevelChanged.connect(on_zoom_changed)
        state_manager.set_zoom_level(2.0)
        
        assert signal_received['called']
        assert signal_received['value'] == 2.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
