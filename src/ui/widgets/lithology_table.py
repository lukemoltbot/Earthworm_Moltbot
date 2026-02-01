from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QStyledItemDelegate,
    QComboBox, QHeaderView, QAbstractItemView, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QEvent
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QKeyEvent
from typing import Optional, Dict, List, Tuple
import pandas as pd

from ..core.dictionary_manager import get_dictionary_manager
from ..core.validation import ValidationResult, ValidationIssue, ValidationSeverity


class DictionaryDelegate(QStyledItemDelegate):
    """
    Renders a ComboBox for cells using DictionaryManager.
    Displays: "Description (Code)"
    Saves: "Code"
    """
    def __init__(self, category: str, parent=None):
        super().__init__(parent)
        self.category = category
        self.dictionary_manager = get_dictionary_manager()
        self._update_items()
    
    def _update_items(self):
        """Update the items list from dictionary manager."""
        self.items = []
        self.code_to_desc = {}
        
        if self.dictionary_manager and self.dictionary_manager.is_loaded:
            codes = self.dictionary_manager.get_codes_for_category(self.category)
            for code, desc in codes:
                display_text = f"{desc} ({code})"
                self.items.append(display_text)
                self.code_to_desc[code] = display_text
        
        # Always include empty option
        self.items.insert(0, "")
    
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        editor.setEditable(True)  # Allow typing to search
        editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        return editor

    def setEditorData(self, editor, index):
        current_code = index.model().data(index, Qt.ItemDataRole.EditRole)
        if current_code and current_code in self.code_to_desc:
            full_text = self.code_to_desc[current_code]
            idx = editor.findText(full_text)
            if idx >= 0: 
                editor.setCurrentIndex(idx)
            else:
                editor.setCurrentText(str(current_code))
        else:
            editor.setCurrentText(str(current_code) if current_code else "")

    def setModelData(self, editor, model, index):
        # Parse "Description (Code)" back to just "Code"
        text = editor.currentText()
        if "(" in text and text.endswith(")"):
            code = text.split("(")[-1].replace(")", "").strip()
            model.setData(index, code, Qt.ItemDataRole.EditRole)
        else:
            model.setData(index, text.strip(), Qt.ItemDataRole.EditRole)
    
    def reload_dictionaries(self):
        """Reload dictionaries from file."""
        if self.dictionary_manager:
            self.dictionary_manager.reload()
            self._update_items()


class ValidationDelegate(QStyledItemDelegate):
    """
    Delegate that paints cells with validation errors.
    """
    def __init__(self, validation_issues: Dict[int, List[ValidationIssue]] = None, parent=None):
        super().__init__(parent)
        self.validation_issues = validation_issues or {}
        self.error_brush = QBrush(QColor(255, 200, 200))  # Light red
        self.warning_brush = QBrush(QColor(255, 255, 200))  # Light yellow
    
    def set_validation_issues(self, validation_issues: Dict[int, List[ValidationIssue]]):
        """Update validation issues."""
        self.validation_issues = validation_issues
    
    def paint(self, painter, option, index):
        # Check if this cell has validation issues
        row = index.row()
        col = index.column()
        
        if row in self.validation_issues:
            # Check if any issue is for this specific column
            # This is simplified - in practice we'd need column mapping
            has_error = any(issue.severity == ValidationSeverity.ERROR 
                          for issue in self.validation_issues[row])
            has_warning = any(issue.severity == ValidationSeverity.WARNING 
                            for issue in self.validation_issues[row])
            
            if has_error:
                painter.fillRect(option.rect, self.error_brush)
            elif has_warning:
                painter.fillRect(option.rect, self.warning_brush)
        
        # Call parent paint to draw text
        super().paint(painter, option, index)


class LithologyTableWidget(QTableWidget):
    dataChangedSignal = pyqtSignal(object)  # Signal to notify main window to redraw graphics
    rowSelectionChangedSignal = pyqtSignal(int)  # Signal emitted when row selection changes
    validationChangedSignal = pyqtSignal(object)  # Signal with validation results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary_manager = get_dictionary_manager()
        self.validation_issues: Dict[int, List[ValidationIssue]] = {}
        self.current_dataframe: Optional[pd.DataFrame] = None
        self.total_depth: Optional[float] = None
        
        # 1point Desktop standard column layout with new interbedding columns
        self.headers = [
            'From', 'To', 'Thick', 'Litho', 'Qual',
            'Shade', 'Hue', 'Colour', 'Weath', 'Str',
            'Rec Seq', 'Inter-rel', 'Percent', 'Bed Sp'
        ]
        
        # Map internal DF columns to Table Indices
        self.col_map = {
            'from_depth': 0, 'to_depth': 1, 'thickness': 2,
            'LITHOLOGY_CODE': 3, 'lithology_qualifier': 4,
            'shade': 5, 'hue': 6, 'colour': 7,
            'weathering': 8, 'estimated_strength': 9,
            'record_sequence': 10, 'inter_relationship': 11, 
            'percentage': 12, 'bed_spacing': 13
        }
        
        # Reverse mapping for validation
        self.index_to_col = {v: k for k, v in self.col_map.items()}
        
        # Dictionary column mappings
        self.dict_mappings = {
            3: 'Litho_Type', 4: 'Litho_Qual', 5: 'Shade',
            6: 'Hue', 7: 'Colour', 8: 'Weathering', 9: 'Est_Strength',
            11: 'Litho_Interrel', 13: 'Bed_Spacing'
        }
        
        self.setColumnCount(len(self.headers))
        self.setHorizontalHeaderLabels(self.headers)
        
        # Set column tooltips
        tooltips = {
            0: "From depth (meters)",
            1: "To depth (meters)",
            2: "Thickness (meters)",
            3: "Lithology type code",
            4: "Lithology qualifier",
            5: "Shade (light, medium, dark)",
            6: "Hue (color tint)",
            7: "Colour (primary color)",
            8: "Weathering degree",
            9: "Estimated strength",
            10: "Record sequence for interbedding",
            11: "Inter-relationship code",
            12: "Percentage in interbedded unit",
            13: "Bed spacing (CoalLog standard)"
        }
        for col, tip in tooltips.items():
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                header_item.setToolTip(tip)
        
        self.verticalHeader().setVisible(True)  # Show Row Numbers
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        # Apply dictionary delegates
        self._apply_dictionary_delegates()
        
        # Apply validation delegate
        self.validation_delegate = ValidationDelegate(self.validation_issues, self)
        self.setItemDelegate(self.validation_delegate)
        
        # Connect signals
        self.itemChanged.connect(self._handle_item_changed)
        self.itemSelectionChanged.connect(self._handle_selection_changed)
        
        # Install event filter for F3 key
        self.installEventFilter(self)
    
    def _apply_dictionary_delegates(self):
        """Apply dictionary delegates to appropriate columns."""
        for col_idx, category in self.dict_mappings.items():
            delegate = DictionaryDelegate(category, self)
            self.setItemDelegateForColumn(col_idx, delegate)
    
    def load_data(self, dataframe: pd.DataFrame, total_depth: Optional[float] = None):
        """Load data into the table and run validation."""
        self.blockSignals(True)
        self.current_dataframe = dataframe.copy()
        self.total_depth = total_depth
        
        self.setRowCount(0)
        self.setRowCount(len(dataframe))
        
        for row_idx, row_data in dataframe.iterrows():
            for col_name, col_idx in self.col_map.items():
                if col_name in dataframe.columns:
                    val = row_data[col_name]
                    # Format floats to 3 decimals
                    if isinstance(val, (float, int)) and col_idx <= 2:
                        val = f"{val:.3f}"
                    self.setItem(row_idx, col_idx, QTableWidgetItem(str(val) if val is not None else ""))
        
        self.blockSignals(False)
        
        # Run validation
        self.run_validation()
    
    def run_validation(self):
        """Run validation on current data and update UI."""
        if self.current_dataframe is None or self.current_dataframe.empty:
            self.validation_issues.clear()
            self.validation_delegate.set_validation_issues(self.validation_issues)
            self.viewport().update()
            return
        
        # Import here to avoid circular imports
        from ..core.validation import RealTimeValidator
        
        validator = RealTimeValidator(self.dictionary_manager)
        result = validator.validate_dataframe(self.current_dataframe, self.total_depth)
        
        # Group issues by row
        self.validation_issues.clear()
        for issue in result.issues:
            if issue.row_index is not None:
                if issue.row_index not in self.validation_issues:
                    self.validation_issues[issue.row_index] = []
                self.validation_issues[issue.row_index].append(issue)
        
        # Update validation delegate
        self.validation_delegate.set_validation_issues(self.validation_issues)
        
        # Emit signal with validation results
        self.validationChangedSignal.emit(result)
        
        # Trigger repaint
        self.viewport().update()
    
    def _handle_item_changed(self, item):
        """Handle item changes and update validation."""
        row = item.row()
        col = item.column()
        
        # Update dataframe
        if self.current_dataframe is not None and row < len(self.current_dataframe):
            col_name = self.index_to_col.get(col)
            if col_name:
                try:
                    text = item.text()
                    if col <= 2:  # Depth columns
                        value = float(text) if text else None
                    else:
                        value = text if text else None
                    
                    self.current_dataframe.at[row, col_name] = value
                    
                    # Auto-calc thickness
                    if col in [0, 1]:  # From or To changed
                        self._update_thickness(row)
                    
                except ValueError:
                    pass
        
        # Run validation
        self.run_validation()
        
        # Notify Main Window that data changed
        self.dataChangedSignal.emit(None)
    
    def _update_thickness(self, row: int):
        """Update thickness for a row based on From and To depths."""
        if self.current_dataframe is None:
            return
        
        try:
            from_item = self.item(row, 0)
            to_item = self.item(row, 1)
            if from_item and to_item and from_item.text() and to_item.text():
                start = float(from_item.text())
                end = float(to_item.text())
                thickness = end - start
                
                self.blockSignals(True)
                self.setItem(row, 2, QTableWidgetItem(f"{thickness:.3f}"))
                self.blockSignals(False)
                
                # Update dataframe
                self.current_dataframe.at[row, 'thickness'] = thickness
        except ValueError:
            pass
    
    def _handle_selection_changed(self):
        """Handle row selection changes."""
        selected_rows = self.selectionModel().selectedRows()
        if selected_rows:
            selected_row_index = selected_rows[0].row()
            self.rowSelectionChangedSignal.emit(selected_row_index)
        else:
            self.rowSelectionChangedSignal.emit(-1)
    
    def eventFilter(self, obj, event):
        """Handle F3 key for code search."""
        if event.type() == QEvent.Type.KeyPress:
            key_event = QKeyEvent(event)
            if key_event.key() == Qt.Key.Key_F3:
                self._open_code_search()
                return True
        
        return super().eventFilter(obj, event)
    
    def _open_code_search(self):
        """Open code search dialog."""
        try:
            from ..dialogs.code_search_dialog import CodeSearchDialog
            dialog = CodeSearchDialog(self)
            dialog.code_selected.connect(self._insert_code_from_search)
            dialog.exec()
        except ImportError as e:
            print(f"Could not open code search dialog: {e}")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Code Search", 
                                   "Code search dialog not available.")
    
    def _insert_code_from_search(self, category: str, code: str):
        """Insert code from search dialog into current cell."""
        current_item = self.currentItem()
        if not current_item:
            return
        
        # Check if current column matches the category
        current_col = current_item.column()
        expected_category = self.dict_mappings.get(current_col)
        
        if expected_category == category:
            # Direct match - just insert the code
            current_item.setText(code)
        else:
            # Show message about category mismatch
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Category Mismatch",
                              f"Selected code is from '{category}' category,\n"
                              f"but current column expects '{expected_category}'.")
    
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        """Get current dataframe."""
        return self.current_dataframe.copy() if self.current_dataframe is not None else None
    
    def reload_dictionaries(self):
        """Reload all dictionary delegates."""
        for col_idx in self.dict_mappings.keys():
            delegate = self.itemDelegateForColumn(col_idx)
            if isinstance(delegate, DictionaryDelegate):
                delegate.reload_dictionaries()
        
        # Re-run validation
        self.run_validation()