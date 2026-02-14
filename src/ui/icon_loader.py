"""
Icon Loader - Loads SVG icons directly from files without Qt resource system.
Provides a fallback when resource compiler is not available.
"""

import os
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer

class IconLoader:
    """Loads icons from SVG files in the resources directory."""
    
    # Cache for loaded icons
    _icon_cache = {}
    
    # Base path for icons
    _base_path = os.path.join(os.path.dirname(__file__), 'resources', 'icons')
    
    @classmethod
    def get_icon(cls, icon_name):
        """
        Get an icon by name.
        
        Args:
            icon_name: Name of the icon file (e.g., 'add.svg', 'settings.svg')
            
        Returns:
            QIcon object or empty QIcon if not found
        """
        # Check cache first
        if icon_name in cls._icon_cache:
            return cls._icon_cache[icon_name]
        
        # Construct full path
        icon_path = os.path.join(cls._base_path, icon_name)
        
        # Check if file exists
        if not os.path.exists(icon_path):
            print(f"Warning: Icon not found: {icon_path}")
            # Return empty icon
            icon = QIcon()
            cls._icon_cache[icon_name] = icon
            return icon
        
        # Load SVG and create icon
        try:
            # Read SVG file
            with open(icon_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            
            # Create SVG renderer
            renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
            
            if renderer.isValid():
                # Create pixmaps at different sizes for the icon
                icon = QIcon()
                
                # Create pixmaps at common sizes
                sizes = [(16, 16), (24, 24), (32, 32), (48, 48)]
                
                for width, height in sizes:
                    pixmap = QPixmap(width, height)
                    pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background
                    
                    # Create painter and render SVG
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    
                    # Add pixmap to icon
                    icon.addPixmap(pixmap)
                
                # Cache the icon
                cls._icon_cache[icon_name] = icon
                return icon
            else:
                print(f"Warning: Invalid SVG file: {icon_path}")
                icon = QIcon()
                cls._icon_cache[icon_name] = icon
                return icon
                
        except Exception as e:
            print(f"Error loading icon {icon_name}: {e}")
            icon = QIcon()
            cls._icon_cache[icon_name] = icon
            return icon
    
    @classmethod
    def get_icon_by_theme(cls, theme_name, fallback_icon_name):
        """
        Get icon by theme name with fallback.
        
        Args:
            theme_name: Qt theme icon name (e.g., 'document-open')
            fallback_icon_name: Fallback icon file name
            
        Returns:
            QIcon object
        """
        # Skip Qt theme icons to avoid resource path fallback errors
        # Always use our SVG icons
        return cls.get_icon(fallback_icon_name)

# Convenience functions for common icons
def get_add_icon():
    """Get 'add' icon for Create Interbedding."""
    return IconLoader.get_icon_by_theme('list-add', 'add.svg')

def get_save_icon():
    """Get 'save' icon for Export CSV."""
    return IconLoader.get_icon_by_theme('document-save', 'save.svg')

def get_open_icon():
    """Get 'open' icon for Load LAS File."""
    return IconLoader.get_icon_by_theme('document-open', 'open.svg')

def get_settings_icon():
    """Get 'settings' icon."""
    return IconLoader.get_icon_by_theme('preferences-system', 'settings.svg')

def get_folder_icon():
    """Get 'folder' icon for File Explorer."""
    return IconLoader.get_icon_by_theme('folder', 'folder.svg')

def get_chart_icon():
    """Get 'chart' icon for LAS Curves."""
    return IconLoader.get_icon_by_theme('chart-line', 'chart.svg')

def get_layers_icon():
    """Get 'layers' icon for Enhanced Stratigraphic."""
    return IconLoader.get_icon_by_theme('layers', 'layers.svg')

def get_table_icon():
    """Get 'table' icon for Data Editor."""
    return IconLoader.get_icon_by_theme('table', 'table.svg')

def get_overview_icon():
    """Get 'overview' icon for Overview Stratigraphic."""
    return IconLoader.get_icon_by_theme('overview', 'overview.svg')