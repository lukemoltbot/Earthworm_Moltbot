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
        self.pandas_model = PandasModel()
        self.setModel(self.pandas_model)
        
        # Background validation
        self.validation_worker: Optional[ValidationWorker] = None
        self.validation_thread: Optional[QThread] = None
        self.is_validating = False
        
        # CoalLog v3.1 standard 37-column layout
        self.headers = [
            'From Depth', 'To Depth', 'Recovered Thickness',
            'Record Sequence Flag', 'Seam', 'Ply', 'Horizon',
            'Sample Purpose', 'Lithology Sample Number', 'Interval Status',
            'Lithology', 'Lithology Qualifier', 'Lithology %',
            'Shade', 'Hue', 'Colour',
            'Adjective 1', 'Adjective 2', 'Adjective 3', 'Adjective 4',
            'Interrelationship', 'Lithology Descriptor',
            'Weathering', 'Estimated Strength', 'Bed Spacing',
            'Core State', 'Mechanical State', 'Texture',
            'Defect Type', 'Intact', 'Defect Spacing', 'Defect Dip',
            'Bedding Dip', 'Basal Contact', 'Sedimentary Feature',
            'Mineral / Fossil', 'Abundance'
        ]
        
        # Map internal DF columns to Table Indices (0-36 for 37 columns)
        self.col_map = {
            'from_depth': 0, 'to_depth': 1, 'recovered_thickness': 2,
            'record_sequence_flag': 3, 'seam': 4, 'ply': 5, 'horizon': 6,
            'sample_purpose': 7, 'lithology_sample_number': 8, 'interval_status': 9,
            'lithology': 10, 'lithology_qualifier': 11, 'lithology_percent': 12,
            'shade': 13, 'hue': 14, 'colour': 15,
            'adjective_1': 16, 'adjective_2': 17, 'adjective_3': 18, 'adjective_4': 19,
            'interrelationship': 20, 'lithology_descriptor': 21,
            'weathering': 22, 'estimated_strength': 23, 'bed_spacing': 24,
            'core_state': 25, 'mechanical_state': 26, 'texture': 27,
            'defect_type': 28, 'intact': 29, 'defect_spacing': 30, 'defect_dip': 31,
            'bedding_dip': 32, 'basal_contact': 33, 'sedimentary_feature': 34,
            'mineral_fossil': 35, 'abundance': 36
        }
        
        # Reverse mapping for validation
        self.index_to_col = {v: k for k, v in self.col_map.items()}
        
        # Dictionary column mappings for CoalLog v3.1 standard columns
        # Based on CoalLog v3.1 dictionary standards
        self.dict_mappings = {
            10: 'Litho_Type',        # Lithology
            11: 'Litho_Qual',        # Lithology Qualifier
            13: 'Shade',             # Shade
            14: 'Hue',               # Hue
            15: 'Colour',            # Colour
            20: 'Litho_Interrel',    # Interrelationship
            22: 'Weathering',        # Weathering
            23: 'Est_Strength',      # Estimated Strength
            24: 'Bed_Spacing',       # Bed Spacing
            # Note: Additional dictionary columns in CoalLog v3.1 that may need mapping:
            # 25: 'Core_State',      # Core State (if dictionary exists)
            # 26: 'Mech_State',      # Mechanical State (if dictionary exists)
            # 27: 'Texture',         # Texture (if dictionary exists)
            # 28: 'Defect_Type',     # Defect Type (if dictionary exists)
            # 33: 'Basal_Contact',   # Basal Contact (if dictionary exists)
            # 34: 'Sed_Feature',     # Sedimentary Feature (if dictionary exists)
            # 35: 'Mineral_Fossil',  # Mineral / Fossil (if dictionary exists)
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
        self.pandas_model.dataChanged.connect(self._handle_data_changed)
        
        # Install event filter for F3 key
        self.installEventFilter(self)
        
        # Set editable columns in model
        self._update_editable_columns()
    
    def _update_editable_columns(self):
        """Update editable columns in the PandasModel."""
        if self.current_dataframe is not None:
            # All columns are editable by default
            editable_columns = list(self.current_dataframe.columns)
            self.pandas_model.set_editable_columns(editable_columns)
    
    def _handle_data_changed(self, top_left, bottom_right, roles):
        """Handle data changes from the model."""
        # Update dataframe from model
        self.current_dataframe = self.pandas_model.dataframe()
        
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
                    self.current_dataframe.loc[row_index - 1, 'recovered_thickness'] = prev_thickness
                    
            else:  # 'bottom'
                column_name = 'to_depth'
                # Update To_Depth in dataframe
                self.current_dataframe.loc[row_index, 'to_depth'] = new_depth
                
                # Update From_Depth of next row if it exists
                if row_index < len(self.current_dataframe) - 1:
                    self.current_dataframe.loc[row_index + 1, 'from_depth'] = new_depth
                    # Update thickness for next row
                    next_thickness = self.current_dataframe.loc[row_index + 1, 'to_depth'] - new_depth
                    self.current_dataframe.loc[row_index + 1, 'recovered_thickness'] = next_thickness
            
            # Update thickness for current row
            if boundary_type == 'top':
                current_thickness = self.current_dataframe.loc[row_index, 'to_depth'] - new_depth
            else:
                current_thickness = new_depth - self.current_dataframe.loc[row_index, 'from_depth']
            self.current_dataframe.loc[row_index, 'recovered_thickness'] = current_thickness
            
            # Update the model with new dataframe
            self.pandas_model.set_dataframe(self.current_dataframe)
            
            # Emit data changed for affected cells
            col_idx = self.col_map[column_name]
            thickness_col_idx = self.col_map['recovered_thickness']
            
            # Emit data changed for current row
            top_left = self.pandas_model.index(row_index, min(col_idx, thickness_col_idx))
            bottom_right = self.pandas_model.index(row_index, max(col_idx, thickness_col_idx))
            self.pandas_model.dataChanged.emit(top_left, bottom_right, [])
            
            # Update adjacent rows if needed
            if boundary_type == 'top' and row_index > 0:
                # Emit data changed for previous row
                prev_to_col_idx = self.col_map['to_depth']
                prev_thickness_col_idx = self.col_map['recovered_thickness']
                prev_top_left = self.pandas_model.index(row_index - 1, min(prev_to_col_idx, prev_thickness_col_idx))
                prev_bottom_right = self.pandas_model.index(row_index - 1, max(prev_to_col_idx, prev_thickness_col_idx))
                self.pandas_model.dataChanged.emit(prev_top_left, prev_bottom_right, [])
                
            elif boundary_type == 'bottom' and row_index < len(self.current_dataframe) - 1:
                # Emit data changed for next row
                next_from_col_idx = self.col_map['from_depth']
                next_thickness_col_idx = self.col_map['recovered_thickness']
                next_top_left = self.pandas_model.index(row_index + 1, min(next_from_col_idx, next_thickness_col_idx))
                next_bottom_right = self.pandas_model.index(row_index + 1, max(next_from_col_idx, next_thickness_col_idx))
                self.pandas_model.dataChanged.emit(next_top_left, next_bottom_right, [])
            
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
        self.pandas_model.set_dataframe(self.current_dataframe)
        
        # Update editable columns
        self._update_editable_columns()
        
        self.blockSignals(False)
        
        # Emit data changed signal to notify main window
        self.dataChangedSignal.emit(self.current_dataframe)
        
        # Run validation
        self.run_validation()
    
    def run_validation(self):
        """Run validation in background thread."""
        if self.current_dataframe is None or self.current_dataframe.empty:
            self.validation_issues.clear()
            # Update PandasModel with empty validation issues
            self.pandas_model.set_validation_issues({})
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
        
        self.pandas_model.set_validation_issues(pandas_model_issues)
        
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
                self.current_dataframe.at[row, 'recovered_thickness'] = thickness
                
                # Update model
                thickness_col_idx = self.col_map['recovered_thickness']
                index = self.pandas_model.index(row, thickness_col_idx)
                self.pandas_model.setData(index, thickness, Qt.ItemDataRole.EditRole)
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
            self.pandas_model.setData(current_index, code, Qt.ItemDataRole.EditRole)
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