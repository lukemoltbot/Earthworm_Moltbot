# Analysis: 1 Point Desktop vs Earthworm Graphic Window Implementation

## Executive Summary

After reviewing the 1 Point Desktop Manual and comparing the MainGraphicWindow with your EarthwormGraphicWindow, I've identified **the core architectural difference** you need to implement to achieve perfect alignment between the stratigraphic column and LAS curves.

---

## What 1 Point Desktop Does (From Manual, Section: "Selecting Lithology", Page 88)

### The Critical Feature
> "Wherever you click, the other screen will synchronise and display the same depths."

**Key Architecture Points:**

1. **Shared Depth Tracking System**
   - The graphic log maintains a single "cursor depth" or "active depth range"
   - When ANY element changes (data table selection, graphic log click, or curve interaction), this central depth is updated
   - ALL OTHER ELEMENTS immediately reflect this same depth

2. **Three Synchronized Components:**
   - **Lithology Data Table** (left side)
   - **Graphic Log/Stratigraphic Column** (center)
   - **LAS Curves Display** (right side)
   - **Preview/Overview Window** (far right)

3. **Bidirectional Synchronization**
   - Clicking on lithology table → all components scroll to show that depth
   - Clicking on graphic log → table and curves highlight that depth
   - Clicking on curves → lithology table selects corresponding row
   - Clicking on preview window → main view updates to that depth

4. **Vertical Alignment is Achieved Through:**
   - **Common Depth Axis** - All three components use the exact same depth scale
   - **Event-Driven Updates** - When depth changes, depth-dependent renders occur
   - **Shared Data Model** - The underlying hole data (lithology intervals) determines all visualizations

---

## What Your EarthwormGraphicWindow is Missing

Looking at your implementation, the issue is **architectural isolation**:

### Current Issues:

1. **Separate Rendering Contexts**
   - Your stratigraphic column (left panel with colors) renders independently
   - Your LAS curves (center/right panel) render independently
   - They don't share a **common depth reference point**

2. **No Synchronized Depth State**
   - There's no central state management for "the depth range being viewed"
   - Each visualization component maintains its own view window independently
   - When you interact with one, the other doesn't know about it

3. **Vertical Misalignment Root Cause**
   - The stratigraphic column likely uses a different depth calculation or rendering method
   - LAS curves scale independently
   - Even if they START aligned, any interaction or zoom causes them to drift

4. **Missing Bidirectional Event Handling**
   - No click handlers on the strat column that update the curves
   - No curve interaction that highlights/selects the matching lithology
   - No synchronized scrolling mechanism

---

## How to Fix This: Implementation Strategy

### 1. **Create a Shared Depth State Manager**

```
DepthStateManager {
  - activeDepthRange: {from, to}
  - cursorDepth: number
  - selectedLithologyIndices: array
  
  // Subscribers for all depth changes
  - onDepthRangeChanged: EventEmitter
  - onCursorDepthChanged: EventEmitter
  - onSelectionChanged: EventEmitter
}
```

### 2. **Use a Common Depth Axis**

Both the stratigraphic column and LAS curves should:
- Calculate depth positions using the **identical formula**
- Map model depth (e.g., 87.5 meters) to screen Y-coordinate using the same scale
- Example: `screenY = baseY - (modelDepth - minDepth) * pixelsPerMeter`

### 3. **Synchronize All Interactions**

**When user clicks on stratigraphic column:**
```
1. Determine depth from mouse Y position
2. Find corresponding lithology interval
3. Update DepthStateManager.activeDepthRange
4. Emit event that triggers:
   - LAS curves to highlight/scroll to show that depth
   - Data table to select that row
```

**When user clicks on LAS curves:**
```
1. Determine depth from mouse X position (if interactive)
2. Update DepthStateManager.cursorDepth
3. Emit event that triggers:
   - Stratigraphic column to highlight/draw marker at depth
   - Data table to select corresponding row
```

**When table row is selected:**
```
1. Get from_depth and to_depth from row
2. Update DepthStateManager.activeDepthRange
3. Emit event that triggers both visualizations to update
```

### 4. **Implement Scroll Synchronization**

```
ScrollSynchronizer {
  - mainScrollElement (stratigraphic column)
  - trackDepth(scrollY) {
    visibleDepthRange = calculateDepthFromScrollPosition(scrollY)
    emit depthRangeChanged(visibleDepthRange)
  }
  
  - onDepthRangeChanged(newRange) {
    // Update curves viewport to show same depth range
    // Update table viewport to show same depth range
  }
}
```

### 5. **Depth Coordinate System is Critical**

The magic is in using **the same coordinate transformation** everywhere:

```javascript
// MUST be identical across all components
function depthToScreenY(depth, minDepth, scale, baseY) {
  return baseY - (depth - minDepth) * scale;
}

function screenYToDepth(screenY, minDepth, scale, baseY) {
  return minDepth + (baseY - screenY) / scale;
}
```

**Your stratigraphic column and LAS curves MUST use the same functions.**

---

## Specific Alignment Issues in Your Code

Without seeing your exact code, the typical issues are:

### Issue 1: Different Depth Scaling
- Strat column might use: `y = depth * somePixelHeight`
- LAS curves might use: `x = (depth - minDepth) * differentScale`
- **Fix**: Use identical depth-to-coordinate calculations

### Issue 2: Missing Scroll Binding
- When you scroll the strat column, the curves don't scroll
- **Fix**: Capture scroll events and update both components' view windows

### Issue 3: Different Depth Ranges
- Strat column shows depths 87-98m
- Curves show depths 128-136m
- **Fix**: Ensure they're rendering the same depth interval

### Issue 4: Header Heights and Margins
- If strat column has a header that offsets content vertically
- Curves might not account for the same offset
- **Fix**: Calculate base Y-positions consistently

---

## 1 Point Desktop Architecture (From Manual Sections)

From the manual analysis, 1 Point Desktop achieves this through:

1. **Multi-panel Layout (Page 2262)**
   - Far Left: Detailed graphic log view (main display)
   - Center: Data sheet tables
   - Right: More curves/analysis
   - Far Right: Preview/overview window

2. **Unified Event System**
   - All panels listen to a central "depth changed" event
   - Any mouse click anywhere triggers depth recalculation
   - All dependent visualizations update

3. **Preview Window Interaction (Page 2265)**
   - "Clicking on the preview window will update the main display window to show that depth"
   - This shows explicit synchronization: click → state change → all other views update

4. **Multiple Selection Methods (Page 2285-2288)**
   - Data sheets, graphic log, AND overview window all support clicking for selection
   - All result in synchronized view updates
   - Multiple rows can be selected with visual feedback across all components

---

## Implementation Checklist

- [ ] **Create centralized depth state manager** that all components subscribe to
- [ ] **Use identical depth-to-Y calculation** across strat column and curves
- [ ] **Implement bidirectional scroll binding** between components
- [ ] **Add click handlers** to both strat column and curves that update shared state
- [ ] **Add synchronized horizontal scrolling** if curves extend beyond viewport
- [ ] **Test alignment** by:
  - Clicking on different depths in strat column → curves should highlight same depth
  - Scrolling strat column → curves should scroll to same depth range
  - Clicking table row → both visualizations should update to show that row's depth

---

## Key Insight

The perfect alignment in 1 Point Desktop isn't magic—it's **engineering discipline**:
- One source of truth for depth
- All views subscribe to changes in that depth
- All coordinate systems use identical transformation functions
- Every interaction updates the shared state
- Every state change triggers dependent updates

Your Earthworm implementation needs the same architectural pattern.
