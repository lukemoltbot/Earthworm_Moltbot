# Earthworm Borehole Logger - Complete User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation & Setup](#installation--setup)
4. [Getting Started](#getting-started)
5. [Core Workflow](#core-workflow)
6. [Lithology Rules Management](#lithology-rules-management)
7. [Analysis Settings](#analysis-settings)
8. [Visualization Features](#visualization-features)
9. [Advanced Features](#advanced-features)
10. [File Operations](#file-operations)
11. [Troubleshooting](#troubleshooting)
12. [Tips & Best Practices](#tips--best-practices)

## Introduction

Earthworm Borehole Logger is a comprehensive geological software application designed for processing, analyzing, and visualizing borehole data. It supports LAS, CSV, and Excel file formats and provides advanced lithology classification, stratigraphic column generation, and geological analysis capabilities.

### Key Features
- **Multi-format Support**: Import LAS, CSV, and Excel files
- **Lithology Classification**: Automated classification based on gamma ray and density curves
- **Stratigraphic Visualization**: Generate detailed stratigraphic columns with SVG patterns
- **Interactive Editing**: Edit lithology units, create interbedding, and refine classifications
- **Advanced Analysis**: Smart interbedding detection, range gap analysis, and anomaly detection
- **Multi-hole Management**: Map visualization and cross-section generation
- **Export Capabilities**: Generate comprehensive lithology reports and export to CSV

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 or higher
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 500 MB free space
- **Display**: 1920x1080 resolution minimum

### Software Dependencies
- PyQt6 (GUI framework)
- pandas (data manipulation)
- numpy (numerical computations)
- lasio (LAS file parsing)
- openpyxl (Excel file support)
- matplotlib/pyqtgraph (plotting)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/lukemoltbot/Earthworm_openclaw.git
cd Earthworm_openclaw
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python main.py
```

## Getting Started

### Application Interface Overview

The Earthworm Borehole Logger features a modern, multi-document interface (MDI) with the following main components:

1. **Main Menu Bar**: File operations, settings, and help
2. **Project Explorer**: File browser for LAS/CSV/Excel files
3. **Main Workspace**: MDI area for hole editors, maps, and cross-sections
4. **Status Bar**: Application status and progress indicators

### First-Time Setup

1. **Load CoalLog Dictionaries**: The application automatically loads CoalLog v3.1 standards from `src/assets/CoalLog v3.1 Dictionaries.xlsx`
2. **Configure Settings**: Access Settings via the gear icon or Settings menu
3. **Set Default Paths**: Configure AVG executable and SVG patterns directory if needed

## Core Workflow

### Step 1: Load Data Files

1. **Method A**: Use Project Explorer
   - Navigate to your data directory in the Project Explorer dock
   - Double-click on LAS, CSV, or Excel files to open them

2. **Method B**: Use Load LAS File Button
   - Click "Load LAS File" in the main toolbar
   - Select your LAS file from the file dialog

3. **Method C**: Drag and Drop
   - Drag files directly from your file explorer into the application window

### Step 2: Configure Curve Mapping

When a LAS file is loaded, the application automatically detects available curves (mnemonics):

1. **Gamma Ray Curve**: Select from available mnemonics (typically GR, GAMMA, etc.)
2. **Density Curves**: 
   - Short Space Density (typically RHOB, DENS)
   - Long Space Density (typically LSD, DENL)
3. **Optional Curves**: Caliper, Resistivity, etc.

**Note**: The application uses the Short Space Density selection for both density fields by default.

### Step 3: Define Lithology Rules

Before running analysis, configure lithology classification rules:

1. **Access Settings**: Click the Settings button or use Settings → Lithology Rules
2. **Add Rules**: 
   - Click "Add Rule" to create new lithology classifications
   - Configure Name, Code, Qualifier, and visual properties
   - Set Gamma and Density ranges for classification
3. **Import Standards**: Use "Load Settings" to import predefined rule sets

### Step 4: Run Analysis

1. **Verify Settings**: Ensure lithology rules are configured
2. **Run Analysis**: Click "Run Analysis" button
3. **Monitor Progress**: Analysis runs in background with progress updates
4. **Review Results**: Analysis completes with three synchronized views:
   - Curve Plotter (left): Gamma and density curves with lithology boundaries
   - Stratigraphic Column (center): Visual representation of lithology units
   - Editor Table (right): Detailed lithology unit data

### Step 5: Review and Edit Results

1. **Scroll Synchronization**: All three views scroll together
2. **Unit Selection**: Click on units in any view to highlight them across all views
3. **Edit Data**: Modify lithology units directly in the editor table
4. **Create Interbedding**: Select consecutive units and use "Create Interbedding" button

### Step 6: Export Results

1. **Export CSV**: Click "Export to CSV" to save edited lithology data
2. **Generate Report**: Use Settings → Export Lithology Report for comprehensive analysis
3. **Save Project**: Save all settings and data as a project file

## Lithology Rules Management

### Rule Structure

Each lithology rule contains:

1. **Basic Information**:
   - Name: Descriptive name (e.g., "Sandstone")
   - Code: Standard lithology code (e.g., "SS")
   - Qualifier: Additional classification (e.g., "F" for Fine-grained)

2. **Visual Properties**:
   - Shade, Hue, Colour: From CoalLog standards
   - Estimated Strength: Strength classification
   - Display Color: Background color for stratigraphic column
   - SVG Pattern: Pattern overlay for visualization

3. **Classification Ranges**:
   - Gamma Min/Max: Gamma ray range (API units)
   - Density Min/Max: Density range (g/cc)

### Creating and Editing Rules

#### Adding New Rules
1. Open Settings Dialog → Lithology Rules tab
2. Click "Add Rule"
3. Fill in all required fields
4. Use dropdowns for standardized values (Shade, Hue, Colour, Estimated Strength)
5. Set classification ranges based on geological knowledge

#### Editing Existing Rules
1. Select rule in the table
2. Modify values directly in cells
3. Use color picker for Display Color
4. Use browse button for SVG Pattern selection

#### Importing Rule Sets
1. Use "Load Settings" to import JSON rule files
2. Predefined rule sets available in `config/` directory
3. Can merge with existing rules or replace them

### Range Gap Analysis

The Range Analysis tab helps identify gaps and overlaps in classification ranges:

1. **Visual Representation**: Color-coded bars show covered ranges
2. **Gap Detection**: Red sections indicate uncovered ranges
3. **Overlap Detection**: Darker colors show overlapping ranges
4. **Refresh Analysis**: Click "Refresh Range Analysis" after rule changes

## Analysis Settings

### General Settings

1. **Apply Researched Defaults**: Automatically apply researched gamma/density ranges when rules have zero values
2. **Merge Thin Units**: Combine lithology units thinner than 5cm
3. **Smart Interbedding**: Automatically detect potential interbedding sequences
4. **Fallback Classification**: Reduce "NL" (Not Logged) classifications by applying fallback rules

### Smart Interbedding Parameters

When Smart Interbedding is enabled:

1. **Max Sequence Length**: Maximum number of units to consider for interbedding (default: 10)
2. **Thick Unit Threshold**: Minimum thickness (meters) to consider a unit "thick" (default: 0.5m)

### Curve Settings

1. **Curve Thickness**: Adjust line thickness for all curves
2. **Curve Inversion**: Invert gamma or density curves if needed
3. **Curve Visibility**: Show/hide specific curve types

### Display Settings

1. **Separator Lines**: Show/hide lines between stratigraphic units
2. **Separator Thickness**: Adjust line thickness
3. **SVG Patterns**: Enable/disable SVG pattern overlays
4. **Theme**: Light/dark theme (currently light theme only)

## Visualization Features

### Curve Plotter

The Curve Plotter displays:

1. **Gamma Ray Curve**: Typically on left track
2. **Density Curves**: Short and long space density on right track
3. **Lithology Boundaries**: Vertical lines showing unit boundaries
4. **Anomaly Highlights**: Red highlighting for caliper anomalies (CAL - BitSize > 20mm)
5. **Zoom Controls**: Synchronized zoom with stratigraphic column

**Interactive Features**:
- Click and drag to pan
- Use mouse wheel to zoom
- Right-click for context menu
- Hover for curve values

### Stratigraphic Column

The Stratigraphic Column provides:

1. **Visual Representation**: Color-coded lithology units with patterns
2. **Depth Scale**: Y-axis showing depth in meters
3. **Unit Information**: Hover for lithology details
4. **Selection Highlighting**: Yellow border for selected units
5. **Separator Lines**: Optional lines between units

**SVG Patterns**:
- 239 predefined geological patterns
- Patterns combined with background colors
- Can be disabled for solid colors only

### Editor Table

The Editor Table shows detailed lithology unit data:

1. **37-Column Schema**: Full CoalLog v3.1 compliance
2. **Editable Cells**: Modify lithology classifications directly
3. **Column Visibility**: Show/hide columns via Column Configurator
4. **Sorting**: Click column headers to sort
5. **Filtering**: Basic text filtering available

**Key Columns**:
- from_depth, to_depth: Unit boundaries
- lithology_code, lithology_qualifier: Classification
- shade, hue, colour, estimated_strength: Visual properties
- background_color, svg_path: Display settings
- thickness: Unit thickness

## Advanced Features

### Interbedding Creation

#### Manual Interbedding
1. Select 2+ consecutive lithology units in editor table
2. Click "Create Interbedding" button
3. Configure interbedding parameters in dialog:
   - Select lithologies and percentages
   - Set interrelationship code
   - Choose dominant lithology (sequence 1)
4. Apply to combine selected units into interbedded sequence

#### Smart Interbedding (Automatic)
1. Enable Smart Interbedding in Analysis Settings
2. Run analysis
3. Review suggestions in dialog
4. Select which suggestions to apply
5. Automatically combines thin alternating sequences

### Map Visualization

1. **Open Map Window**: Use View → Map Window or toolbar button
2. **Load Holes**: Automatically loads files from Project Explorer
3. **Coordinate Extraction**: Extracts coordinates from LAS file headers
4. **Selection**: Click holes to select, syncs with Project Explorer
5. **Cross-Section Creation**: Select 2+ holes and create cross-section

### Cross-Section Generation

1. **Select Holes**: Select 2+ holes in Project Explorer or Map
2. **Create Cross-Section**: Use Tools → Cross-Section or right-click menu
3. **3D Visualization**: Shows lithology correlation between holes
4. **Interactive**: Pan, zoom, and adjust visualization

### NL (Not Logged) Review

1. **Access NL Review**: Settings → Review NL Intervals
2. **Statistics**: Shows NL percentage and distribution
3. **Depth Analysis**: Identifies NL concentration zones
4. **Export**: Export NL analysis report

### Column Configurator

1. **Access**: Settings → Column Configurator
2. **Visibility Control**: Show/hide specific columns
3. **Presets**: Save and load column visibility profiles
4. **Apply**: Changes apply to all open hole editors

## File Operations

### Supported File Formats

1. **LAS Files**:
   - Standard LAS 2.0 and 3.0
   - Automatic mnemonic detection
   - Metadata extraction

2. **CSV Files**:
   - Comma or tab separated
   - Header row required
   - Depth column must be named "DEPTH" or similar

3. **Excel Files**:
   - .xlsx format
   - Multiple sheet support
   - Automatic data type detection

### Settings Management

#### Save Settings
1. **Update Settings**: Save current settings to default location
2. **Save Settings As**: Save to custom JSON file
3. **Automatic Save**: Settings saved on application close

#### Load Settings
1. **Load from File**: Import JSON settings file
2. **Merge/Replace**: Choose to merge with or replace current settings
3. **Default Settings**: Reset to application defaults

#### Export Reports
1. **Lithology Report**: Comprehensive analysis with statistics
2. **NL Analysis**: Detailed Not Logged interval report
3. **Range Analysis**: Gap and overlap analysis report

### Project Management

1. **Session Management**: Save/load project sessions
2. **Template System**: Apply project templates for consistent settings
3. **Workspace State**: Automatic saving of window layout and open files

## Troubleshooting

### Common Issues

#### 1. LAS File Loading Errors
- **Issue**: "Failed to load LAS file"
- **Solution**: 
  - Verify LAS file version (2.0 or 3.0 supported)
  - Check for corrupted sections
  - Try loading in lasio library directly

#### 2. Missing Curves
- **Issue**: Expected curves not appearing in dropdowns
- **Solution**:
  - Check LAS file contains the curves
  - Verify mnemonic names match expected values
  - Use Curve Visibility settings to enable hidden curves

#### 3. Slow Performance
- **Issue**: Application runs slowly with large files
- **Solution**:
  - Reduce number of open holes
  - Disable SVG patterns
  - Increase system RAM
  - Use simpler analysis method

#### 4. SVG Pattern Issues
- **Issue**: Patterns not displaying correctly
- **Solution**:
  - Verify SVG directory path in settings
  - Check file permissions
  - Disable SVG patterns temporarily
  - Clear SVG cache

### Error Messages

#### "No lithology rules defined"
- **Cause**: No rules configured before analysis
- **Fix**: Configure lithology rules in Settings

#### "Analysis failed - insufficient data"
- **Cause**: Missing required curves or data
- **Fix**: Ensure gamma and density curves are selected

#### "Memory allocation error"
- **Cause**: File too large for available memory
- **Fix**: 
  - Close other applications
  - Use smaller file subsets
  - Increase system swap space

## Tips & Best Practices

### Data Preparation

1. **LAS File Quality**:
   - Ensure consistent depth sampling
   - Verify curve mnemonics are standard
   - Check for data gaps or anomalies

2. **Pre-analysis Checks**:
   - Review curve ranges before analysis
   - Check for calibration issues
   - Identify and mark bad data intervals

### Analysis Optimization

1. **Rule Configuration**:
   - Start with broad ranges, then refine
   - Use Researched Defaults for unknown ranges
   - Regularly review and update rules

2. **Performance Tips**:
   - Disable SVG patterns for large files
   - Use Simple analysis method for quick results
   - Close unused hole editors

### Workflow Efficiency

1. **Keyboard Shortcuts**:
   - Ctrl+O: Open file
   - Ctrl+S: Save settings
   - Ctrl+E: Export data
   - F5: Refresh views

2. **Batch Processing**:
   - Use templates for consistent settings
   - Save and load rule sets
   - Automate with project sessions

### Quality Control

1. **Validation Steps**:
   - Compare automated vs manual classifications
   - Review NL intervals for patterns
   - Check range coverage with gap analysis

2. **Documentation**:
   - Save settings with each analysis
   - Export comprehensive reports
   - Maintain change logs for rule updates

## Appendix

### CoalLog v3.1 Standards

Earthworm Borehole Logger implements the full CoalLog v3.1 standard including:

1. **Lithology Types**: Complete classification system
2. **Qualifiers**: Detailed lithology modifiers
3. **Visual Properties**: Shade, Hue, Colour, Strength
4. **Interrelationship Codes**: Geological relationships
5. **37-Column Schema**: Full data structure compliance

### SVG Pattern Library

The application includes 239 geological SVG patterns:

1. **Lithology-specific**: Patterns for common rock types
2. **Qualifier Combinations**: Combined patterns for specific classifications
3. **Custom Patterns**: Support for user-added patterns
4. **Performance Optimized**: Cached rendering for speed

### API and Extensibility

For developers and advanced users:

1. **Plugin System**: Custom analysis modules
2. **Template Engine**: Project template creation
3. **Scripting Support**: Python API for automation
4. **Data Export Formats**: Multiple output formats

---

## Support and Resources

- **Documentation**: Complete documentation at [docs.earthworm-logger.com](https://docs.earthworm-logger.com)
- **Community**: Join the Earthworm user community on Discord
- **Issue Tracking**: Report bugs and request features on GitHub
- **Training**: Online tutorials and webinars available

---

*Earthworm Borehole Logger v3.1 - Last Updated: February 2026*