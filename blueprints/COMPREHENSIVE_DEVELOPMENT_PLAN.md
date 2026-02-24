# COMPREHENSIVE DEVELOPMENT PLAN: 1 Point Desktop Main Graphic Window UI Replication
## Earthworm Borehole Logger - Phase 4 Implementation

**Document Version**: 1.0  
**Target Framework**: PyQt6  
**Target Python Version**: 3.8+  
**Status**: Ready for Implementation  

---

## TABLE OF CONTENTS
1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Project Structure & Organization](#project-structure--organization)
4. [Core Data Models](#core-data-models)
5. [State Management System](#state-management-system)
6. [UI Layout Architecture](#ui-layout-architecture)
7. [Component Implementation Guide](#component-implementation-guide)
8. [Integration & Synchronization](#integration--synchronization)
9. [Testing Strategy](#testing-strategy)
10. [Performance Optimization](#performance-optimization)
11. [Implementation Checklist](#implementation-checklist)

---

## EXECUTIVE SUMMARY

This plan provides step-by-step instructions to replicate the 1 Point Desktop Main Graphic Window in Earthworm Borehole Logger. The implementation requires:

- **Architecture**: Unified depth state management system with event-driven synchronization
- **Components**: 5 major UI components + 2 core managers
- **Data Flow**: Centralized state → all visualizations subscribe and update
- **Key Innovation**: Shared depth coordinate system used by ALL components
- **Expected Timeline**: 3-4 weeks for full implementation with testing
- **Complexity Level**: Advanced (requires careful coordinate system management)

### What Makes This Different from Current Implementation

Your current `EarthwormGraphicWindow` has isolated rendering contexts. This plan consolidates them into a unified system where:
- One "source of truth" for depth
- All visualizations share identical coordinate transformations
- All interactions (clicks, scrolls, selections) update central state
- All components automatically re-render in response to state changes

---

## SYSTEM ARCHITECTURE OVERVIEW

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIFIED GRAPHIC WINDOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │         DepthStateManager (Central State)                    │  │
│  │  - viewportDepthRange                                        │  │
│  │  - cursorDepth                                              │  │
│  │  - selectedLithologyRange                                    │  │
│  │  - Events: depthRangeChanged, cursorDepthChanged, etc        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ▲                                      │
│        ┌─────────────────────┼─────────────────────┐               │
│        │                     │                     │               │
│        ▼                     ▼                     ▼               │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │ Strat       │      │ LAS Curves  │      │ Lithology   │      │
│  │ Column      │      │ Canvas      │      │ Table       │      │
│  └─────────────┘      └─────────────┘      └─────────────┘      │
│        │                     │                     │               │
│  Event: click          Event: click          Event: selection    │
│  Updates depth        Updates depth         Updates depth        │
│        │                     │                     │               │
│        └─────────────────────┼─────────────────────┘               │
│                              │                                     │
│                              ▼                                     │
│                    DepthStateManager                               │
│                   (Emits state changes)                            │
│                   All components re-render                         │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │    DepthCoordinateSystem (Shared by ALL components)          │  │
│  │  - depthToScreenY(depth) → consistent mapping everywhere     │  │
│  │  - screenYToDepth(screenY) → consistent reverse mapping      │  │
│  │  - depthToPixelHeight(depth) → consistent sizing             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Example: User Clicks on Stratigraphic Column

```
User Click on Strat Column
        ↓
StratigraphicColumn.handleClick(event)
        ↓
Calculate depth from click using DepthCoordinateSystem
        ↓
Find matching lithology interval
        ↓
depthStateManager.setSelectedDepthRange(from, to)
        ↓
depthStateManager emits 'selectionChanged' signal
        ↓
All subscribed components receive signal:
├─ StratigraphicColumn.onSelectionChanged() → re-render with highlight
├─ LASCurves.onSelectionChanged() → re-render with highlight
└─ LithologyTable.onSelectionChanged() → select corresponding rows
        ↓
All updates use SAME DepthCoordinateSystem
        ↓
Perfect synchronization achieved ✓
```

---

## PROJECT STRUCTURE & ORGANIZATION

### Current Structure (To Preserve)
```
src/
├── ui/
│   ├── main_window.py
│   ├── dialogs/
│   ├── widgets/
│   └── components/
├── core/
│   ├── config.py
│   ├── settings_manager.py
│   └── template_manager.py
└── ...
```

### New Files to Create

```
src/ui/graphic_window/
├── __init__.py
├── unified_graphic_window.py          # Main composite window (REPLACES old EarthwormGraphicWindow)
├── state/
│   ├── __init__.py
│   ├── depth_state_manager.py         # Central state (NEW - CRITICAL)
│   └── depth_coordinate_system.py     # Shared coordinates (NEW - CRITICAL)
├── components/
│   ├── __init__.py
│   ├── stratigraphic_column.py        # Left panel - lithology visualization
│   ├── las_curves_display.py          # Center/Right - geophysics curves
│   ├── lithology_data_table.py        # Upper right - data entry table
│   ├── preview_window.py              # Far right - mini overview
│   └── information_panel.py           # Bottom - info/tabs (Info, Core Photo, etc)
├── synchronizers/
│   ├── __init__.py
│   ├── scroll_synchronizer.py         # Handles scroll sync
│   ├── selection_synchronizer.py      # Handles selection sync
│   └── depth_synchronizer.py          # Handles depth cursor sync
├── utils/
│   ├── __init__.py
│   ├── depth_calculations.py          # Depth-related math utilities
│   └── rendering_utils.py             # Canvas/rendering helpers
└── styles/
    ├── __init__.py
    └── graphic_window_styles.py       # QSS stylesheets for colors/fonts

src/core/
├── graphic_models/                     # Data models for graphic window
│   ├── __init__.py
│   ├── lithology_interval.py          # Represents single lithology layer
│   ├── las_point.py                   # Single curve data point
│   ├── hole_data_provider.py          # Interface to hole data
│   └── synchronization_cache.py       # Cache for performance
```

### File Interdependencies

```
                         unified_graphic_window.py (Main Composite)
                                    ▲
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
         stratigraphic_column    las_curves      lithology_table
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                        depth_state_manager
                        depth_coordinate_system
                                    ▲
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
          scroll_synchronizer  selection_synchronizer  depth_synchronizer
                  │                 │                 │
                  └─────────────────┼─────────────────┘
                                    ▼
                        depth_calculations.py
```

---

## CORE DATA MODELS

### 1. LithologyInterval (Core Data Structure)

**File**: `src/core/graphic_models/lithology_interval.py`

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class LithologyCode(Enum):
    """Lithology classification codes"""
    SAND = "SAND"
    SILT = "SILT"
    COAL = "COAL"
    SHALE = "SHALE"
    MUDSTONE = "MUDSTONE"
    # ... add all codes from CoalLog dictionary

@dataclass
class LithologyInterval:
    """
    Represents a single lithology interval in a borehole.
    This is the fundamental unit of data visualization.
    """
    from_depth: float              # Depth at top of interval (meters)
    to_depth: float                # Depth at bottom of interval (meters)
    code: str                       # Lithology code (e.g., "COAL", "SAND")
    description: str               # Human-readable description
    color: tuple = (128, 128, 128) # RGB color tuple
    pattern: Optional[str] = None  # Pattern name if applicable
    thickness: float = None        # Calculated: to_depth - from_depth
    
    # Metadata
    sample_number: Optional[str] = None
    comment: str = ""
    
    # Validation
    is_valid: bool = True
    validation_messages: list = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.thickness = self.to_depth - self.from_depth
        if self.validation_messages is None:
            self.validation_messages = []
    
    def contains_depth(self, depth: float) -> bool:
        """Check if interval contains a depth"""
        return self.from_depth <= depth <= self.to_depth
    
    def get_depth_ratio(self, depth: float) -> float:
        """Get ratio of depth within interval (0.0 to 1.0)"""
        if self.thickness == 0:
            return 0.0
        return (depth - self.from_depth) / self.thickness
```

### 2. LASPoint (Curve Data)

**File**: `src/core/graphic_models/las_point.py`

```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class LASPoint:
    """
    Represents a single depth sample of LAS curve data.
    
    LAS (Log ASCII Standard) files contain geophysical measurements
    at various depths. Each point has multiple curve values.
    """
    depth: float                    # Depth in meters
    curves: Dict[str, float]        # {curve_name: value}
    # Common curves:
    # - gamma: Gamma Ray API units
    # - density: Bulk Density g/cm³
    # - resistivity: Resistivity ohm-m
    # - caliper: Caliper mm
    # - porosity: Porosity %
    
    def get_curve_value(self, curve_name: str, default: float = None) -> float:
        """Get value for specific curve, return default if missing"""
        return self.curves.get(curve_name, default)
    
    def has_curve(self, curve_name: str) -> bool:
        """Check if curve exists"""
        return curve_name in self.curves
```

### 3. HoleDataProvider (Data Interface)

**File**: `src/core/graphic_models/hole_data_provider.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from .lithology_interval import LithologyInterval
from .las_point import LASPoint

class HoleDataProvider(ABC):
    """
    Abstract interface for accessing hole data.
    Allows different data sources (database, file, memory) without
    coupling the UI to any specific data store.
    """
    
    @abstractmethod
    def get_lithology_intervals(self) -> List[LithologyInterval]:
        """Get all lithology intervals for this hole"""
        pass
    
    @abstractmethod
    def get_lithology_for_depth(self, depth: float) -> Optional[LithologyInterval]:
        """Get lithology interval containing this depth"""
        pass
    
    @abstractmethod
    def get_las_points(self, curve_names: List[str] = None) -> List[LASPoint]:
        """Get LAS curve data points"""
        pass
    
    @abstractmethod
    def get_depth_range(self) -> tuple:
        """Get (min_depth, max_depth) for the hole"""
        pass
    
    @abstractmethod
    def get_available_curves(self) -> List[str]:
        """Get list of available curve names"""
        pass
    
    def get_depth_bounds(self) -> dict:
        """Get depth information dict"""
        min_depth, max_depth = self.get_depth_range()
        return {
            'min': min_depth,
            'max': max_depth,
            'range': max_depth - min_depth
        }
```

### 4. Implementation: ExcelHoleDataProvider

**File**: `src/core/graphic_models/excel_hole_data_provider.py`

```python
import pandas as pd
from typing import List, Optional
from .hole_data_provider import HoleDataProvider
from .lithology_interval import LithologyInterval
from .las_point import LASPoint

class ExcelHoleDataProvider(HoleDataProvider):
    """
    Provides hole data from Earthworm Excel format (.xlsx).
    Reads lithology from one sheet, LAS from another.
    """
    
    def __init__(self, lithology_df: pd.DataFrame, las_df: pd.DataFrame):
        """
        Args:
            lithology_df: DataFrame with columns [from_depth, to_depth, code, description, ...]
            las_df: DataFrame with columns [depth, gamma, density, ...]
        """
        self.lithology_df = lithology_df.sort_values('from_depth')
        self.las_df = las_df.sort_values('depth')
        self._lithology_cache = None
        self._las_cache = None
    
    def get_lithology_intervals(self) -> List[LithologyInterval]:
        """Load and cache lithology intervals"""
        if self._lithology_cache is not None:
            return self._lithology_cache
        
        intervals = []
        for _, row in self.lithology_df.iterrows():
            interval = LithologyInterval(
                from_depth=row['from_depth'],
                to_depth=row['to_depth'],
                code=row.get('code', 'UNKNOWN'),
                description=row.get('description', ''),
                color=self._get_color_for_code(row.get('code')),
                sample_number=row.get('sample_number'),
                comment=row.get('comment', '')
            )
            intervals.append(interval)
        
        self._lithology_cache = intervals
        return intervals
    
    def get_lithology_for_depth(self, depth: float) -> Optional[LithologyInterval]:
        """Get lithology containing specific depth"""
        for interval in self.get_lithology_intervals():
            if interval.contains_depth(depth):
                return interval
        return None
    
    def get_las_points(self, curve_names: List[str] = None) -> List[LASPoint]:
        """Get LAS points for specified curves"""
        if self._las_cache is not None and curve_names is None:
            return self._las_cache
        
        if curve_names is None:
            curve_names = self.get_available_curves()
        
        points = []
        for _, row in self.las_df.iterrows():
            point = LASPoint(
                depth=row['depth'],
                curves={name: row.get(name, None) for name in curve_names}
            )
            points.append(point)
        
        if curve_names is None:
            self._las_cache = points
        
        return points
    
    def get_depth_range(self) -> tuple:
        """Get min/max depths from lithology"""
        lith = self.get_lithology_intervals()
        if not lith:
            return (0, 100)
        return (lith[0].from_depth, lith[-1].to_depth)
    
    def get_available_curves(self) -> List[str]:
        """Get all curve names from LAS data"""
        # Exclude 'depth' column
        return [col for col in self.las_df.columns if col != 'depth']
    
    def _get_color_for_code(self, code: str) -> tuple:
        """Get RGB color for lithology code"""
        color_map = {
            'SAND': (255, 215, 0),
            'COAL': (0, 0, 0),
            'SHALE': (169, 169, 169),
            'SILT': (210, 180, 140),
            'MUDSTONE': (128, 128, 128),
        }
        return color_map.get(code, (128, 128, 128))
```

---

## STATE MANAGEMENT SYSTEM

### 1. DepthStateManager (Central State Authority)

**File**: `src/ui/graphic_window/state/depth_state_manager.py`

```python
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, Tuple
from dataclasses import dataclass

@dataclass
class DepthRange:
    """Immutable depth range"""
    from_depth: float
    to_depth: float
    
    @property
    def range_size(self) -> float:
        return self.to_depth - self.from_depth
    
    def contains(self, depth: float) -> bool:
        return self.from_depth <= depth <= self.to_depth

class DepthStateManager(QObject):
    """
    Central state manager for all depth-related state.
    This is the SINGLE SOURCE OF TRUTH.
    All components subscribe to signals and update accordingly.
    
    This is critical: do NOT let components maintain their own depth state.
    All depth changes MUST go through this manager.
    """
    
    # Signals - emitted when state changes
    viewportRangeChanged = pyqtSignal(DepthRange)      # Visible depth range changed
    cursorDepthChanged = pyqtSignal(float)              # Cursor/selection depth changed
    selectionRangeChanged = pyqtSignal(DepthRange)     # Selected interval changed
    zoomLevelChanged = pyqtSignal(float)                # Zoom factor changed
    
    def __init__(self, min_depth: float = 0.0, max_depth: float = 100.0):
        super().__init__()
        
        # Depth bounds
        self.min_depth = min_depth
        self.max_depth = max_depth
        
        # Viewport (what's visible on screen)
        window_size = max_depth - min_depth
        self._viewport_range = DepthRange(min_depth, min(max_depth, min_depth + window_size / 2))
        
        # Cursor depth (for highlighting)
        self._cursor_depth = min_depth
        
        # Selection range (from lithology selection)
        self._selection_range: Optional[DepthRange] = None
        
        # Zoom level (1.0 = normal, >1 = zoomed in, <1 = zoomed out)
        self._zoom_level = 1.0
    
    # ========== VIEWPORT MANAGEMENT ==========
    
    def set_viewport_range(self, from_depth: float, to_depth: float):
        """
        Set the depth range being viewed.
        Called when user scrolls or changes view window.
        """
        from_depth = max(self.min_depth, from_depth)
        to_depth = min(self.max_depth, to_depth)
        
        if from_depth >= to_depth:
            return  # Invalid range
        
        new_range = DepthRange(from_depth, to_depth)
        
        if new_range.from_depth != self._viewport_range.from_depth or \
           new_range.to_depth != self._viewport_range.to_depth:
            self._viewport_range = new_range
            self.viewportRangeChanged.emit(new_range)
    
    def get_viewport_range(self) -> DepthRange:
        """Get currently visible depth range"""
        return self._viewport_range
    
    def scroll_viewport(self, depth_delta: float):
        """
        Scroll viewport by depth delta.
        Positive = deeper, Negative = shallower
        """
        new_from = self._viewport_range.from_depth + depth_delta
        new_to = self._viewport_range.to_depth + depth_delta
        
        # Clamp to bounds
        if new_from < self.min_depth:
            new_from = self.min_depth
            new_to = new_from + self._viewport_range.range_size
        elif new_to > self.max_depth:
            new_to = self.max_depth
            new_from = new_to - self._viewport_range.range_size
        
        self.set_viewport_range(new_from, new_to)
    
    # ========== CURSOR MANAGEMENT ==========
    
    def set_cursor_depth(self, depth: float):
        """
        Set the cursor depth (for highlighting/crosshair).
        Called when user clicks or moves cursor.
        """
        depth = max(self.min_depth, min(self.max_depth, depth))
        
        if depth != self._cursor_depth:
            self._cursor_depth = depth
            self.cursorDepthChanged.emit(depth)
    
    def get_cursor_depth(self) -> float:
        """Get current cursor depth"""
        return self._cursor_depth
    
    # ========== SELECTION MANAGEMENT ==========
    
    def set_selection_range(self, from_depth: float, to_depth: float):
        """
        Set selected lithology range.
        Called when user selects interval in table or strat column.
        """
        if from_depth >= to_depth:
            return
        
        new_range = DepthRange(from_depth, to_depth)
        
        if self._selection_range is None or \
           self._selection_range.from_depth != new_range.from_depth or \
           self._selection_range.to_depth != new_range.to_depth:
            self._selection_range = new_range
            self.selectionRangeChanged.emit(new_range)
    
    def get_selection_range(self) -> Optional[DepthRange]:
        """Get selected depth range, or None if nothing selected"""
        return self._selection_range
    
    def clear_selection(self):
        """Clear selection"""
        if self._selection_range is not None:
            self._selection_range = None
            self.selectionRangeChanged.emit(None)
    
    # ========== ZOOM MANAGEMENT ==========
    
    def set_zoom_level(self, zoom: float):
        """
        Set zoom level.
        1.0 = normal, 2.0 = zoomed in 2x, 0.5 = zoomed out 2x
        """
        zoom = max(0.1, min(10.0, zoom))  # Clamp between 0.1x and 10x
        
        if zoom != self._zoom_level:
            self._zoom_level = zoom
            self.zoomLevelChanged.emit(zoom)
    
    def get_zoom_level(self) -> float:
        """Get current zoom level"""
        return self._zoom_level
    
    def zoom_in(self, factor: float = 1.25):
        """Zoom in by factor"""
        self.set_zoom_level(self._zoom_level * factor)
    
    def zoom_out(self, factor: float = 0.8):
        """Zoom out by factor"""
        self.set_zoom_level(self._zoom_level * factor)
    
    # ========== UTILITY METHODS ==========
    
    def center_on_depth(self, depth: float):
        """
        Center viewport on a specific depth.
        Used when user clicks to navigate.
        """
        window_size = self._viewport_range.range_size
        new_from = max(self.min_depth, depth - window_size / 2)
        new_to = min(self.max_depth, new_from + window_size)
        self.set_viewport_range(new_from, new_to)
    
    def reset_to_defaults(self):
        """Reset all state to defaults"""
        window_size = self.max_depth - self.min_depth
        self.set_viewport_range(self.min_depth, min(self.max_depth, self.min_depth + window_size / 2))
        self.set_cursor_depth(self.min_depth)
        self.clear_selection()
        self.set_zoom_level(1.0)
    
    def get_state_dict(self) -> dict:
        """Get complete state as dict (for saving/debugging)"""
        return {
            'viewport': {
                'from': self._viewport_range.from_depth,
                'to': self._viewport_range.to_depth
            },
            'cursor': self._cursor_depth,
            'selection': {
                'from': self._selection_range.from_depth,
                'to': self._selection_range.to_depth
            } if self._selection_range else None,
            'zoom': self._zoom_level
        }
```

### 2. DepthCoordinateSystem (Shared Coordinates)

**File**: `src/ui/graphic_window/state/depth_coordinate_system.py`

```python
from typing import Tuple

class DepthCoordinateSystem:
    """
    Transforms between model depth (meters) and screen coordinates (pixels).
    
    THIS IS CRITICAL: All components MUST use this for ALL coordinate conversions.
    If different components use different coordinate systems, misalignment WILL occur.
    
    Pattern:
    - Strat column uses this to position rectangles
    - LAS curves use this to position curve paths
    - Table uses this to position selection highlights
    - All use IDENTICAL transformation functions
    """
    
    def __init__(self, 
                 canvas_height: float,
                 canvas_width: float,
                 padding_top: float = 20,
                 padding_bottom: float = 20,
                 padding_left: float = 50,
                 padding_right: float = 50):
        """
        Initialize coordinate system.
        
        Args:
            canvas_height: Height of drawing area in pixels
            canvas_width: Width of drawing area in pixels
            padding_*: Padding for axes/labels
        """
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom
        self.padding_left = padding_left
        self.padding_right = padding_right
        
        # Current depth range being displayed
        self.min_depth = 0.0
        self.max_depth = 100.0
        self.zoom_level = 1.0
    
    # ========== DEPTH TO SCREEN CONVERSION ==========
    
    def set_depth_range(self, min_depth: float, max_depth: float):
        """
        Set the depth range being displayed.
        Must be called whenever viewport changes.
        """
        self.min_depth = min_depth
        self.max_depth = max_depth
    
    def depth_to_screen_y(self, depth: float) -> float:
        """
        Convert depth (meters) to screen Y coordinate (pixels).
        
        This is THE MOST IMPORTANT FUNCTION.
        Every visualization that positions something vertically must use this.
        
        Y increases downward in screen coordinates.
        Depth increases downward in model.
        So mapping is straightforward: deeper = lower Y value.
        """
        total_depth = self.max_depth - self.min_depth
        
        if total_depth <= 0:
            return self.padding_top
        
        # Calculate which fraction of the depth range this depth is
        depth_ratio = (depth - self.min_depth) / total_depth
        
        # Map to screen coordinates
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        screen_y = self.padding_top + (depth_ratio * usable_height)
        
        return screen_y
    
    def screen_y_to_depth(self, screen_y: float) -> float:
        """
        Inverse of depth_to_screen_y.
        Convert screen Y coordinate back to depth.
        Used when processing user clicks.
        """
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        
        if usable_height <= 0:
            return self.min_depth
        
        # Calculate which fraction of screen height this is
        screen_ratio = (screen_y - self.padding_top) / usable_height
        
        # Map back to depth
        total_depth = self.max_depth - self.min_depth
        depth = self.min_depth + (screen_ratio * total_depth)
        
        return depth
    
    # ========== DEPTH TO PIXEL HEIGHT CONVERSION ==========
    
    def depth_thickness_to_pixel_height(self, depth_thickness: float) -> float:
        """
        Convert a depth thickness (e.g., 1 meter) to pixel height on screen.
        
        Used for:
        - Height of lithology rectangles
        - Height of curve segments
        - Selection box height
        """
        total_depth = self.max_depth - self.min_depth
        
        if total_depth <= 0:
            return 0
        
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        
        pixel_height = (depth_thickness / total_depth) * usable_height
        return pixel_height
    
    # ========== UTILITY CONVERSIONS ==========
    
    def get_pixels_per_meter(self) -> float:
        """Get the scale: how many pixels per meter of depth"""
        total_depth = self.max_depth - self.min_depth
        if total_depth <= 0:
            return 0
        
        usable_height = self.canvas_height - self.padding_top - self.padding_bottom
        return usable_height / total_depth
    
    def get_viewable_depth_range(self) -> Tuple[float, float]:
        """Get the depth range currently visible"""
        return (self.min_depth, self.max_depth)
    
    def get_usable_canvas_area(self) -> Tuple[float, float, float, float]:
        """Get (left, top, right, bottom) of usable drawing area"""
        left = self.padding_left
        top = self.padding_top
        right = self.canvas_width - self.padding_right
        bottom = self.canvas_height - self.padding_bottom
        return (left, top, right, bottom)
    
    def apply_zoom(self, zoom_level: float):
        """
        Apply zoom factor to scaling.
        Used when user zooms in/out.
        """
        self.zoom_level = zoom_level
```

---

## STATE MANAGEMENT SYSTEM (CONTINUED)

### 3. Integration Pattern: How Components Use State

**Pattern Example**: StratigraphicColumn subscribing to state changes

```python
class StratigraphicColumn(QWidget):
    def __init__(self, depth_state_manager, depth_coord_system):
        super().__init__()
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        # CRITICAL: Subscribe to ALL state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        self.state.zoomLevelChanged.connect(self.on_zoom_changed)
    
    def on_viewport_changed(self, depth_range):
        """Called when visible depth range changes"""
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.repaint()  # Re-render with new viewport
    
    def on_cursor_changed(self, depth):
        """Called when cursor depth changes"""
        self.repaint()  # Re-render to show cursor at new position
    
    def on_selection_changed(self, depth_range):
        """Called when selection changes"""
        self.repaint()  # Re-render to show selection highlight
    
    def on_zoom_changed(self, zoom_level):
        """Called when zoom changes"""
        self.coords.apply_zoom(zoom_level)
        self.repaint()
    
    def mousePressEvent(self, event):
        """User clicked on strat column"""
        screen_y = event.y()
        
        # Convert click to depth using SHARED coordinate system
        depth = self.coords.screen_y_to_depth(screen_y)
        
        # Find lithology at this depth
        interval = self.find_lithology_at_depth(depth)
        
        if interval:
            # Update CENTRAL state
            # This will trigger all other components to update
            self.state.set_selection_range(interval.from_depth, interval.to_depth)
            self.state.set_cursor_depth(depth)
```

---

## UI LAYOUT ARCHITECTURE

### 1 Point Desktop Layout Structure

Based on the manual and screenshots:

```
┌─────────────────────────────────────────────────────────────────┐
│ Menu Bar (File, Edit, View, Tools, Windows, Help)              │
├─────────────────────────────────────────────────────────────────┤
│ Toolbar (Layout buttons, zoom, etc)                             │
├─────────────────────────────────────────────────────────────────┤
│ Holes List │ ┌─────────────────────────────────────────────┐   │
│            │ │  MAIN GRAPHIC WINDOW (our focus)            │   │
│  AA0101    │ │  ┌────────────────────────────────────┐    │   │
│  AA0102    │ │  │ Preview        Header              │    │   │
│  AA0103    │ │  │ (88-98m)       Text                │    │   │
│  AA0104    │ │  ├────────────────────────────────────┤    │   │
│  AA0105    │ │  │ Strat Column │ LAS Curves │ Table │    │   │
│  AA0106    │ │  │              │            │       │    │   │
│  AA0107    │ │  │ Depth: 87-98m│ Gamma Ray  │       │    │   │
│  ...       │ │  │              │ Density    │ Depth │    │   │
│            │ │  │ [Colored      │ Caliper   │ Code  │    │   │
│            │ │  │  Rectangles]  │           │ Desc  │    │   │
│            │ │  │              │ [Curves]   │       │    │   │
│            │ │  │              │           │       │    │   │
│            │ │  └────────────────────────────────────┘    │   │
│            │ │  ┌────────────────────────────────────┐    │   │
│            │ │  │ Info Tab │ Core Photo │ Quality│  │    │   │
│            │ │  │ Display selected depth info     │  │    │   │
│            │ │  └────────────────────────────────────┘    │   │
│            │ └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

Layout Proportions (% of width):
- Holes List: 10%
- Strat Column: 12%
- LAS Curves: 55%
- Data Table: 23%
```

### PyQt6 Layout Implementation

**File**: `src/ui/graphic_window/unified_graphic_window.py` (Layout Section)

```python
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt

class UnifiedGraphicWindow(QMainWindow):
    """
    Main graphic window replicating 1 Point Desktop layout.
    This is the PRIMARY container for all graphic window components.
    """
    
    def __init__(self, hole_data_provider):
        super().__init__()
        self.setWindowTitle("Unified Graphic Window")
        self.setGeometry(100, 100, 1600, 900)
        
        self.data_provider = hole_data_provider
        
        # Initialize state managers
        min_depth, max_depth = hole_data_provider.get_depth_range()
        self.depth_state = DepthStateManager(min_depth, max_depth)
        self.depth_coords = DepthCoordinateSystem(
            canvas_height=600,
            canvas_width=1200
        )
        
        # Create main layout
        self.setup_ui()
    
    def setup_ui(self):
        """Create the main UI layout"""
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # ============ LEFT: Preview Window ============
        # Shows entire hole as miniature
        self.preview_window = PreviewWindow(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.preview_window.setMaximumWidth(150)
        main_layout.addWidget(self.preview_window)
        
        # ============ CENTER-RIGHT: Main Content Area ============
        # This uses a splitter for flexible resizing
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setStyleSheet("QSplitter::handle { background: #CCCCCC; width: 4px; }")
        
        # --- LEFT SECTION: Strat Column ---
        self.strat_column = StratigraphicColumn(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.strat_column.setMinimumWidth(100)
        main_splitter.addWidget(self.strat_column)
        
        # --- CENTER SECTION: LAS Curves ---
        self.las_curves = LASCurvesDisplay(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        self.las_curves.setMinimumWidth(400)
        main_splitter.addWidget(self.las_curves)
        
        # --- RIGHT SECTION: Data Table + Info ---
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (in percentages)
        main_splitter.setSizes([100, 550, 400])
        main_splitter.setCollapsible(0, False)
        main_splitter.setCollapsible(1, False)
        main_splitter.setCollapsible(2, False)
        
        main_layout.addWidget(main_splitter)
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with table and info tabs"""
        
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Upper: Data table
        self.lithology_table = LithologyDataTable(
            self.data_provider,
            self.depth_state,
            self.depth_coords
        )
        layout.addWidget(self.lithology_table, stretch=2)
        
        # Lower: Info tabs (Info, Core Photo, Quality, Validation)
        self.info_tabs = self.create_info_tabs()
        layout.addWidget(self.info_tabs, stretch=1)
        
        return panel
    
    def create_info_tabs(self) -> QTabWidget:
        """Create bottom tabbed information panel"""
        
        tabs = QTabWidget()
        
        # Tab 1: Info
        from .components.information_panel import InformationPanel
        info_panel = InformationPanel(self.depth_state, self.depth_coords)
        tabs.addTab(info_panel, "Info")
        
        # Tab 2: Core Photo (placeholder for now)
        core_photo_widget = QWidget()
        tabs.addTab(core_photo_widget, "Core Photo")
        
        # Tab 3: Quality (placeholder)
        quality_widget = QWidget()
        tabs.addTab(quality_widget, "Quality")
        
        # Tab 4: Validation (placeholder)
        validation_widget = QWidget()
        tabs.addTab(validation_widget, "Validation")
        
        return tabs
```

---

## COMPONENT IMPLEMENTATION GUIDE

### Component 1: Stratigraphic Column

**File**: `src/ui/graphic_window/components/stratigraphic_column.py`

This is a CRITICAL component. It must:
1. Render lithology rectangles using the shared coordinate system
2. Handle clicks to update selection
3. Respond to all state changes
4. Maintain perfect alignment (uses shared DepthCoordinateSystem)

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PyQt6.QtCore import Qt, QRect
from typing import Optional, List

class StratigraphicColumn(QWidget):
    """
    Left panel: Colored column showing lithology intervals.
    
    CRITICAL: Uses SHARED DepthCoordinateSystem to ensure alignment.
    All rectangles positioned using depth_to_screen_y().
    """
    
    def __init__(self, data_provider, depth_state_manager, depth_coord_system):
        super().__init__()
        
        self.data = data_provider
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMinimumWidth(120)
        self.setStyleSheet("background-color: white;")
        
        # Cache lithology data
        self.lithology_intervals = self.data.get_lithology_intervals()
        
        # Subscribe to state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.zoomLevelChanged.connect(self.on_zoom_changed)
        
        self.selected_range = None
        self.cursor_depth = None
    
    def on_viewport_changed(self, depth_range):
        """Viewport changed - update coordinate system and repaint"""
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()
    
    def on_selection_changed(self, depth_range):
        """Selection changed - store and repaint"""
        self.selected_range = depth_range
        self.update()
    
    def on_cursor_changed(self, depth):
        """Cursor changed - store and repaint"""
        self.cursor_depth = depth
        self.update()
    
    def on_zoom_changed(self, zoom_level):
        """Zoom changed - update coordinate system and repaint"""
        self.coords.apply_zoom(zoom_level)
        self.update()
    
    def paintEvent(self, event):
        """Render the stratigraphic column"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Get visible depth range from state
        min_depth, max_depth = self.coords.get_viewable_depth_range()
        
        # Draw each lithology interval
        for interval in self.lithology_intervals:
            # Skip if outside viewport
            if interval.to_depth < min_depth or interval.from_depth > max_depth:
                continue
            
            # Convert depths to screen coordinates using SHARED system
            screen_y1 = self.coords.depth_to_screen_y(interval.from_depth)
            screen_y2 = self.coords.depth_to_screen_y(interval.to_depth)
            
            # Clamp to visible area
            screen_y1 = max(screen_y1, 0)
            screen_y2 = min(screen_y2, self.height())
            
            height = screen_y2 - screen_y1
            if height <= 0:
                continue
            
            # Draw rectangle
            rect = QRect(10, int(screen_y1), self.width() - 20, int(height))
            color = QColor(*interval.color)
            painter.fillRect(rect, QBrush(color))
            
            # Draw border
            painter.drawRect(rect)
            
            # Draw pattern if applicable (hatch, dots, etc)
            if interval.pattern:
                self.draw_pattern(painter, rect, interval.pattern)
        
        # Draw selection highlight
        if self.selected_range:
            self.draw_selection(painter)
        
        # Draw cursor line
        if self.cursor_depth is not None:
            self.draw_cursor(painter)
        
        # Draw depth scale on left edge
        self.draw_depth_scale(painter)
    
    def draw_selection(self, painter: QPainter):
        """Draw highlight around selected interval"""
        screen_y1 = self.coords.depth_to_screen_y(self.selected_range.from_depth)
        screen_y2 = self.coords.depth_to_screen_y(self.selected_range.to_depth)
        
        rect = QRect(10, int(screen_y1), self.width() - 20, int(screen_y2 - screen_y1))
        
        painter.setPen(QPen(QColor(0, 0, 255), 3))
        painter.drawRect(rect)
    
    def draw_cursor(self, painter: QPainter):
        """Draw horizontal line at cursor depth"""
        screen_y = self.coords.depth_to_screen_y(self.cursor_depth)
        
        painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, int(screen_y), self.width(), int(screen_y))
    
    def draw_depth_scale(self, painter: QPainter):
        """Draw depth numbers on left edge"""
        min_depth, max_depth = self.coords.get_viewable_depth_range()
        
        # Draw every 1 meter
        step = 1.0
        depth = int(min_depth) + (1 if int(min_depth) < min_depth else 0)
        
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 8))
        
        while depth <= max_depth:
            screen_y = self.coords.depth_to_screen_y(depth)
            painter.drawText(0, int(screen_y) - 5, 8, 10, Qt.AlignmentFlag.AlignRight, str(depth))
            depth += step
    
    def draw_pattern(self, painter: QPainter, rect: QRect, pattern: str):
        """Draw lithology pattern (hatch, dots, etc)"""
        # Implement pattern rendering based on pattern name
        # This is optional but adds visual richness
        pass
    
    def mousePressEvent(self, event):
        """Handle click on strat column"""
        screen_y = event.y()
        
        # Convert click position to depth using SHARED coordinate system
        depth = self.coords.screen_y_to_depth(screen_y)
        
        # Find lithology interval at this depth
        interval = None
        for lit in self.lithology_intervals:
            if lit.contains_depth(depth):
                interval = lit
                break
        
        if interval:
            # Update CENTRAL state
            self.state.set_selection_range(interval.from_depth, interval.to_depth)
            self.state.set_cursor_depth(depth)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for scrolling"""
        # Scroll amount (positive = scroll down = deeper)
        scroll_delta = 0.5 if event.angleDelta().y() > 0 else -0.5
        
        self.state.scroll_viewport(scroll_delta)
```

### Component 2: LAS Curves Display

**File**: `src/ui/graphic_window/components/las_curves_display.py`

```python
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt
from typing import List, Optional, Dict

class LASCurvesDisplay(QWidget):
    """
    Center panel: LAS (Log ASCII Standard) curve visualization.
    Shows geophysical measurements (gamma ray, density, etc) as curves.
    
    CRITICAL: Must use SHARED DepthCoordinateSystem for vertical alignment.
    All depths positioned using depth_to_screen_y().
    """
    
    def __init__(self, data_provider, depth_state_manager, depth_coord_system):
        super().__init__()
        
        self.data = data_provider
        self.state = depth_state_manager
        self.coords = depth_coord_system
        
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: #f0f0f0;")
        
        # Load LAS data
        self.las_points = self.data.get_las_points()
        self.curve_names = self.data.get_available_curves()
        
        # Curve display settings
        self.displayed_curves = {
            'gamma': {'color': QColor(255, 0, 0), 'min': 0, 'max': 200},
            'density': {'color': QColor(0, 0, 255), 'min': 1.5, 'max': 2.5},
        }
        
        # Subscribe to state changes
        self.state.viewportRangeChanged.connect(self.on_viewport_changed)
        self.state.cursorDepthChanged.connect(self.on_cursor_changed)
        self.state.selectionRangeChanged.connect(self.on_selection_changed)
        
        self.selected_range = None
        self.cursor_depth = None
    
    def on_viewport_changed(self, depth_range):
        """Viewport changed - update and repaint"""
        self.coords.set_depth_range(depth_range.from_depth, depth_range.to_depth)
        self.update()
    
    def on_cursor_changed(self, depth):
        """Cursor changed - repaint to show new cursor line"""
        self.cursor_depth = depth
        self.update()
    
    def on_selection_changed(self, depth_range):
        """Selection changed - repaint to show selection box"""
        self.selected_range = depth_range
        self.update()
    
    def paintEvent(self, event):
        """Render LAS curves"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background
        painter.fillRect(self.rect(), QColor(240, 240, 240))
        
        min_depth, max_depth = self.coords.get_viewable_depth_range()
        
        # Filter visible points
        visible_points = [p for p in self.las_points 
                         if min_depth <= p.depth <= max_depth]
        
        # Draw each curve
        for curve_name, curve_config in self.displayed_curves.items():
            if curve_name not in self.curve_names:
                continue
            
            self.draw_curve(painter, visible_points, curve_name, curve_config)
        
        # Draw selection highlight
        if self.selected_range:
            self.draw_selection(painter)
        
        # Draw cursor line
        if self.cursor_depth is not None:
            self.draw_cursor(painter)
    
    def draw_curve(self, painter: QPainter, points: List, 
                   curve_name: str, config: Dict):
        """Draw a single curve"""
        if len(points) < 2:
            return
        
        color = config['color']
        min_value = config['min']
        max_value = config['max']
        
        painter.setPen(QPen(color, 2))
        
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        usable_width = right - left
        
        # Draw curve as connected line segments
        for i, point in enumerate(points):
            if point.depth < 0 or not point.has_curve(curve_name):
                continue
            
            # Convert depth to Y using SHARED coordinate system
            screen_y = self.coords.depth_to_screen_y(point.depth)
            
            # Convert curve value to X
            value = point.get_curve_value(curve_name, None)
            if value is None:
                continue
            
            # Normalize value to 0-1 range
            if max_value <= min_value:
                value_ratio = 0.5
            else:
                value_ratio = (value - min_value) / (max_value - min_value)
                value_ratio = max(0, min(1, value_ratio))  # Clamp
            
            screen_x = left + (value_ratio * usable_width)
            
            # Draw line to this point
            if i == 0:
                painter.drawPoint(int(screen_x), int(screen_y))
            else:
                # Get previous point
                prev = points[i - 1]
                prev_y = self.coords.depth_to_screen_y(prev.depth)
                prev_value = prev.get_curve_value(curve_name, None)
                if prev_value is not None:
                    prev_ratio = (prev_value - min_value) / (max_value - min_value)
                    prev_ratio = max(0, min(1, prev_ratio))
                    prev_x = left + (prev_ratio * usable_width)
                    painter.drawLine(int(prev_x), int(prev_y), int(screen_x), int(screen_y))
    
    def draw_selection(self, painter: QPainter):
        """Draw selection box"""
        screen_y1 = self.coords.depth_to_screen_y(self.selected_range.from_depth)
        screen_y2 = self.coords.depth_to_screen_y(self.selected_range.to_depth)
        
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        
        painter.setPen(QPen(QColor(0, 0, 255), 2))
        painter.drawRect(int(left), int(screen_y1), int(right - left), int(screen_y2 - screen_y1))
    
    def draw_cursor(self, painter: QPainter):
        """Draw horizontal cursor line"""
        screen_y = self.coords.depth_to_screen_y(self.cursor_depth)
        
        left, top, right, bottom = self.coords.get_usable_canvas_area()
        
        painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(left), int(screen_y), int(right), int(screen_y))
    
    def wheelEvent(self, event):
        """Handle mouse wheel"""
        scroll_delta = 0.5 if event.angleDelta().y() > 0 else -0.5
        self.state.scroll_viewport(scroll_delta)
```

(Continue with other components: PreviewWindow, LithologyDataTable, InformationPanel)

---

## INTEGRATION & SYNCHRONIZATION

### Synchronization Flow Diagram

```
Component Interaction Flow:

1. USER INTERACTION
   └─ Click/Scroll/Keyboard
      ↓
2. COMPONENT EVENT HANDLER
   └─ Component catches event
      ├─ Convert coordinates (click position → depth)
      ├─ Validate/Find related data
      └─ Update CENTRAL STATE
         ↓
3. DEPTH STATE MANAGER
   └─ Update internal state
   └─ Emit signal(s)
      ↓
4. SIGNAL BROADCASTS
   ├─ viewportRangeChanged
   ├─ cursorDepthChanged
   ├─ selectionRangeChanged
   ├─ zoomLevelChanged
   └─ ... etc
      ↓
5. ALL COMPONENTS RESPOND
   ├─ StratigraphicColumn.onStateChange()
   ├─ LASCurves.onStateChange()
   ├─ LithologyTable.onStateChange()
   ├─ PreviewWindow.onStateChange()
   └─ InformationPanel.onStateChange()
      ↓
6. EACH COMPONENT UPDATES
   ├─ Update coordinate system (set_depth_range)
   ├─ Recalculate visual elements
   └─ Re-render (paintEvent / update tables)
      ↓
7. RESULT: PERFECT SYNCHRONIZATION
   All components show same depth range
   All components use same coordinate system
   No misalignment possible!
```

---

## TESTING STRATEGY

### Unit Tests to Create

1. **test_depth_state_manager.py** - State transitions
2. **test_depth_coordinate_system.py** - Coordinate conversions
3. **test_lithology_data_model.py** - Data model validation
4. **test_component_synchronization.py** - Component signal handling
5. **test_alignment.py** - Verify pixel-perfect alignment

### Test Example: Coordinate System Alignment

**File**: `tests/test_alignment.py`

```python
import pytest
from src.ui.graphic_window.state import (
    DepthCoordinateSystem,
    DepthStateManager
)

def test_coordinate_consistency():
    """
    Test that coordinate conversions are consistent.
    This is CRITICAL to ensure alignment.
    """
    coord_sys = DepthCoordinateSystem(
        canvas_height=600,
        canvas_width=800
    )
    coord_sys.set_depth_range(87.0, 98.0)
    
    # Test round-trip conversion
    test_depths = [87.0, 87.5, 88.0, 90.0, 95.0, 98.0]
    
    for test_depth in test_depths:
        screen_y = coord_sys.depth_to_screen_y(test_depth)
        back_to_depth = coord_sys.screen_y_to_depth(screen_y)
        
        # Should be virtually identical (allow tiny floating point error)
        assert abs(back_to_depth - test_depth) < 0.001, \
            f"Round-trip failed for depth {test_depth}: got {back_to_depth}"

def test_multiple_components_same_coordinates():
    """
    Test that multiple components using same coordinate system
    produce identical positions.
    """
    coord_sys = DepthCoordinateSystem(600, 800)
    coord_sys.set_depth_range(87.0, 98.0)
    
    # Simulate two components getting position for same depth
    depth = 90.5
    
    position_1 = coord_sys.depth_to_screen_y(depth)
    position_2 = coord_sys.depth_to_screen_y(depth)
    
    assert position_1 == position_2, \
        "Same depth should produce identical screen position"

def test_pixel_height_calculation():
    """Test that depth thickness converts to correct pixel height"""
    coord_sys = DepthCoordinateSystem(600, 800)
    coord_sys.set_depth_range(87.0, 98.0)
    
    # 11 meters total depth, 560 pixels usable height (600 - 20 - 20)
    # So 1 meter = 560/11 ≈ 50.9 pixels
    
    thickness = 1.0
    pixel_height = coord_sys.depth_thickness_to_pixel_height(thickness)
    
    expected = 560 / 11.0
    assert abs(pixel_height - expected) < 0.1
```

---

## PERFORMANCE OPTIMIZATION

### Caching Strategy

1. **Lithology Data Caching**
   - Cache lithology intervals after loading
   - Invalidate only if data changes
   
2. **LAS Point Caching**
   - Cache LAS points after loading
   - Filter visible points in render loop only

3. **Render Optimization**
   - Don't repaint entire window on every state change
   - Use repaint() for full refresh only when necessary
   - Use update() for efficient partial updates

4. **Memory Optimization**
   - Don't store duplicate data in each component
   - Use data provider for single source
   - Clear selection/cursor data when not needed

### Rendering Performance Targets

- **60 FPS minimum**: Smooth scrolling/interaction
- **<100ms response time**: Instant user feedback
- **<200MB RAM**: For typical 10,000+ depth points
- **Support for 10,000+ LAS points**: Without performance degradation

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Core State Management ✓
- [ ] Create `DepthStateManager` class
- [ ] Create `DepthCoordinateSystem` class
- [ ] Create `DepthRange` dataclass
- [ ] Add comprehensive docstrings
- [ ] Create unit tests

### Phase 2: Data Models ✓
- [ ] Create `LithologyInterval` class
- [ ] Create `LASPoint` class
- [ ] Create `HoleDataProvider` interface
- [ ] Create `ExcelHoleDataProvider` implementation
- [ ] Add validation logic

### Phase 3: Core Components
- [ ] Create `StratigraphicColumn` component
  - [ ] Render rectangles for intervals
  - [ ] Handle click events
  - [ ] Subscribe to state changes
  - [ ] Draw depth scale
  - [ ] Draw selection highlight
  - [ ] Draw cursor line
- [ ] Create `LASCurvesDisplay` component
  - [ ] Render curve lines
  - [ ] Handle multiple curves
  - [ ] Subscribe to state changes
  - [ ] Draw selection highlight
  - [ ] Draw cursor line
- [ ] Create `LithologyDataTable` component
  - [ ] Display table of intervals
  - [ ] Handle row selection
  - [ ] Sync selection with state
- [ ] Create `PreviewWindow` component
  - [ ] Show full hole miniature
  - [ ] Handle click to navigate
- [ ] Create `InformationPanel` component
  - [ ] Display Info tab
  - [ ] Display selected interval data
  - [ ] Show LAS values at cursor depth

### Phase 4: Layout & Integration
- [ ] Create `UnifiedGraphicWindow` main container
- [ ] Implement splitter-based layout
- [ ] Wire components together
- [ ] Connect all state signals
- [ ] Add menu bar
- [ ] Add toolbar

### Phase 5: Synchronizers
- [ ] Create `ScrollSynchronizer`
- [ ] Create `SelectionSynchronizer`
- [ ] Create `DepthSynchronizer`
- [ ] Test all synchronization scenarios

### Phase 6: Testing
- [ ] Unit tests for state manager
- [ ] Unit tests for coordinate system
- [ ] Integration tests for components
- [ ] Alignment verification tests
- [ ] Performance benchmarking tests

### Phase 7: Polish & Optimization
- [ ] Style improvements (QSS)
- [ ] Performance optimization
- [ ] Memory profiling
- [ ] Bug fixes
- [ ] Documentation

---

## CODE STYLE & STANDARDS

### Python Standards

```python
# Naming
- Classes: PascalCase (StratigraphicColumn)
- Methods: snake_case (get_lithology_intervals)
- Constants: UPPER_CASE (DEFAULT_PADDING)
- Private: _name (self._cache)

# Type Hints (REQUIRED)
from typing import List, Optional, Tuple, Dict

def get_depth_range(self) -> Tuple[float, float]:
    """Always use type hints"""
    pass

# Docstrings (REQUIRED)
def depth_to_screen_y(self, depth: float) -> float:
    """
    Convert depth (meters) to screen Y coordinate (pixels).
    
    Args:
        depth: Depth in meters
        
    Returns:
        Screen Y coordinate in pixels
        
    Raises:
        ValueError: If depth is outside valid range
    """
    pass
```

### PyQt6 Standards

```python
# Always use full imports
from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPen

# Never use wildcard imports
# WRONG: from PyQt6.QtWidgets import *

# Connect signals properly
self.state.viewportRangeChanged.connect(self.on_viewport_changed)

# Clean up on exit
def closeEvent(self, event):
    """Clean up before window closes"""
    self.state.disconnect()
    super().closeEvent(event)
```

---

## CRITICAL NOTES FOR AI CODER

1. **Coordinate System is NOT Optional**: Every visualization MUST use the shared `DepthCoordinateSystem`. Do not create alternative coordinate systems.

2. **State is Source of Truth**: Do NOT cache coordinate/position information in components. Always derive from state using the coordinate system.

3. **Signals Must Be Connected**: Every component that subscribes to state changes must properly connect and disconnect signals. Test signal connections thoroughly.

4. **Test Alignment Continuously**: Create a simple test that verifies strat column and curves have matching vertical positions for the same depth. Run after each component implementation.

5. **Document Coordinate Conversions**: Any time you convert between depth and screen coordinates, add a comment explaining the calculation.

6. **Performance Monitoring**: Keep an eye on frame rate while implementing. Aim for 60 FPS minimum.

---

## NEXT STEPS

1. **Start with Phase 1**: Implement state managers first. These are the foundation.
2. **Then Phase 2**: Create data models to test state with real data.
3. **Then Phase 3**: Implement components one at a time, testing each thoroughly.
4. **Then Phase 4**: Integrate into main window and test synchronization.
5. **Then Phase 5-7**: Polish and optimize.

**Estimated Timeline**: 3-4 weeks with focused development.

**Key Success Metric**: When you can click on the strat column at 90m and the LAS curves highlight the same 90m point with ZERO pixel misalignment.
