# OPTION B: Full Architectural Migration Specification

**Date:** 2026-03-01 20:30 GMT+11
**Status:** READY FOR DELEGATION TO CODER (Sonnet 4.6)
**Target:** System A (DepthStateManager) consolidation for 1point Desktop parity

---

## PHASE OVERVIEW

```
Phase 1: Spike Analysis (audit dependencies)
    ↓
Phase 2: EnhancedStratigraphicColumn migration
    ↓
Phase 3: PyQtGraphCurvePlotter migration
    ↓
Phase 4: HoleEditorWindow orchestration
    ↓
Phase 5: UnifiedGraphicWindow activation
    ↓
Phase 6: System B deprecation
    ↓
Phase 7: Comprehensive testing (unit + integration + regression)
    ↓
Phase 8: Escalation checkpoint (Opus if needed)
    ↓
Phase 9: Final validation & deployment
```

---

## PHASE 1: SPIKE ANALYSIS (1 hour)

**Goal:** Map all dependencies before starting migration

### Task 1.1: Audit Import Dependencies
```bash
grep -r "UnifiedDepthScaleManager\|PixelDepthMapper\|GeologicalAnalysisViewport" src/ui/ --include="*.py"
grep -r "from.*unified_viewport" src/ --include="*.py"
grep -r "from.*graphic_window.state" src/ --include="*.py"
```

**Deliverable:** List of all files importing from System B vs System A

### Task 1.2: Map Signal Dependencies
```python
# Identify all signals emitted/consumed
grep -r "\.connect(" src/ui/main_window.py | grep -E "viewRangeChanged|depthRangeChanged|zoomLevelChanged"
grep -r "@pyqtSlot\|\.emit(" src/ui/widgets/enhanced_stratigraphic_column.py | head -20
grep -r "@pyqtSlot\|\.emit(" src/ui/widgets/pyqtgraph_curve_plotter.py | head -20
```

**Deliverable:** Signal flow diagram (current → target)

### Task 1.3: Identify Breaking Changes
```python
# Check if System B components are used elsewhere
grep -r "geometric_analysis_viewport\|unified_depth_manager\|unified_pixel_mapper" src/ --include="*.py"
```

**Deliverable:** List of all components that depend on System B

**Output:** SPIKE_ANALYSIS.txt with findings

---

## PHASE 2: ENHANCED STRATIGRAPHIC COLUMN MIGRATION (1.5 hours)

**File:** `src/ui/widgets/enhanced_stratigraphic_column.py`

### Current State
```python
class EnhancedStratigraphicColumn(StratigraphicColumn):
    def __init__(self, parent=None, depth_state_manager: 'DepthStateManager' = None):
        super().__init__(parent)
        self.depth_state_manager = depth_state_manager  # ← Already has parameter!
        # BUT: signals not connected in initialization
        # AND: scroll handlers don't propagate to depth_state_manager
```

### Changes Required

#### 2.1: Fix Signal Connection in __init__
```python
def __init__(self, parent=None, depth_state_manager: 'DepthStateManager' = None):
    super().__init__(parent)
    
    # Store state manager reference
    self.depth_state_manager = depth_state_manager
    
    # ✅ ADD: Connect state manager signals if provided
    if self.depth_state_manager:
        self.depth_state_manager.viewportRangeChanged.connect(self._on_state_viewport_changed)
        self.depth_state_manager.cursorDepthChanged.connect(self._on_state_cursor_changed)
        self.depth_state_manager.zoomLevelChanged.connect(self._on_state_zoom_changed)
```

#### 2.2: Implement State Manager Signal Handlers
```python
@pyqtSlot(object)  # DepthRange
def _on_state_viewport_changed(self, depth_range):
    """Handle viewport range change from DepthStateManager."""
    # Update visible depth range
    self.visible_min_depth = depth_range.from_depth
    self.visible_max_depth = depth_range.to_depth
    self.visible_range = depth_range.range_size
    
    # Trigger redraw
    self.viewport().update()

@pyqtSlot(float)
def _on_state_cursor_changed(self, depth):
    """Handle cursor depth change from DepthStateManager."""
    self.cursor_depth = depth
    self.viewport().update()

@pyqtSlot(float)
def _on_state_zoom_changed(self, zoom_level):
    """Handle zoom change from DepthStateManager."""
    self.zoom_factor = zoom_level
    self.viewport().update()
```

#### 2.3: Wire Scroll Events to State Manager
```python
def wheelEvent(self, event):
    """Handle mouse wheel scroll."""
    # Calculate new depth range based on scroll
    scroll_delta = event.angleDelta().y()
    # ... existing scroll calculation ...
    
    # ✅ ADD: Update state manager (this triggers cross-widget sync)
    if self.depth_state_manager:
        self.depth_state_manager.set_viewport_range(new_min_depth, new_max_depth)
    
    # Prevent parent handling
    event.accept()
```

#### 2.4: Wire Click Events to State Manager
```python
def mousePressEvent(self, event):
    """Handle mouse click on lithology unit."""
    # ... existing click handling ...
    
    # ✅ ADD: Update cursor depth in state manager
    if self.depth_state_manager:
        self.depth_state_manager.set_cursor_depth(clicked_depth)
    
    super().mousePressEvent(event)
```

### Validation Checklist
- [ ] EnhancedStratigraphicColumn initializes with DepthStateManager
- [ ] All 3 signals (viewportRangeChanged, cursorDepthChanged, zoomLevelChanged) are connected
- [ ] Scroll events trigger state manager updates
- [ ] Click events update cursor in state manager
- [ ] Widget redraws when state manager signals fire

### Rollback Plan
```bash
git diff src/ui/widgets/enhanced_stratigraphic_column.py > phase2.patch
# If issues: git apply -R phase2.patch
```

---

## PHASE 3: PYQTGRAPH CURVE PLOTTER MIGRATION (1.5 hours)

**File:** `src/ui/widgets/pyqtgraph_curve_plotter.py`

### Current State
```python
class PyQtGraphCurvePlotter(QWidget):
    viewRangeChanged = pyqtSignal(float, float)  # min_depth, max_depth
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ❌ NO depth_state_manager parameter
        # ❌ NO signal connections to external state manager
```

### Changes Required

#### 3.1: Add DepthStateManager Parameter
```python
def __init__(self, parent=None, depth_state_manager: 'DepthStateManager' = None):
    super().__init__(parent)
    
    # ✅ ADD: Store state manager reference
    self.depth_state_manager = depth_state_manager
    
    # ✅ ADD: Connect state manager signals if provided
    if self.depth_state_manager:
        self.depth_state_manager.viewportRangeChanged.connect(self._on_state_viewport_changed)
        self.depth_state_manager.cursorDepthChanged.connect(self._on_state_cursor_changed)
        self.depth_state_manager.zoomLevelChanged.connect(self._on_state_zoom_changed)
```

#### 3.2: Implement State Manager Handlers
```python
@pyqtSlot(object)  # DepthRange
def _on_state_viewport_changed(self, depth_range):
    """Handle viewport range change from DepthStateManager."""
    # Update Y-axis range in PyQtGraph
    min_depth = depth_range.from_depth
    max_depth = depth_range.to_depth
    
    # Update plot range (suppress auto-range)
    for viewbox in self.plot.viewBox:
        viewbox.setYRange(max_depth, min_depth, padding=0)
    
    # Trigger redraw
    self.plot.replot()

@pyqtSlot(float)
def _on_state_cursor_changed(self, depth):
    """Handle cursor depth change from DepthStateManager."""
    # Draw cursor line at depth
    self._update_cursor_line(depth)

@pyqtSlot(float)
def _on_state_zoom_changed(self, zoom_level):
    """Handle zoom change from DepthStateManager."""
    # Adjust visible range based on zoom
    current_range = self.get_current_depth_range()
    center = (current_range[0] + current_range[1]) / 2
    half_width = (current_range[1] - current_range[0]) / (2 * zoom_level)
    
    self._on_state_viewport_changed(DepthRange(center - half_width, center + half_width))
```

#### 3.3: Wire Scroll Events to State Manager
```python
def wheelEvent(self, event):
    """Handle mouse wheel scroll."""
    # ... existing scroll calculation ...
    
    # ✅ ADD: Update state manager
    if self.depth_state_manager:
        self.depth_state_manager.set_viewport_range(new_min_depth, new_max_depth)
    
    # Also emit local signal for backward compatibility
    self.viewRangeChanged.emit(new_min_depth, new_max_depth)
    
    event.accept()
```

#### 3.4: Wire Drag Events to State Manager
```python
def mouseMoveEvent(self, event):
    """Handle mouse drag."""
    if self.is_dragging:
        # ... existing drag calculation ...
        
        # ✅ ADD: Update state manager on boundary drag
        if self.depth_state_manager and self.dragging_boundary:
            self.depth_state_manager.set_viewport_range(new_min_depth, new_max_depth)
```

### Validation Checklist
- [ ] PyQtGraphCurvePlotter accepts depth_state_manager parameter
- [ ] All 3 signals connected
- [ ] Scroll events trigger state manager updates
- [ ] Y-axis updates when state manager signals fire
- [ ] Cursor line updates when cursor depth changes
- [ ] Zoom changes propagate through state manager

### Rollback Plan
```bash
git diff src/ui/widgets/pyqtgraph_curve_plotter.py > phase3.patch
```

---

## PHASE 4: HOLEEDITORWINDOW ORCHESTRATION (1 hour)

**File:** `src/ui/main_window.py` (HoleEditorWindow class)

### Current State
```python
class HoleEditorWindow:
    def __init__(self):
        # Creates System B:
        self.unified_depth_manager = UnifiedDepthScaleManager(depth_config)
        self.unifiedViewport = GeologicalAnalysisViewport()
        
        # Creates System A components but doesn't wire them:
        self.curvePlotter = PyQtGraphCurvePlotter()  # ← No DepthStateManager
        self.enhancedStratColumnView = EnhancedStratigraphicColumn()  # ← No DepthStateManager
```

### Changes Required

#### 4.1: Create DepthStateManager Instance
```python
# ADD at top of __init__:
from src.ui.graphic_window.state.depth_state_manager import DepthStateManager

# In __init__, replace UnifiedDepthScaleManager creation:
# OLD:
# self.unified_depth_manager = UnifiedDepthScaleManager(depth_config)

# NEW:
self.depth_state_manager = DepthStateManager()
```

#### 4.2: Pass DepthStateManager to Widgets
```python
# OLD:
# self.curvePlotter = PyQtGraphCurvePlotter()
# self.enhancedStratColumnView = EnhancedStratigraphicColumn()

# NEW:
self.curvePlotter = PyQtGraphCurvePlotter(depth_state_manager=self.depth_state_manager)
self.enhancedStratColumnView = EnhancedStratigraphicColumn(
    depth_state_manager=self.depth_state_manager
)
```

#### 4.3: Remove System B References
```python
# DELETE/COMMENT OUT:
# self.unified_depth_manager = UnifiedDepthScaleManager(depth_config)
# self.unified_pixel_mapper = PixelDepthMapper(pixel_config)
# self.unifiedViewport = GeologicalAnalysisViewport()
# self.unifiedViewport.set_components(...)
```

#### 4.4: Create New Unified Container
```python
# ADD:
from src.ui.graphic_window.unified_graphic_window import UnifiedGraphicWindow

self.unified_viewport = UnifiedGraphicWindow(
    self.depth_state_manager,
    self.curvePlotter,
    self.enhancedStratColumnView
)

# Add to layout instead of old GeologicalAnalysisViewport
unified_layout.addWidget(self.unified_viewport)
```

#### 4.5: Wire Top-Level Zoom Controls
```python
# Connect zoom state manager to new container:
self.zoom_state_manager.zoomLevelChanged.connect(
    self.depth_state_manager.set_zoom_level
)

# Connect new container back to zoom manager:
self.depth_state_manager.zoomLevelChanged.connect(
    self.zoom_state_manager.set_zoom_level
)
```

### Validation Checklist
- [ ] DepthStateManager created and properly initialized
- [ ] Both widgets receive DepthStateManager reference
- [ ] Old System B components removed/commented
- [ ] UnifiedGraphicWindow instantiated and wired
- [ ] Zoom controls bidirectionally connected
- [ ] No import errors on startup

### Rollback Plan
```bash
git diff src/ui/main_window.py > phase4.patch
```

---

## PHASE 5: UNIFIEDGRAPHICWINDOW ACTIVATION (1 hour)

**File:** `src/ui/graphic_window/unified_graphic_window.py`

### Goal
Ensure UnifiedGraphicWindow properly instantiates and wires all synchronizers

### Changes Required

#### 5.1: Verify Synchronizer Initialization
```python
# In UnifiedGraphicWindow.__init__:
# Ensure these are created and active:
self.depth_synchronizer = DepthSynchronizer(self.depth_state_manager)
self.scroll_synchronizer = ScrollSynchronizer(self.depth_state_manager)
self.selection_synchronizer = SelectionSynchronizer(self.depth_state_manager)
```

#### 5.2: Verify Signal Wiring
```python
# Ensure all component signals are wired:
self.curve_plotter.viewRangeChanged.connect(self.depth_synchronizer.on_viewport_changed)
self.strat_column.depthClicked.connect(self.depth_synchronizer.on_cursor_depth_changed)
self.depth_state_manager.viewportRangeChanged.connect(self.curve_plotter.set_viewport_range)
self.depth_state_manager.viewportRangeChanged.connect(self.strat_column.set_viewport_range)
```

#### 5.3: Enable Feature Flags
```python
# Ensure System A features are enabled:
ENABLE_DEPTH_STATE_MANAGER = True
ENABLE_SYNCHRONIZERS = True
DISABLE_SYSTEM_B = True  # Prevent old system interference
```

### Validation Checklist
- [ ] All synchronizers instantiated
- [ ] All signals properly connected
- [ ] No circular signal loops
- [ ] Feature flags set correctly

---

## PHASE 6: SYSTEM B DEPRECATION (30 minutes)

**Files:** All System B components in `src/ui/widgets/unified_viewport/`

### Changes Required

#### 6.1: Mark as Deprecated
```python
# In unified_depth_scale_manager.py:
"""
DEPRECATED: This module is maintained for backward compatibility only.
Use src/ui/graphic_window/state/depth_state_manager.py instead.

System A (DepthStateManager) is the preferred implementation.
This System B implementation will be removed in Phase 5.
"""

class UnifiedDepthScaleManager(QObject):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "UnifiedDepthScaleManager is deprecated. Use DepthStateManager instead.",
            DeprecationWarning,
            stacklevel=2
        )
```

#### 6.2: Consolidate Duplicate Code
```python
# In depth_state_manager.py:
# Copy useful utility functions from UnifiedDepthScaleManager:
# - depth_to_pixel()
# - pixel_to_depth()
# - depth_to_screen_y()
# Ensure DepthCoordinateSystem has all capabilities

# Merge PixelDepthMapper functionality into DepthCoordinateSystem
```

#### 6.3: Comment Out Unused References
```bash
# In main_window.py:
# Comment out all imports of System B:
# from .widgets.unified_viewport.geometric_analysis_viewport import GeologicalAnalysisViewport
# from .widgets.unified_viewport.unified_depth_scale_manager import UnifiedDepthScaleManager

# Verify no other files import System B
grep -r "from.*unified_viewport\|from.*UnifiedDepthScaleManager" src/ --include="*.py"
```

### Validation Checklist
- [ ] Deprecation warnings added to System B
- [ ] Duplicate utility functions merged into System A
- [ ] All System B imports disabled
- [ ] No active code uses System B

---

## PHASE 7: COMPREHENSIVE TESTING (3 hours)

### Phase 7A: Unit Testing (1 hour)

#### Test 7A.1: EnhancedStratigraphicColumn
```python
# tests/test_enhanced_strat_column_system_a.py
def test_strat_column_receives_state_manager_signals():
    """Verify strat column responds to DepthStateManager signals."""
    state_mgr = DepthStateManager()
    strat_col = EnhancedStratigraphicColumn(depth_state_manager=state_mgr)
    
    # Change viewport in state manager
    state_mgr.set_viewport_range(100, 150)
    
    # Assert strat column updated
    assert strat_col.visible_min_depth == 100
    assert strat_col.visible_max_depth == 150

def test_strat_column_emits_scroll_events_to_state_manager():
    """Verify strat column scroll events update state manager."""
    state_mgr = DepthStateManager()
    strat_col = EnhancedStratigraphicColumn(depth_state_manager=state_mgr)
    
    # Simulate scroll event
    strat_col.wheelEvent(create_wheel_event(delta=120))  # scroll up
    
    # Assert state manager was updated
    # (use spy to check signal emission)
```

#### Test 7A.2: PyQtGraphCurvePlotter
```python
# tests/test_curve_plotter_system_a.py
def test_curve_plotter_receives_state_manager_signals():
    """Verify curve plotter Y-axis responds to DepthStateManager."""
    state_mgr = DepthStateManager()
    plotter = PyQtGraphCurvePlotter(depth_state_manager=state_mgr)
    
    # Change viewport
    state_mgr.set_viewport_range(100, 150)
    
    # Assert Y-axis range updated
    y_min, y_max = plotter.get_yaxis_range()
    assert y_min == 150  # Inverted for well logs
    assert y_max == 100
```

### Phase 7B: Integration Testing (1 hour)

#### Test 7B.1: Cross-Widget Synchronization
```python
# tests/test_viewport_integration_system_a.py
def test_scroll_sync_bidirectional():
    """Verify scrolling one widget updates the other."""
    state_mgr = DepthStateManager()
    strat_col = EnhancedStratigraphicColumn(depth_state_manager=state_mgr)
    plotter = PyQtGraphCurvePlotter(depth_state_manager=state_mgr)
    
    # Scroll curve plotter
    plotter.wheelEvent(create_wheel_event(100, 150))  # min, max
    
    # Verify strat column viewport changed
    assert strat_col.visible_min_depth == 100
    assert strat_col.visible_max_depth == 150

def test_cursor_depth_sync():
    """Verify cursor changes propagate across components."""
    state_mgr = DepthStateManager()
    strat_col = EnhancedStratigraphicColumn(depth_state_manager=state_mgr)
    plotter = PyQtGraphCurvePlotter(depth_state_manager=state_mgr)
    
    # Click strat column at depth 125
    strat_col.mousePressEvent(create_mouse_event(depth=125))
    
    # Verify plotter cursor line updated
    assert plotter.cursor_depth == 125
```

### Phase 7C: Regression Testing (1 hour)

#### Test 7C.1: Phase 5/6 Test Suite
```bash
# Run existing test suite to ensure no breakage:
python -m pytest tests/test_phase5_workflow_validation.py -v
python -m pytest tests/test_pixel_alignment.py -v
python -m pytest tests/test_phase3_integration.py -v
```

**Expected:** All tests pass with System A architecture

#### Test 7C.2: Pixel Alignment Validation
```python
# tests/test_system_a_pixel_alignment.py
def test_pixel_perfect_depth_mapping():
    """Verify System A achieves pixel-perfect depth mapping."""
    state_mgr = DepthStateManager()
    
    # Test depth-to-pixel mapping consistency
    for depth in [0, 50, 100, 150, 200, 500, 1000]:
        pixel_pos = state_mgr.depth_to_screen_y(depth)
        recovered_depth = state_mgr.screen_y_to_depth(pixel_pos)
        
        # Should round-trip with <1px error
        assert abs(recovered_depth - depth) < 0.1
```

### Validation Checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Phase 5/6 regression tests pass
- [ ] Pixel alignment <1px
- [ ] No performance regressions

### If Tests Fail
```
ESCALATE TO OPUS:
- Provide failing test output
- Ask for root cause analysis
- Opus will identify architectural issues
- Proceed with Phase 8 escalation
```

---

## PHASE 8: ESCALATION CHECKPOINT (Decision Point)

**Trigger:** If Phase 7 tests reveal breaking changes or issues

### Escalation Criteria
✅ **Proceed to Phase 9** if:
- All unit tests pass
- All integration tests pass
- Phase 5/6 regression tests pass
- Pixel alignment verified

🔴 **Escalate to Opus** if:
- Critical failures in scroll sync
- Pixel alignment > 2px deviation
- Signal loop detected
- Memory leaks in state manager

### Escalation Task
```python
if critical_test_failures:
    escalate_to_opus(
        issue="Phase 7 test failures",
        context={
            "failing_tests": [...],
            "error_messages": [...],
            "suspected_cause": "..."
        },
        task="Diagnose architectural issues and provide remediation"
    )
```

---

## PHASE 9: FINAL VALIDATION & DEPLOYMENT (1 hour)

### Task 9.1: Update Documentation
```python
# Update HANDOFFS.md:
# [SYSTEM A MIGRATION COMPLETE]
# Date: YYYY-MM-DD
# Changes:
# - Migrated EnhancedStratigraphicColumn to use DepthStateManager
# - Migrated PyQtGraphCurvePlotter to use DepthStateManager
# - Updated HoleEditorWindow to create and inject state manager
# - Activated UnifiedGraphicWindow from graphic_window/
# - Deprecated System B (UnifiedDepthScaleManager, PixelDepthMapper)
#
# Test Results:
# - Unit tests: X/X passed
# - Integration tests: X/X passed
# - Regression tests: X/X passed
# - Pixel alignment: <1px
```

### Task 9.2: Commit Changes
```bash
git add -A
git commit -m "feat: migrate viewport to System A (DepthStateManager) for 1point Desktop parity

- Inject DepthStateManager into EnhancedStratigraphicColumn
- Inject DepthStateManager into PyQtGraphCurvePlotter
- Activate UnifiedGraphicWindow as primary container
- Wire all signals for pixel-perfect scroll synchronization
- Deprecate System B (UnifiedDepthScaleManager)
- All Phase 5/6 tests passing, <1px pixel alignment

Closes: System architecture alignment issue"

git push origin main
```

### Task 9.3: Summary Report
```markdown
# System A Migration Summary

## What Changed
- **Before**: System B (UnifiedDepthScaleManager) with incomplete signal wiring
- **After**: System A (DepthStateManager) with complete bidirectional sync

## Architecture Achievement
✅ Single source of truth (DepthStateManager)
✅ Broadcast-based signal flow
✅ Pixel-perfect depth synchronization
✅ 100% 1point Desktop parity

## Verification
✅ Unit tests: All passed
✅ Integration tests: All passed
✅ Regression tests: All passed
✅ Pixel alignment: <1px verified

## Risk Mitigation
✅ Rollback patches created at each phase
✅ Comprehensive testing at Phase 7
✅ Escalation path available for critical issues
```

---

## CRITICAL SUCCESS FACTORS

1. **Test Early, Test Often**
   - Run tests after each phase
   - Don't skip validation

2. **Rollback Plan**
   - Keep .patch files from each phase
   - Can revert individually if needed

3. **Communication**
   - Report status at each checkpoint
   - Escalate immediately if issues arise

4. **Phase Independence**
   - Each phase should compile and test independently
   - Don't combine phases if one has issues

---

## TIMELINE

| Phase | Duration | Cumulative |
|-------|----------|-----------|
| 1: Spike Analysis | 1h | 1h |
| 2: Strat Column | 1.5h | 2.5h |
| 3: Curve Plotter | 1.5h | 4h |
| 4: HoleEditorWindow | 1h | 5h |
| 5: UnifiedGraphicWindow | 1h | 6h |
| 6: Deprecation | 0.5h | 6.5h |
| 7: Testing | 3h | 9.5h |
| 8: Escalation (if needed) | variable | — |
| 9: Final Validation | 1h | 10.5h |

**Best Case:** 6.5 hours (no issues in testing)
**Typical:** 9.5 hours (find and fix minor issues)
**Worst Case:** 12+ hours (escalation to Opus required)

---

## SUCCESS CRITERIA (GO/NO-GO)

| Criterion | Target | Verification |
|-----------|--------|--------------|
| Unit Tests | 100% pass | pytest Phase 7A |
| Integration Tests | 100% pass | pytest Phase 7B |
| Regression Tests | 100% pass | pytest Phase 5/6 suite |
| Pixel Alignment | <1px | alignment_validator test |
| Signal Loops | 0 | Qt signal spy analysis |
| Performance | No regression | FPS benchmark |
| Code Coverage | >90% new code | coverage report |

**GO DECISION:** All criteria met → Commit to main
**NO-GO DECISION:** Any criterion failed → Escalate to Opus Phase 8

