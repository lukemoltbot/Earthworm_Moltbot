"""
Curve Analysis Manager - Advanced analysis tools for geological curves.

Provides professional analysis features matching 1Point Desktop capabilities:
1. Statistical analysis (mean, min, max, std dev, percentiles)
2. Filtering and smoothing (moving average, Gaussian, median)
3. Curve comparison (cross-plotting, correlation)
4. Anomaly detection (statistical outliers, thresholds)
5. Depth range analysis (interval statistics)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from PyQt6.QtCore import QObject, pyqtSignal
import warnings

# Optional imports for advanced analysis
try:
    from scipy import signal
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Create dummy objects for type checking
    class DummyStats:
        def linregress(self, *args, **kwargs):
            raise ImportError("scipy.stats not available. Install with: pip install scipy")
        def skew(self, *args, **kwargs):
            raise ImportError("scipy.stats not available. Install with: pip install scipy")
        def kurtosis(self, *args, **kwargs):
            raise ImportError("scipy.stats not available. Install with: pip install scipy")
    
    class DummySignal:
        def savgol_filter(self, *args, **kwargs):
            raise ImportError("scipy.signal not available. Install with: pip install scipy")
    
    stats = DummyStats()
    signal = DummySignal()


class CurveAnalysisManager(QObject):
    """Manager for advanced curve analysis operations."""
    
    # Signals
    analysisComplete = pyqtSignal(str, dict)  # analysis_type, results
    analysisError = pyqtSignal(str)  # error_message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def analyze_statistics(self, data: pd.DataFrame, curve_names: List[str], 
                          depth_range: Optional[Tuple[float, float]] = None) -> Dict[str, Dict]:
        """
        Calculate comprehensive statistics for curves.
        
        Args:
            data: DataFrame with curve data
            curve_names: List of curve names to analyze
            depth_range: Optional (min_depth, max_depth) tuple
            
        Returns:
            Dictionary of statistics for each curve
        """
        results = {}
        
        for curve_name in curve_names:
            if curve_name not in data.columns:
                continue
                
            # Extract curve data
            curve_data = data[curve_name].values
            
            # Apply depth range filter if specified
            if depth_range and 'DEPTH' in data.columns:
                min_depth, max_depth = depth_range
                depth_mask = (data['DEPTH'] >= min_depth) & (data['DEPTH'] <= max_depth)
                curve_data = curve_data[depth_mask]
            
            # Remove NaN values
            valid_data = curve_data[~np.isnan(curve_data)]
            
            if len(valid_data) == 0:
                results[curve_name] = {'error': 'No valid data points'}
                continue
            
            # Calculate statistics
            stats_dict = {
                'count': len(valid_data),
                'mean': float(np.mean(valid_data)),
                'median': float(np.median(valid_data)),
                'min': float(np.min(valid_data)),
                'max': float(np.max(valid_data)),
                'std': float(np.std(valid_data)),
                'variance': float(np.var(valid_data)),
                'range': float(np.max(valid_data) - np.min(valid_data)),
                'percentile_10': float(np.percentile(valid_data, 10)),
                'percentile_25': float(np.percentile(valid_data, 25)),
                'percentile_50': float(np.percentile(valid_data, 50)),
                'percentile_75': float(np.percentile(valid_data, 75)),
                'percentile_90': float(np.percentile(valid_data, 90)),
            }
            
            # Add scipy-dependent statistics if available
            if SCIPY_AVAILABLE:
                stats_dict['skewness'] = float(stats.skew(valid_data))
                stats_dict['kurtosis'] = float(stats.kurtosis(valid_data))
            else:
                stats_dict['skewness'] = None
                stats_dict['kurtosis'] = None
            
            results[curve_name] = stats_dict
        
        self.analysisComplete.emit('statistics', results)
        return results
    
    def apply_filter(self, data: pd.Series, filter_type: str = 'moving_average', 
                    window_size: int = 5, **kwargs) -> pd.Series:
        """
        Apply filter to curve data.
        
        Args:
            data: Curve data series
            filter_type: Type of filter ('moving_average', 'gaussian', 'median', 'savitzky_golay')
            window_size: Filter window size
            **kwargs: Additional filter parameters
            
        Returns:
            Filtered data series
        """
        if len(data) < window_size:
            return data.copy()
        
        valid_data = data.copy()
        
        if filter_type == 'moving_average':
            # Simple moving average
            filtered = valid_data.rolling(window=window_size, center=True, min_periods=1).mean()
            
        elif filter_type == 'gaussian':
            # Gaussian filter
            sigma = kwargs.get('sigma', 1.0)
            filtered = valid_data.rolling(
                window=window_size, center=True, min_periods=1
            ).apply(lambda x: np.mean(x * np.exp(-0.5 * ((np.arange(len(x)) - (len(x)-1)/2)**2) / sigma**2)))
            
        elif filter_type == 'median':
            # Median filter
            filtered = valid_data.rolling(window=window_size, center=True, min_periods=1).median()
            
        elif filter_type == 'savitzky_golay':
            # Savitzky-Golay filter (requires scipy)
            if not SCIPY_AVAILABLE:
                self.analysisError.emit("Savitzky-Golay filter requires scipy. Install with: pip install scipy")
                return valid_data
            
            polyorder = kwargs.get('polyorder', 2)
            try:
                filtered = pd.Series(
                    signal.savgol_filter(valid_data.values, window_size, polyorder),
                    index=valid_data.index
                )
            except Exception as e:
                self.analysisError.emit(f"Savitzky-Golay filter error: {str(e)}")
                return valid_data
                
        else:
            self.analysisError.emit(f"Unknown filter type: {filter_type}")
            return valid_data
        
        # Preserve NaN values from original data
        filtered[data.isna()] = np.nan
        
        self.analysisComplete.emit('filter', {'filter_type': filter_type, 'window_size': window_size})
        return filtered
    
    def detect_anomalies(self, data: pd.Series, method: str = 'zscore', 
                        threshold: float = 3.0, **kwargs) -> pd.Series:
        """
        Detect anomalies in curve data.
        
        Args:
            data: Curve data series
            method: Detection method ('zscore', 'iqr', 'threshold')
            threshold: Detection threshold
            **kwargs: Additional parameters
            
        Returns:
            Boolean series indicating anomalies
        """
        valid_data = data.dropna()
        
        if len(valid_data) == 0:
            return pd.Series(False, index=data.index)
        
        if method == 'zscore':
            # Z-score method (requires scipy for stats.zscore)
            if SCIPY_AVAILABLE:
                z_scores = np.abs(stats.zscore(valid_data.values))
            else:
                # Manual z-score calculation
                mean = np.mean(valid_data.values)
                std = np.std(valid_data.values)
                if std > 0:
                    z_scores = np.abs((valid_data.values - mean) / std)
                else:
                    z_scores = np.zeros_like(valid_data.values)
            anomalies = z_scores > threshold
            
        elif method == 'iqr':
            # Interquartile Range method
            q1 = np.percentile(valid_data.values, 25)
            q3 = np.percentile(valid_data.values, 75)
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            anomalies = (valid_data.values < lower_bound) | (valid_data.values > upper_bound)
            
        elif method == 'threshold':
            # Simple threshold method
            lower_threshold = kwargs.get('lower_threshold', -np.inf)
            upper_threshold = kwargs.get('upper_threshold', np.inf)
            anomalies = (valid_data.values < lower_threshold) | (valid_data.values > upper_threshold)
            
        else:
            self.analysisError.emit(f"Unknown anomaly detection method: {method}")
            return pd.Series(False, index=data.index)
        
        # Create result series with same index as input
        result = pd.Series(False, index=data.index)
        result.loc[valid_data.index] = anomalies
        
        self.analysisComplete.emit('anomaly_detection', {
            'method': method, 
            'threshold': threshold,
            'anomaly_count': int(np.sum(anomalies))
        })
        
        return result
    
    def calculate_correlation(self, data: pd.DataFrame, curve_names: List[str]) -> pd.DataFrame:
        """
        Calculate correlation matrix between curves.
        
        Args:
            data: DataFrame with curve data
            curve_names: List of curve names
            
        Returns:
            Correlation matrix DataFrame
        """
        # Filter to valid curves
        valid_curves = [c for c in curve_names if c in data.columns]
        
        if len(valid_curves) < 2:
            self.analysisError.emit("Need at least 2 curves for correlation analysis")
            return pd.DataFrame()
        
        # Extract data and remove rows with any NaN
        curve_data = data[valid_curves].dropna()
        
        if len(curve_data) < 2:
            self.analysisError.emit("Insufficient valid data for correlation")
            return pd.DataFrame()
        
        # Calculate correlation matrix
        correlation_matrix = curve_data.corr()
        
        self.analysisComplete.emit('correlation', {
            'matrix': correlation_matrix.to_dict(),
            'curve_count': len(valid_curves)
        })
        
        return correlation_matrix
    
    def analyze_depth_intervals(self, data: pd.DataFrame, curve_name: str, 
                               intervals: List[Tuple[float, float]]) -> Dict[str, Dict]:
        """
        Analyze curve statistics within specific depth intervals.
        
        Args:
            data: DataFrame with curve and depth data
            curve_name: Name of curve to analyze
            intervals: List of (start_depth, end_depth) tuples
            
        Returns:
            Dictionary of statistics for each interval
        """
        if curve_name not in data.columns or 'DEPTH' not in data.columns:
            self.analysisError.emit(f"Missing required columns: {curve_name} or DEPTH")
            return {}
        
        results = {}
        
        for i, (start_depth, end_depth) in enumerate(intervals):
            interval_key = f"{start_depth:.1f}-{end_depth:.1f}m"
            
            # Filter data for interval
            mask = (data['DEPTH'] >= start_depth) & (data['DEPTH'] <= end_depth)
            interval_data = data.loc[mask, curve_name].dropna()
            
            if len(interval_data) == 0:
                results[interval_key] = {'error': 'No data in interval'}
                continue
            
            # Calculate statistics
            stats_dict = {
                'depth_start': start_depth,
                'depth_end': end_depth,
                'thickness': end_depth - start_depth,
                'count': len(interval_data),
                'mean': float(np.mean(interval_data)),
                'median': float(np.median(interval_data)),
                'min': float(np.min(interval_data)),
                'max': float(np.max(interval_data)),
                'std': float(np.std(interval_data)),
                'data_density': len(interval_data) / (end_depth - start_depth) if end_depth > start_depth else 0
            }
            
            results[interval_key] = stats_dict
        
        self.analysisComplete.emit('depth_interval_analysis', {
            'curve_name': curve_name,
            'interval_count': len(intervals),
            'results': results
        })
        
        return results
    
    def create_cross_plot(self, data: pd.DataFrame, x_curve: str, y_curve: str,
                         depth_range: Optional[Tuple[float, float]] = None) -> Dict[str, Any]:
        """
        Create cross-plot analysis between two curves.
        
        Args:
            data: DataFrame with curve data
            x_curve: Name of X-axis curve
            y_curve: Name of Y-axis curve
            depth_range: Optional depth range filter
            
        Returns:
            Dictionary with cross-plot data and statistics
        """
        if x_curve not in data.columns or y_curve not in data.columns:
            self.analysisError.emit(f"Missing curves: {x_curve} or {y_curve}")
            return {}
        
        # Filter data
        plot_data = data[[x_curve, y_curve]].copy()
        
        if depth_range and 'DEPTH' in data.columns:
            min_depth, max_depth = depth_range
            depth_mask = (data['DEPTH'] >= min_depth) & (data['DEPTH'] <= max_depth)
            plot_data = plot_data[depth_mask]
        
        # Remove rows with NaN in either curve
        plot_data = plot_data.dropna()
        
        if len(plot_data) < 2:
            self.analysisError.emit("Insufficient data for cross-plot")
            return {}
        
        # Calculate cross-plot statistics
        x_values = plot_data[x_curve].values
        y_values = plot_data[y_curve].values
        
        # Calculate correlation
        correlation = float(np.corrcoef(x_values, y_values)[0, 1])
        
        results = {
            'x_curve': x_curve,
            'y_curve': y_curve,
            'data_points': len(plot_data),
            'correlation': correlation,
        }
        
        # Linear regression (requires scipy)
        if SCIPY_AVAILABLE:
            try:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
                results['regression'] = {
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'r_squared': float(r_value ** 2),
                    'p_value': float(p_value),
                    'std_error': float(std_err)
                }
            except Exception as e:
                results['regression'] = {'error': str(e)}
        else:
            results['regression'] = {'error': 'scipy not available for regression analysis'}
            'x_statistics': {
                'mean': float(np.mean(x_values)),
                'std': float(np.std(x_values)),
                'min': float(np.min(x_values)),
                'max': float(np.max(x_values))
            },
            'y_statistics': {
                'mean': float(np.mean(y_values)),
                'std': float(np.std(y_values)),
                'min': float(np.min(y_values)),
                'max': float(np.max(y_values))
            },
            'plot_data': {
                'x': x_values.tolist(),
                'y': y_values.tolist()
            }
        }
        
        self.analysisComplete.emit('cross_plot', results)
        return results
    
    def calculate_derivative(self, data: pd.Series, depth: pd.Series, 
                           method: str = 'central_difference') -> pd.Series:
        """
        Calculate derivative of curve with respect to depth.
        
        Args:
            data: Curve data series
            depth: Depth data series
            method: Differentiation method ('forward', 'backward', 'central_difference')
            
        Returns:
            Derivative series
        """
        if len(data) != len(depth):
            self.analysisError.emit("Data and depth series must have same length")
            return pd.Series()
        
        # Sort by depth
        sort_idx = np.argsort(depth.values)
        sorted_depth = depth.values[sort_idx]
        sorted_data = data.values[sort_idx]
        
        # Remove NaN values
        valid_mask = ~np.isnan(sorted_data) & ~np.isnan(sorted_depth)
        valid_depth = sorted_depth[valid_mask]
        valid_data = sorted_data[valid_mask]
        
        if len(valid_data) < 2:
            self.analysisError.emit("Insufficient valid data for derivative calculation")
            return pd.Series()
        
        # Calculate derivative
        if method == 'forward':
            derivative = np.diff(valid_data) / np.diff(valid_depth)
            # Pad with NaN to match length
            derivative = np.concatenate([derivative, [np.nan]])
            
        elif method == 'backward':
            derivative = np.diff(valid_data) / np.diff(valid_depth)
            # Pad with NaN to match length
            derivative = np.concatenate([[np.nan], derivative])
            
        elif method == 'central_difference':
            # Central difference (more accurate)
            derivative = np.zeros_like(valid_data)
            derivative[0] = (valid_data[1] - valid_data[0]) / (valid_depth[1] - valid_depth[0])
            derivative[-1] = (valid_data[-1] - valid_data[-2]) / (valid_depth[-1] - valid_depth[-2])
            
            for i in range(1, len(valid_data) - 1):
                derivative[i] = (valid_data[i+1] - valid_data[i-1]) / (valid_depth[i+1] - valid_depth[i-1])
                
        else:
            self.analysisError.emit(f"Unknown derivative method: {method}")
            return pd.Series()
        
        # Create result series with original indices
        result = pd.Series(np.nan, index=data.index)
        
        # Map back to original indices
        original_indices = np.arange(len(data))[sort_idx][valid_mask]
        for idx, deriv in zip(original_indices, derivative):
            result.iloc[idx] = deriv
        
        self.analysisComplete.emit('derivative', {'method': method})
        return result


# Factory function
def create_curve_analysis_manager(parent=None):
    """Create and initialize a curve analysis manager."""
    manager = CurveAnalysisManager(parent)
    return manager