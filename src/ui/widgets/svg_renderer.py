import os
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QPainter, QColor

class SvgRenderer:
    def __init__(self):
        self.renderer_cache = {}

    def get_renderer(self, svg_path):
        if not svg_path:
            return None
        if svg_path not in self.renderer_cache:
            if os.path.exists(svg_path):
                self.renderer_cache[svg_path] = QSvgRenderer(svg_path)
            else:
                return None
        return self.renderer_cache.get(svg_path)

    def render_svg(self, svg_path, width, height, background_color):
        if not svg_path:
            # print(f"DEBUG (SvgRenderer): No SVG path provided, returning None")
            return None
            
        renderer = self.get_renderer(svg_path)
        if not renderer or not renderer.isValid():
            # print(f"DEBUG (SvgRenderer): SVG renderer invalid or not found for path: {svg_path}")
            return None

        # print(f"DEBUG (SvgRenderer): Rendering SVG {svg_path} at {width}x{height} with background {background_color.name()}")
        pixmap = QPixmap(width, height)
        if pixmap.isNull():
            # print(f"DEBUG (SvgRenderer): Failed to create pixmap of size {width}x{height}")
            return None
        pixmap.fill(background_color)
        
        painter = QPainter()
        # Explicitly begin painting and check if it was successful
        if painter.begin(pixmap):
            try:
                renderer.render(painter)
                # print(f"DEBUG (SvgRenderer): Successfully rendered SVG")
            except Exception as e:
                pass
            finally:
                painter.end() # Ensure painter is ended even if render fails
        else:
            # print(f"DEBUG (SvgRenderer): Failed to begin painting")
            pass
        
        # print(f"DEBUG (SvgRenderer): Returning pixmap, isNull={pixmap.isNull()}, size={pixmap.size().width()}x{pixmap.size().height()}")
        return pixmap
