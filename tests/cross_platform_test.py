#!/usr/bin/env python3
"""
Cross-platform bug diagnosis tests for EZpanso.

This module tests the specific issues reported by Windows 11 and Linux Mint users:
1. "Can add new matches but not save edits to existing matches"
2. "Replacements can be edited, no problem. Trigger can be edited, but not saved"
3. "No changes to save" popup when changes were made
4. "Strangely, if I revert my change on a trigger manually, then a change is detected"

These tests focus on the modification tracking system and cross-platform differences.
"""

import pytest
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

# Import the class to test (adjust path since we're in tests/ subdirectory)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import EZpanso


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_settings():
    """Mock QSettings for testing."""
    with patch('main.QSettings') as mock:
        mock_instance = Mock()
        mock_instance.value.return_value = ""
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_os_path():
    """Mock os.path methods for testing."""
    with patch('main.os.path.isdir', return_value=True), \
         patch('main.os.path.exists', return_value=True), \
         patch('main.os.path.expanduser', return_value="/mock/home"):
        yield


class TestCrossPlatformModificationTracking:
    """Test cases specifically for cross-platform modification tracking bugs."""
    
    def test_trigger_edit_modification_tracking(self, qapp, mock_settings, mock_os_path):
        """Test that editing triggers properly marks files as modified."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_show_warning'), \
             patch.object(EZpanso, '_save_state'):
            
            window = EZpanso()
            
            # Set up test data
            test_file_path = '/test/file.yml'
            window.active_file_path = test_file_path
            window.files_data = {
                test_file_path: [
                    {'trigger': ':test', 'replace': 'test value'},
                    {'trigger': ':hello', 'replace': 'Hello World'}
                ]
            }
            window.modified_files = set()
            window.is_modified = False
            
            # Create table and populate it
            window.table = Mock()
            window.table.item = Mock()
            
            # Simulate editing a trigger - create a mock table item
            mock_item = Mock(spec=QTableWidgetItem)
            mock_item.row.return_value = 0
            mock_item.column.return_value = 0  # Trigger column
            mock_item.text.return_value = ':new_trigger'
            
            # Mock the trigger item lookup
            mock_trigger_item = Mock(spec=QTableWidgetItem)
            mock_trigger_item.text.return_value = ':test'  # Original trigger
            window.table.item.return_value = mock_trigger_item
            
            # Call the method that should detect changes
            window._on_item_changed(mock_item)
            
            # Verify modification tracking worked
            assert window.is_modified, "File should be marked as modified after trigger edit"
            assert test_file_path in window.modified_files, "File path should be in modified files set"
            
            # Verify the trigger was actually updated in the data
            updated_match = window.files_data[test_file_path][0]
            assert updated_match['trigger'] == ':new_trigger', "Trigger should be updated in data structure"
    
    def test_replace_edit_modification_tracking(self, qapp, mock_settings, mock_os_path):
        """Test that editing replacements properly marks files as modified."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_save_state') as mock_save_state:
            
            window = EZpanso()
            
            # Set up test data
            test_file_path = '/test/file.yml'
            window.active_file_path = test_file_path
            window.files_data = {
                test_file_path: [
                    {'trigger': ':test', 'replace': 'old value'},
                ]
            }
            window.modified_files = set()
            window.is_modified = False
            
            # Create table and populate it
            window.table = Mock()
            window.table.item = Mock()
            
            # Simulate editing a replacement - create a mock table item
            mock_item = Mock(spec=QTableWidgetItem)
            mock_item.row.return_value = 0
            mock_item.column.return_value = 1  # Replace column
            mock_item.text.return_value = 'new value'
            
            # Mock the trigger item lookup
            mock_trigger_item = Mock(spec=QTableWidgetItem)
            mock_trigger_item.text.return_value = ':test'
            window.table.item.return_value = mock_trigger_item
            
            # Call the method that should detect changes
            window._on_item_changed(mock_item)
            
            # Verify modification tracking worked
            assert window.is_modified == True, "File should be marked as modified after replace edit"
            assert test_file_path in window.modified_files, "File path should be in modified files set"
            
            # Verify the replacement was actually updated in the data
            updated_match = window.files_data[test_file_path][0]
            assert updated_match['replace'] == 'new value', "Replace should be updated in data structure"
    
    def test_comparison_logic_cross_platform(self, qapp, mock_settings, mock_os_path):
        """Test the comparison logic that might be causing cross-platform issues."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test various string comparison scenarios that might differ across platforms
            test_cases = [
                # (stored_value, display_value, new_input, should_detect_change)
                (':test', ':test', ':test', False),  # No change
                (':test', ':test', ':new', True),    # Clear change
                ('test', 'test', 'test', False),     # No quotes, no change
                ("'test'", 'test', 'test', False),   # Quoted vs unquoted, no change
                ('"test"', 'test', 'test', False),   # Double quoted vs unquoted, no change
                ('test\n', 'test\\n', 'test\\n', False),  # Newline handling, no change
                ('test\n', 'test\\n', 'new\\n', True),    # Newline handling, with change
                ('test\t', 'test\\t', 'test\\t', False),  # Tab handling, no change
                ('', '', 'new', True),               # Empty to non-empty
                ('old', 'old', '', True),            # Non-empty to empty
            ]
            
            for stored_value, display_value, new_input, should_detect_change in test_cases:
                # Set up test data
                test_file_path = '/test/file.yml'
                window.active_file_path = test_file_path
                window.files_data = {
                    test_file_path: [
                        {'trigger': stored_value, 'replace': 'test replace'},
                    ]
                }
                window.modified_files = set()
                window.is_modified = False
                
                # Test the comparison logic directly
                old_value = stored_value
                compare_value = window._get_display_value(str(old_value))
                
                # Verify our test assumptions about display value conversion
                if display_value != compare_value:
                    print(f"Display value mismatch: expected '{display_value}', got '{compare_value}'")
                
                # Test if change detection works correctly
                change_detected = (compare_value != new_input)
                
                if change_detected != should_detect_change:
                    pytest.fail(
                        f"Change detection failed for case: stored='{stored_value}', "
                        f"display='{display_value}', input='{new_input}'. "
                        f"Expected change detection: {should_detect_change}, "
                        f"Got: {change_detected}"
                    )
    
    def test_escape_sequence_handling_cross_platform(self, qapp, mock_settings, mock_os_path):
        """Test escape sequence handling that might differ across platforms."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test escape sequence processing
            test_cases = [
                ('\\n', '\n'),    # Newline escape
                ('\\t', '\t'),    # Tab escape
                ('\\\\', '\\'),   # Literal backslash
                ('test\\nline', 'test\nline'),  # Mixed content
                ('no escapes', 'no escapes'),  # No escapes
            ]
            
            for input_str, expected_output in test_cases:
                result = window._process_escape_sequences(input_str)
                assert result == expected_output, f"Escape processing failed: '{input_str}' -> '{result}', expected '{expected_output}'"
    
    def test_display_value_conversion_cross_platform(self, qapp, mock_settings, mock_os_path):
        """Test display value conversion that might cause cross-platform issues."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test display value conversion (actual to display)
            test_cases = [
                ('\n', '\\n'),    # Newline to display
                ('\t', '\\t'),    # Tab to display
                ('normal', 'normal'),  # No conversion needed
                ('test\nline', 'test\\nline'),  # Mixed content
                ('', ''),  # Empty string
            ]
            
            for actual_value, expected_display in test_cases:
                result = window._get_display_value(actual_value)
                assert result == expected_display, f"Display conversion failed: '{actual_value}' -> '{result}', expected '{expected_display}'"
    
    def test_revert_change_detection_bug(self, qapp, mock_settings, mock_os_path):
        """Test the specific bug where reverting a change then making it again works."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_save_state') as mock_save_state:
            
            window = EZpanso()
            
            # Set up test data
            test_file_path = '/test/file.yml'
            window.active_file_path = test_file_path
            original_trigger = ':original'
            window.files_data = {
                test_file_path: [
                    {'trigger': original_trigger, 'replace': 'test value'},
                ]
            }
            window.modified_files = set()
            window.is_modified = False
            
            # Create mocks
            window.table = Mock()
            window.table.item = Mock()
            
            # Step 1: Make an edit (change trigger)
            mock_item = Mock(spec=QTableWidgetItem)
            mock_item.row.return_value = 0
            mock_item.column.return_value = 0  # Trigger column
            mock_item.text.return_value = ':changed'
            
            mock_trigger_item = Mock(spec=QTableWidgetItem)
            mock_trigger_item.text.return_value = original_trigger
            window.table.item.return_value = mock_trigger_item
            
            window._on_item_changed(mock_item)
            
            # Verify change was detected
            assert window.is_modified == True, "First edit should be detected"
            assert test_file_path in window.modified_files
            
            # Step 2: Revert the change (change back to original)
            window.modified_files = set()  # Reset for clean test
            window.is_modified = False
            
            mock_item.text.return_value = original_trigger  # Revert to original
            mock_trigger_item.text.return_value = ':changed'  # Current state is changed
            
            window._on_item_changed(mock_item)
            
            # This should also be detected as a change
            assert window.is_modified == True, "Revert should also be detected as a change"
            assert test_file_path in window.modified_files
    
    def test_modification_tracking_edge_cases(self, qapp, mock_settings, mock_os_path):
        """Test edge cases in modification tracking."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test case 1: No active file
            mock_item = Mock(spec=QTableWidgetItem)
            mock_item.row.return_value = 0
            mock_item.column.return_value = 0
            mock_item.text.return_value = ':test'
            
            window.active_file_path = None
            window._on_item_changed(mock_item)  # Should not crash
            
            # Test case 2: No table item
            window.active_file_path = '/test/file.yml'
            window.table = Mock()
            window.table.item.return_value = None
            
            window._on_item_changed(mock_item)  # Should not crash
            
            # Test case 3: Match not found
            window.files_data = {'/test/file.yml': []}
            mock_trigger_item = Mock()
            mock_trigger_item.text.return_value = ':nonexistent'
            window.table.item.return_value = mock_trigger_item
            
            window._on_item_changed(mock_item)  # Should not crash


class TestCrossPlatformSaveOperations:
    """Test save operations across platforms."""
    
    def test_save_with_modifications_detected(self, qapp, mock_settings, mock_os_path):
        """Test that save operations work when modifications are properly detected."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_show_information') as mock_info:
            
            window = EZpanso()
            
            # Set up modified state
            test_file_path = '/test/file.yml'
            window.active_file_path = test_file_path
            window.files_data = {
                test_file_path: [{'trigger': ':test', 'replace': 'value'}]
            }
            window.modified_files = {test_file_path}
            window.is_modified = True
            
            # Mock the actual save operation
            with patch.object(window, '_save_single_file', return_value=True) as mock_save:
                window._save_all_files()
                
                # Verify save was attempted
                mock_save.assert_called_once_with(test_file_path, [{'trigger': ':test', 'replace': 'value'}])
                
                # Verify state was cleared after successful save
                assert not window.is_modified, "is_modified should be False after successful save"
                assert len(window.modified_files) == 0, "modified_files should be empty after successful save"
    
    def test_save_with_no_modifications(self, qapp, mock_settings, mock_os_path):
        """Test that save operations correctly handle no modifications."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_show_information') as mock_info:
            
            window = EZpanso()
            
            # Set up unmodified state
            test_file_path = '/test/file.yml'
            window.active_file_path = test_file_path
            window.files_data = {
                test_file_path: [{'trigger': ':test', 'replace': 'value'}]
            }
            window.modified_files = set()  # No modifications
            window.is_modified = False
            
            # Mock the actual save operation
            with patch.object(window, '_save_single_file') as mock_save:
                window._save_all_files()
                
                # Verify save was NOT attempted
                mock_save.assert_not_called()
                
                # Verify no information dialog was shown
                mock_info.assert_not_called()


def run_cross_platform_diagnostics():
    """Run diagnostic tests and print results."""
    print("Running cross-platform diagnostic tests...")
    
    # Run the tests and collect results
    pytest_args = [
        __file__,
        '-v',
        '--tb=short',
        '-x'  # Stop on first failure for easier debugging
    ]
    
    result = pytest.main(pytest_args)
    
    if result == 0:
        print("✅ All diagnostic tests passed!")
    else:
        print("❌ Some diagnostic tests failed. Check output above.")
    
    return result


if __name__ == "__main__":
    # Allow running diagnostics directly
    run_cross_platform_diagnostics()
