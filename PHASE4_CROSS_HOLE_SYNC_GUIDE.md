# Phase 4: Cross-Hole Synchronization User Guide

## Overview

Earthworm now features professional **cross-hole curve synchronization** that matches 1Point Desktop's capabilities. This allows geologists to work with multiple boreholes simultaneously while maintaining consistent curve settings across all open holes.

## Key Features

### 1. **Automatic Curve Synchronization**
- **Curve Selection**: When you select curves in one hole, they're automatically selected in all other open holes
- **Curve Settings**: Line styles, colors, thickness, and visibility sync across holes
- **Real-time Updates**: Changes apply immediately to all synchronized holes

### 2. **SHIFT Key Temporary Override**
- **Hold SHIFT**: Temporarily disable synchronization for quick individual adjustments
- **Release SHIFT**: Automatic re-synchronization resumes
- **Visual Feedback**: Status indicator shows when override is active

### 3. **Granular Sync Controls**
Configure exactly what gets synchronized:
- ✅ Curve selection
- ✅ Line colors
- ✅ Line styles (solid, dotted, dashed, dash-dot)
- ✅ Line thickness
- ✅ Curve visibility
- ✅ Auto-sync on changes

### 4. **Professional UI Integration**
- **Tools Menu**: Tools → Settings → LAS → Sync LAS Curves
- **Status Indicator**: Visual sync status in toolbar
- **Settings Dialog**: Comprehensive configuration options

## How to Use

### Enabling Cross-Hole Sync

1. **Open Multiple Holes**
   - File → Load LAS File (open multiple LAS files)
   - Each hole opens in its own window within the MDI area

2. **Access Sync Settings**
   - Go to: **Tools → Settings → LAS → Sync LAS Curves...**
   - Or click the sync status indicator in the toolbar

3. **Configure Sync Options**
   - Enable/disable synchronization
   - Select which settings to sync
   - Set auto-sync behavior
   - Enable SHIFT key override

### Working with Synchronized Holes

#### Basic Workflow:
1. **Open Hole 1 and Hole 2**
2. **Select curves** in Hole 1 (Gamma, Resistivity)
3. **Observe** same curves automatically selected in Hole 2
4. **Change line style** to dotted in Hole 1
5. **See** line style update in Hole 2 automatically

#### Temporary Override:
1. **Hold SHIFT key** while making changes
2. **Make individual adjustments** to one hole
3. **Release SHIFT key** to resume synchronization
4. **Changes sync** across all holes again

### Sync Status Indicators

| Indicator | Meaning |
|-----------|---------|
| 🔗 **Green Link** | Synchronization active |
| 🔴 **Red Broken Link** | Synchronization disabled |
| ⚠️ **Yellow Warning** | SHIFT key override active |
| 🔵 **Blue Pulsing** | Sync in progress |

## Configuration Options

### Sync Settings Dialog

Access via: **Tools → Settings → LAS → Sync LAS Curves...**

#### Main Settings:
- **Enable Synchronization**: Master on/off switch
- **Auto-sync on Changes**: Automatically sync when any hole changes
- **SHIFT Key Override**: Enable temporary override with SHIFT key

#### Sync Granularity:
- **Sync Curve Selection**: Share which curves are selected
- **Sync Curve Colors**: Keep colors consistent across holes
- **Sync Line Styles**: Maintain same line styles (solid, dotted, etc.)
- **Sync Line Thickness**: Keep line widths consistent
- **Sync Curve Visibility**: Share show/hide states

### Status Bar Display

The status bar shows:
- Number of open holes being synchronized
- Current sync status
- SHIFT key override status
- Last sync time

## Advanced Features

### Curve Settings Templates
- **Save Templates**: Export current curve settings as templates
- **Apply Templates**: Import and apply templates to holes
- **Share Templates**: Exchange templates with colleagues

Access via: **Tools → Curve Settings Templates...**

### Performance Optimization
- **Smart Syncing**: Only sync changed settings
- **Batch Updates**: Group multiple changes into single sync
- **Background Processing**: Non-blocking sync operations

## Troubleshooting

### Common Issues

#### Sync Not Working:
1. Check sync is enabled in settings
2. Verify multiple holes are open
3. Ensure holes are properly registered
4. Check SHIFT key isn't pressed

#### Performance Issues:
1. Reduce number of synchronized settings
2. Disable auto-sync for manual control
3. Close unused holes
4. Use SHIFT override for individual work

#### Settings Not Persisting:
1. Check write permissions for settings file
2. Verify settings are being saved
3. Restart application to reload settings

### Debug Mode

Enable debug logging for sync operations:
```bash
export EARTHWORM_SYNC_DEBUG=1
python main.py
```

Debug output shows:
- Hole registration events
- Sync operations
- Settings changes
- SHIFT key events

## Best Practices

### For Geological Teams:
1. **Establish Standards**: Create team-wide curve setting templates
2. **Use SHIFT Override**: For quick individual adjustments
3. **Save Templates**: Before major changes for easy rollback
4. **Communicate**: When making changes that affect synchronized holes

### For Individual Work:
1. **Disable Auto-sync**: When focusing on one hole
2. **Use Templates**: For consistent curve presentations
3. **Leverage SHIFT**: For temporary individual adjustments
4. **Monitor Status**: Keep an eye on the sync indicator

## Technical Details

### Architecture
- **Signal-based**: Qt signals for real-time updates
- **Event-driven**: Responds to curve changes immediately
- **Modular**: Separate sync manager from hole windows
- **Persistent**: Settings saved to disk between sessions

### Files Modified
- `cross_hole_sync_manager.py` - Core sync logic
- `sync_settings_dialog.py` - Configuration UI
- `main_window.py` - Menu integration
- `curve_settings_template_manager.py` - Template system

### Data Flow
1. Hole makes change → emits signal
2. Sync manager receives signal
3. Manager validates sync rules
4. Manager broadcasts to other holes
5. Other holes apply changes

## Migration from Previous Versions

### New in Phase 4:
- Cross-hole synchronization
- SHIFT key override
- Granular sync controls
- Professional menu integration
- Status indicators

### Backward Compatibility:
- Existing single-hole workflows unchanged
- All Phase 3 curve features preserved
- Settings automatically migrated
- No data loss during upgrade

## Support

### Getting Help:
1. **Documentation**: This guide and inline help
2. **Debug Mode**: Enable for detailed logging
3. **Community**: Earthworm user forums
4. **Support**: Contact development team

### Reporting Issues:
Include in bug reports:
1. Sync settings configuration
2. Number of open holes
3. Steps to reproduce
4. Debug log output
5. Expected vs actual behavior

---

## Quick Reference

### Keyboard Shortcuts:
- **SHIFT**: Temporary sync override
- **Ctrl+S**: Save sync settings
- **Ctrl+Shift+S**: Open sync settings

### Menu Paths:
- **Tools → Settings → LAS → Sync LAS Curves...**
- **Tools → Curve Settings Templates...**

### Status Indicators:
- Green: Sync active
- Red: Sync disabled  
- Yellow: SHIFT override
- Blue: Syncing in progress

### Settings File:
- Location: `~/.earthworm/cross_hole_sync.json`
- Format: JSON with sync configuration
- Backup: Recommended before major changes

---

**Phase 4 Cross-Hole Synchronization - Professional Multi-hole Workflow Enabled**