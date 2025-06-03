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
        icon_path = os.path.join(os.path.dirname(__file__), 'icon_512x512.png')
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
        
        # Define unified minimal styles
        self.button_style = """
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 2px;
                background-color: white;
                color: #333;
                min-width: 60px;
            }
            QPushButton:hover {
                border-color: #999;
                background-color: #f8f8f8;
            }
            QPushButton:pressed {
                background-color: #eee;
            }
        """
        
        self.primary_button_style = """
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                border: 1px solid #007acc;
                border-radius: 2px;
                background-color: #007acc;
                color: white;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #005c99;
                border-color: #005c99;
            }
            QPushButton:pressed {
                background-color: #004080;
            }
        """
        
        self.input_style = """
            QLineEdit {
                padding: 4px;
                border: 1px solid #ddd;
                border-radius: 2px;
                font-size: 11px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """
        
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
        
        # File selector dropdown with proportional layout: 25% Find, 50% Dropdown, 25% Open
        file_layout = QHBoxLayout()
        
        self.filter_box = QLineEdit()
        self.filter_box.setPlaceholderText("Filter...")
        self.filter_box.setStyleSheet(self.input_style)
        self.filter_box.textChanged.connect(self._apply_filter)
        file_layout.addWidget(self.filter_box, 1)  # 25% proportion
        
        self.file_selector = QComboBox()
        self.file_selector.currentTextChanged.connect(self._on_file_selected)
        file_layout.addWidget(self.file_selector, 2)  # 50% proportion
        
        # Get platform-specific shortcut string for Open button
        if sys.platform == 'darwin':  # macOS
            open_key = "⌘O"
        else:  # Windows/Linux/Unix
            open_key = "Ctrl+O"
        
        open_btn = QPushButton(f"Open ({open_key})")
        open_btn.setStyleSheet(self.button_style)
        open_btn.clicked.connect(self._open_current_file)
        file_layout.addWidget(open_btn, 1)  # 25% proportion
        
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
        
        new_btn = QPushButton(f"New match ({new_key})")
        new_btn.setStyleSheet(self.button_style)
        new_btn.clicked.connect(self._add_new_snippet)
        bottom_btn_layout.addWidget(new_btn)
        
        bottom_btn_layout.addStretch()
        
        self.save_btn = QPushButton(f"Save ({save_key})")
        self.save_btn.setStyleSheet(self.primary_button_style)
        self.save_btn.clicked.connect(self._save_all_with_confirmation)
        self._update_save_button_state()  # Set initial state
        bottom_btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(bottom_btn_layout)
        
    def _setup_menubar(self):
        """Setup the application menubar with all items under the main application menu."""
        menubar = self.menuBar()
        if not menubar:
            return
        
        # On macOS, use the application menu (first menu). On other platforms, create EZpanso menu.
        if sys.platform == 'darwin':  # macOS
            # Get the application menu (automatically created by Qt)
            app_menu = None
            for action in menubar.actions():
                menu = action.menu()
                if menu:
                    app_menu = menu
                    break
            
            # If no application menu exists, create one
            if not app_menu:
                app_menu = menubar.addMenu("EZpanso")
        else:
            # On Windows/Linux, create a regular EZpanso menu
            app_menu = menubar.addMenu("EZpanso")
        
        if app_menu:
            # Add a separator before our custom items (on macOS this separates from default items)
            if sys.platform == 'darwin':
                app_menu.addSeparator()
            
            # Preferences action (includes About, Settings, and Links)
            preferences_action = app_menu.addAction("Preferences...")
            if preferences_action:
                preferences_action.setShortcut(QKeySequence.StandardKey.Preferences)
                preferences_action.triggered.connect(self._show_preferences_dialog)
        
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
            self._show_warning("Missing Directory", "Could not find Espanso match directory.\nUse File > Set Folder to select one.")
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
                message = f"Delete match '{triggers_to_delete[0]}'?\nThis action cannot be undone."
            else:
                message = f"Delete {len(triggers_to_delete)} matches?\nThis action cannot be undone."

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
        self._update_save_button_state()
        if self.active_file_path:
            matches = self.files_data.get(self.active_file_path, [])
            self._populate_table(matches)

    def _validate_and_update_field(self, item: QTableWidgetItem, target_match: Dict[str, Any], 
                                 target_index: int, field: str, new_value: str, current_trigger: str):
        """Validate and update a field (trigger or replace) with proper error handling."""
        is_trigger = field == 'trigger'
        
        # Check for duplicates if editing trigger
        if is_trigger and self._check_duplicate_trigger(new_value, target_index):
            self._show_warning("Duplicate Trigger", f"Trigger '{new_value}' already exists!\nPlease choose a different trigger.")
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
            self._show_information("No Changes", "No changes to save.\nAll files are already up to date.")
            return
        
        modified_count = len(self.modified_files)
        reply = self._show_question(
            "Save Changes", 
            f"Save changes and overwrite {modified_count} modified file(s)?\nThis will update the YAML files on disk.",
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
            
            # Write back with clean YAML formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_content, f, sort_keys=False, allow_unicode=True, default_style=None)
            
            return True
            
        except Exception as e:
            self._show_critical("Save Error", f"Error saving file:\n{e}")
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
            self._update_save_button_state()
            self._show_information("Files Saved", f"Successfully saved {saved_count} file(s).\nAll changes have been written to disk.")
    
    def _update_title(self):
        """Update window title with modification indicator."""
        base_title = "EZpanso"
        self.setWindowTitle(f"{base_title}{' *' if self.is_modified else ''}")
    
    def _add_new_snippet(self):
        """Add a new snippet via dialog."""
        if not self.active_file_path:
            self._show_information("No File Selected", "Please select a file first.\nChoose a file from the dropdown menu.")
            return
        
        # Simple input dialog with clean styling
        dialog = QDialog(self)
        dialog.setWindowTitle("New Match")
        dialog.setModal(True)
        dialog.resize(350, 160)
        
        # Set the app icon
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Trigger input
        trigger_layout = QHBoxLayout()
        trigger_layout.setSpacing(8)
        label = QLabel("Trigger:")
        label.setMinimumWidth(60)
        label.setStyleSheet("font-weight: bold; color: #333; font-size: 11px;")
        trigger_layout.addWidget(label)
        trigger_input = QLineEdit()
        trigger_input.setPlaceholderText(":email")
        trigger_input.setStyleSheet(self.input_style)
        trigger_layout.addWidget(trigger_input)
        layout.addLayout(trigger_layout)
        
        # Replace input
        replace_layout = QHBoxLayout()
        replace_layout.setSpacing(8)
        label = QLabel("Replace:")
        label.setMinimumWidth(60)
        label.setStyleSheet("font-weight: bold; color: #333; font-size: 11px;")
        replace_layout.addWidget(label)
        replace_input = QLineEdit()
        replace_input.setPlaceholderText("johnny@water.com")
        replace_input.setStyleSheet(self.input_style)
        replace_layout.addWidget(replace_input)
        layout.addLayout(replace_layout)
        
        # Tip
        tip_label = QLabel("Tip: Type \\n for new lines, \\t for tabs")
        tip_label.setStyleSheet("color: #666; font-size: 10px; margin: 5px 0;")
        layout.addWidget(tip_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self.button_style)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        add_btn = QPushButton("Add")
        add_btn.setStyleSheet(self.primary_button_style)
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
                self._show_warning("Missing Input", "Both trigger and replace must be filled.\nPlease complete both fields.")
                continue  # Show dialog again
            
            # Process escape sequences in both trigger and replace
            trigger = self._process_escape_sequences(trigger)
            replace = self._process_escape_sequences(replace)
            
            # Check for duplicates using helper method
            if self._check_duplicate_trigger(trigger):
                self._show_warning("Duplicate Trigger", f"Trigger '{trigger}' already exists.\nPlease choose a different trigger.")
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
        self._update_save_button_state()
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
        """Create a message box with consistent styling and no icons."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.NoIcon)  # Remove icons from all dialogs
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setStandardButtons(buttons)
        
        # Set the app icon (works best with PNG format)
        if self.app_icon:
            msg_box.setWindowIcon(self.app_icon)
        
        # Enhanced styling with consistent button appearance and transparent backgrounds
        msg_box.setStyleSheet("""
            QMessageBox {
                border: 1px solid #ccc;
                min-width: 300px;
            }
            QMessageBox QLabel {
                color: #333;
                font-size: 12px;
                padding: 15px;
                line-height: 1.5;
                margin: 5px;
            }
            QMessageBox QPushButton {
                padding: 4px 8px;
                font-size: 11px;
                border: 1px solid #ddd;
                border-radius: 2px;
                color: #333;
                min-width: 60px;
                margin: 2px;
            }
            QMessageBox QPushButton:hover {
                border-color: #999;
            }
            QMessageBox QPushButton:pressed {
                border-color: #666;
            }
            QMessageBox QPushButton:default {
                border: 1px solid #007acc;
                background-color: #007acc;
                color: white;
            }
            QMessageBox QPushButton:default:hover {
                background-color: #005c99;
                border-color: #005c99;
            }
            QMessageBox QPushButton:default:pressed {
                background-color: #004080;
            }
        """)
        
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
                "You have unsaved changes.\nDo you want to save before closing?",
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
            (QKeySequence.StandardKey.Open, self._open_current_file),
            (QKeySequence(Qt.Key.Key_Delete), self._delete_selected_snippets),
            (QKeySequence(Qt.Key.Key_Backspace), self._delete_selected_snippets),
            (QKeySequence.StandardKey.Undo, self._undo),
            (QKeySequence.StandardKey.Redo, self._redo),
        ]
        
        for key_sequence, callback in shortcuts:
            shortcut = QShortcut(key_sequence, self)
            shortcut.activated.connect(callback)
            
    def _show_preferences_dialog(self):
        """Show the Preferences dialog with About, Settings, and Links in one view."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setModal(True)
        dialog.setFixedWidth(400)  # Set width only, let content determine height

        # Set the app icon
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Get version and current year
        version = getattr(self, 'app_version', '1.2.0')
        current_year = __import__('datetime').datetime.now().year
        
        # Settings Section
        current_folder_label = QLabel("Espanso Match Folder Directory:")
        current_folder_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #333;")
        layout.addWidget(current_folder_label)
        
        # Create horizontal layout for text field and button
        folder_input_layout = QHBoxLayout()
        folder_input_layout.setSpacing(8)
        
        current_folder_input = QLineEdit(self.custom_espanso_dir or "")
        current_folder_input.setPlaceholderText("Auto-detected if empty")
        current_folder_input.setStyleSheet(self.input_style)
        folder_input_layout.addWidget(current_folder_input, 1)
        
        # Change folder button
        change_folder_btn = QPushButton("Browse...")
        change_folder_btn.setStyleSheet(self.button_style)
        change_folder_btn.clicked.connect(lambda: self._change_folder_from_preferences(dialog, current_folder_input))
        folder_input_layout.addWidget(change_folder_btn)
        
        layout.addLayout(folder_input_layout)
        
        # Add spacing
        layout.addSpacing(15)
        
        # About Section - get platform info
        import platform
        arch = platform.machine()
        arch_display = "Apple Silicon" if arch == "arm64" else "Intel" if arch == "x86_64" else arch
        
        about_content = QLabel(f"""EZpanso v{version} ({arch_display})
 Easy editor for Espanso © {current_year} by Longman""")
        about_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_content.setStyleSheet("color: #666; font-size: 11px; line-height: 1.4;")
        layout.addWidget(about_content)
        
        # Add stretch before buttons
        layout.addStretch()
        layout.addSpacing(15)
        # Buttons with links
        button_layout = QHBoxLayout()
        
        # Create link buttons
        links = [
            ("Espanso Hub", "https://hub.espanso.org/"),
            ("EZpanso GitHub", "https://github.com/luklongman/EZpanso")
        ]
        
        for title, url in links:
            link_btn = QPushButton(title)
            link_btn.setStyleSheet(self.button_style)
            link_btn.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            button_layout.addWidget(link_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(self.primary_button_style)
        close_btn.clicked.connect(dialog.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
    
    def _change_folder_from_preferences(self, parent_dialog, folder_input):
        """Change folder from within preferences dialog."""
        folder = QFileDialog.getExistingDirectory(
            parent_dialog,
            "Select Espanso Match Directory",
            self.custom_espanso_dir or os.path.expanduser("~")
        )
        
        if folder:
            self.custom_espanso_dir = folder
            self.settings.setValue("espanso_dir", folder)
            
            # Update the text field in the preferences dialog
            folder_input.setText(folder)
            
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
            self._update_save_button_state()
            self._show_information("Folder Changed", f"Espanso match folder updated successfully.\nNow using: {folder}")

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
        dialog.resize(480, 250)  # Slightly larger for better readability
        
        # Set the app icon
        if self.app_icon:
            dialog.setWindowIcon(self.app_icon)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(25, 25, 25, 25)
        
        # Warning icon and message
        message_layout = QHBoxLayout()
        message_layout.setSpacing(15)
        
        # Warning icon
        icon_label = QLabel("⚠️")
        icon_label.setStyleSheet("font-size: 32px; color: #ff9500;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        message_layout.addWidget(icon_label)
        
        # Warning message
        warning_text = QLabel(
            "<b style='font-size: 16px; color: #333;'>Package Files</b><br><br>"
            "<span style='color: #666; line-height: 1.4;'>"
            "Editing Espanso packages is <b>not recommended</b> at this stage.<br>"
            "Files may not work properly due to formatting issues with advanced matches.<br><br>"
            "Consider creating your own match files for experimentation."
            "</span>"
        )
        warning_text.setWordWrap(True)
        warning_text.setTextFormat(Qt.TextFormat.RichText)
        warning_text.setStyleSheet("""
            QLabel {
                padding: 15px;
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 6px;
                line-height: 1.6;
            }
        """)
        message_layout.addWidget(warning_text, 1)
        
        layout.addLayout(message_layout)
        
        # "Do not show again" checkbox
        self.dont_show_checkbox = QCheckBox("Do not show this warning again")
        self.dont_show_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 12px;
                color: #666;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #007acc;
                border-radius: 3px;
                background-color: #007acc;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjg1IDQuMTVMMTAuNSA3LjVMNy4xNSA0LjE1TDguNSAyLjhMMTAuNSA0LjhMMTIuNSAyLjhMMTMuODUgNC4xNVoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPg==);
            }
        """)
        layout.addWidget(self.dont_show_checkbox)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("Continue")
        ok_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #ff9500;
                border-radius: 4px;
                background-color: #ff9500; 
                color: white;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e6840e;
                border-color: #e6840e;
            }
            QPushButton:pressed {
                background-color: #cc7300;
            }
        """)
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

    def _open_current_file(self):
        """Open the currently selected YAML file in the system's default editor."""
        if not self.active_file_path:
            self._show_information("No File Selected", "Please select a file first.\nChoose a file from the dropdown menu.")
            return
        
        if not os.path.exists(self.active_file_path):
            self._show_warning("File Not Found", f"The selected file no longer exists.\nPath: {self.active_file_path}")
            return
        
        try:
            # Use QDesktopServices to open file with default application
            file_url = QUrl.fromLocalFile(self.active_file_path)
            QDesktopServices.openUrl(file_url)
        except Exception as e:
            self._show_critical("Open Error", f"Could not open file with default application.\nError: {e}")

    def _update_save_button_state(self):
        """Update save button enabled/disabled state based on unsaved changes."""
        if hasattr(self, 'save_btn'):
            has_changes = self.is_modified and bool(self.modified_files)
            self.save_btn.setEnabled(has_changes)
            
            # Update button style to show grayed out state
            if has_changes:
                self.save_btn.setStyleSheet(self.primary_button_style)
            else:
                gray_style = """
                    QPushButton {
                        padding: 4px 8px;
                        font-size: 11px;
                        border: 1px solid #ccc;
                        border-radius: 2px;
                        background-color: #f5f5f5;
                        color: #999;
                        min-width: 60px;
                    }
                """
                self.save_btn.setStyleSheet(gray_style)

    def _check_unsaved_changes_before_switch(self, target_display_name: str) -> bool:
        """Check for unsaved changes before switching files. Returns True if switch should proceed."""
        if not self.is_modified or not self.modified_files:
            return True
        
        # Ask user what to do with unsaved changes
        reply = self._show_question(
            "Unsaved Changes",
            "You have unsaved changes.\nSave before switching files?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Save:
            self._save_all_files()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            # Reset modification state
            self.is_modified = False
            self.modified_files.clear()
            self._update_save_button_state()
            return True
        else:  # Cancel
            # Revert the combo box selection
            if self.active_file_path:
                for display_name, path in self.display_name_to_path.items():
                    if path == self.active_file_path:
                        self.file_selector.blockSignals(True)
                        self.file_selector.setCurrentText(display_name)
                        self.file_selector.blockSignals(False)
                        break
            return False
    
def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Set application name for proper menubar display
    app.setApplicationName("EZpanso")
    app.setApplicationDisplayName("EZpanso")
    app.setOrganizationName("EZpanso")
    
    # Set version for the application
    app.setApplicationVersion("1.2.0")
    
    # Set application icon globally
    icon_path = os.path.join(os.path.dirname(__file__), 'icon_512x512.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = EZpanso()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
