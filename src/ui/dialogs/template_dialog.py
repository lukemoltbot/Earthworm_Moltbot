"""
Template Selection Dialog for Earthworm Moltbot
Provides UI for selecting project templates.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QTextEdit, QGroupBox,
    QGridLayout, QSplitter, QMessageBox, QFrame,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from ...core.template_manager import TemplateManager, ProjectTemplate


class TemplateDialog(QDialog):
    """Dialog for selecting project templates."""
    
    template_selected = pyqtSignal(str)  # Signal emitted when a template is selected
    
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.template_manager = TemplateManager()
        
        self.setWindowTitle("New Project from Template")
        self.setGeometry(100, 100, 800, 500)
        self.setMinimumSize(700, 400)
        
        self.setup_ui()
        self.load_templates()
        
        # Connect signals
        self.template_list.itemSelectionChanged.connect(self.on_template_selected)
        self.template_list.itemDoubleClicked.connect(self.on_template_double_clicked)
    
    def setup_ui(self):
        """Create the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Top section: Title and filter
        top_layout = QHBoxLayout()
        
        title_label = QLabel("Project Templates")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        top_layout.addWidget(title_label)
        
        top_layout.addStretch()
        
        filter_label = QLabel("Filter:")
        top_layout.addWidget(filter_label)
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter templates...")
        self.filter_edit.textChanged.connect(self.filter_templates)
        self.filter_edit.setMaximumWidth(200)
        top_layout.addWidget(self.filter_edit)
        
        main_layout.addLayout(top_layout)
        
        # Main content area
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Template list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Template list
        self.template_list = QListWidget()
        self.template_list.setAlternatingRowColors(True)
        self.template_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        left_layout.addWidget(self.template_list)
        
        # List actions
        list_actions_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_templates)
        list_actions_layout.addWidget(self.refresh_button)
        
        list_actions_layout.addStretch()
        left_layout.addLayout(list_actions_layout)
        
        main_splitter.addWidget(left_panel)
        
        # Right panel: Template details and actions
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Template details group
        details_group = QGroupBox("Template Details")
        details_layout = QVBoxLayout(details_group)
        
        # Template name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_label = QLabel("")
        self.name_label.setFont(QFont("", 12, QFont.Weight.Bold))
        name_layout.addWidget(self.name_label)
        name_layout.addStretch()
        details_layout.addLayout(name_layout)
        
        # Template description
        details_layout.addWidget(QLabel("Description:"))
        self.description_text = QTextEdit()
        self.description_text.setMaximumHeight(80)
        self.description_text.setReadOnly(True)
        details_layout.addWidget(self.description_text)
        
        # Template features
        features_group = QGroupBox("Template Features")
        features_layout = QVBoxLayout(features_group)
        
        self.features_label = QLabel("")
        self.features_label.setWordWrap(True)
        features_layout.addWidget(self.features_label)
        
        details_layout.addWidget(features_group)
        
        # Lithology rules preview
        rules_group = QGroupBox("Lithology Rules Preview")
        rules_layout = QVBoxLayout(rules_group)
        
        self.rules_text = QTextEdit()
        self.rules_text.setMaximumHeight(120)
        self.rules_text.setReadOnly(True)
        rules_layout.addWidget(self.rules_text)
        
        details_layout.addWidget(rules_group)
        
        right_layout.addWidget(details_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.create_button = QPushButton("Create New Project from Template")
        self.create_button.clicked.connect(self.create_from_template)
        self.create_button.setEnabled(False)
        self.create_button.setToolTip("Create a new project using the selected template")
        actions_layout.addWidget(self.create_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setToolTip("Close without creating a project")
        actions_layout.addWidget(self.cancel_button)
        
        right_layout.addWidget(actions_group)
        
        right_layout.addStretch()
        
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(main_splitter)
    
    def load_templates(self):
        """Load and display all templates."""
        self.template_list.clear()
        templates = self.template_manager.get_all_templates()
        
        for template in templates:
            item = QListWidgetItem(template.name)
            item.setData(Qt.ItemDataRole.UserRole, template.name)
            
            # Add description as tooltip
            item.setToolTip(template.description)
            
            self.template_list.addItem(item)
        
        # Update UI state
        self.update_ui_state()
    
    def filter_templates(self):
        """Filter templates based on search text."""
        filter_text = self.filter_edit.text().lower()
        
        for i in range(self.template_list.count()):
            item = self.template_list.item(i)
            item_text = item.text().lower()
            item.setHidden(filter_text not in item_text)
    
    def on_template_selected(self):
        """Handle template selection."""
        selected_items = self.template_list.selectedItems()
        
        if not selected_items:
            self.clear_template_details()
            self.update_ui_state()
            return
        
        template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        template = self.template_manager.get_template(template_name)
        
        if template:
            self.display_template_details(template)
        
        self.update_ui_state()
    
    def on_template_double_clicked(self, item):
        """Handle template double-click (create from template)."""
        template_name = item.data(Qt.ItemDataRole.UserRole)
        self.create_from_template_name(template_name)
    
    def display_template_details(self, template: ProjectTemplate):
        """Display template details in the details panel."""
        self.name_label.setText(template.name)
        self.description_text.setText(template.description)
        
        # Generate features text
        features = []
        
        # Count lithology rules
        features.append(f"• {len(template.lithology_rules)} lithology rules")
        
        # Workspace layout features
        if template.workspace_layout:
            layout = template.workspace_layout
            if "default_docks" in layout:
                features.append(f"• {len(layout['default_docks'])} default dock widgets")
            if "default_view" in layout:
                features.append(f"• {layout['default_view']} view mode")
            if "preferred_tools" in layout:
                features.append(f"• {len(layout['preferred_tools'])} preferred tools")
        
        # Default settings
        if template.default_settings:
            features.append(f"• {len(template.default_settings)} default settings")
        
        self.features_label.setText("\n".join(features))
        
        # Display lithology rules preview
        rules_text = []
        for rule in template.lithology_rules[:5]:  # Show first 5 rules
            rules_text.append(f"{rule['code']}: {rule['name']} (Gamma: {rule['gamma_min']}-{rule['gamma_max']}, Density: {rule['density_min']}-{rule['density_max']})")
        
        if len(template.lithology_rules) > 5:
            rules_text.append(f"... and {len(template.lithology_rules) - 5} more rules")
        
        self.rules_text.setText("\n".join(rules_text))
    
    def clear_template_details(self):
        """Clear template details panel."""
        self.name_label.clear()
        self.description_text.clear()
        self.features_label.clear()
        self.rules_text.clear()
    
    def update_ui_state(self):
        """Update UI button states based on selection."""
        has_selection = len(self.template_list.selectedItems()) > 0
        self.create_button.setEnabled(has_selection)
    
    def create_from_template(self):
        """Create new project from selected template."""
        selected_items = self.template_list.selectedItems()
        if not selected_items:
            return
        
        template_name = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.create_from_template_name(template_name)
    
    def create_from_template_name(self, template_name: str):
        """Create new project from template by name."""
        template = self.template_manager.get_template(template_name)
        if not template:
            QMessageBox.warning(self, "Error", f"Template '{template_name}' not found.")
            return
        
        # Confirm creation
        reply = QMessageBox.question(
            self, "Create New Project",
            f"Create new project from template '{template_name}'?\n\n"
            f"This will apply the template's lithology rules and settings to a new project.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Apply template settings
            success = self.template_manager.apply_template(template_name, self.main_window)
            
            if success:
                QMessageBox.information(
                    self, "Success", 
                    f"Project created from template '{template_name}'.\n\n"
                    f"Template settings have been applied. You can now start working with the new project."
                )
                self.template_selected.emit(template_name)
                self.accept()  # Close dialog
            else:
                QMessageBox.warning(
                    self, "Warning", 
                    f"Template '{template_name}' was applied with some issues.\n"
                    f"Some settings may not have been applied correctly."
                )
                self.template_selected.emit(template_name)
                self.accept()  # Close dialog
                
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Failed to create project from template:\n{str(e)}"
            )