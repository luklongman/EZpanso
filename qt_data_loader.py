"""
Helper module for loading and saving Espanso data in the Qt application.
"""
import os
from typing import Dict, List, Any
from PyQt6.QtCore import QObject, pyqtSignal, QRunnable
from data_model import Snippet
from file_handler import load_espanso_data, save_espanso_file

class DataLoaderSignals(QObject):
    """Signals for the data loader thread."""
    # Emits data package and an optional error string
    data_loaded = pyqtSignal(dict, object) # dict for data, object for error string (or None)

class DataLoader(QRunnable):
    """Worker thread for loading Espanso data."""
    def __init__(self, directory_path: str):
        super().__init__()
        self.directory_path = directory_path
        self.signals = DataLoaderSignals()

    def run(self):
        try:
            data_package = load_espanso_data(self.directory_path)
            error_list = data_package.get("errors", [])
            error_str = None
            if error_list:
                # Consolidate errors into a single string
                error_str = "; ".join([f"{path if path else 'General'} - {msg}" for path, msg in error_list])
            
            self.signals.data_loaded.emit(data_package, error_str)

        except Exception as e:
            # For unexpected errors during the load_espanso_data call itself or signal emission
            self.signals.data_loaded.emit({}, str(e))


class DataSaverSignals(QObject):
    """Signals for the data saver thread."""
    # Emits list of successfully saved temp file paths
    save_complete = pyqtSignal(list) 
    # Emits error message string if saving fails
    save_error = pyqtSignal(str)

class DataSaver(QRunnable):
    """Worker thread for saving Espanso data. Handles a list of files."""
    # Takes a list of packages, where each package has "path" and "snippets"
    def __init__(self, files_to_save_pkg: List[Dict[str, Any]]):
        super().__init__()
        self.files_to_save_pkg = files_to_save_pkg
        self.signals = DataSaverSignals()

    def run(self):
        saved_paths = []
        has_errors = False
        error_message_to_emit = ""

        for file_pkg in self.files_to_save_pkg:
            file_path = file_pkg["path"]
            snippets: List[Snippet] = file_pkg["snippets"] 
            try:
                success, error_msg = save_espanso_file(file_path, snippets)
                if success:
                    saved_paths.append(file_path)
                else:
                    has_errors = True
                    error_message_to_emit = error_msg or f"Unknown error saving {os.path.basename(file_path)}"
                    break # Stop on first error
            except Exception as e:
                has_errors = True
                error_message_to_emit = str(e)
                break # Stop on first error
        
        if has_errors:
            self.signals.save_error.emit(error_message_to_emit)
        else:
            # Only emit save_complete if no errors occurred for any file
            self.signals.save_complete.emit(saved_paths)
