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
   - [Project Sessions](#project-sessions)
   - [Template System](#template-system)
   - [Map Window](#map-window)
   - [Cross-Section Window](#cross-section-window)
   - [Anomaly Detection](#anomaly-detection)
9. [Settings & Configuration](#settings--configuration)
   - [Settings Dialog Overview](#settings-dialog-overview)
   - [Lithology Rules Tab](#lithology-rules-tab)
   - [Visualization Tab](#visualization-tab)
   - [Analysis Tab](#analysis-tab)
   - [General Tab](#general-tab)
   - [File Management Tab](#file-management-tab)
   - [Advanced Settings](#advanced-settings)
   - [Settings Management](#settings-management)
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

### Project Sessions
Project sessions allow you to save and restore the complete state of your work, including all open files, analysis results, and settings.

#### What's Saved in a Session:
- **Open Files**: All currently loaded borehole files
- **Analysis Results**: Classification results for each hole
- **Visualization State**: Current views, zoom levels, selections
- **Settings**: Current lithology rules and application settings
- **Window Layout**: Positions of all open windows (editor, map, cross-section)

#### Creating and Managing Sessions:
1. **Save Session**: File → Save Session (Ctrl+S)
   - Saves current project state to a session file (.json)
   - Includes all data, analysis, and visualization states
   - Can be shared with colleagues for collaboration

2. **Load Session**: File → Load Session (Ctrl+O)
   - Restores a previously saved session
   - Reopens all files and restores analysis results
   - Recreates the exact workspace state

3. **Session Management Dialog**: File → Session Management
   - View all saved sessions
   - Delete old sessions
   - Set default session to load on startup
   - Export/import sessions for sharing

#### Session File Structure:
Session files are JSON format containing:
- Metadata (name, description, creation date)
- File paths and loaded data references
- Analysis parameters and results
- Visualization settings and window states
- Application configuration

### Template System
Templates allow you to save and apply consistent analysis settings across multiple projects or holes.

#### Template Components:
A template includes:
- **Lithology Rules**: Complete set of classification rules
- **Visualization Settings**: Colors, patterns, display options
- **Analysis Parameters**: Method, thresholds, interbedding settings
- **Application Configuration**: General settings and preferences

#### Creating Templates:
1. Configure all desired settings in the application
2. Click **File → Save Template** or use Template Manager
3. Provide template details:
   - **Name**: Descriptive template name
   - **Description**: Purpose and use cases
   - **Category**: Organizational category (e.g., "Coal", "Sandstone", "General")
   - **Tags**: Searchable keywords

4. Template is saved to the templates directory for future use

#### Applying Templates:
1. **New Project from Template**: File → New from Template
   - Creates a new project with template settings applied
   - Perfect for starting consistent analysis workflows

2. **Apply to Existing Project**: Template Manager → Apply Template
   - Applies template settings to current project
   - Can selectively apply components (rules only, visualization only, etc.)

3. **Template Manager**: Access via Settings dialog or File menu
   - Browse all available templates
   - Preview template settings before applying
   - Edit, duplicate, or delete templates
   - Import/export templates for sharing

#### Template Management:
- **Default Templates**: System includes pre-configured templates for common scenarios
- **Custom Templates**: Create your own for specific projects or regions
- **Template Inheritance**: Create templates that extend or modify existing ones
- **Version Control**: Templates can be versioned for tracking changes

### Map Window
The Map Window provides geographical visualization of borehole locations and spatial analysis capabilities.

#### Opening the Map Window:
1. **Window → New Map Window** or toolbar button
2. Map opens as a new tab in the main workspace
3. Initially empty - need to import or add hole locations

#### Adding Hole Locations:
1. **Manual Entry**:
   - Right-click on map → Add Hole
   - Enter hole name, coordinates (Easting/Northing or Lat/Long)
   - Select coordinate system (UTM, Geographic, Local)

2. **Import from CSV**:
   - File → Import Coordinates
   - CSV format: HoleID, Easting, Northing, [Optional: Elevation]
   - Supports multiple coordinate systems
   - Automatic coordinate conversion if needed

3. **Extract from LAS Files**:
   - Automatically extracts location from LAS file headers
   - Looks for standard location mnemonics (X, Y, Z, LAT, LONG)
   - Can batch process multiple files

#### Map Features:
1. **Base Maps**:
   - **Street Map**: OpenStreetMap background
   - **Satellite**: Aerial/satellite imagery
   - **Topographic**: Contour and elevation data
   - **Custom**: Load your own background images

2. **Coordinate Systems**:
   - **UTM**: Universal Transverse Mercator (zones 1-60)
   - **Geographic**: Latitude/Longitude (WGS84)
   - **Local Grids**: Project-specific coordinate systems
   - **Automatic Conversion**: Convert between systems on the fly

3. **Visualization Options**:
   - **Symbol Size**: Adjust hole marker size
   - **Color Coding**: Color by lithology, depth, or custom attribute
   - **Labels**: Show hole names, depths, or other attributes
   - **Clustering**: Group nearby holes for cleaner display

4. **Measurement Tools**:
   - **Distance**: Measure between any two points
   - **Area**: Calculate polygon areas
   - **Bearing**: Determine direction between holes
   - **Elevation Profile**: Create elevation cross-sections

#### Spatial Analysis:
1. **Density Analysis**:
   - Heat maps showing hole density
   - Identify drilling concentration areas
   - Useful for planning additional drilling

2. **Proximity Analysis**:
   - Find holes within specified distance
   - Identify nearest neighbors
   - Calculate average spacing

3. **Trend Analysis**:
   - Identify spatial trends in lithology
   - Map thickness variations
   - Visualize geological trends

#### Cross-Section Preparation:
1. **Select Holes for Cross-Section**:
   - Click individual holes or draw selection rectangle
   - Selected holes highlight in different color
   - Minimum 3 holes required for cross-section

2. **Line of Section**:
   - Draw line on map representing cross-section orientation
   - Automatically projects holes onto section line
   - Calculates true horizontal distances

3. **Cross-Section Creation**:
   - Click "Create Cross-Section" button
   - Opens Cross-Section Window with selected holes
   - Maintains spatial relationships from map

### Cross-Section Window
The Cross-Section Window creates fence diagrams (correlation panels) showing lithology relationships between multiple boreholes.

#### Creating Cross-Sections:
1. **From Map Window**:
   - Select 3+ holes on map
   - Click "Create Cross-Section" button
   - Cross-section oriented along selected line

2. **From Project Explorer**:
   - Select multiple hole files
   - Right-click → Create Cross-Section
   - Uses default spacing if coordinates unavailable

3. **Manual Creation**:
   - Window → New Cross-Section Window
   - Manually add holes from project list
   - Specify spacing manually

#### Cross-Section Components:
1. **Stratigraphic Columns**:
   - Vertical columns for each hole
   - Shows lithology with colors and patterns
   - Depth scale consistent across all holes
   - Interactive - click to select units

2. **Spacing Calculation**:
   - **With Coordinates**: Uses true horizontal distance from map
   - **Without Coordinates**: Uses equal spacing or user-defined
   - **Vertical Exaggeration**: Adjustable scale factor (1x to 20x)

3. **Correlation Lines**:
   - **Automatic**: Connects similar lithology units
   - **Manual**: Draw custom correlation lines
   - **Edit Mode**: Drag and adjust correlation points
   - **Multiple Horizons**: Correlate specific geological horizons

4. **Polygon Fill**:
   - Fills between correlation lines
   - Color by lithology or custom palette
   - Transparency adjustable
   - Helps visualize geological units between holes

#### Interactive Features:
1. **Navigation**:
   - **Pan**: Click and drag
   - **Zoom**: Mouse wheel or zoom tools
   - **Fit to View**: Auto-adjust to show all holes
   - **Depth Range**: Adjust visible depth range

2. **Selection and Editing**:
   - **Select Units**: Click on lithology units
   - **Multi-select**: Ctrl+Click or drag selection box
   - **Edit Correlation**: Drag correlation lines
   - **Add/Remove Holes**: Modify cross-section composition

3. **Measurement Tools**:
   - **Depth Measurement**: Measure vertical distances
   - **Horizontal Measurement**: Measure between holes
   - **Dip Calculation**: Calculate dip angles from correlation
   - **Thickness Measurement**: Measure unit thicknesses

#### Display Options:
1. **Column Display**:
   - **Width**: Adjust column width
   - **Spacing**: Adjust space between columns
   - **Labels**: Show hole names, depths, coordinates
   - **Background**: Grid lines, depth markers

2. **Visualization Modes**:
   - **Lithology Colors**: Standard lithology coloring
   - **Property Colors**: Color by density, gamma, or other properties
   - **Pattern Fill**: Geological patterns or solid colors
   - **Wireframe**: Outline only for fast rendering

3. **Annotation Tools**:
   - **Text Labels**: Add annotations to cross-section
   - **Lines and Arrows**: Highlight features
   - **Scale Bar**: Add measurement scale
   - **Legend**: Auto-generated or custom

#### Analysis Tools:
1. **Correlation Analysis**:
   - **Auto-correlation**: Suggests correlation lines
   - **Confidence Scoring**: Rates correlation quality
   - **Conflict Detection**: Identifies correlation conflicts
   - **Multiple Scenarios**: Save different correlation interpretations

2. **Thickness Analysis**:
   - **Isopach Maps**: Create thickness maps from cross-section
   - **Trend Analysis**: Identify thickening/thinning trends
   - **Statistical Analysis**: Calculate thickness statistics

3. **Structural Analysis**:
   - **Dip Calculation**: From correlation line angles
   - **Fault Detection**: Identify offset correlations
   - **Fold Analysis**: Analyze folding patterns

#### Export and Sharing:
1. **Image Export**:
   - **PNG/JPG**: Raster images for reports
   - **SVG**: Vector graphics for publication
   - **PDF**: Multi-page PDF with metadata
   - **High Resolution**: Export at print quality

2. **Data Export**:
   - **Correlation Data**: Export correlation lines as CSV
   - **Section Coordinates**: Export section geometry
   - **Annotation Data**: Save annotations with positions

3. **Project Integration**:
   - **Save with Project**: Cross-sections saved in project sessions
   - **Template Cross-Sections**: Save as templates for reuse
   - **Multiple Sections**: Create and manage multiple cross-sections

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

## Settings & Configuration

The Settings dialog provides comprehensive control over all aspects of Earthworm Borehole Logger. Access it via **View → Settings** or the toolbar button.

### Settings Dialog Overview
The Settings dialog is organized into tabs:
1. **Lithology Rules** - Define classification rules
2. **Visualization** - Control display options
3. **Analysis** - Configure analysis parameters
4. **General** - Application-wide settings
5. **File Management** - File handling and paths

### Lithology Rules Tab
This tab allows you to define and manage lithology classification rules.

#### Lithology Rules Table
The main component is a table where each row defines one lithology rule:

**Table Columns:**
1. **Name** - Descriptive name (e.g., "Coal", "Sandstone")
2. **Code** - Short code (e.g., "CO", "SS") used in outputs
3. **Background Color** - Display color for this lithology
4. **SVG Pattern** - Geological pattern file path
5. **Pattern Preview** - Visual preview of the pattern
6. **Lithology Qualifier** - Additional qualifier (e.g., "fine", "coarse")
7. **Shade** - Color shade variant
8. **Hue** - Color hue adjustment
9. **Gamma Min** - Minimum gamma ray value (API units)
10. **Gamma Max** - Maximum gamma ray value (API units)
11. **Density Min** - Minimum density value (g/cm³)
12. **Density Max** - Maximum density value (g/cm³)

**Special Values:**
- **INVALID_DATA_VALUE** (-999.25): Marks "don't care" for a parameter
- **0.0 to 0.0 range**: Treated as "missing" when researched defaults are enabled

#### Rule Management Buttons:
- **Add Rule**: Creates a new empty rule row
- **Remove Rule**: Deletes selected rule(s)
- **Import Rules**: Load rules from JSON or CSV file
- **Export Rules**: Save rules to file for sharing
- **Reset to Defaults**: Restore factory default rules
- **Researched Defaults**: Open dialog with pre-defined ranges

#### Range Gap Visualizer
A visual tool that shows:
- **Coverage Gaps**: Depth ranges not covered by any rule
- **Rule Overlaps**: Where multiple rules might apply
- **Missing Parameters**: Rules with incomplete ranges
- **Visual Feedback**: Color-coded coverage map

**Using the Visualizer:**
1. Rules are displayed as horizontal bars
2. Gaps show as white spaces
3. Overlaps show as darker bands
4. Click bars to select corresponding rule
5. Adjust rules to eliminate gaps and reduce overlaps

### Visualization Tab
Controls all display and rendering options.

#### Stratigraphic Column Settings:
1. **Separator Line Thickness** (0.0-5.0 pixels):
   - Controls thickness of lines between lithology units
   - 0.0 = no lines, 0.5 = default, 5.0 = very thick
   - Affects both overview and enhanced columns

2. **Draw Separator Lines** (checkbox):
   - Toggle visibility of separator lines
   - Useful for cleaner display with many thin units
   - Can be disabled for solid color blocks

3. **Disable SVG Patterns** (checkbox):
   - Use solid colors instead of geological patterns
   - Improves performance with many units
   - Useful for printing or simplified displays

#### Curve Display Settings:
1. **Curve Line Thickness** (0.1-5.0 pixels):
   - Thickness of gamma and density curves
   - Thicker lines for presentations, thinner for detail
   - Affects all curve displays

2. **Curve Inversion Options**:
   - **Invert Gamma Curve**: Flip gamma scale (high to low)
   - **Invert Short Space Density**: Flip SSD scale
   - **Invert Long Space Density**: Flip LSD scale
   - Useful for matching different tool conventions

#### Color and Pattern Management:
1. **Background Color Picker**:
   - Click color cell in rules table to change
   - Color dialog with custom palette
   - Colors saved with rules

2. **SVG Pattern Browser**:
   - Browse and select pattern files
   - Preview patterns before applying
   - Supports custom SVG patterns

### Analysis Tab
Controls lithology classification and analysis parameters.

#### Analysis Method:
- **Standard Method** (default):
  - Uses both gamma AND density ranges
  - More accurate but requires both curves
  - Applies researched defaults for missing ranges

- **Simple Method**:
  - Classifies by density first, then gamma
  - Useful when only one curve is reliable
  - Faster but less precise

#### Research Defaults Settings:
1. **Use Researched Defaults** (checkbox):
   - Apply pre-defined ranges when rules have missing/zero ranges
   - Defaults based on geological research
   - Can be disabled for manual control only

2. **Researched Defaults Dialog**:
   - View and edit default ranges
   - Based on common lithology properties
   - Can be customized for local geology

#### Unit Merging Settings:
1. **Merge Thin Units** (checkbox):
   - Combine adjacent units below threshold
   - Reduces clutter in stratigraphic column
   - Preserves geological accuracy

2. **Merge Threshold** (0.01-1.0 meters):
   - Minimum thickness to keep as separate unit
   - 0.05m (5cm) default, adjustable
   - Units thinner than threshold are merged

#### Smart Interbedding Settings:
1. **Enable Smart Interbedding** (checkbox):
   - Automatically detect interbedded sequences
   - Analyzes curve patterns for mixing
   - Suggests interbedding where appropriate

2. **Max Sequence Length** (5-50 units):
   - Maximum components in interbedded sequence
   - Prevents overly complex interbedding
   - 10 units default

3. **Thick Unit Threshold** (0.1-5.0 meters):
   - Stop interbedding when next unit exceeds this thickness
   - Prevents breaking thick homogeneous units
   - 0.5m default

#### Fallback Classification:
- **Enable Fallback Classification** (checkbox):
  - Reduces "NL" (Not Logged) results
  - Applies less strict classification when no rule matches
  - Useful for incomplete rule sets

### General Tab
Application-wide settings and preferences.

#### Drilling Parameters:
1. **Bit Size** (50-500 mm):
   - Drilling bit diameter in millimeters
   - Used for caliper anomaly detection
   - Typical values: 150mm (exploration), 100mm (production)

2. **Show Anomaly Highlights** (checkbox):
   - Highlight caliper anomalies (CAL - BitSize > 20mm)
   - Red highlighting in curve plotter
   - Helps identify poor hole conditions

#### Casing Depth Masking:
1. **Enable Casing Depth Masking** (checkbox):
   - Mask intervals above casing depth as "NL"
   - Useful for cased hole sections
   - Automatically applies to all analysis

2. **Casing Depth** (0-5000 meters):
   - Depth of casing shoe in meters
   - Everything above this depth forced to "NL"
   - Can be hole-specific or global

#### Performance Settings:
1. **SVG Pattern Caching**:
   - Cache rendered patterns for faster display
   - Adjustable cache size
   - Clear cache if patterns change

2. **Data Sampling**:
   - Reduce data points for large files
   - Maintains accuracy while improving performance
   - Adjustable sampling interval

### File Management Tab
Controls file handling, paths, and workspace management.

#### Workspace Settings:
1. **Default Workspace Path**:
   - Location for project files
   - Can be changed for different projects
   - Supports network paths

2. **Auto-save Interval** (1-60 minutes):
   - Automatic backup of project state
   - Protects against crashes
   - Adjustable frequency

#### File Handling:
1. **Recent Files List** (5-50 files):
   - Number of files in recent menu
   - Quick access to frequently used files
   - Clear list option

2. **File Association**:
   - Associate file types with Earthworm
   - Double-click files to open in Earthworm
   - Windows/macOS/Linux support

#### Import/Export Settings:
1. **Default Export Format**:
   - CSV, Excel, or JSON
   - Preserves all data and formatting
   - Batch export options

2. **Coordinate System Defaults**:
   - Default projection for new projects
   - Auto-detect from files
   - Conversion settings

#### Session Management:
1. **Session Auto-save**:
   - Save session on exit
   - Prompt to save changes
   - Recovery of unsaved work

2. **Session Templates**:
   - Save common session configurations
   - Quick start for repetitive work
   - Shareable session templates

### Advanced Settings

#### Logging and Debugging:
1. **Log Level**:
   - Error, Warning, Info, Debug
   - Control console/output verbosity
   - Log file location

2. **Debug Mode**:
   - Additional validation checks
   - Performance profiling
   - Detailed error reporting

#### Memory Management:
1. **Cache Size** (10-1000 MB):
   - Maximum memory for cached data
   - Automatic cache cleanup
   - Manual cache clear

2. **Data Compression**:
   - Compress stored data for large projects
   - Trade-off between speed and memory
   - Adjustable compression level

#### Update and Maintenance:
1. **Check for Updates**:
   - Automatic update checking
   - Manual check option
   - Update notification settings

2. **Reset Settings**:
   - Restore all defaults
   - Clear all user settings
   - Factory reset option

### Settings Management

#### Saving and Applying:
- **OK Button**: Save settings and close dialog
- **Apply Button**: Save settings without closing
- **Cancel Button**: Discard changes
- Settings take effect immediately when applied

#### Settings Files:
1. **User Settings File**:
   - Stored in user application data directory
   - Persists between sessions
   - Platform-specific locations

2. **Project Settings File**:
   - Saved with project sessions
   - Overrides user settings for specific projects
   - Travels with project files

3. **Template Settings**:
   - Saved in template files
   - Applied when template is loaded
   - Can be exported/imported

#### Settings Migration:
- **Import Settings**: From older versions
- **Export Settings**: For backup or transfer
- **Settings Comparison**: Compare different settings files
- **Batch Apply**: Apply settings to multiple projects

#### Best Practices:
1. **Start with Defaults**: Use factory defaults, then customize
2. **Save Templates**: Save common configurations as templates
3. **Project-specific Settings**: Override defaults per project
4. **Regular Backups**: Export settings periodically
5. **Document Changes**: Note important setting changes

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