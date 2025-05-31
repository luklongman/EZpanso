# simplified_file_handler.py
"""
Simplified file handler for EZpanso.
Focuses on direct load/save without temporary file complexity.
"""
import os
import yaml
from typing import Dict, List, Any, Tuple, Optional
from simplified_data_model import Snippet
import constants as C


def load_espanso_data_simple(espanso_match_dir: str) -> Dict[str, Any]:
    """
    Load all Espanso snippets from YAML files.
    Returns a simple dictionary structure without complex mappings.
    """
    files_data: Dict[str, List[Snippet]] = {}
    file_dropdown_map: Dict[str, str] = {}
    errors: List[str] = []
    total_snippets = 0

    if not espanso_match_dir or not os.path.isdir(espanso_match_dir):
        return {
            "files_data": files_data,
            "file_dropdown_map": file_dropdown_map,
            "file_display_names": [],
            "total_snippets": total_snippets,
            "errors": ["Espanso directory not set or invalid."]
        }

    for root_dir, dirs, files in os.walk(espanso_match_dir):
        for filename in sorted(files):
            if not filename.endswith((".yml", ".yaml")):
                continue
                
            # Skip system files
            if filename in ['_manifest.yml', '_pkgsource.yml']:
                continue
                
            file_path = os.path.join(root_dir, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    yaml_content = yaml.safe_load(f) or {}
                
                matches = yaml_content.get(C.YAML_MATCHES_KEY, [])
                if not isinstance(matches, list):
                    errors.append(f"Invalid matches format in {filename}")
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
                    files_data[file_path] = snippets
                    
                    # Create display name
                    if filename == 'package.yml':
                        display_name = os.path.basename(os.path.dirname(file_path))
                    else:
                        display_name = os.path.splitext(filename)[0]
                        
                    file_dropdown_map[display_name] = file_path
                    total_snippets += len(snippets)
                    
            except Exception as e:
                errors.append(f"Error loading {filename}: {str(e)}")
    
    return {
        "files_data": files_data,
        "file_dropdown_map": file_dropdown_map,
        "file_display_names": sorted(file_dropdown_map.keys()),
        "total_snippets": total_snippets,
        "errors": errors
    }


def save_file_simple(file_path: str, snippets: List[Snippet]) -> Tuple[bool, Optional[str]]:
    """
    Save snippets directly to the original file.
    No temporary files - simple overwrite.
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Load existing file to preserve other keys
        file_content = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = yaml.safe_load(f) or {}
            except Exception:
                # If can't read existing file, start fresh
                pass

        # Update matches section
        matches_data = [snippet.original_yaml_entry for snippet in snippets]
        file_content[C.YAML_MATCHES_KEY] = matches_data

        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(file_content, f, 
                     sort_keys=False, 
                     allow_unicode=True, 
                     default_flow_style=False)
        
        return True, None
        
    except Exception as e:
        return False, str(e)


def create_new_file_simple(file_path: str) -> Tuple[bool, Optional[str]]:
    """Create a new YAML file with basic structure."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        template_data = {
            C.YAML_MATCHES_KEY: []
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(template_data, f, sort_keys=False)
            
        return True, None
        
    except Exception as e:
        return False, str(e)
