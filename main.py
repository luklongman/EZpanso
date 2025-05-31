#!/usr/bin/env python3
import sys
import os
import yaml
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QComboBox,
    QMessageBox, QHeaderView, QLineEdit, QLabel, QDialog, QMenu
)
from PyQt6.QtGui import QKeySequence, QShortcut

FileData = Dict[str, List[Dict[str, Any]]]  # file_path -> list of match dictionaries


class EZpanso(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZpanso")
        self.resize(800, 600)
        
        # Step 1-2: Data storage - simple dictionaries
        self.files_data: FileData = {}  # file_path -> list of match dicts
        self.file_paths: List[str] = []  # ordered list of file paths
        self.display_name_to_path: Dict[str, str] = {}  # display name -> file path mapping
        self.active_file_path: Optional[str] = None
        self.is_modified = False
        
        # For sorting and filtering
        self.current_matches: List[Dict[str, Any]] = []  # Current file's matches
        self.filtered_indices: List[int] = []  # Indices of visible rows
        
        # Undo/Redo system
        self.undo_stack: List[Dict[str, Any]] = []  # Stack of undo states
        self.redo_stack: List[Dict[str, Any]] = []  # Stack of redo states
        self.max_undo_steps = 50  # Limit undo history
        
        self._setup_ui()
        self._load_all_yaml_files()
        
    def _setup_ui(self):
        """Simple UI setup."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        self.resize(600, 880)  # Make window thinner and longer
        
        # File selector dropdown
        file_layout = QHBoxLayout()
        self.file_selector = QComboBox()
        self.file_selector.currentTextChanged.connect(self._on_file_selected)
        file_layout.addWidget(self.file_selector)
        
        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Filter...")
        self.filter_box.setMaximumWidth(200)
        self.filter_box.textChanged.connect(self._apply_filter)
        file_layout.addWidget(self.filter_box)
        
        layout.addLayout(file_layout)
        
        # Step 3: Table with trigger/replace columns
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Trigger", "Replace"])
        
        # Enable sorting
        self.table.setSortingEnabled(True)
        
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Enable multiple selection
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Configure column resize modes
        header = self.table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.table.setColumnWidth(0, 144)
        
        # Step 5: Enable in-place editing
        self.table.itemChanged.connect(self._on_item_changed)
        
        layout.addWidget(self.table)
        
        # Setup keyboard shortcuts (cross-platform using Qt standard)
        new_shortcut = QShortcut(QKeySequence.StandardKey.New, self)
        new_shortcut.activated.connect(self._add_new_snippet)
        
        save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
        save_shortcut.activated.connect(self._save_all_with_confirmation)
        
        find_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        find_shortcut.activated.connect(self._focus_filter)
        
        # Delete key shortcuts - using specific key codes for better cross-platform support
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self._delete_selected_snippets)
        
        backspace_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        backspace_shortcut.activated.connect(self._delete_selected_snippets)
        
        # Undo/Redo shortcuts
        undo_shortcut = QShortcut(QKeySequence.StandardKey.Undo, self)
        undo_shortcut.activated.connect(self._undo)
        
        redo_shortcut = QShortcut(QKeySequence.StandardKey.Redo, self)
        redo_shortcut.activated.connect(self._redo)
        
        # Get platform-specific shortcut strings for button labels
        if sys.platform == 'darwin':  # macOS
            new_key = "⌘N"
            save_key = "⌘S"
            find_key = "⌘F"
            undo_key = "⌘Z"
            redo_key = "⌘⇧Z"
        else:  # Windows/Linux/Unix
            new_key = "Ctrl+N"
            save_key = "Ctrl+S"
            find_key = "Ctrl+F"
            undo_key = "Ctrl+Z"
            redo_key = "Ctrl+Y"  # This is the only different one
        
        # Update filter box placeholder with find shortcut
        self.filter_box.setPlaceholderText(f"Find ({find_key})...")
        
        # Bottom button layout: New (left) and Save (right)
        bottom_btn_layout = QHBoxLayout()
        
        new_btn = QPushButton(f"New ({new_key})")
        new_btn.clicked.connect(self._add_new_snippet)
        bottom_btn_layout.addWidget(new_btn)
        
        bottom_btn_layout.addStretch()
        
        save_btn = QPushButton(f"Save ({save_key})")
        save_btn.clicked.connect(self._save_all_with_confirmation)
        bottom_btn_layout.addWidget(save_btn)
        
        layout.addLayout(bottom_btn_layout)
        
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
            
        # Clear filter when switching files
        if hasattr(self, 'filter_box'):
            self.filter_box.clear()
            
        matches = self.files_data.get(self.active_file_path, [])
        self._populate_table(matches)
    
    def _populate_table(self, matches: List[Dict[str, Any]]):
        """Populate table with matches, graying out complex ones."""
        # Store the original matches
        self.current_matches = matches.copy()
        
        # Sort: Editable entries first, then alphabetical by trigger
        sorted_matches = self._sort_matches(matches)
        
        self.table.blockSignals(True)
        self.table.setSortingEnabled(False)  # Disable during population
        self.table.setRowCount(len(sorted_matches))
        
        for i, match in enumerate(sorted_matches):
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
        
        self.table.setSortingEnabled(True)  # Re-enable sorting
        self.table.blockSignals(False)
        
        # Initialize filter indices
        self.filtered_indices = list(range(len(sorted_matches)))
        self._apply_filter()
    
    def _is_complex_match(self, match: Dict[str, Any]) -> bool:
        """Step 4: Determine if match has more than trigger/replace."""
        # Check for extra keys beyond trigger/replace
        simple_keys = {'trigger', 'replace'}
        extra_keys = set(match.keys()) - simple_keys
        
        # Consider complex if has extra keys or vars
        return len(extra_keys) > 0 or 'vars' in match
    
    def _sort_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort matches: editable entries first, then alphabetical by trigger."""
        def sort_key(match):
            is_complex = self._is_complex_match(match)
            trigger = str(match.get('trigger', '')).lower()
            # Return tuple: (is_complex, trigger) - False sorts before True
            return (is_complex, trigger)
        
        return sorted(matches, key=sort_key)
    
    def _apply_filter(self):
        """Apply filter to table rows based on search text."""
        if not hasattr(self, 'filter_box'):
            return
            
        filter_text = self.filter_box.text().lower()
        
        # Show/hide rows based on filter
        for row in range(self.table.rowCount()):
            trigger_item = self.table.item(row, 0)
            replace_item = self.table.item(row, 1)
            
            if trigger_item and replace_item:
                trigger_text = trigger_item.text().lower()
                replace_text = replace_item.text().lower()
                
                # Show row if filter text is found in either trigger or replace
                show_row = (filter_text in trigger_text or 
                           filter_text in replace_text or 
                           filter_text == "")
                
                self.table.setRowHidden(row, not show_row)
    
    def _focus_filter(self):
        """Focus the filter input field for Find shortcut."""
        self.filter_box.setFocus()
        self.filter_box.selectAll()
    
    def _show_context_menu(self, position):
        """Show context menu for table right-click."""
        item = self.table.itemAt(position)
        if not item:
            return
        
        # Get selected rows
        selected_rows = self._get_selected_editable_rows()
        if not selected_rows:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Get delete key shortcut string (Del key)
        delete_key = "Del"  # Simple cross-platform representation
        
        if len(selected_rows) == 1:
            delete_action = menu.addAction(f"Delete snippet ({delete_key})")
        else:
            delete_action = menu.addAction(f"Delete {len(selected_rows)} snippets ({delete_key})")
        
        # Connect the action after creation
        if delete_action:
            delete_action.triggered.connect(lambda checked=False: self._delete_selected_snippets())
        
        # Show menu at cursor position
        menu.exec(self.table.mapToGlobal(position))
    
    def _delete_snippet(self, row):
        """Delete a snippet from the current file."""
        if not self.active_file_path:
            return
        
        # Get the trigger to identify which snippet to delete
        trigger_item = self.table.item(row, 0)
        if not trigger_item:
            return
        
        trigger = trigger_item.text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Delete Snippet", 
            f"Delete snippet '{trigger}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Find and remove the snippet from files_data
        matches = self.files_data[self.active_file_path]
        for i, match in enumerate(matches):
            if str(match.get('trigger', '')) == trigger:
                matches.pop(i)
                break
        
        # Mark as modified and refresh table
        self.is_modified = True
        self._update_title()
        self._populate_table(matches)
    
    def _get_selected_editable_rows(self):
        """Get list of selected rows that contain editable (non-complex) snippets."""
        selected_rows = []
        selection_model = self.table.selectionModel()
        if not selection_model:
            return selected_rows
        
        selected_indexes = selection_model.selectedRows()
        for index in selected_indexes:
            row = index.row()
            trigger_item = self.table.item(row, 0)
            
            # Only include editable (non-grayed) items
            if trigger_item and (trigger_item.flags() & Qt.ItemFlag.ItemIsEditable):
                selected_rows.append(row)
        
        return selected_rows
    
    def _delete_selected_snippets(self):
        """Delete all selected snippets."""
        if not self.active_file_path:
            return
        
        selected_rows = self._get_selected_editable_rows()
        if not selected_rows:
            return
        
        # Get triggers for confirmation and deletion
        triggers_to_delete = []
        for row in selected_rows:
            trigger_item = self.table.item(row, 0)
            if trigger_item:
                triggers_to_delete.append(trigger_item.text())
        
        if not triggers_to_delete:
            return
        
        # Confirm deletion
        if len(triggers_to_delete) == 1:
            message = f"Delete snippet '{triggers_to_delete[0]}'?"
        else:
            message = f"Delete {len(triggers_to_delete)} snippets?"
        
        reply = QMessageBox.question(
            self, "Delete Snippets", 
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Save state before deletion
        if len(triggers_to_delete) == 1:
            self._save_state(f"Delete snippet: '{triggers_to_delete[0]}'")
        else:
            self._save_state(f"Delete {len(triggers_to_delete)} snippets")
        
        # Remove snippets from files_data
        matches = self.files_data[self.active_file_path]
        # Remove in reverse order to avoid index issues, or use trigger matching
        remaining_matches = []
        for match in matches:
            trigger = str(match.get('trigger', ''))
            if trigger not in triggers_to_delete:
                remaining_matches.append(match)
        
        self.files_data[self.active_file_path] = remaining_matches
        
        # Mark as modified and refresh table
        self.is_modified = True
        self._update_title()
        self._populate_table(remaining_matches)
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Step 5-6: Handle in-place editing and update dictionary."""
        if not self.active_file_path:
            return
            
        row = item.row()
        col = item.column()
        new_value = item.text()
        
        # Get the trigger value to find the corresponding match in original data
        trigger_item = self.table.item(row, 0)
        if not trigger_item:
            return
            
        current_trigger = trigger_item.text()
        
        # Find the match in the original files_data
        matches = self.files_data[self.active_file_path]
        target_match = None
        target_index = -1
        
        for i, match in enumerate(matches):
            if str(match.get('trigger', '')) == current_trigger:
                target_match = match
                target_index = i
                break
        
        if target_match is None:
            return
        
        # Save state before making changes
        old_value = target_match.get('trigger' if col == 0 else 'replace', '')
        if str(old_value) != new_value:  # Only save state if value actually changed
            if col == 0:
                self._save_state(f"Edit trigger: '{old_value}' → '{new_value}'")
            else:
                self._save_state(f"Edit replace: '{current_trigger}' content")
        
        # Step 6: Update dictionary directly
        if col == 0:  # Trigger column
            # Check for duplicates in the original data
            for i, other_match in enumerate(matches):
                if i != target_index and other_match.get('trigger') == new_value:
                    QMessageBox.warning(self, "Duplicate", f"Trigger '{new_value}' already exists!")
                    item.setText(str(target_match.get('trigger', '')))  # Revert
                    return
            target_match['trigger'] = new_value
        elif col == 1:  # Replace column
            target_match['replace'] = new_value
        
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
        base_title = "EZpanso"
        self.setWindowTitle(f"{base_title}{' *' if self.is_modified else ''}")
    
    def _add_new_snippet(self):
        """Add a new snippet via dialog."""
        if not self.active_file_path:
            QMessageBox.information(self, "No File", "Please select a file first.")
            return
        
        # Simple input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("New Snippet")
        dialog.setModal(True)
        dialog.resize(400, 120)
        
        layout = QVBoxLayout(dialog)
        
        # Trigger input
        trigger_layout = QHBoxLayout()
        label = QLabel("Trigger:")
        label.setMinimumWidth(60)  # Set fixed width for labels
        trigger_layout.addWidget(label)
        trigger_input = QLineEdit()
        trigger_input.setPlaceholderText(":email")
        trigger_layout.addWidget(trigger_input)
        layout.addLayout(trigger_layout)
        
        # Replace input
        replace_layout = QHBoxLayout()
        label = QLabel("Replace:")
        label.setMinimumWidth(60)  # Same fixed width for consistency
        replace_layout.addWidget(label)
        replace_input = QLineEdit()
        replace_input.setPlaceholderText("johnny@water.com")
        replace_layout.addWidget(replace_input)
        layout.addLayout(replace_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setDefault(True)
        button_layout.addWidget(add_btn)
        
        layout.addLayout(button_layout)
        
        trigger_input.setFocus()
        
        # Show dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            trigger = trigger_input.text().strip()
            replace = replace_input.text().strip()
            
            if not trigger or not replace:
                QMessageBox.warning(self, "Invalid Input", "Both trigger and replace must be filled.")
                return
            
            # Check for duplicates
            existing_triggers = [match.get('trigger', '') for match in self.files_data[self.active_file_path]]
            if trigger in existing_triggers:
                QMessageBox.warning(self, "Duplicate", f"Trigger '{trigger}' already exists.")
                return
            
            # Save state before adding new snippet
            self._save_state(f"Add snippet: '{trigger}'")
            
            # Add new snippet
            new_snippet = {'trigger': trigger, 'replace': replace}
            self.files_data[self.active_file_path].append(new_snippet)
            
            # Mark as modified and refresh
            self.is_modified = True
            self._update_title()
            
            # Refresh table
            matches = self.files_data.get(self.active_file_path, [])
            self._populate_table(matches)

    def _save_state(self, description: str):
        """Save current state to undo stack for operation tracking."""
        if not self.active_file_path:
            return
            
        # Create state snapshot
        state = {
            'description': description,
            'file_path': self.active_file_path,
            'matches': [match.copy() for match in self.files_data[self.active_file_path]],
            'is_modified': self.is_modified
        }
        
        # Add to undo stack
        self.undo_stack.append(state)
        
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is performed
        self.redo_stack.clear()

    def _undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            return
        
        # Save current state to redo stack before undoing
        if self.active_file_path:
            current_state = {
                'description': 'redo_point',
                'file_path': self.active_file_path,
                'matches': [match.copy() for match in self.files_data[self.active_file_path]],
                'is_modified': self.is_modified
            }
            self.redo_stack.append(current_state)
        
        # Restore previous state
        state = self.undo_stack.pop()
        
        # Switch to the file if needed
        if state['file_path'] != self.active_file_path:
            # Find the display name for this file path
            for display_name, file_path in self.display_name_to_path.items():
                if file_path == state['file_path']:
                    self.file_selector.setCurrentText(display_name)
                    break
        
        # Restore the data
        self.files_data[state['file_path']] = [match.copy() for match in state['matches']]
        self.is_modified = state['is_modified']
        
        # Refresh UI
        self._update_title()
        if self.active_file_path == state['file_path']:
            self._populate_table(self.files_data[state['file_path']])

    def _redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            return
        
        # Save current state to undo stack before redoing
        if self.active_file_path:
            current_state = {
                'description': 'undo_point',
                'file_path': self.active_file_path,
                'matches': [match.copy() for match in self.files_data[self.active_file_path]],
                'is_modified': self.is_modified
            }
            self.undo_stack.append(current_state)
        
        # Restore redo state
        state = self.redo_stack.pop()
        
        # Switch to the file if needed
        if state['file_path'] != self.active_file_path:
            # Find the display name for this file path
            for display_name, file_path in self.display_name_to_path.items():
                if file_path == state['file_path']:
                    self.file_selector.setCurrentText(display_name)
                    break
        
        # Restore the data
        self.files_data[state['file_path']] = [match.copy() for match in state['matches']]
        self.is_modified = state['is_modified']
        
        # Refresh UI
        self._update_title()
        if self.active_file_path == state['file_path']:
            self._populate_table(self.files_data[state['file_path']])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EZpanso()
    window.show()
    sys.exit(app.exec())
