"""
Pytest configuration for Earthworm tests.
Sets up test environment and fixtures.
"""

import pytest
import os
import sys
from pathlib import Path

# Set headless for all tests
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

@pytest.fixture(scope="session")
def project_root_path():
    """Return project root path."""
    return project_root

@pytest.fixture(scope="session")
def test_data_dir():
    """Return test data directory."""
    return project_root / "tests" / "test_data"

@pytest.fixture(scope="session")
def visual_baseline_dir():
    """Return visual baseline directory."""
    return project_root / "tests" / "visual_baselines"

@pytest.fixture(scope="session")
def benchmarks_dir():
    """Return benchmarks directory."""
    return project_root / "benchmarks"

@pytest.fixture(scope="session")
def headless_app():
    """Create headless QApplication for testing (session-scoped)."""
    from PyQt6.QtWidgets import QApplication
    
    # Check if app already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Store original top-level widgets
    from PyQt6.QtWidgets import QWidget
    original_widgets = QApplication.topLevelWidgets().copy()
    
    yield app
    
    # Cleanup: close any new top-level widgets created during tests
    for widget in QApplication.topLevelWidgets():
        if widget not in original_widgets:
            try:
                widget.close()
                widget.deleteLater()
            except:
                pass
    
    # Process events to allow cleanup
    if hasattr(app, 'processEvents'):
        app.processEvents()

@pytest.fixture(autouse=True)
def cleanup_qt_objects(headless_app):
    """Cleanup Qt objects after each test (autouse)."""
    from PyQt6.QtWidgets import QApplication
    
    yield
    
    # Close any top-level widgets that might have been created
    for widget in QApplication.topLevelWidgets():
        try:
            widget.close()
            widget.deleteLater()
        except:
            pass
    
    # Process events to allow cleanup
    headless_app.processEvents()

@pytest.fixture
def empty_main_window(headless_app):
    """Create empty main window for testing."""
    from src.ui.main_window import MainWindow
    window = MainWindow()
    yield window
    window.close()

@pytest.fixture
def test_dataset():
    """Create synthetic test dataset."""
    import pandas as pd
    import numpy as np
    
    depth = np.arange(0, 100.1, 0.1)  # 0-100m at 0.1m intervals
    data = {
        'DEPT': depth,
        'gamma': 50 + np.sin(depth * 0.1) * 20,
        'short_space_density': 2.0 + np.cos(depth * 0.05) * 0.5,
        'long_space_density': 2.0 + np.cos(depth * 0.05) * 0.5,
        'caliper': 150 + np.sin(depth * 0.03) * 50,
    }
    return pd.DataFrame(data)

@pytest.fixture
def curve_configs():
    """Create standard curve configurations."""
    from src.core.config import CURVE_RANGES
    
    configs = []
    for curve_name in ['gamma', 'short_space_density', 'long_space_density', 'caliper']:
        configs.append({
            'name': curve_name,
            'min': CURVE_RANGES.get(curve_name, {}).get('min', 0),
            'max': CURVE_RANGES.get(curve_name, {}).get('max', 100),
            'color': CURVE_RANGES.get(curve_name, {}).get('color', '#000000'),
            'inverted': False,
            'thickness': 1.5
        })
    
    return configs

# Markers for different test types
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "visual: mark test as visual regression test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# Skip visual tests in headless environment
def pytest_collection_modifyitems(config, items):
    """Skip visual tests in headless environment."""
    skip_visual = pytest.mark.skip(reason="Visual tests require non-headless environment")
    
    for item in items:
        if "visual" in item.keywords:
            item.add_marker(skip_visual)