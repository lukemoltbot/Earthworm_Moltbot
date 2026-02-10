"""
InteractiveLegend - An interactive legend widget for curve visibility control.
Provides click-to-toggle functionality and visual feedback.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint

class InteractiveLegend(QWidget):
    """An interactive legend widget for curve visibility control."""
    
    # Signal emitted when curve visibility changes
    curve_visibility_changed = pyqtSignal(str, bool)  # curve_name, visible
    legend_clicked = pyqtSignal(str)  # curve_name
    
    def __init__(self, parent=None, visibility_manager=None):
        super().__init__(parent)
        self.visibility_manager = visibility_manager
        
        # Legend items dictionary
        self.legend_items = {}
        
        # Setup UI
        self.setup_ui()
        
        # Set style
        self.setStyleSheet("""
            InteractiveLegend {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        
        # Connect to visibility manager if provided
        if self.visibility_manager:
            self.visibility_manager.visibility_changed.connect(self.on_visibility_changed)
    
    def setup_ui(self):
        """Setup the legend UI."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        self.main_layout.setSpacing(4)
        
        # Title
        title_label = QLabel("Curve Legend")
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #333;
                padding-bottom: 5px;
                border-bottom: 1px solid #ddd;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # Scroll area for legend items
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Container for legend items
        self.legend_container = QWidget()
        self.legend_layout = QVBoxLayout(self.legend_container)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_layout.setSpacing(2)
        
        self.scroll_area.setWidget(self.legend_container)
        self.main_layout.addWidget(self.scroll_area)
        
        # Group controls
        self.setup_group_controls()
    
    def setup_group_controls(self):
        """Setup group control buttons at the bottom."""
        group_frame = QFrame()
        group_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        group_layout = QHBoxLayout(group_frame)
        group_layout.setContentsMargins(5, 5, 5, 5)
        group_layout.setSpacing(5)
        
        # Show All Gamma button
        self.show_gamma_button = QPushButton("All Gamma")
        self.show_gamma_button.setStyleSheet("""
            QPushButton {
                background-color: #8b008b;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #a020f0;
            }
        """)
        self.show_gamma_button.setToolTip("Show/hide all gamma ray curves")
        self.show_gamma_button.clicked.connect(lambda: self.on_group_clicked('gamma'))
        group_layout.addWidget(self.show_gamma_button)
        
        # Show All Density button
        self.show_density_button = QPushButton("All Density")
        self.show_density_button.setStyleSheet("""
            QPushButton {
                background-color: #0000ff;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4169e1;
            }
        """)
        self.show_density_button.setToolTip("Show/hide all density curves")
        self.show_density_button.clicked.connect(lambda: self.on_group_clicked('density'))
        group_layout.addWidget(self.show_density_button)
        
        # Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                border: none;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #888;
            }
        """)
        self.reset_button.setToolTip("Reset all curves to default visibility")
        self.reset_button.clicked.connect(self.on_reset_clicked)
        group_layout.addWidget(self.reset_button)
        
        group_layout.addStretch()
        
        self.main_layout.addWidget(group_frame)
    
    def add_legend_item(self, curve_name: str, display_name: str, 
                       color: str, visible: bool = True):
        """
        Add an interactive legend item for a curve.
        
        Args:
            curve_name: Internal curve name
            display_name: User-friendly display name
            color: Curve color in hex format
            visible: Initial visibility state
        """
        # Create legend item widget
        legend_item = LegendItem(
            curve_name=curve_name,
            display_name=display_name,
            color=color,
            visible=visible,
            parent=self
        )
        
        # Connect signals
        legend_item.visibility_toggled.connect(self.on_item_visibility_toggled)
        legend_item.item_clicked.connect(self.on_item_clicked)
        
        # Add to layout
        self.legend_layout.addWidget(legend_item)
        
        # Store reference
        self.legend_items[curve_name] = legend_item
    
    def on_item_visibility_toggled(self, curve_name: str, visible: bool):
        """Handle legend item visibility toggle."""
        # Update visibility manager if available
        if self.visibility_manager:
            self.visibility_manager.set_curve_visibility(curve_name, visible)
        
        # Emit signal
        self.curve_visibility_changed.emit(curve_name, visible)
    
    def on_item_clicked(self, curve_name: str):
        """Handle legend item click (for selection/focus)."""
        self.legend_clicked.emit(curve_name)
    
    def on_group_clicked(self, group_name: str):
        """Handle group button click."""
        if not self.visibility_manager:
            return
        
        # Toggle group visibility
        self.visibility_manager.toggle_group(group_name)
    
    def on_reset_clicked(self):
        """Handle reset button click."""
        if not self.visibility_manager:
            return
        
        # Reset to defaults
        self.visibility_manager.reset_to_defaults()
    
    def on_visibility_changed(self, curve_name: str, visible: bool):
        """Update legend item when visibility changes externally."""
        if curve_name in self.legend_items:
            self.legend_items[curve_name].set_visible(visible)
    
    def update_from_visibility_manager(self):
        """Update legend items from visibility manager."""
        if not self.visibility_manager:
            return
        
        # Clear existing items
        self.clear_legend_items()
        
        # Add items for each curve in the manager
        for curve_name, metadata in self.visibility_manager.curve_metadata.items():
            display_name = metadata.get('display_name', curve_name)
            color = metadata.get('color', '#666666')
            visible = metadata.get('visible', True)
            
            self.add_legend_item(curve_name, display_name, color, visible)
    
    def clear_legend_items(self):
        """Clear all legend items."""
        # Remove all items from layout
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear dictionary
        self.legend_items.clear()
    
    def register_curves_from_manager(self):
        """Register curves from visibility manager."""
        self.update_from_visibility_manager()


class LegendItem(QWidget):
    """A single interactive legend item."""
    
    # Signals
    visibility_toggled = pyqtSignal(str, bool)  # curve_name, visible
    item_clicked = pyqtSignal(str)  # curve_name
    
    def __init__(self, curve_name: str, display_name: str, 
                 color: str, visible: bool = True, parent=None):
        super().__init__(parent)
        self.curve_name = curve_name
        self.display_name = display_name
        self.color = QColor(color)
        self.visible = visible
        self.hovered = False
        self.selected = False
        
        # Setup UI
        self.setup_ui()
        
        # Set mouse tracking
        self.setMouseTracking(True)
        
        # Set fixed height
        self.setFixedHeight(28)
        
        # Set style
        self.update_style()
    
    def setup_ui(self):
        """Setup the legend item UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Color indicator
        self.color_indicator = ColorIndicator(self.color, self.visible, self)
        layout.addWidget(self.color_indicator)
        
        # Display name label
        self.name_label = QLabel(self.display_name)
        self.name_label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.name_label)
        
        layout.addStretch()
        
        # Visibility indicator (eye icon)
        self.visibility_label = QLabel("👁️" if self.visible else "🚫")
        self.visibility_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                padding: 0 5px;
            }
        """)
        layout.addWidget(self.visibility_label)
    
    def update_style(self):
        """Update widget style based on state."""
        if self.selected:
            style = """
                LegendItem {
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                    border-radius: 3px;
                }
            """
        elif self.hovered:
            style = """
                LegendItem {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                }
            """
        else:
            style = """
                LegendItem {
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 3px;
                }
            """
        
        self.setStyleSheet(style)
        
        # Update visibility indicator
        if self.visible:
            self.visibility_label.setText("👁️")
            self.visibility_label.setToolTip("Visible - click to hide")
        else:
            self.visibility_label.setText("🚫")
            self.visibility_label.setToolTip("Hidden - click to show")
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Toggle visibility on click
            self.toggle_visibility()
            event.accept()
        
        # Emit click signal
        self.item_clicked.emit(self.curve_name)
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move events for hover effect."""
        self.hovered = True
        self.update_style()
        super().mouseMoveEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events."""
        self.hovered = False
        self.update_style()
        super().leaveEvent(event)
    
    def toggle_visibility(self):
        """Toggle curve visibility."""
        self.visible = not self.visible
        self.color_indicator.set_visible(self.visible)
        self.update_style()
        
        # Emit signal
        self.visibility_toggled.emit(self.curve_name, self.visible)
    
    def set_visible(self, visible: bool):
        """Set visibility state."""
        if self.visible != visible:
            self.visible = visible
            self.color_indicator.set_visible(visible)
            self.update_style()
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        if self.selected != selected:
            self.selected = selected
            self.update_style()


class ColorIndicator(QWidget):
    """A colored indicator widget with visibility state."""
    
    def __init__(self, color: QColor, visible: bool = True, parent=None):
        super().__init__(parent)
        self.color = color
        self.visible = visible
        self.setFixedSize(16, 16)
    
    def paintEvent(self, event):
        """Paint the color indicator."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw colored circle
        if self.visible:
            painter.setBrush(QBrush(self.color))
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
        else:
            # Draw with diagonal line for hidden state
            painter.setBrush(QBrush(QColor(200, 200, 200)))
            painter.setPen(QPen(QColor(150, 150, 150), 1))
        
        painter.drawEllipse(1, 1, 14, 14)
        
        # Draw diagonal line if hidden
        if not self.visible:
            painter.setPen(QPen(QColor(100, 100, 100), 2))
            painter.drawLine(3, 3, 13, 13)
    
    def set_visible(self, visible: bool):
        """Set visibility state."""
        if self.visible != visible:
            self.visible = visible
            self.update()