# ACTIVE_TASK.md - Earthworm Moltbot Phase 1: MDI Framework & Project Indexing

## Primary Goal
Implement Phase 1 of the 1PD UI/UX Roadmap: Transition from tab-based interface to Multiple Document Interface (MDI) with Project Explorer sidebar.

## Known Constraints
- **Environment**: macOS, Python 3.14, PyQt6, Earthworm_Moltbot workspace
- **Paths**:
  - Project root: `/Users/lukemoltbot/clawd/Earthworm_Moltbot/`
  - Source code: `src/ui/main_window.py` (primary file being modified)
  - Roadmap: `1PD_UI_UX_ROADMAP.md` (master plan)
- **Phase 1 Deadline**: ASAP, with periodic 5-minute progress updates requested
- **Discord Limits**: 1,200 character cap

## Phase 1: The MDI Framework & Project Indexing

### Task 1: Transition to Multiple Document Interface (MDI)
- [x] **Subtask 1.1**: Replace central layout with `QMdiArea` in `main_window.py`
  - Status: **Completed** - MDI area implemented, editor window converted to subwindow
- [x] **Subtask 1.2**: Create `Window` menu with tile, cascade, and close actions
  - Status: **Completed** - Window menu with tile/cascade/close actions added

### Task 2: Persistent "Holes List" (The Sidebar)
- [x] **Subtask 2.1**: Create `QDockWidget` containing a `QTreeView`
  - Status: **Completed** - QDockWidget with QTreeView added as "Project Explorer"
- [x] **Subtask 2.2**: Implement "Root Folder Scanner" using `QFileSystemModel`
  - Status: **Completed** - QFileSystemModel with name filters for .csv/.xlsx/.las files
- [ ] **Subtask 2.3**: Map double-clicks to `open_hole()` function that spawns new MDI SubWindow
  - Status: **In Progress** - Double-click mapping implemented; `open_hole()` loads file into existing editor (needs multi-window support)

## Phase 1 Progress Summary
- **Overall Completion**: 80% (4/5 subtasks completed)
- **Current Focus**: Complete Subtask 2.3 (multi-window hole support)

## Technical Implementation Details

### Changes Made to `src/ui/main_window.py`:
1. Added `QTreeView` import to PyQt6 imports
2. Added `QFileSystemModel` import to QtGui imports  
3. Created `holes_dock` QDockWidget with tree view
4. Configured `QFileSystemModel` to show current directory with file type filters
5. Connected `doubleClicked` signal to `on_hole_double_clicked` method
6. Implemented `open_hole()` method (currently loads into existing editor)

### Remaining Work for Subtask 2.3:
1. Create new `HoleEditorWindow` widget class for multi-hole support
2. Modify `open_hole()` to spawn new MDI subwindow instead of reusing editor
3. Ensure each hole window has its own curve plotter, strat column, and editor table
4. Test opening multiple holes simultaneously

## Universal Resilience Protocol Compliance
1. **Search-Before-Crash**: Maintained - using ACTIVE_TASK.md for state tracking
2. **Discord Safety Valve**: 1,200 character cap observed for progress updates
3. **Context & Task Switching**: ACTIVE_TASK.md updated with current task state
4. **Self-Correction**: All changes compiled and syntax-checked
5. **Autonomous Error Recovery**: Ready to fix any issues with MDI implementation

## Next Immediate Actions
1. Complete Subtask 2.3: Make `open_hole()` spawn new MDI subwindow
2. Test MDI functionality with multiple hole windows
3. Verify project explorer navigation works correctly
4. Move to Phase 2 (Synchronized Graphic Log) once Phase 1 is 100% complete

---
*Last updated: 2026-02-01 19:25 AEST (GMT+11)*