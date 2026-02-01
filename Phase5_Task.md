# Phase 5: GIS & Cross-Sections

**Purpose:** Moving from "Hole view" to "Site view." Provide interactive map and cross‑section (fence diagram) capabilities.

## Prerequisites
- Phase 4 completed (Interactive lithology boundaries)
- MDI framework with multiple window support (Phase 1)
- Hole data with Easting/Northing coordinates (CSV headers or separate metadata)

## Tasks

### Task 8: The Interactive Map Window

**Subtask 8.1: Create Map MDI Window**
- Create a new MDI subwindow class `MapWindow` using `pg.PlotWidget` for 2D scatter plot.
- Integrate with the MDI area (add to Window menu).
- Display Easting (X) vs Northing (Y) coordinates.
- Style points with color coding based on hole properties (e.g., total depth, lithology count).

**Subtask 8.2: Load and Plot Hole Locations**
- Extract Easting/Northing from CSV file headers (or from a separate metadata file).
- Plot each hole as a point with hole ID label.
- Implement zoom/pan navigation.
- Add grid and scale reference.

**Subtask 8.3: Lasso Selection**
- Implement interactive lasso (polygon) selection tool.
- Allow user to draw a polygon on the map to select multiple holes.
- Highlight selected holes both on map and in the "Holes List" sidebar.
- Emit selection changed signal to other windows (e.g., cross‑section generator).

### Task 9: The Cross-Section (Fence Diagram)

**Subtask 9.1: Cross‑Section Tool**
- Create a tool that takes 3+ selected holes (from map or list) and generates a new `CrossSectionWindow`.
- Design UI for selecting holes, ordering, and setting parameters (vertical exaggeration, etc.).
- Calculate "True Spacing" between holes using Pythagorean theorem on Easting/Northing coordinates.

**Subtask 9.2: Plot Holes Side‑by‑Side**
- Plot each selected hole as a vertical stratigraphic column.
- Arrange columns horizontally with spacing proportional to true distances.
- Use consistent depth scale (0 at top).
- Show lithology blocks with same coloring as main plot.

**Subtask 9.3: Draw Connecting Polygons**
- Identify common "Seam Name" (or lithology code) across holes.
- Draw polygons connecting the top and bottom boundaries of the same seam across holes.
- Use alpha blending to show continuity/dip.
- Allow interactive adjustment of seam correlation (dragging seam boundaries).

## Technical Requirements

1. **Coordinate System**
   - Assume Easting/Northing are in meters (same projection).
   - Handle missing coordinates gracefully.

2. **Performance**
   - Use PyQtGraph for efficient rendering of many holes.
   - Implement lazy loading for large projects.

3. **Integration**
   - Map window should sync with Holes List sidebar.
   - Cross‑section window should update when hole data changes.
   - Support printing/export of maps and cross‑sections.

4. **User Experience**
   - Intuitive lasso tool with visual feedback.
   - Clear visual distinction between selected/unselected holes.
   - Cross‑section should be draggable/zoomable.

## Deliverables

1. **MapWindow** class with scatter plot and lasso selection.
2. **CrossSectionWindow** class for fence diagrams.
3. **Coordinate extraction** from hole data.
4. **Polygon drawing** for seam correlation.
5. **Integration** with existing MDI and sidebar.

## Integration Points

- **Holes List** – sync selection between list and map.
- **HoleEditorWindow** – clicking a hole on map could open its editor.
- **Validation** – ensure coordinates are valid numbers.

## Potential Challenges

- **Missing Coordinates** – some holes may lack Easting/Northing; need fallback.
- **Large Datasets** – rendering hundreds of holes may be slow; need optimization.
- **Seam Matching** – identifying equivalent seams across holes may require fuzzy matching.

## Success Criteria

- User can view all holes on an interactive map.
- User can select multiple holes via lasso and see them highlighted.
- User can generate a cross‑section from selected holes with accurate spacing.
- Seam polygons visually indicate dip and continuity.