# LAS Curve Pane Scaling Issues - Root Cause Analysis Report

## Executive Summary

This report analyzes the LAS curve pane scaling, alignment, and visibility toggle implementation issues in the Earthworm Moltbot application. The analysis identifies root causes for four main issues and provides technical recommendations for fixes.

## Investigation Areas

### 1. Curve Scaling Problems - Why density curves become too small when scrolling

**Root Cause Analysis:**
- **Depth Scale Mismatch**: Both `PyQtGraphCurvePlotter` and `EnhancedStratigraphicColumn` use `depth_scale = 10`, which should match
- **Viewport Synchronization Issue**: The `scroll_to_depth` method calculates center position but may not account for viewport transformations
- **Y-axis Range Calculation**: When scrolling, the method calculates new Y range but may not preserve the visible height correctly
- **Potential Bug**: In `scroll_to_depth` method, the calculation `new_y_min = depth - current_height / 2` assumes `current_height` is valid, but if view hasn't been initialized properly, this could cause scaling issues

**Technical Details:**
```python
# In PyQtGraphCurvePlotter.scroll_to_depth():
current_y_min = view_range[1][0]
current_y_max = view_range[1][1]
current_height = current_y_max - current_y_min
# If current_height is 0 or invalid, scaling breaks
```

**Fix Recommendation:**
- Add validation for `current_height` before calculations
- Ensure view range is properly initialized before scrolling
- Add bounds checking to prevent invalid ranges

### 2. Gamma Ray Alignment Issues - Why gamma ray is too large and misaligned

**Root Cause Analysis:**
- **Dual-Axis Synchronization Bug**: The gamma viewbox is linked with `setXLink()` but Y-axis synchronization is incomplete
- **Viewbox Geometry Update**: `update_gamma_view()` function calls `linkedViewChanged()` but only on resize events
- **Missing Y-axis Link**: Gamma viewbox needs `setYLink(self.plot_item.vb)` for proper scrolling synchronization
- **Stationary Curves**: Gamma curves appear stationary because their viewbox Y-axis doesn't move with main view

**Critical Bug Found:**
```python
# In setup_dual_axes():
self.gamma_viewbox.setXLink(self.plot_item)  # Only X-axis linked!
# Missing: self.gamma_viewbox.setYLink(self.plot_item.vb)
```

**The `update_gamma_view` function is called on resize, but scrolling doesn't trigger resize events, so gamma viewbox doesn't update its Y-axis position.**

**Fix Recommendation:**
1. Add Y-axis linking: `self.gamma_viewbox.setYLink(self.plot_item.vb)`
2. Connect scrolling signals to update gamma viewbox geometry
3. Ensure `linkedViewChanged` is called during scrolling, not just resizing

### 3. Range Normalization - How curves with different ranges should be aligned

**Current Implementation:**
- Gamma Ray: 0-300 API (top axis)
- Density Curves: 0-4 g/cc (bottom axis)
- Range ratio: 75:1 (300/4)

**Issues Identified:**
1. **Visual Scaling**: 75x difference in ranges makes density curves appear compressed
2. **Dual-Axis System**: Implemented but potentially buggy
3. **Auto-ranging**: Not implemented - uses fixed ranges from config

**Normalization Strategies:**

**Option A: Dual-Axis System (Current Approach)**
- Pros: Preserves actual measurement units
- Cons: Requires proper synchronization, different scales can be confusing

**Option B: Normalized Ranges (0-1)**
- Pros: Consistent visual scale, easier comparison
- Cons: Loses actual measurement context

**Option C: Smart Auto-ranging**
- Pros: Adapts to data, optimal use of space
- Cons: More complex, may confuse users expecting standard ranges

**Option D: Logarithmic Scaling for Large Ranges**
- Pros: Handles large range differences well
- Cons: Not intuitive for all users, distorts linear relationships

**Recommended Solution:**
- Fix dual-axis synchronization bugs
- Add optional normalization toggle
- Implement data-aware auto-ranging as fallback
- Maintain current ranges as defaults but allow adjustment

### 4. Visibility Toggle Architecture

**Current Implementation Analysis:**
- `set_curve_visibility()` method exists with curve name mapping
- Uses `curve_items` dictionary to find and toggle curves
- Updates legend visibility
- Has comprehensive name mapping for flexible curve identification

**Issues Identified:**
1. **UI Integration**: Method exists but UI controls not connected
2. **Name Mapping**: May not match all possible curve column names
3. **State Persistence**: No mechanism to save/restore visibility states
4. **Batch Operations**: No method to toggle multiple curves at once

**Architecture Design:**

**Core Components:**
1. **Visibility Manager**: Tracks curve visibility states
2. **UI Controller**: Manages checkbox/button states
3. **Signal Handler**: Propagates visibility changes
4. **State Persistence**: Saves/loads visibility preferences

**Recommended Implementation:**
```python
class CurveVisibilityManager:
    def __init__(self, plotter):
        self.plotter = plotter
        self.visibility_states = {}  # curve_name -> bool
        self.ui_controls = {}  # curve_name -> QCheckBox
        
    def toggle_curve(self, curve_name, visible=None):
        # Toggle single curve
        pass
        
    def toggle_group(self, curve_group, visible):
        # Toggle multiple curves
        pass
        
    def save_state(self):
        # Save to settings
        pass
        
    def load_state(self):
        # Load from settings
        pass
```

### 5. UI/UX Considerations for Curve Controls

**Recommended UI Design:**

**Primary Controls:**
1. **Checkbox List**: Color-coded checkboxes for each curve type
2. **Group Toggles**: "Show All Gamma", "Show All Density" buttons
3. **Quick Toggles**: Keyboard shortcuts (Ctrl+G, Ctrl+D, etc.)
4. **Context Menu**: Right-click on curves to toggle visibility
5. **Legend Integration**: Click legend items to toggle curves

**Layout Options:**
```
Option 1: Side Panel
┌─────────────────┐
│ ✓ Gamma (Purple)│
│ ✓ SS Density    │
│ ✓ LS Density    │
│ ✓ Caliper       │
│ [Show All]      │
│ [Hide All]      │
└─────────────────┘

Option 2: Toolbar
[Γ] [SS] [LS] [CAL] [All] [None]

Option 3: Legend Integration
Gamma ──────✓
SS Density ─✓
LS Density ─✓
```

**UX Best Practices:**
- Color coding matches curve colors
- Tooltips show curve names and ranges
- State persists between sessions
- Visual feedback when toggling
- Group operations for efficiency

## Specific Issue Diagnoses

### Issue 3: Curve Scaling Degradation During Vertical Scroll
**Root Cause**: Improper viewport height calculation in `scroll_to_depth`
**Fix**: Validate `current_height` and add bounds checking

### Issue 4: Gamma Ray Stationary Scrolling Bug  
**Root Cause**: Missing Y-axis link between gamma viewbox and main view
**Fix**: Add `self.gamma_viewbox.setYLink(self.plot_item.vb)`

### Issue 5: Curve Misalignment and Sizing Problems
**Root Cause**: 75:1 range ratio between gamma and density curves
**Fix**: Ensure dual-axis system works correctly, consider normalization options

### Issue 6: Missing Visibility Toggle Functionality
**Root Cause`: UI controls not connected to existing `set_curve_visibility` method
**Fix**: Implement visibility manager and connect UI controls

## Technical Recommendations

### Immediate Fixes (High Priority):
1. **Fix Gamma Ray Scrolling**: Add Y-axis linking in `setup_dual_axes()`
2. **Validate Scroll Calculations**: Add bounds checking in `scroll_to_depth()`
3. **Connect Visibility Toggles**: Implement basic UI controls for existing method

### Medium-Term Improvements:
1. **Enhanced Range Normalization**: Implement optional 0-1 normalization
2. **Smart Auto-ranging**: Add data-aware range adjustment
3. **Visibility State Persistence**: Save/load curve visibility preferences

### Long-Term Enhancements:
1. **Advanced Synchronization**: Improve viewport coordination between components
2. **Custom Range Settings**: Allow user-defined curve ranges
3. **Curve Grouping**: Logical grouping of related curves
4. **Export with Visibility**: Include visibility state in exports

## Code Changes Required

### 1. Fix Gamma Ray Scrolling Bug:
```python
# In PyQtGraphCurvePlotter.setup_dual_axes():
self.gamma_viewbox.setYLink(self.plot_item.vb)  # Add this line

# Also update update_gamma_view to handle scrolling:
def update_gamma_view_on_scroll():
    if self.gamma_viewbox:
        self.gamma_viewbox.setGeometry(self.plot_item.vb.sceneBoundingRect())
        self.gamma_viewbox.linkedViewChanged(self.plot_item.vb, self.gamma_viewbox.XAxis)
        self.gamma_viewbox.linkedViewChanged(self.plot_item.vb, self.gamma_viewbox.YAxis)

# Connect to view range changes:
self.plot_item.vb.sigRangeChanged.connect(update_gamma_view_on_scroll)
```

### 2. Fix Scroll Calculations:
```python
# In PyQtGraphCurvePlotter.scroll_to_depth():
def scroll_to_depth(self, depth):
    if self.data is None or self.data.empty:
        return
        
    # Get current view range
    view_range = self.plot_widget.viewRange()
    if len(view_range) < 2:
        return
        
    current_y_min = view_range[1][0]
    current_y_max = view_range[1][1]
    current_height = current_y_max - current_y_min
    
    # Validate current_height
    if current_height <= 0:
        # Use default height
        data_y_min = self.data[self.depth_column].min()
        data_y_max = self.data[self.depth_column].max()
        current_height = min(50.0, (data_y_max - data_y_min) * 0.1)
    
    # Calculate new view range centered on target depth
    new_y_min = depth - current_height / 2
    new_y_max = depth + current_height / 2
    
    # Ensure we don't go beyond data bounds
    data_y_min = self.data[self.depth_column].min()
    data_y_max = self.data[self.depth_column].max()
    
    if new_y_min < data_y_min:
        new_y_min = data_y_min
        new_y_max = new_y_min + current_height
        
    if new_y_max > data_y_max:
        new_y_max = data_y_max
        new_y_min = new_y_max - current_height
        
    # Apply new range
    self.plot_widget.setYRange(new_y_min, new_y_max)
```

### 3. Implement Visibility UI Controls:
```python
# Add to main_window.py or create new widget
class CurveVisibilityWidget(QWidget):
    def __init__(self, curve_plotter):
        super().__init__()
        self.curve_plotter = curve_plotter
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create checkboxes for each curve type
        self.checkboxes = {}
        curves = ['gamma', 'short_space_density', 'long_space_density', 'caliper']
        
        for curve in curves:
            cb = QCheckBox(f"Show {curve}")
            cb.setChecked(True)
            cb.toggled.connect(lambda checked, c=curve: self.toggle_curve(c, checked))
            layout.addWidget(cb)
            self.checkboxes[curve] = cb
            
        layout.addStretch()
        
    def toggle_curve(self, curve_name, visible):
        self.curve_plotter.set_curve_visibility(curve_name, visible)
```

## Conclusion

The LAS curve pane issues stem from three main areas:
1. **Dual-axis synchronization bugs** causing gamma ray scrolling problems
2. **Viewport calculation issues** leading to scaling degradation
3. **Missing UI integration** for existing visibility toggle functionality

The fixes are relatively straightforward but require careful implementation to ensure all components remain synchronized. The recommended approach is to address the critical scrolling bugs first, then implement the visibility UI, and finally enhance the range normalization system.

**Priority Order:**
1. Fix gamma ray scrolling bug (missing Y-axis link)
2. Fix scroll calculation validation
3. Implement basic visibility UI controls
4. Enhance range normalization options
5. Add advanced features (group toggles, persistence, etc.)