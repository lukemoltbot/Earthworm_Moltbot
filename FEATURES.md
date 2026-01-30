# Earthworm Feature & Bug Log

## Priority Features (from user)

### 1. Smart Interbedding Function
**Status:** Improved algorithm, needs testing with real data.
**Expected behavior:** Detect multiple consecutive small units that alternate between two or three lithology types, merge them correctly, and write correct output.
**Notes:** Algorithm now allows up to 3 lithologies, strict alternating pattern, and coarse interbedding (CB) for avg layer thickness >=200mm. Awaiting LAS file for validation.

### 2. Row Selection Synchronization
**Status:** Implemented.
**Expected behavior:** When user selects a row in the editor table, automatically scroll the curve pane and stratigraphic column pane to the same depth location.
**Implementation:** Added scroll_to_depth methods to both CurvePlotter and StratigraphicColumn; enhanced _on_table_row_selected.

### 3. Click Lithology Unit → Editor
**Status:** Implemented.
**Expected behavior:** When user clicks a lithology unit in the stratigraphic column, highlight/show the corresponding row in the editor table.
**Implementation:** Added unitClicked signal and mousePressEvent to StratigraphicColumn; added _on_unit_clicked slot.

### 4. UI Redesign – Remove Tabbed System
**Status:** In progress.
**Desired UI:** Editor as main window; settings moved to a series of buttons at the top (similar to 1pointdesktop software by Flout Software).
**Actions completed:**
- Moved control panel (Load LAS, curve selection, Run Analysis) above the tab widget, making it always visible.
- Settings tab still exists but no longer contains the control panel.
**Remaining actions:**
- Move remaining settings (lithology rules, visual settings, interbedding options) into a dialog or side panel.
- Remove Settings tab entirely.
- Add toolbar with Settings button.

## Bugs (to be identified)
- Run the app and test core workflows; log any crashes, freezes, or incorrect outputs.
- Smart interbedding not working (already listed).
- Other bugs may surface during testing.

## Licensing & Packaging (Lower Priority)
- Need licensing system (single‑computer, subscription).
- Prefer easiest to manage and most secure (fraud prevention).
- Online vs offline activation – research pros/cons.
- Packaging for Windows (PyInstaller + InnoSetup) and macOS (.app for testing).

---

## Testing Notes

### App Launch
- Dependencies installed successfully (PyQt6, pandas, lasio, etc.).
- UI imports OK.
- Need to run app with sample data to verify functionality.

### Sample Data
- No sample LAS files in repo.
- Need to acquire or generate a small test LAS file.

---

## Next Actions

1. **Run the app** (if possible with virtual display) or ask Luke to run and provide screenshots/observations.
2. **Examine smart interbedding code** (`src/core/analyzer.py`) to understand current logic.
3. **Plan UI redesign** – sketch new layout, identify which settings need to be moved.
4. **Implement row‑selection synchronization** (editor → curve/column).
5. **Implement click‑to‑select** (column → editor).
6. **Fix smart interbedding** after understanding the bug.

---

*This log will be updated as we discover more.*