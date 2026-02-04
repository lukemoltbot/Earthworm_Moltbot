# Earthworm Moltbot Development Plan 2026-02-03
## Comprehensive Feature Implementation Roadmap

**Purpose:** Implement the 5-phase development plan outlined in the attached RTF document, transforming Earthworm Moltbot into a professional-grade geological analysis tool with enhanced settings, data schema, plotting, masking, and bug fixes.

**Status:** 🟢 Complete (100% complete)  
**Last Updated:** 2026-02-04 20:45 AEDT  
**Total Phases:** 5 | **Total Tasks:** 10 | **Total Subtasks:** 22  
**GitHub Repository:** https://github.com/lukemoltbot/Earthworm_Moltbot  
**Continuous Monitoring:** 15-minute progress updates via Discord (User ID: 1465989240746934410)

---

## 📊 Progress Summary
| Phase | Tasks Completed | Total Tasks | Completion |
|-------|----------------|-------------|------------|
| Phase 1 | 2/2 | 2 | 100% |
| Phase 2 | 2/2 | 2 | 100% |
| Phase 3 | 2/2 | 2 | 100% |
| Phase 4 | 2/2 | 2 | 100% |
| Phase 5 | 2/2 | 2 | 100% |
| **Overall** | **10/10** | **10** | **100%** |

**Active Sub-agents:** 0 (Development complete)  
**Last Commit:** Phase 5 Task 5.2 completed - settings safety workflow implemented  
**Next Update:** N/A (Development complete)

---

## 🗺️ Phase 1: Settings Optimization & Vertical Flow
**Purpose:** Transform the settings pane from a cramped horizontal layout into a clean, vertically-scrolling panel that maximizes usability.

### Task 1.1: Vertical Layout Overhaul & Anti-Horizontal Scroll
**Status:** ✅ Completed  
**Priority:** High  
**Estimated Complexity:** Medium  
**Files to Modify:** `src/ui/main_window.py`, `src/ui/dialogs/settings_dialog.py`

#### Subtasks:
- [x] **1.1.1:** Reconstruct Settings Pane using `QVBoxLayout` nested inside `QScrollArea`
- [x] **1.1.2:** Set scroll area policy to `setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)`
- [x] **1.1.3:** Use `QFormLayout` for setting rows (Label on top/left, Input on right)
- [x] **1.1.4:** Group related settings into `QGroupBox` containers (e.g., "Analysis Specs", "Plot Controls")
- [x] **1.1.5:** Test vertical scrolling functionality and ensure no horizontal scrollbars appear

### Task 1.2: Externalizing "Lithology Rules" to a Modal Dialog
**Status:** ✅ Completed  
**Priority:** High  
**Estimated Complexity:** Medium  
**Files to Modify:** `src/ui/main_window.py`, new `src/ui/dialogs/lithology_rules_dialog.py`

#### Subtasks:
- [x] **1.2.1:** Remove "Lithology Rules" table from settings sidebar
- [x] **1.2.2:** Create new class `LithologyRulesDialog(QDialog)` with full-size rules table
- [x] **1.2.3:** Add prominent button/icon in Settings Pane labeled "✏️ Edit Lithology Rules"
- [x] **1.2.4:** Ensure dialog pulls from main settings dictionary on open and pushes changes back on "Save"
- [x] **1.2.5:** Maintain compatibility with existing Save/Load project functionality

---

## 🗺️ Phase 2: CoalLog v3.1 Data Schema (37 Columns)
**Purpose:** Ensure the logging sheet is 1:1 compliant with industry standards.

### Task 2.1: Full Column Implementation
**Status:** ✅ Completed  
**Priority:** High  
**Estimated Complexity:** High  
**Files to Modify:** `src/ui/widgets/lithology_table.py`, `src/ui/models/pandas_model.py`

#### Subtasks:
- [x] **2.1.1:** Initialize `QTableWidget` (or Pandas model) with exact 37 columns in specified order
- [x] **2.1.2:** Update data model to handle all 37 columns
- [x] **2.1.3:** Ensure column headers match industry standard naming
- [x] **2.1.4:** Test data import/export with new column schema

### Task 2.2: Visibility Toggle System
**Status:** ✅ Completed  
**Priority:** Medium  
**Estimated Complexity:** Medium  
**Files to Modify:** `src/ui/main_window.py`, new `src/ui/dialogs/column_configurator_dialog.py`

#### Subtasks:
- [x] **2.2.1:** Add "Column Configurator" button in Settings pane
- [x] **2.2.2:** Create dialog with checklist to hide/show any of the 37 columns
- [x] **2.2.3:** Implement column visibility persistence in settings
- [x] **2.2.4:** Apply visibility changes dynamically to the table view

---

## 🗺️ Phase 3: Advanced LAS Comparative Plotting
**Purpose:** Overlay curves with different scales for easy visual analysis.

### Task 3.1: Dual-Axis Overlay (0-4 vs 0-300)
**Status:** ✅ Complete (5/5 subtasks done)  
**Priority:** High  
**Estimated Complexity:** High  
**Files to Modify:** `src/ui/widgets/pyqtgraph_curve_plotter.py`

#### Subtasks:
- [x] **3.1.1:** Implement dual-axis plotting using PyQtGraph's dual ViewBox system (functional equivalent)
- [x] **3.1.2:** Configure bottom axis (0.0 to 4.0) for SS, LS, and CD Density
- [x] **3.1.3:** Configure top axis (0 to 300) for Gamma Ray (GR)
- [x] **3.1.4:** Ensure proper axis labeling and legend placement
- [x] **3.1.5:** Test with sample LAS data to verify scaling accuracy

### Task 3.2: Plot Feature Controls
**Status:** ✅ Complete  
**Priority:** Medium  
**Estimated Complexity:** Medium  
**Files to Modify:** `src/ui/main_window.py`, `src/ui/widgets/pyqtgraph_curve_plotter.py`

#### Subtasks:
- [x] **3.2.1:** Add vertical list of checkboxes for curve visibility: [SS], [LS], [GR], [CD], [RES], [CAL]
- [x] **3.2.2:** Add "Bit Size (mm)" input field in settings
- [x] **3.2.3:** Implement anomaly detection: if `(CAL - BitSize) > 20`, highlight interval in red
- [x] **3.2.4:** Add toggle for anomaly highlighting on/off
- [x] **3.2.5:** Ensure real-time updates when checkboxes are toggled

---

## 🗺️ Phase 4: Masking & NL Analysis Logic
**Purpose:** Automate the handling of cased hole intervals and "Not Logged" data.

### Task 4.1: Casing Depth Integration
**Status:** ✅ Complete  
**Priority:** Medium  
**Estimated Complexity:** Low  
**Files to Modify:** `src/ui/main_window.py`, `src/core/analyzer.py`

#### Subtasks:
- [x] **4.1.1:** Add checkbox and numeric input for "Casing Depth (m)" in Settings pane
- [x] **4.1.2:** Implement logic: if checked, all rows where `Lithology To Depth <= Casing Depth` are forced to 'NL'
- [x] **4.1.3:** Update analysis to respect casing depth masking
- [x] **4.1.4:** Visual indication of masked intervals in table/plot

### Task 4.2: 'NL' Analysis Review
**Status:** ✅ Completed  
**Priority:** Medium  
**Estimated Complexity:** Medium  
**Files to Modify:** `src/ui/main_window.py`, new `src/ui/dialogs/nl_review_dialog.py`

#### Subtasks:
- [x] **4.2.1:** Add "Review NL Intervals" button in settings sidebar
- [x] **4.2.2:** Create dialog showing all 'NL' rows with calculated mean of SS, LS, and GR for those intervals
- [x] **4.2.3:** Implement calculation logic for mean values
- [x] **4.2.4:** Allow user to export NL analysis report

---

## 🗺️ Phase 5: Core Bug Fixes & Safety
**Purpose:** Resolve the interbedding data-write bug and enforce a clean user workflow.

### Task 5.1: Fix Smart Interbedding Data-Write
**Status:** ✅ Completed  
**Priority:** Critical  
**Estimated Complexity:** Low  
**Files to Modify:** `src/ui/dialogs/interbedding_dialog.py`, `src/ui/main_window.py`, `src/ui/widgets/lithology_table.py`, `src/ui/models/pandas_model.py`

#### Subtasks:
- [x] **5.1.1:** Ensure `InterbeddingDialog` correctly passes data back to main dataframe
- [x] **5.1.2:** Trigger full table refresh (`layoutChanged.emit()`) after dialog closes with "Apply"
- [x] **5.1.3:** Test interbedding functionality end-to-end
- [x] **5.1.4:** Verify data persistence after refresh

### Task 5.2: "Update Settings" Safety Workflow
**Status:** ✅ Completed  
**Priority:** Medium  
**Estimated Complexity:** Low  
**Files to Modify:** `src/ui/main_window.py`, `src/ui/dialogs/settings_dialog.py`

#### Subtasks:
- [x] **5.2.1:** Implement `self.settings_dirty` flag that triggers on sidebar input changes
- [x] **5.2.2:** Add prominent "Update Settings" button at bottom of Settings pane
- [x] **5.2.3:** On "Run Analysis" click: if `settings_dirty` is true, prompt user to confirm applying changes
- [x] **5.2.4:** Implement confirmation dialog with options to apply, discard, or cancel

---

## 🔄 Orchestration & Monitoring System

### Sub-agent Management Protocol
1. **Task Assignment:** Each subtask will be assigned to a dedicated sub-agent
2. **Naming Convention:** `DevPlan_PhaseX_TaskY_SubtaskZ_Description`
3. **Timeout:** 30 minutes per sub-agent (extendable if complex)
4. **Completion Criteria:** Subtask checklist items completed, code tested, commit created
5. **Cleanup:** Sub-agent removed after successful completion or failure

### Continuous Progress Monitoring
- **Update Frequency:** 15 minutes via cron job
- **Metrics Reported:** Overall progress %, phase progress %, active sub-agents count
- **Alert Conditions:** Zero active sub-agents between updates (spawn new one)
- **Failure Recovery:** Automatic retry with new sub-agent after 15 minutes of inactivity

### GitHub Integration
- **Commit Policy:** After each subtask completion
- **Commit Message Format:** `DevPlan Phase X.Y.Z: [Brief description of changes]`
- **Branch:** `main` (direct commits with thorough testing)
- **Validation:** Syntax checking before commit, basic functionality test

---

## 🚀 Execution Plan

### Immediate Actions (Initiation):
1. ✅ Create comprehensive roadmap (this document)
2. 🔄 Update ACTIVE_TASK.md to reflect new development plan
3. 🔄 Spawn first sub-agent for Phase 1 Task 1.1
4. 🔄 Establish 15-minute progress monitoring cron job

### Workflow Cycle (Continuous):
1. **Check Status:** Every 15 minutes, assess progress and active sub-agents
2. **Spawn Next:** If no active sub-agents, spawn next pending subtask
3. **Monitor:** Track sub-agent progress and intervene if stuck
4. **Commit:** On subtask completion, commit changes to GitHub
5. **Update:** Refresh roadmap status and progress percentages
6. **Repeat:** Continue until all phases complete (100%)

### Risk Mitigation:
- **Loop Avoidance:** Sub-agents have clear exit criteria and timeout limits
- **Error Handling:** SENTINEL protocol activated for autonomous troubleshooting
- **Independence:** Sub-agents work within defined boundaries with minimal supervision
- **Quality Control:** Syntax validation and basic testing before commits

---

## 📈 Progress Tracking Log

| Timestamp | Phase | Task | Subtask | Status | Commit Hash | Notes |
|-----------|-------|------|---------|--------|-------------|-------|
| 2026-02-03 20:30 | Init | Roadmap | Creation | ✅ Complete | - | Development plan roadmap created |
| 2026-02-03 20:31 | Setup | Orchestration | Monitoring | ⏳ Pending | - | 15-minute cron job to be established |
| 2026-02-03 21:43 | 2 | 2.2 | 2.2.1 | ✅ Complete | 0b5de22 | Added "Column Configurator" button to Settings pane with placeholder dialog |
| 2026-02-04 06:47 | 2 | 2.2 | 2.2.2-2.2.4 | ✅ Complete | - | Created column configurator dialog with persistence and dynamic visibility |
| 2026-02-04 11:05 | 3 | 3.1 | Start | 🔄 In Progress | - | Beginning dual-axis overlay implementation |
| 2026-02-04 11:15 | 3 | 3.1 | 3.1.1-3.1.4 | ✅ Complete | - | Dual-axis plotting, axis configuration, labeling, and legend added |
| 2026-02-04 11:35 | 3 | 3.2 | Start | 🔄 In Progress | - | Beginning plot feature controls implementation |
| 2026-02-04 11:45 | 3 | 3.2 | 3.2.1 & 3.2.5 | ✅ Complete | - | Curve visibility checkboxes added with real-time updates |
| 2026-02-04 12:43 | 3 | 3.2 | 3.2.2 | ✅ Complete | - | Bit Size input field added to settings |
| 2026-02-04 13:10 | 3 | 3.2 | 3.2.3 | ✅ Complete | - | Anomaly detection implemented: CAL - BitSize > 20 highlights intervals in red |

| 2026-02-04 13:30 | 3 | 3.2 | 3.2.4 | ✅ Complete | - | Anomaly highlight toggle added: checkbox to show/hide red intervals |
| 2026-02-04 14:55 | 3 | 3.1 | 3.1.5 | ✅ Complete | - | LAS scaling accuracy tested and verified; config.py updated for 0-300 API range |
| 2026-02-04 14:56 | 4 | 4.1 | 4.1.1-4.1.4 | ✅ Complete | - | Casing depth integration complete: checkbox, numeric input, NL forcing logic, visual indications |
| 2026-02-04 15:32 | 4 | 4.2 | Start | 🔄 In Progress | - | Beginning NL analysis review implementation |
| 2026-02-04 15:35 | 4 | 4.2 | 4.2.2-4.2.3 | ✅ Complete | - | NL review dialog designed with calculation logic for mean SS, LS, GR values |
| 2026-02-04 16:10 | 5 | 5.1 | 5.1.1-5.1.4 | ✅ Complete | - | Fixed smart interbedding data-write bug: added dataChangedSignal emission and layoutChanged signal |
---

**Next Scheduled Update:** 2026-02-04 07:00 AEDT  
**Projected Completion:** Based on 22 subtasks × 30 minutes each = 11 hours of active work (spread over continuous operation)