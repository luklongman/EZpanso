# simplified_data_model.py
"""
Simplified data model for EZpanso focusing on core functionality.
Removes unnecessary tracking flags and complexity.
"""
from typing import Dict, Any
from constants import COL_TRIGGER, COL_REPLACE


class Snippet:
    """Simplified snippet representation."""
    
    def __init__(self, trigger: str, replace_text: str, file_path: str,
                 original_yaml_entry: Dict[str, Any] = None):
        self.trigger = str(trigger)
        self.replace_text = str(replace_text) 
        self.file_path = file_path
        
        # Preserve original YAML structure for saving
        if original_yaml_entry is None:
            self.original_yaml_entry = {
                COL_TRIGGER: self.trigger,
                COL_REPLACE: self.replace_text
            }
        else:
            self.original_yaml_entry = original_yaml_entry.copy()
            # Ensure trigger and replace are up to date
            self.original_yaml_entry[COL_TRIGGER] = self.trigger
            self.original_yaml_entry[COL_REPLACE] = self.replace_text
    
    def __repr__(self) -> str:
        return f"Snippet(trigger='{self.trigger}', file='{self.file_path}')"
