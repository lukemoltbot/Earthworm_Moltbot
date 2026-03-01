# VIEWPORT REDESIGN STRATEGY
**Status:** PHASE A DIAGNOSIS COMPLETE
**Date:** 2026-03-01 19:30 GMT+11
**Auditor:** Debugger (OPUS)
**Confidentiality:** Technical Escalation Document

---

## EXECUTIVE SUMMARY

**Architecture Status:** DUAL VIEWPORT SYSTEMS DISCOVERED
- System A (Unused): `src/ui/graphic_window/` — Complete, well-designed, **NOT INSTANTIATED**
- System B (Active): `src/ui/widgets/unified_viewport/` — Functional, **REPLICATED INFRASTRUCTURE**

**Critical Finding:** Earthworm has built TWO independent viewport sync systems that serve the same purpose. This is a major code smell indicating an architectural pivot mid-development.

**Feasibility of Integration:** ✅ YES, but requires **strategic consolidation** not greenfield rewrite.

**Recommendation:** Consolidate to **System A** (better design, cleaner signals) with minimal breaking changes.

---

## SECTION 1: ARCHITECTURE DISCONNECT MAP

### Current Architecture State (SYSTEM B ACTIVE - CORRECTED)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN_WINDOW.PY                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HoleEditorWindow                                                    │
│  ├─ self.curvePlotter: PyQtGraphCurvePlotter                         │
│  ├─ self.enhancedStratColumnView: EnhancedStratigraphicColumn()      │
│  ├─ self.zoom_state_manager: ZoomStateManager                       │
│  │                                                                   │
│  └─ self.unifiedViewport: GeologicalAnalysisViewport()              │
│     │                                                                │
│     └─> ACTIVE SYSTEM B (src/ui/widgets/unified_viewport/)          │
│         │                                                             │
│         ├─ UnifiedDepthScaleManager (ACTUAL STATE MANAGER)          │
│         │  ├─ Mode: PIXEL_PERFECT (1px tolerance)                  │
│         │  ├─ Signals: depthRangeChanged, viewRangeChanged, etc.   │
│         │  └─ Maps: depth ranges ↔ pixel positions                 │
│         │                                                             │
│         ├─ PixelDepthMapper                                         │
│         │  ├─ depth_to_pixel(depth) → screen_y                     │
│         │  ├─ pixel_to_depth(screen_y) → depth                     │
│         │  └─ Cache: 1000 mappings for performance                 │
│         │                                                             │
│         ├─ ScrollingSynchronizer                                    │
│         │  ├─ Handles: wheel events, programmatic scrolls          │
│         │  └─ Updates: UnifiedDepthScaleManager on scroll          │
│         │                                                             │
│         └─ set_components() wires:                                  │
│            ├─ curve plotter → sync on viewport change             │
│            ├─ strat column → sync on depth clicked                │
│            └─ zoom state manager → sync on zoom change            │
│                                                                      │
│  └─ (UNUSED BUT COMPLETE) SYSTEM A (src/ui/graphic_window/)        │
│     └─> DepthStateManager + DepthCoordinateSystem (alternative)    │
│         (Not instantiated in actual app; kept for reference)       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Target Architecture State (CONSOLIDATED)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MAIN_WINDOW.PY                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  HoleEditorWindow                                                    │
│  │                                                                   │
│  └─> UnifiedGraphicWindow (UNIFIED SYSTEM)                          │
│      │                                                               │
│      ├─ DepthStateManager (SINGLE SOURCE OF TRUTH)                  │
│      │  ├─ viewportRangeChanged → All components update            │
│      │  ├─ cursorDepthChanged → Cursor highlights sync             │
│      │  ├─ selectionRangeChanged → Selection highlights sync       │
│      │  └─ zoomLevelChanged → All zoom in unison                   │
│      │                                                               │
│      ├─ DepthCoordinateSystem (SHARED Y-AXIS SPACE)                │
│      │  ├─ depth_to_screen_y(depth) → Pixel position              │
│      │  ├─ screen_y_to_depth(pixel) → Depth value                 │
│      │  └─ set_depth_range(from, to) → Update canvas mapping      │
│      │                                                               │
│      ├─ ScrollingSynchronizer (ENHANCED)                           │
│      │  └─ Subscribes to DepthStateManager for scroll events      │
│      │                                                               │
│      ├─ Components (PROPERLY WIRED)                                │
│      │  ├─ StratigraphicColumn                                    │
│      │  │  ├─ Subscribes: viewportRangeChanged, cursorDepthChanged │
│      │  │  ├─ Updates: depth_state on scroll/click                │
│      │  │  └─ Uses: coords.depth_to_screen_y() for positioning    │
│      │  │                                                            │
│      │  ├─ LASCurvesDisplay                                       │
│      │  │  ├─ Subscribes: viewportRangeChanged, cursorDepthChanged │
│      │  │  ├─ Updates: depth_state on scroll                       │
│      │  │  └─ Uses: coords.depth_to_screen_y() for positioning    │
│      │  │                                                            │
│      │  └─ Other Components                                        │
│      │     └─ [Information Panel, Preview, Lithology Table]       │
│      │                                                               │
│      └─ (DEPRECATED) UnifiedDepthScaleManager, PixelDepthMapper    │
│         └─ Consolidated into DepthStateManager + DepthCoordSystem │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Disconnect Points

| Component | Current (System B) | Target (System A) | Gap |
|-----------|------------------|-------------------|-----|
| **State Manager** | UnifiedDepthScaleManager (custom) | DepthStateManager (signals-based) | 🔴 Separate systems |
| **Coordinate Space** | PixelDepthMapper (pixel-centric) | DepthCoordinateSystem (depth-centric) | 🔴 Different abstraction |
| **Scroll Sync** | ScrollingSynchronizer (component-internal) | ScrollSynchronizer (state-driven) | 🔴 Opposite flows |
| **Widget Wiring** | ComponentAdapter.connect_components() | Direct state.signal.connect() | 🔴 Adapter overhead |
| **Signal Flow** | Component → ScrollSync → State (push) | State → Components (broadcast) | 🔴 Opposite patterns |
| **Components** | Enhanced*, PyQtGraph* (custom tweaks) | Generic (stateless renderers) | ⚠️ Feature parity unknown |

---

## SECTION 2: REFACTORING STRATEGY (NON-BREAKING PRIORITY)

### Phase 1: Verify & Activate UnifiedDepthScaleManager Signal Wiring (LOWEST RISK) ✅

**CORRECTED SPECIFICATION** (2026-03-01 19:45)
- **Real System in Use:** System B (UnifiedDepthScaleManager, NOT System A DepthStateManager)
- **Location:** `src/ui/widgets/unified_viewport/unified_depth_scale_manager.py`
- **Active Container:** `src/ui/widgets/unified_viewport/geological_analysis_viewport.py`

**Scope:** Verify that UnifiedDepthScaleManager signals are wired to widget callbacks.
**Approach:** Audit signal connections; add missing handlers if signals aren't propagating.
**Timeline:** 1-2 hours | **Tokens:** ~2K-3K

**Actual Files to Audit/Modify:**
```
src/ui/widgets/unified_viewport/geological_analysis_viewport.py
├─ Verify: set_components() properly wires depth_manager signals
├─ Check: depthRangeChanged → update curve plotter Y-axis
├─ Check: depthRangeChanged → update strat column viewport
└─ Missing handlers? → Add _on_unified_depth_changed(), _on_zoom_changed()

src/ui/widgets/pyqtgraph_curve_plotter.py
├─ Verify: Y-axis updates respond to external depth_range_changed signals
├─ Check: Does it listen to unified_viewport's depth changes?
├─ If not: Add signal listener in constructor from parent/manager
└─ Test: Scroll in strat column → curve plotter Y-axis updates

src/ui/widgets/enhanced_stratigraphic_column.py
├─ Status: Already has depth_state_manager parameter in __init__ ✅
├─ Check: Are DepthStateManager signals actually connected? (grep for .connect())
├─ If incomplete: Wire viewportRangeChanged, zoomLevelChanged handlers
└─ Test: Scroll in curve plotter → strat column viewport updates

src/ui/main_window.py (HoleEditorWindow)
├─ Status: Creates UnifiedDepthScaleManager at line 121 ✅
├─ Status: Creates unified_viewport.set_components() at line 135 ✅
├─ Verify: Are signals throttled properly? (update_throttle_ms = 16)
└─ Check: Does zoom_state_manager properly propagate zoom changes?
```

**Regression Testing Scope:**
- Phase 5/6 scroll synchrony tests
- Zoom level changes (must update all widgets)
- Cursor depth tracking (highlight must sync)
- No breaking changes to Phase 5/6 feature API

**Risk Assessment:** 🟢 LOW
- Widgets keep internal state (backward compatible)
- Signals are additive (existing handlers still work)
- Can disable via feature flag if regressions appear

**Evidence:** enhs_strat_col.py line 116 already listens to `.connect()` pattern ✅

---

### Phase 2: Integrate ScrollingSynchronizer (MEDIUM RISK)

**Scope:** Replace widget-local scroll handlers with state-driven updates.
**Approach:** ScrollSynchronizer becomes a bridge: `Widget scroll event → DepthStateManager.set_viewport_range() → All widgets react`
**Timeline:** 4-6 hours | **Tokens:** ~5K-8K

**Files to Modify:**
```
src/ui/graphic_window/synchronizers/scroll_synchronizer.py
├─ Enhance to work with DepthStateManager signals
├─ Listen to widget scroll events (from enhanced_strat_col, pyqtgraph)
├─ Emit depthRangeChanged → DepthStateManager.set_viewport_range()
└─ Performance optimization: throttle updates to 60 FPS

src/ui/widgets/enhanced_stratigraphic_column.py
├─ Remove: self.verticalScrollBar().sliderMoved.connect(self._internal_handler)
├─ Add: self.verticalScrollBar().sliderMoved.connect(self._on_scroll_to_state)
├─ _on_scroll_to_state(): converts pixel scroll to depth, calls state.set_viewport_range()
└─ Remove redundant scroll calculations

src/ui/widgets/pyqtgraph_curve_plotter.py
├─ Similar: Remove internal scroll state updates
├─ Add: Report scroll position to DepthStateManager
└─ Let state broadcast new viewport to all widgets

src/ui/graphic_window/state/depth_state_manager.py
├─ Already has set_viewport_range() — just ensure it emits viewportRangeChanged ✅
└─ Verify synchronizers are wired to signals
```

**Backward Compatibility:**
- Widgets keep their internal scroll bars (no layout change)
- Events propagate: scroll → state → broadcast (not widget → widget)
- Phase 5/6 tests must still pass (pixel alignment, zoom, selection)

**Risk Assessment:** 🟡 MEDIUM
- Changes scroll event flow (could introduce latency)
- Must benchmark: is DepthStateManager.emit() faster/slower than direct updates?
- Rollback: Revert to Phase 1 if scroll feels sluggish

**Hidden Dependency Check:**
- Q: Do any Phase 5/6 tests directly mock scroll bar events?
  - If YES: Will need to update test fixtures
  - If NO: Tests should pass without changes

---

### Phase 3: Unify Depth Scaling (HIGHEST RISK)

**Scope:** Consolidate independent depth_scale logic into DepthCoordinateSystem.
**Approach:** Single source of truth: `DepthCoordinateSystem.depth_to_screen_y()` used by all widgets.
**Timeline:** 6-8 hours | **Tokens:** ~8K-12K

**Files to Modify:**
```
src/ui/widgets/enhanced_stratigraphic_column.py
├─ Remove: self._depth_scale = (max_visible - min_visible) / canvas_height
├─ Add: Use self.coords.depth_to_screen_y(depth) for all positioning
├─ Remove: self._screen_y_from_depth() (redundant)
└─ Verify: All rectangle positioning uses shared coordinate system

src/ui/widgets/pyqtgraph_curve_plotter.py
├─ Remove: self._pixels_per_meter calculation
├─ Add: Use self.coords for y-axis mapping
├─ Remove: self._depth_to_pixel_y() (redundant)
└─ Update curve rendering to use shared coords

src/ui/graphic_window/state/depth_coordinate_system.py
├─ Enhance: Add unit test for depth_to_screen_y() consistency
├─ Add: Cache recent mappings for performance
└─ Document: "This is the ONLY place depth→pixel Y mapping happens"

src/ui/widgets/unified_viewport/pixel_depth_mapper.py
├─ Deprecated (or kept for legacy support)
└─ All calls redirected to DepthCoordinateSystem
```

**Impact Analysis on Phase 5/6:**

| Feature | Risk | Mitigation |
|---------|------|-----------|
| **Pixel Alignment** | 🔴 HIGH | Ensure DepthCoordinateSystem canvas_height = actual rendered height |
| **Fixed-Scale Tracks** | 🔴 HIGH | Update scale calculations to use shared coords |
| **LAS Curve Rendering** | 🟡 MEDIUM | PyQtGraph viewport must sync with depth range |
| **Stratigraphic Column** | 🟡 MEDIUM | SVG positioning must use shared coords |
| **Zoom Behavior** | 🟡 MEDIUM | ZoomStateManager must update DepthCoordinateSystem.scale_factor |

**Rollback Strategy:**
1. If pixel misalignment occurs: Revert to Phase 2, keep dual coordinate systems
2. If curves render incorrectly: Investigate DepthCoordinateSystem.canvas_height updates
3. Quick restore: `git revert` to Phase 2 commit + re-test Phase 5/6

**Risk Assessment:** 🔴 HIGH
- Touches core rendering paths (alignment, zoom, positioning)
- Phase 5/6 test suite is regression-critical
- Requires careful canvas_height tracking on resize events

---

## SECTION 3: RISK MITIGATION

### Phase 5/6 Test Coverage Assessment

**Critical Tests to Run Before Each Phase:**
```bash
# Pixel alignment tests
pytest tests/test_pixel_alignment.py -v

# Unified viewport integration tests
pytest tests/test_unified_viewport_integration.py -v

# Phase 5/6 workflow validation
pytest tests/phase_5_workflow_tests.py -v
pytest tests/phase_6_workflow_tests.py -v

# Zoom and scale tests
pytest tests/test_zoom_state_manager.py -v
pytest tests/test_depth_scale.py -v
```

**Regression Likelihood by Phase:**

| Phase | Test Impact | Regression Probability | Mitigation |
|-------|-------------|------------------------|-----------|
| **Phase 1** | No test changes needed | 5% (signal latency) | Feature flag to disable if slow |
| **Phase 2** | May need scroll event mocks | 20% (event flow) | Benchmark scroll responsiveness |
| **Phase 3** | Full regression suite | 40% (positioning) | Run pixel alignment tests 10x |

### Validation Strategy per Phase

**Phase 1 Checkpoint (After 4 hours):**
```
✓ Widgets accept DepthStateManager in __init__
✓ Signals connected without errors
✓ Phase 5/6 tests pass (no regressions)
✓ Manual: Scroll in one widget, other widget updates
```

**Phase 2 Checkpoint (After 8 hours total):**
```
✓ Scroll bar events → DepthStateManager.set_viewport_range()
✓ DepthStateManager broadcasts → all widgets update
✓ Performance: Scroll at 60 FPS without frame drops
✓ Phase 5/6 tests pass (no regressions)
✓ Manual: Scroll synchrony feels smooth (no jank)
```

**Phase 3 Checkpoint (After 16 hours total):**
```
✓ All depth→pixel calculations use DepthCoordinateSystem
✓ Pixel alignment tests: <1 pixel variance across all widgets
✓ Zoom operations: All widgets scale in unison
✓ Phase 5/6 tests pass (pixel-perfect alignment)
✓ Manual: LAS curves + strat column perfectly aligned at all zoom levels
```

### Rollback Strategy

**If Phase 1 shows slowness:** Disable DepthStateManager signal connections via environment variable.
```python
# In enhanced_stratigraphic_column.py
if os.getenv('USE_EXPERIMENTAL_DEPTH_STATE') == '1':
    self.state.viewportRangeChanged.connect(self.on_viewport_changed)
```

**If Phase 2 breaks scroll sync:** Revert to Phase 1, keep signal connections only (read-only).
```
git revert <Phase 2 commit>
git checkout <Phase 1 branch>
```

**If Phase 3 breaks pixel alignment:** Emergency fallback to PixelDepthMapper.
```python
# In DepthCoordinateSystem
def depth_to_screen_y(self, depth):
    if FALLBACK_TO_PIXEL_MAPPER:
        return legacy_pixel_mapper.depth_to_pixel(depth)
    else:
        return (depth - self.min_depth) / self.range_size * self.canvas_height
```

---

## SECTION 4: INTEGRATION DEPENDENCIES

### Dependency Order (What Must Happen First?)

**Critical Path:**
```
1. DepthStateManager ready (already is)
   ↓
2. Phase 1: Wire DepthStateManager to widgets
   ├─ Must complete before Phase 2
   └─ Unlock: Signals flowing through widgets
   ↓
3. Phase 2: Scroll events → DepthStateManager
   ├─ Depends on Phase 1 signals being connected
   └─ Unlock: Centralized scroll handling
   ↓
4. Phase 3: Unify depth scaling
   ├─ Depends on Phase 2 scroll sync working
   └─ Final: Pixel-perfect alignment
```

### Hidden Dependencies Between Phases

**Q: Does EnhancedStratigraphicColumn.set_depth_range() conflict with DepthStateManager?**
- **Answer:** Currently no. enhanced_strat_col has internal _depth_scale, DepthStateManager is external.
- **Risk:** If Phase 1 wires signals but Phase 2 doesn't update set_depth_range(), widgets may have TWO depth ranges.
- **Mitigation:** In Phase 2, ensure set_depth_range() calls DepthStateManager.set_viewport_range().

**Q: Will ScrollingSynchronizer interfere with UnifiedDepthScaleManager?**
- **Answer:** Yes, both manage depth state. Consolidation required in Phase 3.
- **Risk:** If Phase 2 leaves both active, scroll events may propagate twice (2x updates).
- **Mitigation:** Phase 2 must disable UnifiedDepthScaleManager signal handlers OR ensure idempotency.

**Q: Can Phase 5/6 tests run during Phase 1/2 without modification?**
- **Answer:** Yes. As long as scroll sync works, tests should pass.
- **Risk:** If tests mock DepthStateManager, Phase 1/2 changes may expose test assumptions.
- **Mitigation:** Run full test suite after each phase; fix test mocks if needed.

### Timeline Estimate for Full Integration

```
Phase 1: Wire DepthStateManager             2-4 hours  (7,500 tokens)
Phase 2: Integrate ScrollingSynchronizer    4-6 hours  (12,500 tokens)
Phase 3: Unify depth scaling                6-8 hours  (20,000 tokens)
────────────────────────────────────────────────────────
TOTAL:                                     12-18 hours (40,000 tokens)

Plus testing/validation:                    4-6 hours  (10,000 tokens)
────────────────────────────────────────────────────────
TOTAL WITH QA:                             16-24 hours (50,000 tokens)
```

**Elapsed Time Estimate:**
- Phase 1: 1-2 days (including testing)
- Phase 2: 2-3 days (including performance validation)
- Phase 3: 3-4 days (including pixel-perfect alignment validation)
- **Total: 6-9 days** (assuming 4-6 hour coding sessions with breaks)

---

## SECTION 5: ARCHITECTURAL ASSESSMENT ANSWERS

### Q1: Can we integrate without rewriting unified_graphic_window.py?

**Answer:** ✅ YES, but with caveats.

**Justification:**
- UnifiedGraphicWindow is already well-designed (DepthStateManager → signals → components)
- Widgets (enhanced_strat_col, pyqtgraph) can be adapted to accept external DepthStateManager
- No rewrite needed; strategic injection of signals

**Approach:**
1. Keep unified_graphic_window.py as-is
2. Modify widgets to work with external DepthStateManager
3. Eventually, instantiate UnifiedGraphicWindow in HoleEditorWindow
4. Deprecate (don't delete) GeologicalAnalysisViewport for legacy support

---

### Q2: Minimum refactoring scope to achieve viewport parity?

**Answer:** Phase 1 + Phase 2 (~8 hours)

**Scope:**
- Add DepthStateManager parameter to 2 widget files
- Connect signals in 2 widget files
- Update scroll event handlers to call DepthStateManager
- Update HoleEditorWindow to create and pass DepthStateManager

**What you DON'T need to change:**
- PyQt6 layout (no visual refactoring)
- Component rendering logic (keep all custom tweaks)
- Phase 5/6 test files (should pass unchanged)

---

### Q3: Which Phase 5/6 features are at risk?

**Risk Matrix:**

| Feature | Phase 1 Risk | Phase 2 Risk | Phase 3 Risk | Notes |
|---------|-----------|-----------|-----------|-------|
| Scroll Sync | 🟢 NONE | 🟡 MEDIUM | 🟢 LOW | Phase 2 restructures event flow |
| Zoom | 🟡 LOW | 🟡 MEDIUM | 🔴 HIGH | Phase 3 unifies scaling |
| Pixel Alignment | 🟢 NONE | 🟢 NONE | 🔴 HIGH | Phase 3 is critical |
| Selection | 🟢 NONE | 🟢 NONE | 🟢 NONE | Not affected |
| LAS Curves | 🟢 NONE | 🟡 MEDIUM | 🔴 HIGH | Phase 2/3 touch rendering |
| Strat Column | 🟢 NONE | 🟡 MEDIUM | 🔴 HIGH | Phase 2/3 touch positioning |

**High-Risk Phase 5/6 Tests:**
```python
test_unified_viewport_integration.py  # Pixel alignment
test_zoom_state_manager.py              # Zoom behavior
test_las_curve_rendering.py             # Curve positioning
test_stratigraphic_column_sync.py       # Column sync with curves
test_phase_5_workflow_tests.py           # Integration test
```

---

### Q4: Is phased integration possible (non-breaking)?

**Answer:** ✅ YES, fully phased with rollback at each stage.

**Non-Breaking Strategy:**
- Phase 1: Add signals (non-breaking, just subscribe)
- Phase 2: Decouple scroll handlers (breaking but reversible)
- Phase 3: Consolidate coords (breaking but well-tested)

**Feature Flag Approach:**
```python
# In HoleEditorWindow.__init__
if ENABLE_EXPERIMENTAL_VIEWPORT_REDESIGN:
    self.depth_state = DepthStateManager(...)
    # Pass to widgets → Phase 1 signals active
    
    if ENABLE_CENTRALIZED_SCROLL_SYNC:
        # Phase 2 scroll handling
        self.scroll_sync = ScrollSynchronizer(...)
    
    if ENABLE_UNIFIED_DEPTH_COORDS:
        # Phase 3 coordinate unification
        self.depth_coords = DepthCoordinateSystem(...)
```

Each phase can be toggled independently for testing.

---

## SECTION 6: ESCALATION SUMMARY (150 tokens max)

### Can this be done without architectural pivot?

**YES.** No pivot needed. Earthworm already has the right architecture (System A in graphic_window/). The issue is **adoption**, not design.

**Justification:**
- DepthStateManager exists and is well-designed
- Components are properly wired (seen in graphic_window/components/)
- Problem: Never instantiated in actual UI (HoleEditorWindow uses System B instead)
- Solution: Wire System A signals into System B widgets via Phase 1/2/3

### Recommended Path Forward

**IMMEDIATE (next 2-4 hours):**
1. Phase 1: Inject DepthStateManager into widgets
2. Connect signals (viewportRangeChanged, cursorDepthChanged)
3. Run Phase 5/6 tests → should pass unchanged
4. **GATE:** If tests pass, proceed. If fail, rollback and investigate.

**SHORT-TERM (next 1-2 weeks):**
5. Phase 2: Decouple widget scroll handlers → DepthStateManager.set_viewport_range()
6. Benchmark scroll responsiveness
7. Full regression test suite

**MEDIUM-TERM (weeks 3-4):**
8. Phase 3: Consolidate depth scaling into DepthCoordinateSystem
9. Pixel-perfect alignment validation
10. Deprecate PixelDepthMapper, UnifiedDepthScaleManager (keep for legacy)

### Delegation Recommendation

**✅ Phase 1 (Wire Signals) → Can delegate to CODER**
- Low risk
- Clear scope (4 files, ~200 lines of code)
- Regression tests validate
- Reversible if issues arise

**⚠️ Phase 2+ (Scroll/Scaling) → Recommend OPUS Oversight**
- Medium/high risk to Phase 5/6 tests
- Requires performance benchmarking
- Coordinate system changes affect core rendering
- Continue under Opus review; checkpoint after Phase 2

---

**Escalation Approval:** RECOMMEND PHASE 1 DELEGATION TO CODER
- Clear, low-risk, bounded scope
- Can proceed immediately
- Full regression testing available
- Ready to escalate if Phase 2 complications arise

