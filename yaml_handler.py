"""
YAML Handler module for EZpanso with comment preservation support.

This module provides a unified interface for YAML operations that can use either:
- ruamel.yaml (preserves comments and formatting)
- PyYAML (faster, but loses comments)

The handler automatically falls back to PyYAML if ruamel.yaml is not available.
"""

from typing import Dict, Any, Optional
import io

# Try to import ruamel.yaml, fall back to PyYAML
try:
    from ruamel.yaml import YAML
    RUAMEL_AVAILABLE = True
except ImportError:
    RUAMEL_AVAILABLE = False

import yaml


class YAMLHandler:
    """
    Unified YAML handler that preserves comments when possible.
    
    Uses ruamel.yaml for comment preservation if available,
    otherwise falls back to PyYAML for compatibility.
    """
    
    def __init__(self, preserve_comments: bool = True):
        """
        Initialize the YAML handler.
        
        Args:
            preserve_comments: Whether to attempt comment preservation
        """
        self.preserve_comments = preserve_comments and RUAMEL_AVAILABLE
        
        if self.preserve_comments:
            self.ruamel_yaml = YAML()
            self.ruamel_yaml.preserve_quotes = True
            self.ruamel_yaml.map_indent = 2
            self.ruamel_yaml.sequence_indent = 4
            self.ruamel_yaml.sequence_dash_offset = 2
            # Maintain compatibility with Espanso's preferred formatting
            self.ruamel_yaml.default_style = None
            self.ruamel_yaml.allow_unicode = True
    
    def load(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load YAML from file with comment preservation if possible.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Parsed YAML data or None on error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if self.preserve_comments:
                    return self.ruamel_yaml.load(f)
                else:
                    return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading YAML file {file_path}: {e}")
            return None
    
    def save(self, data: Dict[str, Any], file_path: str) -> bool:
        """
        Save YAML to file with comment preservation if possible.
        
        Args:
            data: Data to save
            file_path: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if self.preserve_comments:
                    self.ruamel_yaml.dump(data, f)
                else:
                    yaml.dump(data, f, sort_keys=False, allow_unicode=True, default_style=None)
            return True
        except Exception as e:
            print(f"Error saving YAML file {file_path}: {e}")
            return False
    
    def load_from_string(self, yaml_string: str) -> Optional[Dict[str, Any]]:
        """
        Load YAML from string with comment preservation if possible.
        
        Args:
            yaml_string: YAML content as string
            
        Returns:
            Parsed YAML data or None on error
        """
        try:
            if self.preserve_comments:
                return self.ruamel_yaml.load(io.StringIO(yaml_string))
            else:
                return yaml.safe_load(yaml_string)
        except Exception as e:
            print(f"Error parsing YAML string: {e}")
            return None
    
    def dump_to_string(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Dump YAML to string with comment preservation if possible.
        
        Args:
            data: Data to dump
            
        Returns:
            YAML string or None on error
        """
        try:
            if self.preserve_comments:
                stream = io.StringIO()
                self.ruamel_yaml.dump(data, stream)
                return stream.getvalue()
            else:
                return yaml.dump(data, sort_keys=False, allow_unicode=True, default_style=None)
        except Exception as e:
            print(f"Error dumping YAML to string: {e}")
            return None
    
    @property
    def supports_comments(self) -> bool:
        """Check if comment preservation is supported."""
        return self.preserve_comments
    
    @property
    def backend(self) -> str:
        """Get the backend being used."""
        return "ruamel.yaml" if self.preserve_comments else "PyYAML"


def create_yaml_handler(preserve_comments: bool = True) -> YAMLHandler:
    """
    Factory function to create a YAML handler.
    
    Args:
        preserve_comments: Whether to attempt comment preservation
        
    Returns:
        Configured YAMLHandler instance
    """
    return YAMLHandler(preserve_comments=preserve_comments)
