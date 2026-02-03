"""
MapRenderWorker - Background worker for rendering map points.

This worker prepares data arrays for scatter plot rendering in a background thread
to prevent UI freezing when dealing with large datasets.
"""

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QObject, QMutex, QMutexLocker
from PyQt6.QtGui import QColor

class MapRenderWorker(QThread):
    """
    Worker thread for preparing map rendering data.
    
    Processes hole data in the background and emits signals with prepared
    data arrays for the scatter plot.
    """
    
    # Signals
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    batch_ready = pyqtSignal(list, list, list, list, list, list)  # eastings, northings, sizes, brushes, symbols, labels
    data_ready = pyqtSignal(list, list, list, list, list, list)  # Same as batch_ready, but for complete dataset
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, hole_data, selected_holes, color_by, point_size, selected_point_size, 
                 point_color, selected_point_color, batch_size=50):
        """
        Initialize the worker.
        
        Args:
            hole_data: Dict of hole data (file_path -> hole_info)
            selected_holes: Set of selected hole file paths
            color_by: Color coding setting ("Default", "Total Depth", etc.)
            point_size: Default point size
            selected_point_size: Selected point size
            point_color: Default point color (QColor)
            selected_point_color: Selected point color (QColor)
            batch_size: Number of points to process per batch (for progressive loading)
        """
        super().__init__()
        
        # Make copies of data for thread safety
        self.hole_data = dict(hole_data)  # Shallow copy
        self.selected_holes = set(selected_holes)  # Copy
        self.color_by = color_by
        self.point_size = point_size
        self.selected_point_size = selected_point_size
        self.point_color = point_color
        self.selected_point_color = selected_point_color
        self.batch_size = batch_size
        
        # Accumulated data for progressive rendering
        self.accumulated_data = {
            'eastings': [],
            'northings': [],
            'sizes': [],
            'brushes': [],
            'symbols': [],
            'labels': []
        }
        
        # Thread control
        self._mutex = QMutex()
        self._cancelled = False
        
    def run(self):
        """Main worker execution method."""
        try:
            # Check if we should use progressive loading
            total_holes = len(self.hole_data)
            if total_holes == 0:
                self.data_ready.emit([], [], [], [], [], [])
                self.finished.emit()
                return
                
            if total_holes <= self.batch_size:
                # Small dataset - process all at once
                self._process_batch(list(self.hole_data.items()), 0, total_holes, is_final=True)
            else:
                # Large dataset - process in batches
                hole_items = list(self.hole_data.items())
                num_batches = (total_holes + self.batch_size - 1) // self.batch_size
                
                for batch_idx in range(num_batches):
                    # Check for cancellation
                    with QMutexLocker(self._mutex):
                        if self._cancelled:
                            return
                    
                    # Calculate batch range
                    start_idx = batch_idx * self.batch_size
                    end_idx = min((batch_idx + 1) * self.batch_size, total_holes)
                    is_final = (batch_idx == num_batches - 1)
                    
                    # Process batch
                    self._process_batch(hole_items, start_idx, end_idx, is_final)
                    
                    # Emit progress
                    progress_pct = int((batch_idx + 1) * 100 / num_batches)
                    self.progress.emit(progress_pct)
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Error in map render worker: {str(e)}")
            self.finished.emit()
    
    def _process_batch(self, hole_items, start_idx, end_idx, is_final=False):
        """
        Process a batch of hole items.
        
        Args:
            hole_items: List of (file_path, hole_info) tuples
            start_idx: Start index in the list
            end_idx: End index (exclusive)
            is_final: Whether this is the final batch
        """
        # Prepare data arrays for this batch
        eastings = []
        northings = []
        sizes = []
        brushes = []
        symbols = []
        labels = []
        
        for i in range(start_idx, end_idx):
            file_path, hole_info = hole_items[i]
            
            easting = hole_info.get('easting', 0)
            northing = hole_info.get('northing', 0)
            
            # Skip holes without coordinates
            if easting is None or northing is None:
                continue
                
            eastings.append(easting)
            northings.append(northing)
            labels.append(hole_info.get('hole_id', file_path))
            
            # Determine point color based on selection and color_by setting
            if file_path in self.selected_holes:
                sizes.append(self.selected_point_size)
                brush_color = self.selected_point_color
                symbols.append('o')  # Circle
            else:
                sizes.append(self.point_size)
                brush_color = self._get_color_for_hole(hole_info, self.color_by)
                symbols.append('o')  # Circle
                
            brushes.append(self._qcolor_to_tuple(brush_color))
        
        # Accumulate data
        self.accumulated_data['eastings'].extend(eastings)
        self.accumulated_data['northings'].extend(northings)
        self.accumulated_data['sizes'].extend(sizes)
        self.accumulated_data['brushes'].extend(brushes)
        self.accumulated_data['symbols'].extend(symbols)
        self.accumulated_data['labels'].extend(labels)
        
        # Emit signal with batch data
        if is_final:
            # Emit full accumulated data
            self.data_ready.emit(
                self.accumulated_data['eastings'],
                self.accumulated_data['northings'],
                self.accumulated_data['sizes'],
                self.accumulated_data['brushes'],
                self.accumulated_data['symbols'],
                self.accumulated_data['labels']
            )
        else:
            # Emit just this batch's data for progressive rendering
            self.batch_ready.emit(eastings, northings, sizes, brushes, symbols, labels)
    
    def _get_color_for_hole(self, hole_info, color_by):
        """Get color for a hole based on the color_by setting."""
        if color_by == "Default":
            return self.point_color
        elif color_by == "Total Depth":
            return self._get_color_by_depth(hole_info.get('total_depth'))
        elif color_by == "Hole Count":
            # Color by sequence - just for demonstration
            return QColor(70, 130, 180)  # Steel blue
        elif color_by == "File Type":
            # Color by file extension - just for demonstration
            return QColor(100, 149, 237)  # Cornflower blue
        else:
            return self.point_color
    
    def _get_color_by_depth(self, depth):
        """Get color based on total depth."""
        if depth is None:
            return self.point_color
            
        # Color gradient from light blue (shallow) to dark blue (deep)
        # Normalize depth to 0-1 range (assuming max depth ~500m)
        normalized = min(depth / 500.0, 1.0)
        
        # Interpolate between light blue and dark blue
        r = int(70 + normalized * 30)  # 70-100
        g = int(130 + normalized * 50)  # 130-180
        b = int(180 + normalized * 75)  # 180-255
        
        return QColor(r, g, b)
    
    def _qcolor_to_tuple(self, color):
        """Convert QColor to (r, g, b, a) tuple for pyqtgraph."""
        return (color.red(), color.green(), color.blue(), color.alpha())
    
    def cancel(self):
        """Cancel the worker execution."""
        with QMutexLocker(self._mutex):
            self._cancelled = True
    
    def is_cancelled(self):
        """Check if the worker has been cancelled."""
        with QMutexLocker(self._mutex):
            return self._cancelled