# Phase 6: Technical Infrastructure & Polish

**Purpose:** Improve performance, user experience, and professional polish to match 1PD standards.

## Prerequisites
- Phases 1‑5 completed (core functionality)
- Stable codebase with working features

## Tasks

### Task 10: Threading for Heavy Operations

**Subtask 10.1: QThread for LAS Loading**
- Create a `Worker` class that loads LAS files in a background thread.
- Emit progress signals for UI feedback.
- Prevent UI freezing during large file loads.

**Subtask 10.2: Background Validation**
- Move validation engine to a separate thread for large datasets.
- Show "Validating..." status in UI.
- Cache validation results to avoid recomputation.

**Subtask 10.3: Concurrent Map Rendering**
- Use threading for rendering large map datasets.
- Implement progressive loading for many hole locations.

### Task 11: PandasModel Integration

**Subtask 11.1: Create PandasModel Class**
- Implement `QAbstractTableModel` that wraps a pandas DataFrame.
- Support editing, sorting, and filtering directly in the model.
- Efficiently handle large datasets (>10k rows).

**Subtask 11.2: Replace QTableWidget with QTableView**
- Update `LithologyTableWidget` to use `QTableView` with `PandasModel`.
- Maintain all existing functionality (delegates, validation highlighting).
- Improve performance for large lithology tables.

**Subtask 11.3: Synchronize with Graphics**
- Ensure table‑view synchronization works with the new model.
- Update signals/slots for selection and data changes.

### Task 12: Professional Styling (QSS)

**Subtask 12.1: Create Stylesheet**
- Design a `styles.qss` file with modern dark/light themes.
- Style all widgets: buttons, tables, plots, menus, dock widgets.
- Use consistent colors, spacing, and fonts.

**Subtask 12.2: Theme Switching**
- Add theme toggle (dark/light) in preferences or toolbar.
- Store theme preference in settings.

**Subtask 12.3: Custom Icons**
- Create or source professional icons for toolbar actions.
- Replace default Qt icons with themed ones.

### Task 13: Configuration & Session Management

**Subtask 13.1: Enhanced Settings**
- Expand `earthworm_settings.json` to include:
  - Last workspace state (open windows, positions, sizes)
  - Recent files/projects
  - User preferences (default units, display options)
  - Map and cross‑section defaults

**Subtask 13.2: Session Restore**
- On startup, restore previous session if user chooses.
- Re‑open all windows with their data and view states.
- Handle missing files gracefully.

**Subtask 13.3: Export/Import Settings**
- Allow users to export settings profile.
- Import settings from another installation.

## Technical Requirements

1. **Performance**
   - No UI freezing during file operations.
   - Smooth scrolling through large tables.
   - Responsive map interaction.

2. **Memory Management**
   - Clean up resources when windows close.
   - Use lazy loading for large datasets.
   - Avoid memory leaks in long sessions.

3. **User Experience**
   - Professional appearance matching commercial software.
   - Intuitive preferences dialog.
   - Clear feedback for long operations.

4. **Compatibility**
   - Support multiple Python versions (3.9+).
   - Work across Windows, macOS, Linux.
   - Handle different screen resolutions.

## Deliverables

1. **Threading system** for LAS loading and validation.
2. **PandasModel** class and integrated table view.
3. **Professional QSS stylesheet** with theme switching.
4. **Enhanced settings** with session restore.

## Integration Points

- **Existing windows** – apply styles to all UI elements.
- **File loading** – replace existing LAS loader with threaded version.
- **Validation engine** – optional background execution.
- **User preferences** – integrate with existing settings dialog.

## Potential Challenges

- **Thread‑safety** – ensuring GUI updates happen in main thread.
- **Model complexity** – implementing full `QAbstractTableModel` correctly.
- **Style conflicts** – QSS may not affect all custom widgets.
- **Session serialization** – capturing complex window states.

## Success Criteria

- Application feels responsive even with large datasets.
- Table performance is noticeably improved.
- UI looks professional and consistent.
- Users can resume work exactly where they left off.