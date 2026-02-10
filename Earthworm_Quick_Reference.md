# Earthworm Borehole Logger - Quick Reference Guide

## Application Startup
```
python main.py
```

## Main Interface Components

### 1. Project Explorer (Left Dock)
- Browse and open LAS/CSV/Excel files
- Double-click files to open in new editor window
- Shows file hierarchy with filtering

### 2. Main Toolbar
- **Load LAS File**: Open LAS file dialog
- **Run Analysis**: Start lithology classification
- **Settings**: Open settings dialog
- **Export CSV**: Export current data
- **Map Window**: Open map visualization
- **Cross-Section**: Create cross-section from selected holes

### 3. MDI Workspace (Center)
- Multiple hole editors can be open simultaneously
- Each editor has: Curve Plotter | Stratigraphic Column | Editor Table
- Tile/Cascade windows from Window menu

### 4. Status Bar (Bottom)
- File loading progress
- Analysis status
- Memory usage

## Keyboard Shortcuts

### File Operations
- `Ctrl+O`: Open file
- `Ctrl+S`: Save settings
- `Ctrl+Shift+S`: Save settings as
- `Ctrl+E`: Export data
- `Ctrl+Q`: Quit application

### Navigation
- `F5`: Refresh all views
- `Ctrl+F`: Find in table
- `Ctrl+Z`: Undo (in editor)
- `Ctrl+Y`: Redo (in editor)
- `Space`: Play/pause auto-scroll

### View Controls
- `Mouse Wheel`: Zoom in/out
- `Right-click + Drag`: Pan view
- `Ctrl+Mouse Wheel`: Horizontal zoom
- `Shift+Mouse Wheel`: Vertical zoom

## Analysis Workflow - Step by Step

### Phase 1: Data Loading
1. **Load File**: Use Project Explorer or Load LAS File button
2. **Verify Curves**: Check detected mnemonics in dropdowns
3. **Map Curves**: Select Gamma Ray and Density curves

### Phase 2: Rule Configuration
1. **Open Settings**: Click Settings button
2. **Lithology Rules Tab**: Add/configure classification rules
3. **Set Ranges**: Define Gamma and Density ranges for each lithology
4. **Visual Properties**: Set colors and patterns

### Phase 3: Run Analysis
1. **Click Run Analysis**: Starts background processing
2. **Monitor Progress**: Status bar shows progress
3. **Review Results**: Three synchronized views appear

### Phase 4: Review & Edit
1. **Scroll**: All views scroll together
2. **Select Units**: Click in any view to highlight
3. **Edit Table**: Modify lithology data directly
4. **Create Interbedding**: Select units → Create Interbedding button

### Phase 5: Export
1. **Export CSV**: Save edited data
2. **Generate Report**: Settings → Export Lithology Report
3. **Save Project**: File → Save Session

## Settings Reference

### Lithology Rules (Tab 1)
- **Add Rule**: Create new classification
- **Remove Rule**: Delete selected rule
- **Columns**:
  - Name, Code, Qualifier
  - Shade, Hue, Colour, Estimated Strength (dropdowns)
  - Display Color (color picker)
  - SVG Pattern (browse button)
  - Gamma Min/Max, Density Min/Max

### Display Settings (Tab 2)
- **Separator Lines**: Thickness and visibility
- **Curve Display**: Thickness and inversion
- **SVG Patterns**: Enable/disable
- **Curve Visibility**: Show/hide specific curves
- **Column Configurator**: Configure table columns

### Analysis Settings (Tab 3)
- **Researched Defaults**: Auto-apply known ranges
- **Merge Thin Units**: Combine <5cm units
- **Smart Interbedding**: Auto-detect interbedding
- **Fallback Classification**: Reduce NL results
- **Bit Size**: For anomaly detection (CAL - BitSize > 20mm)
- **Casing Depth**: Mask intervals above casing
- **NL Review**: Analyze Not Logged intervals

### File Operations (Tab 4)
- **Save/Load Settings**: JSON file operations
- **AVG Executable**: Path to AVG software
- **SVG Directory**: Path to pattern files
- **Export Report**: Comprehensive lithology report

### Range Analysis (Tab 5)
- **Visual Gap Analysis**: Color-coded range coverage
- **Refresh**: Update after rule changes
- **Overlap Detection**: Identify conflicting ranges

## Common Tasks

### Creating Interbedding
1. Select 2+ consecutive units in editor table
2. Click "Create Interbedding" button
3. In dialog:
   - Select lithologies and percentages
   - Set interrelationship code
   - Choose dominant lithology (Sequence 1)
4. Click OK to apply

### Using Map Window
1. Open Map Window (toolbar button)
2. Files auto-load from Project Explorer
3. Click holes to select
4. Right-click for options:
   - Open hole
   - Create cross-section
   - Show details

### Generating Cross-Section
1. Select 2+ holes (in Project Explorer or Map)
2. Click Cross-Section button
3. Adjust visualization:
   - Pan: Click and drag
   - Zoom: Mouse wheel
   - Settings: Right-click menu

### Configuring Column Visibility
1. Settings → Display Settings → Column Configurator
2. Check/uncheck columns to show/hide
3. Click Apply
4. Changes affect all open hole editors

### Exporting Reports
1. **Lithology Report**: Settings → File Operations → Export Lithology Report
   - Includes statistics and density analysis
   - NL analysis section
   - Individual data points

2. **NL Analysis**: Settings → Analysis Settings → Review NL Intervals
   - NL percentage and distribution
   - Depth concentration analysis
   - Export to CSV

## Troubleshooting Quick Fixes

### Problem: LAS file won't load
- **Check**: File format (LAS 2.0/3.0)
- **Try**: Load with lasio library directly
- **Fix**: Convert to CSV if necessary

### Problem: Curves missing
- **Check**: LAS file contains the curves
- **Try**: Different mnemonic names
- **Fix**: Use Curve Visibility settings

### Problem: Slow performance
- **Try**: Disable SVG patterns
- **Try**: Use Simple analysis method
- **Fix**: Close unused hole editors

### Problem: Patterns not showing
- **Check**: SVG directory path in settings
- **Try**: Disable/enable SVG patterns
- **Fix**: Clear SVG cache

### Problem: Analysis fails
- **Check**: Lithology rules are defined
- **Check**: Required curves are selected
- **Fix**: Review error message details

## Data Formats

### Input Files
- **LAS**: .las extension, standard oilfield format
- **CSV**: .csv, comma-separated, header row required
- **Excel**: .xlsx, multiple sheets supported

### Output Files
- **CSV**: Edited lithology data
- **JSON**: Settings and rules
- **Reports**: Comprehensive analysis (CSV)

### Required Columns (CSV/Excel)
- `DEPTH`: Depth values (mandatory)
- `GR` or `GAMMA`: Gamma ray curve
- `RHOB` or `DENS`: Density curve
- Other curves optional

## Best Practices

### Before Analysis
1. Verify data quality
2. Set appropriate curve ranges
3. Configure lithology rules
4. Save settings template

### During Analysis
1. Start with broad rules
2. Use Researched Defaults
3. Review NL intervals
4. Save intermediate results

### After Analysis
1. Export comprehensive report
2. Save final settings
3. Document changes
4. Archive project session

## Support Resources

- **Documentation**: `docs/` folder in installation
- **Example Data**: `examples/` folder
- **Community**: Earthworm user Discord
- **Updates**: Check GitHub repository

---

*Quick Reference v1.0 - Earthworm Borehole Logger*