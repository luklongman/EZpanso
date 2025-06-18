#!/usr/bin/env python3
"""
Test script to verify that table is properly refreshed after file saving.
This script demonstrates the new functionality where the table state
is updated after saving files.
"""

import os
import tempfile
import sys
from unittest.mock import patch, MagicMock

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from main import EZpanso
from PyQt6.QtWidgets import QApplication


def test_save_and_refresh():
    """Test that saving files properly refreshes the table."""
    
    # Create a QApplication instance
    app = QApplication(sys.argv)
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
        tf.write("""
matches:
  - trigger: ":test"
    replace: "original value"
  - trigger: ":hello"
    replace: "world"
""")
        test_file_path = tf.name
    
    try:
        # Mock the UI setup to avoid actual GUI creation
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            # Create EZpanso instance
            ezpanso = EZpanso()
            
            # Mock the table to track refresh calls
            ezpanso.table = MagicMock()
            ezpanso.active_file_path = test_file_path
            
            # Load the test file
            ezpanso._load_single_yaml_file(test_file_path)
            
            # Verify the file was loaded
            assert test_file_path in ezpanso.files_data
            assert len(ezpanso.files_data[test_file_path]) == 2
            print("✓ File loaded successfully")
            
            # Modify the data
            ezpanso.files_data[test_file_path][0]['replace'] = "modified value"
            ezpanso.modified_files.add(test_file_path)
            ezpanso.is_modified = True
            
            # Mock the _populate_table method to track calls
            populate_table_calls = []
            original_populate_table = ezpanso._populate_table
            
            def mock_populate_table(matches):
                populate_table_calls.append(matches)
                return original_populate_table(matches)
            
            ezpanso._populate_table = mock_populate_table
            
            # Save the file
            print("Saving file...")
            ezpanso._save_all_files()
            
            # Verify that _populate_table was called (meaning table was refreshed)
            assert len(populate_table_calls) > 0, "Table should have been refreshed after saving"
            print("✓ Table was refreshed after saving")
            
            # Verify the file was actually saved and reloaded
            assert test_file_path not in ezpanso.modified_files
            assert not ezpanso.is_modified
            print("✓ File state correctly updated after saving")
            
            # Verify the data is still there after reloading
            assert test_file_path in ezpanso.files_data
            assert len(ezpanso.files_data[test_file_path]) == 2
            print("✓ Data preserved after save and reload")
            
            print("\n✅ All tests passed! Save and refresh functionality is working correctly.")
            
    finally:
        # Clean up
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
        app.quit()


if __name__ == '__main__':
    test_save_and_refresh()
