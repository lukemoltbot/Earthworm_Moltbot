# Earthworm Borehole Logger

## Overview

Earthworm Borehole Logger is a comprehensive geological software application for processing, analyzing, and visualizing borehole data. It supports LAS, CSV, and Excel file formats and provides advanced lithology classification, stratigraphic column generation, and geological analysis capabilities.

## Features

### Core Functionality
- **Multi-format Support**: Import LAS, CSV, and Excel files
- **Lithology Classification**: Automated classification based on gamma ray and density curves
- **Stratigraphic Visualization**: Generate detailed stratigraphic columns with SVG patterns
- **Interactive Editing**: Edit lithology units, create interbedding, and refine classifications

### Advanced Analysis
- **Smart Interbedding Detection**: Automatically identify potential interbedding sequences
- **Range Gap Analysis**: Visualize coverage gaps in lithology classification ranges
- **Anomaly Detection**: Highlight caliper anomalies (CAL - BitSize > 20mm)
- **NL Review**: Analyze "Not Logged" intervals with statistics

### Visualization Tools
- **Curve Plotter**: Display gamma and density curves with lithology boundaries
- **Stratigraphic Column**: Color-coded lithology units with geological patterns
- **Map Window**: Visualize hole locations and create cross-sections
- **Cross-Section Generator**: 3D visualization of lithology correlation between holes

### Data Management
- **37-Column CoalLog v3.1 Compliance**: Full industry standard support
- **Project Sessions**: Save and load complete project states
- **Template System**: Apply consistent settings across projects
- **Comprehensive Export**: Generate detailed lithology reports and CSV exports

## Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/lukemoltbot/Earthworm_openclaw.git
cd Earthworm_openclaw

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Basic Workflow
1. **Load Data**: Open LAS/CSV/Excel file via Project Explorer or File menu
2. **Configure Rules**: Set up lithology classification rules in Settings
3. **Run Analysis**: Click "Run Analysis" to process the data
4. **Review Results**: Examine curves, stratigraphic column, and editor table
5. **Edit & Export**: Modify classifications and export results

## Documentation

- **[Complete User Guide](Earthworm_Borehole_Logger_User_Guide.md)**: Detailed instructions for all features
- **[Quick Reference Guide](Earthworm_Quick_Reference.md)**: Fast lookup for common tasks
- **In-app Help**: Tooltips and context-sensitive help throughout the application

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+)
- **Python**: 3.8 or higher
- **RAM**: 8 GB minimum, 16 GB recommended
- **Storage**: 500 MB free space
- **Display**: 1920x1080 resolution minimum

## Dependencies

- PyQt6 (GUI framework)
- pandas (data manipulation)
- numpy (numerical computations)
- lasio (LAS file parsing)
- openpyxl (Excel file support)
- matplotlib/pyqtgraph (plotting)

## Project Structure

```
Earthworm_openclaw/
├── main.py                    # Application entry point
├── src/
│   ├── core/                  # Core functionality
│   │   ├── config.py          # Configuration constants
│   │   ├── settings_manager.py # Settings management
│   │   └── analyzer.py        # Analysis algorithms
│   ├── ui/                    # User interface
│   │   ├── main_window.py     # Main application window
│   │   ├── widgets/           # Custom UI widgets
│   │   └── dialogs/           # Dialog windows
│   └── assets/                # Resources
│       ├── svg/               # 239 geological SVG patterns
│       └── CoalLog v3.1 Dictionaries.xlsx
├── config/                    # Configuration files
├── examples/                  # Sample data files
└── docs/                      # Documentation
```

## Recent Enhancements

### Phase 3: Enhanced Visualization & Real-time Sync
- **Enhanced Stratigraphic Column**: Improved pattern rendering and display
- **Real-time Synchronization**: All views scroll and zoom together
- **SVG Pattern Integration**: 239 geological patterns with color blending

### Phase 4: Depth Correction - Interactive Lithology Boundaries
- **Interactive Boundary Editing**: Click and drag lithology boundaries
- **Enhanced Settings Dialog**: Added dropdowns for Shade, Hue, Colour, Estimated Strength
- **Display Color Column**: Color picker for stratigraphic column visualization
- **SVG Pattern Selection**: Browse and select SVG patterns for lithology units

### Phase 5: Multi-hole Management & Analysis
- **Map Visualization**: Geographic display of hole locations
- **Cross-Section Generation**: 3D correlation between holes
- **Smart Interbedding**: Automatic detection of interbedded sequences
- **Range Gap Analysis**: Visual identification of classification gaps

## Support

- **Documentation**: Complete user guide and quick reference included
- **Community**: Join the Earthworm user community on Discord
- **Issue Tracking**: Report bugs and request features on GitHub
- **Training**: Online tutorials and webinars available

## License

[License information to be added]

## Acknowledgments

- CoalLog v3.1 standards implementation
- Geological SVG pattern library contributors
- Open source community for dependencies

---

*Earthworm Borehole Logger - Professional Geological Analysis Software*