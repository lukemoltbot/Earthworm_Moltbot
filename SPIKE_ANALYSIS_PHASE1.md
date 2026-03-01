# PHASE 1: SPIKE ANALYSIS - System A Migration

**Date:** 2026-03-01  
**Duration:** 1 hour  
**Status:** COMPLETE  

---

## EXECUTIVE SUMMARY

The codebase is currently using **System B** (UnifiedDepthScaleManager) for viewport management, but **System A** (DepthStateManager) already exists and is fully implemented. The migration requires wiring System A into the existing widgets and replacing System B references in the main window.

---

## CURRENT STATE ANALYSIS

### System B (UnifiedDepthScaleManager) - ACTIVE
Located in: `src/ui/widgets/unified_viewport/`

**Files:**
- `unified_depth_scale_manager.py` - Synchronization engine
- `pixel_depth_mapper.py` - Pixel-accurate depth mapping
- `geological_analysis_viewport.py` - Main container widget
- `component_adapter.py` - Helper utilities

**Usage in codebase:**
- `src/ui/main_window.py:HoleEditorWindow` creates and uses:
  - `self.unified_depth_manager = UnifiedDepthScaleManager(depth_config)`
  - `self.unified_pixel_mapper = PixelDepthMapper(pixel_config)`
  - `self.unifiedViewport = GeologicalAnalysisViewport()`

**Signal Flow:**
- Incomplete: handlers don't propagate updates bidirectionally
- Result: Widgets scroll independently

### System A (DepthStateManager) - READY TO USE
Located in: `src/ui/graphic_window/state/`

**Files:**
- `depth_state_manager.py` - Central state manager (COMPLETE)
- `depth_range.py` - DepthRange dataclass
- `depth_coordinate_system.py` - Coordinate transformation
- `__init__.py` - Module exports

**Key Signals in DepthStateManager:**
```python
viewportRangeChanged = pyqtSignal(DepthRange)      # Visible range changed
cursorDepthChanged = pyqtSignal(float)              # Cursor changed
selectionRangeChanged = pyqtSignal(object)         # Selection changed
zoomLevelChanged = pyqtSignal(float)                # Zoom changed
```

**Key Methods:**
- `set_viewport_range(from_depth, to_depth)` - Update visible range
- `set_cursor_depth(depth, snap=True)` - Update cursor
- `set_zoom_level(zoom)` - Update zoom factor
- `handle_wheel_event(delta, ctrl_pressed)` - Handle scroll events

**Status:** Already integrated with ScrollSynchronizer, SelectionSynchronizer, DepthSynchronizer

---

## BREAKING CHANGE ANALYSIS

### Files That Must Be Modified (In Phase Order)

#### **PHASE 2: EnhancedStratigraphicColumn**
File: `src/ui/widgets/enhanced_stratigraphic_column.py`

**Current State:**
- Has TYPE_CHECKING import for DepthStateManager
- Constructor accepts optional `depth_state_manager` parameter
- Already has signal connections started (lines ~80-85)
- Signal handlers partially defined (lines ~206-224)

**What's Missing:**
- [ ] Handlers don't call `self.viewport().update()` to trigger redraw
- [ ] Scroll/wheel event wiring to state manager incomplete
- [ ] Click events don't update state manager cursor

**Breaking Points:**
- Comment at line ~47: "Skip scaling when column is part of unified viewport (scaling managed by UnifiedDepthScaleManager)" - needs updating

#### **PHASE 3: PyQtGraphCurvePlotter**
File: `src/ui/widgets/pyqtgraph_curve_plotter.py`

**Current State:**
- Constructor takes `parent=None` only
- NO DepthStateManager parameter

**What's Needed:**
- [ ] Add `depth_state_manager` parameter to `__init__`
- [ ] Connect state manager signals
- [ ] Implement handlers for viewport/cursor/zoom changes
- [ ] Wire scroll events to state manager

**Breaking Points:**
- Uses local Y-axis range management (line ~118 `self.max_depth = 100.0`)
- Wheel event handling in `wheelEvent()` method (around line ~500+)
- Needs bidirectional communication

#### **PHASE 4: HoleEditorWindow (main_window.py)**
File: `src/ui/main_window.py:HoleEditorWindow.__init__`

**Current State:**
```python
# Lines ~290-310
self.curvePlotter = PyQtGraphCurvePlotter()
self.enhancedStratColumnView = EnhancedStratigraphicColumn()

self.unified_depth_manager = UnifiedDepthScaleManager(depth_config)
self.unified_pixel_mapper = PixelDepthMapper(pixel_config)
self.unifiedViewport = GeologicalAnalysisViewport()
self.unifiedViewport.set_components(...)
```

**What's Needed:**
- [ ] Create `self.depth_state_manager = DepthStateManager()` 
- [ ] Pass it to both widgets
- [ ] Comment out or remove all System B instantiations
- [ ] Replace `self.unifiedViewport = GeologicalAnalysisViewport()` with System A container

**Breaking Points:**
- Lines ~291-310 (System B instantiation)
- Lines ~338-341 (Zoom state manager connections)
- All zoom control wiring

#### **PHASE 5: UnifiedGraphicWindow**
File: `src/ui/graphic_window/unified_graphic_window.py`

**Current State:**
- Likely exists but needs verification
- Should create synchronizer instances
- Should wire all signals

**What's Needed:**
- [ ] Verify synchronizers created
- [ ] Verify signal wiring complete
- [ ] Check for circular signal loops

#### **PHASE 6: System B Deprecation**
Files: `src/ui/widgets/unified_viewport/*.py`

**What's Needed:**
- [ ] Add deprecation warnings to all System B classes
- [ ] Extract utility functions that System A needs
- [ ] Comment out all active imports of System B

---

## SIGNAL FLOW DIAGRAM

### CURRENT (System B) - BROKEN
```
User Scroll in CurvePlotter
    ↓ (wheelEvent)
PyQtGraphCurvePlotter (internal state updates)
    ↓ (viewRangeChanged signal)
GeologicalAnalysisViewport
    ↓ (incomplete handler)
EnhancedStratigraphicColumn (does NOT update)
    ↓ (STUCK HERE - no feedback)

Result: Strat column scrolls independently
```

### TARGET (System A) - BROADCAST
```
User Scroll in CurvePlotter
    ↓ (wheelEvent)
PyQtGraphCurvePlotter.wheelEvent()
    ↓ (calls)
DepthStateManager.set_viewport_range(new_min, new_max)
    ↓ (emits)
viewportRangeChanged(DepthRange)
    ├→ EnhancedStratigraphicColumn._on_state_viewport_changed() [redraws]
    ├→ PyQtGraphCurvePlotter._on_state_viewport_changed() [updates Y-axis]
    └→ Any other component listening

Same for click events:
User Click in EnhancedStratigraphicColumn
    ↓ (mousePressEvent)
EnhancedStratigraphicColumn.mousePressEvent()
    ↓ (calls)
DepthStateManager.set_cursor_depth(clicked_depth)
    ↓ (emits)
cursorDepthChanged(float)
    ├→ PyQtGraphCurvePlotter._on_state_cursor_changed() [updates cursor line]
    └→ Any other component listening

Result: SYNCHRONIZED - All components update together
```

---

## DEPENDENCY MAP

### Imports That Must Be Updated

**System B (to be removed/deprecated):**
```python
from .widgets.unified_viewport.geological_analysis_viewport import GeologicalAnalysisViewport
from .widgets.unified_viewport.unified_depth_scale_manager import UnifiedDepthScaleManager, DepthScaleConfig, DepthScaleMode
from .widgets.unified_viewport.pixel_depth_mapper import PixelDepthMapper, PixelMappingConfig
```

**System A (to be added):**
```python
from .graphic_window.state.depth_state_manager import DepthStateManager
from .graphic_window.state.depth_range import DepthRange
from .graphic_window.state.depth_coordinate_system import DepthCoordinateSystem
from .graphic_window.unified_graphic_window import UnifiedGraphicWindow
```

---

## MIGRATION STRATEGY

### Phase Order (DEPENDENCIES)

1. **Phase 1 (DONE):** Spike analysis ✅
2. **Phase 2:** EnhancedStratigraphicColumn migration
   - Depends on: Phase 1 analysis
   - Unblocks: Phase 4
3. **Phase 3:** PyQtGraphCurvePlotter migration
   - Depends on: Phase 1 analysis
   - Unblocks: Phase 4
4. **Phase 4:** HoleEditorWindow orchestration
   - Depends on: Phases 2, 3
   - Unblocks: Phase 5
5. **Phase 5:** UnifiedGraphicWindow activation
   - Depends on: Phase 4
   - Unblocks: Phase 6
6. **Phase 6:** System B deprecation
   - Depends on: Phase 5
   - Unblocks: Phase 7
7. **Phase 7:** Comprehensive testing
   - Depends on: Phase 6
   - Unblocks: Phase 8/9
8. **Phase 8:** Escalation checkpoint (conditional)
9. **Phase 9:** Final validation & deployment

---

## CRITICAL SUCCESS FACTORS

### Must-Have Behaviors After Migration

1. **Bidirectional Scroll Sync**
   - Scroll curve plotter → strat column updates
   - Scroll strat column → curve plotter updates
   - Both use same DepthStateManager instance

2. **Cursor Synchronization**
   - Click in strat column → cursor appears in curve plotter
   - Click in curve plotter → cursor updates in strat column
   - Both update via DepthStateManager.set_cursor_depth()

3. **Zoom Synchronization**
   - Zoom controls propagate to all components
   - Uses DepthStateManager.set_zoom_level()

4. **Pixel Alignment**
   - Curve Y-axis and strat column Y-axis must align to <1px
   - Uses same DepthCoordinateSystem for coordinate transformation

5. **No Breaking Changes**
   - All existing tests must pass
   - App must start without errors
   - Zoom controls must work as before

---

## RISK ASSESSMENT

### Low Risk
- EnhancedStratigraphicColumn already partially integrated
- System A infrastructure is complete
- Phase 2-3 are purely wiring changes

### Medium Risk
- HoleEditorWindow has many dependencies (Phase 4)
- Removing System B requires careful commenting
- Signal loop prevention (Phase 5)

### High Risk (Requires Testing)
- Pixel alignment between components
- Performance impact of synchronizers
- Backward compatibility

### Mitigation Strategy
- Rollback patches at each phase
- Comprehensive unit + integration tests (Phase 7)
- Escalation to Opus if tests fail

---

## NEXT STEPS

**Ready to proceed to Phase 2: EnhancedStratigraphicColumn Migration**

Prepared by: CODER (Sonnet 4.6)  
Authority: MAXIMUM (all 9 phases authorized)  
Escalation Path: Opus (if Phase 7 tests fail)  
