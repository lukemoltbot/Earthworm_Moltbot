# Earthworm Architecture
## Unified Viewport Implementation

**Documentation Date:** 2026-02-22  
**Git Commit:** [Latest unified viewport implementation]  
**Phase:** Post-Unification (Phases 0-6 Complete)

## Overview
Earthworm now features a unified geological analysis viewport that combines LAS curves display and Enhanced Stratigraphic Column display with pixel-perfect synchronization in a single viewport.

> **Note:** This document was originally written during the pre-unification phase (2026-02-18) and has been updated to reflect the completed unification.

## Unified Architecture
The `GeologicalAnalysisViewport` now serves as the central visualization component, providing:
- Side-by-side layout (68% curves, 32% column)
- Pixel-perfect synchronization (≤1 pixel drift)
- Professional geological software aesthetics
- Unified navigation and event handling

For detailed API documentation, see `Unified_Viewport_API.md`.
For migration guidance, see `Migration_Guide.md`.

---

*The following sections describe the original pre-unification architecture for historical context:*

## Pre-Unification State Analysis
**Original Date:** 2026-02-18  
**Original Commit:** 835d54c5a9563fe23c00fc234177303e5b73dcab  
**Phase:** Pre-Unification (Before Curve and Strat Unification)

## Original Overview
Original Earthworm architecture used separate components for LAS curves display and Enhanced Stratigraphic Column display. These components were synchronized programmatically but displayed in separate UI areas.

## Component Architecture

### Core Visualization Components
```
MainWindow
├── Analysis Workspace
│   ├── PyQtGraphCurvePlotter (LAS curves)
│   ├── EnhancedStratigraphicColumn (Strat column)
│   └── EditorTable (Data editor)
├── Overview Panel
└── Toolbars/Controls
```

### 1. PyQtGraphCurvePlotter
**Location:** `src/ui/widgets/pyqtgraph_curve_plotter.py`
**Purpose:** Display LAS well log curves using PyQtGraph
**Key Features:**
- Dual-axis support (Gamma on top, Density on bottom)
- Multiple curve types (Gamma, Density, Caliper, Resistivity)
- Zoom and scroll capabilities
- Curve visibility control
- Anomaly detection

**Dependencies:**
- PyQt6
- PyQtGraph
- NumPy
- Pandas

**Integration Points:**
- Connected to `zoom_state_manager` for synchronization
- Receives data from LAS loader
- Sends click events to editor table
- Controlled by `curve_visibility_manager`

### 2. EnhancedStratigraphicColumn
**Location:** `src/ui/widgets/enhanced_stratigraphic_column.py`
**Purpose:** Display stratigraphic column with lithology patterns
**Key Features:**
- Lithology patterns and colors
- Unit boundaries
- Depth scaling
- Tooltips with curve values
- SVG pattern support

**Dependencies:**
- PyQt6
- NumPy
- Pandas
- SVG rendering

**Integration Points:**
- Connected to `zoom_state_manager` for synchronization
- Receives lithology data from analysis
- Synchronized with curve plotter for depth
- Connected to editor table for boundary editing

### 3. ZoomStateManager
**Location:** `src/ui/widgets/zoom_state_manager.py`
**Purpose:** Synchronize zoom and scroll between components
**Key Features:**
- Manages zoom levels (0.5x to 10x)
- Coordinates scrolling between curve plotter and strat column
- Maintains engineering scales (1:100, 1:200, etc.)
- Provides zoom state signals

**Current Synchronization:**
- Programmatic synchronization via signals/slots
- Separate Y-axis ranges maintained in sync
- Potential for drift due to floating point calculations
- No pixel-perfect alignment guarantee

### 4. CurveVisibilityManager
**Location:** `src/ui/widgets/curve_visibility_manager.py`
**Purpose:** Manage visibility of LAS curves
**Key Features:**
- Toggle individual curve visibility
- Group visibility controls (all gamma, all density, etc.)
- Persistence of visibility state
- Integration with toolbar

### 5. MainWindow Integration
**Location:** `src/ui/main_window.py`
**Current Layout:**
```python
# Simplified layout structure
self.central_widget
├── self.main_splitter
│   ├── self.left_panel (Analysis workspace)
│   │   ├── self.curvePlotter (PyQtGraphCurvePlotter)
│   │   └── self.enhancedStratColumnView (EnhancedStratigraphicColumn)
│   └── self.right_panel (Editor/Overview)
│       ├── self.editorTable
│       └── self.overview widgets
└── Various toolbars and controls
```

## Signal/Slot Connections

### Curve Plotter → Other Components
```python
# In main_window.py
self.curvePlotter.pointClicked.connect(self._on_plot_point_clicked)
self.curvePlotter.viewRangeChanged.connect(self._on_plot_view_range_changed)
self.curvePlotter.boundaryDragged.connect(self._on_boundary_dragged)
self.curvePlotter.zoomLevelChanged.connect(self._on_zoom_level_changed)
```

### Strat Column → Other Components
```python
self.enhancedStratColumnView.depthClicked.connect(self._on_column_depth_clicked)
self.enhancedStratColumnView.viewRangeChanged.connect(self._on_column_view_range_changed)
```

### Zoom State Manager Connections
```python
self.zoom_state_manager.set_widgets(self.enhancedStratColumnView, self.curvePlotter)
self.zoom_state_manager.zoomStateChanged.connect(self._on_zoom_state_changed)
```

## Data Flow

### LAS File Loading
```
LAS File → LAS Parser → DataFrame → CurvePlotter.set_data()
                                  → EnhancedStratColumn.set_classified_data()
```

### Analysis Workflow
```
Raw Data → Analysis Worker → Units DataFrame → EnhancedStratColumn.draw_column()
         → Classified DataFrame → CurvePlotter.set_data()
                               → EditorTable.load_data()
```

### Synchronization Flow
```
User scroll/zoom → ZoomStateManager → CurvePlotter.setYRange()
                                   → EnhancedStratColumn.set_view_range()
```

## Performance Characteristics
**Baseline Metrics (from Phase 0):**
- Application startup: 0.06s
- Window creation: 1.38s
- Memory usage: ~133MB
- Data loading (5000 points): < 0.01s

**Synchronization Accuracy:**
- Programmatic synchronization via floating point calculations
- No pixel-level alignment guarantee
- Potential for visual drift at different zoom levels

## Limitations for Unification

### 1. Visual Separation
- Curve plotter and strat column in different UI areas
- Requires mental correlation by user
- No immediate visual comparison

### 2. Synchronization Limitations
- Separate scroll bars
- Potential for drift
- No pixel-perfect alignment

### 3. UI/UX Issues
- Professional geological software standards not fully met
- Layout differs from industry-standard tools like 1 Point Desktop
- Reduced information density due to separated components

### 4. Technical Debt
- Separate event handling for each component
- Duplicated scroll/zoom logic
- Complex signal/slot network for synchronization

## Files Requiring Modification for Unification

### Core New Components
1. `src/ui/widgets/geological_analysis_viewport.py` - NEW
2. `src/ui/widgets/unified_depth_scale_manager.py` - NEW
3. `src/ui/widgets/pixel_depth_mapper.py` - NEW

### Modified Components
1. `src/ui/widgets/pyqtgraph_curve_plotter.py` - Unified integration
2. `src/ui/widgets/enhanced_stratigraphic_column.py` - Unified integration
3. `src/ui/main_window.py` - Layout restructuring
4. `src/ui/widgets/zoom_state_manager.py` - Integration with unified manager
5. `src/ui/widgets/curve_visibility_manager.py` - Updated connections

### Test Files
1. `tests/test_unified_viewport.py` - NEW
2. `tests/test_pixel_synchronization.py` - NEW
3. `tests/test_visual_regression.py` - NEW
4. `tests/test_performance_benchmarks.py` - UPDATED

## Risk Assessment

### High Risk Areas
1. **Synchronization Engine** - Pixel-perfect alignment is technically challenging
2. **Performance** - Unified rendering must maintain or improve current performance
3. **Backward Compatibility** - Existing features must continue to work

### Medium Risk Areas
1. **UI Layout** - Restructuring main window layout
2. **Event Handling** - Unified mouse/keyboard events
3. **Visual Regression** - Maintaining current visual quality

### Low Risk Areas
1. **Component Wrapping** - Existing components can be reused with adapters
2. **Documentation** - Well-defined interfaces reduce risk
3. **Testing** - Comprehensive test suite provides safety net

## Migration Strategy

### Phase 1: Wrapper Approach
Create `GeologicalAnalysisViewport` that wraps existing components
- Minimal changes to existing code
- Gradual migration path
- Easy rollback if needed

### Phase 2: Integration
Connect components through unified manager
- Maintain existing APIs where possible
- Add new unified interfaces
- Deprecate old patterns gradually

### Phase 3: Optimization
Optimize for performance and pixel accuracy
- Replace floating point with integer pixel math
- Implement viewport caching
- Optimize event handling

## Success Metrics for Unification

### Quantitative
1. Pixel alignment accuracy: ≤1 pixel drift
2. Performance: ≥60 FPS scrolling, <100ms zoom response
3. Memory: <10% increase from baseline (133MB → <146MB)
4. Startup time: <20% increase from baseline (1.38s → <1.66s)

### Qualitative
1. Professional geological software appearance
2. Immediate visual correlation between curves and lithology
3. Reduced cognitive load for users
4. Industry-standard workflow compatibility

## Next Steps
1. **Phase 1 Implementation** - Create `GeologicalAnalysisViewport` skeleton
2. **Component Integration** - Wrap existing components in unified viewport
3. **Synchronization Engine** - Implement pixel-perfect depth alignment
4. **Testing & Validation** - Verify all metrics and requirements met

---

*This document will be updated as unification progresses. Last updated: 2026-02-18*