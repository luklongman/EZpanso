# file_handler.py
import os
import platform
import yaml
from typing import Dict, List, Any, Tuple, Optional

from data_model import Snippet
import constants as C

# Setup a more robust YAML dumper to handle unicode and block style
class SafeDumperUnicode(yaml.SafeDumper):
    def represent_scalar(self, tag, value, style=None):
        if isinstance(value, str):
            # Use block style for multiline strings if no explicit style given
            if '\n' in value and style is None:
                style = '|'
            return super().represent_scalar(tag, value, style=style)
        return super().represent_scalar(tag, value, style)

SafeDumperUnicode.add_representer(
    str,
    lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|' if '\n' in data else None)
)


def get_default_espanso_config_path() -> Optional[str]:
    """Determines the default Espanso match directory based on OS."""
    system: str = platform.system()
    path_template: Optional[str] = C.DEFAULT_ESPANSO_PATHS.get(system)

    if system == "Linux":
        xdg_config_home: Optional[str] = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            return os.path.join(xdg_config_home, "espanso/match")
    
    if path_template:
        return os.path.expanduser(path_template)
    return None


def load_espanso_data(espanso_match_dir: str) -> Dict[str, Any]:
    """
    Loads all Espanso snippets from YAML files in the given directory,
    excluding any subdirectories named C.TEMP_EZ_FOLDER_NAME.

    Returns:
        A dictionary containing:
        - 'snippets_by_file': Dict[str, List[Snippet]]
        - 'file_dropdown_map': Dict[str, str] (display_name -> file_path)
        - 'file_display_names': List[str]
        - 'total_snippets_loaded': int
        - 'errors': List[Tuple[str, str]] (file_path, error_message)
    """
    snippets_by_file: Dict[str, List[Snippet]] = {}
    file_dropdown_map: Dict[str, str] = {}
    file_display_names: List[str] = []
    errors: List[Tuple[str, str]] = []
    total_snippets_loaded = 0

    if not espanso_match_dir or not os.path.isdir(espanso_match_dir):
        errors.append(("", "Espanso directory not set or invalid."))
        return {
            "snippets_by_file": snippets_by_file,
            "file_dropdown_map": file_dropdown_map,
            "file_display_names": file_display_names,
            "total_snippets_loaded": total_snippets_loaded,
            "errors": errors,
        }

    for root_dir, dirs, files in os.walk(espanso_match_dir):
        # Exclude the temp-ez directory from being processed
        if C.TEMP_EZ_FOLDER_NAME in dirs:
            dirs.remove(C.TEMP_EZ_FOLDER_NAME)
            
        for filename in sorted(files):
            # Skip manifest and package source files
            if filename in ['_manifest.yml', '_pkgsource.yml']:
                continue
                
            if filename.endswith((".yml", ".yaml")):
                file_path: str = os.path.join(root_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        yaml_content = yaml.safe_load(f) or {}
                    
                    # Process the matches in the YAML file
                    matches = yaml_content.get(C.YAML_MATCHES_KEY, [])
                    if not isinstance(matches, list):
                        errors.append((file_path, f"Invalid matches format in {filename}"))
                        continue

                    snippets = []
                    for match in matches:
                        if not isinstance(match, dict):
                            continue
                        trigger = match.get(C.COL_TRIGGER)
                        replace = match.get(C.COL_REPLACE)
                        if trigger is not None and replace is not None:
                            snippet = Snippet(trigger, replace, file_path, match)
                            snippets.append(snippet)
                    
                    if snippets:
                        # For package.yml files, use the parent folder name as the file name
                        if filename == 'package.yml':
                            file_name = os.path.basename(os.path.dirname(file_path))
                        else:
                            file_name = os.path.splitext(filename)[0]
                            
                        snippets_by_file[file_path] = snippets
                        file_dropdown_map[file_name] = file_path
                        file_display_names.append(file_name)
                        total_snippets_loaded += len(snippets)
                except Exception as e:
                    errors.append((file_path, f"Error loading {filename}: {str(e)}"))
    
    return {
        "snippets_by_file": snippets_by_file,
        "file_dropdown_map": file_dropdown_map,
        "file_display_names": sorted(file_display_names),
        "total_snippets_loaded": total_snippets_loaded,
        "errors": errors,
    }


def save_espanso_file(file_path: str, snippets_list: List[Snippet]) -> Tuple[bool, Optional[str]]:
    """Saves a single Espanso YAML file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Preserve other top-level keys in the YAML file if it exists
        file_content_to_write: Dict[str, Any] = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f_read:
                    existing_content = yaml.safe_load(f_read)
                    if isinstance(existing_content, dict):
                        file_content_to_write = existing_content
            except Exception: # If reading fails, start fresh but warn or log
                # For now, we'll overwrite with a clean structure if read fails.
                # A more robust solution might backup the old file.
                pass # `file_content_to_write` remains empty or its last state

        # Prepare the list of matches from snippet.original_yaml_entry
        # This ensures any extra fields in each snippet's definition are preserved
        matches_yaml_list: List[Dict[str, Any]] = [s.original_yaml_entry for s in snippets_list]
        file_content_to_write[C.YAML_MATCHES_KEY] = matches_yaml_list

        # Ensure 'matches' key exists even if empty, for consistency
        if C.YAML_MATCHES_KEY not in file_content_to_write:
            file_content_to_write[C.YAML_MATCHES_KEY] = []


        with open(file_path, 'w', encoding='utf-8') as f_write:
            yaml.dump(file_content_to_write, f_write, Dumper=SafeDumperUnicode,
                      sort_keys=False, allow_unicode=True, default_flow_style=False)
        return True, None
    except Exception as e:
        return False, f"Error saving {os.path.basename(file_path)}: {e}"

def create_empty_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """Creates a new, empty Espanso YAML file with a template match."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            template_data = {
                C.YAML_MATCHES_KEY: [
                    {
                        "trigger": ":test",
                        "replace": "result"
                    }
                ]
            }
            yaml.dump(template_data, f, Dumper=SafeDumperUnicode, sort_keys=False)
        return True, None
    except Exception as e:
        return False, f"Could not create file {os.path.basename(file_path)}: {e}"

def delete_file(file_path: str) -> Tuple[bool, Optional[str]]:
    """Deletes a YAML file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True, None
    except Exception as e:
        return False, f"Could not delete file {os.path.basename(file_path)}: {e}"