from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QDoubleSpinBox, QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from ..core.config import LITHOLOGY_COLUMN, RECOVERED_THICKNESS_COLUMN

class InterbeddingDialog(QDialog):
    def __init__(self, selected_units, parent=None):
        super().__init__(parent)
        self.selected_units = selected_units  # List of unit dictionaries
        self.setWindowTitle("Create Interbedding")
        self.setModal(True)
        self.resize(800, 600)

        self.setup_ui()
        self.populate_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel("Selected units will be merged into an interbedded section. "
                             "Configure the interrelationship code and review percentages.")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Table for selected units
        self.units_table = QTableWidget()
        self.units_table.setColumnCount(5)
        self.units_table.setHorizontalHeaderLabels([
            "Lithology", "Thickness (m)", "Percentage (%)", "Sequence", "Include"
        ])
        self.units_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.units_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.units_table)

        # Interrelationship code selection
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("Interrelationship Code:"))
        self.code_combo = QComboBox()
        self.code_combo.addItems([
            "IL - Interlaminated (< 20mm)",
            "UB - Very Thinly Interbedded (20-60mm)",
            "TB - Thinly Interbedded (60-200mm)",
            "CB - Coarsely Interbedded (> 200mm)"
        ])
        self.code_combo.setCurrentText("TB - Thinly Interbedded (60-200mm)")  # Default
        code_layout.addWidget(self.code_combo)
        code_layout.addStretch()
        layout.addLayout(code_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Create Interbedding")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

    def populate_table(self):
        """Populate the table with selected units and calculate percentages."""
        total_thickness = sum(unit[RECOVERED_THICKNESS_COLUMN] for unit in self.selected_units)

        # Group by lithology code for percentage calculation
        lithology_groups = {}
        for unit in self.selected_units:
            code = unit[LITHOLOGY_COLUMN]
            if code not in lithology_groups:
                lithology_groups[code] = {'thickness': 0, 'count': 0}
            lithology_groups[code]['thickness'] += unit[RECOVERED_THICKNESS_COLUMN]
            lithology_groups[code]['count'] += 1

        # Sort by thickness (dominance)
        sorted_lithologies = sorted(lithology_groups.items(),
                                   key=lambda x: x[1]['thickness'],
                                   reverse=True)

        self.units_table.setRowCount(len(sorted_lithologies))

        for row, (code, data) in enumerate(sorted_lithologies):
            percentage = (data['thickness'] / total_thickness) * 100

            # Lithology code
            code_item = QTableWidgetItem(code)
            code_item.setFlags(code_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.units_table.setItem(row, 0, code_item)

            # Thickness
            thickness_item = QTableWidgetItem(f"{data['thickness']:.3f}")
            thickness_item.setFlags(thickness_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.units_table.setItem(row, 1, thickness_item)

            # Percentage
            percentage_item = QTableWidgetItem(f"{percentage:.2f}")
            percentage_item.setFlags(percentage_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.units_table.setItem(row, 2, percentage_item)

            # Sequence number
            seq_item = QTableWidgetItem(str(row + 1))
            seq_item.setFlags(seq_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.units_table.setItem(row, 3, seq_item)

            # Include checkbox (for lithologies >= 5%)
            include_checkbox = QTableWidgetItem()
            include_checkbox.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            if percentage >= 5:
                include_checkbox.setCheckState(Qt.CheckState.Checked)
            else:
                include_checkbox.setCheckState(Qt.CheckState.Unchecked)
                include_checkbox.setToolTip("Lithology makes up < 5% of section")
            self.units_table.setItem(row, 4, include_checkbox)

    def get_interbedding_data(self):
        """Return the interbedding configuration with percentages recalculated for included lithologies only."""
        # Get selected code
        code_text = self.code_combo.currentText()
        inter_code = code_text.split(' - ')[0]  # Extract code (IL, UB, TB, CB)

        # Get included lithologies and their original thicknesses
        included_lithologies = []
        total_included_thickness = 0.0

        for row in range(self.units_table.rowCount()):
            include_item = self.units_table.item(row, 4)
            if include_item and include_item.checkState() == Qt.CheckState.Checked:
                code = self.units_table.item(row, 0).text()
                thickness = float(self.units_table.item(row, 1).text())
                sequence = int(self.units_table.item(row, 3).text())
                included_lithologies.append({
                    'code': code,
                    'original_thickness': thickness,
                    'sequence': sequence
                })
                total_included_thickness += thickness

        # Recalculate percentages based only on included lithologies
        for lith in included_lithologies:
            if total_included_thickness > 0:
                lith['percentage'] = round((lith['original_thickness'] / total_included_thickness) * 100, 2)
            else:
                lith['percentage'] = 0.0
            # Remove the temporary thickness field
            del lith['original_thickness']

        # Sort by thickness (dominance) to assign proper sequence numbers
        included_lithologies.sort(key=lambda x: x['percentage'], reverse=True)
        for i, lith in enumerate(included_lithologies):
            lith['sequence'] = i + 1

        return {
            'interrelationship_code': inter_code,
            'lithologies': included_lithologies,
            'from_depth': min(unit['from_depth'] for unit in self.selected_units),
            'to_depth': max(unit['to_depth'] for unit in self.selected_units)
        }

    def accept(self):
        """Validate before accepting."""
        data = self.get_interbedding_data()

        # Check that at least 2 lithologies are included
        if len(data['lithologies']) < 2:
            QMessageBox.warning(self, "Invalid Configuration",
                              "Interbedding requires at least 2 lithologies.")
            return

        # Check that percentages sum to approximately 100%
        total_percentage = sum(lith['percentage'] for lith in data['lithologies'])
        if not (99.5 <= total_percentage <= 100.5):
            QMessageBox.warning(self, "Invalid Percentages",
                              f"Percentages must sum to 100% (currently {total_percentage:.2f}%).")
            return

        super().accept()