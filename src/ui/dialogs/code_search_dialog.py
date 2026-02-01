"""
Code Search Dialog for F3 key functionality.

Provides a searchable dialog for browsing and selecting codes
from all dictionary categories.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel, QPushButton,
    QSplitter, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QDialogButtonBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from ...core.dictionary_manager import get_dictionary_manager


class CodeSearchDialog(QDialog):
    """Dialog for searching and selecting codes from dictionaries."""
    
    code_selected = pyqtSignal(str, str)  # category, code
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary_manager = get_dictionary_manager()
        self.setup_ui()
        self.setWindowTitle("Code Search (F3)")
        self.resize(800, 600)
        
        # Load data
        self.load_categories()
        
        # Set up shortcuts
        self.setup_shortcuts()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search codes and descriptions...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        # Category filter
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        search_layout.addWidget(QLabel("Category:"))
        search_layout.addWidget(self.category_combo)
        
        # Show descriptions checkbox
        self.show_desc_check = QCheckBox("Show Descriptions")
        self.show_desc_check.setChecked(True)
        self.show_desc_check.stateChanged.connect(self.update_display)
        search_layout.addWidget(self.show_desc_check)
        
        layout.addLayout(search_layout)
        
        # Splitter for categories and codes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Categories tree
        self.categories_tree = QTreeWidget()
        self.categories_tree.setHeaderLabel("Categories")
        self.categories_tree.itemSelectionChanged.connect(self.on_category_selected)
        splitter.addWidget(self.categories_tree)
        
        # Codes list
        self.codes_list = QListWidget()
        self.codes_list.itemDoubleClicked.connect(self.on_code_double_clicked)
        self.codes_list.setAlternatingRowColors(True)
        splitter.addWidget(self.codes_list)
        
        # Set splitter sizes
        splitter.setSizes([200, 600])
        layout.addWidget(splitter)
        
        # Selected code info
        info_layout = QHBoxLayout()
        self.selected_label = QLabel("Selected: ")
        self.selected_label.setWordWrap(True)
        info_layout.addWidget(self.selected_label)
        layout.addLayout(info_layout)
        
        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to search
        self.search_input.setFocus()
    
    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # Enter to accept
        enter_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Return), self)
        enter_shortcut.activated.connect(self.accept)
        
        # Escape to cancel
        esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc_shortcut.activated.connect(self.reject)
        
        # Ctrl+F to focus search
        ctrl_f_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        ctrl_f_shortcut.activated.connect(self.focus_search)
    
    def focus_search(self):
        """Focus the search input."""
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def load_categories(self):
        """Load categories into the tree and combo box."""
        if not self.dictionary_manager or not self.dictionary_manager.is_loaded:
            return
        
        categories = self.dictionary_manager.get_all_categories()
        self.categories_tree.clear()
        
        # Add "All" category
        all_item = QTreeWidgetItem(self.categories_tree, ["All Categories"])
        all_item.setData(0, Qt.ItemDataRole.UserRole, None)
        
        # Add actual categories
        for category in categories:
            item = QTreeWidgetItem(self.categories_tree, [category])
            item.setData(0, Qt.ItemDataRole.UserRole, category)
        
        self.categories_tree.expandAll()
        
        # Update combo box
        self.category_combo.clear()
        self.category_combo.addItem("All Categories")
        for category in categories:
            self.category_combo.addItem(category)
    
    def load_codes(self, category: str = None, search_text: str = None):
        """Load codes into the list based on category and search."""
        self.codes_list.clear()
        
        if not self.dictionary_manager or not self.dictionary_manager.is_loaded:
            return
        
        # Get codes
        if category and category != "All Categories":
            codes = self.dictionary_manager.get_codes_for_category(category)
            self.display_codes(codes, category, search_text)
        else:
            # Show all codes grouped by category
            categories = self.dictionary_manager.get_all_categories()
            for cat in categories:
                codes = self.dictionary_manager.get_codes_for_category(cat)
                if codes:
                    # Add category header
                    header_item = QListWidgetItem(f"--- {cat} ---")
                    header_item.setFlags(Qt.ItemFlag.NoItemFlags)
                    header_item.setBackground(Qt.GlobalColor.lightGray)
                    font = header_item.font()
                    font.setBold(True)
                    header_item.setFont(font)
                    self.codes_list.addItem(header_item)
                    
                    # Add codes for this category
                    self.display_codes(codes, cat, search_text, indent=True)
    
    def display_codes(self, codes, category: str, search_text: str = None, indent: bool = False):
        """Display codes in the list with optional filtering."""
        show_descriptions = self.show_desc_check.isChecked()
        
        for code, desc in codes:
            # Apply search filter
            if search_text and search_text.strip():
                search_lower = search_text.lower()
                if (search_lower not in code.lower() and 
                    search_lower not in desc.lower()):
                    continue
            
            # Create display text
            if show_descriptions:
                display_text = f"{desc} ({code})"
            else:
                display_text = code
            
            if indent:
                display_text = f"    {display_text}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, (category, code, desc))
            
            # Tooltip with full info
            item.setToolTip(f"Category: {category}\nCode: {code}\nDescription: {desc}")
            
            self.codes_list.addItem(item)
    
    def on_search_changed(self, text: str):
        """Handle search text changes with debouncing."""
        # Use a timer to debounce rapid typing
        if hasattr(self, '_search_timer'):
            self._search_timer.stop()
        
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(lambda: self.perform_search(text))
        self._search_timer.start(300)  # 300ms delay
    
    def perform_search(self, text: str):
        """Perform the actual search."""
        category = self.category_combo.currentText()
        self.load_codes(category, text)
    
    def on_category_changed(self, category: str):
        """Handle category filter changes."""
        self.load_codes(category, self.search_input.text())
    
    def on_category_selected(self):
        """Handle category tree selection."""
        items = self.categories_tree.selectedItems()
        if not items:
            return
        
        item = items[0]
        category = item.data(0, Qt.ItemDataRole.UserRole)
        
        if category is None:
            self.category_combo.setCurrentText("All Categories")
        else:
            self.category_combo.setCurrentText(category)
    
    def update_display(self):
        """Update display when show descriptions checkbox changes."""
        self.load_codes(self.category_combo.currentText(), self.search_input.text())
    
    def on_code_double_clicked(self, item):
        """Handle double-click on code item."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            category, code, desc = data
            self.code_selected.emit(category, code)
            self.accept()
    
    def get_selected_code(self):
        """Get the currently selected code."""
        items = self.codes_list.selectedItems()
        if not items:
            return None
        
        item = items[0]
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            return data  # (category, code, description)
        return None
    
    def accept(self):
        """Handle dialog acceptance."""
        selected = self.get_selected_code()
        if selected:
            category, code, desc = selected
            self.code_selected.emit(category, code)
        
        super().accept()
    
    def showEvent(self, event):
        """Handle show event to refresh data."""
        super().showEvent(event)
        self.load_categories()
        self.load_codes()
        self.search_input.clear()
        self.search_input.setFocus()


class QuickCodeSearchDialog(QDialog):
    """
    Simplified version for quick code insertion.
    Designed to be non-modal and stay on top.
    """
    
    code_selected = pyqtSignal(str)  # just the code
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dictionary_manager = get_dictionary_manager()
        self.setup_ui()
        self.setWindowTitle("Quick Code Search")
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        self.resize(400, 300)
    
    def setup_ui(self):
        """Set up simplified UI."""
        layout = QVBoxLayout(self)
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search codes...")
        self.search_input.textChanged.connect(self.on_search)
        layout.addWidget(self.search_input)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.results_list)
        
        # Status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def on_search(self, text: str):
        """Handle search text changes."""
        self.results_list.clear()
        
        if not text.strip():
            self.status_label.setText("Type to search")
            return
        
        if not self.dictionary_manager or not self.dictionary_manager.is_loaded:
            self.status_label.setText("Dictionaries not loaded")
            return
        
        # Search across all categories
        results = self.dictionary_manager.search_codes(text)
        
        if not results:
            self.status_label.setText(f"No results for '{text}'")
            return
        
        # Display results
        for category, code, desc in results:
            item_text = f"{code}: {desc} [{category}]"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, code)
            item.setToolTip(f"Category: {category}\nCode: {code}\nDescription: {desc}")
            self.results_list.addItem(item)
        
        self.status_label.setText(f"Found {len(results)} result(s)")
        
        # Select first item
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)
    
    def on_item_double_clicked(self, item):
        """Handle double-click on result item."""
        code = item.data(Qt.ItemDataRole.UserRole)
        if code:
            self.code_selected.emit(code)
            self.close()
    
    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Return and self.results_list.currentItem():
            # Enter key selects current item
            item = self.results_list.currentItem()
            code = item.data(Qt.ItemDataRole.UserRole)
            if code:
                self.code_selected.emit(code)
                self.close()
        elif event.key() == Qt.Key.Key_Up or event.key() == Qt.Key.Key_Down:
            # Arrow keys navigate list
            self.results_list.keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def show_at_cursor(self):
        """Show dialog at cursor position."""
        cursor_pos = self.parent().cursor().pos()
        self.move(cursor_pos)
        self.show()
        self.search_input.setFocus()
        self.search_input.selectAll()