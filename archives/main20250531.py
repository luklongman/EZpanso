"""
EZpanso - PyQt6 Version
A modern GUI for managing Espanso text expansion snippets.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import Qt, pyqtSlot, QThreadPool
from PyQt6.QtGui import QKeySequence, QAction, QShortcut, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QPushButton,
    QHeaderView,
    QDialog,
    QLabel,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QFileDialog,
    QDialogButtonBox,
)
from qt_data_loader import DataLoader, DataSaver
import constants as C
from data_model import Snippet


class EditSnippetDialog(QDialog):
    """Dialog for editing an existing snippet."""

    def __init__(self, parent: QWidget, title: str, snippet: Snippet):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.snippet = snippet
        self.result: Optional[Dict[str, str]] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Trigger field
        trigger_layout = QHBoxLayout()
        trigger_label = QLabel("Trigger:")
        self.trigger_entry = QLineEdit()
        self.trigger_entry.setText(self.snippet.trigger)
        self.trigger_entry.setMinimumWidth(300)
        trigger_layout.addWidget(trigger_label)
        trigger_layout.addWidget(self.trigger_entry)
        layout.addLayout(trigger_layout)

        # Replace field
        replace_layout = QHBoxLayout()
        replace_label = QLabel("Replace:")
        self.replace_text = QTextEdit()
        self.replace_text.setText(self.snippet.replace_text)
        self.replace_text.setMinimumHeight(200)
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_text)
        layout.addLayout(replace_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        trigger = self.trigger_entry.text().strip()
        replace = self.replace_text.toPlainText().strip()

        if not trigger:
            QMessageBox.critical(self, "Error", C.ERROR_TRIGGER_EMPTY)
            return

        self.result = {C.COL_TRIGGER: trigger, C.COL_REPLACE: replace}
        super().accept()


class NewCategoryDialog(QDialog):
    """Dialog for creating a new category."""

    def __init__(self, parent: QWidget, espanso_match_dir: str):
        super().__init__(parent)
        self.setWindowTitle(C.TITLE_NEW_CATEGORY)
        self.espanso_match_dir = espanso_match_dir
        self.result: Optional[Dict[str, str]] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Name field
        name_layout = QHBoxLayout()
        name_label = QLabel("Title:")
        self.name_entry = QLineEdit()
        self.name_entry.setMinimumWidth(300)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_entry)
        layout.addLayout(name_layout)

        # Add description label
        desc_label = QLabel(f"A yml file will be created at {self.espanso_match_dir}.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        name = self.name_entry.text().strip()

        # Validate filename
        if not name:
            QMessageBox.critical(self, "Error", C.ERROR_CATEGORY_NAME_EMPTY)
            return

        if any(c in name for c in r'/\:*?"<>|'):
            QMessageBox.critical(self, "Error", C.ERROR_CATEGORY_NAME_INVALID_CHARS)
            return

        if name.endswith((".yml", ".yaml")):
            QMessageBox.critical(self, "Error", C.ERROR_CATEGORY_NO_EXTENSION)
            return

        filename = f"{name}.yml"
        file_path = os.path.join(self.espanso_match_dir, filename)

        if os.path.exists(file_path):
            QMessageBox.critical(
                self, "Error", C.ERROR_CATEGORY_FILE_EXISTS.format(filename)
            )
            return

        self.result = {"file_path": file_path, "display_name": filename}
        super().accept()


class EZpanso(QMainWindow):
    """Main window of the EZpanso application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(C.TITLE_APP)
        self.resize(1000, 600)

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # State
        self.espanso_config_dir = ""
        self.snippets_by_file_path: Dict[str, List[Snippet]] = {}
        self.category_dropdown_map: Dict[str, str] = {}
        self.active_file_path: Optional[str] = None

        # Thread pool for background operations
        self.thread_pool = QThreadPool.globalInstance()

        self._setup_ui()
        self._setup_shortcuts()
        self._load_initial_config()

    def _create_preview_text(self, text: str) -> str:
        """Create a preview of replacement text, truncating if multiline."""
        if not text:
            return ""
        lines = text.split("\n")
        if len(lines) > 1:
            return lines[0] + "..."
        return text

    def _create_confirmation_dialog(self, title: str, message: str) -> bool:
        """Create a standard Yes/No confirmation dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        question = QLabel(message)
        layout.addWidget(question)

        button_box = QDialogButtonBox()
        button_box.addButton("No", QDialogButtonBox.ButtonRole.RejectRole)
        button_box.addButton("Yes", QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        return dialog.exec() == QDialog.DialogCode.Accepted

    def _disconnect_category_selector(self):
        """Temporarily disconnect category selector to prevent signal loops."""
        self.category_selector.currentIndexChanged.disconnect(self._on_category_selected)

    def _reconnect_category_selector(self):
        """Reconnect category selector after temporary disconnection."""
        self.category_selector.currentIndexChanged.connect(self._on_category_selected)

    def _setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Category selector
        self.category_selector = QComboBox()
        self.category_selector.setMinimumWidth(200)
        self.category_selector.currentIndexChanged.connect(self._on_category_selected)
        layout.addWidget(self.category_selector)

        # Snippet table
        self.snippet_table = QTableWidget()
        self.snippet_table.setColumnCount(2)
        self.snippet_table.setHorizontalHeaderLabels(["Trigger", "Replace With"])
        self.snippet_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.snippet_table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft
        )
        self.snippet_table.verticalHeader().hide()
        self.snippet_table.setAlternatingRowColors(True)
        self.snippet_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.snippet_table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.EditKeyPressed
            | QTableWidget.EditTrigger.AnyKeyPressed
        )
        self.snippet_table.itemChanged.connect(self._on_item_edited)
        layout.addWidget(self.snippet_table)

        # Always ensure there's an empty row at the bottom for adding new snippets
        self._ensure_empty_bottom_row()

        # Button bar
        button_layout = QHBoxLayout()
        self.new_snippet_btn = QPushButton("New Snippet")
        self.edit_snippet_btn = QPushButton("Edit")
        self.delete_snippet_btn = QPushButton("Delete")
        self.delete_category_btn = QPushButton("Delete Category")

        self.new_snippet_btn.clicked.connect(self._new_snippet)
        self.edit_snippet_btn.clicked.connect(self._edit_selected)
        self.delete_snippet_btn.clicked.connect(self._remove_selected_snippets)
        self.delete_category_btn.clicked.connect(self._delete_category)

        for btn in (
            self.new_snippet_btn,
            self.edit_snippet_btn,
            self.delete_snippet_btn,
            self.delete_category_btn,
        ):
            btn.setAutoDefault(False)
            button_layout.addWidget(btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status bar
        self.statusBar().showMessage(C.MSG_WELCOME)

        # Menu bar
        self._setup_menu()

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_dir_action = QAction("Open Espanso Directory...", self)
        open_dir_action.triggered.connect(self._select_espanso_directory)
        file_menu.addAction(open_dir_action)

        file_menu.addSeparator()

        add_snippet_action = QAction(C.MENU_FILE_ADD, self)
        add_snippet_action.setShortcut(QKeySequence(C.SHORTCUT_ADD))
        add_snippet_action.triggered.connect(self._new_snippet)
        file_menu.addAction(add_snippet_action)

        new_category_action = QAction(C.MENU_FILE_NEW_CATEGORY, self)
        new_category_action.setShortcut(QKeySequence(C.SHORTCUT_NEW_CATEGORY))
        new_category_action.triggered.connect(self._new_category)
        file_menu.addAction(new_category_action)

        file_menu.addSeparator()

        save_action = QAction(C.MENU_FILE_SAVE, self)
        save_action.setShortcut(QKeySequence(C.SHORTCUT_SAVE))
        save_action.triggered.connect(self._save_all_changes)
        file_menu.addAction(save_action)

        refresh_action = QAction(C.MENU_FILE_REFRESH, self)
        refresh_action.setShortcut(QKeySequence(C.SHORTCUT_REFRESH))
        refresh_action.triggered.connect(self._refresh_data)
        file_menu.addAction(refresh_action)

    def _setup_shortcuts(self):
        # Navigation shortcuts bound to table
        QShortcut(
            QKeySequence(C.SHORTCUT_MOVE_UP),
            self.snippet_table,
            self._move_selection_up,
        )
        QShortcut(
            QKeySequence(C.SHORTCUT_MOVE_DOWN),
            self.snippet_table,
            self._move_selection_down,
        )

        # Action shortcuts bound to main window
        QShortcut(QKeySequence(C.SHORTCUT_EDIT), self, self._edit_selected)
        QShortcut(
            QKeySequence(C.SHORTCUT_CANCEL),
            self,
            lambda: self.snippet_table.clearSelection(),
        )
        QShortcut(QKeySequence(C.SHORTCUT_ADD), self, self._new_snippet)
        QShortcut(QKeySequence(C.SHORTCUT_NEW_CATEGORY), self, self._new_category)
        QShortcut(QKeySequence(C.SHORTCUT_DELETE), self, self._remove_selected_snippets)
        QShortcut(QKeySequence(C.SHORTCUT_DELETE_CATEGORY), self, self._delete_category)
        QShortcut(QKeySequence(C.SHORTCUT_SAVE), self, self._save_all_changes)
        QShortcut(QKeySequence(C.SHORTCUT_REFRESH), self, self._refresh_data)

        # Multi-select mode
        self.snippet_table.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )

    def _load_initial_config(self):
        """Load the default config directory on startup."""
        from file_handler import get_default_espanso_config_path

        default_path = get_default_espanso_config_path()

        if default_path and os.path.isdir(default_path):
            self.espanso_config_dir = default_path
            self._refresh_data()
        else:
            self.statusBar().showMessage(C.MSG_DEFAULT_DIR_NOT_FOUND)

    @pyqtSlot()
    def _select_espanso_directory(self):
        """Open directory selection dialog."""
        self.statusBar().showMessage(C.MSG_SELECTING_DIR)

        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Espanso Match Directory", os.path.expanduser("~")
        )

        if dir_path:
            self.espanso_config_dir = dir_path
            self._refresh_data()
        else:
            self.statusBar().showMessage(C.MSG_DIR_SELECTION_CANCELLED)

    @pyqtSlot()
    def _refresh_data(self, select_category: str = None):
        """Reload all data from the config directory."""
        if not self.espanso_config_dir:
            QMessageBox.warning(self, "Error", C.ERROR_ESPANSO_DIR_NOT_SET)
            return

        self.statusBar().showMessage(C.MSG_REFRESHING_DATA)

        # Create and start the loader thread
        loader = DataLoader(self.espanso_config_dir)

        # Use a lambda to pass the select_category parameter
        if select_category:
            loader.signals.finished.connect(
                lambda data: self._handle_data_loaded(data, select_category)
            )
        else:
            loader.signals.finished.connect(self._handle_data_loaded)

        loader.signals.error.connect(self._handle_data_error)
        QThreadPool.globalInstance().start(loader)

    def _handle_data_loaded(self, data: Dict[str, Any], select_category: str = None):
        """Handle loaded data from the worker thread."""
        # Update internal state
        self.snippets_by_file_path = data["snippets_by_file"]
        self.category_dropdown_map = data["category_dropdown_map"]

        # Update UI
        self.category_selector.clear()
        display_names = data["category_display_names"]

        # Safely populate the QComboBox to avoid macOS NSException
        self._safely_populate_category_selector(display_names)

        # Select specific category if requested, otherwise select first one
        if select_category and select_category in display_names:
            index = display_names.index(select_category)
            self.category_selector.setCurrentIndex(index)
        elif display_names:
            self.category_selector.setCurrentIndex(0)

        # Update status
        msg = C.MSG_LOADED_SNIPPETS_COUNT.format(
            snippet_count=data["total_snippets_loaded"],
            category_count=len(display_names),
        )
        self.statusBar().showMessage(msg)

    def _handle_data_error(self, error_msg: str):
        """Handle errors from the worker thread."""
        QMessageBox.critical(self, "Error Loading Data", error_msg)
        self.statusBar().showMessage(C.MSG_SAVE_ERROR_UNEXPECTED)

    @pyqtSlot()
    def _new_snippet(self):
        """Create a new snippet in the current category."""
        if not self.active_file_path:
            QMessageBox.warning(self, "Error", C.ERROR_NO_CATEGORY_TO_ADD_SNIPPET)
            return

        # Create an empty snippet
        new_snippet = Snippet("", "", self.active_file_path)
        new_snippet.is_new = True

        # Open edit dialog
        dialog = EditSnippetDialog(self, "New Snippet", new_snippet)
        if dialog.exec():
            new_data = dialog.result

            # Check if trigger already exists
            existing_snippets = self.snippets_by_file_path.get(
                self.active_file_path, []
            )
            if any(s.trigger == new_data[C.COL_TRIGGER] for s in existing_snippets):
                QMessageBox.warning(
                    self,
                    "Error",
                    C.ERROR_TRIGGER_EXISTS.format(new_data[C.COL_TRIGGER]),
                )
                return

            # Update snippet and add to list
            new_snippet.mark_modified(new_data[C.COL_TRIGGER], new_data[C.COL_REPLACE])
            if self.active_file_path not in self.snippets_by_file_path:
                self.snippets_by_file_path[self.active_file_path] = []
            self.snippets_by_file_path[self.active_file_path].append(new_snippet)

            # Add to table
            row = self.snippet_table.rowCount()
            self.snippet_table.insertRow(row)
            self.snippet_table.setItem(
                row, 0, QTableWidgetItem(new_data[C.COL_TRIGGER])
            )
            preview = new_data[C.COL_REPLACE].split("\n")[0]
            if len(new_data[C.COL_REPLACE].splitlines()) > 1:
                preview += "..."
            self.snippet_table.setItem(row, 1, QTableWidgetItem(preview))

            # Auto-save the changes
            self._auto_save()

    @pyqtSlot()
    def _edit_selected(self):
        """Edit the currently selected snippet."""
        current = self.snippet_table.currentRow()
        if current < 0:
            return

        # Get the current snippet
        trigger = self.snippet_table.item(current, 0).text()
        snippets = self.snippets_by_file_path.get(self.active_file_path, [])
        snippet = next((s for s in snippets if s.trigger == trigger), None)

        if not snippet:
            QMessageBox.warning(self, "Error", C.ERROR_COULD_NOT_FIND_SNIPPET)
            return

        # Open edit dialog
        dialog = EditSnippetDialog(self, C.TITLE_EDIT_SNIPPET.format(trigger), snippet)
        if dialog.exec():
            new_data = dialog.result
            if snippet.mark_modified(new_data[C.COL_TRIGGER], new_data[C.COL_REPLACE]):
                # Update the table
                self.snippet_table.item(current, 0).setText(new_data[C.COL_TRIGGER])
                preview = new_data[C.COL_REPLACE].split("\n")[0]
                if len(new_data[C.COL_REPLACE].splitlines()) > 1:
                    preview += "..."
                self.snippet_table.item(current, 1).setText(preview)

    @pyqtSlot()
    def _new_category(self):
        """Create a new category file."""
        if not self.espanso_config_dir:
            QMessageBox.warning(self, "Error", C.ERROR_OPEN_ESPANSO_DIR_FIRST)
            return

        dialog = NewCategoryDialog(self, self.espanso_config_dir)
        if dialog.exec():
            result = dialog.result
            self.statusBar().showMessage(C.MSG_CREATING_CATEGORY)

            from file_handler import create_empty_category_file

            success, error_msg = create_empty_category_file(result["file_path"])

            if success:
                self.statusBar().showMessage(
                    C.MSG_CREATED_NEW_CATEGORY.format(result["display_name"])
                )
                # Store the new category name for selection after refresh
                new_category = result["display_name"]

                # Disconnect signal temporarily to prevent recursion
                self._disconnect_category_selector()

                # Refresh data and select the new category
                self._refresh_data(select_category=new_category)

                # Reconnect signal
                self._reconnect_category_selector()
            else:
                QMessageBox.critical(
                    self, "Error", error_msg or C.MSG_FAILED_CREATE_CATEGORY
                )

    def _move_selection_up(self):
        """Move selection up one row."""
        current = self.snippet_table.currentRow()
        if current > 0:
            self.snippet_table.selectRow(current - 1)

    def _move_selection_down(self):
        """Move selection down one row."""
        current = self.snippet_table.currentRow()
        if current < self.snippet_table.rowCount() - 1:
            self.snippet_table.selectRow(current + 1)

    @pyqtSlot(int)
    def _on_category_selected(self, index: int):
        """Handle category selection change."""
        if index < 0:
            return

        # Store the current selection index before any changes
        current_index = self.category_selector.currentIndex()
        category_name = self.category_selector.currentText()

        # Handle "Add new Category..." option
        if category_name == "Add new Category...":
            # Temporarily disconnect the signal to prevent recursive calls
            self._disconnect_category_selector()

            # Reset to first item if available, otherwise clear selection
            if (
                self.category_selector.count() > 2
            ):  # 2 because of separator and "Add new Category..."
                self.category_selector.setCurrentIndex(0)

            # Reconnect the signal
            self._reconnect_category_selector()

            # Show the new category dialog
            self._new_category()
            return

        self.active_file_path = self.category_dropdown_map.get(category_name)

        if not self.active_file_path:
            self.statusBar().showMessage(C.MSG_NO_CATEGORY_SELECTED)
            return

        # Display snippets for selected category
        self._display_snippets_for_category(category_name)

    def _display_snippets_for_category(self, category_name: str):
        """Display snippets for the selected category."""
        # Clear existing items
        self.snippet_table.setRowCount(0)

        # Get snippets for current category
        snippets = self.snippets_by_file_path.get(self.active_file_path, [])

        # Update table with existing snippets
        self.snippet_table.setRowCount(len(snippets))
        for row, snippet in enumerate(snippets):
            trigger_item = QTableWidgetItem(snippet.trigger)
            replace_item = QTableWidgetItem(
                snippet.replace_text.split("\n")[0] + "..."
                if "\n" in snippet.replace_text
                else snippet.replace_text
            )

            self.snippet_table.setItem(row, 0, trigger_item)
            self.snippet_table.setItem(row, 1, replace_item)

        # Add empty row at the bottom for new entries
        self._ensure_empty_bottom_row()

        # Update status bar
        self.statusBar().showMessage(
            C.MSG_CATEGORY_DISPLAY.format(
                category_name=category_name,
                snippet_count=len(snippets),
                mtime=datetime.fromtimestamp(
                    os.path.getmtime(self.active_file_path)
                ).strftime("%Y-%m-%d %H:%M:%S")
                if os.path.exists(self.active_file_path)
                else "Unknown",
            )
        )

    @pyqtSlot()
    def _remove_selected_snippets(self):
        """Remove selected snippets from the active category."""
        if not self.active_file_path:
            QMessageBox.warning(self, "Error", C.ERROR_NO_CATEGORY_TO_REMOVE)
            return

        selected_rows = sorted(
            set(item.row() for item in self.snippet_table.selectedItems())
        )
        if not selected_rows:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Delete")
        layout = QVBoxLayout(dialog)

        # Question label
        question = QLabel(f"Delete {len(selected_rows)}?")
        layout.addWidget(question)

        # Buttons
        button_box = QDialogButtonBox()
        no_button = button_box.addButton("No", QDialogButtonBox.ButtonRole.RejectRole)
        yes_button = button_box.addButton("Yes", QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec():
            # Remove the snippets from our data structure
            snippets = self.snippets_by_file_path.get(self.active_file_path, [])
            triggers_to_remove = [
                self.snippet_table.item(row, 0).text() for row in selected_rows
            ]
            self.snippets_by_file_path[self.active_file_path] = [
                s for s in snippets if s.trigger not in triggers_to_remove
            ]

            # Remove the rows from the table
            for row in reversed(
                selected_rows
            ):  # Remove from bottom to top to keep indices valid
                self.snippet_table.removeRow(row)

            # Auto-save after removal
            self._auto_save()

    @pyqtSlot()
    def _delete_category(self):
        """Delete the current category file."""
        if not self.active_file_path or not os.path.exists(self.active_file_path):
            QMessageBox.warning(self, "Error", C.ERROR_NO_CATEGORY_TO_REMOVE)
            return

        category_name = self.category_selector.currentText()

        dialog = QDialog(self)
        dialog.setWindowTitle("Delete")
        layout = QVBoxLayout(dialog)

        # Question label
        question = QLabel(f"Delete {category_name}?")
        layout.addWidget(question)

        # Buttons
        button_box = QDialogButtonBox()
        no_button = button_box.addButton("No", QDialogButtonBox.ButtonRole.RejectRole)
        yes_button = button_box.addButton("Yes", QDialogButtonBox.ButtonRole.AcceptRole)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec():
            try:
                # Delete the file
                os.remove(self.active_file_path)

                # Clean up internal state
                del self.snippets_by_file_path[self.active_file_path]
                del self.category_dropdown_map[category_name]

                # Refresh the display
                self._refresh_data()

                self.statusBar().showMessage(
                    C.MSG_CATEGORY_DELETED.format(category_name)
                )
            except Exception:
                QMessageBox.critical(
                    self, "Error", C.MSG_FAILED_DELETE_CATEGORY.format(category_name)
                )

    def _save_all_changes(self):
        """Save all changes to disk."""
        modified_files = {
            file_path: snippets
            for file_path, snippets in self.snippets_by_file_path.items()
            if any(s.is_modified or s.is_new for s in snippets)
        }

        if not modified_files:
            self.statusBar().showMessage("No changes to save")
            return

        self.statusBar().showMessage(C.MSG_SAVING_ALL_CHANGES)

        # Save each modified file
        for file_path, snippets in modified_files.items():
            saver = DataSaver(file_path, snippets)
            saver.signals.finished.connect(self._handle_save_complete)
            saver.signals.error.connect(self._handle_save_error)
            self.thread_pool.start(saver)

    def _handle_save_complete(self, data: Dict[str, Any]):
        """Handle successful save operation."""
        file_path = data["file_path"]
        # Reset modified flags
        for snippet in self.snippets_by_file_path.get(file_path, []):
            snippet.is_modified = False
            snippet.is_new = False

        self.statusBar().showMessage(C.MSG_SAVE_SUCCESSFUL_COUNT.format(count=1))

    def _handle_save_error(self, error_msg: str):
        """Handle save operation error."""
        QMessageBox.critical(self, "Error Saving Data", error_msg)
        self.statusBar().showMessage(C.MSG_SAVE_ERROR_UNEXPECTED)

    def _auto_save(self):
        """Automatically save changes without showing dialogs."""
        modified_files = {
            file_path: snippets
            for file_path, snippets in self.snippets_by_file_path.items()
            if any(s.is_modified or s.is_new for s in snippets)
        }

        if not modified_files:
            return

        self.statusBar().showMessage("Auto-saving changes...")

        # Save each modified file
        for file_path, snippets in modified_files.items():
            saver = DataSaver(file_path, snippets)
            saver.signals.finished.connect(self._handle_autosave_complete)
            saver.signals.error.connect(self._handle_save_error)
            self.thread_pool.start(saver)

    def _handle_autosave_complete(self, data: Dict[str, Any]):
        """Handle successful autosave operation silently."""
        file_path = data["file_path"]
        # Reset modified flags
        for snippet in self.snippets_by_file_path.get(file_path, []):
            snippet.is_modified = False
            snippet.is_new = False

        self.statusBar().showMessage("Changes saved", 2000)  # Show for 2 seconds only

    @pyqtSlot(QTableWidgetItem)
    def _on_item_edited(self, item: QTableWidgetItem):
        """Handle in-place editing of table items."""
        if not self.active_file_path:
            if item.text().strip():  # Only show error if actually trying to enter data
                QMessageBox.warning(self, "Error", C.ERROR_NO_CATEGORY_TO_ADD_SNIPPET)
                item.setText("")  # Clear the invalid entry
            return

        row = item.row()
        col = item.column()
        new_value = item.text().strip()
        snippets = self.snippets_by_file_path.get(self.active_file_path, [])
        other_cell = self.snippet_table.item(row, 1 if col == 0 else 0)
        other_value = other_cell.text().strip() if other_cell else ""

        # Get the current trigger (for duplicate checks)
        current_trigger = new_value if col == 0 else other_value

        # If editing a trigger, check for duplicates (excluding self)
        if col == 0 and current_trigger:
            old_trigger = item.text()  # Before the edit
            for s in snippets:
                if s.trigger == current_trigger and s.trigger != old_trigger:
                    QMessageBox.warning(
                        self, "Error", C.ERROR_TRIGGER_EXISTS.format(current_trigger)
                    )
                    item.setText(old_trigger)  # Revert the change
                    return

        # Update or create snippet
        replace_text = other_value if col == 0 else new_value
        trigger = current_trigger if col == 0 else other_value

        # Find existing snippet or create a new one
        snippet = next((s for s in snippets if s.trigger == trigger), None)
        if snippet:
            # Update existing snippet
            if new_value:  # Only update if there's a value
                snippet.mark_modified(trigger, replace_text)
        else:
            # Create new snippet if we have both trigger and replace text
            if trigger and replace_text:
                new_snippet = Snippet(trigger, replace_text, self.active_file_path)
                new_snippet.is_new = True
                if self.active_file_path not in self.snippets_by_file_path:
                    self.snippets_by_file_path[self.active_file_path] = []
                self.snippets_by_file_path[self.active_file_path].append(new_snippet)

        # Auto-save if we have both trigger and replace text
        if trigger and replace_text:
            self._auto_save()

        # Always ensure there's an empty row at the bottom
        self._ensure_empty_bottom_row()

    def _ensure_empty_bottom_row(self):
        """Ensure there is an empty row at the bottom of the table for adding new snippets."""
        # If the last row has any content, add a new empty row
        last_row = self.snippet_table.rowCount() - 1
        last_row_has_content = False

        if last_row >= 0:
            trigger_item = self.snippet_table.item(last_row, 0)
            replace_item = self.snippet_table.item(last_row, 1)
            if (trigger_item and trigger_item.text().strip()) or (
                replace_item and replace_item.text().strip()
            ):
                last_row_has_content = True

        if last_row < 0 or last_row_has_content:
            # Add new empty row
            new_row = self.snippet_table.rowCount()
            self.snippet_table.insertRow(new_row)
            self.snippet_table.setItem(new_row, 0, QTableWidgetItem(""))
            self.snippet_table.setItem(new_row, 1, QTableWidgetItem(""))

    def _refresh_snippet_table(self):
        """Refresh the snippet table with current data."""
        if self.active_file_path and self.category_selector.currentText():
            self._display_snippets_for_category(self.category_selector.currentText())

    def _safely_populate_category_selector(self, display_names: List[str]):
        """Safely populate the category selector to avoid macOS NSException in QComboBox.addItems()."""
        try:
            # Block signals temporarily to prevent recursive calls during population
            self.category_selector.blockSignals(True)
            
            # Add categories one by one instead of using addItems() to avoid NSException
            if display_names:
                for name in display_names:
                    # Validate each name before adding
                    if name and isinstance(name, str):
                        self.category_selector.addItem(name)
                
                # Add separator only if we have valid categories
                if self.category_selector.count() > 0:
                    self.category_selector.insertSeparator(self.category_selector.count())
            
            # Always add the "Add new Category..." option at the end
            self.category_selector.addItem("Add new Category...")
            
        except Exception as e:
            print(f"Error safely populating category selector: {e}")
            # Fallback: ensure at least the "Add new Category..." option is available
            try:
                self.category_selector.clear()
                self.category_selector.addItem("Add new Category...")
            except Exception as fallback_error:
                print(f"Critical error in category selector fallback: {fallback_error}")
        finally:
            # Always re-enable signals
            self.category_selector.blockSignals(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set fusion style for consistent look
    app.setStyle("Fusion")

    # Set application icon
    icon_path = os.path.join(os.path.dirname(__file__), "logo.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Increase font sizes slightly for better macOS rendering
    font = app.font()
    font.setPointSize(13)
    app.setFont(font)

    window = EZpanso()
    window.show()
    sys.exit(app.exec())
