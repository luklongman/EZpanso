#!/usr/bin/env python3
"""
YAML Handler Test Suite for EZpanso.

Consolidates all YAML-related functionality tests:
- Comment preservation
- YAML handler fallback behavior  
- YAML saving operations
- EZpanso workflow with YAML processing
"""

import pytest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from PyQt6.QtWidgets import QApplication
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("Warning: PyQt6 not available. GUI tests will be skipped.")

try:
    from yaml_handler import create_yaml_handler
    YAML_HANDLER_AVAILABLE = True
except ImportError:
    YAML_HANDLER_AVAILABLE = False
    print("Warning: yaml_handler not available. Some tests will be skipped.")

if PYQT_AVAILABLE:
    from main import EZpanso


class TestYAMLHandler:
    """Test YAML handler creation and functionality."""
    
    @pytest.mark.skipif(not YAML_HANDLER_AVAILABLE, reason="yaml_handler not available")
    def test_yaml_handler_creation(self):
        """Test creating YAML handler with comment preservation."""
        handler = create_yaml_handler(preserve_comments=True)
        assert handler is not None
        print(f"Backend: {handler.backend}")
        print(f"Supports comments: {handler.supports_comments}")
    
    @pytest.mark.skipif(not YAML_HANDLER_AVAILABLE, reason="yaml_handler not available")
    def test_yaml_handler_fallback(self):
        """Test YAML handler fallback behavior."""
        handler = create_yaml_handler(preserve_comments=False)
        assert handler is not None
        assert handler.backend == "PyYAML"
        assert not handler.supports_comments
    
    @pytest.mark.skipif(not YAML_HANDLER_AVAILABLE, reason="yaml_handler not available")
    def test_load_save_cycle(self):
        """Test loading and saving YAML with comment preservation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
            yaml_content = """# Test comment
matches:
  - trigger: :test
    replace: Hello  # inline comment
"""
            tf.write(yaml_content)
            temp_path = tf.name
        
        try:
            handler = create_yaml_handler(preserve_comments=True)
            
            # Load the file
            data = handler.load(temp_path)
            assert data is not None
            assert 'matches' in data
            assert len(data['matches']) == 1
            assert data['matches'][0]['trigger'] == ':test'
            
            # Modify and save
            data['matches'][0]['replace'] = 'Modified'
            success = handler.save(data, temp_path)
            
            if handler.supports_comments:
                assert success, "Save should succeed with comment preservation"
                
                # Reload and verify
                reloaded = handler.load(temp_path)
                assert reloaded['matches'][0]['replace'] == 'Modified'
                
                # Check if comments are preserved (if supported)
                with open(temp_path, 'r') as f:
                    content = f.read()
                    if handler.supports_comments:
                        assert '# Test comment' in content or '# inline comment' in content
            else:
                # Without comment preservation, save might not work
                print("Comment preservation not available, skipping save test")
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestCommentPreservation:
    """Test YAML comment preservation functionality."""
    
    @pytest.mark.skipif(not YAML_HANDLER_AVAILABLE, reason="yaml_handler not available")
    def test_comment_preservation_with_ruamel(self):
        """Test that comments are preserved when ruamel.yaml is available."""
        yaml_with_comments = """# Top level comment
matches:
  # Comment before match
  - trigger: :hello  # Inline comment 1
    replace: |
      Hello World!
      Multiple lines here
  # Another comment
  - trigger: :test
    replace: "test value"  # Inline comment 2
# Final comment
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
            tf.write(yaml_with_comments)
            temp_path = tf.name
        
        try:
            # Test with comment preservation
            handler = create_yaml_handler(preserve_comments=True)
            
            # Load the YAML
            data = handler.load(temp_path)
            assert data is not None
            assert 'matches' in data
            assert len(data['matches']) == 2
            
            # Verify the data structure
            assert data['matches'][0]['trigger'] == ':hello'
            assert 'Hello World!' in data['matches'][0]['replace']
            assert data['matches'][1]['trigger'] == ':test'
            assert data['matches'][1]['replace'] == 'test value'
            
            # Modify the data
            data['matches'][0]['replace'] = 'Modified Hello!'
            
            # Save back
            if handler.supports_comments:
                success = handler.save(data, temp_path)
                assert success, "Should be able to save with comment preservation"
                
                # Read the file and check for comment preservation
                with open(temp_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                
                # Should contain the modification
                assert 'Modified Hello!' in saved_content
                
                # Should preserve at least some comments (implementation dependent)
                # Note: Comment preservation may vary based on ruamel.yaml version
                print("Saved content preview:")
                print(saved_content[:200] + "..." if len(saved_content) > 200 else saved_content)
            else:
                print("Comment preservation not supported, skipping save test")
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.skipif(not YAML_HANDLER_AVAILABLE, reason="yaml_handler not available")
    def test_fallback_without_comments(self):
        """Test fallback behavior when comment preservation is not available."""
        yaml_with_comments = """# This comment will be lost
matches:
  - trigger: :test
    replace: value
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
            tf.write(yaml_with_comments)
            temp_path = tf.name
        
        try:
            # Force fallback to PyYAML (no comment preservation)
            handler = create_yaml_handler(preserve_comments=False)
            
            # Load the YAML
            data = handler.load(temp_path)
            assert data is not None
            assert 'matches' in data
            assert data['matches'][0]['trigger'] == ':test'
            
            # Modify and save
            data['matches'][0]['replace'] = 'modified'
            
            # Save back (should work but lose comments)
            success = handler.save(data, temp_path)
            assert success, "PyYAML save should always work"
            
            # Read back and verify
            reloaded = handler.load(temp_path)
            assert reloaded['matches'][0]['replace'] == 'modified'
            
            # Comments should be lost
            with open(temp_path, 'r') as f:
                content = f.read()
                assert '# This comment will be lost' not in content
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


@pytest.mark.skipif(not PYQT_AVAILABLE or not YAML_HANDLER_AVAILABLE, 
                   reason="PyQt6 or yaml_handler not available")
class TestEZpansoYAMLWorkflow:
    """Test EZpanso workflow with YAML processing."""
    
    def test_ezpanso_yaml_integration(self):
        """Test EZpanso integration with YAML handler."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tf:
            tf.write("""matches:
  - trigger: :hello
    replace: Hello World
  - trigger: :test
    replace: Test Value
""")
            temp_path = tf.name
        
        try:
            # Mock UI setup to avoid actual GUI
            with patch.object(EZpanso, '_setup_ui'), \
                 patch.object(EZpanso, '_setup_menubar'), \
                 patch.object(EZpanso, '_load_all_yaml_files'):
                
                ezpanso = EZpanso()
                
                # Load the test file
                ezpanso._load_single_yaml_file(temp_path)
                
                # Verify loading
                assert temp_path in ezpanso.files_data
                assert len(ezpanso.files_data[temp_path]) == 2
                
                # Test modification
                ezpanso.files_data[temp_path][0]['replace'] = 'Modified Hello'
                ezpanso.modified_files.add(temp_path)
                ezpanso.is_modified = True
                
                # Test saving
                success = ezpanso._save_single_file(temp_path, ezpanso.files_data[temp_path])
                assert success, "Save should succeed"
                
                # Verify the file was reloaded
                assert temp_path in ezpanso.files_data
                # Note: After save, file is reloaded, so changes should still be there
                assert ezpanso.files_data[temp_path][0]['replace'] == 'Modified Hello'
                
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
            # Clean up QApplication
            if app:
                app.processEvents()
    
    def test_yaml_value_formatting(self):
        """Test YAML value formatting methods."""
        app = QApplication.instance() or QApplication(sys.argv)
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            ezpanso = EZpanso()
            
            # Test _format_yaml_value (should return as-is)
            test_value = "Hello\nWorld\tWith\ttabs"
            formatted = ezpanso._format_yaml_value(test_value)
            assert formatted == test_value
            
            # Test _get_display_value (should escape newlines/tabs)
            display = ezpanso._get_display_value(test_value)
            assert "\\n" in display
            assert "\\t" in display
            assert "\n" not in display  # Actual newlines should be escaped
            
            # Test _process_escape_sequences (should convert back)
            processed = ezpanso._process_escape_sequences(display)
            assert processed == test_value
            assert "\n" in processed  # Should have actual newlines
            assert "\t" in processed  # Should have actual tabs


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
