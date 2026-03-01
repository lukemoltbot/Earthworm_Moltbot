# REFERENCE_SUMMARY: 1point Desktop Architecture

**Source:** `blueprints/1point.desktop.manual.md` | **Target:** Coal borehole logging suite | **Type:** Professional GIS-integrated data mgmt

---

## 🎯 Core Features (Top 10)

| # | Feature | Pattern | Tech Stack |
|---|---------|---------|-----------|
| 1 | **Multi-window UI** | MDI (Multiple Document Interface) | .NET WinForms + separate viewports (Graphic Log, Map, Table, Section) |
| 2 | **Graphic Log Viewer** | Depth-synchronized visualization + scroll-sync | Bitmap rendering + real-time depth correction |
| 3 | **LAS Curve Rendering** | Customizable well-log tracks (gamma, density, resistivity) | Load + parse LAS files; curve normalization & scaling |
| 4 | **Map Window (GIS)** | Spatial hole visualization + polygon select + layer system | DotSpatial (MIT) + SHP/DXF/KML overlay support |
| 5 | **Cross-Section (Fence)** | 2D profile generation with hole correlation | Mouse-driven object placement + depth interpolation |
| 6 | **Lithology Depth System** | Interval-based strata with CoalLog v3.1 qualifier validation | Thickness calc + auto-correction + boundary snapping |
| 7 | **Configuration Wizard** | Settings import/export (.csv/.xml/.wizard) + remote dictionary sync | Centralized config mgmt + auto-update mechanism |
| 8 | **Data Validation Engine** | Rule-based validation (lithology, coal quality, depth consistency) | Dictionary-driven constraints + error flagging |
| 9 | **Export/Reporting System** | Bulk report generation (English logs, graphic logs, PDF/SVG/KML/MapInfo) | Template-based rendering + batch processing |
| 10 | **Database Integration** | GeoCore abstraction layer + multi-database support (custom/built-in) | ODBC + SQL queries + data sync protocols |

---

## 🏗️ Architectural Patterns

### A. **Window Management**
- MDI pattern: Parent container → child windows (Graphic, Map, Table, Section)
- Synchronized state across windows (depth selection, hole filter, display opts)
- Context menus + right-click operations for mode switching

### B. **Data Pipeline**
1. **Load** → Parse (LAS, CoalLog, Excel, DBF, Vulcan)
2. **Transform** → Validation + dictionary lookup + depth correction
3. **Render** → Display in appropriate window (plot, table, map, cross-section)
4. **Export** → PDF/SVG/KML/MapInfo/custom formats

### C. **Depth Coordinate System**
- Absolute depth + relative depth + elevation modes
- Correction offsets (roof/floor, manual adjustments, LAS offset)
- Continuous synchronization across all viewports

### D. **Configuration Pattern**
- Hierarchical settings (General → Folders → Files → LAS → Database)
- Settings wizard files (.wizard) for org-wide deployment
- Remote dictionary sync from network/web server
- Per-user + per-organization customization

### E. **Dictionary-Driven Design**
- CoalLog v3.1 standard as validation source
- Lithology qualifiers (coal brightness, sandstone grain size)
- Custom dictionaries + auto-update mechanism
- Coding enforcement optional

### F. **Validation Framework**
- Rules engine: Header validation, lithology depth/thickness, coal quality limits
- ASH/KL percentage checks, seam name uniqueness, zero-thickness flagging
- Optional constraints + user-defined limits

### G. **Plugin/Extension System**
- MapInfo interop (conditional on installed MapInfo)
- Custom import/export handlers
- Analysis procedures (composites, sample tracking)
- Photo management tools (core photo rename/resize)

### H. **Performance Optimization**
- Lazy-load LAS headers (skip data until curves needed)
- Partial/quick load modes (subset of holes)
- Display toggle for expensive features (high-res photos, curve density)
- Cached viewport + incremental rendering

### I. **Licensing Model**
- Token-based subscription (annual/quarterly/monthly)
- 30-day trial + grace period (read-only fallback)
- Per-user licenses with flexible transfer

### J. **UI/Display Abstraction**
- Layout presets (multiple predefined arrangements)
- Display mode switching (vertical/horizontal scale, aspect ratio, depth modes)
- Custom headers + label templates
- Print-to-PDF/SVG with layout preservation

---

## 📊 Technology Stack (Dependencies)

- **.NET Framework 4.0+** (runtime)
- **DotSpatial (MIT)** — GIS operations, spatial queries
- **GemBox.Spreadsheet** — Excel read/write
- **netDxf (LGPL)** — DXF file parsing
- **PdfSharp (MIT)** — PDF generation
- **Svg (Ms-PL)** — SVG rendering
- **FastDBF (BSD)** — DBF format support
- **Interop.MapInfo** — Optional GIS integration
- **WebEye + wContour** — Camera + contour rendering

---

## 🔗 Earthworm Alignment

**Borrowed from 1PD:**
✅ Graphic Log window (depth-sync viewport) → `src/ui/graphic_window/` + `UnifiedDepthScaleManager`
✅ LAS curve rendering (fixed-scale tracks) → `src/ui/widgets/pyqtgraph_curve_plotter.py`
✅ Stratigraphic column (lithology + SVG patterns) → `src/ui/widgets/enhanced_stratigraphic_column.py`
✅ Scroll synchronization (unified viewport) → `src/ui/graphic_window/synchronizers/`
✅ Configuration management → `.openclaw/CONTEXT.md` + `src/core/settings_manager.py`

**Divergence from 1PD:**
❌ No MapInfo (focus: PyQt + PyQtGraph instead of .NET WinForms)
❌ No legacy format support (CoalLog v3.1 target only, not TM2008)
❌ No database backend (file-based + in-memory data streams)

---

**Token Count: 742** | **Compression Ratio: 3.8:1 (source→summary)**
