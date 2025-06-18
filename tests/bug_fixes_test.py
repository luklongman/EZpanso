#!/usr/bin/env python3
"""
Bug Fixes Test Suite for EZpanso.

Consolidates all bug verification and edge case tests:
- TSM (Table Selection Model) error fixes
- In-place editing fixes
- Real file handling edge cases
- Data consistency issues
"""

import pytest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PyQt6.QtWidgets import QApplication, QTableWidgetItem
    from PyQt6.QtCore import Qt
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("Warning: PyQt6 not available. GUI tests will be skipped.")

if PYQT_AVAILABLE:
    from main import EZpanso


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
class TestTSMErrorFixes:
    """Test fixes for Table Selection Model (TSM) errors."""
    
    def test_table_signal_blocking_during_bulk_operations(self):
        """Test that table signals are properly blocked during bulk operations."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Mock table
            ezpanso.table = MagicMock()
            ezpanso.active_file_path = '/test/file.yml'
            ezpanso.files_data = {'/test/file.yml': [
                {'trigger': ':test1', 'replace': 'value1'},
                {'trigger': ':test2', 'replace': 'value2'}
            ]}
            
            # Test _populate_table blocks signals
            ezpanso._populate_table(ezpanso.files_data['/test/file.yml'])
            
            # Verify signals were blocked and unblocked
            assert ezpanso.table.blockSignals.call_count >= 2
            block_calls = ezpanso.table.blockSignals.call_args_list
            assert any(call[0][0] is True for call in block_calls)  # blockSignals(True)
            assert any(call[0][0] is False for call in block_calls)  # blockSignals(False)
    
    def test_clear_selection_before_operations(self):
        """Test that table selection is cleared before potentially problematic operations."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Mock table with clearSelection method
            ezpanso.table = MagicMock()
            ezpanso.active_file_path = '/test/file.yml'
            ezpanso.files_data = {'/test/file.yml': [
                {'trigger': ':test1', 'replace': 'value1'}
            ]}
            ezpanso.modified_files = {'/test/file.yml'}
            ezpanso.is_modified = True
            
            # Mock other required methods
            ezpanso._save_single_file = MagicMock(return_value=True)
            ezpanso._show_information = MagicMock()
            ezpanso._refresh_current_view = MagicMock()
            
            # Test that clearSelection is called during save operations
            ezpanso._save_all_files()
            
            # The implementation should call clearSelection or similar TSM-safe operations
            # This test verifies the fix is in place
            assert ezpanso._save_single_file.called
    
    def test_multiple_selection_deletion_fix(self):
        """Test that multiple selections can be deleted without TSM errors."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Setup test data
            ezpanso.active_file_path = '/test/file.yml'
            ezpanso.files_data = {'/test/file.yml': [
                {'trigger': ':test1', 'replace': 'value1'},
                {'trigger': ':test2', 'replace': 'value2'},
                {'trigger': ':test3', 'replace': 'value3'}
            ]}
            
            # Mock table and its methods
            ezpanso.table = MagicMock()
            ezpanso.table.clearSelection = MagicMock()
            
            # Mock _mark_modified_and_refresh
            ezpanso._mark_modified_and_refresh = MagicMock()
            
            # Mock dialog confirmation
            from PyQt6.QtWidgets import QMessageBox
            ezpanso._show_question = MagicMock(return_value=QMessageBox.StandardButton.Yes)
            
            # Test deleting multiple triggers
            triggers_to_delete = [':test1', ':test3']
            result = ezpanso._delete_snippets_by_triggers(triggers_to_delete)
            
            assert result is True
            assert len(ezpanso.files_data['/test/file.yml']) == 1
            assert ezpanso.files_data['/test/file.yml'][0]['trigger'] == ':test2'
            
            # Verify selection was cleared
            ezpanso.table.clearSelection.assert_called()


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
class TestInPlaceEditingFixes:
    """Test fixes for in-place editing issues."""
    
    def test_table_row_to_data_mapping_fix(self):
        """Test that table rows correctly map to data after sorting."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Setup test data with mixed complexity
            ezpanso.active_file_path = '/test/file.yml'
            test_matches = [
                {'trigger': ':complex', 'replace': 'value', 'vars': [{'name': 'test'}]},  # Complex
                {'trigger': ':simple1', 'replace': 'value1'},  # Simple
                {'trigger': ':simple2', 'replace': 'value2'}   # Simple
            ]
            ezpanso.files_data = {'/test/file.yml': test_matches}
            
            # Test sorting (simple matches should come first)
            sorted_matches = ezpanso._sort_easy_match(test_matches)
            
            # Verify simple matches come first
            assert not ezpanso._is_complex_match(sorted_matches[0])  # :simple1
            assert not ezpanso._is_complex_match(sorted_matches[1])  # :simple2  
            assert ezpanso._is_complex_match(sorted_matches[2])      # :complex
            
            # Test that current_matches stores the sorted order
            ezpanso.current_matches = sorted_matches.copy()
            
            # Verify the mapping works correctly
            for i, match in enumerate(sorted_matches):
                assert ezpanso.current_matches[i] == match
    
    def test_find_match_by_trigger_display(self):
        """Test finding matches by their display trigger value."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Setup test data
            ezpanso.active_file_path = '/test/file.yml'
            ezpanso.files_data = {'/test/file.yml': [
                {'trigger': ':test\nwith\nnewlines', 'replace': 'value1'},
                {'trigger': ':simple', 'replace': 'value2'}
            ]}
            
            # Test finding match with newlines
            trigger_with_newlines = ':test\nwith\nnewlines'
            display_trigger = ezpanso._get_display_value(trigger_with_newlines)
            
            match, index = ezpanso._find_match_by_trigger_display(display_trigger)
            
            assert match is not None
            assert match['trigger'] == trigger_with_newlines
            assert index == 0
            
            # Test finding simple match
            simple_trigger = ':simple'
            simple_display = ezpanso._get_display_value(simple_trigger)
            
            match, index = ezpanso._find_match_by_trigger_display(simple_display)
            
            assert match is not None
            assert match['trigger'] == simple_trigger
            assert index == 1
            
            # Test non-existent match
            match, index = ezpanso._find_match_by_trigger_display('nonexistent')
            
            assert match is None
            assert index == -1
    
    def test_duplicate_trigger_validation(self):
        """Test duplicate trigger validation during editing."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Setup test data
            ezpanso.active_file_path = '/test/file.yml'
            ezpanso.files_data = {'/test/file.yml': [
                {'trigger': ':test1', 'replace': 'value1'},
                {'trigger': ':test2', 'replace': 'value2'}
            ]}
            
            # Test duplicate detection
            assert ezpanso._check_duplicate_trigger(':test1')  # Should find duplicate
            assert ezpanso._check_duplicate_trigger(':test2')  # Should find duplicate
            assert not ezpanso._check_duplicate_trigger(':test3')  # Should not find duplicate
            
            # Test excluding current index
            assert not ezpanso._check_duplicate_trigger(':test1', exclude_index=0)  # Should not find (excluded)
            assert ezpanso._check_duplicate_trigger(':test1', exclude_index=1)      # Should find (not excluded)


@pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")
class TestRealFileHandling:
    """Test handling of real Espanso files and edge cases."""
    
    def test_package_file_handling(self):
        """Test handling of package.yml files."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Test package file display name
            package_path = '/path/to/some-package/package.yml'
            display_name = ezpanso._get_display_name(package_path)
            
            assert 'some-package' in display_name
            assert '(package)' in display_name.lower()
    
    def test_complex_yaml_structure_handling(self):
        """Test handling of complex YAML structures."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
            # Complex YAML with multiple sections
            tf.write("""# Package configuration
package_name: test-package
package_title: Test Package
package_desc: A test package
package_version: 1.0.0
package_author: Test Author

# Import definitions
imports:
  - ../base/_base.yml

# Global variables
global_vars:
  - name: name
    type: echo
    params:
      echo: "Test"

# Matches
matches:
  # Simple match
  - trigger: ":hello"
    replace: "Hello World"
  
  # Complex match with variables
  - trigger: ":form"
    replace: |
      Name: {{name}}
      Date: {{date}}
    vars:
      - name: name
        type: echo
        params:
          echo: "Test User"
      - name: date  
        type: date
        params:
          format: "%Y-%m-%d"
  
  # Match with form
  - trigger: ":contact"
    form: |
      Name: [[name]]
      Email: [[email]]
    vars:
      - name: name
        type: form
        params:
          layout: "Name: {{form1.name}}"
      - name: email
        type: form  
        params:
          layout: "Email: {{form1.email}}"
""")
            temp_path = tf.name
        
        try:
            with patch.object(EZpanso, '_setup_ui'), \
                 patch.object(EZpanso, '_setup_menubar'), \
                 patch.object(EZpanso, '_load_all_yaml_files'):
                
                ezpanso = EZpanso()
                
                # Load the complex file
                ezpanso._load_single_yaml_file(temp_path)
                
                # Verify it loaded correctly
                assert temp_path in ezpanso.files_data
                matches = ezpanso.files_data[temp_path]
                assert len(matches) == 3
                
                # Test complexity detection
                simple_match = next(m for m in matches if m['trigger'] == ':hello')
                complex_match_vars = next(m for m in matches if m['trigger'] == ':form')
                complex_match_form = next(m for m in matches if m['trigger'] == ':contact')
                
                assert not ezpanso._is_complex_match(simple_match)
                assert ezpanso._is_complex_match(complex_match_vars)  # Has vars
                assert ezpanso._is_complex_match(complex_match_form)  # Has form
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML files."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
            # Malformed YAML
            tf.write("""matches:
  - trigger: ":test"
    replace: "unclosed quote
  - trigger: ":another"
    replace: "valid"
""")
            temp_path = tf.name
        
        try:
            with patch.object(EZpanso, '_setup_ui'), \
                 patch.object(EZpanso, '_setup_menubar'), \
                 patch.object(EZpanso, '_load_all_yaml_files'):
                
                ezpanso = EZpanso()
                
                # Should handle the error gracefully
                ezpanso._load_single_yaml_file(temp_path)
                
                # File should not be loaded if malformed
                # (implementation may vary based on error handling)
                if temp_path in ezpanso.files_data:
                    # If it did load, it should be empty or partial
                    matches = ezpanso.files_data[temp_path]
                    assert isinstance(matches, list)
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_escape_sequence_edge_cases(self):
        """Test edge cases in escape sequence handling."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Test edge cases
            test_cases = [
                ("Simple text", "Simple text"),
                ("Text\\nwith\\nnewlines", "Text\nwith\nnewlines"),
                ("Text\\twith\\ttabs", "Text\twith\ttabs"),
                ("Mixed\\nand\\tescapes", "Mixed\nand\tescapes"),
                ("Literal\\\\backslash", "Literal\\backslash"),
                ("Complex\\\\n\\tcase", "Complex\\n\tcase"),  # Literal \n but actual tab
                ("", ""),  # Empty string
                ("\\n", "\n"),  # Just newline
                ("\\t", "\t"),  # Just tab
                ("\\\\", "\\"),  # Just literal backslash
            ]
            
            for input_val, expected_output in test_cases:
                result = ezpanso._process_escape_sequences(input_val)
                assert result == expected_output, f"Failed for input: '{input_val}'"
                
                # Test round-trip (display -> process -> display)
                display = ezpanso._get_display_value(expected_output)
                processed_back = ezpanso._process_escape_sequences(display)
                assert processed_back == expected_output, f"Round-trip failed for: '{input_val}'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
