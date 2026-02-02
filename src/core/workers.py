"""
Worker classes for background operations to prevent UI freezing.
"""
import traceback
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import lasio

from .validation import validate_hole, ValidationResult


class LASLoaderWorker(QObject):
    """
    Worker for loading LAS files in background thread.
    """
    # Signals for communication with main thread
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(pd.DataFrame, dict, str)  # dataframe, metadata, file_path
    error = pyqtSignal(str, str)  # error message, file_path
    
    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        """Load LAS file in background thread."""
        try:
            self.progress.emit(0, f"Opening LAS file: {self.file_path}")
            
            # Read LAS file
            las = lasio.read(self.file_path)
            self.progress.emit(30, "Parsing LAS data...")
            
            # Convert to DataFrame
            df = las.df()
            df.reset_index(inplace=True)
            
            # Extract metadata
            metadata = {
                'well': str(las.well.WELL.value) if hasattr(las.well, 'WELL') else '',
                'company': str(las.well.COMP.value) if hasattr(las.well, 'COMP') else '',
                'field': str(las.well.FLD.value) if hasattr(las.well, 'FLD') else '',
                'location': str(las.well.LOC.value) if hasattr(las.well, 'LOC') else '',
                'state': str(las.well.STAT.value) if hasattr(las.well, 'STAT') else '',
                'country': str(las.well.CNTRY.value) if hasattr(las.well, 'CNTRY') else '',
                'service': str(las.well.SRVC.value) if hasattr(las.well, 'SRVC') else '',
                'date': str(las.well.DATE.value) if hasattr(las.well, 'DATE') else '',
                'uwi': str(las.well.UWI.value) if hasattr(las.well, 'UWI') else '',
                'api': str(las.well.API.value) if hasattr(las.well, 'API') else '',
            }
            
            # Try to extract coordinates from header
            coordinates = {}
            if hasattr(las.well, 'X'):
                coordinates['easting'] = float(las.well.X.value)
            if hasattr(las.well, 'Y'):
                coordinates['northing'] = float(las.well.Y.value)
            if hasattr(las.well, 'LATI'):
                coordinates['latitude'] = float(las.well.LATI.value)
            if hasattr(las.well, 'LONG'):
                coordinates['longitude'] = float(las.well.LONG.value)
            
            metadata['coordinates'] = coordinates
            
            self.progress.emit(70, "Processing curve data...")
            
            # Add depth column if not present
            if 'DEPTH' not in df.columns and len(df.columns) > 0:
                # Use first column as depth if it's numeric
                first_col = df.columns[0]
                if pd.api.types.is_numeric_dtype(df[first_col]):
                    df = df.rename(columns={first_col: 'DEPTH'})
            
            self.progress.emit(100, "LAS file loaded successfully")
            self.finished.emit(df, metadata, self.file_path)
            
        except Exception as e:
            error_msg = f"Error loading LAS file: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg, self.file_path)


class ValidationWorker(QObject):
    """
    Worker for running validation in background thread.
    """
    # Signals for communication with main thread
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(ValidationResult)  # validation result
    error = pyqtSignal(str)  # error message
    
    def __init__(self, dataframe: pd.DataFrame, total_depth: Optional[float] = None):
        super().__init__()
        self.dataframe = dataframe.copy()
        self.total_depth = total_depth
    
    def run(self):
        """Run validation in background thread."""
        try:
            self.progress.emit(0, "Starting validation...")
            
            # Validate the dataframe
            result = validate_hole(self.dataframe, self.total_depth)
            
            self.progress.emit(100, "Validation completed")
            self.finished.emit(result)
            
        except Exception as e:
            error_msg = f"Error during validation: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class MapDataWorker(QObject):
    """
    Worker for processing map data in background.
    """
    # Signals for communication with main thread
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(list, dict)  # processed data, metadata
    error = pyqtSignal(str)  # error message
    
    def __init__(self, file_paths: List[str]):
        super().__init__()
        self.file_paths = file_paths
    
    def run(self):
        """Process map data in background thread."""
        try:
            processed_data = []
            metadata = {'total_files': len(self.file_paths), 'processed_files': 0}
            
            for i, file_path in enumerate(self.file_paths):
                progress_pct = int((i / len(self.file_paths)) * 100)
                self.progress.emit(progress_pct, f"Processing {file_path}...")
                
                try:
                    if file_path.lower().endswith('.las'):
                        # Load LAS file
                        las = lasio.read(file_path)
                        df = las.df()
                        df.reset_index(inplace=True)
                        
                        # Extract coordinates
                        coords = {}
                        if hasattr(las.well, 'X'):
                            coords['easting'] = float(las.well.X.value)
                        if hasattr(las.well, 'Y'):
                            coords['northing'] = float(las.well.Y.value)
                        if hasattr(las.well, 'LATI'):
                            coords['latitude'] = float(las.well.LATI.value)
                        if hasattr(las.well, 'LONG'):
                            coords['longitude'] = float(las.well.LONG.value)
                        
                        # Extract well name
                        well_name = str(las.well.WELL.value) if hasattr(las.well, 'WELL') else file_path
                        
                        processed_data.append({
                            'file_path': file_path,
                            'well_name': well_name,
                            'coordinates': coords,
                            'data_type': 'las'
                        })
                        
                    elif file_path.lower().endswith('.csv'):
                        # Load CSV file
                        df = pd.read_csv(file_path)
                        
                        # Try to extract coordinates from header or first row
                        coords = {}
                        if 'Easting' in df.columns and 'Northing' in df.columns:
                            coords['easting'] = float(df['Easting'].iloc[0])
                            coords['northing'] = float(df['Northing'].iloc[0])
                        elif 'X' in df.columns and 'Y' in df.columns:
                            coords['easting'] = float(df['X'].iloc[0])
                            coords['northing'] = float(df['Y'].iloc[0])
                        
                        processed_data.append({
                            'file_path': file_path,
                            'well_name': file_path,
                            'coordinates': coords,
                            'data_type': 'csv'
                        })
                    
                    metadata['processed_files'] = i + 1
                    
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
            
            self.progress.emit(100, "Map data processing completed")
            self.finished.emit(processed_data, metadata)
            
        except Exception as e:
            error_msg = f"Error processing map data: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)


class ValidationCache:
    """
    Simple cache for validation results to avoid recomputation.
    """
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get_key(self, dataframe: pd.DataFrame, total_depth: Optional[float] = None) -> str:
        """Generate cache key from dataframe and total depth."""
        # Create a hash from dataframe content and total depth
        data_hash = hash(pd.util.hash_pandas_object(dataframe).sum())
        key = f"{data_hash}_{total_depth}"
        return key
    
    def get(self, dataframe: pd.DataFrame, total_depth: Optional[float] = None) -> Optional[ValidationResult]:
        """Get cached validation result."""
        key = self.get_key(dataframe, total_depth)
        if key in self.cache:
            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, dataframe: pd.DataFrame, result: ValidationResult, total_depth: Optional[float] = None):
        """Cache validation result."""
        key = self.get_key(dataframe, total_depth)
        
        # Remove oldest entry if cache is full
        if len(self.cache) >= self.max_size and self.access_order:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        # Add new entry
        self.cache[key] = result
        self.access_order.append(key)
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()