import json
import os
import pandas as pd

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

# Import dialogs for column configurator and NL review
from ..dialogs.column_configurator_dialog import ColumnConfiguratorDialog
from ..dialogs.nl_review_dialog import NLReviewDialog

class SettingsDialog(QDialog):
    # Signal to notify MainWindow when settings are updated
    settings_updated = pyqtSignal(dict)

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        print("[DEBUG] SettingsDialog.__init__ called")
        self.setWindowTitle("Earthworm Settings")
        self.setGeometry(100, 100, 900, 650)  # Reasonable size for settings dialog
        self.setMinimumSize(800, 600)

        # Store current settings passed from MainWindow
        self.current_settings = current_settings or {}

        # Load CoalLog qualifiers from JSON file
        self.lithology_qualifiers = self.load_qualifiers()
        
        # Load dropdown options from Excel file
        self.dropdown_options = self.load_dropdown_options()
        
        # Store extra fields for lithology rules (background_color, svg_path, etc.)
        self.rule_extra_data = []

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

    def load_qualifiers(self):
        """Load lithology qualifiers from the CoalLog standards JSON file."""
        qualifiers_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'assets', 'litho_lithoQuals.json'
        )
        try:
            with open(qualifiers_path, 'r') as f:
                data = json.load(f)
                # Extract mapping from lithology code to qualifier dict (code->description)
                qualifier_map = {}
                for litho_code, litho_data in data.get('lithology_qualifiers', {}).items():
                    qualifier_map[litho_code] = litho_data.get('qualifiers', {})
                return qualifier_map
        except Exception as e:
            print(f"[WARNING] Could not load lithology qualifiers from {qualifiers_path}: {e}")
            return {}

    def load_dropdown_options(self):
        """Load dropdown options from CoalLog Excel dictionary file."""
        excel_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'assets', 'CoalLog v3.1 Dictionaries.xlsx'
        )
        
        options = {
            'shade': [],
            'hue': [],
            'colour': [],
            'estimated_strength': []
        }
        
        try:
            # Load Shade options
            shade_df = pd.read_excel(excel_path, sheet_name='Shade')
            # Filter out header row and get code-description pairs
            for _, row in shade_df.iterrows():
                code = row.get('Sorted on Code', '')
                desc = row.get('Sorted on Description', '')
                if pd.notna(code) and pd.notna(desc) and code != 'Code' and desc != 'Shade':
                    options['shade'].append((str(code).strip(), str(desc).strip()))
            
            # Load Hue options
            hue_df = pd.read_excel(excel_path, sheet_name='Hue')
            for _, row in hue_df.iterrows():
                code = row.get('Sorted on Code', '')
                desc = row.get('Sorted on Description', '')
                if pd.notna(code) and pd.notna(desc) and code != 'Code' and desc != 'Hue':
                    options['hue'].append((str(code).strip(), str(desc).strip()))
            
            # Load Colour options
            colour_df = pd.read_excel(excel_path, sheet_name='Colour')
            for _, row in colour_df.iterrows():
                code = row.get('Sorted on Code', '')
                desc = row.get('Sorted on Description', '')
                if pd.notna(code) and pd.notna(desc) and code != 'Code' and desc != 'Colour':
                    options['colour'].append((str(code).strip(), str(desc).strip()))
            
            # Load Estimated Strength options
            strength_df = pd.read_excel(excel_path, sheet_name='Est_Strength')
            for _, row in strength_df.iterrows():
                code = row.get('Sorted on Code', '')
                desc = row.get('Unnamed: 1', '')
                if pd.notna(code) and pd.notna(desc) and code != 'Code' and desc != 'Estimated Strength':
                    options['estimated_strength'].append((str(code).strip(), str(desc).strip()))
            
            print(f"[DEBUG] Loaded dropdown options: Shade={len(options['shade'])}, Hue={len(options['hue'])}, Colour={len(options['colour'])}, Est Strength={len(options['estimated_strength'])}")
            
        except Exception as e:
            print(f"[WARNING] Could not load dropdown options from Excel: {e}")
            import traceback
            traceback.print_exc()
        
        return options

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
        self.rulesTable.setColumnCount(11)
        # Column indices: 
        # 0: Lithology Name, 1: Litho Code, 2: Litho Qualifier, 
        # 3: Shade, 4: Hue, 5: Colour, 6: Estimated Strength,
        # 7: Gamma Min, 8: Gamma Max, 9: Density Min, 10: Density Max
        self.rulesTable.setHorizontalHeaderLabels([
            "Lithology Name", "Litho Code", "Litho Qualifier", 
            "Shade", "Hue", "Colour", "Estimated Strength",
            "Gamma Min", "Gamma Max", "Density Min", "Density Max"
        ])
        self.rulesTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.rulesTable)

        # Connect cell changed signal to update qualifier dropdown when lithology code changes
        self.rulesTable.cellChanged.connect(self.on_cell_changed)

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
        print("[DEBUG] create_display_tab called")
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

        # Curve Visibility group
        curve_visibility_group = QGroupBox("Curve Visibility")
        curve_visibility_layout = QVBoxLayout(curve_visibility_group)
        curve_visibility_layout.setSpacing(6)
        
        # Create checkboxes for each curve type
        self.curve_visibility_checkboxes = {}
        
        # Curve types with their display names and abbreviations
        curve_types = [
            ("SS", "Short Space Density", "short_space_density"),
            ("LS", "Long Space Density", "long_space_density"),
            ("GR", "Gamma Ray", "gamma"),
            ("CD", "Caliper", "cd"),
            ("RES", "Resistivity", "res"),
            ("CAL", "Caliper", "cal")
        ]
        
        for abbr, display_name, curve_name in curve_types:
            checkbox = QCheckBox(f"[{abbr}] {display_name}")
            checkbox.setChecked(True)  # All curves visible by default
            checkbox.curve_name = curve_name  # Store the internal curve name
            self.curve_visibility_checkboxes[curve_name] = checkbox
            curve_visibility_layout.addWidget(checkbox)
        
        curve_visibility_layout.addStretch()
        layout.addWidget(curve_visibility_group)
        print(f"[DEBUG] Added curve visibility group with {len(self.curve_visibility_checkboxes)} checkboxes")

        # Table Settings group
        table_group = QGroupBox("Table Settings")
        table_layout = QVBoxLayout(table_group)
        table_layout.setSpacing(8)
        
        # Column Configurator button
        self.columnConfiguratorButton = QPushButton("⚙️ Column Configurator")
        self.columnConfiguratorButton.setToolTip("Configure visible columns in the lithology table")
        self.columnConfiguratorButton.clicked.connect(self.open_column_configurator_dialog)
        table_layout.addWidget(self.columnConfiguratorButton)
        
        layout.addWidget(table_group)
        print("[DEBUG] Added table settings group with column configurator button")

        layout.addStretch()

        # Set container as scroll widget
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        return tab

    def create_analysis_tab(self):
        """Create analysis settings tab."""
        print("[DEBUG] create_analysis_tab called")
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

        # Bit size input field and anomaly detection
        bit_size_widget = QWidget()
        bit_size_layout = QFormLayout(bit_size_widget)
        bit_size_layout.setSpacing(8)
        bit_size_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        self.bitSizeSpinBox = QDoubleSpinBox()
        self.bitSizeSpinBox.setRange(50.0, 500.0)  # Reasonable range for bit sizes in mm
        self.bitSizeSpinBox.setValue(150.0)  # Default will be overridden by load_settings
        self.bitSizeSpinBox.setSingleStep(10.0)
        self.bitSizeSpinBox.setSuffix(" mm")
        self.bitSizeSpinBox.setToolTip("Bit size in millimeters for caliper anomaly detection (CAL - BitSize > 20)")
        bit_size_layout.addRow("Bit Size:", self.bitSizeSpinBox)
        
        # Anomaly highlighting checkbox
        self.showAnomalyHighlightsCheckBox = QCheckBox("Show anomaly highlights")
        self.showAnomalyHighlightsCheckBox.setChecked(True)  # Default
        self.showAnomalyHighlightsCheckBox.setToolTip("Show/hide red highlighting for caliper anomalies (CAL - BitSize > 20 mm)")
        bit_size_layout.addRow("", self.showAnomalyHighlightsCheckBox)
        
        layout.addWidget(bit_size_widget)
        print("[DEBUG] Added bit size widget with spinbox and anomaly checkbox")
        
        # Casing depth masking
        casing_depth_widget = QWidget()
        casing_depth_layout = QFormLayout(casing_depth_widget)
        casing_depth_layout.setSpacing(8)
        casing_depth_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        
        # Enable casing depth masking checkbox
        self.casingDepthEnabledCheckBox = QCheckBox("Enable Casing Depth Masking")
        self.casingDepthEnabledCheckBox.setChecked(False)  # Default
        self.casingDepthEnabledCheckBox.setToolTip("Mask intervals above casing depth as 'NL' (Not Logged)")
        casing_depth_layout.addRow("", self.casingDepthEnabledCheckBox)
        self.casingDepthEnabledCheckBox.stateChanged.connect(self.toggle_casing_depth_spinbox)
        
        # Casing depth input (only enabled when checkbox is checked)
        self.casingDepthSpinBox = QDoubleSpinBox()
        self.casingDepthSpinBox.setRange(0.0, 5000.0)  # Reasonable range for casing depth in meters
        self.casingDepthSpinBox.setValue(0.0)  # Default
        self.casingDepthSpinBox.setSingleStep(1.0)
        self.casingDepthSpinBox.setSuffix(" m")
        self.casingDepthSpinBox.setToolTip("Casing depth in meters. Intervals above this depth will be masked as 'NL'")
        self.casingDepthSpinBox.setEnabled(False)  # Initially disabled if not checked
        casing_depth_layout.addRow("Casing Depth:", self.casingDepthSpinBox)
        
        layout.addWidget(casing_depth_widget)
        print("[DEBUG] Added casing depth widget with checkbox and spinbox")
        
        # NL Review button
        nl_review_widget = QWidget()
        nl_review_layout = QHBoxLayout(nl_review_widget)
        nl_review_layout.setSpacing(8)
        nl_review_layout.setContentsMargins(0, 0, 0, 0)
        
        self.nlReviewButton = QPushButton("📊 Review NL Intervals")
        self.nlReviewButton.setToolTip("Review 'NL' (Not Logged) intervals with statistics")
        self.nlReviewButton.clicked.connect(self.open_nl_review_dialog)
        nl_review_layout.addWidget(self.nlReviewButton)
        nl_review_layout.addStretch()
        
        layout.addWidget(nl_review_widget)
        print("[DEBUG] Added NL review button")

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

    def open_column_configurator_dialog(self):
        """Open the column configurator dialog."""
        dialog = ColumnConfiguratorDialog(self, main_window=self.parent(), current_visibility=self.current_settings.get("column_visibility", {}))
        dialog.visibility_changed.connect(self.on_column_visibility_changed)
        dialog.exec()

    def on_column_visibility_changed(self, visibility_map):
        """Handle column visibility changes from the configurator dialog."""
        self.current_settings["column_visibility"] = visibility_map
        # Emit settings updated signal if needed
        # self.settings_updated.emit(self.current_settings)
        # Apply visibility to table via main window
        main_window = self.parent()
        if main_window and hasattr(main_window, 'on_column_visibility_changed'):
            main_window.on_column_visibility_changed(visibility_map)

    def open_nl_review_dialog(self):
        """Open the NL review dialog."""
        # Check if there's a main window with data
        main_window = self.parent()
        if main_window and hasattr(main_window, 'dataframe') and main_window.dataframe is not None:
            dialog = NLReviewDialog(parent=self, main_window=main_window)
            dialog.exec()
        else:
            QMessageBox.warning(self, "No Data", "Please load data first to review NL intervals.")

    def toggle_casing_depth_spinbox(self):
        """Enable/disable casing depth spinbox based on checkbox state."""
        enabled = self.casingDepthEnabledCheckBox.isChecked()
        self.casingDepthSpinBox.setEnabled(enabled)

    def refresh_range_analysis(self):
        """Refresh the range gap analysis with current lithology rules."""
        # Gather lithology rules from the table
        rules = []
        for row_idx in range(self.rulesTable.rowCount()):
            rule = {}
            rule['name'] = self.rulesTable.item(row_idx, 0).text() if self.rulesTable.item(row_idx, 0) else ''
            rule['code'] = self.rulesTable.item(row_idx, 1).text() if self.rulesTable.item(row_idx, 1) else ''

            # Convert numeric fields (indices shifted due to new columns)
            try:
                rule['gamma_min'] = float(self.rulesTable.item(row_idx, 7).text()) if self.rulesTable.item(row_idx, 7) and self.rulesTable.item(row_idx, 7).text() else 0.0
            except ValueError:
                rule['gamma_min'] = 0.0
            try:
                rule['gamma_max'] = float(self.rulesTable.item(row_idx, 8).text()) if self.rulesTable.item(row_idx, 8) and self.rulesTable.item(row_idx, 8).text() else 0.0
            except ValueError:
                rule['gamma_max'] = 0.0
            try:
                rule['density_min'] = float(self.rulesTable.item(row_idx, 9).text()) if self.rulesTable.item(row_idx, 9) and self.rulesTable.item(row_idx, 9).text() else 0.0
            except ValueError:
                rule['density_min'] = 0.0
            try:
                rule['density_max'] = float(self.rulesTable.item(row_idx, 10).text()) if self.rulesTable.item(row_idx, 10) and self.rulesTable.item(row_idx, 10).text() else 0.0
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
        print(f"[DEBUG] SettingsDialog.load_settings called, keys: {list(self.current_settings.keys())}")
        if 'lithology_rules' in self.current_settings:
            print(f"[DEBUG] Lithology rules count: {len(self.current_settings['lithology_rules'])}")

        # Load lithology rules into table
        if 'lithology_rules' in self.current_settings:
            rules = self.current_settings['lithology_rules']
            self.rulesTable.setRowCount(0)  # Clear existing rows
            self.rule_extra_data = []  # Reset extra fields storage
            for rule in rules:
                row_position = self.rulesTable.rowCount()
                self.rulesTable.insertRow(row_position)
                # Set items for each column (11 columns)
                self.rulesTable.setItem(row_position, 0, QTableWidgetItem(rule.get('name', '')))
                self.rulesTable.setItem(row_position, 1, QTableWidgetItem(rule.get('code', '')))
                # Qualifier column will have a dropdown widget; set item text for storage
                self.rulesTable.setItem(row_position, 2, QTableWidgetItem(rule.get('qualifier', '')))
                
                # Create dropdowns for Shade, Hue, Colour, Estimated Strength
                dropdown_columns = {
                    3: ('shade', rule.get('shade', '')),
                    4: ('hue', rule.get('hue', '')),
                    5: ('colour', rule.get('colour', '')),
                    6: ('estimated_strength', rule.get('estimated_strength', ''))
                }
                
                for col, (option_type, value) in dropdown_columns.items():
                    combo = self.create_dropdown_for_cell(row_position, col, option_type)
                    self.rulesTable.setCellWidget(row_position, col, combo)
                    # Create hidden item to store value
                    self.rulesTable.setItem(row_position, col, QTableWidgetItem(value))
                    # Set dropdown selection
                    self.update_dropdown_selection(row_position, col, value)
                
                # Set numeric columns (indices shifted due to new Estimated Strength column)
                self.rulesTable.setItem(row_position, 7, QTableWidgetItem(str(rule.get('gamma_min', 0.0))))
                self.rulesTable.setItem(row_position, 8, QTableWidgetItem(str(rule.get('gamma_max', 0.0))))
                self.rulesTable.setItem(row_position, 9, QTableWidgetItem(str(rule.get('density_min', 0.0))))
                self.rulesTable.setItem(row_position, 10, QTableWidgetItem(str(rule.get('density_max', 0.0))))
                # Update qualifier dropdown based on lithology code
                self.update_qualifier_dropdown(row_position, rule.get('code', ''))
                # Store extra fields not represented in the table (background_color, svg_path, etc.)
                extra = {k: v for k, v in rule.items() if k not in [
                    'name', 'code', 'qualifier', 'shade', 'hue', 'colour', 'estimated_strength',
                    'gamma_min', 'gamma_max', 'density_min', 'density_max'
                ]}
                self.rule_extra_data.append(extra)

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

        # Load curve visibility settings
        if 'curve_visibility' in self.current_settings:
            for curve_name, visible in self.current_settings['curve_visibility'].items():
                if curve_name in self.curve_visibility_checkboxes:
                    self.curve_visibility_checkboxes[curve_name].setChecked(visible)
        
        # Load column visibility (store in current_settings for later gathering)
        # No UI to load, just keep in current_settings
        
        # Load bit size and anomaly detection settings
        if 'bit_size_mm' in self.current_settings:
            self.bitSizeSpinBox.setValue(self.current_settings['bit_size_mm'])
        if 'show_anomaly_highlights' in self.current_settings:
            self.showAnomalyHighlightsCheckBox.setChecked(self.current_settings['show_anomaly_highlights'])
        
        # Load casing depth settings
        if 'casing_depth_enabled' in self.current_settings:
            self.casingDepthEnabledCheckBox.setChecked(self.current_settings['casing_depth_enabled'])
            self.casingDepthSpinBox.setEnabled(self.current_settings['casing_depth_enabled'])
        if 'casing_depth_m' in self.current_settings:
            self.casingDepthSpinBox.setValue(self.current_settings['casing_depth_m'])

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
            rule['qualifier'] = self.rulesTable.item(row_idx, 2).text() if self.rulesTable.item(row_idx, 2) else ''
            
            # Get values from dropdown columns
            dropdown_columns = {
                3: 'shade',
                4: 'hue',
                5: 'colour',
                6: 'estimated_strength'
            }
            
            for col, field_name in dropdown_columns.items():
                # Try to get value from dropdown widget first, then from item
                widget = self.rulesTable.cellWidget(row_idx, col)
                if widget and isinstance(widget, QComboBox):
                    current_data = widget.currentData()
                    rule[field_name] = current_data if current_data is not None else ""
                else:
                    rule[field_name] = self.rulesTable.item(row_idx, col).text() if self.rulesTable.item(row_idx, col) else ''

            # Convert numeric fields (indices shifted due to new Estimated Strength column)
            try:
                rule['gamma_min'] = float(self.rulesTable.item(row_idx, 7).text()) if self.rulesTable.item(row_idx, 7) and self.rulesTable.item(row_idx, 7).text() else 0.0
            except ValueError:
                rule['gamma_min'] = 0.0
            try:
                rule['gamma_max'] = float(self.rulesTable.item(row_idx, 8).text()) if self.rulesTable.item(row_idx, 8) and self.rulesTable.item(row_idx, 8).text() else 0.0
            except ValueError:
                rule['gamma_max'] = 0.0
            try:
                rule['density_min'] = float(self.rulesTable.item(row_idx, 9).text()) if self.rulesTable.item(row_idx, 9) and self.rulesTable.item(row_idx, 9).text() else 0.0
            except ValueError:
                rule['density_min'] = 0.0
            try:
                rule['density_max'] = float(self.rulesTable.item(row_idx, 10).text()) if self.rulesTable.item(row_idx, 10) and self.rulesTable.item(row_idx, 10).text() else 0.0
            except ValueError:
                rule['density_max'] = 0.0

            # Merge extra fields (background_color, svg_path, etc.)
            if row_idx < len(self.rule_extra_data):
                rule.update(self.rule_extra_data[row_idx])

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
        
        # Gather curve visibility settings
        curve_visibility = {}
        for curve_name, checkbox in self.curve_visibility_checkboxes.items():
            curve_visibility[curve_name] = checkbox.isChecked()
        settings['curve_visibility'] = curve_visibility
        
        # Gather column visibility (stored in current_settings)
        if 'column_visibility' in self.current_settings:
            settings['column_visibility'] = self.current_settings['column_visibility']
        else:
            settings['column_visibility'] = {}
        
        # Gather bit size and anomaly detection settings
        settings['bit_size_mm'] = self.bitSizeSpinBox.value()
        settings['show_anomaly_highlights'] = self.showAnomalyHighlightsCheckBox.isChecked()
        
        # Gather casing depth settings
        settings['casing_depth_enabled'] = self.casingDepthEnabledCheckBox.isChecked()
        settings['casing_depth_m'] = self.casingDepthSpinBox.value()

        return settings

    def create_dropdown_for_cell(self, row, column, option_type):
        """Create a dropdown combobox for a specific cell."""
        combo = QComboBox()
        combo.setEditable(False)  # Fixed selection only
        
        # Add empty option first
        combo.addItem("", "")
        
        # Add options from loaded data
        if option_type in self.dropdown_options:
            for code, description in self.dropdown_options[option_type]:
                display_text = f"{code} - {description}" if description else code
                combo.addItem(display_text, code)
        
        # Connect signal to update table item
        combo.currentIndexChanged.connect(lambda idx, r=row, c=column, cb=combo: self.on_dropdown_changed(r, c, cb))
        
        return combo

    def on_dropdown_changed(self, row, column, combo):
        """Handle dropdown selection change."""
        current_data = combo.currentData()
        value = current_data if current_data is not None else ""
        
        # Ensure a table item exists for the column
        item = self.rulesTable.item(row, column)
        if not item:
            item = QTableWidgetItem(value)
            self.rulesTable.setItem(row, column, item)
        else:
            item.setText(value)

    def update_dropdown_selection(self, row, column, value):
        """Update dropdown selection based on stored value."""
        widget = self.rulesTable.cellWidget(row, column)
        if widget and isinstance(widget, QComboBox):
            # Find index by data
            index = widget.findData(value, Qt.ItemDataRole.UserRole)
            if index >= 0:
                widget.setCurrentIndex(index)
            else:
                widget.setCurrentIndex(0)  # Set to empty

    def add_rule(self):
        """Add a new empty row to the lithology rules table."""
        row_position = self.rulesTable.rowCount()
        self.rulesTable.insertRow(row_position)
        
        # Create items for text columns
        for col in [0, 1]:  # Name and Code columns
            self.rulesTable.setItem(row_position, col, QTableWidgetItem(""))
        
        # Create dropdown for qualifier column
        self.update_qualifier_dropdown(row_position, "")
        
        # Create dropdowns for Shade, Hue, Colour, Estimated Strength
        dropdown_columns = {
            3: 'shade',
            4: 'hue', 
            5: 'colour',
            6: 'estimated_strength'
        }
        
        for col, option_type in dropdown_columns.items():
            combo = self.create_dropdown_for_cell(row_position, col, option_type)
            self.rulesTable.setCellWidget(row_position, col, combo)
            # Create hidden item to store value
            self.rulesTable.setItem(row_position, col, QTableWidgetItem(""))
        
        # Create items for numeric columns
        for col in range(7, 11):  # Gamma Min to Density Max
            self.rulesTable.setItem(row_position, col, QTableWidgetItem(""))
        
        # Add empty extra fields dict for this row
        self.rule_extra_data.append({})
        # Refresh range analysis to include new (empty) rule
        self.refresh_range_analysis()

    def remove_rule(self):
        """Remove the currently selected row from the lithology rules table."""
        current_row = self.rulesTable.currentRow()
        if current_row >= 0:
            self.rulesTable.removeRow(current_row)
            # Remove corresponding extra fields
            if current_row < len(self.rule_extra_data):
                del self.rule_extra_data[current_row]
            # Refresh range analysis after removal
            self.refresh_range_analysis()

    def on_cell_changed(self, row, column):
        """Handle cell changes in the lithology rules table."""
        print(f"[DEBUG] on_cell_changed row={row}, column={column}")
        if column == 1:  # Litho Code column changed
            item = self.rulesTable.item(row, column)
            if item:
                litho_code = item.text().strip()
                print(f"[DEBUG] Litho code changed to '{litho_code}', updating qualifier dropdown")
                self.update_qualifier_dropdown(row, litho_code)

    def update_qualifier_dropdown(self, row, litho_code):
        """Update the qualifier dropdown for a given row based on lithology code."""
        # Remove existing widget if any
        existing_widget = self.rulesTable.cellWidget(row, 2)
        if existing_widget:
            existing_widget.deleteLater()
        # DEBUG: Also check for stray widget in column 0 (reported bug)
        stray_widget = self.rulesTable.cellWidget(row, 0)
        if stray_widget:
            print(f"[DEBUG] Removing stray widget from column 0, row {row}")
            stray_widget.deleteLater()
        
        # Create a new combobox with qualifier options for this lithology code
        combo = QComboBox()
        combo.setEditable(True)  # Allow custom qualifiers
        combo.addItem("", "")  # Empty option with empty data
        
        # Get current qualifier text from table item (if any)
        qualifier_item = self.rulesTable.item(row, 2)
        current_qualifier = qualifier_item.text() if qualifier_item else ""
        
        # Normalize lithology code to uppercase for lookup (JSON keys are uppercase)
        lookup_code = litho_code.strip().upper() if litho_code else ""
        
        # Add standard qualifiers from CoalLog standards
        if lookup_code in self.lithology_qualifiers:
            qualifier_dict = self.lithology_qualifiers[lookup_code]
            for code, description in qualifier_dict.items():
                display_text = f"{code} - {description}"
                combo.addItem(display_text, code)
        
        # Add current qualifier as an extra item if not already present
        if current_qualifier and current_qualifier not in [combo.itemData(i) for i in range(combo.count())]:
            combo.addItem(current_qualifier, current_qualifier)
        
        # Set current selection based on qualifier item
        if current_qualifier:
            # Find by data (qualifier code) - case-insensitive match
            index = combo.findData(current_qualifier, Qt.ItemDataRole.UserRole)
            if index >= 0:
                combo.setCurrentIndex(index)
                combo.setEditText(current_qualifier)  # Show code, not description
            else:
                # If not found, set editable text
                combo.setCurrentText(current_qualifier)
        
        # Connect combobox changes to update table item
        combo.currentIndexChanged.connect(lambda: self.on_qualifier_changed(row, combo))
        
        # Set combobox as cell widget
        print(f"[DEBUG] Setting combo box at row {row}, column 2 (litho_code='{litho_code}')")
        self.rulesTable.setCellWidget(row, 2, combo)

    def on_qualifier_changed(self, row, combo):
        """Handle qualifier combobox selection change."""
        # Get the qualifier code from combobox data or text
        current_data = combo.currentData()
        qualifier_code = current_data if current_data is not None else combo.currentText()
        
        # Ensure a table item exists for the qualifier column
        item = self.rulesTable.item(row, 2)
        if not item:
            item = QTableWidgetItem(qualifier_code)
            self.rulesTable.setItem(row, 2, item)
        else:
            item.setText(qualifier_code)
        # Update combobox display to show code, not description
        combo.setEditText(qualifier_code)

    def save_settings_as_file(self):
        """Open file dialog to save settings to a JSON file."""
        # This should delegate to parent MainWindow
        if self.parent():
            self.parent().save_settings_as_file()

    def load_settings_from_file(self):
        """Open file dialog to load settings from a JSON file."""
        # This should delegate to parent MainWindow
        if self.parent():
            print(f"[DEBUG] SettingsDialog.load_settings_from_file delegating to parent")
            self.parent().load_settings_from_file()
            # After loading, update current settings from parent
            self.current_settings = self.parent().get_current_settings()
            print(f"[DEBUG] Updated current_settings, keys: {list(self.current_settings.keys())}")
            # Update dialog controls
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
        # Note: This call passes a dict to update_settings which expects auto_save parameter
        # Disabled because settings_updated signal already triggers update_settings_from_dialog
        # if self.parent() and hasattr(self.parent(), 'update_settings'):
        #     self.parent().update_settings(settings)

    def accept(self):
        """Override accept to ensure settings are saved."""
        super().accept()

    def reject(self):
        """Override reject to handle cancellation."""
        super().reject()