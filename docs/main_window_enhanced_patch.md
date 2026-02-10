# Main Window Enhancement Patch

This document shows the changes needed to update `main_window.py` to use the `EnhancedStratigraphicColumn` instead of the base `StratigraphicColumn`.

## Required Changes

### 1. Update Import Statement

**File:** `src/ui/main_window.py`
**Line:** ~24

```diff
 from .widgets.stratigraphic_column import StratigraphicColumn
+from .widgets.enhanced_stratigraphic_column import EnhancedStratigraphicColumn
```

### 2. Update Widget Creation

**File:** `src/ui/main_window.py`
**Line:** ~80 (in `HoleEditorWindow.__init__`)

```diff
         # Create widgets - using PyQtGraphCurvePlotter for better performance
         self.curvePlotter = PyQtGraphCurvePlotter()
-        self.stratigraphicColumnView = StratigraphicColumn()
+        self.stratigraphicColumnView = EnhancedStratigraphicColumn()
         self.editorTable = LithologyTableWidget()
         self.exportCsvButton = QPushButton("Export to CSV")
```

### 3. Add Synchronization Setup

**File:** `src/ui/main_window.py`
**Line:** After widget creation (around line 85)

Add this code after creating the widgets:

```python
        # Set up enhanced synchronization between strat column and curve plotter
        self.stratigraphicColumnView.sync_with_curve_plotter(self.curvePlotter)
        
        # Configure enhanced display options
        self.stratigraphicColumnView.set_detailed_labels_enabled(True)
        self.stratigraphicColumnView.set_lithology_codes_enabled(True)
        self.stratigraphicColumnView.set_thickness_values_enabled(True)
        self.stratigraphicColumnView.set_qualifiers_enabled(True)
        self.stratigraphicColumnView.set_sync_enabled(True)
```

### 4. Update Signal Connections (Optional)

The enhanced column emits additional signals that can be connected for enhanced functionality:

```python
        # Connect enhanced signals (optional)
        self.stratigraphicColumnView.unitSelected.connect(self._on_enhanced_unit_selected)
        self.stratigraphicColumnView.depthScrolled.connect(self._on_enhanced_depth_scrolled)
        self.stratigraphicColumnView.depthRangeChanged.connect(self._on_depth_range_changed)
```

### 5. Add Enhanced Signal Handlers (Optional)

Add these methods to the `HoleEditorWindow` class:

```python
    def _on_enhanced_unit_selected(self, unit_index):
        """Enhanced unit selection handler."""
        print(f"Enhanced unit selected: {unit_index}")
        # Add any enhanced logic here
        
    def _on_enhanced_depth_scrolled(self, center_depth):
        """Enhanced depth scroll handler."""
        print(f"Enhanced column scrolled to: {center_depth}m")
        # Add any enhanced scroll logic here
        
    def _on_depth_range_changed(self, min_depth, max_depth):
        """Depth range changed handler."""
        print(f"Visible depth range: {min_depth:.1f}-{max_depth:.1f}m")
        # Update any range-dependent UI elements
```

## Complete Patch Example

Here's a complete example of the changes in context:

```python
# In imports section (around line 24):
from .widgets.stratigraphic_column import StratigraphicColumn
from .widgets.enhanced_stratigraphic_column import EnhancedStratigraphicColumn  # ADD THIS

# In HoleEditorWindow.__init__ method (around line 80):
class HoleEditorWindow(QWidget):
    def __init__(self, parent=None, coallog_data=None, file_path=None, main_window=None):
        # ... existing code ...
        
        # Create widgets - using PyQtGraphCurvePlotter for better performance
        self.curvePlotter = PyQtGraphCurvePlotter()
        self.stratigraphicColumnView = EnhancedStratigraphicColumn()  # CHANGED
        self.editorTable = LithologyTableWidget()
        self.exportCsvButton = QPushButton("Export to CSV")
        
        # Set up enhanced synchronization between strat column and curve plotter  # ADD THIS
        self.stratigraphicColumnView.sync_with_curve_plotter(self.curvePlotter)  # ADD THIS
        self.stratigraphicColumnView.set_detailed_labels_enabled(True)  # ADD THIS
        self.stratigraphicColumnView.set_sync_enabled(True)  # ADD THIS
        
        # ... rest of existing code ...
```

## Backward Compatibility Notes

1. **Full Compatibility**: The enhanced column is fully backward compatible
2. **Same API**: All existing method calls will continue to work
3. **Additional Features**: Enhanced features are opt-in via configuration
4. **Performance**: Minimal performance impact with default settings

## Testing the Integration

After making these changes, test the integration:

1. **Basic Functionality**: Ensure the strat column still draws correctly
2. **Synchronization**: Scroll the curve plotter and verify the strat column follows
3. **Enhanced Features**: Verify detailed labels appear on units
4. **Selection**: Click units and verify highlighting works

## Troubleshooting

If you encounter issues:

1. **Import Errors**: Verify the enhanced_stratigraphic_column.py file exists
2. **Synchronization Not Working**: Check that `sync_enabled` is True
3. **Labels Not Showing**: Verify unit height is sufficient (≥15 pixels)
4. **Performance Issues**: Disable gradient highlighting or detailed labels

## Benefits of the Enhanced Column

1. **Real-time Sync**: Seamless scrolling between curves and strat column
2. **Better Visualization**: More detailed unit information
3. **Improved UX**: Enhanced selection feedback
4. **Configurable**: Toggle features based on user preferences
5. **Future Extensible**: Ready for additional enhancements