# ui_dialogs.py
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import Optional, Dict, Tuple
import os
from data_model import Snippet # Assuming Snippet class is in data_model.py
import constants as C


class EditSnippetDialog(simpledialog.Dialog):
    """Dialog for *editing* an existing snippet."""
    def __init__(self, parent, title: str, existing_snippet: Snippet):
        self.snippet_data: Snippet = existing_snippet
        self.result: Optional[Dict[str, str]] = None
        super().__init__(parent, title)

    def body(self, master: tk.Frame) -> ttk.Entry:
        ttk.Label(master, text="Trigger:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.trigger_entry = ttk.Entry(master, width=50)
        self.trigger_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.trigger_entry.insert(0, self.snippet_data.trigger)

        ttk.Label(master, text="Replace:").grid(row=1, column=0, sticky="nw", padx=5, pady=2)
        self.replace_text_widget = tk.Text(master, width=50, height=10, wrap=tk.WORD)
        self.replace_text_widget.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.replace_text_widget.insert(tk.END, self.snippet_data.replace_text)

        master.grid_columnconfigure(1, weight=1)
        return self.trigger_entry  # Initial focus

    def apply(self) -> None:
        trigger: str = self.trigger_entry.get().strip()
        replace: str = self.replace_text_widget.get("1.0", tk.END).strip()

        if not trigger:
            messagebox.showerror("Error", C.ERROR_TRIGGER_EMPTY, parent=self)
            self.result = None # Indicate failure
            # Ensure dialog does not close by overriding buttonbox, or by this causing an error
            # that simpledialog handles by not closing. Here, setting result to None works.
            return

        self.result = {C.COL_TRIGGER: trigger, C.COL_REPLACE: replace}


class NewCategoryDialog(simpledialog.Dialog):
    """Dialog for creating a new Espanso YAML file (category)."""
    def __init__(self, parent, title: str, espanso_match_dir: str):
        self.espanso_match_dir: str = espanso_match_dir
        self.result: Optional[Dict[str, str]] = None
        super().__init__(parent, title)

    def body(self, master: tk.Frame) -> ttk.Entry:
        ttk.Label(master, text="New Category Name (e.g., 'my_work_snippets'):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = ttk.Entry(master, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        master.grid_columnconfigure(1, weight=1)
        return self.name_entry

    def _validate_filename(self, name: str) -> Tuple[bool, str]:
        if not name:
            return False, C.ERROR_CATEGORY_NAME_EMPTY
        if any(c in name for c in r'/\:*?"<>|'): # Common invalid filename chars
            return False, C.ERROR_CATEGORY_NAME_INVALID_CHARS
        if name.endswith((".yml", ".yaml")):
            return False, C.ERROR_CATEGORY_NO_EXTENSION
        return True, ""

    def apply(self) -> None:
        raw_name: str = self.name_entry.get().strip()
        is_valid, error_msg = self._validate_filename(raw_name)

        if not is_valid:
            messagebox.showerror("Invalid Category Name", error_msg, parent=self)
            self.result = None
            return

        filename: str = f"{raw_name}.yml"
        file_path: str = os.path.join(self.espanso_match_dir, filename)

        if os.path.exists(file_path):
            messagebox.showerror("Error", C.ERROR_CATEGORY_FILE_EXISTS.format(filename), parent=self)
            self.result = None
            return

        self.result = {"file_path": file_path, "display_name": filename}