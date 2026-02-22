#!/usr/bin/env python3
"""
Earthworm Borehole Logger - Main Entry Point

Professional geological software for borehole data analysis,
featuring unified geological analysis viewport with pixel-perfect
synchronization of LAS curves and stratigraphic column.
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
src_dir = project_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from PyQt6.QtWidgets import QApplication, QStyleFactory
    from src.ui.main_window import MainWindow
except ImportError as e:
    print(f"Import error: {e}")
    print("\nPlease install required dependencies:")
    print("  pip install PyQt6 PyQtGraph pandas numpy lasio")
    sys.exit(1)


def configure_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('earthworm.log')
        ]
    )
    
    # Reduce logging noise from some libraries
    logging.getLogger('PyQt6').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def main():
    """Main application entry point."""
    logger = configure_logging()
    logger.info("Starting Earthworm Borehole Logger")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Earthworm Borehole Logger")
    app.setApplicationVersion("1.0.0")
    
    # Set modern style if available
    if "Fusion" in QStyleFactory.keys():
        app.setStyle("Fusion")
        logger.debug("Set Fusion style")
    
    try:
        # Create and show main window
        logger.info("Creating main window...")
        window = MainWindow()
        window.setWindowTitle("Earthworm Borehole Logger - Unified Geological Analysis Viewport")
        window.show()
        
        logger.info("Application started successfully")
        logger.info("Unified viewport features:")
        logger.info("  - Pixel-perfect synchronization (≤1 pixel drift)")
        logger.info("  - Side-by-side layout (68% curves, 32% column)")
        logger.info("  - Professional geological aesthetics")
        logger.info("  - 322.9 FPS performance target")
        
        # Start event loop
        return_code = app.exec()
        logger.info(f"Application exiting with code: {return_code}")
        return return_code
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n⚠️  Fatal error: {e}")
        print("Check earthworm.log for details.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)