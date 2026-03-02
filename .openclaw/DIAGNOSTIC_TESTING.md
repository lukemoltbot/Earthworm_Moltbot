# DIAGNOSTIC TESTING - Viewport Synchrony Issue

**Status:** Investigating why System A widgets appear in separate panes instead of unified viewport  
**Date:** 2026-03-02  
**User Report:** Curves pane and Strat column pane are separate, both not rendering together

---

## OBSERVATIONS FROM TESTING

**What's Working:**
- ✅ Application starts without errors
- ✅ LAS file loads successfully
- ✅ Curves mapping works
- ✅ Settings load correctly
- ✅ Analysis runs successfully
- ✅ **LAS Curves pane shows data** (populated)

**What's NOT Working:**
- ❌ Data Editor pane: Completely blank (no grid, no rows)
- ❌ Enhanced Strat Column: Completely blank (no lithology rendering)
- ❌ Panes NOT unified: Curves and Strat Column in SEPARATE panes (not side-by-side)
- ❌ Scroll synchronization: Cannot verify if working (panes separate)

**Side Issue:**
- PyQtGraph error: `setTickTextOffset` invalid parameter (non-blocking, doesn't prevent rendering)

---

## DIAGNOSTIC TESTING PROTOCOL

To identify the root cause, run these tests in order.

### Test 1: Debug Output Inspection

**Objective:** See what widgets are being created and their parent relationships

**Steps:**
```bash
# 1. Pull latest diagnostic code
cd /path/to/Earthworm_Moltbot
git pull origin main

# 2. Run and capture DEBUG output
python main.py 2>&1 | tee test_output.log

# 3. Load LAS file, map curves, run analysis

# 4. Search for debug output
grep "DEBUG (UnifiedGraphicWindow)" test_output.log
grep "DEBUG (HoleEditorWindow)" test_output.log
```

**Expected Output (If Working Correctly):**
```
DEBUG (UnifiedGraphicWindow): strat_column type=EnhancedStratigraphicColumn, is None=False
DEBUG (UnifiedGraphicWindow): strat_column parent=HoleEditorWindow
DEBUG (UnifiedGraphicWindow): curve_plotter type=PyQtGraphCurvePlotter, is None=False
DEBUG (UnifiedGraphicWindow): curve_plotter parent=HoleEditorWindow
DEBUG (UnifiedGraphicWindow): Added strat_column to splitter
DEBUG (UnifiedGraphicWindow): Added curve_plotter to splitter
DEBUG (UnifiedGraphicWindow): Component area created with splitter, count=2
DEBUG (HoleEditorWindow): Creating unified_viewport...
DEBUG (HoleEditorWindow): unified_viewport created, type=UnifiedGraphicWindow
DEBUG (HoleEditorWindow): unified_viewport added to unified_layout
```

**What This Tells Us:**
- Widget types are correct
- Parent widgets are HoleEditorWindow (expected)
- Both widgets added to splitter (expected)
- Splitter has 2 children (expected)

---

### Test 2: Visual Inspection of Widget Layout

**Objective:** Determine if unified_viewport is visible and contains both widgets

**Questions to Answer:**
1. **Is there ONE pane that contains both curves and strat column?**
   - YES: Unified viewport is working, issue is data flow
   - NO: Unified viewport not visible, or panes are truly separate

2. **Are curves and strat column in the SAME visual container?**
   - YES: Can you see a divider/seam between them?
   - NO: They're in different panes, unified viewport failed

3. **What panes are visible after "Run Analysis"?**
   - Expected: Unified viewport (curves + strat) | Data Editor | Overview
   - Actual: [Report what you see]

**Report:**
```
Visible panes after analysis:
[ ] Unified viewport (curves left + strat right + seam divider)
[ ] Data Editor (populated table)
[ ] Overview (right sidebar)
OR
[ ] Curves pane (standalone)
[ ] Strat column pane (standalone)
[ ] Data Editor pane (blank)
[ ] Overview pane
```

---

### Test 3: Widget Geometry Inspection (Advanced)

**Objective:** Check if unified_viewport and its contents have valid geometry

**Add to main_window.py after load completes:**
```python
# In HoleEditorWindow, after Run Analysis finishes
print(f"\n=== WIDGET GEOMETRY DEBUG ===")
print(f"unified_viewport visible: {self.unified_viewport.isVisible()}")
print(f"unified_viewport geometry: {self.unified_viewport.geometry()}")
print(f"unified_viewport size: {self.unified_viewport.size().width()}x{self.unified_viewport.size().height()}")

if hasattr(self.unified_viewport, 'main_splitter'):
    print(f"main_splitter visible: {self.unified_viewport.main_splitter.isVisible()}")
    print(f"main_splitter geometry: {self.unified_viewport.main_splitter.geometry()}")
    print(f"main_splitter count: {self.unified_viewport.main_splitter.count()}")
    print(f"main_splitter sizes: {self.unified_viewport.main_splitter.sizes()}")
    
    print(f"strat_column visible: {self.unified_viewport.strat_column.isVisible()}")
    print(f"strat_column geometry: {self.unified_viewport.strat_column.geometry()}")
    
    print(f"curve_plotter visible: {self.unified_viewport.curve_plotter.isVisible()}")
    print(f"curve_plotter geometry: {self.unified_viewport.curve_plotter.geometry()}")
```

---

## DATA FLOW INVESTIGATION

**Objective:** Determine if data is reaching the widgets

### Question 1: Is data reaching curvePlotter?
- Check: Are curves visible in the curves pane?
- Answer: **YES** (user confirmed curves are visible and populated)
- Conclusion: curvePlotter.set_data() is working ✓

### Question 2: Is data reaching enhancedStratColumnView?
- Check: Are lithology units visible?
- Answer: **NO** (strat column is blank)
- Possible causes:
  - enhancedStratColumnView.set_classified_data() not called
  - enhancedStratColumnView.draw_column() not called
  - Data format incompatible
  - Widget has zero geometry

### Question 3: Is data reaching editorTable?
- Check: Are rows visible in the table?
- Answer: **NO** (table is completely blank)
- Possible causes:
  - Data model not set on table
  - Table has zero geometry
  - Model is empty

---

## ROOT CAUSE HYPOTHESES

### Hypothesis 1: Unified Viewport Not Displayed
**Problem:** unified_viewport exists but is not visible (hidden or zero size)
- Widgets inside it (curves, strat) are in splitter but splitter is too small
- User sees widgets appearing elsewhere (old containers or overlays)

**Evidence:** Panes are separate

**Test:** Check geometry in Test 3 above

**Fix:** Ensure unified_viewport gets space in layout

---

### Hypothesis 2: Widgets Still in Original Parents
**Problem:** Widgets were created with parent containers, adding to splitter doesn't remove from original parent
- Widgets appear in original layout AND in splitter
- One set is visible (original), other is hidden (splitter)

**Evidence:** Panes are separate

**Test:** Check parent widgets in debug output (Test 1)

**Fix:** Reparent widgets before adding to splitter

---

### Hypothesis 3: Data Not Reaching Enhanced Widgets
**Problem:** unified_viewport works correctly, but data flow is broken
- Curves show because curvePlotter.set_data() is called directly
- Strat column blank because enhancedStratColumnView methods not called correctly
- Table blank for similar reason

**Evidence:** Curves visible but strat and table blank

**Test:** Check if set_classified_data() is called (add debug print)

**Fix:** Ensure data methods are called on widgets after analysis

---

## NEXT DIAGNOSTIC STEPS

1. **Run Test 1** → Provide debug output (save to file)
2. **Run Test 2** → Describe layout visually (which panes visible)
3. **Run Test 3** (if needed) → Provide geometry values

Once we have this information, we can narrow down the root cause.

---

## PYQTGRAPH ERROR (Side Issue)

**Error:** `ValueError: Argument 'tickTextOffset' must be int`

**Location:** pyqtgraph_curve_plotter.py, line 1230-1233

**Issue:** `setTickTextOffset()` doesn't exist; `setStyle()` parameter is wrong type

**Fix Approach:**
```python
# BEFORE (broken):
bottom_axis.setTickTextOffset(5)

# AFTER (working):
bottom_axis.setStyle(tickTextOffset=5)  # Must be int, not list
```

**Status:** Non-blocking (doesn't prevent rendering), will fix after main issue

---

## SUMMARY

**Current Status:**
- ✅ Application starts and runs analysis
- ✅ Curves render with data
- ❌ Panes not unified (separate containers)
- ❌ Strat column and table blank

**Next Action:**
Run diagnostic tests above and report findings. This will tell us whether the unified_viewport architecture is working or if there's a data flow issue.

