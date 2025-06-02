#!/usr/bin/env python3
import sys
import os
import yaml
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import Qt, QSettings, QUrl
from PyQt6.QtGui import QBrush, QColor, QKeySequence, QShortcut, QIcon, QDesktopServices
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QComboBox,
    QMessageBox, QHeaderView, QLineEdit, QLabel, QDialog, QMenu,
    QFileDialog, QCheckBox
)

FileData = Dict[str, List[Dict[str, Any]]]  # file_path -> list of match dictionaries


class EZpanso(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EZpanso")
        self.resize(600, 800)
        
        # Set window icon
        self.app_icon = None
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.iconset', 'icon_512x512.png')
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
        
        # Settings for persistence
        self.settings = QSettings("EZpanso", "EZpanso")
        self.custom_espanso_dir = self.settings.value("espanso_dir", "")
        
        # Step 1-2: Data storage - simple dictionaries
        self.files_data: FileData = {}  # file_path -> list of match dicts
        self.file_paths: List[str] = []  # ordered list of file paths
        self.display_name_to_path: Dict[str, str] = {}  # display name -> file path mapping
        self.active_file_path: Optional[str] = None
        self.is_modified = False
        self.modified_files: set = set()  # Track which files have been modified
        
        # For sorting and filtering
        self.current_matches: List[Dict[str, Any]] = []  # Current file's matches
        self.filtered_indices: List[int] = []  # Indices of visible rows
        
        # Undo/Redo system
        self.undo_stack: List[Dict[str, Any]] = []  # Stack of undo states
        self.redo_stack: List[Dict[str, Any]] = []  # Stack of redo states
        self.max_undo_steps = 50  # Limit undo history
        
        self._setup_ui()
        self._setup_menubar()
        self._load_all_yaml_files()
    
    def _format_yaml_value(self, value: str) -> str:
        """Store value as-is - YAML will handle quoting automatically when saving."""
        return value
    
    def _get_display_value(self, value: str) -> str:
        """Get the display value for UI, converting actual newlines/tabs to escape sequences."""
        if not isinstance(value, str):
            return str(value)
        # Convert actual newlines and tabs to escape sequences for display
        display_value = value.replace('\n', '\\n').replace('\t', '\\t')
        return display_value
    
    def _process_escape_sequences(self, value: str) -> str:
        """Convert escape sequences like \\n and \\t to actual characters."""
        if not isinstance(value, str):
            return str(value)
        # Convert escape sequences to actual characters
        processed_value = value.replace('\\n', '\n').replace('\\t', '\t')
        return processed_value
        
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
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()
        
        # Get platform-specific shortcut strings for button labels
        if sys.platform == 'darwin':  # macOS
            new_key = "⌘N"
            save_key = "⌘S"
            find_key = "⌘F"
        else:  # Windows/Linux/Unix
            new_key = "Ctrl+N"
            save_key = "Ctrl+S"
            find_key = "Ctrl+F"
        
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
        
    def _setup_menubar(self):
        """Setup the application menubar with all items under EZpanso menu."""
        menubar = self.menuBar()
        if not menubar:
            return
        
        # Single EZpanso menu for simplicity
        ezpanso_menu = menubar.addMenu("EZpanso")
        if ezpanso_menu:
            # Set Folder action
            set_folder_action = ezpanso_menu.addAction("Set Folder...")
            if set_folder_action:
                set_folder_action.setShortcut(QKeySequence.StandardKey.Open)
                set_folder_action.triggered.connect(self._set_custom_folder)
            
            # Separator
            ezpanso_menu.addSeparator()
            
            # Visit Espanso Hub action
            visit_hub_action = ezpanso_menu.addAction("Visit Espanso Hub")
            if visit_hub_action:
                visit_hub_action.triggered.connect(self._visit_espanso_hub)
            
            # About action
            about_action = ezpanso_menu.addAction("About EZpanso")
            if about_action:
                about_action.triggered.connect(self._show_about_dialog)
        
    def _load_all_yaml_files(self):
        """Step 1: safe_load all YAML files under match folder."""
        # Use custom directory if set, otherwise auto-detect
        if self.custom_espanso_dir and os.path.isdir(self.custom_espanso_dir):
            espanso_dir = self.custom_espanso_dir
        else:
            # Simple auto-detection of Espanso directory
            espanso_dir = os.path.expanduser("~/Library/Application Support/espanso/match")
            if not os.path.isdir(espanso_dir):
                espanso_dir = os.path.expanduser("~/.config/espanso/match")
        
        if not os.path.isdir(espanso_dir):
            self._show_warning("Error", "Could not find Espanso match directory. Use File > Set Folder to select one.")
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
        
        # Show package warning if this is a package.yml file
        if "(package)" in display_name.lower():
            if not self._show_package_warning():
                return  # User cancelled, don't proceed
            
        # Clear filter when switching files
        if hasattr(self, 'filter_box'):
            self.filter_box.clear()
            
        matches = self.files_data.get(self.active_file_path, [])
        self._populate_table(matches)
    
    def _create_table_item(self, text: str, is_complex: bool = False) -> QTableWidgetItem:
        """Create a table item with consistent formatting."""
        item = QTableWidgetItem(text)
        
        if is_complex:
            # Gray out complex matches and prevent editing
            gray_brush = QBrush(QColor(180, 180, 180))
            item.setBackground(gray_brush)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        return item

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
            
            # Display unquoted values in UI for both trigger and replace
            display_trigger = self._get_display_value(trigger)
            display_replace = self._get_display_value(replace)
            
            # Step 4: Check if complex (more than trigger/replace)
            is_complex = self._is_complex_match(match)
            
            # Create table items using helper method
            trigger_item = self._create_table_item(display_trigger, is_complex)
            replace_item = self._create_table_item(display_replace, is_complex)
            
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
            delete_action = menu.addAction(f"Delete match ({delete_key})")
        else:
            delete_action = menu.addAction(f"Delete {len(selected_rows)} matches ({delete_key})")

        # Connect the action after creation
        if delete_action:
            delete_action.triggered.connect(lambda checked=False: self._delete_selected_snippets())
        
        # Show menu at cursor position
        menu.exec(self.table.mapToGlobal(position))
    
    def _delete_snippets_by_triggers(self, triggers_to_delete: List[str], show_confirmation: bool = True) -> bool:
        """Delete matches by their trigger values."""
        if not self.active_file_path or not triggers_to_delete:
            return False
        
        # Confirm deletion if requested
        if show_confirmation:
            if len(triggers_to_delete) == 1:
                message = f"Delete match '{triggers_to_delete[0]}'?"
            else:
                message = f"Delete {len(triggers_to_delete)} matches?"

            reply = self._show_question("Delete Matches", message,
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply != QMessageBox.StandardButton.Yes:
                return False
        
        # Save state before deletion
        if len(triggers_to_delete) == 1:
            self._save_state(f"Delete match: '{triggers_to_delete[0]}'")
        else:
            self._save_state(f"Delete {len(triggers_to_delete)} matches")

        # Remove matches from files_data
        matches = self.files_data[self.active_file_path]
        remaining_matches = []
        for match in matches:
            trigger = str(match.get('trigger', ''))
            if trigger not in triggers_to_delete:
                remaining_matches.append(match)
        
        self.files_data[self.active_file_path] = remaining_matches
        
        # Mark as modified and refresh
        self._mark_modified_and_refresh()
        return True
    
    def _get_selected_editable_rows(self):
        """Get list of selected rows that contain editable (non-complex) matches."""
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
        """Delete all selected matches."""
        if not self.active_file_path:
            return
        
        selected_rows = self._get_selected_editable_rows()
        if not selected_rows:
            return
        
        # Get triggers for deletion
        triggers_to_delete = []
        for row in selected_rows:
            trigger_item = self.table.item(row, 0)
            if trigger_item:
                triggers_to_delete.append(trigger_item.text())
        
        self._delete_snippets_by_triggers(triggers_to_delete)
    
    def _on_item_changed(self, item: QTableWidgetItem):
        """Step 5-6: Handle in-place editing and update dictionary."""
        if not self.active_file_path:
            return
            
        row = item.row()
        col = item.column()
        new_value = item.text()
        
        # Process escape sequences in the input
        new_value = self._process_escape_sequences(new_value)
        
        # Get the trigger value to find the corresponding match in original data
        trigger_item = self.table.item(row, 0)
        if not trigger_item:
            return
            
        current_trigger = trigger_item.text()
        
        # Find the match using helper method
        target_match, target_index = self._find_match_by_trigger_display(current_trigger)
        
        if target_match is None:
            return
        
        # Get old value for comparison
        old_value = target_match.get('trigger' if col == 0 else 'replace', '')
        compare_value = self._get_display_value(str(old_value)) if col == 1 else str(old_value)
        
        # Save state before making changes
        if compare_value != new_value:  # Only save state if value actually changed
            if col == 0:
                self._save_state(f"Edit trigger: '{compare_value}' → '{new_value}'")
            else:
                self._save_state(f"Edit replace: '{current_trigger}' content")
        
        # Update the field using validation helper
        field_name = 'trigger' if col == 0 else 'replace'
        if self._validate_and_update_field(item, target_match, target_index, field_name, new_value, current_trigger):
            self._mark_modified_and_refresh()
        
    def _check_duplicate_trigger(self, new_trigger: str, exclude_index: int = -1) -> bool:
        """Check if a trigger already exists in the current file."""
        if not self.active_file_path:
            return False
        
        matches = self.files_data[self.active_file_path]
        for i, match in enumerate(matches):
            if i != exclude_index and match.get('trigger') == new_trigger:
                return True
        return False
    
    def _find_match_by_trigger_display(self, trigger_display: str):
        """Find a match by its display trigger value. Returns (match, index) or (None, -1)."""
        if not self.active_file_path:
            return None, -1
        
        matches = self.files_data[self.active_file_path]
        for i, match in enumerate(matches):
            stored_trigger = str(match.get('trigger', ''))
            display_trigger = self._get_display_value(stored_trigger)
            if display_trigger == trigger_display:
                return match, i
        return None, -1

    def _mark_modified_and_refresh(self):
        """Mark the file as modified and refresh the UI."""
        if self.active_file_path:
            self.modified_files.add(self.active_file_path)
        self.is_modified = True
        self._update_title()
        if self.active_file_path:
            matches = self.files_data.get(self.active_file_path, [])
            self._populate_table(matches)

    def _validate_and_update_field(self, item: QTableWidgetItem, target_match: Dict[str, Any], 
                                 target_index: int, field: str, new_value: str, current_trigger: str):
        """Validate and update a field (trigger or replace) with proper error handling."""
        is_trigger = field == 'trigger'
        
        # Check for duplicates if editing trigger
        if is_trigger and self._check_duplicate_trigger(new_value, target_index):
            self._show_warning("Duplicate", f"Trigger '{new_value}' already exists!")
            # Revert to original value
            original_value = str(target_match.get(field, ''))
            item.setText(self._get_display_value(original_value))
            return False
        
        # Format and store the value
        formatted_value = self._format_yaml_value(new_value)
        target_match[field] = formatted_value
        
        # Update display
        item.setText(self._get_display_value(new_value))
        return True
    
    def _save_all_with_confirmation(self):
        """Step 7: Save with confirmation, overwrite original YAML."""
        if not self.is_modified or not self.modified_files:
            self._show_information("Info", "No changes to save.")
            return
        
        modified_count = len(self.modified_files)
        reply = self._show_question(
            "Save Changes", 
            f"Save changes and Overwrite {modified_count} modified file(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._save_all_files()
    
    def _save_single_file(self, file_path: str, matches: List[Dict[str, Any]]) -> bool:
        """Save a single YAML file. Returns True if successful."""
        try:
            # Read existing file to preserve other keys
            existing_content = {}
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = yaml.safe_load(f) or {}
            
            # Update matches section
            existing_content['matches'] = matches
            
            # Write back with double quotes as default style
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_content, f, sort_keys=False, allow_unicode=True, default_style='"')
            
            return True
            
        except Exception as e:
            self._show_critical("Save Error", f"Error saving {file_path}:\n{e}")
            return False

    def _save_all_files(self):
        """Save only the modified YAML files."""
        saved_count = 0
        
        # Only save files that have been modified
        for file_path in self.modified_files.copy():  # Use copy to avoid modification during iteration
            matches = self.files_data.get(file_path, [])
            if self._save_single_file(file_path, matches):
                saved_count += 1
                self.modified_files.discard(file_path)  # Remove from modified set after successful save
        
        if saved_count > 0:
            # Only clear is_modified if no files remain modified
            if not self.modified_files:
                self.is_modified = False
            self._update_title()
            self._show_information("Saved", f"Successfully saved {saved_count} file(s).")
    
    def _update_title(self):
        """Update window title with modification indicator."""
        base_title = "EZpanso"
        self.setWindowTitle(f"{base_title}{' *' if self.is_modified else ''}")
    
    def _add_new_snippet(self):
        """Add a new snippet via dialog."""
        if not self.active_file_path:
            self._show_information("No File", "Please select a file first.")
            return
        
        # Simple input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("New Match")
        dialog.setModal(True)
        dialog.resize(400, 160)  # Increased height for reminder
        
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
        
        # Reminder about special characters
        reminder_label = QLabel("💡 Type \\n for new lines, \\t for tabs. YAML special characters are handled automatically.")
        reminder_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        reminder_label.setWordWrap(True)
        reminder_label.setMinimumHeight(40)
        reminder_label.setWordWrap(True)
        layout.addWidget(reminder_label)
        
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
        
        # Keep dialog open until validation passes or user cancels
        while True:
            # Show dialog
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return  # User cancelled
            
            trigger = trigger_input.text().strip()
            replace = replace_input.text().strip()
            
            # Validate input
            if not trigger or not replace:
                self._show_warning("Invalid Input", "Both trigger and replace must be filled.")
                continue  # Show dialog again
            
            # Process escape sequences in both trigger and replace
            trigger = self._process_escape_sequences(trigger)
            replace = self._process_escape_sequences(replace)
            
            # Check for duplicates using helper method
            if self._check_duplicate_trigger(trigger):
                self._show_warning("Duplicate", f"Trigger '{trigger}' already exists.")
                continue  # Show dialog again
            
            # All validation passed, break out of loop
            break
        
        # Save state before adding new snippet
        self._save_state(f"Add snippet: '{trigger}'")
        
        # Format both trigger and replace values with proper YAML quoting for consistency
        formatted_trigger = self._format_yaml_value(trigger)
        formatted_replace = self._format_yaml_value(replace)
        
        # Add new snippet
        new_snippet = {'trigger': formatted_trigger, 'replace': formatted_replace}
        self.files_data[self.active_file_path].append(new_snippet)
        
        # Mark as modified and refresh
        self._mark_modified_and_refresh()

    def _save_state(self, description: str):
        """Save current state to undo stack for operation tracking."""
        if not self.active_file_path:
            return
            
        # Create state snapshot and add to undo stack
        self.undo_stack.append(self._create_state(description))
        
        # Limit stack size
        if len(self.undo_stack) > self.max_undo_steps:
            self.undo_stack.pop(0)
        
        # Clear redo stack when new action is performed
        self.redo_stack.clear()
    
    def _create_state(self, description: str) -> Dict[str, Any]:
        """Create a state snapshot for undo/redo operations."""
        if not self.active_file_path:
            return {}
        return {
            'description': description,
            'file_path': self.active_file_path,
            'matches': [match.copy() for match in self.files_data[self.active_file_path]],
            'is_modified': self.is_modified,
            'modified_files': self.modified_files.copy()
        }
    
    def _restore_state(self, state: Dict[str, Any]):
        """Restore application state from a state snapshot."""
        # Switch to the file if needed
        if state['file_path'] != self.active_file_path:
            self._switch_to_file(state['file_path'])
        
        # Restore the data
        self.files_data[state['file_path']] = [match.copy() for match in state['matches']]
        self.is_modified = state['is_modified']
        self.modified_files = state.get('modified_files', set()).copy()
        
        # Refresh UI
        self._refresh_current_view()
    
    def _switch_to_file(self, file_path: str):
        """Switch to a specific file by finding its display name."""
        for display_name, path in self.display_name_to_path.items():
            if path == file_path:
                self.file_selector.setCurrentText(display_name)
                break
    
    def _refresh_current_view(self):
        """Refresh the current UI view."""
        self._update_title()
        if self.active_file_path:
            self._populate_table(self.files_data[self.active_file_path])

    def _undo(self):
        """Undo the last operation."""
        if not self.undo_stack:
            return
        
        # Save current state to redo stack before undoing
        if self.active_file_path:
            state = self._create_state('redo_point')
            if state:  # Only add if valid state was created
                self.redo_stack.append(state)
        
        # Restore previous state
        state = self.undo_stack.pop()
        self._restore_state(state)

    def _redo(self):
        """Redo the last undone operation."""
        if not self.redo_stack:
            return
        
        # Save current state to undo stack before redoing
        if self.active_file_path:
            state = self._create_state('undo_point')
            if state:  # Only add if valid state was created
                self.undo_stack.append(state)
        
        # Restore redo state
        state = self.redo_stack.pop()
        self._restore_state(state)
    
    def _create_message_box(self, icon_type, title, text, buttons=QMessageBox.StandardButton.Ok):
        """Create a message box with the app icon."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon_type)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(buttons)
        
        # Set the app icon (works best with PNG format)
        if self.app_icon:
            msg_box.setWindowIcon(self.app_icon)
        
        return msg_box
    
    def _show_question(self, title, text, buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No):
        """Show a question dialog."""
        return self._create_message_box(QMessageBox.Icon.Question, title, text, buttons).exec()
    
    def _show_warning(self, title, text):
        """Show a warning dialog."""
        self._create_message_box(QMessageBox.Icon.Warning, title, text).exec()
    
    def _show_information(self, title, text):
        """Show an information dialog."""
        self._create_message_box(QMessageBox.Icon.Information, title, text).exec()
    
    def _show_critical(self, title, text):
        """Show a critical dialog."""
        self._create_message_box(QMessageBox.Icon.Critical, title, text).exec()
    
    def closeEvent(self, event):
        """Handle window close event - warn if there are unsaved changes."""
        if self.is_modified:
            reply = self._show_question(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._save_all_files()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:  # Cancel
                event.ignore()
        else:
            event.accept()
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts for the application."""
        shortcuts = [
            (QKeySequence.StandardKey.New, self._add_new_snippet),
            (QKeySequence.StandardKey.Save, self._save_all_with_confirmation),
            (QKeySequence.StandardKey.Find, self._focus_filter),
            (QKeySequence(Qt.Key.Key_Delete), self._delete_selected_snippets),
            (QKeySequence(Qt.Key.Key_Backspace), self._delete_selected_snippets),
            (QKeySequence.StandardKey.Undo, self._undo),
            (QKeySequence.StandardKey.Redo, self._redo),
        ]
        
        for key_sequence, callback in shortcuts:
            shortcut = QShortcut(key_sequence, self)
            shortcut.activated.connect(callback)
            
    def _set_custom_folder(self):
        """Open a folder dialog to set custom Espanso match directory."""
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Espanso Match Directory",
            self.custom_espanso_dir or os.path.expanduser("~")
        )
        
        if folder:
            self.custom_espanso_dir = folder
            self.settings.setValue("espanso_dir", folder)
            
            # Reload files from new directory
            self.files_data.clear()
            self.file_paths.clear()
            self.display_name_to_path.clear()
            self.active_file_path = None
            self.is_modified = False
            self.modified_files.clear()
            self.file_selector.clear()
            self.table.setRowCount(0)
            
            self._load_all_yaml_files()
            QMessageBox.information(self, "Folder Set", f"Espanso directory set to:\n{folder}")
    
    def _visit_espanso_hub(self):
        """Open the Espanso Hub website in the default browser."""
        QDesktopServices.openUrl(QUrl("https://hub.espanso.org/"))
    
    def _show_about_dialog(self):
        """Show the About dialog with application information."""
        about_text = """
        <h2>EZpanso</h2>
        <p>Managing Espanso matches made even easier.</p>
        <p>Workflow</p>
        <li>📂 Open match files and packages</li>
        <li>🔍 Find, Sort, Create and Delete matches</li>
        <li>✏️ In-place Edit for non-dynamic matches</li>
        <li>💾 Save and Done</li>
        <p>Features (v1.0)</p>
        <li>✅ Keyboard shortcuts</li>
        <li>✅ Multi-line replacement</li>
        <li>✅ Undo and Redo</li>
        <li></li>
        <p><a href="https://github.com/luklongman/EZpanso">EZpanso</a> by <a href="https://www.instagram.com/l.ongman">Longman</a> (June 2025)</p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About EZpanso")
        msg_box.setText(about_text)
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        
        if self.app_icon:
            msg_box.setIconPixmap(self.app_icon.pixmap(64, 64))
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
            
        msg_box.exec()

    def _show_package_warning(self) -> bool:
        """Show warning dialog for package.yml files. Returns True if user wants to proceed."""
        # Check if user has opted out of this warning
        show_warning = self.settings.value("show_package_warning", True, type=bool)
        if not show_warning:
            return True
        
        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Package File Warning")
        dialog.setModal(True)
        dialog.resize(450, 200)
        
        # Set the app icon
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        
        layout = QVBoxLayout(dialog)
        
        # Warning icon and message
        message_layout = QHBoxLayout()
        
        # Warning message
        warning_text = QLabel(
            "⚠️ <b>Package Files</b><br><br>"
            "Editing Espanso packages is <b>not recommended</b> at this stage.<br>"
            "File may not work properly due to formatting issues of advanced matches.<br><br>"
            "Consider creating your own match files for experimentation."
        )
        warning_text.setWordWrap(True)
        warning_text.setTextFormat(Qt.TextFormat.RichText)
        warning_text.setStyleSheet("padding: 10px;")
        
        message_layout.addWidget(warning_text)
        layout.addLayout(message_layout)
        
        # "Do not show again" checkbox
        self.dont_show_checkbox = QCheckBox("Do not show this warning again")
        layout.addWidget(self.dont_show_checkbox)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # Show dialog and handle result
        result = dialog.exec()
        
        # Save preference if user checked "do not show again"
        if self.dont_show_checkbox.isChecked():
            self.settings.setValue("show_package_warning", False)
        
        return result == QDialog.DialogCode.Accepted


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application name for proper menubar display
    app.setApplicationName("EZpanso")
    app.setApplicationDisplayName("EZpanso")
    app.setOrganizationName("EZpanso")
    
    # Set application icon globally
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.iconset', 'icon_512x512.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = EZpanso()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
    