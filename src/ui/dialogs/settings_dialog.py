from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTabWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QWidget, QLabel,
    QDoubleSpinBox, QCheckBox, QComboBox, QSpinBox, QFrame,
    QScrollArea, QGroupBox, QGridLayout, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Import widgets that might be needed
# Note: We'll need to handle imports for range visualizer and other custom widgets
# from ..widgets.enhanced_range_gap_visualizer import EnhancedRangeGapVisualizer

class SettingsDialog(QDialog):
    # Signal to notify MainWindow when settings are updated
    settings_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Earthworm Settings")
        self.setGeometry(100, 100, 1000, 700)  # Larger dialog to accommodate all controls
        
        # Store current settings passed from MainWindow
        self.current_settings = current_settings or {}
        
        # Store references to controls for later access
        self.controls = {}
        
        self.main_layout = QVBoxLayout(self)
        
        # Create tab widget for organization
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.lithology_tab = self.create_lithology_tab()
        self.display_tab = self.create_display_tab()
        self.analysis_tab = self.create_analysis_tab()
        self.file_tab = self.create_file_tab()
        self.range_tab = self.create_range_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.lithology_tab, "Lithology Rules")
        self.tab_widget.addTab(self.display_tab, "Display Settings")
        self.tab_widget.addTab(self.analysis_tab, "Analysis Settings")
        self.tab_widget.addTab(self.file_tab, "File Operations")
        self.tab_widget.addTab(self.range_tab, "Range Analysis")
        
        self.main_layout.addWidget(self.tab_widget)
        
        # Dialog buttons at bottom
        self.button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.apply_button = QPushButton("Apply")
        self.cancel_button = QPushButton("Cancel")
        
        self.button_layout.addStretch()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.apply_button)
        self.button_layout.addWidget(self.cancel_button)
        
        self.main_layout.addLayout(self.button_layout)
        
        # Connect signals
        self.ok_button.clicked.connect(self.on_ok)
        self.apply_button.clicked.connect(self.on_apply)
        self.cancel_button.clicked.connect(self.reject)
        
        # Load initial settings into controls
        self.load_settings()
    
    def create_lithology_tab(self):
        """Create the lithology rules tab with table and controls."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Table for lithology rules
        self.rulesTable = QTableWidget()
        self.rulesTable.setColumnCount(6)
        self.rulesTable.setHorizontalHeaderLabels([
            "Lithology Name", "2-Letter Code", "Gamma Min", "Gamma Max", 
            "Density Min", "Density Max"
        ])
        self.rulesTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.rulesTable)
        
        # Buttons for adding/removing rules
        button_layout = QHBoxLayout()
        self.addRuleButton = QPushButton("Add Rule")
        self.removeRuleButton = QPushButton("Remove Rule")
        button_layout.addWidget(self.addRuleButton)
        button_layout.addWidget(self.removeRuleButton)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Connect signals
        self.addRuleButton.clicked.connect(self.add_rule)
        self.removeRuleButton.clicked.connect(self.remove_rule)
        
        return tab
    
    def create_display_tab(self):
        """Create display settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Separator settings group
        separator_group = QGroupBox("Stratigraphic Column Separators")
        separator_layout = QVBoxLayout(separator_group)
        
        # Separator thickness
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel("Separator Line Thickness:"))
        self.separatorThicknessSpinBox = QDoubleSpinBox()
        self.separatorThicknessSpinBox.setRange(0.0, 5.0)
        self.separatorThicknessSpinBox.setSingleStep(0.1)
        thickness_layout.addWidget(self.separatorThicknessSpinBox)
        thickness_layout.addStretch()
        separator_layout.addLayout(thickness_layout)
        
        # Draw separators checkbox
        self.drawSeparatorsCheckBox = QCheckBox("Draw Separator Lines")
        separator_layout.addWidget(self.drawSeparatorsCheckBox)
        
        layout.addWidget(separator_group)
        
        # Curve display settings group
        curve_group = QGroupBox("Curve Display")
        curve_layout = QVBoxLayout(curve_group)
        
        # Curve thickness
        curve_thickness_layout = QHBoxLayout()
        curve_thickness_layout.addWidget(QLabel("Curve Line Thickness:"))
        self.curveThicknessSpinBox = QDoubleSpinBox()
        self.curveThicknessSpinBox.setRange(0.1, 5.0)
        self.curveThicknessSpinBox.setSingleStep(0.1)
        curve_thickness_layout.addWidget(self.curveThicknessSpinBox)
        curve_thickness_layout.addStretch()
        curve_layout.addLayout(curve_thickness_layout)
        
        # Curve inversion checkboxes
        self.invertGammaCheckBox = QCheckBox("Invert Gamma Curve")
        self.invertShortSpaceDensityCheckBox = QCheckBox("Invert Short Space Density")
        self.invertLongSpaceDensityCheckBox = QCheckBox("Invert Long Space Density")
        
        curve_layout.addWidget(self.invertGammaCheckBox)
        curve_layout.addWidget(self.invertShortSpaceDensityCheckBox)
        curve_layout.addWidget(self.invertLongSpaceDensityCheckBox)
        
        layout.addWidget(curve_group)
        
        layout.addStretch()
        return tab
    
    def create_analysis_tab(self):
        """Create analysis settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # General analysis settings group
        general_group = QGroupBox("General Analysis Settings")
        general_layout = QVBoxLayout(general_group)
        
        self.useResearchedDefaultsCheckBox = QCheckBox("Apply Researched Defaults for Missing Ranges")
        self.mergeThinUnitsCheckBox = QCheckBox("Merge thin lithology units (< 5cm)")
        self.smartInterbeddingCheckBox = QCheckBox("Smart Interbedding")
        self.fallbackClassificationCheckBox = QCheckBox("Enable Fallback Classification")
        self.fallbackClassificationCheckBox.setToolTip("Apply fallback classification to reduce 'NL' (Not Logged) results")
        
        general_layout.addWidget(self.useResearchedDefaultsCheckBox)
        general_layout.addWidget(self.mergeThinUnitsCheckBox)
        general_layout.addWidget(self.smartInterbeddingCheckBox)
        general_layout.addWidget(self.fallbackClassificationCheckBox)
        
        layout.addWidget(general_group)
        
        # Smart interbedding parameters group
        interbedding_group = QGroupBox("Smart Interbedding Parameters")
        interbedding_layout = QGridLayout(interbedding_group)
        
        interbedding_layout.addWidget(QLabel("Max Sequence Length:"), 0, 0)
        self.smartInterbeddingMaxSequenceSpinBox = QSpinBox()
        self.smartInterbeddingMaxSequenceSpinBox.setRange(5, 50)
        interbedding_layout.addWidget(self.smartInterbeddingMaxSequenceSpinBox, 0, 1)
        
        interbedding_layout.addWidget(QLabel("Thick Unit Threshold (m):"), 1, 0)
        self.smartInterbeddingThickUnitSpinBox = QDoubleSpinBox()
        self.smartInterbeddingThickUnitSpinBox.setRange(0.1, 5.0)
        self.smartInterbeddingThickUnitSpinBox.setSingleStep(0.1)
        interbedding_layout.addWidget(self.smartInterbeddingThickUnitSpinBox, 1, 1)
        
        interbedding_layout.setColumnStretch(2, 1)
        layout.addWidget(interbedding_group)
        
        # Analysis method
        method_group = QGroupBox("Analysis Method")
        method_layout = QHBoxLayout(method_group)
        method_layout.addWidget(QLabel("Analysis Method:"))
        self.analysisMethodComboBox = QComboBox()
        self.analysisMethodComboBox.addItems(["Standard", "Simple"])
        method_layout.addWidget(self.analysisMethodComboBox)
        method_layout.addStretch()
        layout.addWidget(method_group)
        
        layout.addStretch()
        return tab
    
    def create_file_tab(self):
        """Create file operations tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File operations group
        file_group = QGroupBox("Settings File Operations")
        file_layout = QVBoxLayout(file_group)
        
        # Buttons for file operations
        self.saveAsSettingsButton = QPushButton("Save Settings As...")
        self.updateSettingsButton = QPushButton("Update Settings")
        self.loadSettingsButton = QPushButton("Load Settings...")
        self.researchedDefaultsButton = QPushButton("Researched Defaults...")
        self.exportLithologyReportButton = QPushButton("Export Lithology Report")
        
        file_layout.addWidget(self.saveAsSettingsButton)
        file_layout.addWidget(self.updateSettingsButton)
        file_layout.addWidget(self.loadSettingsButton)
        file_layout.addWidget(self.researchedDefaultsButton)
        file_layout.addWidget(self.exportLithologyReportButton)
        
        layout.addWidget(file_group)
        
        # Connect signals (will be connected to parent methods)
        self.saveAsSettingsButton.clicked.connect(self.save_settings_as_file)
        self.loadSettingsButton.clicked.connect(self.load_settings_from_file)
        self.researchedDefaultsButton.clicked.connect(self.open_researched_defaults_dialog)
        self.exportLithologyReportButton.clicked.connect(self.export_lithology_report)
        
        layout.addStretch()
        return tab
    
    def create_range_tab(self):
        """Create range analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Range analysis group
        range_group = QGroupBox("Range Gap Analysis")
        range_layout = QVBoxLayout(range_group)
        
        range_layout.addWidget(QLabel("Analyze gaps and overlaps in lithology rule ranges"))
        
        # Placeholder for range visualizer
        # TODO: Import and add EnhancedRangeGapVisualizer
        range_layout.addWidget(QLabel("Range visualizer would appear here"))
        
        # Refresh button
        self.refreshRangeAnalysisButton = QPushButton("Refresh Range Analysis")
        range_layout.addWidget(self.refreshRangeAnalysisButton)
        
        layout.addWidget(range_group)
        
        layout.addStretch()
        return tab
    
    def load_settings(self):
        """Load current settings into dialog controls."""
        # This method should populate controls with values from self.current_settings
        # For now, implement basic loading
        pass
    
    def gather_settings(self):
        """Gather all settings from dialog controls into a dictionary."""
        settings = {}
        
        # Gather lithology rules from table
        rules = []
        for row_idx in range(self.rulesTable.rowCount()):
            rule = {}
            rule['name'] = self.rulesTable.item(row_idx, 0).text() if self.rulesTable.item(row_idx, 0) else ''
            rule['code'] = self.rulesTable.item(row_idx, 1).text() if self.rulesTable.item(row_idx, 1) else ''
            
            # Convert numeric fields
            try:
                rule['gamma_min'] = float(self.rulesTable.item(row_idx, 2).text()) if self.rulesTable.item(row_idx, 2) and self.rulesTable.item(row_idx, 2).text() else 0.0
            except ValueError:
                rule['gamma_min'] = 0.0
            try:
                rule['gamma_max'] = float(self.rulesTable.item(row_idx, 3).text()) if self.rulesTable.item(row_idx, 3) and self.rulesTable.item(row_idx, 3).text() else 0.0
            except ValueError:
                rule['gamma_max'] = 0.0
            try:
                rule['density_min'] = float(self.rulesTable.item(row_idx, 4).text()) if self.rulesTable.item(row_idx, 4) and self.rulesTable.item(row_idx, 4).text() else 0.0
            except ValueError:
                rule['density_min'] = 0.0
            try:
                rule['density_max'] = float(self.rulesTable.item(row_idx, 5).text()) if self.rulesTable.item(row_idx, 5) and self.rulesTable.item(row_idx, 5).text() else 0.0
            except ValueError:
                rule['density_max'] = 0.0
            
            rules.append(rule)
        settings['lithology_rules'] = rules
        
        # Gather display settings
        settings['separator_thickness'] = self.separatorThicknessSpinBox.value()
        settings['draw_separators'] = self.drawSeparatorsCheckBox.isChecked()
        settings['curve_thickness'] = self.curveThicknessSpinBox.value()
        settings['invert_gamma'] = self.invertGammaCheckBox.isChecked()
        settings['invert_short_space_density'] = self.invertShortSpaceDensityCheckBox.isChecked()
        settings['invert_long_space_density'] = self.invertLongSpaceDensityCheckBox.isChecked()
        
        # Gather analysis settings
        settings['use_researched_defaults'] = self.useResearchedDefaultsCheckBox.isChecked()
        settings['merge_thin_units'] = self.mergeThinUnitsCheckBox.isChecked()
        settings['smart_interbedding'] = self.smartInterbeddingCheckBox.isChecked()
        settings['fallback_classification'] = self.fallbackClassificationCheckBox.isChecked()
        settings['smart_interbedding_max_sequence_length'] = self.smartInterbeddingMaxSequenceSpinBox.value()
        settings['smart_interbedding_thick_unit_threshold'] = self.smartInterbeddingThickUnitSpinBox.value()
        settings['analysis_method'] = self.analysisMethodComboBox.currentText().lower()
        
        return settings
    
    def add_rule(self):
        """Add a new empty row to the lithology rules table."""
        row_position = self.rulesTable.rowCount()
        self.rulesTable.insertRow(row_position)
        # Pre-fill with empty QTableWidgetItems
        for col in range(self.rulesTable.columnCount()):
            self.rulesTable.setItem(row_position, col, QTableWidgetItem(""))
    
    def remove_rule(self):
        """Remove the currently selected row from the lithology rules table."""
        current_row = self.rulesTable.currentRow()
        if current_row >= 0:
            self.rulesTable.removeRow(current_row)
    
    def save_settings_as_file(self):
        """Open file dialog to save settings to a JSON file."""
        # This should delegate to parent MainWindow
        if self.parent():
            self.parent().save_settings_as_file()
    
    def load_settings_from_file(self):
        """Open file dialog to load settings from a JSON file."""
        # This should delegate to parent MainWindow
        if self.parent():
            self.parent().load_settings_from_file()
            # After loading, we should update dialog controls
            self.load_settings()
    
    def open_researched_defaults_dialog(self):
        """Open researched defaults dialog."""
        if self.parent():
            self.parent().open_researched_defaults_dialog()
    
    def export_lithology_report(self):
        """Export lithology report."""
        if self.parent():
            self.parent().export_lithology_report()
    
    def on_ok(self):
        """Handle OK button - apply settings and close dialog."""
        self.on_apply()
        self.accept()
    
    def on_apply(self):
        """Handle Apply button - apply settings without closing dialog."""
        settings = self.gather_settings()
        self.settings_updated.emit(settings)
        # Also notify parent if it has an update_settings method
        if self.parent() and hasattr(self.parent(), 'update_settings'):
            self.parent().update_settings(settings)
    
    def accept(self):
        """Override accept to ensure settings are saved."""
        super().accept()
    
    def reject(self):
        """Override reject to handle cancellation."""
        super().reject()