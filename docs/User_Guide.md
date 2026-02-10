# Earthworm Borehole Logger - User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Interface](#main-interface)
4. [Loading Data](#loading-data)
5. [Lithology Classification](#lithology-classification)
6. [Stratigraphic Column](#stratigraphic-column)
7. [Editing Lithology](#editing-lithology)
8. [Advanced Features](#advanced-features)
9. [Settings & Configuration](#settings--configuration)
10. [Troubleshooting](#troubleshooting)

## Introduction

Earthworm Borehole Logger is a professional geological software application designed for processing, analyzing, and visualizing borehole data. It supports industry-standard file formats and provides comprehensive tools for lithology classification, stratigraphic analysis, and geological interpretation.

### Key Features
- **Multi-format Support**: LAS, CSV, Excel files
- **Automated Lithology Classification**: Based on gamma ray and density curves
- **Interactive Visualization**: Real-time curve plotting and stratigraphic columns
- **Advanced Analysis**: Smart interbedding detection, range gap analysis
- **Industry Compliance**: 37-column CoalLog v3.1 schema support
- **Project Management**: Save/load complete project sessions

## Getting Started

### System Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, Linux
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 500MB for installation, additional for project files

### Installation
1. Download the latest release from GitHub
2. Extract the archive to your preferred location
3. Run the application:
   - **Windows**: Double-click `earthworm.exe`
   - **macOS/Linux**: Run `python main.py` from terminal

### First Launch
On first launch, the application will:
- Create a default settings file
- Set up the workspace directory
- Load default lithology rules

## Main Interface

The main interface consists of several key areas:

### 1. Menu Bar
- **File**: Open/save projects, load data files, exit
- **Window**: Manage open windows (tile, cascade, close)
- **View**: Toggle visibility of panels and tools
- **Help**: Access user guide and about information

### 2. Project Explorer (Left Panel)
- Browse and manage project files
- Double-click files to open them
- Organize files into folders

### 3. Main Workspace (Center)
- **Hole Editor Window**: Primary workspace for analyzing borehole data
- **Map Window**: Visualize hole locations geographically
- **Cross-Section Window**: Create fence diagrams between holes

### 4. Control Panel (Right Panel)
- Analysis controls and settings
- Curve selection and configuration
- Run analysis button

## Loading Data

### Supported File Formats
1. **LAS Files** (Log ASCII Standard)
   - Industry standard for well logging data
   - Supports multiple curves (GR, RHOB, CAL, etc.)
   - Automatic mnemonic detection

2. **CSV Files** (Comma-Separated Values)
   - Flexible column-based format
   - Custom column mapping available
   - Supports both depth-based and interval-based data

3. **Excel Files** (.xlsx, .xls)
   - Multiple sheet support
   - Preserves formatting and formulas
   - Easy data review before import

### Loading Process
1. Click **File → Load LAS File** or use the toolbar button
2. Select your data file
3. The system will:
   - Parse the file format
   - Detect available curves
   - Map mnemonics to standard names
   - Display preview in the control panel

### Curve Mapping
When loading LAS files, the application automatically maps common mnemonics:
- **Gamma Ray**: GR, GAMMA, GR_EDTC
- **Density**: RHOB, DEN, DENS
- **Caliper**: CAL, CALI, CALX

You can manually adjust mappings in the settings if needed.

## Lithology Classification

### Classification Methods
Earthworm offers two classification methods:

#### 1. Standard Method (Default)
- Uses both gamma ray AND density ranges
- Applies researched defaults for missing ranges (configurable)
- More accurate but requires both curves

#### 2. Simple Method
- Classifies by density first, then gamma ray
- Useful when only one curve is reliable
- Faster but less precise

### Lithology Rules
Lithology classification is based on user-defined rules:

#### Rule Components
- **Lithology Code**: Short code (e.g., CO, SS, ST)
- **Lithology Name**: Full name (e.g., Coal, Sandstone, Siltstone)
- **Gamma Range**: Minimum and maximum gamma ray values
- **Density Range**: Minimum and maximum density values
- **Color**: Display color for visualization
- **SVG Pattern**: Geological pattern for stratigraphic column

#### Default Rules
The application includes default rules for common lithologies:
- **CO** (Coal): Gamma 0-20, Density 1.2-1.8
- **SS** (Sandstone): Gamma 20-60, Density 2.4-2.7
- **ST** (Siltstone): Gamma 50-100, Density 2.2-2.6
- **SH** (Shale): Gamma 80-150, Density 2.5-2.8

### Running Analysis
1. Load your data file
2. Select curves in the control panel
3. Configure analysis settings:
   - **Analysis Method**: Standard or Simple
   - **Use Researched Defaults**: Apply defaults for missing ranges
   - **Merge Thin Units**: Combine units below threshold
   - **Smart Interbedding**: Detect interbedded sequences
4. Click **Run Analysis**

### Analysis Results
After analysis, you'll see:
1. **Classified Data Table**: Each row shows depth interval and lithology
2. **Curve Plotter**: Gamma and density curves with lithology colors
3. **Stratigraphic Column**: Visual representation of lithology units
4. **Statistics Panel**: Classification summary and confidence metrics

## Stratigraphic Column

The stratigraphic column provides a visual representation of lithology units:

### Overview Column (Right)
- Shows entire borehole at once
- Uses compressed scale to fit all data
- Includes zoom overlay showing current view range
- Color-coded by lithology with SVG patterns

### Enhanced Column (Center-Left)
- Detailed view synchronized with curve plotter
- Shows more detail (labels, thickness, qualifiers)
- Scrolls vertically with curve plotter
- Interactive unit selection

### Column Features
- **Color Coding**: Each lithology has unique color
- **SVG Patterns**: Geological patterns for better visualization
- **Unit Labels**: Display lithology code and thickness
- **Selection Highlight**: Selected units are highlighted
- **Depth Scale**: Vertical scale in meters

### Navigation
- **Vertical Scroll**: Mouse wheel or scroll bar
- **Zoom**: Use zoom controls or mouse wheel with Ctrl
- **Sync with Curves**: Enhanced column scrolls with curve plotter
- **Unit Selection**: Click units to select corresponding table rows

## Editing Lithology

### Manual Editing
1. **Select Unit**: Click in stratigraphic column or data table
2. **Edit Properties**: Double-click table cell to edit
3. **Apply Changes**: Press Enter to save, Esc to cancel

### Bulk Operations
1. **Multiple Selection**: Ctrl+Click or Shift+Click units
2. **Change Lithology**: Right-click → Change Lithology
3. **Merge Units**: Select adjacent units → Right-click → Merge

### Creating Interbedding
Interbedding represents mixed lithology intervals:

#### Manual Creation
1. Select start and end depths
2. Click **Create Interbedding** button
3. Define component lithologies and percentages
4. System creates detailed interbedding sequence

#### Smart Detection
Enable **Smart Interbedding** in settings to:
- Automatically detect potential interbedding
- Suggest sequences based on curve patterns
- Review and accept/reject suggestions

### Quality Control Tools
1. **NL Review**: Analyze "Not Logged" intervals
   - Statistics on unclassified sections
   - Suggestions for rule adjustments
   - Export review report

2. **Range Gap Analysis**: Visualize classification coverage
   - Identify depth ranges without rules
   - Suggest rule adjustments
   - Optimize classification coverage

## Advanced Features

### Map Window
Visualize borehole locations geographically:

#### Features
- **Import Coordinates**: From CSV or manually entered
- **Multiple Projections**: UTM, Lat/Long, local grids
- **Distance Calculation**: Automatic spacing for cross-sections
- **Hole Selection**: Select holes for cross-section creation

#### Usage
1. Open Map Window from Window menu
2. Import hole coordinates
3. View spatial distribution
4. Select holes for cross-section

### Cross-Section Window
Create fence diagrams between multiple holes:

#### Creation Process
1. Select 3+ holes in Map Window or Project Explorer
2. Open Cross-Section Window
3. System calculates true spacing from coordinates
4. Plots holes side-by-side with stratigraphic columns

#### Features
- **True Spacing**: Uses Pythagorean theorem on coordinates
- **Polygon Connection**: Connects common lithology units
- **Interactive Adjustment**: Drag correlation lines
- **Export Options**: Save as image or PDF

### Anomaly Detection
Highlights data quality issues:

#### Caliper Anomalies
- Detects where CAL - BitSize > 20mm
- Highlights in curve plotter
- Can be filtered or corrected

#### Curve Quality
- Identifies noisy or missing data
- Suggests filtering or interpolation
- Quality metrics in statistics

### Template System
Save and apply consistent settings:

#### Creating Templates
1. Configure all settings (rules, colors, patterns)
2. Click **Save Template**
3. Name and describe template
4. Template saved for future use

#### Applying Templates
1. Click **Load Template**
2. Select template from list
3. All settings applied automatically
4. Can be applied to existing or new projects

## Settings & Configuration

### Accessing Settings
1. Click **View → Settings** or use toolbar button
2. Settings dialog opens with multiple tabs

### General Settings
- **Separator Thickness**: Line thickness between units
- **Draw Separators**: Toggle separator lines
- **Curve Thickness**: Line thickness for curves
- **Bit Size**: Drilling bit size for anomaly detection

### Lithology Rules Settings
- **Edit Rules**: Add, modify, or delete lithology rules
- **Import/Export**: Share rule sets with colleagues
- **Reset to Defaults**: Restore factory rules

### Analysis Settings
- **Analysis Method**: Standard or Simple
- **Use Researched Defaults**: Apply defaults for missing ranges
- **Merge Thin Units**: Combine units below threshold
- **Merge Threshold**: Minimum unit thickness (meters)
- **Smart Interbedding**: Enable automatic detection
- **Fallback Classification**: Reduce NL results

### Visualization Settings
- **Color Scheme**: Choose color palette
- **SVG Patterns**: Toggle geological patterns
- **Disable SVG**: Use solid colors only
- **Column Visibility**: Show/hide data columns
- **Curve Visibility**: Show/hide specific curves

### Project Settings
- **Workspace Path**: Default project location
- **Auto-save**: Automatic project backup
- **Session Management**: Save/load complete sessions
- **Recent Files**: Number of files in history

## Troubleshooting

### Common Issues

#### 1. File Loading Errors
- **Issue**: "Unsupported file format" or parsing errors
- **Solution**: 
  - Verify file format (LAS, CSV, Excel)
  - Check file encoding (use UTF-8 for CSV)
  - Ensure proper column headers
  - Try opening in text editor to check format

#### 2. Missing Curves
- **Issue**: Required curves not detected
- **Solution**:
  - Check mnemonic mapping in settings
  - Verify curve exists in file
  - Try manual column mapping for CSV/Excel
  - Use Simple analysis method if one curve missing

#### 3. Poor Classification Results
- **Issue**: Too many NL (Not Logged) results
- **Solution**:
  - Adjust lithology rules in settings
  - Enable "Use Researched Defaults"
  - Enable "Fallback Classification"
  - Review Range Gap Analysis for coverage

#### 4. Performance Issues
- **Issue**: Slow loading or analysis
- **Solution**:
  - Reduce file size (sample interval)
  - Close other applications
  - Increase system RAM
  - Use simpler visualization options

#### 5. Visualization Problems
- **Issue**: Stratigraphic column not displaying correctly
- **Solution**:
  - Check SVG pattern files exist
  - Try "Disable SVG" option
  - Update graphics drivers
  - Reduce column complexity

### Getting Help

#### Application Help
1. **Help Menu**: Access this user guide
2. **Tool Tips**: Hover over controls for descriptions
3. **Status Bar**: Bottom of window shows current operation

#### External Resources
- **GitHub Repository**: Source code and issues
- **Documentation**: Technical documentation
- **Community Forum**: User discussions and tips

#### Reporting Issues
When reporting issues, include:
1. Earthworm version number
2. Operating system and version
3. Steps to reproduce the issue
4. Error messages or screenshots
5. Sample data file (if possible)

## Appendix

### Keyboard Shortcuts

#### General
- **Ctrl+N**: New project
- **Ctrl+O**: Open project
- **Ctrl+S**: Save project
- **Ctrl+W**: Close window
- **F1**: Help

#### Navigation
- **Ctrl+Mouse Wheel**: Zoom in/out
- **Space**: Reset view
- **Arrow Keys**: Pan view
- **Home**: Jump to top
- **End**: Jump to bottom

#### Editing
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+C**: Copy
- **Ctrl+V**: Paste
- **Delete**: Delete selection

### File Formats Reference

#### LAS File Structure
```
~VERSION INFORMATION
~WELL INFORMATION
~CURVE INFORMATION
~PARAMETER INFORMATION
~OTHER INFORMATION
~ASCII DATA
```

#### CSV Column Requirements
Minimum required columns:
- Depth column (DEPT, DEPTH, etc.)
- Gamma ray column (GR, GAMMA, etc.)
- Density column (RHOB, DEN, DENS, etc.)

#### Excel Sheet Requirements
- Data must be in first sheet
- Column headers in first row
- No merged cells in data area

### Lithology Code Reference

| Code | Name | Description | Typical Gamma | Typical Density |
|------|------|-------------|---------------|-----------------|
| CO | Coal | Organic sedimentary rock | 0-20 API | 1.2-1.8 g/cm³ |
| SS | Sandstone | Clastic sedimentary rock | 20-60 API | 2.4-2.7 g/cm³ |
| ST | Siltstone | Fine-grained clastic rock | 50-100 API | 2.2-2.6 g/cm³ |
| SH | Shale | Fine-grained sedimentary rock | 80-150 API | 2.5-2.8 g/cm³ |
| XM | Carbonaceous Mudstone | Organic-rich mudstone | 60-120 API | 2.0-2.3 g/cm³ |
| ZM | Coaly Mudstone | Transitional coal-mudstone | 30-80 API | 1.7-2.1 g/cm³ |
| NL | Not Logged | Unclassified interval | N/A | N/A |

### Version History

#### Version 1.0 (Current)
- Initial release with core functionality
- LAS, CSV, Excel file support
- Lithology classification engine
- Stratigraphic column visualization
- Project session management

#### Planned Features
- 3D visualization
- Advanced statistical analysis
- Machine learning classification
- Cloud collaboration
- Mobile companion app

---

*Earthworm Borehole Logger - Professional Geological Software*
*© 2024 Earthworm Development Team*
*Version 1.0 | Last Updated: February 2024*