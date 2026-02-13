# UI IMPROVEMENTS IMPLEMENTATION PLAN
## Earthworm Borehole Logger - User Interface Enhancements

**Date:** February 13, 2026  
**Project:** Earthworm Borehole Logger  
**Prepared By:** AI Operating System - The Orchestrator

---

## EXECUTIVE SUMMARY

This document outlines a comprehensive implementation plan for 8 UI improvements requested by the user. The plan is based on thorough codebase research and investigation, with detailed step-by-step instructions for each improvement.

## RESEARCH FINDINGS

### Current State Analysis:

1. **LAS Curves Pane Legend**: Located in `src/ui/widgets/interactive_legend.py`, added to plot layout in `HoleEditorWindow.setup_ui()` with 1:4 ratio (legend:plotter)
2. **Zoom Slider**: Located in `HoleEditorWindow.setup_ui()` with `self.zoomSlider` and `self.zoomSpinBox`
3. **Create Interbedding Button**: Located in `HoleEditorWindow.setup_ui()` as `self.createInterbeddingButton`
4. **Export CSV Button**: Located in `HoleEditorWindow.setup_ui()` as `self.exportCsvButton`
5. **Settings Icon**: Main toolbar has settings action, but no dedicated icon location identified
6. **Pane Toggling**: Basic project explorer toggle exists (`toggle_project_explorer()`), no other pane toggles
7. **Editor Window Maximization**: Editor windows are created as `QMdiSubWindow` in MDI area, not maximizing by default
8. **LAS Curve Mapping**: Caliper and Resistivity already supported in curve visibility manager and settings dialog

---

## IMPLEMENTATION PLAN

### 1. REMOVE LAS CURVES PANE LEGEND

**Current Implementation:**
- File: `src/ui/main_window.py` (HoleEditorWindow.setup_ui())
- Legend widget: `self.interactive_legend`
- Layout: Added with `plot_layout.addWidget(self.interactive_legend, 1)` (1 part to legend)

**Implementation Steps:**
1. Remove legend widget addition from `plot_layout`
2. Update plotter ratio from 4:1 to use all available space
3. Remove `self.interactive_legend` initialization if no longer needed
4. Update any legend-related method calls

**Files to Modify:**
- `src/ui/main_window.py` (HoleEditorWindow class)
- `src/ui/widgets/interactive_legend.py` (may remove if unused)

**Expected Outcome:** More vertical space for curve plotting, legend functionality removed.

### 2. REMOVE ZOOM SLIDER AND FUNCTIONALITY

**Current Implementation:**
- File: `src/ui/main_window.py` (HoleEditorWindow.setup_ui())
- Widgets: `self.zoomSlider`, `self.zoomSpinBox`
- Layout: In `zoom_controls_layout` within main splitter container

**Implementation Steps:**
1. Remove zoom slider and spin box creation
2. Remove `zoom_controls_layout` and its widgets
3. Remove zoom-related signal connections
4. Remove zoom state manager if no longer needed
5. Update layout structure to fill space

**Files to Modify:**
- `src/ui/main_window.py` (HoleEditorWindow class)
- `src/ui/widgets/zoom_state_manager.py` (may remove if unused)

**Expected Outcome:** Cleaner UI without zoom controls, relying on scroll/pan for navigation.

### 3. REPLACE "CREATE INTERBEDDING" BUTTON WITH ICON

**Current Implementation:**
- File: `src/ui/main_window.py` (HoleEditorWindow.setup_ui())
- Button: `self.createInterbeddingButton`
- Location: In table container button layout
- Function: Connected to `self.create_manual_interbedding()`

**Implementation Steps:**
1. Create icon button (QToolButton) with appropriate icon
2. Add to toolbar or dedicated icon area near Settings
3. Connect to existing `create_manual_interbedding()` method
4. Remove original button from layout
5. Add tooltip for icon

**Files to Modify:**
- `src/ui/main_window.py` (HoleEditorWindow class)
- Icon resource file (to be created)

**Expected Outcome:** Space-saving icon instead of text button, same functionality.

### 4. REPLACE "EXPORT CSV" BUTTON WITH ICON

**Current Implementation:**
- File: `src/ui/main_window.py` (HoleEditorWindow.setup_ui())
- Button: `self.exportCsvButton`
- Location: In table container button layout
- Function: Connected to `self.export_editor_data_to_csv()`

**Implementation Steps:**
1. Create icon button (QToolButton) with export icon
2. Add to toolbar or dedicated icon area next to Interbedding icon
3. Connect to existing `export_editor_data_to_csv()` method
4. Remove original button from layout
5. Add tooltip for icon

**Files to Modify:**
- `src/ui/main_window.py` (HoleEditorWindow class)
- Icon resource file (to be created)

**Expected Outcome:** Space-saving icon instead of text button, same functionality.

### 5. CREATE ICON-BASED PANE TOGGLES

**Current Implementation:**
- File: `src/ui/main_window.py` (MainWindow class)
- Existing: `toggle_project_explorer()` method for project explorer dock
- Missing: Toggles for other panes

**Panes to Toggle:**
1. File Explorer Pane (Project Explorer dock)
2. LAS Curves Pane (Plot container in editor window)
3. Enhanced Stratigraphic Pane (Enhanced column container)
4. Data Editor Pane (Table container)
5. Overview Stratigraphic Column Pane (Overview container)

**Implementation Steps:**
1. Create toolbar with 5 toggle buttons (QToolButton)
2. Each button toggles visibility of corresponding pane
3. Store pane visibility state in settings
4. Add icons for each pane type
5. Implement toggle methods for each pane
6. Update layouts when panes are hidden/shown

**Files to Modify:**
- `src/ui/main_window.py` (MainWindow and HoleEditorWindow classes)
- Icon resource file (to be created)

**Expected Outcome:** Flexible workspace with collapsible panes for focused work.

### 6. MAXIMIZE EDITOR WINDOW ON START

**Current Implementation:**
- File: `src/ui/main_window.py` (MainWindow.open_hole_file())
- Editor windows created as `QMdiSubWindow` in MDI area
- Default size based on MDI area, not maximized

**Implementation Steps:**
1. Modify `open_hole_file()` method to maximize new editor windows
2. Use `subwindow.showMaximized()` instead of `subwindow.show()`
3. Ensure initial editor window in `setup_ui()` is also maximized
4. Test with multiple editor windows

**Files to Modify:**
- `src/ui/main_window.py` (MainWindow class)

**Expected Outcome:** Editor windows fill available MDI area space on creation.

### 7. ADD CALIPER AND RESISTIVITY TO LAS CURVE MAPPING

**Current Implementation:**
- Files: `src/ui/dialogs/settings_dialog.py`, `src/ui/widgets/curve_visibility_manager.py`
- Already supported in curve patterns and settings
- Need to ensure they appear in curve selection dropdowns

**Implementation Steps:**
1. Verify Caliper and Resistivity are in curve pattern matching
2. Ensure they appear in settings dialog curve mapping
3. Test with LAS files containing CAL/CD/RES/RT curves
4. Add to default curve visibility if needed

**Files to Modify:**
- `src/ui/dialogs/settings_dialog.py`
- `src/ui/widgets/curve_visibility_manager.py`
- `src/ui/widgets/curve_visibility_toolbar.py`

**Expected Outcome:** Caliper and Resistivity curves properly detected and displayed.

### 8. CREATE ICON AREA NEXT TO SETTINGS

**Current Implementation:**
- File: `src/ui/main_window.py` (MainWindow.create_toolbar())
- Settings action in main toolbar
- No dedicated icon area identified

**Implementation Steps:**
1. Create dedicated icon area/container in main window
2. Add Settings icon (existing)
3. Add Create Interbedding icon (from improvement 3)
4. Add Export CSV icon (from improvement 4)
5. Add pane toggle icons (from improvement 5)
6. Organize in logical groups with separators

**Files to Modify:**
- `src/ui/main_window.py` (MainWindow class)
- Icon resource file (to be created)

**Expected Outcome:** Consolidated icon-based controls in dedicated area.

---

## TECHNICAL DETAILS

### Icon Resources Required:
1. Create Interbedding icon
2. Export CSV icon
3. File Explorer Pane toggle icon
4. LAS Curves Pane toggle icon
5. Enhanced Stratigraphic Pane toggle icon
6. Data Editor Pane toggle icon
7. Overview Stratigraphic Column Pane toggle icon
8. Settings icon (may already exist)

### Layout Changes:
1. **HoleEditorWindow Layout:**
   - Remove legend from plot container
   - Remove zoom controls container
   - Update button layouts to use icons
   - Adjust splitter ratios for removed elements

2. **MainWindow Layout:**
   - Add icon toolbar/area
   - Add pane toggle controls
   - Update MDI area for maximized windows

### Settings Management:
1. Store pane visibility states
2. Store icon toolbar configuration
3. Maintain backward compatibility

---

## IMPLEMENTATION PHASING

### Phase 1: Core UI Changes (High Impact)
1. Remove LAS curves pane legend
2. Remove zoom slider
3. Maximize editor windows on start
4. Add Caliper/Resistivity mapping verification

### Phase 2: Icon Conversion
1. Replace Create Interbedding button with icon
2. Replace Export CSV button with icon
3. Create icon area next to Settings

### Phase 3: Pane Toggling System
1. Implement pane toggle icons
2. Add pane visibility management
3. Update layouts for toggled states

### Phase 4: Polish & Testing
1. Icon resource creation/selection
2. Tooltip and accessibility improvements
3. Comprehensive testing of all changes
4. Settings migration if needed

---

## RISK ASSESSMENT

### Technical Risks:
1. **Layout Breakage**: Removing elements may cause layout issues
   - Mitigation: Test incrementally, use Qt Designer if needed
2. **Icon Resource Management**: Need consistent icon set
   - Mitigation: Use standard Qt icons initially, custom later
3. **Pane Toggle Complexity**: Managing multiple pane states
   - Mitigation: Implement simple show/hide, add complexity later

### User Experience Risks:
1. **Discoverability**: Icons may be less discoverable than text
   - Mitigation: Comprehensive tooltips, optional text labels
2. **Learning Curve**: Changed UI may require adaptation
   - Mitigation: Gradual rollout, user documentation

### Compatibility Risks:
1. **Settings Migration**: Existing user settings may need updating
   - Mitigation: Backward compatibility layer, settings migration utility

---

## TESTING STRATEGY

### Unit Tests:
1. Test icon button functionality
2. Test pane toggle methods
3. Test curve mapping for Caliper/Resistivity
4. Test editor window maximization

### Integration Tests:
1. Test complete UI workflow with all changes
2. Test multiple editor windows
3. Test pane toggling in different configurations
4. Test with various LAS file types

### User Acceptance Tests:
1. Verify all requested improvements are implemented
2. Test intuitive use of icon-based controls
3. Verify no regression in existing functionality
4. Test performance with large datasets

---

## DELIVERABLES

1. **Modified Source Code** with all 8 improvements
2. **Icon Resources** for all new icon buttons
3. **Updated Documentation** reflecting UI changes
4. **Test Suite** covering new functionality
5. **Settings Migration** if required

---

## APPROVAL REQUIRED

Please review this implementation plan and provide approval to proceed with the changes. Specific areas for feedback:

1. Icon design preferences (standard Qt icons vs custom)
2. Pane toggle behavior preferences (hide vs collapse)
3. Icon placement preferences (toolbar vs dedicated area)
4. Testing priorities

Upon approval, I will begin implementation following the phased approach outlined above.