"""
EZpanso - PyQt6 Version (Improved)
A modern GUI for managing Espanso text expansion snippets.

Key improvements:
- Better error handling and type safety
- Extracted helper methods to reduce duplication
- Clearer separation of concerns
- More robust state management
"""

import sys
import os
import logging
import webbrowser
import copy
from typing import Dict, List, Any, Optional
from PyQt6.QtCore import (
    Qt,
    pyqtSlot,
    QThreadPool,
    QRunnable,
)  # Added QRunnable for type hint
from PyQt6.QtGui import QKeySequence, QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QMessageBox,
    QLabel,
    QDialog,
    QSizePolicy,
    QTextEdit,
    QDialogButtonBox,
    QHeaderView,
    QMenuBar,
)

# Assuming these modules are in the same directory or correctly in PYTHONPATH
from ui_utils import UIHelpers
from qt_data_loader import DataLoader, DataSaver
from utils import get_default_espanso_config_path
from data_model import Snippet
import constants as C

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class SnippetValidator:
    @staticmethod
    def validate_trigger(
        trigger: str,
        existing_snippets: List[Snippet],
        exclude_trigger: Optional[str] = None,
    ) -> None:
        if not trigger.strip():
            raise ValidationError(C.ERROR_TRIGGER_EMPTY)
        for snippet in existing_snippets:
            if snippet.trigger == trigger and snippet.trigger != exclude_trigger:
                raise ValidationError(C.ERROR_TRIGGER_EXISTS.format(trigger=trigger))


class EditSnippetDialog(QDialog):
    def __init__(self, parent: QWidget, title: str, snippet: Snippet):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.snippet = snippet  # Store the original snippet
        self.result: Optional[Dict[str, str]] = None
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        if parent:
            self.setParent(parent)
        self.setMinimumSize(500, 350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        trigger_layout = QHBoxLayout()
        trigger_label = QLabel("Trigger:")
        self.trigger_entry = QLineEdit()
        self.trigger_entry.setText(self.snippet.trigger)
        self.trigger_entry.setMinimumWidth(300)
        trigger_layout.addWidget(trigger_label)
        trigger_layout.addWidget(self.trigger_entry)
        layout.addLayout(trigger_layout)

        replace_layout = QHBoxLayout()
        replace_label = QLabel("Replace:")
        self.replace_text = QTextEdit()
        self.replace_text.setText(self.snippet.replace_text)
        self.replace_text.setMinimumHeight(200)
        replace_layout.addWidget(replace_label)
        replace_layout.addWidget(self.replace_text)
        layout.addLayout(replace_layout)

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


class NewFileDialog(QDialog):
    def __init__(self, parent: QWidget, espanso_match_dir: str):
        super().__init__(parent)
        self.setWindowTitle(C.TITLE_NEW_FILE)
        self.setModal(True)
        self.espanso_match_dir = espanso_match_dir
        self.result: Optional[Dict[str, str]] = None
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        if parent:
            self.setParent(parent)
        self.setMinimumSize(400, 180)
        self.setMaximumSize(600, 250)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        name_layout = QHBoxLayout()
        name_label = QLabel("Title:")
        name_label.setMinimumWidth(60)
        self.name_entry = QLineEdit()
        self.name_entry.setMinimumWidth(300)
        self.name_entry.setPlaceholderText("Enter file name (no extension)...")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_entry)
        layout.addLayout(name_layout)
        desc_label = QLabel(f"A .yml file will be created in {self.espanso_match_dir}.")
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        self.name_entry.setFocus()

    def accept(self):
        name = self.name_entry.text().strip()
        if not name:
            QMessageBox.critical(self, "Error", C.ERROR_FILE_NAME_EMPTY)
            return
        if any(c in name for c in r'/\\:*?"<>|'):
            QMessageBox.critical(self, "Error", C.ERROR_FILE_NAME_INVALID_CHARS)
            return
        if name.endswith((".yml", ".yaml")):
            QMessageBox.critical(self, "Error", C.ERROR_FILE_NO_EXTENSION)
            return
        filename = f"{name}.yml"
        original_file_path = os.path.join(self.espanso_match_dir, filename)
        if os.path.exists(original_file_path):
            QMessageBox.critical(
                self, "Error", C.ERROR_FILE_FILE_EXISTS.format(filename=filename)
            )
            return
        self.result = {"file_path": original_file_path, "display_name": filename}
        super().accept()


class EZpanso(QMainWindow):
    thread_pool: QThreadPool # Add class-level type hint

    def __init__(self):
        super().__init__()
        self.setWindowTitle(C.TITLE_APP)
        self.resize(1000, 600)
        self._init_state()
        self._setup_ui_elements()
        self._setup_menu_and_shortcuts()
        self._load_initial_config()

    def _init_state(self):
        self.espanso_match_dir = ""
        self.file_dropdown_map: Dict[str, str] = {}
        self.active_file_path: Optional[str] = None
        global_pool = QThreadPool.globalInstance()
        self.thread_pool = global_pool if global_pool is not None else QThreadPool()
        self.is_modified = False
        self.original_data: Dict[str, List[Snippet]] = {}
        self.current_data: Dict[str, List[Snippet]] = {}
        self.data_loader_thread: Optional[DataLoader] = None
        self.data_saver_thread: Optional[DataSaver] = None
        self._set_application_icon()

    def _set_application_icon(self):
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning(f"Application icon not found at {icon_path}")

    def _setup_ui_elements(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self._setup_file_selector_ui(main_layout)
        self._setup_snippet_table_ui(main_layout)
        self._setup_button_bar_ui(main_layout)
        self._setup_status_bar_ui()

    def _setup_menu_and_shortcuts(self):
        menubar = QMenuBar() # Remove noqa: F821
        self.setMenuBar(menubar)
        file_menu = menubar.addMenu("&File")
        # Use C.MENU_FILE_NEW_FILE if it exists and is preferred for the label
        new_file_action = QAction(
            C.DROPDOWN_CREATE_NEW_FILE.split(" (")[0], self
        )  # Label from constant
        new_file_action.triggered.connect(self._new_file)
        file_menu.addAction(new_file_action)

        save_action = QAction(C.BTN_SAVE_ALL, self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._manual_save_triggered)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        exit_action = QAction("&Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("&Help")
        espanso_hub_action = QAction("Espanso Hub", self)
        espanso_hub_action.triggered.connect(self._open_espanso_hub)
        help_menu.addAction(espanso_hub_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)

    def _setup_file_selector_ui(self, layout: QVBoxLayout):
        file_selector_layout = QHBoxLayout()
        self.file_selector = QComboBox()
        self.file_selector.setMinimumWidth(200)
        self.file_selector.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.file_selector.currentIndexChanged.connect(self._on_file_selected)
        file_selector_layout.addWidget(self.file_selector)

        # Using text directly for buttons, or ensure constants like C.BTN_NEW_FILE_TEXT exist
        new_file_btn = QPushButton(C.DROPDOWN_CREATE_NEW_FILE.split(" (")[0])
        new_file_btn.clicked.connect(self._new_file)
        file_selector_layout.addWidget(new_file_btn)

        delete_file_btn = QPushButton(C.BTN_DELETE_FILE.split(" (")[0])
        delete_file_btn.clicked.connect(self._delete_category)
        file_selector_layout.addWidget(delete_file_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setShortcut(QKeySequence(C.SHORTCUT_REFRESH))
        refresh_btn.clicked.connect(self._refresh_data)
        file_selector_layout.addWidget(refresh_btn)
        layout.addLayout(file_selector_layout)

    def _setup_snippet_table_ui(self, layout: QVBoxLayout):
        self.snippet_table = QTableWidget()
        self.snippet_table.setColumnCount(2)
        self.snippet_table.setHorizontalHeaderLabels([C.COL_TRIGGER, C.COL_REPLACE])
        # Ensure header is available before configuring resize mode
        header = self.snippet_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            header.setStretchLastSection(
                False
            )  # Ensure last section doesn't always stretch if column 1 is not last
            self.snippet_table.setColumnWidth(0, 250)

        self.snippet_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.snippet_table.itemChanged.connect(self._on_item_edited)
        self.snippet_table.doubleClicked.connect(self._edit_selected_on_double_click)
        layout.addWidget(self.snippet_table)

    def _setup_button_bar_ui(self, layout: QVBoxLayout):
        button_layout = QHBoxLayout()
        # Using text from constants, ensure they are defined e.g. C.BTN_NEW_SNIPPET_TEXT
        add_btn = QPushButton(C.BTN_NEW_SNIPPET.split(" (")[0])
        add_btn.setShortcut(QKeySequence(C.SHORTCUT_ADD))
        add_btn.clicked.connect(self._create_new_snippet)
        button_layout.addWidget(add_btn)

        edit_btn = QPushButton(C.BTN_EDIT_SNIPPET.split(" (")[0])
        edit_btn.setShortcut(QKeySequence(C.SHORTCUT_EDIT))
        edit_btn.clicked.connect(self._edit_selected)
        button_layout.addWidget(edit_btn)

        remove_btn = QPushButton(C.BTN_DELETE_SNIPPET.split(" (")[0])
        remove_btn.setShortcut(QKeySequence(C.SHORTCUT_DELETE))
        remove_btn.clicked.connect(self._remove_selected_snippets)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _setup_status_bar_ui(self):
        self.status_bar = self.statusBar()
        if self.status_bar:
            self.status_bar.showMessage("Ready.")
        else:
            logger.error("QMainWindow statusBar is None, cannot display status.")
            # As a last resort, create a QLabel and add it to the main layout if statusbar is critical
            # For now, we assume self.statusBar() works.

    def _update_status(self, message: str, timeout: int = 0):
        if self.status_bar:  # Check if status_bar exists and is a QStatusBar
            if hasattr(self.status_bar, "showMessage"):
                self.status_bar.showMessage(message, timeout)
            else:
                logger.warning(
                    "Attempted to use showMessage on a non-QStatusBar object."
                )
        logger.info(f"Status: {message}")

    @pyqtSlot()
    def _manual_save_triggered(self):
        self._save_all_changes()

    def _create_new_snippet(self):
        if not self.active_file_path:
            QMessageBox.warning(self, "Error", C.ERROR_NO_FILE_TO_ADD_SNIPPET)
            return
        dialog = None
        try:
            new_snippet_for_dialog = Snippet("", "", self.active_file_path)
            dialog_title = C.TITLE_EDIT_SNIPPET.format(
                "New Snippet"
            )  # Use format for title
            dialog = EditSnippetDialog(self, dialog_title, new_snippet_for_dialog)
            if dialog.exec() != QDialog.DialogCode.Accepted or not dialog.result:
                return
            result_data = dialog.result
            active_snippets = self.current_data.get(self.active_file_path, [])
            SnippetValidator.validate_trigger(
                result_data[C.COL_TRIGGER], active_snippets
            )
            final_new_snippet = Snippet(
                trigger=result_data[C.COL_TRIGGER],
                replace_text=result_data[C.COL_REPLACE],
                file_path=self.active_file_path,
            )
            self._add_snippet_to_data(final_new_snippet)
            self._add_snippet_to_table_display(final_new_snippet)
            self.is_modified = True
            self._update_window_title()
            self._ensure_empty_bottom_row()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            logger.error(f"Error creating new snippet: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
        finally:
            if dialog:
                dialog.deleteLater()

    def _add_snippet_to_data(self, snippet: Snippet):
        if not snippet.file_path:
            logger.error("Attempted to add snippet with no file_path.")
            return
        if snippet.file_path not in self.current_data:
            self.current_data[snippet.file_path] = []
        self.current_data[snippet.file_path].append(snippet)

    def _add_snippet_to_table_display(self, snippet: Snippet):
        row = self.snippet_table.rowCount()
        # If the last row is the empty "new entry" row, insert before it
        if row > 0:
            last_row_trigger_item = self.snippet_table.item(row - 1, 0)
            is_trigger_empty = (
                not last_row_trigger_item or not last_row_trigger_item.text().strip()
            )
            if is_trigger_empty:
                row -= 1
        self.snippet_table.insertRow(row)
        trigger_item = QTableWidgetItem(snippet.trigger)
        replace_preview = UIHelpers.create_preview_text(snippet.replace_text)
        replace_item = QTableWidgetItem(replace_preview)
        self.snippet_table.setItem(row, 0, trigger_item)
        self.snippet_table.setItem(row, 1, replace_item)

    @pyqtSlot(QTableWidgetItem)
    def _on_item_edited(self, item: QTableWidgetItem):
        if not self.active_file_path or self.active_file_path not in self.current_data:
            return
        active_snippets = self.current_data[self.active_file_path]
        row, col, new_text = item.row(), item.column(), item.text()

        if row >= len(active_snippets):  # Editing placeholder row
            if col == 0 and new_text.strip():
                replace_item = self.snippet_table.item(row, 1)
                replace_text = (
                    replace_item.text()
                    if replace_item and replace_item.text().strip()
                    else ""
                )
                try:
                    SnippetValidator.validate_trigger(new_text, active_snippets)
                    new_snippet_obj = Snippet(
                        new_text, replace_text, self.active_file_path
                    )
                    active_snippets.append(new_snippet_obj)
                    if not replace_item or not replace_item.text().strip():
                        self.snippet_table.setItem(
                            row,
                            1,
                            QTableWidgetItem(
                                UIHelpers.create_preview_text(replace_text)
                            ),
                        )
                    self.is_modified = True
                    self._update_window_title()
                    self._ensure_empty_bottom_row()
                except ValidationError as e:
                    QMessageBox.warning(self, "Validation Error", str(e))
                    item.setText("")
            elif col == 1 and new_text.strip():
                trigger_item = self.snippet_table.item(row, 0)
                if trigger_item and trigger_item.text().strip():
                    trigger_text = trigger_item.text().strip()
                    try:
                        SnippetValidator.validate_trigger(trigger_text, active_snippets)
                        new_snippet_obj = Snippet(
                            trigger_text, new_text, self.active_file_path
                        )
                        active_snippets.append(new_snippet_obj)
                        item.setText(UIHelpers.create_preview_text(new_text))
                        self.is_modified = True
                        self._update_window_title()
                        self._ensure_empty_bottom_row()
                    except ValidationError as e:
                        QMessageBox.warning(self, "Validation Error", str(e))
                        if trigger_item:
                            trigger_item.setText("")
            return

        if row < len(active_snippets):  # Editing existing snippet
            snippet_to_edit = active_snippets[row]
            original_trigger = snippet_to_edit.trigger
            if col == 0:
                try:
                    SnippetValidator.validate_trigger(
                        new_text, active_snippets, exclude_trigger=original_trigger
                    )
                    snippet_to_edit.trigger = new_text
                except ValidationError as e:
                    QMessageBox.warning(self, "Validation Error", str(e))
                    item.setText(original_trigger)
                    return
            elif col == 1:
                snippet_to_edit.replace_text = new_text
                item.setText(UIHelpers.create_preview_text(new_text))
            self.is_modified = True
            self._update_window_title()

    def _ensure_empty_bottom_row(self):
        if not self.active_file_path:
            if self.snippet_table.rowCount() > 0:
                self.snippet_table.setRowCount(0)
            return
        current_rows = self.snippet_table.rowCount()
        has_empty_row = False
        if current_rows > 0:
            last_row_trigger_item = self.snippet_table.item(current_rows - 1, 0)
            last_row_replace_item = self.snippet_table.item(current_rows - 1, 1)
            is_trigger_empty = (
                not last_row_trigger_item or not last_row_trigger_item.text().strip()
            )
            is_replace_empty = (
                not last_row_replace_item or not last_row_replace_item.text().strip()
            )
            if is_trigger_empty and is_replace_empty:
                has_empty_row = True
        if not has_empty_row:
            self.snippet_table.insertRow(current_rows)

    @pyqtSlot()
    def _edit_selected_on_double_click(self):
        self._edit_selected()

    def _edit_selected(self):
        if not self.active_file_path or self.active_file_path not in self.current_data:
            QMessageBox.warning(self, "Error", "No file or snippets to edit.")
            return
        selected_items = self.snippet_table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Info", C.ERROR_NO_SNIPPET_SELECTED_EDIT)
            return
        row_to_edit = selected_items[0].row()
        active_snippets = self.current_data[self.active_file_path]
        if row_to_edit >= len(active_snippets):
            QMessageBox.warning(
                self,
                "Info",
                "Cannot edit the new entry row with this action. Type directly.",
            )
            return
        snippet_to_edit = active_snippets[row_to_edit]
        dialog_title = C.TITLE_EDIT_SNIPPET.format(
            os.path.basename(snippet_to_edit.file_path)
            + " - "
            + snippet_to_edit.trigger[:20]
        )
        dialog = EditSnippetDialog(self, dialog_title, snippet_to_edit)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result:
            new_trigger, new_replace = (
                dialog.result[C.COL_TRIGGER],
                dialog.result[C.COL_REPLACE],
            )
            try:
                SnippetValidator.validate_trigger(
                    new_trigger,
                    active_snippets,
                    exclude_trigger=snippet_to_edit.trigger,
                )
                snippet_to_edit.trigger = new_trigger
                snippet_to_edit.replace_text = new_replace
                self.is_modified = True
                self._update_window_title()
                # Ensure table items exist before setting text
                trigger_table_item = self.snippet_table.item(row_to_edit, 0)
                if trigger_table_item:
                    trigger_table_item.setText(new_trigger)
                else:
                    self.snippet_table.setItem(
                        row_to_edit, 0, QTableWidgetItem(new_trigger)
                    )

                replace_table_item = self.snippet_table.item(row_to_edit, 1)
                if replace_table_item:
                    replace_table_item.setText(
                        UIHelpers.create_preview_text(new_replace)
                    )
                else:
                    self.snippet_table.setItem(
                        row_to_edit,
                        1,
                        QTableWidgetItem(UIHelpers.create_preview_text(new_replace)),
                    )

            except ValidationError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
        if dialog:
            dialog.deleteLater()

    def _remove_selected_snippets(self):
        if not self.active_file_path or self.active_file_path not in self.current_data:
            QMessageBox.warning(self, "Error", "No file or snippets to delete from.")
            return
        selected_rows = sorted(
            list(set(item.row() for item in self.snippet_table.selectedItems())),
            reverse=True,
        )
        if not selected_rows:
            QMessageBox.information(self, "Info", C.ERROR_NO_SNIPPET_SELECTED_DELETE)
            return
        valid_rows_to_delete = [
            r
            for r in selected_rows
            if r < len(self.current_data[self.active_file_path])
        ]
        if not valid_rows_to_delete:
            QMessageBox.information(
                self, "Info", "No actual snippets selected for deletion."
            )
            return
        reply = UIHelpers.create_confirmation_dialog(
            self, C.MSG_CONFIRM_DELETE_SNIPPET_TITLE, C.MSG_CONFIRM_DELETE_SNIPPET_TEXT
        )
        if reply == QMessageBox.StandardButton.Yes:
            active_snippets_list = self.current_data[self.active_file_path]
            for row in valid_rows_to_delete:
                del active_snippets_list[row]
                self.snippet_table.removeRow(row)
            self.is_modified = True
            self._update_window_title()
            self._ensure_empty_bottom_row()

    def _save_all_changes(self):
        if not self.is_modified:
            self._update_status("No changes to save.", 3000)
            return
        modified_files_details = []
        deleted_original_paths = set(self.original_data.keys()) - set(
            self.current_data.keys()
        )
        if not self.espanso_match_dir or not os.path.isdir(self.espanso_match_dir):
            UIHelpers.show_error_message(self, "Espanso match directory not set.")
            return
        try:
            espanso_config_parent_dir = os.path.dirname(self.espanso_match_dir)
            if not espanso_config_parent_dir:
                UIHelpers.show_error_message(
                    self, "Cannot determine parent for temp save."
                )
                return
            temp_ez_dir = os.path.join(espanso_config_parent_dir, C.TEMP_EZ_FOLDER_NAME)
        except Exception as e:
            logger.error(f"Error determining temp_ez_dir: {e}", exc_info=True)
            UIHelpers.show_error_message(
                self, f"Error setting up temp save location: {e}"
            )
            return

        for original_file_path, current_snippets_list in self.current_data.items():
            original_snippets_list = self.original_data.get(original_file_path)
            is_new_file = original_file_path not in self.original_data
            if is_new_file or self._are_snippet_lists_different(
                current_snippets_list,
                original_snippets_list if original_snippets_list else [],
            ):
                original_filename = os.path.basename(original_file_path)
                temp_save_path = os.path.join(temp_ez_dir, original_filename)
                modified_files_details.append(
                    {"path": temp_save_path, "snippets": current_snippets_list}
                )

        total_affected_files = len(modified_files_details) + len(deleted_original_paths)
        if total_affected_files == 0:
            self._update_status("No effective changes to save.", 3000)
            self.is_modified = False
            self._update_window_title()
            return

        reply = UIHelpers.create_confirmation_dialog(
            self,
            "Save Changes?",
            f"You have {total_affected_files} file(s) with changes. Save to '{C.TEMP_EZ_FOLDER_NAME}' backup?",
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._execute_save_to_temp_ez(
                temp_ez_dir, modified_files_details, list(deleted_original_paths)
            )
        else:
            self._update_status("Save cancelled.", 3000)

    def _are_snippet_lists_different(
        self, list1: List[Snippet], list2: List[Snippet]
    ) -> bool:
        if len(list1) != len(list2):
            return True
        for s1, s2 in zip(list1, list2):
            if (
                s1.trigger != s2.trigger
                or s1.replace_text != s2.replace_text
                or s1.original_yaml_entry != s2.original_yaml_entry
            ):
                return True
        return False

    def _execute_save_to_temp_ez(
        self,
        temp_ez_dir: str,
        files_to_save_pkg: List[Dict[str, Any]],
        deleted_original_paths: List[str],
    ):
        try:
            if not os.path.exists(temp_ez_dir):
                os.makedirs(temp_ez_dir, exist_ok=True)
                logger.info(f"Created temp directory: {temp_ez_dir}")
        except Exception as e:
            logger.error(
                f"Error creating temp directory {temp_ez_dir}: {e}", exc_info=True
            )
            UIHelpers.show_error_message(self, f"Error creating temp directory: {e}")
            return

        for original_file_path_to_delete in deleted_original_paths:
            original_filename = os.path.basename(original_file_path_to_delete)
            temp_file_to_delete_path = os.path.join(temp_ez_dir, original_filename)
            if os.path.exists(temp_file_to_delete_path):
                try:
                    os.remove(temp_file_to_delete_path)
                    logger.info(
                        f"Deleted {temp_file_to_delete_path} from {C.TEMP_EZ_FOLDER_NAME}."
                    )
                except Exception as e:
                    logger.error(
                        f"Error deleting {temp_file_to_delete_path} from {C.TEMP_EZ_FOLDER_NAME}: {e}",
                        exc_info=True,
                    )

        if not files_to_save_pkg and not deleted_original_paths:
            self._update_status("No changes to save to temp directory.", 3000)
            self.is_modified = False
            self._update_window_title()
            return

        if files_to_save_pkg:
            self._update_status(
                f"Saving {len(files_to_save_pkg)} file(s) to {C.TEMP_EZ_FOLDER_NAME}...",
                0,
            )
            self.data_saver_thread = DataSaver(files_to_save_pkg)
            self.data_saver_thread.signals.save_complete.connect(
                self._handle_save_complete
            )
            self.data_saver_thread.signals.save_error.connect(self._handle_save_error)
            self.thread_pool.start(self.data_saver_thread)
        elif deleted_original_paths and not files_to_save_pkg:
            self._handle_save_complete([])

    def _handle_save_complete(self, saved_temp_files_paths: List[str]):
        num_saved = len(saved_temp_files_paths)
        self._update_status(
            f"Successfully saved changes to '{C.TEMP_EZ_FOLDER_NAME}'. ({num_saved} file(s) written/updated).",
            5000,
        )
        self.is_modified = False
        self._update_window_title()
        self.original_data = copy.deepcopy(self.current_data)
        logger.info(f"Save complete. Temp files affected: {saved_temp_files_paths}")

    def _handle_save_error(self, error_message: str):
        UIHelpers.show_error_message(
            self, f"Error saving to '{C.TEMP_EZ_FOLDER_NAME}': {error_message}"
        )
        self._update_status(f"Error saving changes: {error_message}", 0)

    def _update_window_title(self, modified: Optional[bool] = None):
        base_title = C.TITLE_APP
        current_modified_status = self.is_modified if modified is None else modified
        self.setWindowTitle(f"{base_title}{' *' if current_modified_status else ''}")

    def closeEvent(self, event):
        if self.is_modified:
            reply = QMessageBox.question(
                self,
                C.MSG_UNSAVED_CHANGES_TITLE,
                C.MSG_UNSAVED_CHANGES_TEXT,
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_all_changes()
                if self.is_modified:
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()

    def _load_initial_config(self):
        self._update_status(C.MSG_LOADING_INITIAL_CONFIG)
        detected_match_dir = get_default_espanso_config_path()
        if not detected_match_dir or not os.path.isdir(detected_match_dir):
            QMessageBox.warning(
                self,
                "Error",
                C.ERROR_ESPANSO_DIR_NOT_FOUND
                + " Please ensure Espanso is installed and configured.",
            )
            self._update_status(C.ERROR_ESPANSO_DIR_NOT_FOUND, 0)
            self.current_data, self.original_data = {}, {}
            self._safely_populate_file_selector([])
            self.snippet_table.setRowCount(0)
            self._ensure_empty_bottom_row()
            return
        self.espanso_match_dir = detected_match_dir
        logger.info(f"Espanso match directory set to: {self.espanso_match_dir}")
        self._refresh_data()

    def _refresh_data(self):
        if not self.espanso_match_dir:
            logger.warning("Refresh data: espanso_match_dir not set.")
            self.snippet_table.setRowCount(0)
            self._ensure_empty_bottom_row()
            self._safely_populate_file_selector([])
            return

        self._update_status(C.MSG_REFRESHING_DATA)

        # Check if a QRunnable from this instance is already running or queued
        # This is a simplified check; QThreadPool doesn't directly expose QRunnables by instance.
        # A more robust check would involve managing active runnables.
        if (
            isinstance(self.data_loader_thread, QRunnable)
            and self.thread_pool.activeThreadCount() > 0
        ):
            # A simple way to check if *any* thread is active, not specific to this loader.
            # For more precise control, DataLoader could set an internal flag or emit a started signal.
            current_active_runnable = getattr(
                self.data_loader_thread, "_is_running_flag", False
            )
            if current_active_runnable:
                logger.info(
                    "Data loading already in progress. Ignoring refresh request."
                )
                return

        self.data_loader_thread = DataLoader(self.espanso_match_dir)
        # Add a flag to the runnable instance (optional, for more direct checking)
        # setattr(self.data_loader_thread, '_is_running_flag', True)
        self.data_loader_thread.signals.data_loaded.connect(self._handle_data_loaded)
        self.thread_pool.start(self.data_loader_thread)

    @pyqtSlot(dict, object)
    def _handle_data_loaded(
        self, loaded_data_package: Dict[str, Any], error_str: Optional[str] = None
    ):
        # if hasattr(self.data_loader_thread, '_is_running_flag'):
        #     setattr(self.data_loader_thread, '_is_running_flag', False)

        if error_str:
            UIHelpers.show_error_message(self, f"Error loading data: {error_str}")
            # Ensure C.MSG_LOAD_ERROR is defined in your constants.py file
            self._update_status(C.MSG_LOAD_ERROR + f": {error_str}", 0) # Pylance error here if C.MSG_LOAD_ERROR is missing
            self.current_data, self.original_data, self.file_dropdown_map = {}, {}, {}
            self._safely_populate_file_selector([])
            self.snippet_table.setRowCount(0)
            self._ensure_empty_bottom_row()
            self.is_modified = False
            self._update_window_title()
            return

        self.current_data = loaded_data_package.get("snippets_by_file", {})
        self.original_data = copy.deepcopy(self.current_data)
        self.file_dropdown_map = loaded_data_package.get("file_dropdown_map", {})
        file_display_names = loaded_data_package.get("file_display_names", [])
        total_snippets = loaded_data_package.get("total_snippets_loaded", 0)
        load_errors = loaded_data_package.get("errors", [])
        if load_errors:
            error_summary = "; ".join([f"{path}: {msg}" for path, msg in load_errors])
            logger.warning(f"Some files had issues during loading: {error_summary}")

        self._safely_populate_file_selector(file_display_names)
        self.is_modified = False
        self._update_window_title()
        self._update_status(
            f"{C.MSG_LOADED_SNIPPETS_COUNT.format(snippet_count=total_snippets, file_count=len(file_display_names))}",
            5000,
        )
        logger.info(f"Data loaded. Active file: {self.active_file_path or 'None'}")

    def _safely_populate_file_selector(self, file_display_names: List[str]):
        current_selection_text = self.file_selector.currentText()
        self.file_selector.blockSignals(True)
        self.file_selector.clear()
        if file_display_names:
            self.file_selector.addItems(file_display_names)
            if current_selection_text and current_selection_text in file_display_names:
                self.file_selector.setCurrentText(current_selection_text)
            elif self.file_selector.count() > 0:
                self.file_selector.setCurrentIndex(0)
        self.file_selector.blockSignals(False)
        if self.file_selector.count() > 0:
            self._on_file_selected(self.file_selector.currentIndex())
        else:
            self.active_file_path = None
            self._display_snippets_for_file(None)

    @pyqtSlot(int)
    def _on_file_selected(self, index: int):
        if index < 0 or not self.file_dropdown_map or self.file_selector.count() == 0:
            self.active_file_path = None
            self._display_snippets_for_file(None)
            return
        selected_display_name = self.file_selector.itemText(index)
        new_active_file_path = self.file_dropdown_map.get(selected_display_name)
        # Only log if path actually changes to avoid spam on refresh with same file selected
        if new_active_file_path != self.active_file_path:
            logger.info(
                f"File selected: {selected_display_name} (Path: {new_active_file_path})"
            )
        self.active_file_path = new_active_file_path
        self._display_snippets_for_file(self.active_file_path)

    def _display_snippets_for_file(self, file_path: Optional[str]):
        self.snippet_table.blockSignals(True)
        self.snippet_table.setRowCount(0)
        if file_path and file_path in self.current_data:
            snippets_to_display = self.current_data[file_path]
            for snippet in snippets_to_display:
                self._add_snippet_to_table_display(snippet)
            self._update_status(
                f"Displaying: {os.path.basename(file_path)} ({len(snippets_to_display)} snippets)",
                3000,
            )
        elif file_path:
            logger.warning(
                f"Attempted to display '{file_path}' but not in current_data."
            )
            self._update_status(f"No snippets for {os.path.basename(file_path)}.", 3000)
        else:
            self._update_status("No file selected.", 3000)
        self.snippet_table.blockSignals(False)
        self._ensure_empty_bottom_row()

    def _new_file(self):
        if not self.espanso_match_dir:
            QMessageBox.warning(self, "Error", "Espanso match directory not set.")
            return
        dialog = NewFileDialog(self, self.espanso_match_dir)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result:
            intended_original_path = dialog.result["file_path"]
            display_name_with_ext = dialog.result["display_name"]
            display_name_no_ext = os.path.splitext(display_name_with_ext)[0]
            self.current_data[intended_original_path] = []
            self.file_dropdown_map[display_name_no_ext] = intended_original_path
            self._safely_populate_file_selector(list(self.file_dropdown_map.keys()))
            self.file_selector.setCurrentText(display_name_no_ext)
            self.is_modified = True
            self._update_window_title()
            self._update_status(
                f"New file '{display_name_with_ext}' added. Save to backup.", 3000
            )
        if dialog:
            dialog.deleteLater()

    def _delete_category(self):
        if not self.active_file_path:
            QMessageBox.warning(self, "Error", C.MSG_NO_FILE_SELECTED)
            return
        file_display_name_for_msg = os.path.basename(self.active_file_path)
        reply = UIHelpers.create_confirmation_dialog(
            self,
            C.MSG_CONFIRM_DELETE_FILE_TITLE,
            C.MSG_CONFIRM_DELETE_FILE_TEXT.format(filename=file_display_name_for_msg),
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._perform_category_deletion(
                self.active_file_path, file_display_name_for_msg
            )

    def _perform_category_deletion(
        self, original_file_path_to_delete: str, display_name_of_deleted: str
    ):
        logger.info(f"Marking for deletion: {original_file_path_to_delete}")
        if original_file_path_to_delete in self.current_data:
            del self.current_data[original_file_path_to_delete]
        key_to_delete_from_map = None
        for name, path_in_map in self.file_dropdown_map.items():
            if path_in_map == original_file_path_to_delete:
                key_to_delete_from_map = name
                break
        if key_to_delete_from_map and key_to_delete_from_map in self.file_dropdown_map:
            del self.file_dropdown_map[key_to_delete_from_map]
        self.is_modified = True
        self._update_window_title()
        remaining_file_display_names = list(self.file_dropdown_map.keys())
        self._safely_populate_file_selector(remaining_file_display_names)
        msg = f"File '{display_name_of_deleted}' removed from working set."
        if not remaining_file_display_names:
            msg += " No files remaining."
        self._update_status(msg, 3000)
        logger.info(
            f"Category '{display_name_of_deleted}' removed. Changes apply to temp-ez on save."
        )

    def _open_espanso_hub(self):
        try:
            webbrowser.open(C.URL_ESPANSO_HUB)
        except Exception as e:
            logger.error(f"Could not open Espanso Hub URL: {e}", exc_info=True)
            QMessageBox.warning(
                self, "Error", f"Could not open URL: {C.URL_ESPANSO_HUB}"
            )

    def _show_about_dialog(self):
        QMessageBox.about(
            self,
            "About EZpanso",
            "EZpanso - Espanso Configuration Manager\nVersion 0.3 (Temp Save Update)\n\n"
            "Manage Espanso snippets. Changes are backed up to 'temp-ez'.",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle("Fusion")
    main_window = EZpanso()
    main_window.show()
    sys.exit(app.exec())
