# PROJECT: EARTHWORM BOREHOLE LOGGER
**Last Audited:** 2026-03-01 by Orchestrator (main session)
**Description:** Professional geological software for borehole data analysis, featuring a unified geological analysis viewport with pixel-perfect synchronization of LAS curves and stratigraphic column.

## Business Context
- **Industry:** Mining / Geoscience / Borehole Logging Software
- **Target Audience:** Geologists, drillers, and logging engineers (primarily Australian market)
- **Core Product:** Earthworm — a PyQt6 desktop application for borehole data visualisation and analysis
- **Brand Voice:** Professional, technical, concise, data-driven.
- **Key Differentiator:** Unified viewport with pixel-perfect depth synchronisation across LAS curve tracks and stratigraphic column.

## 🛠 Tech Stack (Audited 2026-03-01)
- **Primary Language:** Python 3
- **GUI Framework:** PyQt6 6.9.1
- **Plotting Engine:** PyQtGraph 0.13.7
- **Data Processing:** pandas 2.3.1, numpy 2.3.1
- **LAS File Parsing:** lasio 0.31
- **Excel I/O:** openpyxl 3.1.5
- **System Monitoring:** psutil 7.0.0
- **HTTP Client:** requests 2.32.4
- **Credentials:** keyring 25.6.0
- **Repository:** https://github.com/lukemoltbot/Earthworm_Moltbot.git

## 📂 Architecture Overview

### Entry Point
- `main.py` — Application entry point, configures logging and launches MainWindow

### `/src/core/` — Business Logic
- `config.py` — App configuration
- `data_processor.py` — Core data processing pipeline
- `data_stream_manager.py` — Real-time/streamed data management
- `memory_mapped_las.py` — Memory-efficient LAS file reading
- `session_manager.py` — Session persistence
- `settings_manager.py` — User settings
- `dictionary_manager.py` — CoalLog dictionary management
- `template_manager.py` — Excel template management
- `analyzer.py` — Data analysis utilities
- `api_client.py` — External API integration
- `validation.py` — Data validation
- `workers.py` — Background thread workers
- `coallog_utils.py` — CoalLog v3.1 utilities
- `/core/depth/` — Depth coordinate system, depth state manager, data structures
- `/core/graphic_models/` — Data providers (Excel, LAS point, lithology interval), hole data provider, sync cache

### `/src/ui/` — User Interface
- `main_window.py` — Main application window
- `context_menus.py`, `icon_loader.py`, `layout_presets.py`, `status_bar_enhancer.py`
- `/ui/graphic_window/` — Unified graphic window with:
  - `unified_graphic_window.py` — Main graphic container
  - `/components/` — Sub-components of the graphic window
  - `/state/` — Viewport and scroll state management
  - `/synchronizers/` — Scroll/zoom synchronisation engines
  - `/unified_viewport/` — Unified depth viewport system
- `/ui/widgets/` — 30+ specialised widgets including:
  - `enhanced_stratigraphic_column.py` — Lithology column with SVG patterns
  - `pyqtgraph_curve_plotter.py` — LAS curve rendering (gamma, density, resistivity, caliper)
  - `scroll_optimizer.py`, `scroll_optimization_integration.py` — High-performance scroll sync
  - `zoom_state_manager.py`, `scale_keyboard_controls.py` — Zoom/scale management
  - `curve_plotter.py`, `curve_display_modes.py`, `curve_visibility_manager.py`
  - `multi_attribute_widget.py`, `compact_range_widget.py`, `matrix_visualizer.py`
  - `cross_hole_sync_manager.py`, `cross_section_window.py`
  - `map_window.py`, `validation_panel.py`, `interactive_legend.py`
  - `svg_renderer.py`, `enhanced_pattern_preview.py`
- `/ui/dialogs/` — Application dialogs
- `/ui/models/` — Qt data models
- `/ui/styles/` — QSS stylesheets
- `/ui/resources/` — App resources

### `/src/assets/`
- CoalLog v3.1 dictionary spreadsheet, TEMPLATE.xlsx, litho JSON, icons, SVG patterns

### `/src/utils/`
- `range_analyzer.py` — Range analysis utilities

### `/tests/` — Test Suite
- Phase 3 integration & performance tests
- Pixel alignment tests
- Unified viewport integration tests
- Phase 5 workflow validation
- Qt test helpers (conftest.py, isolated_test_runner.py)

### Supporting Directories
- `/blueprints/` — Comprehensive development plan, quick reference guide
- `/docs/` — Architecture docs, API docs, user guide, migration guide, phase completion summaries
- `/research/` — CoalLog v3.1 research, Australian lithology geophysical data
- `/archive_layout_files/` — Deprecated layout manager system (archived)
- `/examples/` — Demo scripts for enhanced strat column and scroll optimisation
- `/logs/` — Runtime logs and test screenshots

## 🤖 Agent Roles & Model Tiers
1. **Orchestrator (Sonnet/Haiku):** The Manager. Plans tasks, reviews logic, routes work to specialised agents.
2. **Coder (Sonnet):** The Developer. Implements features, writes tests, fixes bugs in `/src`.
3. **Git-Ops (Haiku):** The Release Engineer. Handles all git operations.
4. **Debugger (Opus):** The Expert. Escalation for difficult logic errors or major refactoring.

## 📜 Operational Guardrails
- **Tiered Delegation:** Haiku for planning/status. Sonnet for code writing. Opus for escalations only.
- **Session Init:** Agents load `IDENTITY.md`, `SOUL.md`, and `CONTEXT.md` on startup only.
- **Code Access:** Never `cat` entire directories. Use `ls` first, read only what's needed.
- **Tracking:** Every successful code change logged in `HANDOFFS.md` before Git-Ops commits.

## 🚀 Git Strategy
- **Branching:** Features → `feat/` branches; fixes → `fix/` branches.
- **Commits:** Conventional Commits only (e.g., `feat: add unified viewport sync`).
- **Sync:** Git-Ops must pull latest from `origin` before every new task.

## 🔄 Current Development Status (as of 2026-03-01)
- **Phase 3:** COMPLETE ✅ — Unified depth sync, ScrollingSynchronizer, UnifiedDepthScaleManager
- **Phase 5/6:** COMPLETE ✅ — LAS curve rendering, fixed-scale tracks, stratigraphic column integration
- **Latest fixes:** LAS curve X-axis alignment (density/gamma tracks), stratigraphic column scale (10m view), auto-range padding disabled
- **In progress:** Manual testing of latest axis alignment and orientation fixes (commits up to `88125a5`)
