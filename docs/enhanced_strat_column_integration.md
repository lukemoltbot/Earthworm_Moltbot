# Enhanced Stratigraphic Column Integration Guide

## Overview

The `EnhancedStratigraphicColumn` widget extends the base `StratigraphicColumn` class to provide real-time synchronization with LAS curve plotters and enhanced visualization features. This document explains how to integrate it into the Earthworm Moltbot application.

## Key Features

1. **Real-time Vertical Scrolling Synchronization**: Synchronized scrolling with LAS curves pane
2. **Detailed Lithology Display**: More detailed unit information than the overview column
3. **Depth Synchronization Signals**: Bidirectional communication via Qt signals
4. **Enhanced Selection Highlighting**: Improved visual feedback for selected units
5. **Configurable Display Options**: Toggle detailed labels, thickness values, qualifiers, etc.

## Integration Steps

### 1. Import the Enhanced Widget

Replace the import of `StratigraphicColumn` with `EnhancedStratigraphicColumn`:

```python
# Instead of:
# from .widgets.stratigraphic_column import StratigraphicColumn

# Use:
from .widgets.enhanced_stratigraphic_column import EnhancedStratigraphicColumn
```

### 2. Update Widget Creation

Update the widget creation in your UI setup:

```python
# Instead of:
# self.stratigraphicColumnView = StratigraphicColumn()

# Use:
self.stratigraphicColumnView = EnhancedStratigraphicColumn()
```

### 3. Set Up Synchronization

Connect the enhanced column with the curve plotter for real-time synchronization:

```python
# Assuming you have a curve plotter instance
self.curvePlotter = PyQtGraphCurvePlotter()

# Set up synchronization
self.stratigraphicColumnView.sync_with_curve_plotter(self.curvePlotter)
```

### 4. Configure Display Options (Optional)

Customize the display based on your needs:

```python
# Enable/disable detailed features
self.stratigraphicColumnView.set_detailed_labels_enabled(True)
self.stratigraphicColumnView.set_lithology_codes_enabled(True)
self.stratigraphicColumnView.set_thickness_values_enabled(True)
self.stratigraphicColumnView.set_qualifiers_enabled(True)
self.stratigraphicColumnView.set_highlight_gradient_enabled(True)

# Enable/disable synchronization
self.stratigraphicColumnView.set_sync_enabled(True)
```

### 5. Handle Signals (Optional)

Connect to the enhanced signals for custom behavior:

```python
# Depth range changed signal
self.stratigraphicColumnView.depthRangeChanged.connect(
    lambda min_depth, max_depth: print(f"Visible range: {min_depth}-{max_depth}m")
)

# Depth scrolled signal
self.stratigraphicColumnView.depthScrolled.connect(
    lambda center_depth: print(f"Scrolled to: {center_depth}m")
)

# Unit selected signal
self.stratigraphicColumnView.unitSelected.connect(
    lambda unit_index: print(f"Unit selected: {unit_index}")
)

# Sync requested signal
self.stratigraphicColumnView.syncRequested.connect(
    lambda: print("Synchronization requested")
)
```

## Signal Reference

### Emitted Signals

- `depthRangeChanged(min_depth, max_depth)`: Emitted when the visible depth range changes
- `depthScrolled(center_depth)`: Emitted when the column is scrolled
- `unitSelected(unit_index)`: Emitted when a unit is selected (enhanced version of unitClicked)
- `syncRequested()`: Emitted when synchronization is requested

### Inherited Signals

- `unitClicked(unit_index)`: Inherited from base class, emitted when a unit is clicked

## Method Reference

### Core Methods

- `draw_column(units_dataframe, min_overall_depth, max_overall_depth, ...)`: Draw the stratigraphic column with enhanced features
- `sync_with_curve_plotter(curve_plotter)`: Set up synchronization with a curve plotter
- `scroll_to_depth(depth)`: Scroll to a specific depth (with synchronization)
- `clear_column()`: Clear the column and reset enhanced data structures

### Configuration Methods

- `set_sync_enabled(enabled)`: Enable/disable synchronization
- `set_detailed_labels_enabled(enabled)`: Enable/disable detailed unit labels
- `set_lithology_codes_enabled(enabled)`: Enable/display of lithology codes
- `set_thickness_values_enabled(enabled)`: Enable/disable display of thickness values
- `set_qualifiers_enabled(enabled)`: Enable/disable display of lithology qualifiers
- `set_highlight_gradient_enabled(enabled)`: Enable/disable gradient highlighting

### Utility Methods

- `get_visible_depth_range()`: Get the currently visible depth range
- `update_synchronization()`: Force update of synchronization with curve plotter

## Synchronization Mechanism

### How It Works

1. **Scroll Bar Tracking**: The enhanced column monitors its vertical scroll bar for changes
2. **Depth Calculation**: Converts scroll position to depth values using the current depth scale
3. **Signal Emission**: Emits `depthScrolled` signal with the center depth
4. **Curve Plotter Update**: Connected curve plotter receives the signal and updates its view
5. **Bidirectional Sync**: Curve plotter changes also update the strat column via `viewRangeChanged`

### Configuration Options

- **Sync Enabled/Disabled**: Toggle synchronization on/off
- **Sync Threshold**: Minimum depth change (0.1m) before emitting signals to prevent excessive updates
- **Direct Method Calls**: Manual synchronization via `update_synchronization()`

## Example: Enhanced Hole Editor

Here's a complete example of integrating the enhanced column into a hole editor:

```python
class EnhancedHoleEditorWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create enhanced widgets
        self.curvePlotter = PyQtGraphCurvePlotter()
        self.stratigraphicColumnView = EnhancedStratigraphicColumn()  # Enhanced!
        self.editorTable = LithologyTableWidget()
        
        # Set up synchronization
        self.stratigraphicColumnView.sync_with_curve_plotter(self.curvePlotter)
        
        # Configure enhanced display
        self.stratigraphicColumnView.set_detailed_labels_enabled(True)
        self.stratigraphicColumnView.set_sync_enabled(True)
        
        # Connect enhanced signals
        self.stratigraphicColumnView.unitSelected.connect(self._on_enhanced_unit_selected)
        self.stratigraphicColumnView.depthScrolled.connect(self._on_depth_scrolled)
        
        # Setup UI layout
        self.setup_ui()
        
    def _on_enhanced_unit_selected(self, unit_index):
        """Enhanced unit selection handler."""
        print(f"Enhanced unit selected: {unit_index}")
        # Additional enhanced logic here
        
    def _on_depth_scrolled(self, center_depth):
        """Depth scroll handler."""
        print(f"Column scrolled to: {center_depth}m")
        # Additional scroll logic here
```

## Migration Considerations

### Backward Compatibility

The `EnhancedStratigraphicColumn` is fully backward compatible with the base `StratigraphicColumn`:

1. **Same Interface**: All base class methods are available
2. **Additional Features**: Enhanced features are opt-in via configuration methods
3. **Signal Compatibility**: Inherits all base class signals, adds enhanced versions

### Performance Considerations

- **Enhanced Features**: Detailed labels and gradients have minimal performance impact
- **Synchronization**: Signal-based synchronization is efficient and non-blocking
- **Memory Usage**: Additional data structures for quick unit access

### Testing

Use the provided offscreen test script to validate integration:

```bash
cd /path/to/Earthworm_Moltbot
QT_QPA_PLATFORM=offscreen python tests/test_enhanced_stratigraphic_column.py
```

## Troubleshooting

### Common Issues

1. **Synchronization Not Working**:
   - Verify `sync_enabled` is True
   - Check that `sync_with_curve_plotter()` was called
   - Ensure curve plotter has `viewRangeChanged` signal

2. **Detailed Labels Not Showing**:
   - Verify `show_detailed_labels` is True
   - Check unit height (labels only show on units ≥15 pixels tall)
   - Verify data has required columns (lithology_code, thickness, qualifier)

3. **Performance Issues**:
   - Disable gradient highlighting if not needed
   - Reduce label complexity for very dense columns
   - Consider increasing sync threshold

### Debugging

Enable debug output:

```python
# In your application setup
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check signal connections:

```python
# Verify signal connections
print(f"DepthScrolled connected: {self.stratigraphicColumnView.depthScrolled.receivers() > 0}")
print(f"Sync enabled: {self.stratigraphicColumnView.sync_enabled}")
```

## Conclusion

The `EnhancedStratigraphicColumn` provides significant improvements over the base stratigraphic column while maintaining full compatibility. The real-time synchronization with LAS curves creates a more integrated and user-friendly experience for geological data analysis.

For further assistance, refer to the test scripts or contact the development team.