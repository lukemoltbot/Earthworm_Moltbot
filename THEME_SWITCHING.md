# Theme Switching Feature

## Overview
The theme switching feature allows users to toggle between dark and light themes in the Earthworm application. This improves usability in different lighting conditions and user preferences.

## Implementation Details

### 1. Stylesheet (styles.qss)
- Location: `src/ui/styles/styles.qss`
- Uses CSS variables for easy theme switching
- Two themes: Dark (default) and Light
- Comprehensive styling for all Qt widgets

### 2. Theme Persistence
- Theme preference saved in `~/.earthworm_settings.json`
- Settings key: `"theme"` with values `"dark"` or `"light"`
- Automatically loads user's preferred theme on startup

### 3. UI Controls
- **Toolbar Button**: 🌓 icon in main toolbar
- **Menu**: View → Theme → [Dark/Light/Toggle/Preview]
- **Keyboard Shortcut**: None by default (can be added)

### 4. Theme Preview Dialog
- Accessible via View → Theme → Preview Theme...
- Shows sample widgets in selected theme
- Allows immediate theme application

## How It Works

### CSS Variables System
The stylesheet uses CSS custom properties (variables):
```css
:root {
    --primary-bg: #1e1e1e;
    --primary-text: #d4d4d4;
    /* ... more variables ... */
}

.light-theme {
    --primary-bg: #ffffff;
    --primary-text: #1e1e1e;
    /* ... light theme overrides ... */
}
```

### Theme Application
1. On startup: `load_stylesheet()` loads the QSS file
2. Theme class applied to QApplication instance
3. CSS variables automatically switch based on class

### Theme Switching Process
1. User clicks theme toggle button or selects menu item
2. `toggle_theme()` or `set_theme()` called
3. Theme preference saved via `save_theme_preference()`
4. Application property updated for CSS class
5. User notified that restart may be needed for full effect

## Code Structure

### MainWindow Additions
- `current_theme` attribute
- `load_stylesheet()` - Loads and applies QSS
- `toggle_theme()` - Toggles between dark/light
- `set_theme(theme_name)` - Sets specific theme
- `save_theme_preference()` - Saves to settings
- `create_view_menu()` - Adds Theme menu
- `create_toolbar()` - Adds theme toggle button
- `show_theme_preview()` - Shows preview dialog

### Settings Manager Updates
- Added `theme` parameter to `save_settings()`
- Added `"theme": "dark"` to default settings
- Theme loaded/saved with other preferences

### ThemePreviewDialog
- New dialog class for theme preview
- Shows sample widgets in selected theme
- Emits `themeChanged` signal when applied

## Testing

### Manual Testing
1. Start the application
2. Click the 🌓 toolbar button
3. Check theme changes (may need restart for full effect)
4. Use View → Theme menu options
5. Open theme preview dialog
6. Restart app to verify persistence

### Automated Tests
Run: `python test_final_theme.py`
- Checks stylesheet existence and validity
- Verifies settings persistence
- Confirms all required methods exist
- Validates roadmap updates

## Limitations & Notes

### Dynamic Theme Switching
- Some Qt widgets may not update dynamically
- Full theme application may require restart
- Notification shown to user about restart

### CSS Coverage
- Stylesheet covers most common Qt widgets
- Custom widgets may need additional styling
- PyQtGraph plots not affected by QSS

### Future Enhancements
1. **More Themes**: Add additional theme options
2. **Custom Themes**: Allow user-defined color schemes
3. **Dynamic Updates**: Improve live theme switching
4. **Icon Themes**: Switch icons with themes
5. **Accent Colors**: Allow custom accent colors

## Files Modified
1. `src/ui/styles/styles.qss` - New stylesheet
2. `src/ui/main_window.py` - Theme UI and logic
3. `src/core/settings_manager.py` - Theme persistence
4. `src/ui/dialogs/theme_preview_dialog.py` - Preview dialog
5. `1PD_UI_UX_ROADMAP.md` - Updated progress
6. `Phase6_Task.md` - Updated task status

## Related Subtasks
- **12.1**: Created professional stylesheet ✓
- **12.2**: Theme switching UI and persistence ✓
- **12.3**: Configuration panel for theme management (Next)