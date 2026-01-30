# Earthworm Feature & Bug Log

## Priority Features (from user)

### 1. Smart Interbedding Function
**Status:** Not working properly.
**Expected behavior:** Detect multiple consecutive small units that alternate between two types, merge them correctly, and write correct output.
**Notes:** This is an important feature for geological analysis.

### 2. Row Selection Synchronization
**Status:** Missing.
**Expected behavior:** When user selects a row in the editor table, automatically scroll the curve pane and stratigraphic column pane to the same depth location.

### 3. Click Lithology Unit → Editor
**Status:** Missing.
**Expected behavior:** When user clicks a lithology unit in the stratigraphic column, highlight/show the corresponding row in the editor table.

### 4. UI Redesign – Remove Tabbed System
**Status:** Current UI uses a QTabWidget with "Settings" and "Editor" tabs.
**Desired UI:** Editor as main window; settings moved to a series of buttons at the top (similar to 1pointdesktop software by Flout Software).
**Actions:**
- Remove QTabWidget.
- Create a toolbar or button bar at top for settings/controls.
- Ensure all settings are accessible via modal dialogs or side panels.

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