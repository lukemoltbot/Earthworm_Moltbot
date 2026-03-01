# EARTHWORM TASKS

## 🚀 OPTION B: FULL SYSTEM A MIGRATION (2026-03-01)

**Strategic Decision:** Migrate to DepthStateManager (System A) for 100% 1point Desktop architectural parity
**Target Status:** Production-ready viewport with pixel-perfect scroll synchronization
**Timeline:** 6-10 hours (9 phases)
**Risk Level:** 🟡 Medium (comprehensive testing mitigates risk)
**Specification:** See `.openclaw/OPTION_B_MIGRATION_SPEC.md` for detailed implementation plan

---

## 🔴 CRITICAL MIGRATION TASKS (IN ORDER)

### PHASE 1: Spike Analysis ⏱️ 1 hour
- [ ] [MIGRATION-P1-1] Map all System B/A dependencies
  - Identify all files importing UnifiedDepthScaleManager vs DepthStateManager
  - List breaking change targets
  - **Output:** SPIKE_ANALYSIS.txt with dependency map

### PHASE 2: EnhancedStratigraphicColumn Migration ⏱️ 1.5 hours
- [ ] [MIGRATION-P2-1] Fix signal connections in __init__
  - Connect viewportRangeChanged, cursorDepthChanged, zoomLevelChanged
  - **File:** src/ui/widgets/enhanced_stratigraphic_column.py
  - **Dependency:** Phase 1 complete
  
- [ ] [MIGRATION-P2-2] Implement state manager signal handlers
  - _on_state_viewport_changed(), _on_state_cursor_changed(), _on_state_zoom_changed()
  - **Deliverable:** Widget responds to external state changes
  
- [ ] [MIGRATION-P2-3] Wire scroll events to state manager
  - wheelEvent() → state_manager.set_viewport_range()
  - mousePressEvent() → state_manager.set_cursor_depth()
  - **Validation:** Create phase2.patch for rollback

### PHASE 3: PyQtGraphCurvePlotter Migration ⏱️ 1.5 hours
- [ ] [MIGRATION-P3-1] Add DepthStateManager parameter to __init__
  - **File:** src/ui/widgets/pyqtgraph_curve_plotter.py
  - **Dependency:** Phase 1 complete
  
- [ ] [MIGRATION-P3-2] Implement state manager handlers
  - _on_state_viewport_changed() → Update Y-axis range
  - _on_state_cursor_changed() → Update cursor line
  - _on_state_zoom_changed() → Adjust visible range
  
- [ ] [MIGRATION-P3-3] Wire scroll/drag events to state manager
  - wheelEvent() → state_manager.set_viewport_range()
  - mouseMoveEvent() → state_manager on boundary drag
  - **Validation:** Create phase3.patch for rollback

### PHASE 4: HoleEditorWindow Orchestration ⏱️ 1 hour
- [ ] [MIGRATION-P4-1] Create DepthStateManager instance
  - Replace UnifiedDepthScaleManager creation
  - **File:** src/ui/main_window.py
  - **Dependency:** Phases 2-3 complete
  
- [ ] [MIGRATION-P4-2] Pass state manager to widgets
  - PyQtGraphCurvePlotter(depth_state_manager=self.depth_state_manager)
  - EnhancedStratigraphicColumn(depth_state_manager=self.depth_state_manager)
  
- [ ] [MIGRATION-P4-3] Remove/comment out System B references
  - Comment out: UnifiedDepthScaleManager, PixelDepthMapper, GeologicalAnalysisViewport
  - Verify no broken imports
  - **Validation:** Create phase4.patch for rollback

### PHASE 5: UnifiedGraphicWindow Activation ⏱️ 1 hour
- [ ] [MIGRATION-P5-1] Verify synchronizer initialization
  - Ensure DepthSynchronizer, ScrollSynchronizer, SelectionSynchronizer created
  - **File:** src/ui/graphic_window/unified_graphic_window.py
  - **Dependency:** Phase 4 complete
  
- [ ] [MIGRATION-P5-2] Verify all signal wiring
  - Component signals → synchronizers → depth_state_manager
  - No circular signal loops
  
- [ ] [MIGRATION-P5-3] Enable System A feature flags
  - ENABLE_DEPTH_STATE_MANAGER = True
  - DISABLE_SYSTEM_B = True

### PHASE 6: System B Deprecation ⏱️ 30 minutes
- [ ] [MIGRATION-P6-1] Add deprecation warnings to System B
  - UnifiedDepthScaleManager, PixelDepthMapper
  - **File:** src/ui/widgets/unified_viewport/*.py
  - **Dependency:** Phase 5 complete
  
- [ ] [MIGRATION-P6-2] Consolidate duplicate code
  - Merge PixelDepthMapper utilities into DepthCoordinateSystem
  - **Deliverable:** System A has all System B capabilities
  
- [ ] [MIGRATION-P6-3] Comment out unused System B imports
  - Verify no active code uses System B
  - **Validation:** grep reports zero System B imports from main code

### PHASE 7: Comprehensive Testing ⏱️ 3 hours
- [ ] [MIGRATION-P7A-1] Unit test: EnhancedStratigraphicColumn
  - Test signal reception from state manager
  - Test scroll event propagation to state manager
  - **File:** tests/test_enhanced_strat_column_system_a.py
  - **Target:** 100% pass
  
- [ ] [MIGRATION-P7A-2] Unit test: PyQtGraphCurvePlotter
  - Test signal reception from state manager
  - Test Y-axis range updates
  - **File:** tests/test_curve_plotter_system_a.py
  - **Target:** 100% pass
  
- [ ] [MIGRATION-P7B-1] Integration test: Bidirectional scroll sync
  - Scroll curve → verify strat column follows
  - Scroll strat column → verify curve follows
  - **File:** tests/test_viewport_integration_system_a.py
  - **Target:** 100% pass
  
- [ ] [MIGRATION-P7B-2] Integration test: Cursor depth sync
  - Click strat column → verify plotter cursor updates
  - Click plotter → verify strat column highlights update
  - **Target:** 100% pass
  
- [ ] [MIGRATION-P7C-1] Regression test: Phase 5/6 compatibility
  - Run: tests/test_phase5_workflow_validation.py
  - Run: tests/test_pixel_alignment.py
  - Run: tests/test_phase3_integration.py
  - **Target:** 100% pass (no breakage)
  
- [ ] [MIGRATION-P7C-2] Pixel alignment validation
  - Verify depth-to-pixel round-trip <1px error
  - Compare Y-axis alignment between curve + strat column
  - **Target:** <1px maximum deviation

### PHASE 8: Escalation Checkpoint (CONDITIONAL) ⏱️ variable
- [ ] [MIGRATION-P8-1] IF tests fail → Escalate to Opus
  - Provide failing test output
  - Request root cause analysis + remediation plan
  - **Condition:** Any test fails in Phase 7
  - **Outcome:** Opus provides architectural fix or rollback guidance

### PHASE 9: Final Validation & Deployment ⏱️ 1 hour
- [ ] [MIGRATION-P9-1] Update HANDOFFS.md with migration summary
  - List all files changed
  - Document test results
  - Note any issues encountered and resolved
  
- [ ] [MIGRATION-P9-2] Commit migration to GitHub
  - Message: `feat: migrate viewport to System A (DepthStateManager) for 1point Desktop parity`
  - Tag: v1.0.0-system-a-migration
  
- [ ] [MIGRATION-P9-3] Create migration summary report
  - Before/after comparison
  - Architecture achievement checklist
  - Go-live validation

---

## CHECKPOINT GATES

| Gate | Triggered By | Action |
|------|--------------|--------|
| **P1→P2** | Spike analysis complete | Proceed if no showstoppers found |
| **P2→P3** | Phase 2 test pass | Proceed if strat column properly wired |
| **P3→P4** | Phase 3 test pass | Proceed if curve plotter properly wired |
| **P4→P5** | Phase 4 import check pass | Proceed if no broken imports |
| **P5→P6** | Signal wiring verification pass | Proceed if all synchronizers active |
| **P6→P7** | System B deprecation complete | Proceed to comprehensive testing |
| **P7→P8** | All Phase 7 tests pass | Proceed to deployment; skip P8 |
| **P7→P8 ALT** | Any Phase 7 test fails | Escalate to Opus; pause deployment |
| **P9 GO** | Phase 8 resolved OR tests pass | Deploy to main branch |

---

## SUCCESS CRITERIA (GO/NO-GO)

**GO Decision:** All criteria met → Commit to main and mark System A as stable
- [ ] Unit tests: 100% pass
- [ ] Integration tests: 100% pass
- [ ] Regression tests: 100% pass
- [ ] Pixel alignment: <1px verified
- [ ] No signal loops detected
- [ ] Code review approval (if required)

**NO-GO Decision:** Any criterion failed → Escalate and investigate
- [ ] Will NOT deploy with failing tests
- [ ] Will NOT merge if pixel alignment >2px
- [ ] Will NOT ignore signal loop warnings

---

## 🟢 COMPLETED SPRINT: Phase 4 Integration
- [✅ COMPLETE] Task Alpha: Infrastructure Stress Test (Verify swarm communication)
- [✅ COMPLETE] .gitignore: Created with comprehensive Python/project patterns
- [✅ COMPLETE] REFERENCE_SUMMARY.md: Created with 1point Desktop architecture comparison
- [✅ COMPLETE] VIEWPORT_REDESIGN.md: Created with dual-system analysis
- [✅ COMPLETE] STRATEGIC_ANALYSIS.md: Created comparing Options A/B/C

---

## 🔵 BACKLOG (POST-MIGRATION)

### Phase 3+ Features (Non-Critical)
- [ ] Task Delta: Multi-Window Correlation (Seam/Horizon lines) — Advanced, post-migration
- [ ] Task Epsilon: Layout Preset System (Window arrangements) — UX enhancement
- [ ] Task Zeta: Photo/Document System (Core photo + metadata) — Future release

### Maintenance
- [ ] LAS data export to Excel (CoalLog v3.1 support)
- [ ] Logging feature for LAS parsing performance
- [ ] Performance profiling (GPU acceleration evaluation)
