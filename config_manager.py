# config_manager.py
"""
Configuration manager for EZpanso.
Handles persistent user preferences like match folder path.
"""
import os
import configparser
import platform
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages user configuration and preferences."""
    
    def __init__(self):
        self.config_file_path = self._get_config_file_path()
        self.config = configparser.ConfigParser()
        self._load_config()
    
    def _get_config_file_path(self) -> str:
        """Get the platform-appropriate config file path."""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            config_dir = os.path.expanduser("~/Library/Preferences")
            return os.path.join(config_dir, "com.ezpanso.config")
        elif system == "Windows":
            config_dir = os.path.expanduser("~/AppData/Local/EZpanso")
            os.makedirs(config_dir, exist_ok=True)
            return os.path.join(config_dir, "config.ini")
        else:  # Linux and others
            config_dir = os.path.expanduser("~/.config/ezpanso")
            os.makedirs(config_dir, exist_ok=True)
            return os.path.join(config_dir, "config.ini")
    
    def _load_config(self):
        """Load configuration from file."""
        if os.path.exists(self.config_file_path):
            try:
                self.config.read(self.config_file_path)
                logger.info(f"Loaded configuration from {self.config_file_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                # Create default sections
                self._create_default_sections()
        else:
            self._create_default_sections()
    
    def _create_default_sections(self):
        """Create default configuration sections."""
        if 'GENERAL' not in self.config:
            self.config.add_section('GENERAL')
        if 'PATHS' not in self.config:
            self.config.add_section('PATHS')
        if 'UI' not in self.config:
            self.config.add_section('UI')
    
    def save_config(self):
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            
            with open(self.config_file_path, 'w') as config_file:
                self.config.write(config_file)
            logger.info(f"Configuration saved to {self.config_file_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_match_folder_path(self) -> Optional[str]:
        """Get the saved match folder path."""
        return self.config.get('PATHS', 'match_folder', fallback=None)
    
    def set_match_folder_path(self, path: str):
        """Set the match folder path."""
        self.config.set('PATHS', 'match_folder', path)
        self.save_config()
    
    def get_window_geometry(self) -> Optional[str]:
        """Get saved window geometry."""
        return self.config.get('UI', 'window_geometry', fallback=None)
    
    def set_window_geometry(self, geometry: str):
        """Set window geometry."""
        self.config.set('UI', 'window_geometry', geometry)
        self.save_config()
    
    def get_last_selected_file(self) -> Optional[str]:
        """Get the last selected file."""
        return self.config.get('GENERAL', 'last_selected_file', fallback=None)
    
    def set_last_selected_file(self, file_path: str):
        """Set the last selected file."""
        self.config.set('GENERAL', 'last_selected_file', file_path)
        self.save_config()
    
    def get_auto_save(self) -> bool:
        """Get auto-save preference."""
        return self.config.getboolean('GENERAL', 'auto_save', fallback=True)
    
    def set_auto_save(self, enabled: bool):
        """Set auto-save preference."""
        self.config.set('GENERAL', 'auto_save', str(enabled))
        self.save_config()
