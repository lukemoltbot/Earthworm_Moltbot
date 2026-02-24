"""
LithologyDataTable component - displays lithology intervals in a table.
Synchronizes selection with other components via shared DepthStateManager.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QTimer
from typing import Optional, List
from src.core.graphic_models import HoleDataProvider, LithologyInterval
from src.ui.graphic_window.state import DepthStateManager, DepthRange


class LithologyDataTable(QWidget):
    """
    Right panel: Table showing lithology intervals.
    
    Synchronization pattern:
    - When table row is selected → update central state
    - When central state selection changes → select corresponding table row
    """
    
    def __init__(self, data_provider: HoleDataProvider,
                 depth_state_manager: DepthStateManager,
                 depth_coord_system=None):  # depth_coord_system not used but kept for consistency
        super().__init__()
        
        self.data_provider = data_provider
        self.state = depth_state_manager
        
        self.setMinimumWidth(200)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "From", "To", "Code", "Description", "Sample"
        ])
        
        # Style table
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        
        # Load data
        self.lithology_intervals: List[LithologyInterval] = (
            self.data_provider.get_lithology_intervals()
        )
        self.populate_table()
        
        # Connect table selection change
        self.table.itemSelectionChanged.connect(self.on_table_selection_changed)
        
        # Subscribe to state changes
        self.state.selectionRangeChanged.connect(self.on_state_selection_changed)
    
    def populate_table(self):
        """Populate table with lithology data."""
        self.table.setRowCount(len(self.lithology_intervals))
        
        for row, interval in enumerate(self.lithology_intervals):
            # From depth
            from_item = QTableWidgetItem(f"{interval.from_depth:.2f}")
            from_item.setData(Qt.ItemDataRole.UserRole, interval.from_depth)
            from_item.setFlags(from_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, from_item)
            
            # To depth
            to_item = QTableWidgetItem(f"{interval.to_depth:.2f}")
            to_item.setData(Qt.ItemDataRole.UserRole, interval.to_depth)
            to_item.setFlags(to_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, to_item)
            
            # Code
            code_item = QTableWidgetItem(interval.code)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 2, code_item)
            
            # Description
            desc_item = QTableWidgetItem(interval.description)
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, desc_item)
            
            # Sample number
            sample_item = QTableWidgetItem(interval.sample_number or "")
            sample_item.setFlags(sample_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 4, sample_item)
    
    def on_table_selection_changed(self):
        """Table selection changed by user - update central state."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.lithology_intervals):
            return
        
        interval = self.lithology_intervals[row]
        
        # Update central state (this will trigger all components)
        self.state.set_selection_range(interval.from_depth, interval.to_depth)
        self.state.set_cursor_depth(interval.from_depth)
    
    def on_state_selection_changed(self, depth_range: Optional[DepthRange]):
        """Central state selection changed - update table selection."""
        if depth_range is None:
            # Clear selection
            self.table.clearSelection()
            return
        
        # Find row matching this depth range
        for row, interval in enumerate(self.lithology_intervals):
            if (abs(interval.from_depth - depth_range.from_depth) < 0.001 and
                abs(interval.to_depth - depth_range.to_depth) < 0.001):
                # Select the row
                # Use QTimer.singleShot to avoid recursion
                QTimer.singleShot(0, lambda r=row: self.select_table_row(r))
                return
        
        # If no exact match, find row containing the from_depth
        for row, interval in enumerate(self.lithology_intervals):
            if interval.contains_depth(depth_range.from_depth):
                QTimer.singleShot(0, lambda r=row: self.select_table_row(r))
                return
    
    def select_table_row(self, row: int):
        """Select a specific row in the table."""
        if 0 <= row < self.table.rowCount():
            # Block signals to avoid triggering on_table_selection_changed
            self.table.blockSignals(True)
            self.table.selectRow(row)
            self.table.blockSignals(False)
            
            # Ensure row is visible
            self.table.scrollToItem(self.table.item(row, 0))