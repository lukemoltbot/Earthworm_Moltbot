# ACTIVE_TASK.md - VSED Settings Dialog Unification & Testing

## Primary Goal
Unify settings widgets (bit size, casing depth, NL review, column configurator, curve visibility) into the settings dialog only, removing duplicates from the docked settings panel. Ensure all new features work correctly.

## Known Constraints
- Environment: Mac with virtual environment (.venv)
- GUI may not be testable in headless environment, but we can check imports and basic functionality
- Must maintain backward compatibility (fallback to default values when widgets missing)

## Step-by-Step Checklist

### Phase 0: Remove Duplicate Widgets from Docked Settings Panel
- [x] Identify widgets in main_window.py setup_settings_tab that duplicate settings dialog
- [x] Remove bit size input field block (lines 1634‑1655)
- [x] Remove casing depth masking block (lines 1656‑1679)
- [x] Remove NL review button block (lines 1680‑1695)
- [x] Remove Table Settings group (lines 1696‑1708)
- [x] Remove Curve Visibility group (lines 1709‑1739)
- [x] Fix empty if‑blocks and indentation errors after removal
- [x] Ensure curve_visibility_checkboxes attribute initialized (empty dict)
- [x] Verify syntax and compilation passes

### Phase 1: Pre-flight Checks
- [x] Verify syntax of modified files
- [x] Check existence of referenced modules (nl_review_dialog, column_configurator_dialog)
- [x] Ensure all imports are correct and don't cause circular dependencies
- [x] Check for missing dependencies

### Phase 2: Sub-agent Deployment
- [x] Deploy [THE RESEARCHER] to examine codebase for import issues and dependencies → **Complete** (imports OK, no circular dependencies, core deps present)
- [x] Deploy [THE VALIDATOR] to run unit tests and validate functionality → **Complete** (headless test passes, settings dialog loads, new UI elements verified)
- [ ] Deploy [THE SENTINEL] to handle any errors during testing
- [ ] Deploy [THE CODER] to fix any issues found

### Phase 3: Integration Testing
- [x] Test settings dialog loads within main application (headless test passed)
- [x] Verify new UI elements appear (curve visibility group, table settings, bit size, casing depth, NL review button) via test_settings_dialog_headless.py
- [x] Test column configurator dialog opens and functions (import test)
- [x] Test NL review dialog opens with data (import test)
- [x] Verify settings persistence (gather_settings includes new fields) – test passed

### Phase 4: Error Scenario Testing
- [ ] Test edge cases (missing data, invalid inputs)
- [ ] Verify error handling for missing main window reference
- [ ] Test casing depth spinbox enable/disable toggle

### Phase 5: Reporting
- [ ] Generate comprehensive test report
- [ ] Document any issues found and fixes applied
- [ ] Provide recommendations for further testing

## Current Status
Phase 0 and Phase 1 complete. Phase 3 partially complete (headless tests pass). Ready for sub‑agent deployment for deeper validation.