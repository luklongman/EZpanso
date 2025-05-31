# data_model.py
from typing import Dict, Any, Tuple, Optional, List
from constants import COL_TRIGGER, COL_REPLACE

class Snippet:
    """Represents a single Espanso snippet."""
    def __init__(self, trigger: str, replace_text: str, file_path: str,
                 original_yaml_entry: Optional[Dict[str, Any]] = None):
        self.trigger: str = str(trigger) if trigger is not None else ""
        self.replace_text: str = str(replace_text) if replace_text is not None else ""
        self.file_path: str = file_path  # Full path to the YML file

        if original_yaml_entry is None:
            self.original_yaml_entry: Dict[str, Any] = {
                COL_TRIGGER: self.trigger,
                COL_REPLACE: self.replace_text
            }
        else:
            self.original_yaml_entry: Dict[str, Any] = original_yaml_entry
            # Ensure main keys are strings, preserving other potential data types in original_yaml_entry
            self.original_yaml_entry[COL_TRIGGER] = str(self.original_yaml_entry.get(COL_TRIGGER, ''))
            self.original_yaml_entry[COL_REPLACE] = str(self.original_yaml_entry.get(COL_REPLACE, ''))


        self.tree_item_iid_str: Optional[str] = None  # String version of unique ID for Treeview
        self.is_new: bool = False
        self.is_modified: bool = False

    def get_display_values_for_tree(self) -> Tuple[str, str]:
        """Values to display in the Treeview columns for this snippet."""
        lines: List[str] = self.replace_text.splitlines()
        first_line_replace: str = lines[0] if lines else ""
        if len(lines) > 1:
            first_line_replace += "..."
        return self.trigger, first_line_replace

    def mark_modified(self, new_trigger: str, new_replace_text: str) -> bool:
        """Updates snippet and marks as modified if changes occurred.
        Updates the original_yaml_entry to reflect changes.
        """
        new_trigger = str(new_trigger)
        new_replace_text = str(new_replace_text)

        if self.trigger != new_trigger or self.replace_text != new_replace_text:
            self.trigger = new_trigger
            self.replace_text = new_replace_text
            
            # Update the dictionary that will be used for saving
            self.original_yaml_entry[COL_TRIGGER] = new_trigger
            self.original_yaml_entry[COL_REPLACE] = new_replace_text
            
            if not self.is_new: # Don't mark as modified if it's already new
                self.is_modified = True
            return True
        return False

    def __repr__(self) -> str:
        return f"Snippet(trigger='{self.trigger}', file_path='{self.file_path}')"