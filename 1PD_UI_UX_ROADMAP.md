# 1PD UI/UX Development Roadmap for Earthworm

**Purpose:** Bring Earthworm_Moltbot MVP up to the professional standard of **1point Desktop (1PD)**, transitioning from a "script-style" application to an "Integrated Development Environment (IDE)" for geologists.

**Status:** 🟡 In Progress  
**Last Updated:** 2026-02-01  
**Primary Reference:** RTF roadmap provided by Luke

---

## Phase 1: The MDI Framework & Project Indexing
**Purpose:** 1PD allows geologists to work on 20+ holes at once. A single-window layout fails here. You need an architecture that supports multiple floating windows and a persistent "Project Explorer."

### Task 1: Transition to Multiple Document Interface (MDI)
- [ ] **Subtask 1.1:** In `main.py`, replace your central layout with `QMdiArea`. Set `self.mdi_area.setViewMode(QMdiArea.ViewMode.SubWindowView)`.
- [ ] **Subtask 1.2:** Create a `Window` menu with actions for `Tile`, `Cascade`, and `Close All`.
- **How:** This allows users to drag a Graphic Log to a second monitor while keeping the Map on the first—crucial for 1PD workflows.

### Task 2: Persistent "Holes List" (The Sidebar)
- [ ] **Subtask 2.1:** Create a `QDockWidget` containing a `QTreeView`.
- [ ] **Subtask 2.2:** Implement a "Root Folder Scanner" using Python's `os.walk` or `pathlib`. It should index all `.csv`/`.xlsx` files and group them by folder (Lease/Project).
- [ ] **Subtask 2.3:** Map double-clicks in the tree to an `open_hole(path)` function that spawns a new MDI SubWindow.
- **Why:** Geologists shouldn't use "File > Open" for every hole. They need a "library view" of the whole site.

---

## Phase 2: The Synchronized Graphic Log (The "Viewer")
**Purpose:** This is the heart of 1PD. The "Magic" of the software is that the graph and the spreadsheet are the same piece of data shown in two ways.

### Task 3: The 3-Pane Hole Window
- [ ] **Subtask 3.1:** Create a custom `QWidget` called `HoleEditorWindow`. Inside, use a `QSplitter` (Horizontal) to divide the screen into three: [Plot View | Data Table | Overview View].
- [ ] **Subtask 3.2:** Implement **PyQtGraph** in the Plot View. Use a vertical `Y-axis` where 0 is at the top (surface).
- [ ] **Subtask 3.3:** Standardize the "Overview View" on the far right. It should show the *entire* hole (0 to 500m) while the "Plot View" shows a zoomed-in section (e.g., 20m).

### Task 4: Bidirectional Synchronization (The "1PD Feel")
- [ ] **Subtask 4.1:** Connect the Table's `selectionChanged` signal to the Plot's `setYRange`.
    - *Logic:* When a user clicks "Seam A" in the table, the plot automatically scrolls/zooms to that depth.
- [ ] **Subtask 4.2:** Connect the Plot's mouse click signal to the Table's `selectRow`.
    - *Logic:* When a user clicks a lithology block on the graph, the table highlights that row.
- **How:** Use a shared `QtCore.QItemSelectionModel` between the View and the Table.

---

## Phase 3: Geological Logic & Validation
**Purpose:** 1PD isn't just a viewer; it's a "truth checker." It ensures data follows the **CoalLog** standard.

### Task 5: The Dictionary Manager
- [ ] **Subtask 5.1:** Create a `DictionaryManager` class that loads your `code_csv_explanation.md` logic.
- [ ] **Subtask 5.2:** Implement `QComboBox` delegates inside your `QTableView`. When a user clicks the "Lithology" column, they should see a searchable list of valid codes (e.g., CO for Coal, SS for Sandstone).
- [ ] **Subtask 5.3:** Map F3 key to open a "Code Search" pop-up.

### Task 6: Real-time Validation Engine
- [ ] **Subtask 6.1:** Write a `validate_hole(dataframe)` function. It must check for:
    - *Gaps:* Does `To_Depth` of row 1 equal `From_Depth` of row 2?
    - *Overlaps:* Is `From_Depth` ever greater than `To_Depth`?
    - *Total Depth:* Does the last row match the header's "TD"?
- [ ] **Subtask 6.2:** UI Feedback. Use a `QStyledItemDelegate`. If a cell fails validation, paint the background `Qt.red`.
- **Why:** This reduces human error during data entry, which is the primary reason mining companies buy 1PD.

---

## Phase 4: Depth Correction (The "Pro" Feature)
**Purpose:** Replicating the "Lithology Drag" feature (1PD Page 124). Geologists adjust "driller depths" to match "geophysics (LAS) depths."

### Task 7: Interactive Lithology Boundaries
- [ ] **Subtask 7.1:** In your PyQtGraph plot, represent each lithology boundary as a `pg.InfiniteLine` (Horizontal).
- [ ] **Subtask 7.2:** Enable `movable=True` for these lines.
- [ ] **Subtask 7.3:** On the `sigDragged` signal, update the `To_Depth` and `From_Depth` in the Pandas DataFrame and refresh the Table.
- **How:** This requires a "Roof and Floor of Correction" logic. If I drag a line at 50m, I must shrink the unit above and expand the unit below so the total depth stays the same.

---

## Phase 5: GIS & Cross-Sections
**Purpose:** Moving from "Hole view" to "Site view."

### Task 8: The Interactive Map Window
- [ ] **Subtask 8.1:** Create a new MDI window using `pg.PlotWidget` (but as a 2D Scatter Plot).
- [ ] **Subtask 8.2:** Plot points using the `Easting` and `Northing` columns from your CSV headers.
- [ ] **Subtask 8.3:** Implement "Lasso Selection." When the user circles holes on the map, highlight them in the "Holes List" sidebar.

### Task 9: The Cross-Section (Fence Diagram)
- [ ] **Subtask 9.1:** Create a tool that takes 3+ selected holes and creates a new window.
- [ ] **Subtask 9.2:** Plot the holes side-by-side. Calculate the "True Spacing" (distance between Hole A and Hole B) using the Pythagorean theorem on their coordinates.
- [ ] **Subtask 9.3:** Draw polygons between the holes connecting rows with the same "Seam Name."
- **Why:** This allows the geologist to see if a coal seam is dipping or thinning across the project area.

---

## Technical Infrastructure Checklist
To make this performant in Python:

- [ ] **Threading:** Use `QThread` for loading LAS files and running validations so the UI doesn't freeze.
- [ ] **Pandas Integration:** Use `PandasModel` (a custom `QAbstractTableModel`) to link your CSV data directly to the Qt Views.
- [ ] **Styles:** Create a `styles.qss` file to give the app a professional dark or light mode, moving away from the default Windows 95 look.
- [ ] **Configuration:** Expand your `earthworm settings.json` to include "Last Workspace" (which windows were open) so the user can resume work exactly where they left off (1PD Page 26).

---

## Progress Tracking

| Phase | Task | Subtask | Status | Notes |
|-------|------|---------|--------|-------|
| 1 | 1 | 1.1 | Completed | MDI area implemented, editor window converted to subwindow |
| 1 | 1 | 1.2 | Completed | Window menu with tile/cascade/close actions added |
| 1 | 2 | 2.1 | Completed | QDockWidget with QTreeView added |
| 1 | 2 | 2.2 | Completed | QFileSystemModel with name filters for .csv/.xlsx/.las files |
| 1 | 2 | 2.3 | Completed | Double-click mapping opens new MDI subwindow with HoleEditorWindow; file path set and window title updated |
| 2 | 3 | 3.1 | Completed | HoleEditorWindow created with 3-pane layout using QSplitter: [Plot View | Data Table | Overview View] |
| 2 | 3 | 3.2 | Completed | PyQtGraphCurvePlotter widget created and integrated as left pane |
| 2 | 3 | 3.3 | Completed | Overview view shows entire hole (0-500m) with zoom overlay; view range changes update overlay |
| 2 | 4 | 4.1 | Completed | Table selection scrolls plot view to selected unit's depth |
| 2 | 4 | 4.2 | Partially Completed | Plot click signal connected; needs depth-to-row mapping logic |
| 3 | 5 | 5.1 | Completed | DictionaryManager class created with caching and fallback support |
| 3 | 5 | 5.2 | Completed | QComboBox delegates integrated with DictionaryManager for all code columns |
| 3 | 5 | 5.3 | Completed | F3 key mapped to CodeSearchDialog with search across all categories |
| 3 | 6 | 6.1 | Completed | Real-time validation engine with gap/overlap/TD checks and structured results |
| 3 | 6 | 6.2 | Completed | ValidationDelegate paints error/warning cells; ValidationPanel for UI feedback |
| 4 | 7 | 7.1 | Completed | Boundary lines added to PyQtGraphCurvePlotter with movable=True, distinct colors for top/bottom, and mapping to row indices |
| 4 | 7 | 7.2 | Completed | Dragging enabled with constraints, snapping, visual feedback, and tooltips; Integrated with HoleEditorWindow |
| 4 | 7 | 7.3 | Completed | Roof and floor correction logic implemented, data updates on drag, validation integration; Connected to LithologyTableWidget |
| 5 | 8 | 8.1 | Completed | MapWindow class created with PyQtGraph scatter plot, integrated into MDI framework with Window menu |
| 5 | 8 | 8.2 | Completed | Enhanced coordinate extraction from CSV/LAS/Excel files, added point labels, tooltips, and color coding |
| 5 | 8 | 8.3 | Not Started | |
| 5 | 9 | 9.1 | Not Started | |
| 5 | 9 | 9.2 | Not Started | |
| 5 | 9 | 9.3 | Not Started | |

---

## Notes & Questions for Luke

1. **Priority:** Which phase should be tackled first? (Likely Phase 1: MDI Framework)
2. **Existing Code:** Should we build upon the current `main_window.py` or refactor significantly?
3. **Timeline:** Any deadlines or milestones?
4. **Dependencies:** Are there any specific libraries or versions required (PyQtGraph version, etc.)?
5. **Testing:** How should we validate each subtask? Manual testing with sample data?

---
*This roadmap is the primary reference for UI/UX development. Update checkboxes and progress table as tasks are completed.*