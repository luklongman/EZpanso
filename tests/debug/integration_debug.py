#!/usr/bin/env python3
"""
Integration Debug Utilities for EZpanso.

Consolidates GUI, file loading, and integration debug utilities.
"""

import sys
import os
import tempfile
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from PyQt6.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("Warning: PyQt6 not available. GUI debugging will be limited.")

if PYQT_AVAILABLE:
    try:
        from main import EZpanso
        MAIN_AVAILABLE = True
    except ImportError:
        MAIN_AVAILABLE = False
        print("Warning: main module not available.")
else:
    MAIN_AVAILABLE = False

def test_gui_initialization():
    """Test GUI component initialization."""
    if not PYQT_AVAILABLE or not MAIN_AVAILABLE:
        print("GUI testing not available")
        return
    
    print("=== GUI Initialization Test ===\n")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        # Mock the heavy operations
        with patch.object(EZpanso, '_load_all_yaml_files'):
            ezpanso = EZpanso()
            
            print(f"Window title: {ezpanso.windowTitle()}")
            print(f"Window size: {ezpanso.size().width()}x{ezpanso.size().height()}")
            print(f"Has table: {hasattr(ezpanso, 'table')}")
            print(f"Has file_selector: {hasattr(ezpanso, 'file_selector')}")
            print(f"Has filter_box: {hasattr(ezpanso, 'filter_box')}")
            print(f"YAML handler backend: {ezpanso.yaml_handler.backend}")
            print(f"YAML handler supports comments: {ezpanso.yaml_handler.supports_comments}")
            
    except Exception as e:
        print(f"GUI initialization failed: {e}")
    finally:
        if app:
            app.processEvents()

def test_file_loading_integration():
    """Test file loading and data structure integration."""
    if not PYQT_AVAILABLE or not MAIN_AVAILABLE:
        print("File loading integration testing not available")
        return
    
    print("\n=== File Loading Integration Test ===\n")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
        tf.write("""# Test file comment
matches:
  - trigger: ":test1"
    replace: "Test value 1"
  - trigger: ":test2"  
    replace: |
      Multi-line
      test value
  - trigger: ":complex"
    replace: "Complex value"
    vars:
      - name: test
        type: echo
        params:
          echo: "test"
""")
        temp_path = tf.name
    
    try:
        # Mock UI setup but test file loading
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Test loading the file
            print(f"Loading test file: {temp_path}")
            ezpanso._load_single_yaml_file(temp_path)
            
            # Check data structures
            print(f"File in files_data: {temp_path in ezpanso.files_data}")
            if temp_path in ezpanso.files_data:
                matches = ezpanso.files_data[temp_path]
                print(f"Number of matches loaded: {len(matches)}")
                
                for i, match in enumerate(matches):
                    trigger = match.get('trigger', 'NO_TRIGGER')
                    replace = match.get('replace', 'NO_REPLACE')
                    is_complex = ezpanso._is_complex_match(match)
                    
                    print(f"  Match {i}: '{trigger}' -> '{replace[:20]}{'...' if len(replace) > 20 else ''}'")
                    print(f"           Complex: {is_complex}")
                    
                    # Test display formatting
                    display_trigger = ezpanso._get_display_value(trigger)
                    display_replace = ezpanso._get_display_value(replace)
                    
                    if display_trigger != trigger:
                        print(f"           Display trigger: '{display_trigger}'")
                    if display_replace != replace:
                        print(f"           Display replace: '{display_replace[:30]}{'...' if len(display_replace) > 30 else ''}'")
                
                # Test sorting
                sorted_matches = ezpanso._sort_matches(matches)
                print(f"\nSorted order:")
                for i, match in enumerate(sorted_matches):
                    is_complex = ezpanso._is_complex_match(match)
                    print(f"  {i}: '{match.get('trigger', 'NO_TRIGGER')}' (complex: {is_complex})")
                
                # Test saving
                print(f"\nTesting save operation...")
                # Modify a value
                if matches:
                    original_replace = matches[0]['replace']
                    matches[0]['replace'] = 'Modified Test Value'
                    
                    success = ezpanso._save_single_file(temp_path, matches)
                    print(f"Save successful: {success}")
                    
                    if success:
                        # Check if file was reloaded
                        reloaded_matches = ezpanso.files_data.get(temp_path, [])
                        if reloaded_matches:
                            new_replace = reloaded_matches[0]['replace']
                            print(f"Value after save/reload: '{new_replace}'")
                            print(f"Modification preserved: {new_replace == 'Modified Test Value'}")
            
    except Exception as e:
        print(f"File loading integration test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        if app:
            app.processEvents()

def test_mock_integration():
    """Test integration with mocked components (for CI/testing)."""
    print("\n=== Mock Integration Test ===\n")
    
    if not MAIN_AVAILABLE:
        print("Main module not available for mock testing")
        return
    
    # This test can run even without PyQt6
    with patch('main.QApplication'), \
         patch('main.QMainWindow'), \
         patch.object(EZpanso, '_setup_ui'), \
         patch.object(EZpanso, '_setup_menubar'), \
         patch.object(EZpanso, '_load_all_yaml_files'):
        
        ezpanso = EZpanso()
        
        # Test data structures are initialized
        print(f"files_data initialized: {isinstance(ezpanso.files_data, dict)}")
        print(f"file_paths initialized: {isinstance(ezpanso.file_paths, list)}")
        print(f"display_name_to_path initialized: {isinstance(ezpanso.display_name_to_path, dict)}")
        print(f"current_matches initialized: {isinstance(ezpanso.current_matches, list)}")
        print(f"undo_stack initialized: {isinstance(ezpanso.undo_stack, list)}")
        print(f"redo_stack initialized: {isinstance(ezpanso.redo_stack, list)}")
        
        # Test helper methods work
        test_value = "Test\\nwith\\nescapes"
        formatted = ezpanso._format_yaml_value(test_value)
        display = ezpanso._get_display_value(test_value)
        processed = ezpanso._process_escape_sequences(test_value)
        
        print(f"Helper methods working:")
        print(f"  _format_yaml_value: {formatted == test_value}")
        print(f"  _get_display_value: {'\\\\n' in display}")
        print(f"  _process_escape_sequences: {'\\n' in processed}")
        
        # Test match complexity detection
        simple_match = {'trigger': ':test', 'replace': 'value'}
        complex_match = {'trigger': ':test', 'replace': 'value', 'vars': []}
        
        print(f"Complexity detection:")
        print(f"  Simple match detected as simple: {not ezpanso._is_complex_match(simple_match)}")
        print(f"  Complex match detected as complex: {ezpanso._is_complex_match(complex_match)}")

def debug_method_calls():
    """Debug method call patterns."""
    print("\n=== Method Call Debug ===\n")
    
    if not MAIN_AVAILABLE:
        print("Main module not available for method call debugging")
        return
    
    # Track method calls
    call_log = []
    
    def log_call(method_name):
        def decorator(func):
            def wrapper(*args, **kwargs):
                call_log.append(method_name)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    with patch('main.QApplication'), \
         patch('main.QMainWindow'), \
         patch.object(EZpanso, '_setup_ui', side_effect=lambda: call_log.append('_setup_ui')), \
         patch.object(EZpanso, '_setup_menubar', side_effect=lambda: call_log.append('_setup_menubar')), \
         patch.object(EZpanso, '_load_all_yaml_files', side_effect=lambda: call_log.append('_load_all_yaml_files')):
        
        print("Creating EZpanso instance...")
        ezpanso = EZpanso()
        
        print("Initialization call order:")
        for i, call in enumerate(call_log):
            print(f"  {i+1}. {call}")

if __name__ == '__main__':
    test_gui_initialization()
    test_file_loading_integration()
    test_mock_integration()
    debug_method_calls()
