# Unified Geological Analysis Viewport - API Documentation

**Documentation Date:** 2026-02-22  
**Git Commit:** [Latest unified viewport implementation]  
**Phase:** Post-Unification (Phase 6)

## Overview

The `GeologicalAnalysisViewport` is the central component of Earthworm's unified visualization system. It combines LAS curve display and stratigraphic column display with pixel-perfect synchronization in a single, professional geological analysis viewport.

### Architecture Diagram
```
┌─────────────────────────────────────────────┐
│ GeologicalAnalysisViewport                  │
│ ┌─────────────┬──────────────────────────┐ │
│ │             │                          │ │
│ │  Strat      │       LAS Curves         │ │
│ │  Column     │                          │ │
│ │  (32%)      │        (68%)             │ │
│ │             │                          │ │
│ └─────────────┴──────────────────────────┘ │
│          Unified Scroll/Depth              │
└─────────────────────────────────────────────┘
```

## Class Definition

```python
class GeologicalAnalysisViewport(QWidget):
    """Unified viewport for geological analysis."""
```

## Signals

### `depthChanged`
**Signature:** `depthChanged = pyqtSignal(float)`
**Description:** Emitted when the current depth position changes.
**Parameters:**
- `depth` (float): The new current depth in meters.

### `viewRangeChanged`
**Signature:** `viewRangeChanged = pyqtSignal(float, float)`
**Description:** Emitted when the visible depth range changes.
**Parameters:**
- `min_depth` (float): Minimum visible depth in meters.
- `max_depth` (float): Maximum visible depth in meters.

### `zoomLevelChanged`
**Signature:** `zoomLevelChanged = pyqtSignal(float)`
**Description:** Emitted when the zoom level changes.
**Parameters:**
- `zoom_level` (float): New zoom level (1.0 = 100%).

### `pointClicked`
**Signature:** `pointClicked = pyqtSignal(float, dict)`
**Description:** Emitted when a point is clicked in the viewport.
**Parameters:**
- `depth` (float): Depth of the clicked point in meters.
- `data` (dict): Additional data about the click (source, curve type, etc.).

### `boundaryDragged`
**Signature:** `boundaryDragged = pyqtSignal(int, str, float)`
**Description:** Emitted when a stratigraphic boundary is dragged.
**Parameters:**
- `row_index` (int): Index of the edited row in the editor table.
- `boundary_type` (str): Type of boundary ('top' or 'bottom').
- `new_depth` (float): New depth position of the boundary in meters.

### `curveVisibilityChanged`
**Signature:** `curveVisibilityChanged = pyqtSignal(str, bool)`
**Description:** Emitted when curve visibility changes.
**Parameters:**
- `curve_name` (str): Name of the curve (e.g., 'gamma', 'density').
- `visible` (bool): New visibility state.

## Constructor

### `__init__`
```python
def __init__(self, parent: Optional[QWidget] = None):
```

**Description:** Initialize the unified viewport.

**Parameters:**
- `parent` (Optional[QWidget]): Parent widget (default: None).

**Initialization Steps:**
1. Sets up default configuration (`ViewportConfig`)
2. Initializes scrolling synchronization engine
3. Sets up component adapter for integration
4. Configures UI layout and connections

## Configuration

### ViewportConfig Dataclass
The viewport uses a `ViewportConfig` dataclass for configuration:

```python
@dataclass
class ViewportConfig:
    curve_width_ratio: float = 0.68      # 68% for curves
    column_width_ratio: float = 0.32     # 32% for strat column
    min_curve_width: int = 350           # pixels
    min_column_width: int = 220          # pixels
    pixel_tolerance: int = 1             # 1-pixel tolerance target
    enable_viewport_caching: bool = True
    cache_size_mb: int = 50
    background_color: str = "#FFFFFF"
    grid_line_color: str = "#E0E0E0"
    grid_line_width: int = 1
    font_family: str = "Sans Serif"
    axis_label_size: int = 9             # points
    title_size: int = 11                 # points
    tick_label_size: int = 8             # points
```

**Geological Color Palette:**
```python
geological_colors = {
    'gamma': '#8b008b',      # Purple
    'density': '#0066cc',    # Blue
    'caliper': '#ffa500',    # Orange
    'resistivity': '#ff0000', # Red
    'background': '#FFFFFF',  # White
    'grid': '#E0E0E0',       # Light gray
    'text': '#000000',       # Black
    'highlight': '#FFFF00',  # Yellow for highlights
}
```

## Public Methods

### `set_components`
```python
def set_components(self, curve_plotter, strat_column, depth_manager, pixel_mapper) -> None:
```

**Description:** Set the component instances for the unified viewport.

**Parameters:**
- `curve_plotter`: PyQtGraphCurvePlotter instance for LAS curve display
- `strat_column`: EnhancedStratigraphicColumn instance for stratigraphic display
- `depth_manager`: UnifiedDepthScaleManager instance for depth synchronization
- `pixel_mapper`: PixelDepthMapper instance for pixel-depth conversion

**Usage:**
```python
viewport.set_components(
    curve_plotter=curve_plotter,
    strat_column=strat_column,
    depth_manager=depth_manager,
    pixel_mapper=pixel_mapper
)
```

### `set_curve_visibility`
```python
def set_curve_visibility(self, curve_name: str, visible: bool) -> None:
```

**Description:** Set visibility of a specific curve.

**Parameters:**
- `curve_name` (str): Name of the curve ('gamma', 'density', 'caliper', 'resistivity')
- `visible` (bool): Whether the curve should be visible

### `set_depth_range`
```python
def set_depth_range(self, min_depth: float, max_depth: float) -> None:
```

**Description:** Set the visible depth range.

**Parameters:**
- `min_depth` (float): Minimum depth in meters
- `max_depth` (float): Maximum depth in meters

**Notes:**
- Updates all synchronized components
- Emits `viewRangeChanged` signal

### `set_current_depth`
```python
def set_current_depth(self, depth: float) -> None:
```

**Description:** Set the current depth position.

**Parameters:**
- `depth` (float): Current depth in meters

**Notes:**
- Updates cursor positions in all components
- Emits `depthChanged` signal

### `set_zoom_level`
```python
def set_zoom_level(self, zoom: float) -> None:
```

**Description:** Set the zoom level.

**Parameters:**
- `zoom` (float): Zoom level (1.0 = 100%, 2.0 = 200%, 0.5 = 50%)

**Notes:**
- Updates zoom state in all synchronized components
- Emits `zoomLevelChanged` signal

### `get_viewport_rect`
```python
def get_viewport_rect(self) -> QRect:
```

**Description:** Get the viewport rectangle in widget coordinates.

**Returns:**
- `QRect`: Rectangle defining the viewport area

### `get_pixel_for_depth`
```python
def get_pixel_for_depth(self, depth: float) -> Optional[int]:
```

**Description:** Convert depth to pixel position.

**Parameters:**
- `depth` (float): Depth in meters

**Returns:**
- `Optional[int]`: Pixel position, or None if conversion fails

### `get_depth_for_pixel`
```python
def get_depth_for_pixel(self, pixel: int) -> Optional[float]:
```

**Description:** Convert pixel position to depth.

**Parameters:**
- `pixel` (int): Pixel position

**Returns:**
- `Optional[float]`: Depth in meters, or None if conversion fails

### `check_synchronization`
```python
def check_synchronization(self) -> Dict[str, Any]:
```

**Description:** Check synchronization status between components.

**Returns:**
- `Dict[str, Any]`: Dictionary containing synchronization metrics:
  - `in_sync` (bool): Whether components are synchronized
  - `max_pixel_drift` (int): Maximum pixel drift
  - `component_states` (dict): Individual component states
  - `performance_metrics` (dict): Performance metrics

## Properties

### `depth_range`
**Type:** `Optional[Tuple[float, float]]`
**Description:** Get current depth range.

### `current_depth`
**Type:** `Optional[float]`
**Description:** Get current depth position.

### `zoom_level`
**Type:** `float`
**Description:** Get current zoom level.

### `curve_width`
**Type:** `int`
**Description:** Get current curve area width in pixels.

### `column_width`
**Type:** `int`
**Description:** Get current column area width in pixels.

## Integration with Existing Components

### PyQtGraphCurvePlotter Integration
The unified viewport wraps the existing `PyQtGraphCurvePlotter` with:
- Removal of individual scroll bars
- Connection to unified depth synchronization
- Forwarding of click and range change signals

### EnhancedStratigraphicColumn Integration
The unified viewport wraps the existing `EnhancedStratigraphicColumn` with:
- Integration into side-by-side layout
- Synchronized scrolling and zooming
- Boundary drag event forwarding

### ZoomStateManager Integration
The unified viewport connects to `ZoomStateManager` for:
- Bidirectional zoom level synchronization
- Depth range coordination
- Performance-optimized updates

## Performance Characteristics

### Synchronization Performance
- **Target FPS:** 60+ FPS during smooth scrolling
- **Response Time:** < 100ms for zoom changes
- **Memory Usage:** < 50MB additional memory
- **Data Capacity:** Optimized for 10,000 data points

### Pixel Accuracy
- **Tolerance:** ≤1 pixel maximum drift
- **Mapping:** Integer pixel math for precise alignment
- **Validation:** Continuous synchronization checking

## Event Handling

### Mouse Events
- **Wheel Events:** Unified scrolling across all components
- **Click Events:** Propagated to appropriate component with depth information
- **Drag Events:** Boundary dragging forwarded to editor table

### Keyboard Events
- **Navigation:** Arrow keys for depth navigation
- **Zoom:** +/- keys for zoom control
- **Shortcuts:** Preserved from existing components

## Usage Example

```python
from src.ui.widgets.unified_viewport.geological_analysis_viewport import GeologicalAnalysisViewport
from src.ui.widgets.pyqtgraph_curve_plotter import PyQtGraphCurvePlotter
from src.ui.widgets.enhanced_stratigraphic_column import EnhancedStratigraphicColumn
from src.ui.widgets.unified_viewport.unified_depth_scale_manager import UnifiedDepthScaleManager
from src.ui.widgets.unified_viewport.pixel_depth_mapper import PixelDepthMapper

# Create components
curve_plotter = PyQtGraphCurvePlotter()
strat_column = EnhancedStratigraphicColumn()
depth_manager = UnifiedDepthScaleManager()
pixel_mapper = PixelDepthMapper()

# Create unified viewport
viewport = GeologicalAnalysisViewport()

# Connect components
viewport.set_components(
    curve_plotter=curve_plotter,
    strat_column=strat_column,
    depth_manager=depth_manager,
    pixel_mapper=pixel_mapper
)

# Configure viewport
viewport.set_depth_range(0, 500)
viewport.set_curve_visibility('gamma', True)
viewport.set_curve_visibility('density', True)

# Connect signals
viewport.viewRangeChanged.connect(lambda min_d, max_d: print(f"Range: {min_d}-{max_d}m"))
viewport.pointClicked.connect(lambda depth, data: print(f"Clicked at {depth}m"))
```

## Migration from Separated Components

### Before (Separated):
```python
# Old layout with separate components
layout.addWidget(curve_plotter)   # 100% width
layout.addWidget(strat_column)    # 100% width, below curves
```

### After (Unified):
```python
# New layout with unified viewport
layout.addWidget(viewport)  # Single unified widget
```

### Benefits:
1. **Pixel-perfect synchronization** (vs. potential drift)
2. **Professional side-by-side layout** (vs. stacked layout)
3. **Unified event handling** (vs. separate event handlers)
4. **Improved visual correlation** between curves and lithology

## Testing

### Unit Tests
- `tests/test_unified_viewport_integration.py`: Basic integration tests
- `tests/test_phase5_workflow_validation.py`: Geological workflow validation

### Performance Tests
- `tests/test_phase3_performance.py`: Synchronization performance
- `tests/test_pixel_alignment.py`: Pixel accuracy validation

### Integration Tests
- `tests/test_scroll_sync_integration.py`: Scrolling synchronization
- `tests/test_earthworm_headless.py`: End-to-end application testing

## Known Issues & Limitations

### 1. Scrolling with No Data
**Issue:** `EnhancedStratigraphicColumn.scroll_to_depth()` fails when no geological data is loaded.
**Root Cause:** Scene height < viewport height when empty, causing scroll_max = 0.
**Workaround:** Load geological data before programmatic scrolling.
**Status:** Pre-existing issue, does not affect production usage with data.

### 2. Headless Visual Regression Testing
**Limitation:** Cannot capture visual output without physical display.
**Workaround:** Functional testing instead of pixel comparison.
**Status:** Documented limitation for CI/CD environments.

### 3. Test Suite Segmentation Fault
**Issue:** Intermittent segfault when running full test suite.
**Root Cause:** Suspected Qt object lifecycle/cross-test pollution.
**Workaround:** Run tests in isolation or fix test fixture cleanup.
**Status:** Under investigation (Bug Fix Protocol Attempt 3).

## Extension Guide

### Adding New Visualization Components
1. Implement component with standard Qt widget interface
2. Create adapter in `component_adapter.py`
3. Register component with `UnifiedDepthScaleManager`
4. Add to `GeologicalAnalysisViewport.set_components()`

### Customizing Layout Ratios
Override `ViewportConfig`:
```python
config = ViewportConfig(
    curve_width_ratio=0.75,  # 75% curves
    column_width_ratio=0.25,  # 25% column
    min_curve_width=400,
    min_column_width=200
)
```

### Adding New Curve Types
1. Add color to `ViewportConfig.geological_colors`
2. Update curve loading in `PyQtGraphCurvePlotter`
3. Add visibility control in toolbar

---

*Last Updated: 2026-02-22*  
*Part of Earthworm Curve and Strat Unification Project (Phases 0-6)*