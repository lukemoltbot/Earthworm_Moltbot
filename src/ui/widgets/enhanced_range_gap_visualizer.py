"""
Enhanced Widget for visualizing gaps in lithology ranges with statistics panel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QToolTip, QTabWidget, QSplitter
)
from PyQt6.QtGui import QPainter, QBrush, QColor, QFont, QPen
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize

# Import existing components
from .range_gap_visualizer import RangeGapVisualizer
from .gap_statistics_panel import GapStatisticsPanel

class EnhancedRangeGapVisualizer(QWidget):
    """Enhanced widget that combines range visualization with statistics panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.range_analyzer = None
        self.gamma_covered = []
        self.gamma_gaps = []
        self.density_covered = []
        self.density_gaps = []
        self.lithology_rules = []

        self.gamma_range = (0, 300)  # GRDE range
        self.density_range = (0, 4)  # DENB range

        self.setup_ui()

    def setup_ui(self):
        """Setup the UI layout with splitter for visualization and statistics."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        title_label = QLabel("Enhanced Lithology Range Coverage Analysis")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)

        # Left panel: Range visualization
        self.range_visualizer = RangeGapVisualizer()
        self.range_visualizer.set_range_analyzer(None)  # We'll handle analysis ourselves
        self.splitter.addWidget(self.range_visualizer)

        # Right panel: Statistics
        self.statistics_panel = GapStatisticsPanel()
        self.splitter.addWidget(self.statistics_panel)

        # Set initial splitter proportions (70% visualization, 30% statistics)
        self.splitter.setStretchFactor(0, 6)
        self.splitter.setStretchFactor(1, 4)
        
        # Set minimum widths to prevent panels from becoming unusable
        self.range_visualizer.setMinimumWidth(400)
        self.statistics_panel.setMinimumWidth(250)
    def set_range_analyzer(self, analyzer):
        """Set the range analyzer instance"""
        self.range_analyzer = analyzer

    def update_ranges(self, gamma_covered, gamma_gaps, density_covered, density_gaps, use_overlaps=False, lithology_rules=None):
        """Update the visualization with new range data"""
        self.gamma_covered = gamma_covered
        self.density_covered = density_covered
        self.gamma_gaps = gamma_gaps
        self.density_gaps = density_gaps
        self.lithology_rules = lithology_rules or []

        # Update the range visualizer
        self.range_visualizer.update_ranges(gamma_covered, gamma_gaps, density_covered, density_gaps, use_overlaps, lithology_rules)

        # Update the statistics panel
        self.statistics_panel.update_statistics(gamma_gaps, density_gaps, self.gamma_range, self.density_range)

    def refresh_visualization(self):
        """Refresh the visualization with current data"""
        if self.range_analyzer and self.lithology_rules:
            gamma_covered, gamma_gaps = self.range_analyzer.analyze_gamma_ranges_with_overlaps(self.lithology_rules)
            density_covered, density_gaps = self.range_analyzer.analyze_density_ranges_with_overlaps(self.lithology_rules)
            self.update_ranges(gamma_covered, gamma_gaps, density_covered, density_gaps, use_overlaps=True, lithology_rules=self.lithology_rules)