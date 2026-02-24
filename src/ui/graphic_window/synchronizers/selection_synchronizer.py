"""
SelectionSynchronizer - Handles selection synchronization across components.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, List, Tuple
from src.ui.graphic_window.state.depth_range import DepthRange


class SelectionSynchronizer(QObject):
    """
    Handles selection synchronization across all graphic window components.
    
    Responsibilities:
    1. Validate selections (from_depth < to_depth)
    2. Handle multi-select mode
    3. Coordinate selection across components
    4. Manage selection modes (single, range, multiple)
    """
    
    # Signals
    selectionChanged = pyqtSignal(object)  # DepthRange or list of DepthRange or None
    selectionValidated = pyqtSignal(bool, str)  # (is_valid, message)
    
    def __init__(self):
        super().__init__()
        
        self.selection_mode = "single"  # "single", "range", "multiple"
        self.current_selection: Optional[DepthRange] = None
        self.multiple_selections: List[DepthRange] = []
        
        # Selection constraints
        self.min_selection_thickness = 0.01  # Minimum 1cm
        self.max_selection_thickness = 1000.0  # Maximum 1000m
    
    def set_selection(self, from_depth: float, to_depth: float) -> Tuple[bool, str]:
        """
        Set a selection range.
        
        Args:
            from_depth: Start depth
            to_depth: End depth
            
        Returns:
            Tuple of (success, message)
        """
        # Ensure from_depth < to_depth
        if from_depth > to_depth:
            from_depth, to_depth = to_depth, from_depth
        
        # Validate thickness
        thickness = to_depth - from_depth
        if thickness < self.min_selection_thickness:
            msg = f"Selection too thin (min {self.min_selection_thickness}m)"
            self.selectionValidated.emit(False, msg)
            return False, msg
        
        if thickness > self.max_selection_thickness:
            msg = f"Selection too thick (max {self.max_selection_thickness}m)"
            self.selectionValidated.emit(False, msg)
            return False, msg
        
        # Create selection
        selection = DepthRange(from_depth, to_depth)
        
        # Handle based on selection mode
        if self.selection_mode == "single":
            self.current_selection = selection
            self.multiple_selections = []
            self.selectionChanged.emit(selection)
            
        elif self.selection_mode == "range":
            # In range mode, we keep the previous selection and extend to new
            if self.current_selection is None:
                self.current_selection = selection
            else:
                # Combine ranges
                combined_from = min(self.current_selection.from_depth, from_depth)
                combined_to = max(self.current_selection.to_depth, to_depth)
                self.current_selection = DepthRange(combined_from, combined_to)
            
            self.selectionChanged.emit(self.current_selection)
            
        elif self.selection_mode == "multiple":
            # Add to multiple selections
            self.multiple_selections.append(selection)
            self.selectionChanged.emit(self.multiple_selections.copy())
        
        msg = f"Selected {from_depth:.2f}m to {to_depth:.2f}m ({thickness:.2f}m)"
        self.selectionValidated.emit(True, msg)
        return True, msg
    
    def clear_selection(self):
        """Clear all selections."""
        self.current_selection = None
        self.multiple_selections = []
        self.selectionChanged.emit(None)
        self.selectionValidated.emit(True, "Selection cleared")
    
    def get_selection(self) -> Optional[DepthRange]:
        """Get the current selection (for single/range mode)."""
        return self.current_selection
    
    def get_all_selections(self) -> List[DepthRange]:
        """Get all selections (for multiple mode)."""
        if self.selection_mode == "multiple":
            return self.multiple_selections.copy()
        elif self.current_selection is not None:
            return [self.current_selection]
        else:
            return []
    
    def set_selection_mode(self, mode: str):
        """
        Set selection mode.
        
        Args:
            mode: "single", "range", or "multiple"
        """
        valid_modes = ["single", "range", "multiple"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid selection mode: {mode}. Must be one of {valid_modes}")
        
        self.selection_mode = mode
        
        # Clear selections when changing modes (except single->range)
        if mode == "single":
            self.multiple_selections = []
        elif mode == "range":
            # Keep current selection
            pass
        elif mode == "multiple":
            self.current_selection = None
    
    def toggle_selection_mode(self):
        """Cycle through selection modes."""
        modes = ["single", "range", "multiple"]
        current_index = modes.index(self.selection_mode)
        next_index = (current_index + 1) % len(modes)
        self.set_selection_mode(modes[next_index])
    
    def is_depth_selected(self, depth: float) -> bool:
        """Check if a depth is within any selection."""
        if self.selection_mode == "multiple":
            for selection in self.multiple_selections:
                if selection.contains_depth(depth):
                    return True
            return False
        elif self.current_selection is not None:
            return self.current_selection.contains_depth(depth)
        return False
    
    def get_selection_at_depth(self, depth: float) -> Optional[DepthRange]:
        """Get the selection that contains a depth."""
        if self.selection_mode == "multiple":
            for selection in self.multiple_selections:
                if selection.contains_depth(depth):
                    return selection
            return None
        elif self.current_selection is not None:
            if self.current_selection.contains_depth(depth):
                return self.current_selection
        return None
    
    def remove_selection(self, selection: DepthRange):
        """Remove a specific selection (for multiple mode)."""
        if self.selection_mode != "multiple":
            return False
        
        for i, sel in enumerate(self.multiple_selections):
            if (abs(sel.from_depth - selection.from_depth) < 0.001 and
                abs(sel.to_depth - selection.to_depth) < 0.001):
                self.multiple_selections.pop(i)
                self.selectionChanged.emit(self.multiple_selections.copy())
                return True
        
        return False
    
    def merge_selections(self):
        """Merge overlapping selections (for multiple mode)."""
        if self.selection_mode != "multiple" or len(self.multiple_selections) < 2:
            return
        
        # Sort by from_depth
        sorted_selections = sorted(self.multiple_selections, key=lambda s: s.from_depth)
        
        merged = []
        current = sorted_selections[0]
        
        for selection in sorted_selections[1:]:
            if selection.from_depth <= current.to_depth:
                # Overlap - merge
                current = DepthRange(
                    min(current.from_depth, selection.from_depth),
                    max(current.to_depth, selection.to_depth)
                )
            else:
                # No overlap - add current and start new
                merged.append(current)
                current = selection
        
        merged.append(current)
        self.multiple_selections = merged
        self.selectionChanged.emit(self.multiple_selections.copy())