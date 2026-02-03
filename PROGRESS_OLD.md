# PROGRESS.md

## Current Task
Redesign settings tab layout for better organization and aesthetics.

## Completed Steps
- Replaced monolithic settings layout with grouped sections (Lithology Rules, Display Settings, Analysis Settings, File Operations, Range Analysis)
- Added scroll area for better navigation in limited dock space
- Improved button layout with size policies for even distribution
- Added smart interbedding parameters visibility toggle (shows/hides parameters when checkbox toggled)
- Added "Reset to Defaults" button with confirmation dialog
- Connected fallback classification checkbox to auto‑save
- Imported missing default constants (curve thickness, merge thresholds, smart interbedding defaults)
- Fixed syntax error after replacement

## Next Step
Test settings dialog functionality and ensure all controls work correctly.

## Critical Variables / Paths
- `src/ui/main_window.py` – main window with settings tab
- `src/core/config.py` – default constants
- `src/ui/dialogs/settings_dialog.py` – legacy settings dialog (still exists but not used)

## Notes
- Settings are now organized in collapsible groups for clarity.
- Horizontal scrolling enabled for the lithology rules table.
- Auto‑save triggered on value changes (except Reset button).
- Reset button loads defaults from config constants.
- Ensure fallback classification is saved in settings (currently default False).