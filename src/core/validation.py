"""
Validation engine for geological data.

Provides real-time validation of hole data including gaps, overlaps,
and total depth consistency.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    severity: ValidationSeverity
    message: str
    row_index: Optional[int] = None
    column: Optional[str] = None
    value: Optional[Any] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'severity': self.severity.value,
            'message': self.message,
            'row_index': self.row_index,
            'column': self.column,
            'value': str(self.value) if self.value is not None else None
        }


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.is_valid = True
    
    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)
        if issue.severity == ValidationSeverity.ERROR:
            self.is_valid = False
    
    def add_error(self, message: str, row_index: Optional[int] = None, 
                  column: Optional[str] = None, value: Optional[Any] = None):
        """Add an error issue."""
        self.add_issue(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            message=message,
            row_index=row_index,
            column=column,
            value=value
        ))
    
    def add_warning(self, message: str, row_index: Optional[int] = None,
                    column: Optional[str] = None, value: Optional[Any] = None):
        """Add a warning issue."""
        self.add_issue(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            message=message,
            row_index=row_index,
            column=column,
            value=value
        ))
    
    def add_info(self, message: str, row_index: Optional[int] = None,
                 column: Optional[str] = None, value: Optional[Any] = None):
        """Add an info issue."""
        self.add_issue(ValidationIssue(
            severity=ValidationSeverity.INFO,
            message=message,
            row_index=row_index,
            column=column,
            value=value
        ))
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get all error issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warning issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]
    
    def get_infos(self) -> List[ValidationIssue]:
        """Get all info issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.INFO]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'is_valid': self.is_valid,
            'issues': [issue.to_dict() for issue in self.issues],
            'error_count': len(self.get_errors()),
            'warning_count': len(self.get_warnings()),
            'info_count': len(self.get_infos())
        }
    
    def __str__(self) -> str:
        """String representation for debugging."""
        if not self.issues:
            return "No validation issues found."
        
        lines = []
        for issue in self.issues:
            location = ""
            if issue.row_index is not None:
                location = f"Row {issue.row_index}"
                if issue.column:
                    location += f", Column {issue.column}"
            
            if location:
                lines.append(f"[{issue.severity.value.upper()}] {location}: {issue.message}")
            else:
                lines.append(f"[{issue.severity.value.upper()}] {issue.message}")
        
        return "\n".join(lines)


def validate_hole(dataframe: pd.DataFrame, total_depth: Optional[float] = None) -> ValidationResult:
    """
    Validate hole data for gaps, overlaps, and consistency.
    
    Args:
        dataframe: DataFrame containing hole data with 'From_Depth' and 'To_Depth' columns
        total_depth: Optional total depth from header to validate against
        
    Returns:
        ValidationResult object containing all validation issues
    """
    result = ValidationResult()
    
    if dataframe.empty:
        result.add_warning("DataFrame is empty")
        return result
    
    # Check required columns
    required_columns = ['From_Depth', 'To_Depth']
    for col in required_columns:
        if col not in dataframe.columns:
            result.add_error(f"Missing required column: {col}")
    
    if not result.is_valid:
        return result
    
    # Sort by From_Depth to ensure proper validation
    df = dataframe.sort_values('From_Depth').reset_index(drop=True)
    
    # Validate each row
    for idx, row in df.iterrows():
        from_depth = row['From_Depth']
        to_depth = row['To_Depth']
        
        # Check for valid numeric values
        if pd.isna(from_depth) or pd.isna(to_depth):
            result.add_error(f"Missing depth values", row_index=idx)
            continue
        
        # Check From_Depth < To_Depth
        if from_depth >= to_depth:
            result.add_error(
                f"From_Depth ({from_depth}) must be less than To_Depth ({to_depth})",
                row_index=idx,
                column='From_Depth' if from_depth >= to_depth else 'To_Depth',
                value=from_depth if from_depth >= to_depth else to_depth
            )
        
        # Check for negative depths
        if from_depth < 0 or to_depth < 0:
            result.add_error(
                f"Negative depth value",
                row_index=idx,
                column='From_Depth' if from_depth < 0 else 'To_Depth',
                value=from_depth if from_depth < 0 else to_depth
            )
    
    # Check for gaps and overlaps between rows
    for i in range(len(df) - 1):
        current_to = df.iloc[i]['To_Depth']
        next_from = df.iloc[i + 1]['From_Depth']
        
        # Check for gap
        if abs(current_to - next_from) > 0.001:  # Small tolerance for floating point
            gap_size = next_from - current_to
            if gap_size > 0:
                result.add_error(
                    f"Gap of {gap_size:.3f}m between rows {i} and {i+1}",
                    row_index=i,
                    column='To_Depth',
                    value=current_to
                )
            else:  # Overlap
                overlap_size = current_to - next_from
                result.add_error(
                    f"Overlap of {overlap_size:.3f}m between rows {i} and {i+1}",
                    row_index=i,
                    column='To_Depth',
                    value=current_to
                )
    
    # Check total depth consistency
    if total_depth is not None and len(df) > 0:
        last_to_depth = df.iloc[-1]['To_Depth']
        if abs(last_to_depth - total_depth) > 0.001:  # Small tolerance
            diff = total_depth - last_to_depth
            result.add_warning(
                f"Last row To_Depth ({last_to_depth:.3f}) doesn't match header TD ({total_depth:.3f}), difference: {diff:.3f}m",
                row_index=len(df) - 1,
                column='To_Depth',
                value=last_to_depth
            )
    
    # Check for duplicate depth ranges
    depth_ranges = list(zip(df['From_Depth'], df['To_Depth']))
    seen_ranges = set()
    for idx, (f, t) in enumerate(depth_ranges):
        range_str = f"{f:.3f}-{t:.3f}"
        if range_str in seen_ranges:
            result.add_warning(
                f"Duplicate depth range: {range_str}",
                row_index=idx
            )
        seen_ranges.add(range_str)
    
    # Check thickness calculation if Thickness column exists
    if 'Thickness' in df.columns:
        for idx, row in df.iterrows():
            calculated = row['To_Depth'] - row['From_Depth']
            stored = row['Thickness']
            if pd.notna(stored) and abs(calculated - stored) > 0.001:
                result.add_warning(
                    f"Thickness mismatch: calculated {calculated:.3f}, stored {stored:.3f}",
                    row_index=idx,
                    column='Thickness',
                    value=stored
                )
    
    return result


def validate_dictionary_codes(dataframe: pd.DataFrame, 
                             dictionary_manager: Any,
                             code_columns: Dict[str, str]) -> ValidationResult:
    """
    Validate that codes in the dataframe exist in the dictionaries.
    
    Args:
        dataframe: DataFrame containing code columns
        dictionary_manager: DictionaryManager instance
        code_columns: Dict mapping column names to dictionary categories
        
    Returns:
        ValidationResult object containing validation issues
    """
    result = ValidationResult()
    
    if not dictionary_manager or not dictionary_manager.is_loaded:
        result.add_warning("Dictionary manager not loaded, skipping code validation")
        return result
    
    for column, category in code_columns.items():
        if column not in dataframe.columns:
            continue
        
        valid_codes = {code for code, _ in dictionary_manager.get_codes_for_category(category)}
        
        for idx, value in dataframe[column].items():
            if pd.isna(value):
                continue
            
            code_str = str(value).strip()
            if code_str and code_str not in valid_codes:
                result.add_warning(
                    f"Invalid {category} code: {code_str}",
                    row_index=idx,
                    column=column,
                    value=code_str
                )
    
    return result


class RealTimeValidator:
    """
    Real-time validator that can be connected to table models.
    """
    
    def __init__(self, dictionary_manager: Optional[Any] = None):
        self.dictionary_manager = dictionary_manager
        self.code_columns = {
            'LITHOLOGY_CODE': 'Litho_Type',
            'lithology_qualifier': 'Litho_Qual',
            'shade': 'Shade',
            'hue': 'Hue',
            'colour': 'Colour',
            'weathering': 'Weathering',
            'estimated_strength': 'Est_Strength',
            'inter_relationship': 'Litho_Interrel',
            'bed_spacing': 'Bed_Spacing'
        }
    
    def validate_dataframe(self, dataframe: pd.DataFrame, 
                          total_depth: Optional[float] = None) -> ValidationResult:
        """
        Comprehensive validation of dataframe.
        
        Args:
            dataframe: DataFrame to validate
            total_depth: Optional total depth from header
            
        Returns:
            Combined validation result
        """
        result = validate_hole(dataframe, total_depth)
        
        # Add dictionary validation if manager is available
        if self.dictionary_manager and self.dictionary_manager.is_loaded:
            dict_result = validate_dictionary_codes(
                dataframe, self.dictionary_manager, self.code_columns
            )
            for issue in dict_result.issues:
                result.add_issue(issue)
        
        return result
    
    def get_validation_summary(self, result: ValidationResult) -> str:
        """
        Get a summary string for display in status bar.
        
        Args:
            result: ValidationResult object
            
        Returns:
            Summary string
        """
        errors = result.get_errors()
        warnings = result.get_warnings()
        
        if not errors and not warnings:
            return "✓ Valid"
        
        summary_parts = []
        if errors:
            summary_parts.append(f"{len(errors)} error(s)")
        if warnings:
            summary_parts.append(f"{len(warnings)} warning(s)")
        
        return "⚠ " + ", ".join(summary_parts)