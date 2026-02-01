# Phase 4: Depth Correction (Interactive Lithology Boundaries)

**Purpose:** Replicating the "Lithology Drag" feature (1PD Page 124). Geologists adjust "driller depths" to match "geophysics (LAS) depths."

## Prerequisites
- Phase 3 completed (DictionaryManager, validation engine)
- PyQtGraphCurvePlotter widget from Phase 2
- HoleEditorWindow with 3‑pane layout

## Tasks

### Task 7: Interactive Lithology Boundaries

**Subtask 7.1: Represent boundaries as movable lines**
- In `PyQtGraphCurvePlotter` (or a new widget), add horizontal `pg.InfiniteLine` for each lithology boundary (From_Depth and To_Depth of each unit).
- Lines should be initially placed at correct depths based on dataframe.
- Use distinct colors/patterns for top (From_Depth) and bottom (To_Depth) boundaries.

**Subtask 7.2: Enable dragging**
- Set `movable=True` on boundary lines.
- Constrain movement to vertical axis only (depth).
- Implement snapping to nearby boundaries (optional but professional).

**Subtask 7.3: Update data on drag**
- Connect `sigDragged` signal to a handler.
- When a boundary line is dragged, adjust the corresponding `From_Depth`/`To_Depth` in the underlying Pandas DataFrame.
- Implement "Roof and Floor of Correction" logic:
  - Dragging a boundary affects the unit above (shrinks/expands) and the unit below (expands/shrinks) to keep total depth unchanged.
  - Update thickness calculations accordingly.
- Refresh the table view and stratigraphic column to reflect changes.

### Technical Requirements

1. **Data‑Layer Integration**
   - Connect boundary lines to specific rows in the lithology table.
   - Ensure changes propagate bidirectionally: table edits update lines, line drags update table.

2. **Visual Feedback**
   - Highlight the dragged line (e.g., thicker, different color).
   - Show depth value tooltip while dragging.
   - Provide undo/redo support (optional but recommended).

3. **Performance**
   - Use PyQtGraph's efficient graphics system.
   - Batch updates to avoid excessive redraws.

4. **Validation Integration**
   - After a drag operation, run the validation engine to check for new gaps/overlaps.
   - Show validation warnings in real‑time.

## Deliverables

1. **Updated `PyQtGraphCurvePlotter`** (or new widget) with movable boundary lines.
2. **Boundary‑Data mapping** that connects lines to table rows.
3. **Drag‑and‑drop logic** with roof/floor correction.
4. **Integrated UI** where dragging a line immediately updates the table and column.

## Integration Points

- **Existing `HoleEditorWindow`** – add boundary lines to the plot view.
- **Lithology table** – connect `dataChanged` signals to update line positions.
- **Validation engine** – trigger after each drag.

## Potential Challenges

- **Line‑row mapping** – need to reliably associate each line with a specific row index.
- **Concurrent modifications** – ensure table edits and line drags don't conflict.
- **Undo/redo** – may require a command‑pattern implementation.

## Success Criteria

- User can drag a lithology boundary line and see the table update instantly.
- Total depth remains constant after drag (roof/floor correction works).
- Validation errors are shown if drag creates gaps/overlaps.