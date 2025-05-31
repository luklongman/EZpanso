#!/usr/bin/env python3
"""
EZpanso - Simplified Core Implementation
A clean, minimal GUI for managing Espanso text expansion snippets.

Core Workflow:
1. Load all YAML files from match directory (including subfolders)
2. Hold matches in dictionaries per file
3. Populate table with trigger/replace columns for chosen file
4. Gray out rows with complex YAML (more than trigger/replace)
5. Allow in-place editing that updates the dictionary
6. Save with confirmation - overwrite original files
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QComboBox,
    QMessageBox, QHeaderView, QMenuBar
)

from simplified_file_handler import load_espanso_data_simple, save_file_simple
from simplified_data_model import Snippet
from utils import get_default_espanso_config_path
import constants as C

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleEZpanso(QMainWindow):
    """Simplified EZpanso main window focusing on core workflow."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZpanso - Simplified")
        self.resize(1000, 600)
        
        # Core data structures
        self.espanso_match_dir = ""
        self.files_data: Dict[str, List[Snippet]] = {}  # file_path -> snippets
        self.file_dropdown_map: Dict[str, str] = {}     # display_name -> file_path
        self.active_file_path: Optional[str] = None
        self.is_modified = False
        
        self._setup_ui()
        self._setup_menu()
        self._load_initial_data()
        
    def _setup_ui(self):
        """Setup the main UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # File selector
        file_layout = QHBoxLayout()
        self.file_selector = QComboBox()
        self.file_selector.currentIndexChanged.connect(self._on_file_selected)
        file_layout.addWidget(self.file_selector)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_data)
        file_layout.addWidget(refresh_btn)
        layout.addLayout(file_layout)
        
        # Snippets table
        self.snippet_table = QTableWidget()
        self.snippet_table.setColumnCount(2)
        self.snippet_table.setHorizontalHeaderLabels(["Trigger", "Replace"])
        
        # Configure table headers
        header = self.snippet_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.snippet_table.setColumnWidth(0, 250)
        
        # Enable in-place editing
        self.snippet_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.snippet_table.itemChanged.connect(self._on_item_edited)
        layout.addWidget(self.snippet_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save All Changes")
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        
        save_action = QAction("&Save All Changes", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_changes)
        file_menu.addAction(save_action)
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_data)
        file_menu.addAction(refresh_action)
        
    def _load_initial_data(self):
        """Load initial Espanso data."""
        # Try to find default Espanso directory
        self.espanso_match_dir = get_default_espanso_config_path()
        if not self.espanso_match_dir or not os.path.isdir(self.espanso_match_dir):
            QMessageBox.warning(
                self, "Directory Not Found",
                "Could not find default Espanso directory. Please set it manually."
            )
            return
            
        self._refresh_data()
        
    def _refresh_data(self):
        """Refresh data from Espanso files."""
        if not self.espanso_match_dir:
            return
            
        self.status_bar.showMessage("Loading files...")
        
        # Load data using existing file handler
        result = load_espanso_data(self.espanso_match_dir)
        
        self.files_data = result["snippets_by_file"]
        self.file_dropdown_map = result["file_dropdown_map"]
        
        # Update file selector
        self.file_selector.clear()
        display_names = result["file_display_names"]
        self.file_selector.addItems(display_names)
        
        # Show load status
        total_snippets = result["total_snippets_loaded"]
        file_count = len(self.files_data)
        self.status_bar.showMessage(f"Loaded {total_snippets} snippets from {file_count} files")
        
        # Handle errors
        if result["errors"]:
            error_msg = "\n".join([f"{file}: {error}" for file, error in result["errors"]])
            QMessageBox.warning(self, "Load Errors", f"Some files had errors:\n{error_msg}")
        
        self.is_modified = False
        self._update_window_title()
        
    def _on_file_selected(self, index: int):
        """Handle file selection from dropdown."""
        if index < 0 or not self.file_dropdown_map:
            self.active_file_path = None
            self._populate_table([])
            return
            
        display_name = self.file_selector.itemText(index)
        self.active_file_path = self.file_dropdown_map.get(display_name)
        
        if self.active_file_path:
            snippets = self.files_data.get(self.active_file_path, [])
            self._populate_table(snippets)
            self.status_bar.showMessage(f"File: {display_name} ({len(snippets)} snippets)")
        
    def _populate_table(self, snippets: List[Snippet]):
        """Populate table with snippets from current file."""
        # Clear table
        self.snippet_table.setRowCount(0)
        
        if not snippets:
            # Add empty row for new entries
            self._add_empty_row()
            return
            
        # Add snippet rows
        for i, snippet in enumerate(snippets):
            self.snippet_table.insertRow(i)
            
            # Check if this is a complex snippet (more than just trigger/replace)
            is_complex = self._is_complex_snippet(snippet)
            
            # Create table items
            trigger_item = QTableWidgetItem(snippet.trigger)
            replace_item = QTableWidgetItem(self._format_replace_text(snippet.replace_text))
            
            # Gray out complex snippets
            if is_complex:
                trigger_item.setFlags(trigger_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                replace_item.setFlags(replace_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                trigger_item.setBackground(Qt.GlobalColor.lightGray)
                replace_item.setBackground(Qt.GlobalColor.lightGray)
                
            self.snippet_table.setItem(i, 0, trigger_item)
            self.snippet_table.setItem(i, 1, replace_item)
            
        # Add empty row at bottom for new entries
        self._add_empty_row()
        
    def _is_complex_snippet(self, snippet: Snippet) -> bool:
        """Check if snippet has complex YAML structure beyond trigger/replace."""
        yaml_entry = snippet.original_yaml_entry
        
        # Count non-trigger/replace keys
        complex_keys = set(yaml_entry.keys()) - {C.COL_TRIGGER, C.COL_REPLACE}
        
        # Consider it complex if it has other keys or multiline replace
        return len(complex_keys) > 0 or '\n' in snippet.replace_text
        
    def _format_replace_text(self, text: str) -> str:
        """Format replace text for display (show first line if multiline)."""
        lines = text.splitlines()
        if len(lines) <= 1:
            return text
        return lines[0] + " ..."
        
    def _add_empty_row(self):
        """Add empty row at bottom for new snippet entry."""
        row = self.snippet_table.rowCount()
        self.snippet_table.insertRow(row)
        self.snippet_table.setItem(row, 0, QTableWidgetItem(""))
        self.snippet_table.setItem(row, 1, QTableWidgetItem(""))
        
    def _on_item_edited(self, item: QTableWidgetItem):
        """Handle in-place editing of table items."""
        if not self.active_file_path:
            return
            
        row = item.row()
        col = item.column()
        new_text = item.text().strip()
        
        snippets = self.files_data.get(self.active_file_path, [])
        
        # Check if this is the empty row at bottom
        if row >= len(snippets):
            if new_text:  # User entered text in empty row
                self._handle_new_snippet_entry(row, col, new_text)
            return
            
        # Editing existing snippet
        if row < len(snippets):
            snippet = snippets[row]
            
            # Don't allow editing complex snippets
            if self._is_complex_snippet(snippet):
                QMessageBox.information(
                    self, "Cannot Edit",
                    "This snippet has complex YAML structure and cannot be edited in-place."
                )
                # Revert the change
                if col == 0:
                    item.setText(snippet.trigger)
                else:
                    item.setText(self._format_replace_text(snippet.replace_text))
                return
                
            # Update snippet
            if col == 0:  # Trigger column
                # Check for duplicates
                if self._is_duplicate_trigger(new_text, snippets, exclude_index=row):
                    QMessageBox.warning(self, "Duplicate Trigger", f"Trigger '{new_text}' already exists!")
                    item.setText(snippet.trigger)  # Revert
                    return
                snippet.trigger = new_text
                snippet.original_yaml_entry[C.COL_TRIGGER] = new_text
            else:  # Replace column
                snippet.replace_text = new_text
                snippet.original_yaml_entry[C.COL_REPLACE] = new_text
                
            self.is_modified = True
            self._update_window_title()
            
    def _handle_new_snippet_entry(self, row: int, col: int, text: str):
        """Handle entry of new snippet in empty row."""
        # Get both cells
        trigger_item = self.snippet_table.item(row, 0)
        replace_item = self.snippet_table.item(row, 1)
        
        trigger = trigger_item.text().strip() if trigger_item else ""
        replace = replace_item.text().strip() if replace_item else ""
        
        # Need both trigger and replace to create snippet
        if trigger and replace:
            snippets = self.files_data.get(self.active_file_path, [])
            
            # Check for duplicates
            if self._is_duplicate_trigger(trigger, snippets):
                QMessageBox.warning(self, "Duplicate Trigger", f"Trigger '{trigger}' already exists!")
                if col == 0:  # Clear trigger if that's what was just entered
                    trigger_item.setText("")
                return
                
            # Create new snippet
            new_snippet = Snippet(trigger, replace, self.active_file_path)
            
            # Add to data
            if self.active_file_path not in self.files_data:
                self.files_data[self.active_file_path] = []
            self.files_data[self.active_file_path].append(new_snippet)
            
            # Add another empty row
            self._add_empty_row()
            
            self.is_modified = True
            self._update_window_title()
            
    def _is_duplicate_trigger(self, trigger: str, snippets: List[Snippet], exclude_index: int = -1) -> bool:
        """Check if trigger already exists in snippets list."""
        for i, snippet in enumerate(snippets):
            if i != exclude_index and snippet.trigger == trigger:
                return True
        return False
        
    def _save_changes(self):
        """Save all changes back to original YAML files."""
        if not self.is_modified:
            QMessageBox.information(self, "No Changes", "No changes to save.")
            return
            
        # Confirm save
        reply = QMessageBox.question(
            self, "Save Changes",
            "Save all changes to original files? This will overwrite the existing files.",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel
        )
        
        if reply != QMessageBox.StandardButton.Save:
            return
            
        self.status_bar.showMessage("Saving files...")
        
        # Save each modified file
        errors = []
        saved_count = 0
        
        for file_path, snippets in self.files_data.items():
            success, error = save_espanso_file(file_path, snippets)
            if success:
                saved_count += 1
            else:
                errors.append(f"{os.path.basename(file_path)}: {error}")
                
        # Show results
        if errors:
            error_msg = "\n".join(errors)
            QMessageBox.warning(self, "Save Errors", f"Some files failed to save:\n{error_msg}")
        else:
            QMessageBox.information(self, "Save Complete", f"Successfully saved {saved_count} files.")
            
        self.is_modified = False
        self._update_window_title()
        self.status_bar.showMessage(f"Saved {saved_count} files")
        
    def _update_window_title(self):
        """Update window title to show modification status."""
        base_title = "EZpanso - Simplified"
        if self.is_modified:
            self.setWindowTitle(f"{base_title} *")
        else:
            self.setWindowTitle(base_title)
            
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._save_changes()
                if self.is_modified:  # Save was cancelled or failed
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
                
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = SimpleEZpanso()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
