# UI Redesign Plan

## Current UI
- Tabbed interface: Settings tab + Editor tab.
- Editor tab contains three panels: curves, stratigraphic column, editor table.
- Settings tab contains many controls (mnemonic mapping, lithology rules, interbedding options, etc.)

## Desired UI (based on 1pointdesktop)
- Single main window (Editor) with no tabs.
- Settings moved to a series of buttons at the top (toolbar) that open modal dialogs or slide‑out panels.
- Clean, uncluttered workspace.

## Proposed Changes

### 1. Remove QTabWidget
- Delete the Settings tab as a separate tab.
- Move its contents into a new `SettingsDialog` (or multiple dialogs).
- Keep the Editor tab as the sole central widget.

### 2. Top Toolbar
Add a horizontal toolbar with buttons:
- **Load LAS** (already exists as a button, could move to toolbar)
- **Settings** – opens a dialog with tabs for:
  - Mnemonic Mapping
  - Lithology Rules
  - Interbedding Options
  - Visual Settings
- **Run Analysis** (already exists)
- **Export** (already exists)
- **Help** (optional)

### 3. Layout Adjustments
- Keep the existing splitter (curves | column | table).
- Possibly add a collapsible side panel for quick settings (e.g., curve visibility, depth range).
- Ensure the toolbar is always visible.

### 4. Implementation Steps
1. Create `SettingsDialog` class (or reuse existing `SettingsDialog` if exists).
2. Move all controls from the Settings tab into this dialog.
3. Remove the Settings tab from `main_window.py`.
4. Add a toolbar (`QToolBar`) or a row of buttons (`QHBoxLayout`) at the top of the main window.
5. Connect buttons to open dialogs.
6. Test that all functionality remains accessible.

### 5. Considerations
- Need to preserve the ability to quickly adjust settings without modal dialogs? Maybe keep some frequently used settings (e.g., curve ranges) as inline widgets in a side panel.
- Ensure the UI works on both Windows and macOS (Luke's testing environment).

## Next Actions
1. Wait for Luke's feedback on the mockup (screenshot of 1pointdesktop).
2. Create a simple wireframe sketch.
3. Start implementing after approval.