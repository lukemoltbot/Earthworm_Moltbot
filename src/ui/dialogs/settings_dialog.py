from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTabWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QWidget, QLabel,
    QDoubleSpinBox, QCheckBox, QComboBox, QSpinBox, QFrame,
    QScrollArea, QGroupBox, QGridLayout, QFormLayout, QFileDialog, QMessageBox,
    QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# Import widgets that might be needed
# Note: We'll need to handle imports for range visualizer and other custom widgets
from ..widgets.enhanced_range_gap_visualizer import EnhancedRangeGapVisualizer
from ...utils.range_analyzer import RangeAnalyzer

class SettingsDialog(QDialog):
    # Signal to notify MainWindow when settings are updated
    settings_updated = pyqtSignal(dict)

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("Earthworm Settings")
        self.setGeometry(100, 100, 900, 650)  # Reasonable size for settings dialog
        self.setMinimumSize(800, 600)

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
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Create scroll area with vertical-only scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Force vertical-only scrolling
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

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

        # Set container as scroll widget
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        return tab

    def create_display_tab(self):
        """Create display settings tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Create scroll area with vertical-only scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Force vertical-only scrolling
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Separator settings group
        separator_group = QGroupBox("Stratigraphic Column Separators")
        separator_layout = QFormLayout(separator_group)
        separator_layout.setSpacing(8)
        separator_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Separator thickness
        self.separatorThicknessSpinBox = QDoubleSpinBox()
        self.separatorThicknessSpinBox.setRange(0.0, 5.0)
        self.separatorThicknessSpinBox.setSingleStep(0.1)
        self.separatorThicknessSpinBox.setMaximumWidth(100)
        separator_layout.addRow("Separator Line Thickness:", self.separatorThicknessSpinBox)

        # Draw separators checkbox
        self.drawSeparatorsCheckBox = QCheckBox("Draw Separator Lines")
        separator_layout.addRow(self.drawSeparatorsCheckBox)

        layout.addWidget(separator_group)

        # Curve display settings group
        curve_group = QGroupBox("Curve Display")
        curve_layout = QFormLayout(curve_group)
        curve_layout.setSpacing(8)
        curve_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Curve thickness
        self.curveThicknessSpinBox = QDoubleSpinBox()
        self.curveThicknessSpinBox.setRange(0.1, 5.0)
        self.curveThicknessSpinBox.setSingleStep(0.1)
        self.curveThicknessSpinBox.setMaximumWidth(100)
        curve_layout.addRow("Curve Line Thickness:", self.curveThicknessSpinBox)

        # Curve inversion checkboxes
        curve_inv_widget = QWidget()
        curve_inv_layout = QVBoxLayout(curve_inv_widget)
        curve_inv_layout.setSpacing(4)
        curve_inv_layout.setContentsMargins(0, 0, 0, 0)
        self.invertGammaCheckBox = QCheckBox("Invert Gamma Curve")
        self.invertShortSpaceDensityCheckBox = QCheckBox("Invert Short Space Density")
        self.invertLongSpaceDensityCheckBox = QCheckBox("Invert Long Space Density")
        curve_inv_layout.addWidget(self.invertGammaCheckBox)
        curve_inv_layout.addWidget(self.invertShortSpaceDensityCheckBox)
        curve_inv_layout.addWidget(self.invertLongSpaceDensityCheckBox)
        curve_layout.addRow("Curve Inversion:", curve_inv_widget)

        layout.addWidget(curve_group)

        # SVG Patterns group
        svg_group = QGroupBox("SVG Patterns")
        svg_layout = QVBoxLayout(svg_group)
        svg_layout.setSpacing(8)
        
        self.disableSvgCheckBox = QCheckBox("Disable SVG patterns (use solid colors only)")
        svg_layout.addWidget(self.disableSvgCheckBox)
        
        layout.addWidget(svg_group)

        layout.addStretch()

        # Set container as scroll widget
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        return tab

    def create_analysis_tab(self):
        """Create analysis settings tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Create scroll area with vertical-only scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Force vertical-only scrolling
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # General analysis settings group
        general_group = QGroupBox("General Analysis Settings")
        general_layout = QVBoxLayout(general_group)
        general_layout.setSpacing(8)

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
        self.interbedding_group = QGroupBox("Smart Interbedding Parameters")
        interbedding_layout = QFormLayout(self.interbedding_group)
        interbedding_layout.setSpacing(8)
        interbedding_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.smartInterbeddingMaxSequenceSpinBox = QSpinBox()
        self.smartInterbeddingMaxSequenceSpinBox.setRange(5, 50)
        interbedding_layout.addRow("Max Sequence Length:", self.smartInterbeddingMaxSequenceSpinBox)

        self.smartInterbeddingThickUnitSpinBox = QDoubleSpinBox()
        self.smartInterbeddingThickUnitSpinBox.setRange(0.1, 5.0)
        self.smartInterbeddingThickUnitSpinBox.setSingleStep(0.1)
        interbedding_layout.addRow("Thick Unit Threshold (m):", self.smartInterbeddingThickUnitSpinBox)

        layout.addWidget(self.interbedding_group)

        # Analysis method
        method_group = QGroupBox("Analysis Method")
        method_layout = QFormLayout(method_group)
        method_layout.setSpacing(8)
        method_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.analysisMethodComboBox = QComboBox()
        self.analysisMethodComboBox.addItems(["Standard", "Simple"])
        method_layout.addRow("Analysis Method:", self.analysisMethodComboBox)
        layout.addWidget(method_group)

        layout.addStretch()

        # Set container as scroll widget
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Connect smart interbedding checkbox to toggle parameters visibility
        self.smartInterbeddingCheckBox.stateChanged.connect(self.toggle_interbedding_params_visibility)

        return tab

    def toggle_interbedding_params_visibility(self):
        """Show/hide smart interbedding parameters based on checkbox state."""
        visible = self.smartInterbeddingCheckBox.isChecked()
        self.interbedding_group.setVisible(visible)

    def refresh_range_analysis(self):
        """Refresh the range gap analysis with current lithology rules."""
        # Gather lithology rules from the table
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

            # Only add rule if it has a name and code
            if rule['name'] and rule['code']:
                rules.append(rule)

        # Update the range visualizer with the rules
        if hasattr(self, 'range_analyzer') and self.range_analyzer:
            self.range_visualizer.lithology_rules = rules
            self.range_visualizer.refresh_visualization()
        else:
            # Fallback: create a range analyzer
            from ...utils.range_analyzer import RangeAnalyzer
            self.range_analyzer = RangeAnalyzer()
            self.range_visualizer.set_range_analyzer(self.range_analyzer)
            self.range_visualizer.lithology_rules = rules
            self.range_visualizer.refresh_visualization()

    def create_file_tab(self):
        """Create file operations tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Create scroll area with vertical-only scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Force vertical-only scrolling
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # File operations group
        file_group = QGroupBox("Settings File Operations")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)

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

        # AVG Executable group
        avg_group = QGroupBox("AVG Executable")
        avg_layout = QVBoxLayout(avg_group)
        avg_layout.setSpacing(8)

        avg_layout.addWidget(QLabel("Path to AVG executable:"))

        # Horizontal layout for path input and buttons
        path_layout = QHBoxLayout()
        self.avgExecutablePathEdit = QLineEdit()
        self.avgExecutablePathEdit.setPlaceholderText("Select AVG executable path...")
        path_layout.addWidget(self.avgExecutablePathEdit)

        self.browseAvgButton = QPushButton("Browse...")
        path_layout.addWidget(self.browseAvgButton)

        self.clearAvgButton = QPushButton("Clear")
        path_layout.addWidget(self.clearAvgButton)

        avg_layout.addLayout(path_layout)
        layout.addWidget(avg_group)

        # SVG Patterns Directory group
        svg_group = QGroupBox("SVG Patterns Directory")
        svg_layout = QVBoxLayout(svg_group)
        svg_layout.setSpacing(8)

        svg_layout.addWidget(QLabel("Path to SVG patterns directory:"))

        # Horizontal layout for path input and buttons
        svg_path_layout = QHBoxLayout()
        self.svgDirectoryPathEdit = QLineEdit()
        self.svgDirectoryPathEdit.setPlaceholderText("Select SVG patterns directory...")
        svg_path_layout.addWidget(self.svgDirectoryPathEdit)

        self.browseSvgButton = QPushButton("Browse...")
        svg_path_layout.addWidget(self.browseSvgButton)

        self.clearSvgButton = QPushButton("Clear")
        svg_path_layout.addWidget(self.clearSvgButton)

        svg_layout.addLayout(svg_path_layout)
        layout.addWidget(svg_group)

        # Connect signals (will be connected to parent methods)
        self.saveAsSettingsButton.clicked.connect(self.save_settings_as_file)
        self.loadSettingsButton.clicked.connect(self.load_settings_from_file)
        self.researchedDefaultsButton.clicked.connect(self.open_researched_defaults_dialog)
        self.exportLithologyReportButton.clicked.connect(self.export_lithology_report)
        self.browseAvgButton.clicked.connect(self.browse_avg_executable)
        self.clearAvgButton.clicked.connect(self.clear_avg_executable_path)
        self.browseSvgButton.clicked.connect(self.browse_svg_directory)
        self.clearSvgButton.clicked.connect(self.clear_svg_directory_path)

        layout.addStretch()

        # Set container as scroll widget
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        return tab

    def create_range_tab(self):
        """Create range analysis tab."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(4, 4, 4, 4)

        # Create scroll area with vertical-only scrolling
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # Force vertical-only scrolling
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container widget for scroll content
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Range analysis group
        range_group = QGroupBox("Range Gap Analysis")
        range_layout = QVBoxLayout(range_group)
        range_layout.setSpacing(8)

        range_layout.addWidget(QLabel("Analyze gaps and overlaps in lithology rule ranges"))

        # Enhanced range visualizer
        self.range_visualizer = EnhancedRangeGapVisualizer()
        self.range_analyzer = RangeAnalyzer()
        self.range_visualizer.set_range_analyzer(self.range_analyzer)
        range_layout.addWidget(self.range_visualizer)

        # Refresh button
        self.refreshRangeAnalysisButton = QPushButton("Refresh Range Analysis")
        range_layout.addWidget(self.refreshRangeAnalysisButton)

        layout.addWidget(range_group)

        layout.addStretch()

        # Set container as scroll widget
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Connect refresh button
        self.refreshRangeAnalysisButton.clicked.connect(self.refresh_range_analysis)

        return tab

    def load_settings(self):
        """Load current settings into dialog controls."""
        if not self.current_settings:
            return

        # Load lithology rules into table
        if 'lithology_rules' in self.current_settings:
            rules = self.current_settings['lithology_rules']
            self.rulesTable.setRowCount(0)  # Clear existing rows
            for rule in rules:
                row_position = self.rulesTable.rowCount()
                self.rulesTable.insertRow(row_position)
                # Set items for each column
                self.rulesTable.setItem(row_position, 0, QTableWidgetItem(rule.get('name', '')))
                self.rulesTable.setItem(row_position, 1, QTableWidgetItem(rule.get('code', '')))
                self.rulesTable.setItem(row_position, 2, QTableWidgetItem(str(rule.get('gamma_min', 0.0))))
                self.rulesTable.setItem(row_position, 3, QTableWidgetItem(str(rule.get('gamma_max', 0.0))))
                self.rulesTable.setItem(row_position, 4, QTableWidgetItem(str(rule.get('density_min', 0.0))))
                self.rulesTable.setItem(row_position, 5, QTableWidgetItem(str(rule.get('density_max', 0.0))))

        # Load display settings
        if 'separator_thickness' in self.current_settings:
            self.separatorThicknessSpinBox.setValue(self.current_settings['separator_thickness'])
        if 'draw_separators' in self.current_settings:
            self.drawSeparatorsCheckBox.setChecked(self.current_settings['draw_separators'])
        if 'curve_thickness' in self.current_settings:
            self.curveThicknessSpinBox.setValue(self.current_settings['curve_thickness'])
        if 'invert_gamma' in self.current_settings:
            self.invertGammaCheckBox.setChecked(self.current_settings['invert_gamma'])
        if 'invert_short_space_density' in self.current_settings:
            self.invertShortSpaceDensityCheckBox.setChecked(self.current_settings['invert_short_space_density'])
        if 'invert_long_space_density' in self.current_settings:
            self.invertLongSpaceDensityCheckBox.setChecked(self.current_settings['invert_long_space_density'])
        
        # Load SVG disable setting
        if 'disable_svg' in self.current_settings:
            self.disableSvgCheckBox.setChecked(self.current_settings['disable_svg'])

        # Load analysis settings
        if 'use_researched_defaults' in self.current_settings:
            self.useResearchedDefaultsCheckBox.setChecked(self.current_settings['use_researched_defaults'])
        if 'merge_thin_units' in self.current_settings:
            self.mergeThinUnitsCheckBox.setChecked(self.current_settings['merge_thin_units'])
        if 'smart_interbedding' in self.current_settings:
            self.smartInterbeddingCheckBox.setChecked(self.current_settings['smart_interbedding'])
        if 'fallback_classification' in self.current_settings:
            self.fallbackClassificationCheckBox.setChecked(self.current_settings['fallback_classification'])
        if 'smart_interbedding_max_sequence_length' in self.current_settings:
            self.smartInterbeddingMaxSequenceSpinBox.setValue(self.current_settings['smart_interbedding_max_sequence_length'])
        if 'smart_interbedding_thick_unit_threshold' in self.current_settings:
            self.smartInterbeddingThickUnitSpinBox.setValue(self.current_settings['smart_interbedding_thick_unit_threshold'])
        if 'analysis_method' in self.current_settings:
            method = self.current_settings['analysis_method']
            index = self.analysisMethodComboBox.findText(method.capitalize())
            if index >= 0:
                self.analysisMethodComboBox.setCurrentIndex(index)

        # Load AVG executable path
        if 'avg_executable_path' in self.current_settings:
            self.avgExecutablePathEdit.setText(self.current_settings['avg_executable_path'])
        
        # Load SVG directory path
        if 'svg_directory_path' in self.current_settings:
            self.svgDirectoryPathEdit.setText(self.current_settings['svg_directory_path'])

        # Update interbedding parameters visibility based on checkbox
        self.toggle_interbedding_params_visibility()

        # Refresh range analysis with loaded rules
        self.refresh_range_analysis()

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
        settings['disable_svg'] = self.disableSvgCheckBox.isChecked()

        # Gather analysis settings
        settings['use_researched_defaults'] = self.useResearchedDefaultsCheckBox.isChecked()
        settings['merge_thin_units'] = self.mergeThinUnitsCheckBox.isChecked()
        settings['smart_interbedding'] = self.smartInterbeddingCheckBox.isChecked()
        settings['fallback_classification'] = self.fallbackClassificationCheckBox.isChecked()
        settings['smart_interbedding_max_sequence_length'] = self.smartInterbeddingMaxSequenceSpinBox.value()
        settings['smart_interbedding_thick_unit_threshold'] = self.smartInterbeddingThickUnitSpinBox.value()
        settings['analysis_method'] = self.analysisMethodComboBox.currentText().lower()

        # Gather AVG executable path
        settings['avg_executable_path'] = self.avgExecutablePathEdit.text()
        
        # Gather SVG directory path
        settings['svg_directory_path'] = self.svgDirectoryPathEdit.text()

        return settings

    def add_rule(self):
        """Add a new empty row to the lithology rules table."""
        row_position = self.rulesTable.rowCount()
        self.rulesTable.insertRow(row_position)
        # Pre-fill with empty QTableWidgetItems
        for col in range(self.rulesTable.columnCount()):
            self.rulesTable.setItem(row_position, col, QTableWidgetItem(""))
        # Refresh range analysis to include new (empty) rule
        self.refresh_range_analysis()

    def remove_rule(self):
        """Remove the currently selected row from the lithology rules table."""
        current_row = self.rulesTable.currentRow()
        if current_row >= 0:
            self.rulesTable.removeRow(current_row)
            # Refresh range analysis after removal
            self.refresh_range_analysis()

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

    def browse_avg_executable(self):
        """Open file dialog to browse for AVG executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select AVG Executable",
            "",
            "Executable files (*.exe *.bat *.sh);;All files (*.*)"
        )
        if file_path:
            self.avgExecutablePathEdit.setText(file_path)
            # Update settings immediately (optional)
            # self.on_apply()

    def clear_avg_executable_path(self):
        """Clear the AVG executable path."""
        self.avgExecutablePathEdit.setText("")
        # Update settings immediately (optional)
        # self.on_apply()

    def browse_svg_directory(self):
        """Open directory dialog to browse for SVG patterns directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select SVG Patterns Directory",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        if dir_path:
            self.svgDirectoryPathEdit.setText(dir_path)
            # Update settings immediately (optional)
            # self.on_apply()

    def clear_svg_directory_path(self):
        """Clear the SVG directory path."""
        self.svgDirectoryPathEdit.setText("")
        # Update settings immediately (optional)
        # self.on_apply()

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