"""
NL Review Dialog for Earthworm Moltbot
Shows all 'NL' (Not Logged) intervals with calculated statistics.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QGroupBox, QFormLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import pandas as pd
import numpy as np
import sys
import os

class NLReviewDialog(QDialog):
    """Dialog for reviewing NL (Not Logged) intervals with statistics."""
    
    def __init__(self, parent=None, main_window=None):
        """
        Initialize the NL Review Dialog.
        
        Args:
            parent: Parent widget
            main_window: Reference to main window (for accessing data)
        """
        super().__init__(parent)
        self.main_window = main_window
        self.nl_data = None
        self.nl_stats = None
        
        self.setWindowTitle("NL Intervals Review")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(700, 400)
        
        self.setup_ui()
        
        # Load NL data if main_window is available
        if self.main_window:
            self.load_nl_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title label
        title_label = QLabel("NL (Not Logged) Intervals Review")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Description label
        desc_label = QLabel("This dialog shows all intervals classified as 'NL' (Not Logged) with calculated statistics.")
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        
        # Statistics group box
        stats_group = QGroupBox("NL Interval Statistics")
        stats_layout = QFormLayout(stats_group)
        stats_layout.setSpacing(8)
        
        self.total_nl_label = QLabel("0")
        self.total_intervals_label = QLabel("0")
        self.mean_ss_label = QLabel("N/A")
        self.mean_ls_label = QLabel("N/A")
        self.mean_gr_label = QLabel("N/A")
        
        stats_layout.addRow("Total NL Rows:", self.total_nl_label)
        stats_layout.addRow("NL Intervals:", self.total_intervals_label)
        stats_layout.addRow("Mean SS (Short Space Density):", self.mean_ss_label)
        stats_layout.addRow("Mean LS (Long Space Density):", self.mean_ls_label)
        stats_layout.addRow("Mean GR (Gamma Ray):", self.mean_gr_label)
        
        main_layout.addWidget(stats_group)
        
        # Table for NL intervals
        table_label = QLabel("NL Intervals Detail:")
        main_layout.addWidget(table_label)
        
        self.nl_table = QTableWidget()
        self.nl_table.setColumnCount(7)
        self.nl_table.setHorizontalHeaderLabels([
            "Interval", "From Depth (m)", "To Depth (m)", 
            "Thickness (m)", "Mean SS", "Mean LS", "Mean GR"
        ])
        header = self.nl_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        self.nl_table.setAlternatingRowColors(True)
        main_layout.addWidget(self.nl_table)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.export_button = QPushButton("Export Report")
        self.export_button.setToolTip("Export NL analysis report to CSV file")
        self.export_button.clicked.connect(self.export_report)
        self.export_button.setEnabled(False)  # Disabled until data is loaded
        
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.setToolTip("Refresh NL data from current analysis")
        self.refresh_button.clicked.connect(self.refresh_data)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
    
    def load_nl_data(self):
        """Load NL data from the main window's current analysis."""
        if not self.main_window:
            QMessageBox.warning(self, "No Data", "No main window reference available.")
            return False
        
        try:
            # Get the current dataframe from main window
            # Try last_classified_dataframe first (after analysis), then dataframe (loaded data)
            df = None
            if hasattr(self.main_window, 'last_classified_dataframe') and self.main_window.last_classified_dataframe is not None:
                df = self.main_window.last_classified_dataframe
            elif hasattr(self.main_window, 'dataframe') and self.main_window.dataframe is not None:
                df = self.main_window.dataframe
            else:
                QMessageBox.information(self, "No Data", "No analysis data available. Please run analysis first.")
                return False
            
            # Check if lithology column exists
            lithology_col = None
            for col in ['Lithology', 'lithology', 'LITHOLOGY']:
                if col in df.columns:
                    lithology_col = col
                    break
            
            if not lithology_col:
                QMessageBox.warning(self, "Data Error", "No lithology column found in data.")
                return False
            
            # Get NL rows
            nl_mask = df[lithology_col] == 'NL'
            nl_df = df[nl_mask].copy()
            
            if len(nl_df) == 0:
                QMessageBox.information(self, "No NL Data", "No 'NL' (Not Logged) intervals found in current analysis.")
                self.nl_data = pd.DataFrame()
                self.nl_stats = {}
                self.update_display()
                return True
            
            # Get depth column
            depth_col = None
            for col in ['Depth', 'depth', 'DEPTH']:
                if col in df.columns:
                    depth_col = col
                    break
            
            if not depth_col:
                QMessageBox.warning(self, "Data Error", "No depth column found in data.")
                return False
            
            # Sort by depth
            nl_df = nl_df.sort_values(by=depth_col)
            
            # Identify NL intervals (continuous depth ranges)
            nl_intervals = []
            current_interval = None
            
            for idx, row in nl_df.iterrows():
                depth = row[depth_col]
                
                if current_interval is None:
                    # Start new interval
                    current_interval = {
                        'start_idx': idx,
                        'end_idx': idx,
                        'from_depth': depth,
                        'to_depth': depth,
                        'rows': [idx]
                    }
                else:
                    # Check if this row is continuous with current interval
                    # Assuming depth increments are consistent
                    prev_row = nl_df.loc[current_interval['end_idx']]
                    depth_diff = depth - prev_row[depth_col]
                    
                    # If depth difference is small (e.g., <= 0.1m), consider it continuous
                    if depth_diff <= 0.1:
                        # Continue current interval
                        current_interval['end_idx'] = idx
                        current_interval['to_depth'] = depth
                        current_interval['rows'].append(idx)
                    else:
                        # End current interval and start new one
                        nl_intervals.append(current_interval)
                        current_interval = {
                            'start_idx': idx,
                            'end_idx': idx,
                            'from_depth': depth,
                            'to_depth': depth,
                            'rows': [idx]
                        }
            
            # Add the last interval
            if current_interval is not None:
                nl_intervals.append(current_interval)
            
            # Calculate statistics for each interval
            interval_data = []
            all_ss_values = []
            all_ls_values = []
            all_gr_values = []
            
            for i, interval in enumerate(nl_intervals):
                interval_rows = nl_df.loc[interval['rows']]
                
                # Calculate means for SS, LS, GR
                ss_mean = self.calculate_mean(interval_rows, ['SS', 'ss', 'SHORT_SPACE', 'short_space_density'])
                ls_mean = self.calculate_mean(interval_rows, ['LS', 'ls', 'LONG_SPACE', 'long_space_density'])
                gr_mean = self.calculate_mean(interval_rows, ['GR', 'gr', 'GAMMA', 'gamma', 'GAMMA_RAY', 'gamma_ray'])
                
                interval_data.append({
                    'interval': i + 1,
                    'from_depth': interval['from_depth'],
                    'to_depth': interval['to_depth'],
                    'thickness': interval['to_depth'] - interval['from_depth'],
                    'mean_ss': ss_mean,
                    'mean_ls': ls_mean,
                    'mean_gr': gr_mean,
                    'row_indices': interval['rows']
                })
                
                # Collect values for overall statistics
                if not pd.isna(ss_mean):
                    all_ss_values.append(ss_mean)
                if not pd.isna(ls_mean):
                    all_ls_values.append(ls_mean)
                if not pd.isna(gr_mean):
                    all_gr_values.append(gr_mean)
            
            # Create DataFrame for intervals
            self.nl_data = pd.DataFrame(interval_data)
            
            # Calculate overall statistics
            self.nl_stats = {
                'total_nl_rows': len(nl_df),
                'total_intervals': len(nl_intervals),
                'mean_ss': np.mean(all_ss_values) if all_ss_values else np.nan,
                'mean_ls': np.mean(all_ls_values) if all_ls_values else np.nan,
                'mean_gr': np.mean(all_gr_values) if all_gr_values else np.nan
            }
            
            self.update_display()
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading NL data: {str(e)}")
            return False
    
    def calculate_mean(self, df, column_names):
        """Calculate mean for a column, trying multiple possible column names."""
        for col_name in column_names:
            if col_name in df.columns:
                values = df[col_name]
                # Filter out NaN values
                valid_values = values.dropna()
                if len(valid_values) > 0:
                    return valid_values.mean()
        return np.nan
    
    def update_display(self):
        """Update the display with loaded data."""
        # Update statistics labels
        if self.nl_stats:
            self.total_nl_label.setText(str(self.nl_stats['total_nl_rows']))
            self.total_intervals_label.setText(str(self.nl_stats['total_intervals']))
            
            # Format mean values
            ss_mean = self.nl_stats['mean_ss']
            ls_mean = self.nl_stats['mean_ls']
            gr_mean = self.nl_stats['mean_gr']
            
            self.mean_ss_label.setText(f"{ss_mean:.3f}" if not pd.isna(ss_mean) else "N/A")
            self.mean_ls_label.setText(f"{ls_mean:.3f}" if not pd.isna(ls_mean) else "N/A")
            self.mean_gr_label.setText(f"{gr_mean:.3f}" if not pd.isna(gr_mean) else "N/A")
        else:
            self.total_nl_label.setText("0")
            self.total_intervals_label.setText("0")
            self.mean_ss_label.setText("N/A")
            self.mean_ls_label.setText("N/A")
            self.mean_gr_label.setText("N/A")
        
        # Update table
        if self.nl_data is not None and len(self.nl_data) > 0:
            self.nl_table.setRowCount(len(self.nl_data))
            
            for i, row in self.nl_data.iterrows():
                # Interval number
                self.nl_table.setItem(i, 0, QTableWidgetItem(str(int(row['interval']))))
                
                # From depth
                self.nl_table.setItem(i, 1, QTableWidgetItem(f"{row['from_depth']:.3f}"))
                
                # To depth
                self.nl_table.setItem(i, 2, QTableWidgetItem(f"{row['to_depth']:.3f}"))
                
                # Thickness
                self.nl_table.setItem(i, 3, QTableWidgetItem(f"{row['thickness']:.3f}"))
                
                # Mean SS
                ss_val = row['mean_ss']
                self.nl_table.setItem(i, 4, QTableWidgetItem(f"{ss_val:.3f}" if not pd.isna(ss_val) else "N/A"))
                
                # Mean LS
                ls_val = row['mean_ls']
                self.nl_table.setItem(i, 5, QTableWidgetItem(f"{ls_val:.3f}" if not pd.isna(ls_val) else "N/A"))
                
                # Mean GR
                gr_val = row['mean_gr']
                self.nl_table.setItem(i, 6, QTableWidgetItem(f"{gr_val:.3f}" if not pd.isna(gr_val) else "N/A"))
            
            # Enable export button
            self.export_button.setEnabled(True)
        else:
            self.nl_table.setRowCount(0)
            self.export_button.setEnabled(False)
    
    def refresh_data(self):
        """Refresh NL data from current analysis."""
        if self.load_nl_data():
            QMessageBox.information(self, "Data Refreshed", "NL data has been refreshed from current analysis.")
    
    def export_report(self):
        """Export NL analysis report to CSV file."""
        if self.nl_data is None or len(self.nl_data) == 0:
            QMessageBox.warning(self, "No Data", "No NL data to export.")
            return
        
        # Get save file path
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export NL Analysis Report",
            "nl_analysis_report.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Create a comprehensive report
            report_data = []
            
            # Add header with overall statistics
            report_data.append(["NL (Not Logged) Analysis Report"])
            report_data.append([])
            report_data.append(["Overall Statistics:"])
            report_data.append(["Total NL Rows:", self.nl_stats['total_nl_rows']])
            report_data.append(["Total NL Intervals:", self.nl_stats['total_intervals']])
            report_data.append(["Mean SS (Short Space Density):", 
                              f"{self.nl_stats['mean_ss']:.3f}" if not pd.isna(self.nl_stats['mean_ss']) else "N/A"])
            report_data.append(["Mean LS (Long Space Density):", 
                              f"{self.nl_stats['mean_ls']:.3f}" if not pd.isna(self.nl_stats['mean_ls']) else "N/A"])
            report_data.append(["Mean GR (Gamma Ray):", 
                              f"{self.nl_stats['mean_gr']:.3f}" if not pd.isna(self.nl_stats['mean_gr']) else "N/A"])
            report_data.append([])
            report_data.append(["NL Interval Details:"])
            report_data.append([])
            
            # Add column headers
            report_data.append([
                "Interval", "From Depth (m)", "To Depth (m)", "Thickness (m)",
                "Mean SS", "Mean LS", "Mean GR"
            ])
            
            # Add interval data
            for _, row in self.nl_data.iterrows():
                report_data.append([
                    int(row['interval']),
                    f"{row['from_depth']:.3f}",
                    f"{row['to_depth']:.3f}",
                    f"{row['thickness']:.3f}",
                    f"{row['mean_ss']:.3f}" if not pd.isna(row['mean_ss']) else "N/A",
                    f"{row['mean_ls']:.3f}" if not pd.isna(row['mean_ls']) else "N/A",
                    f"{row['mean_gr']:.3f}" if not pd.isna(row['mean_gr']) else "N/A"
                ])
            
            # Write to CSV
            import csv
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(report_data)
            
            QMessageBox.information(self, "Export Successful", 
                                  f"NL analysis report exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", 
                               f"Error exporting report: {str(e)}")