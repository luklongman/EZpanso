#!/usr/bin/env python3
"""
EZpanso - Core Simplified Implementation
Focuses purely on the 7-step workflow without overcomplications.

Core Workflow:
1. safe_load all YAML files under match folder (including subfolders)
2. Per file, hold matches in dictionaries 
3. For chosen file (dropdown), populate table with trigger/replace columns
4. Gray out rows with more vars or more than 2 items, prevent editing
5. Allow in-place editing (no dialogs needed)
6. Update dictionary as user edits table
7. Save with confirmation, overwrite original YAML
"""

import sys
import os
import yaml
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QComboBox,
    QMessageBox, QHeaderView, QMenuBar
)

# Simple data structure - no complex Snippet class needed
FileData = Dict[str, List[Dict[str, Any]]]  # file_path -> list of match dictionaries


class CoreEZpanso(QMainWindow):
    """Core simplified implementation focusing on the exact 7-step workflow."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZpanso - Core")
        self.resize(800, 600)
        
        # Step 1-2: Data storage - simple dictionaries
        self.files_data: FileData = {}  # file_path -> list of match dicts
        self.file_paths: List[str] = []  # ordered list of file paths
        self.display_name_to_path: Dict[str, str] = {}  # display name -> file path mapping
        self.active_file_path: Optional[str] = None
        self.is_modified = False
        
        self._setup_ui()
        self._load_all_yaml_files()
        
    def _setup_ui(self):
        """Simple UI setup."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # File selector dropdown
        file_layout = QHBoxLayout()
        self.file_selector = QComboBox()
        self.file_selector.currentTextChanged.connect(self._on_file_selected)
        file_layout.addWidget(self.file_selector)
        
        save_btn = QPushButton("Save All")
        save_btn.clicked.connect(self._save_all_with_confirmation)
        file_layout.addWidget(save_btn)
        
        layout.addLayout(file_layout)
        
        # Step 3: Table with trigger/replace columns
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Trigger", "Replace"])
        
        # Configure column resize modes
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.table.setColumnWidth(0, 200)
        
        # Step 5: Enable in-place editing
        self.table.itemChanged.connect(self._on_item_changed)
        
        layout.addWidget(self.table)
        
    def _load_all_yaml_files(self):
        """Step 1: safe_load all YAML files under match folder."""
        # Simple auto-detection of Espanso directory
        espanso_dir = os.path.expanduser("~/Library/Application Support/espanso/match")
        if not os.path.isdir(espanso_dir):
            espanso_dir = os.path.expanduser("~/.config/espanso/match")
        
        if not os.path.isdir(espanso_dir):
            QMessageBox.warning(self, "Error", "Could not find Espanso match directory")
            return
            
        # Walk through all files including subfolders
        for root, dirs, files in os.walk(espanso_dir):
            for filename in sorted(files):
                # Skip files that start with "_"
                if filename.startswith('_'):
                    continue
                    
                if filename.endswith(('.yml', '.yaml')):
                    file_path = os.path.join(root, filename)
                    self._load_single_yaml_file(file_path)
        
        # Create display names and populate file selector
        display_names = []
        for file_path in self.file_paths:
            display_name = self._get_display_name(file_path)
            display_names.append(display_name)
            self.display_name_to_path[display_name] = file_path
        
        self.file_selector.addItems(display_names)
        if display_names:
            self._on_file_selected(display_names[0])
    
    def _get_display_name(self, file_path: str) -> str:
        """Get display name for a file, using parent folder name for package.yml files."""
        filename = os.path.basename(file_path)
        if filename.lower() == 'package.yml':
            # Use parent folder name
            parent_folder = os.path.basename(os.path.dirname(file_path))
            return f"{parent_folder} (package)"
        return filename
    
    def _load_single_yaml_file(self, file_path: str):
        """Step 2: Load matches into dictionary per file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_content = yaml.safe_load(f) or {}
            
            # Skip files that don't contain a dictionary or don't have matches
            if not isinstance(yaml_content, dict):
                return
                
            matches = yaml_content.get('matches', [])
            if isinstance(matches, list) and matches:  # Only add if has actual matches
                self.files_data[file_path] = matches
                self.file_paths.append(file_path)
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    def _on_file_selected(self, display_name: str):
        """Step 3: Populate table for chosen file."""
        # Find file path from display name
        self.active_file_path = self.display_name_to_path.get(display_name)
        
        if not self.active_file_path:
            return
            
        matches = self.files_data.get(self.active_file_path, [])
        self._populate_table(matches)
    
    def _populate_table(self, matches: List[Dict[str, Any]]):
        """Populate table with matches, graying out complex ones."""
        self.table.blockSignals(True)
        self.table.setRowCount(len(matches))
        
        for i, match in enumerate(matches):
            trigger = str(match.get('trigger', ''))
            replace = str(match.get('replace', ''))
            
            # Step 4: Check if complex (more than trigger/replace)
            is_complex = self._is_complex_match(match)
            
            # Create table items
            trigger_item = QTableWidgetItem(trigger)
            replace_item = QTableWidgetItem(replace)
            
            if is_complex:
                # Gray out complex matches and prevent editing
                gray_brush = QBrush(QColor(180, 180, 180))
                trigger_item.setBackground(gray_brush)
                replace_item.setBackground(gray_brush)
                trigger_item.setFlags(trigger_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                replace_item.setFlags(replace_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            self.table.setItem(i, 0, trigger_item)
            self.table.setItem(i, 1, replace_item)
        
        self.table.blockSignals(False)
    
    def _is_complex_match(self, match: Dict[str, Any]) -> bool:
        """Step 4: Determine if match has more than trigger/replace."""
        # Check for extra keys beyond trigger/replace
        simple_keys = {'trigger', 'replace'}
        extra_keys = set(match.keys()) - simple_keys
        
        # Consider complex if has extra keys or vars
        return len(extra_keys) > 0 or 'vars' in match
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Step 5-6: Handle in-place editing and update dictionary."""
        if not self.active_file_path:
            return
            
        row = item.row()
        col = item.column()
        new_value = item.text()
        
        matches = self.files_data[self.active_file_path]
        if row >= len(matches):
            return
            
        match = matches[row]
        
        # Step 6: Update dictionary directly
        if col == 0:  # Trigger column
            # Check for duplicates
            for i, other_match in enumerate(matches):
                if i != row and other_match.get('trigger') == new_value:
                    QMessageBox.warning(self, "Duplicate", f"Trigger '{new_value}' already exists!")
                    item.setText(str(match.get('trigger', '')))  # Revert
                    return
            match['trigger'] = new_value
        elif col == 1:  # Replace column
            match['replace'] = new_value
        
        self.is_modified = True
        self._update_title()
    
    def _save_all_with_confirmation(self):
        """Step 7: Save with confirmation, overwrite original YAML."""
        if not self.is_modified:
            QMessageBox.information(self, "Info", "No changes to save.")
            return
        
        reply = QMessageBox.question(
            self, "Save Changes", 
            f"Save changes to {len(self.files_data)} file(s)?\nThis will overwrite the original files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._save_all_files()
    
    def _save_all_files(self):
        """Direct overwrite of original YAML files."""
        saved_count = 0
        
        for file_path, matches in self.files_data.items():
            try:
                # Read existing file to preserve other keys
                existing_content = {}
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_content = yaml.safe_load(f) or {}
                
                # Update matches section
                existing_content['matches'] = matches
                
                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(existing_content, f, sort_keys=False, allow_unicode=True)
                
                saved_count += 1
                
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Error saving {file_path}:\n{e}")
        
        self.is_modified = False
        self._update_title()
        QMessageBox.information(self, "Saved", f"Successfully saved {saved_count} file(s).")
    
    def _update_title(self):
        """Update window title with modification indicator."""
        base_title = "EZpanso - Core"
        self.setWindowTitle(f"{base_title}{' *' if self.is_modified else ''}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoreEZpanso()
    window.show()
    sys.exit(app.exec())
