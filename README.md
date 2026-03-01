# 🪱 Earthworm Borehole Logger

> Professional geological software for borehole data analysis and visualisation.

Earthworm is a PyQt6 desktop application designed for geologists, drillers, and logging engineers. It provides a unified geological analysis viewport with pixel-perfect synchronisation of LAS geophysical curves and stratigraphic column data.

---

## ✨ Features

- **Unified Viewport** — Depth-synchronised display of LAS curves + stratigraphic column
- **LAS Curve Rendering** — Gamma, density, resistivity, and caliper tracks with fixed well-log scales
- **Stratigraphic Column** — SVG-patterned lithology intervals with CoalLog v3.1 dictionary support
- **Scroll & Zoom Sync** — Pixel-perfect synchronisation across all panes
- **Cross-Section View** — Multi-hole comparison window
- **Map View** — Spatial hole location display
- **Excel Integration** — Import/export via CoalLog v3.1 template format
- **Session Persistence** — Save and restore your workspace

---

## 🛠 Tech Stack

| Component | Library |
|-----------|---------|
| GUI Framework | PyQt6 6.9+ |
| Plotting Engine | PyQtGraph 0.13+ |
| Data Processing | pandas, numpy |
| LAS File I/O | lasio |
| Excel I/O | openpyxl |
| System Monitoring | psutil |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/lukemoltbot/Earthworm_Moltbot.git
cd Earthworm_Moltbot

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
python main.py
```

---

## 📂 Project Structure

```
Earthworm_Moltbot/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── src/
│   ├── core/                # Business logic, data processing, LAS parsing
│   │   ├── depth/           # Depth coordinate system
│   │   └── graphic_models/  # Data providers and models
│   ├── ui/
│   │   ├── main_window.py   # Main application window
│   │   ├── graphic_window/  # Unified graphic viewport system
│   │   │   ├── components/
│   │   │   ├── state/
│   │   │   ├── synchronizers/
│   │   │   └── unified_viewport/
│   │   ├── widgets/         # 30+ specialised UI components
│   │   ├── dialogs/
│   │   ├── models/
│   │   └── styles/
│   ├── assets/              # Icons, SVG patterns, CoalLog dictionaries
│   └── utils/               # Utility modules
├── tests/                   # Test suite
├── docs/                    # Architecture and API documentation
├── blueprints/              # Development plans
├── research/                # Geophysical research data (CoalLog, Australian lithology)
└── examples/                # Demo scripts
```

---

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run a specific test file
python -m pytest tests/test_phase3_integration.py -v
```

> **Note:** Qt-dependent tests require a display. Use `examples/` scripts for visual demos.

---

## 📚 Documentation

- [`docs/current_architecture.md`](docs/current_architecture.md) — System architecture overview
- [`docs/Unified_Viewport_API.md`](docs/Unified_Viewport_API.md) — Viewport synchronisation API
- [`docs/LAS_CURVE_PANE_ARCHITECTURE.md`](docs/LAS_CURVE_PANE_ARCHITECTURE.md) — LAS curve rendering design
- [`docs/User_Guide.md`](docs/User_Guide.md) — End-user guide
- [`docs/Migration_Guide.md`](docs/Migration_Guide.md) — Migration notes

---

## 🤝 Development

This project uses a multi-agent autonomous development pipeline:

- **Orchestrator** — Planning and task routing
- **Coder** — Feature implementation and bug fixes
- **Git-Ops** — Branch management and releases
- **Debugger** — Complex refactoring and escalations

All development follows [Conventional Commits](https://www.conventionalcommits.org/).

---

## 📄 License

Private repository. All rights reserved.
