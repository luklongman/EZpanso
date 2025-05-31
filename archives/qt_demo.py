"""
Demo of Espanso Manager using PyQt6 with native macOS look and feel.
This is a small demonstration showing how the snippet management could look with PyQt6.
"""

import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, 
                           QPushButton, QStatusBar, QHeaderView, QStyle, 
                           QStyleOptionHeader, QStyledItemDelegate)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QKeySequence, QAction, QFont, QShortcut
import constants as C

class SnippetTableDelegate(QStyledItemDelegate):
    """Custom delegate for better table cell rendering"""
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        option.textElideMode = Qt.TextElideMode.ElideRight

class EspansoManagerDemo(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(C.TITLE_APP)
        self.resize(1000, 600)
        
        # Setup central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Category selector (ComboBox with native macOS style)
        self.category_selector = QComboBox()
        self.category_selector.setMinimumWidth(200)
        self.category_selector.addItems(["Email Templates", "Code Snippets", "Personal"])
        layout.addWidget(self.category_selector)

        # Snippet table (with native macOS style)
        self.snippet_table = QTableWidget()
        self.snippet_table.setColumnCount(2)
        self.snippet_table.setHorizontalHeaderLabels(["Trigger", "Replace With"])
        self.snippet_table.setItemDelegate(SnippetTableDelegate())
        
        # Set table properties for native look
        self.snippet_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.snippet_table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self.snippet_table.verticalHeader().hide()
        self.snippet_table.setAlternatingRowColors(True)
        self.snippet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.snippet_table)

        # Button bar
        button_layout = QHBoxLayout()
        new_snippet_btn = QPushButton("New Snippet")
        edit_snippet_btn = QPushButton("Edit")
        delete_snippet_btn = QPushButton("Delete")
        
        for btn in (new_snippet_btn, edit_snippet_btn, delete_snippet_btn):
            btn.setAutoDefault(False)
            button_layout.addWidget(btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status bar (native macOS style)
        self.statusBar().showMessage(C.MSG_WELCOME)

        # Setup menu bar (native macOS menu)
        self._setup_menu()
        
        # Add some sample data
        self._add_sample_data()
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def _setup_menu(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_snippet_action = QAction('New Snippet', self)
        new_snippet_action.setShortcut(QKeySequence(C.SHORTCUT_NEW_SNIPPET))
        file_menu.addAction(new_snippet_action)
        
        save_action = QAction('Save All Changes', self)
        save_action.setShortcut(QKeySequence(C.SHORTCUT_SAVE))
        file_menu.addAction(save_action)

    def _setup_shortcuts(self):
        # Up/Down navigation
        QShortcut(QKeySequence("Up"), self.snippet_table, self._move_selection_up)
        QShortcut(QKeySequence("Down"), self.snippet_table, self._move_selection_down)
        
        # Return to edit
        QShortcut(QKeySequence("Return"), self.snippet_table, self._edit_selected)
        
        # Escape to deselect
        QShortcut(QKeySequence("Escape"), self.snippet_table, self.snippet_table.clearSelection)

    def _add_sample_data(self):
        sample_data = [
            ("@email", "your.name@example.com"),
            ("@addr", "123 Main St, City, Country"),
            ("@thanks", "Thank you for your message. I will get back to you soon."),
        ]
        
        self.snippet_table.setRowCount(len(sample_data))
        for row, (trigger, replace) in enumerate(sample_data):
            self.snippet_table.setItem(row, 0, QTableWidgetItem(trigger))
            self.snippet_table.setItem(row, 1, QTableWidgetItem(replace))

    def _move_selection_up(self):
        current = self.snippet_table.currentRow()
        if current > 0:
            self.snippet_table.selectRow(current - 1)

    def _move_selection_down(self):
        current = self.snippet_table.currentRow()
        if current < self.snippet_table.rowCount() - 1:
            self.snippet_table.selectRow(current + 1)

    def _edit_selected(self):
        current = self.snippet_table.currentRow()
        if current >= 0:
            # In a real implementation, this would open the edit dialog
            self.statusBar().showMessage("Editing snippet...")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set fusion style for consistent look
    app.setStyle('Fusion')
    
    # Increase font sizes slightly for better macOS rendering
    font = app.font()
    font.setPointSize(13)
    app.setFont(font)
    
    window = EspansoManagerDemo()
    window.show()
    sys.exit(app.exec())
