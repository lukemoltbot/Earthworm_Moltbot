"""
PandasModel - QAbstractTableModel wrapper for pandas DataFrame.
"""
from typing import Optional, Any, Dict, List, Tuple
import pandas as pd
import numpy as np
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QVariant
from PyQt6.QtGui import QBrush, QColor


class PandasModel(QAbstractTableModel):
    """
    A QAbstractTableModel that wraps a pandas DataFrame.
    
    Features:
    - Efficient handling of large datasets
    - Support for editing, sorting, and filtering
    - Proper data type handling
    - Performance optimizations for large tables
    """
    
    def __init__(self, dataframe: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self._sort_column = -1
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._editable_columns = set()
        self._column_formatters = {}
        self._validation_issues = {}  # row -> list of column issues
        self._background_colors = {}  # (row, col) -> QColor
        
    def set_dataframe(self, dataframe: pd.DataFrame):
        """Set the underlying dataframe."""
        self.beginResetModel()
        self._dataframe = dataframe.copy()
        self.endResetModel()
    
    def dataframe(self) -> pd.DataFrame:
        """Get the underlying dataframe."""
        return self._dataframe.copy()
    
    def rowCount(self, parent=QModelIndex()) -> int:
        """Return number of rows."""
        if parent.isValid():
            return 0
        return len(self._dataframe)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        """Return number of columns."""
        if parent.isValid():
            return 0
        return len(self._dataframe.columns)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if row >= self.rowCount() or col >= self.columnCount():
            return QVariant()
        
        # Get column name
        col_name = self._dataframe.columns[col]
        
        # Handle different roles
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            # Get the value
            value = self._dataframe.iat[row, col]
            
            # Handle NaN/None
            if pd.isna(value):
                return ""
            
            # Apply formatter if available
            if col_name in self._column_formatters:
                return self._column_formatters[col_name](value)
            
            # Convert to string for display
            return str(value)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Align numeric columns to the right
            if pd.api.types.is_numeric_dtype(self._dataframe.dtypes.iloc[col]):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Check for validation issues
            if row in self._validation_issues:
                issues = self._validation_issues[row]
                # Check if any issue is for this column
                # In practice, we'd need better column mapping
                for issue in issues:
                    # Handle both dictionary and object formats
                    column = issue.get('column') if isinstance(issue, dict) else issue.column
                    severity = issue.get('severity') if isinstance(issue, dict) else issue.severity
                    
                    if column == col_name or column is None:
                        if severity == "ERROR":
                            return QBrush(QColor(255, 200, 200))  # Light red
                        elif severity == "WARNING":
                            return QBrush(QColor(255, 255, 200))  # Light yellow
            
            # Check for custom background color
            if (row, col) in self._background_colors:
                return QBrush(self._background_colors[(row, col)])
            
            # Alternate row colors for better readability
            if row % 2 == 0:
                return QBrush(QColor(240, 240, 240))
            
        elif role == Qt.ItemDataRole.ToolTipRole:
            # Show tooltip for validation issues
            if row in self._validation_issues:
                issues = self._validation_issues[row]
                tooltips = []
                for issue in issues:
                    # Handle both dictionary and object formats
                    column = issue.get('column') if isinstance(issue, dict) else issue.column
                    severity = issue.get('severity') if isinstance(issue, dict) else issue.severity
                    message = issue.get('message') if isinstance(issue, dict) else issue.message
                    
                    if column == col_name or column is None:
                        tooltips.append(f"{severity}: {message}")
                if tooltips:
                    return "\n".join(tooltips)
        
        elif role == Qt.ItemDataRole.FontRole:
            # Make validation errors bold
            if row in self._validation_issues:
                issues = self._validation_issues[row]
                for issue in issues:
                    # Handle both dictionary and object formats
                    column = issue.get('column') if isinstance(issue, dict) else issue.column
                    severity = issue.get('severity') if isinstance(issue, dict) else issue.severity
                    
                    if (column == col_name or column is None) and severity == "ERROR":
                        from PyQt6.QtGui import QFont
                        font = QFont()
                        font.setBold(True)
                        return font
        
        return QVariant()
    
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """Set data at the given index."""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        
        row = index.row()
        col = index.column()
        
        if row >= self.rowCount() or col >= self.columnCount():
            return False
        
        # Check if column is editable
        col_name = self._dataframe.columns[col]
        if col_name not in self._editable_columns:
            return False
        
        try:
            # Convert value to appropriate type
            old_value = self._dataframe.iat[row, col]
            dtype = self._dataframe.dtypes.iloc[col]
            
            if pd.api.types.is_numeric_dtype(dtype):
                # Handle numeric columns
                if value == "" or pd.isna(value):
                    new_value = np.nan
                else:
                    new_value = dtype.type(value)
            else:
                # Handle string columns
                new_value = str(value) if value is not None else ""
            
            # Update dataframe
            self._dataframe.iat[row, col] = new_value
            
            # Emit data changed signal
            self.dataChanged.emit(index, index, [role])
            
            return True
            
        except (ValueError, TypeError) as e:
            print(f"Error setting data: {e}")
            return False
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Return header data."""
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        
        if orientation == Qt.Orientation.Horizontal:
            if section < len(self._dataframe.columns):
                return str(self._dataframe.columns[section])
        elif orientation == Qt.Orientation.Vertical:
            return str(section + 1)  # 1-indexed row numbers
        
        return QVariant()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return item flags."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        
        # Check if column is editable
        col = index.column()
        if col < len(self._dataframe.columns):
            col_name = self._dataframe.columns[col]
            if col_name in self._editable_columns:
                flags |= Qt.ItemFlag.ItemIsEditable
        
        return flags
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """Sort the dataframe by the given column."""
        if column < 0 or column >= len(self._dataframe.columns):
            return
        
        self.beginResetModel()
        
        col_name = self._dataframe.columns[column]
        ascending = (order == Qt.SortOrder.AscendingOrder)
        
        try:
            self._dataframe = self._dataframe.sort_values(by=col_name, ascending=ascending)
            self._sort_column = column
            self._sort_order = order
        except Exception as e:
            print(f"Error sorting by column {col_name}: {e}")
        
        self.endResetModel()
    
    def set_editable_columns(self, columns: List[str]):
        """Set which columns are editable."""
        self._editable_columns = set(columns)
    
    def set_column_formatter(self, column: str, formatter):
        """Set a formatter function for a column."""
        self._column_formatters[column] = formatter
    
    def set_validation_issues(self, validation_issues: Dict[int, List]):
        """Set validation issues for highlighting."""
        self._validation_issues = validation_issues
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1),
            [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.FontRole]
        )
    
    def set_background_color(self, row: int, col: int, color: QColor):
        """Set background color for a specific cell."""
        self._background_colors[(row, col)] = color
        index = self.index(row, col)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.BackgroundRole])
    
    def clear_background_colors(self):
        """Clear all custom background colors."""
        self._background_colors.clear()
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.columnCount() - 1),
            [Qt.ItemDataRole.BackgroundRole]
        )
    
    def insert_row(self, row: int, data: Dict[str, Any] = None):
        """Insert a new row at the given position."""
        if row < 0 or row > len(self._dataframe):
            row = len(self._dataframe)
        
        self.beginInsertRows(QModelIndex(), row, row)
        
        # Create new row with default values
        new_row = {}
        for col in self._dataframe.columns:
            if data and col in data:
                new_row[col] = data[col]
            else:
                # Use appropriate default based on dtype
                dtype = self._dataframe.dtypes[col]
                if pd.api.types.is_numeric_dtype(dtype):
                    new_row[col] = 0.0
                else:
                    new_row[col] = ""
        
        # Insert the row
        self._dataframe = pd.concat([
            self._dataframe.iloc[:row],
            pd.DataFrame([new_row]),
            self._dataframe.iloc[row:]
        ], ignore_index=True)
        
        self.endInsertRows()
        return True
    
    def remove_row(self, row: int):
        """Remove a row at the given position."""
        if row < 0 or row >= len(self._dataframe):
            return False
        
        self.beginRemoveRows(QModelIndex(), row, row)
        self._dataframe = self._dataframe.drop(index=row).reset_index(drop=True)
        self.endRemoveRows()
        return True
    
    def get_row_data(self, row: int) -> Dict[str, Any]:
        """Get data for a specific row as a dictionary."""
        if row < 0 or row >= len(self._dataframe):
            return {}
        
        return self._dataframe.iloc[row].to_dict()
    
    def find_rows(self, column: str, value: Any) -> List[int]:
        """Find rows where column matches value."""
        if column not in self._dataframe.columns:
            return []
        
        matches = self._dataframe[self._dataframe[column] == value]
        return matches.index.tolist()