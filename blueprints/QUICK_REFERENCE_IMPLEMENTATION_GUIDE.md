# QUICK REFERENCE: Implementation Guide for AI Coder
## 1 Point Desktop UI Replication in Earthworm

---

## BEFORE YOU START

**Read These in Order:**
1. COMPREHENSIVE_DEVELOPMENT_PLAN.md (the main guide)
2. This file (quick reference while coding)
3. Use analysis.md when you need architecture clarification

**Golden Rules:**
1. There is ONE and ONLY ONE coordinate system (`DepthCoordinateSystem`)
2. There is ONE and ONLY ONE state manager (`DepthStateManager`)
3. All components read from these, never cache position/coordinate data
4. All user interactions update the central state first, then everything else follows

---

## ARCHITECTURE AT A GLANCE

```
┌─── DepthStateManager (Central State) ───┐
│                                          │
│  Properties:                             │
│  - _viewport_range: DepthRange          │
│  - _cursor_depth: float                 │
│  - _selection_range: DepthRange         │
│                                          │
│  Signals (all components listen):       │
│  - viewportRangeChanged                 │
│  - cursorDepthChanged                   │
│  - selectionRangeChanged                │
│  - zoomLevelChanged                     │
│                                          │
└──────────────────────────────────────────┘
         ▲                        ▲
         │                        │
   All components:          DepthCoordinateSystem
   - Listen to signals      - depthToScreenY()
   - Call state methods     - screenYToDepth()
   - Update when signals    - depthToPixelHeight()
     are emitted            - set_depth_range()
```

---

## STEP-BY-STEP IMPLEMENTATION ORDER

### Step 1: Create DepthStateManager
**File**: `src/ui/graphic_window/state/depth_state_manager.py`

```python
class DepthStateManager(QObject):
    # Signals
    viewportRangeChanged = pyqtSignal(DepthRange)
    cursorDepthChanged = pyqtSignal(float)
    selectionRangeChanged = pyqtSignal(DepthRange)
    zoomLevelChanged = pyqtSignal(float)
    
    # Methods
    def set_viewport_range(from_depth, to_depth) → None
    def set_cursor_depth(depth) → None
    def set_selection_range(from_depth, to_depth) → None
    def scroll_viewport(delta) → None
    # ... etc
```

**Test**: Write unit tests that verify signals are emitted when state changes.

### Step 2: Create DepthCoordinateSystem
**File**: `src/ui/graphic_window/state/depth_coordinate_system.py`

```python
class DepthCoordinateSystem:
    # Core methods (MUST BE IDENTICAL across all uses)
    def depth_to_screen_y(depth: float) → float
    def screen_y_to_depth(screen_y: float) → float
    def depth_thickness_to_pixel_height(thickness: float) → float
    
    # Setup
    def set_depth_range(min_depth, max_depth) → None
```

**Test**: Create alignment test that verifies round-trip conversions work:
```python
depth = 90.5
screen_y = coord_sys.depth_to_screen_y(depth)
back = coord_sys.screen_y_to_depth(screen_y)
assert abs(back - depth) < 0.001  # Must be nearly identical
```

### Step 3: Create Data Models
**Files**:
- `src/core/graphic_models/lithology_interval.py`
- `src/core/graphic_models/las_point.py`
- `src/core/graphic_models/hole_data_provider.py`

These hold your data and provide access. Keep them simple and dumb.

### Step 4: Create StratigraphicColumn Component
**File**: `src/ui/graphic_window/components/stratigraphic_column.py`

**Key points:**
```python
class StratigraphicColumn(QWidget):
    def __init__(self, data_provider, depth_state, depth_coords):
        # MUST subscribe to ALL state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
    
    def on_viewport_changed(self, depth_range):
        # Update coordinates AND repaint
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()  # This triggers paintEvent()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        
        for interval in self.lithology_intervals:
            # GET Y POSITION FROM COORDINATE SYSTEM
            screen_y1 = self.coords.depth_to_screen_y(interval.from_depth)
            screen_y2 = self.coords.depth_to_screen_y(interval.to_depth)
            
            # Draw rectangle
            rect = QRect(10, screen_y1, width, screen_y2 - screen_y1)
            painter.fillRect(rect, color)
    
    def mousePressEvent(self, event):
        # Convert click to depth
        depth = self.coords.screen_y_to_depth(event.y())
        
        # Find interval
        interval = find_interval_at_depth(depth)
        
        # UPDATE STATE (NOT LOCAL DATA!)
        self.state.set_selection_range(interval.from_depth, interval.to_depth)
```

### Step 5: Create LASCurvesDisplay Component
**File**: `src/ui/graphic_window/components/las_curves_display.py`

**Key pattern** (same as StratigraphicColumn):
```python
class LASCurvesDisplay(QWidget):
    def __init__(self, data_provider, depth_state, depth_coords):
        # Subscribe to same signals
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        # ... etc
    
    def paintEvent(self, event):
        for point in self.las_points:
            # Use SAME coordinate system
            screen_y = self.coords.depth_to_screen_y(point.depth)
            screen_x = self.value_to_screen_x(point.gamma)  # Separate for values
            
            # Draw curve line
```

### Step 6: Create LithologyDataTable Component
**File**: `src/ui/graphic_window/components/lithology_data_table.py`

```python
class LithologyDataTable(QWidget):
    def __init__(self, data_provider, depth_state, depth_coords):
        self.table = QTableWidget()
        
        # Subscribe to state changes
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
    
    def on_selection_changed(self, depth_range):
        # Find which rows match this depth range
        row_index = find_row_for_depth(depth_range.from_depth)
        
        # Select that row in table
        self.table.selectRow(row_index)
    
    def on_row_selected(self, row_index):
        # Get depth from row
        interval = self.data.get_lithology_intervals()[row_index]
        
        # UPDATE CENTRAL STATE
        self.state.set_selection_range(interval.from_depth, interval.to_depth)
        self.state.set_cursor_depth(interval.from_depth)
```

### Step 7: Create Main Composite Window
**File**: `src/ui/graphic_window/unified_graphic_window.py`

```python
class UnifiedGraphicWindow(QMainWindow):
    def __init__(self, hole_data_provider):
        # Create state managers (SINGLE INSTANCES)
        self.depth_state = DepthStateManager(min_depth, max_depth)
        self.depth_coords = DepthCoordinateSystem(height=600, width=800)
        
        # Create components (pass state managers to ALL)
        self.strat_col = StratigraphicColumn(data, self.depth_state, self.depth_coords)
        self.las_curves = LASCurvesDisplay(data, self.depth_state, self.depth_coords)
        self.table = LithologyDataTable(data, self.depth_state, self.depth_coords)
        
        # Add to layout
        # All components now automatically sync!
```

---

## COMMON PATTERNS

### Pattern 1: Responding to State Changes

```python
class MyComponent(QWidget):
    def __init__(self, depth_state_manager):
        self.state = depth_state_manager
        
        # Connect to signals
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
    
    def on_viewport_changed(self, depth_range):
        # Update coordinate system
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        
        # Trigger repaint
        self.update()  # Calls paintEvent()
```

### Pattern 2: User Interaction Updates State

```python
def mousePressEvent(self, event):
    # Get position
    screen_y = event.y()
    
    # Convert to depth using coordinate system
    depth = self.coords.screen_y_to_depth(screen_y)
    
    # DO NOT update local data
    # DO update central state
    self.state.set_cursor_depth(depth)  # This triggers all updates
```

### Pattern 3: Drawing with Coordinate System

```python
def paintEvent(self, event):
    painter = QPainter(self)
    
    for item in self.items:
        # Convert depth to screen
        screen_y = self.coords.depth_to_screen_y(item.depth)
        
        # Convert thickness to height
        height = self.coords.depth_thickness_to_pixel_height(item.thickness)
        
        # Draw
        painter.fillRect(x, screen_y, width, height, color)
```

---

## TESTING CHECKLIST

After implementing each component:

```python
# Test 1: State Updates
def test_state_updates():
    state = DepthStateManager(0, 100)
    
    state.set_cursor_depth(50.0)
    assert state.get_cursor_depth() == 50.0

# Test 2: Signals Emitted
def test_signals_emitted():
    state = DepthStateManager(0, 100)
    
    signal_received = False
    def on_signal(depth):
        nonlocal signal_received
        signal_received = True
    
    state.cursorDepthChanged.connect(on_signal)
    state.set_cursor_depth(50.0)
    
    assert signal_received

# Test 3: Coordinate Consistency
def test_coordinate_consistency():
    coords = DepthCoordinateSystem(600, 800)
    coords.set_depth_range(87, 98)
    
    test_depth = 90.5
    screen_y = coords.depth_to_screen_y(test_depth)
    back_depth = coords.screen_y_to_depth(screen_y)
    
    assert abs(back_depth - test_depth) < 0.001

# Test 4: Component Synchronization
def test_components_sync():
    state = DepthStateManager(0, 100)
    coords = DepthCoordinateSystem(600, 800)
    
    # Create two components
    comp1 = MyComponent(state, coords)
    comp2 = OtherComponent(state, coords)
    
    # Change state
    state.set_cursor_depth(50.0)
    
    # Both should show depth 50.0
    assert comp1.shown_depth == 50.0
    assert comp2.shown_depth == 50.0
```

---

## DEBUGGING CHECKLIST

If components don't synchronize:

1. **Check signals are connected**
   ```python
   # In __init__:
   self.state.viewportRangeChanged.connect(self.on_viewport_changed)
   # Not: self.state.on_viewport_changed.connect(...)  WRONG!
   ```

2. **Check signal handlers exist**
   ```python
   # Must have matching handler
   def on_viewport_changed(self, depth_range):
       self.update()
   ```

3. **Check coordinate system is updated**
   ```python
   def on_viewport_changed(self, depth_range):
       # THIS LINE IS CRITICAL
       self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
       self.update()
   ```

4. **Check you're using the shared coordinate system**
   ```python
   # RIGHT:
   screen_y = self.coords.depth_to_screen_y(depth)
   
   # WRONG:
   screen_y = self.my_custom_function(depth)
   ```

5. **Check state is updated, not local data**
   ```python
   # RIGHT:
   self.state.set_cursor_depth(depth)
   
   # WRONG:
   self.cursor_depth = depth  # Local copy!
   ```

---

## QUICK IMPLEMENTATION REFERENCE

### DepthStateManager Methods

```python
# Viewport
state.set_viewport_range(from_depth, to_depth)
state.get_viewport_range() → DepthRange
state.scroll_viewport(delta) → None
state.center_on_depth(depth) → None

# Cursor
state.set_cursor_depth(depth) → None
state.get_cursor_depth() → float

# Selection
state.set_selection_range(from_depth, to_depth) → None
state.get_selection_range() → DepthRange
state.clear_selection() → None

# Zoom
state.set_zoom_level(zoom) → None
state.get_zoom_level() → float
state.zoom_in(factor) → None
state.zoom_out(factor) → None
```

### DepthCoordinateSystem Methods

```python
# Setup
coords.set_depth_range(min_depth, max_depth) → None
coords.apply_zoom(zoom_level) → None

# Conversions (THE MOST IMPORTANT)
coords.depth_to_screen_y(depth) → float
coords.screen_y_to_depth(screen_y) → float
coords.depth_thickness_to_pixel_height(thickness) → float

# Info
coords.get_pixels_per_meter() → float
coords.get_viewable_depth_range() → Tuple[float, float]
coords.get_usable_canvas_area() → Tuple[float, float, float, float]
```

---

## FILE STRUCTURE TO CREATE

```
src/ui/graphic_window/
├── __init__.py
├── unified_graphic_window.py          # Main window ← START HERE LAST
├── state/
│   ├── __init__.py
│   ├── depth_state_manager.py        # ← START HERE FIRST
│   └── depth_coordinate_system.py    # ← START HERE SECOND
├── components/
│   ├── __init__.py
│   ├── stratigraphic_column.py       # ← THEN HERE
│   ├── las_curves_display.py         # ← THEN HERE
│   ├── lithology_data_table.py       # ← THEN HERE
│   ├── preview_window.py             # ← THEN HERE
│   └── information_panel.py          # ← THEN HERE
└── styles/
    └── graphic_window_styles.py       # Optional QSS
```

---

## IMPORT PATTERN

All files should start with:

```python
# Type hints
from typing import List, Optional, Tuple, Dict

# PyQt6
from PyQt6.QtWidgets import QWidget, QPushButton, QTableWidget
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QPainter, QPen, QColor

# Project
from ...core.graphic_models import LithologyInterval, LASPoint, HoleDataProvider
from .state import DepthStateManager, DepthCoordinateSystem, DepthRange
```

---

## DEBUGGING: THE MISALIGNMENT TEST

If components are misaligned, run this test:

```python
def test_alignment():
    """Test that strat column and curves use same vertical positioning"""
    
    # Create shared managers
    state = DepthStateManager(87, 98)
    coords = DepthCoordinateSystem(600, 800)
    
    # Create components
    strat = StratigraphicColumn(data, state, coords)
    curves = LASCurvesDisplay(data, state, coords)
    
    # Set viewport
    state.set_viewport_range(87, 98)
    
    # Check same depth maps to same screen position
    test_depth = 90.5
    
    strat_y = strat.coords.depth_to_screen_y(test_depth)
    curves_y = curves.coords.depth_to_screen_y(test_depth)
    
    print(f"Strat column Y: {strat_y}")
    print(f"Curves Y: {curves_y}")
    print(f"Difference: {abs(strat_y - curves_y)} pixels")
    
    # Must be ZERO (same coordinate system)
    assert strat_y == curves_y, "MISALIGNMENT DETECTED"
```

If this fails, verify:
1. Both components are using the SAME `self.coords` object
2. NOT creating separate coordinate systems
3. Both have called `coords.set_depth_range()` with same values

---

## FINAL CHECKLIST BEFORE HANDING TO AI CODER

- [ ] Read entire COMPREHENSIVE_DEVELOPMENT_PLAN.md
- [ ] Understand state manager pattern
- [ ] Understand coordinate system is shared by all
- [ ] All user interactions update central state first
- [ ] All components subscribe to state signals
- [ ] Implement in order: state → models → components → window
- [ ] Test component synchronization after each component
- [ ] Verify alignment test passes before moving forward
- [ ] Use the provided code snippets as templates

**Key Mantra**: "One state, one coordinate system, all components listen and respond."
