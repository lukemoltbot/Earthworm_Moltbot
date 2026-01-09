"""
Gap Statistics Panel for displaying quantitative gap analysis.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class GapStatisticsPanel(QWidget):
    """Panel displaying quantitative statistics about gaps in lithology ranges."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup the statistics panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # Header
        header_label = QLabel("Gap Analysis Statistics")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        layout.addWidget(header_label)

        # Create scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(200)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(3)

        scroll_area.setWidget(self.content_widget)
        layout.addWidget(scroll_area)

        # Initialize with default message
        self.update_statistics(None, None, None, None)

    def update_statistics(self, gamma_gaps, density_gaps, gamma_range, density_range):
        """Update the statistics display with new gap data."""
        # Clear existing content
        self._clear_layout(self.content_layout)

        if gamma_gaps is None or density_gaps is None:
            # Show default message
            default_label = QLabel("No gap analysis available.\nModify lithology ranges to see statistics.")
            default_label.setStyleSheet("color: #666; font-style: italic; padding: 10px;")
            default_label.setWordWrap(True)
            self.content_layout.addWidget(default_label)
            return

        # Calculate statistics
        gamma_stats = self._calculate_gap_statistics(gamma_gaps, gamma_range, "Gamma")
        density_stats = self._calculate_gap_statistics(density_gaps, density_range, "Density")

        # Create statistics sections
        self._add_statistics_section("Gamma Ray Gaps", gamma_stats, "#2E86AB")
        self._add_statistics_section("Density Gaps", density_stats, "#A23B72")

        # Add combined analysis
        combined_stats = self._calculate_combined_statistics(gamma_gaps, density_gaps, gamma_range, density_range)
        self._add_statistics_section("Combined Analysis", combined_stats, "#F18F01")

        # Add stretch to push content up
        self.content_layout.addStretch()

    def _calculate_gap_statistics(self, gaps, value_range, name):
        """Calculate statistics for a single parameter type."""
        if not gaps:
            return {
                'status': 'Good',
                'status_color': '#4CAF50',
                'coverage': '100%',
                'gap_count': 0,
                'total_gap_size': 0.0,
                'avg_gap_size': 0.0,
                'largest_gap': 0.0,
                'message': f'No gaps in {name.lower()} ranges'
            }

        total_range = value_range[1] - value_range[0]
        total_gap_size = sum(gap[1] - gap[0] for gap in gaps)
        coverage_percentage = ((total_range - total_gap_size) / total_range) * 100

        # Determine status based on coverage
        if coverage_percentage >= 95:
            status = 'Good'
            status_color = '#4CAF50'
        elif coverage_percentage >= 85:
            status = 'Fair'
            status_color = '#FF9800'
        else:
            status = 'Poor'
            status_color = '#F44336'

        return {
            'status': status,
            'status_color': status_color,
            'coverage': f'{coverage_percentage:.1f}%',
            'gap_count': len(gaps),
            'total_gap_size': total_gap_size,
            'avg_gap_size': total_gap_size / len(gaps) if gaps else 0,
            'largest_gap': max((gap[1] - gap[0] for gap in gaps), default=0),
            'message': f'{len(gaps)} gaps covering {total_gap_size:.2f} units'
        }

    def _calculate_combined_statistics(self, gamma_gaps, density_gaps, gamma_range, density_range):
        """Calculate combined statistics for both parameters."""
        gamma_gap_count = len(gamma_gaps) if gamma_gaps else 0
        density_gap_count = len(density_gaps) if density_gaps else 0
        total_gaps = gamma_gap_count + density_gap_count

        # Estimate potential NL classifications
        # This is a rough estimate - actual NL depends on data distribution
        nl_estimate = "Unknown"
        if total_gaps == 0:
            nl_estimate = "0% (no gaps)"
            status = 'Excellent'
            status_color = '#4CAF50'
        elif total_gaps <= 2:
            nl_estimate = "<5% (minimal gaps)"
            status = 'Good'
            status_color = '#8BC34A'
        elif total_gaps <= 4:
            nl_estimate = "5-15% (moderate gaps)"
            status = 'Fair'
            status_color = '#FF9800'
        else:
            nl_estimate = ">15% (significant gaps)"
            status = 'Poor'
            status_color = '#F44336'

        return {
            'status': status,
            'status_color': status_color,
            'coverage': 'Combined',
            'gap_count': total_gaps,
            'total_gap_size': 'N/A',
            'avg_gap_size': 'N/A',
            'largest_gap': 'N/A',
            'message': f'Estimated NL classifications: {nl_estimate}'
        }

    def _add_statistics_section(self, title, stats, color):
        """Add a statistics section to the layout."""
        # Section header
        section_frame = QFrame()
        section_frame.setFrameStyle(QFrame.Shape.Box)
        section_frame.setStyleSheet(f"border-left: 4px solid {color}; background-color: #f9f9f9;")
        section_layout = QVBoxLayout(section_frame)
        section_layout.setContentsMargins(8, 5, 8, 5)
        section_layout.setSpacing(2)

        # Title with status indicator
        title_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        title_layout.addWidget(title_label)

        status_label = QLabel(f"[{stats['status']}]")
        status_label.setStyleSheet(f"font-weight: bold; color: {stats['status_color']}; font-size: 10px;")
        title_layout.addWidget(status_label)
        title_layout.addStretch()
        section_layout.addLayout(title_layout)

        # Statistics
        stats_text = f"Coverage: {stats['coverage']}\n"
        if stats['gap_count'] > 0:
            stats_text += f"Gaps: {stats['gap_count']}\n"
            if isinstance(stats['total_gap_size'], (int, float)):
                stats_text += f"Total gap size: {stats['total_gap_size']:.2f}\n"
            if isinstance(stats['largest_gap'], (int, float)):
                stats_text += f"Largest gap: {stats['largest_gap']:.2f}"

        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-size: 10px; color: #555;")
        stats_label.setWordWrap(True)
        section_layout.addWidget(stats_label)

        # Message
        if stats.get('message'):
            msg_label = QLabel(stats['message'])
            msg_label.setStyleSheet("font-size: 9px; color: #777; font-style: italic;")
            msg_label.setWordWrap(True)
            section_layout.addWidget(msg_label)

        self.content_layout.addWidget(section_frame)

    def _clear_layout(self, layout):
        """Clear all widgets from a layout."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())