from PyQt6.QtWidgets import (
    QTableView, QStyledItemDelegate,
    QComboBox, QHeaderView, QAbstractItemView, QApplication
)
from ...ui.models.pandas_model import PandasModel
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex, QEvent, QThread, QObject
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QKeyEvent
from typing import Optional, Dict, List, Tuple
import pandas as pd

from ...core.dictionary_manager import get_dictionary_manager
from ...core.validation import ValidationResult, ValidationIssue, ValidationSeverity
from ...core.workers import ValidationWorker


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


class LithologyTableWidget(QTableView):
    dataChangedSignal = pyqtSignal(object)  # Signal to notify main window to redraw graphics
    rowSelectionChangedSignal = pyqtSignal(int)  # Signal emitted when row selection changes
    validationChangedSignal = pyqtSignal(object)  # Signal with validation results
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary_manager = get_dictionary_manager()
        self.validation_issues: Dict[int, List[ValidationIssue]] = {}
        self.current_dataframe: Optional[pd.DataFrame] = None
        self.total_depth: Optional[float] = None
        
        # Create PandasModel
        self.model = PandasModel()
        self.setModel(self.model)
        
        # Background validation
        self.validation_worker: Optional[ValidationWorker] = None
        self.validation_thread: Optional[QThread] = None
        self.is_validating = False
        
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
        
        # Set up view properties
        self.verticalHeader().setVisible(True)  # Show Row Numbers
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Apply dictionary delegates
        self._apply_dictionary_delegates()
        
        # Note: Validation highlighting is now handled by PandasModel
        # No separate validation delegate needed
        
        # Connect signals
        self.selectionModel().selectionChanged.connect(self._handle_selection_changed)
        self.model.dataChanged.connect(self._handle_data_changed)
        
        # Install event filter for F3 key
        self.installEventFilter(self)
        
        # Set editable columns in model
        self._update_editable_columns()
    
    def _update_editable_columns(self):
        """Update editable columns in the PandasModel."""
        if self.current_dataframe is not None:
            # All columns are editable by default
            editable_columns = list(self.current_dataframe.columns)
            self.model.set_editable_columns(editable_columns)
    
    def _handle_data_changed(self, top_left, bottom_right, roles):
        """Handle data changes from the model."""
        # Update dataframe from model
        self.current_dataframe = self.model.dataframe()
        
        # Skip validation if change is only for background/tooltip/font (i.e., validation updates)
        # If roles is None or empty list, it means all roles changed (including display), so run validation
        if roles:
            # Check if DisplayRole or EditRole are among changed roles
            # Note: roles is a list of Qt.ItemDataRole values
            display_role_changed = Qt.ItemDataRole.DisplayRole in roles
            edit_role_changed = Qt.ItemDataRole.EditRole in roles
            if not (display_role_changed or edit_role_changed):
                # Only background/tooltip/font changed (e.g., validation highlights)
                # Emit data changed signal but skip validation to avoid infinite loop
                self.dataChangedSignal.emit(self.current_dataframe)
                return
        elif roles is None:
            # roles is None, treat as all roles changed
            pass  # Continue to run validation
        
        # Run validation
        self.run_validation()
        
        # Emit data changed signal
        self.dataChangedSignal.emit(self.current_dataframe)
    
    def _apply_dictionary_delegates(self):
        """Apply dictionary delegates to appropriate columns."""
        for col_idx, category in self.dict_mappings.items():
            delegate = DictionaryDelegate(category, self)
            self.setItemDelegateForColumn(col_idx, delegate)
    
    def update_depth_value(self, row_index: int, boundary_type: str, new_depth: float):
        """
        Update a depth value in the table and dataframe.
        
        Args:
            row_index: Row index (0-based)
            boundary_type: 'top' for From_Depth, 'bottom' for To_Depth
            new_depth: New depth value
        """
        if self.current_dataframe is None or row_index >= len(self.current_dataframe):
            return False
            
        # Block signals to prevent recursive updates
        self.blockSignals(True)
        
        try:
            # Update the dataframe
            if boundary_type == 'top':
                column_name = 'from_depth'
                # Update From_Depth in dataframe
                self.current_dataframe.loc[row_index, 'from_depth'] = new_depth
                
                # Update To_Depth of previous row if it exists
                if row_index > 0:
                    self.current_dataframe.loc[row_index - 1, 'to_depth'] = new_depth
                    # Update thickness for previous row
                    prev_thickness = new_depth - self.current_dataframe.loc[row_index - 1, 'from_depth']
                    self.current_dataframe.loc[row_index - 1, 'thickness'] = prev_thickness
                    
            else:  # 'bottom'
                column_name = 'to_depth'
                # Update To_Depth in dataframe
                self.current_dataframe.loc[row_index, 'to_depth'] = new_depth
                
                # Update From_Depth of next row if it exists
                if row_index < len(self.current_dataframe) - 1:
                    self.current_dataframe.loc[row_index + 1, 'from_depth'] = new_depth
                    # Update thickness for next row
                    next_thickness = self.current_dataframe.loc[row_index + 1, 'to_depth'] - new_depth
                    self.current_dataframe.loc[row_index + 1, 'thickness'] = next_thickness
            
            # Update thickness for current row
            if boundary_type == 'top':
                current_thickness = self.current_dataframe.loc[row_index, 'to_depth'] - new_depth
            else:
                current_thickness = new_depth - self.current_dataframe.loc[row_index, 'from_depth']
            self.current_dataframe.loc[row_index, 'thickness'] = current_thickness
            
            # Update the model with new dataframe
            self.model.set_dataframe(self.current_dataframe)
            
            # Emit data changed for affected cells
            col_idx = self.col_map[column_name]
            thickness_col_idx = self.col_map['thickness']
            
            # Emit data changed for current row
            top_left = self.model.index(row_index, min(col_idx, thickness_col_idx))
            bottom_right = self.model.index(row_index, max(col_idx, thickness_col_idx))
            self.model.dataChanged.emit(top_left, bottom_right, [])
            
            # Update adjacent rows if needed
            if boundary_type == 'top' and row_index > 0:
                # Emit data changed for previous row
                prev_to_col_idx = self.col_map['to_depth']
                prev_thickness_col_idx = self.col_map['thickness']
                prev_top_left = self.model.index(row_index - 1, min(prev_to_col_idx, prev_thickness_col_idx))
                prev_bottom_right = self.model.index(row_index - 1, max(prev_to_col_idx, prev_thickness_col_idx))
                self.model.dataChanged.emit(prev_top_left, prev_bottom_right, [])
                
            elif boundary_type == 'bottom' and row_index < len(self.current_dataframe) - 1:
                # Emit data changed for next row
                next_from_col_idx = self.col_map['from_depth']
                next_thickness_col_idx = self.col_map['thickness']
                next_top_left = self.model.index(row_index + 1, min(next_from_col_idx, next_thickness_col_idx))
                next_bottom_right = self.model.index(row_index + 1, max(next_from_col_idx, next_thickness_col_idx))
                self.model.dataChanged.emit(next_top_left, next_bottom_right, [])
            
            # Run validation on affected rows
            affected_rows = [row_index]
            if boundary_type == 'top' and row_index > 0:
                affected_rows.append(row_index - 1)
            elif boundary_type == 'bottom' and row_index < len(self.current_dataframe) - 1:
                affected_rows.append(row_index + 1)
            
            self._run_validation_for_rows(affected_rows)
            
            # Emit data changed signal
            self.dataChangedSignal.emit(self.current_dataframe)
            
            return True
            
        finally:
            self.blockSignals(False)
    
    def load_data(self, dataframe: pd.DataFrame, total_depth: Optional[float] = None):
        """Load data into the table and run validation."""
        self.blockSignals(True)
        self.current_dataframe = dataframe.copy()
        self.total_depth = total_depth
        
        # Set dataframe in model
        self.model.set_dataframe(self.current_dataframe)
        
        # Update editable columns
        self._update_editable_columns()
        
        self.blockSignals(False)
        
        # Run validation
        self.run_validation()
    
    def run_validation(self):
        """Run validation in background thread."""
        if self.current_dataframe is None or self.current_dataframe.empty:
            self.validation_issues.clear()
            # Update PandasModel with empty validation issues
            self.model.set_validation_issues({})
            return
        
        # Cancel any ongoing validation
        self._cancel_validation()
        
        # Create worker and thread
        self.validation_worker = ValidationWorker(self.current_dataframe, self.total_depth)
        self.validation_thread = QThread()
        
        # Move worker to thread
        self.validation_worker.moveToThread(self.validation_thread)
        
        # Connect signals
        self.validation_thread.started.connect(self.validation_worker.run)
        self.validation_worker.progress.connect(self._on_validation_progress)
        self.validation_worker.finished.connect(self._on_validation_finished)
        self.validation_worker.error.connect(self._on_validation_error)
        
        # Cleanup connections
        self.validation_worker.finished.connect(self.validation_thread.quit)
        self.validation_worker.finished.connect(self.validation_worker.deleteLater)
        self.validation_thread.finished.connect(self.validation_thread.deleteLater)
        
        # Set flag and start
        self.is_validating = True
        self.validation_thread.start()
    
    def _cancel_validation(self):
        """Cancel any ongoing validation."""
        if self.validation_thread and self.validation_thread.isRunning():
            self.validation_thread.quit()
            self.validation_thread.wait()
        self.validation_worker = None
        self.validation_thread = None
        self.is_validating = False
    
    def _on_validation_progress(self, percent: int, message: str):
        """Handle validation progress updates."""
        # Could update status bar or show progress in UI
        print(f"Validation: {percent}% - {message}")
    
    def _on_validation_finished(self, result: ValidationResult):
        """Handle validation completion."""
        self.is_validating = False
        
        # Group issues by row
        self.validation_issues.clear()
        for issue in result.issues:
            if issue.row_index is not None:
                if issue.row_index not in self.validation_issues:
                    self.validation_issues[issue.row_index] = []
                self.validation_issues[issue.row_index].append(issue)
        
        # Note: Validation delegate removed - highlighting handled by PandasModel
        
        # Update PandasModel with validation issues
        # Convert ValidationIssue objects to simple dicts with severity and column
        pandas_model_issues = {}
        for row_idx, issues in self.validation_issues.items():
            pandas_model_issues[row_idx] = []
            for issue in issues:
                # Convert ValidationSeverity enum to string
                severity_str = issue.severity.value if hasattr(issue.severity, 'value') else str(issue.severity)
                pandas_model_issues[row_idx].append({
                    'severity': severity_str.upper(),
                    'column': issue.column,
                    'message': issue.message
                })
        
        self.model.set_validation_issues(pandas_model_issues)
        
        # Emit signal with validation results
        self.validationChangedSignal.emit(result)
    
    def _on_validation_error(self, error_msg: str):
        """Handle validation errors."""
        self.is_validating = False
        print(f"Validation error: {error_msg}")
        # Could show error in status bar
    
    def _run_validation_for_rows(self, row_indices: List[int]):
        """Run validation for specific rows (triggers background validation)."""
        # For now, just trigger full background validation
        # This ensures UI doesn't freeze while providing validation feedback
        self.run_validation()
    
    # Note: _handle_item_changed method removed - not needed for QTableView
    # Data changes are handled via model's dataChanged signal connected to _handle_data_changed
    
    def _update_thickness(self, row: int):
        """Update thickness for a row based on From and To depths."""
        if self.current_dataframe is None or row >= len(self.current_dataframe):
            return
        
        try:
            # Get from and to depths from dataframe
            from_depth = self.current_dataframe.at[row, 'from_depth']
            to_depth = self.current_dataframe.at[row, 'to_depth']
            
            if pd.notna(from_depth) and pd.notna(to_depth):
                thickness = to_depth - from_depth
                
                # Update dataframe
                self.current_dataframe.at[row, 'thickness'] = thickness
                
                # Update model
                thickness_col_idx = self.col_map['thickness']
                index = self.model.index(row, thickness_col_idx)
                self.model.setData(index, thickness, Qt.ItemDataRole.EditRole)
        except (ValueError, KeyError):
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
        current_index = self.currentIndex()
        if not current_index.isValid():
            return
        
        # Check if current column matches the category
        current_col = current_index.column()
        expected_category = self.dict_mappings.get(current_col)
        
        if expected_category == category:
            # Direct match - just insert the code
            self.model.setData(current_index, code, Qt.ItemDataRole.EditRole)
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