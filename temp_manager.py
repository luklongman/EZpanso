# temp_manager.py
"""
Temporary file manager for EZpanso.
Handles temporary directories and files for backup operations.
"""
import os
import tempfile
import shutil
import logging
from typing import Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class TempManager:
    """Manages temporary directories and files for backup operations."""
    
    def __init__(self):
        self.temp_dir: Optional[str] = None
        self.cleanup_on_exit: bool = True
    
    def create_temp_backup_dir(self, match_folder_path: str) -> str:
        """
        Create a temporary backup directory inside the match folder.
        
        Args:
            match_folder_path: Path to the Espanso match folder
            
        Returns:
            Path to the created temporary directory
        """
        try:
            # Create temp-ez directory inside the match folder for consistency
            # but use proper temporary directory creation
            match_folder = Path(match_folder_path)
            temp_base_dir = match_folder / "temp-ez"
            
            # Ensure the base temp directory exists
            temp_base_dir.mkdir(exist_ok=True)
            
            # Create a unique temporary directory inside temp-ez
            self.temp_dir = tempfile.mkdtemp(
                prefix="backup_",
                suffix="_ezpanso",
                dir=str(temp_base_dir)
            )
            
            logger.info(f"Created temporary backup directory: {self.temp_dir}")
            return self.temp_dir
            
        except Exception as e:
            logger.error(f"Error creating temporary backup directory: {e}")
            # Fallback to system temp directory
            self.temp_dir = tempfile.mkdtemp(prefix="ezpanso_backup_")
            logger.info(f"Fallback: Created system temp directory: {self.temp_dir}")
            return self.temp_dir
    
    def get_temp_file_path(self, original_file_path: str) -> str:
        """
        Get the temporary file path for a given original file.
        
        Args:
            original_file_path: Path to the original file
            
        Returns:
            Path where the temporary backup should be saved
        """
        if not self.temp_dir:
            raise RuntimeError("Temporary directory not created. Call create_temp_backup_dir first.")
        
        filename = os.path.basename(original_file_path)
        return os.path.join(self.temp_dir, filename)
    
    def cleanup_temp_dir(self):
        """Clean up the temporary directory and all its contents."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
                self.temp_dir = None
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory {self.temp_dir}: {e}")
    
    def list_temp_files(self) -> List[str]:
        """List all files in the temporary directory."""
        if not self.temp_dir or not os.path.exists(self.temp_dir):
            return []
        
        try:
            return [
                os.path.join(self.temp_dir, f) 
                for f in os.listdir(self.temp_dir) 
                if os.path.isfile(os.path.join(self.temp_dir, f))
            ]
        except Exception as e:
            logger.error(f"Error listing temp files: {e}")
            return []
    
    def move_temp_files_to_original(self, file_mappings: List[tuple]) -> bool:
        """
        Move temporary files back to their original locations.
        
        Args:
            file_mappings: List of (temp_path, original_path) tuples
            
        Returns:
            True if all files were moved successfully, False otherwise
        """
        success = True
        for temp_path, original_path in file_mappings:
            try:
                if os.path.exists(temp_path):
                    # Ensure the target directory exists
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    
                    # Move the file
                    shutil.move(temp_path, original_path)
                    logger.info(f"Moved {temp_path} to {original_path}")
                else:
                    logger.warning(f"Temporary file not found: {temp_path}")
                    success = False
            except Exception as e:
                logger.error(f"Error moving {temp_path} to {original_path}: {e}")
                success = False
        
        return success
    
    def __del__(self):
        """Cleanup temporary directory on object destruction."""
        if self.cleanup_on_exit:
            self.cleanup_temp_dir()
