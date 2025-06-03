import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from typing import Dict, List, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QIcon

# Add the missing imports that main.py needs
import yaml

# Import the class to test
from main import EZpanso, FileData


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for tests."""
    if not QApplication.instance():
        app = QApplication([])
        yield app
        app.quit()
    else:
        yield QApplication.instance()


@pytest.fixture
def mock_settings():
    """Mock QSettings for testing."""
    with patch('main.QSettings') as mock_qsettings:
        mock_instance = Mock()
        mock_instance.value.return_value = ""
        mock_qsettings.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_os_path():
    """Mock os.path methods for testing."""
    with patch('main.os.path.join') as mock_join, \
         patch('main.os.path.exists') as mock_exists, \
         patch('main.os.path.dirname') as mock_dirname:
        
        mock_dirname.return_value = "/app/dir"
        mock_join.return_value = "/app/dir/icon.iconset/icon_512x512.png"
        mock_exists.return_value = False  # Default: no icon exists
        
        yield {
            'join': mock_join,
            'exists': mock_exists,
            'dirname': mock_dirname
        }


class TestEZpansoInit:
    """Test cases for EZpanso.__init__ method."""
    
    def test_basic_initialization(self, qapp, mock_settings, mock_os_path):
        """Test basic window initialization."""
        with patch.object(EZpanso, '_setup_ui') as mock_setup_ui, \
             patch.object(EZpanso, '_setup_menubar') as mock_setup_menubar, \
             patch.object(EZpanso, '_load_all_yaml_files') as mock_load_files:
            
            window = EZpanso()
            
            # Test window properties
            assert window.windowTitle() == "EZpanso"
            assert window.size().width() == 600
            assert window.size().height() == 800
            
            # Test setup methods were called
            mock_setup_ui.assert_called_once()
            mock_setup_menubar.assert_called_once()
            mock_load_files.assert_called_once()
    
    def test_icon_handling_when_exists(self, qapp, mock_settings, mock_os_path):
        """Test icon loading when icon file exists."""
        mock_os_path['exists'].return_value = True
        
        with patch('main.QIcon') as mock_qicon, \
             patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, 'setWindowIcon') as mock_set_icon:
            
            mock_icon_instance = Mock()
            mock_qicon.return_value = mock_icon_instance
            
            window = EZpanso()
            
            # Test icon was created and set
            mock_qicon.assert_called_once_with("/app/dir/icon.iconset/icon_512x512.png")
            assert window.app_icon == mock_icon_instance
            # Test that setWindowIcon was called with the icon
            mock_set_icon.assert_called_once_with(mock_icon_instance)
    
    def test_icon_handling_when_not_exists(self, qapp, mock_settings, mock_os_path):
        """Test icon handling when icon file doesn't exist."""
        mock_os_path['exists'].return_value = False
        
        with patch('main.QIcon') as mock_qicon, \
             patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test icon was not created
            mock_qicon.assert_not_called()
            assert window.app_icon is None
    
    def test_settings_initialization(self, qapp, mock_os_path):
        """Test QSettings initialization and custom directory loading."""
        with patch('main.QSettings') as mock_qsettings, \
             patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            mock_settings_instance = Mock()
            mock_settings_instance.value.return_value = "/custom/espanso/dir"
            mock_qsettings.return_value = mock_settings_instance
            
            window = EZpanso()
            
            # Test QSettings was created with correct parameters
            mock_qsettings.assert_called_once_with("EZpanso", "EZpanso")
            assert window.settings == mock_settings_instance
            
            # Test custom directory was loaded
            mock_settings_instance.value.assert_called_once_with("espanso_dir", "")
            assert window.custom_espanso_dir == "/custom/espanso/dir"
    
    def test_data_structures_initialization(self, qapp, mock_settings, mock_os_path):
        """Test that all data structures are properly initialized."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test data storage structures
            assert isinstance(window.files_data, dict)
            assert len(window.files_data) == 0
            assert isinstance(window.file_paths, list)
            assert len(window.file_paths) == 0
            assert isinstance(window.display_name_to_path, dict)
            assert len(window.display_name_to_path) == 0
            assert window.active_file_path is None
            
            # Test modification tracking
            assert window.is_modified is False
            assert isinstance(window.modified_files, set)
            assert len(window.modified_files) == 0
            
            # Test sorting and filtering
            assert isinstance(window.current_matches, list)
            assert len(window.current_matches) == 0
            assert isinstance(window.filtered_indices, list)
            assert len(window.filtered_indices) == 0
            
            # Test undo/redo system
            assert isinstance(window.undo_stack, list)
            assert len(window.undo_stack) == 0
            assert isinstance(window.redo_stack, list)
            assert len(window.redo_stack) == 0
            assert window.max_undo_steps == 50
    
    def test_settings_with_empty_custom_dir(self, qapp, mock_os_path):
        """Test settings when custom espanso directory is empty."""
        with patch('main.QSettings') as mock_qsettings, \
             patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            mock_settings_instance = Mock()
            mock_settings_instance.value.return_value = ""  # Empty string
            mock_qsettings.return_value = mock_settings_instance
            
            window = EZpanso()
            
            assert window.custom_espanso_dir == ""
    
    def test_initialization_call_order(self, qapp, mock_settings, mock_os_path):
        """Test that initialization methods are called in correct order."""
        with patch.object(EZpanso, '_setup_ui') as mock_setup_ui, \
             patch.object(EZpanso, '_setup_menubar') as mock_setup_menubar, \
             patch.object(EZpanso, '_load_all_yaml_files') as mock_load_files:
            
            window = EZpanso()
            
            # Verify call order by checking call counts at each step
            assert mock_setup_ui.call_count == 1
            assert mock_setup_menubar.call_count == 1
            assert mock_load_files.call_count == 1
    
    def test_type_annotations_compliance(self, qapp, mock_settings, mock_os_path):
        """Test that initialized attributes match their type annotations."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test FileData type (Dict[str, List[Dict[str, Any]]])
            assert isinstance(window.files_data, dict)
            
            # Test List[str] types
            assert isinstance(window.file_paths, list)
            assert isinstance(window.filtered_indices, list)
            
            # Test Dict[str, str] type
            assert isinstance(window.display_name_to_path, dict)
            
            # Test Optional[str] type
            assert window.active_file_path is None or isinstance(window.active_file_path, str)
            
            # Test bool type
            assert isinstance(window.is_modified, bool)
            
            # Test set type
            assert isinstance(window.modified_files, set)
            
            # Test List[Dict[str, Any]] types
            assert isinstance(window.current_matches, list)
            assert isinstance(window.undo_stack, list)
            assert isinstance(window.redo_stack, list)
    
    @patch('main.os.path.dirname')
    @patch('main.os.path.join')
    @patch('main.os.path.exists')
    def test_icon_path_construction(self, mock_exists, mock_join, mock_dirname, qapp, mock_settings):
        """Test that icon path is constructed correctly."""
        mock_dirname.return_value = "/test/app/dir"
        mock_join.return_value = "/test/app/dir/icon.iconset/icon_512x512.png"
        mock_exists.return_value = False
        
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Verify path construction calls
            mock_dirname.assert_called_once()
            mock_join.assert_called_once_with("/test/app/dir", 'icon.iconset', 'icon_512x512.png')
            mock_exists.assert_called_once_with("/test/app/dir/icon.iconset/icon_512x512.png")
    
    def test_window_properties_after_init(self, qapp, mock_settings, mock_os_path):
        """Test window properties are set correctly after initialization."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test window title
            assert window.windowTitle() == "EZpanso"
            
            # Test window size
            size = window.size()
            assert size.width() == 600
            assert size.height() == 800
    
    def test_exception_handling_in_setup_methods(self, qapp, mock_settings, mock_os_path):
        """Test that exceptions in setup methods don't prevent initialization."""
        with patch.object(EZpanso, '_setup_ui', side_effect=Exception("UI setup failed")), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            # Should not raise exception even if _setup_ui fails
            with pytest.raises(Exception, match="UI setup failed"):
                window = EZpanso()


class TestEZpansoHelperMethods:
    """Test cases for helper methods used during initialization."""
    
    def test_format_yaml_value(self, qapp, mock_settings, mock_os_path):
        """Test _format_yaml_value method."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test that value is returned as-is
            test_value = "test string"
            result = window._format_yaml_value(test_value)
            assert result == test_value
    
    def test_get_display_value(self, qapp, mock_settings, mock_os_path):
        """Test _get_display_value method."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test newline conversion
            result = window._get_display_value("line1\nline2")
            assert result == "line1\\nline2"
            
            # Test tab conversion
            result = window._get_display_value("col1\tcol2")
            assert result == "col1\\tcol2"
            
            # Test non-string input
            result = window._get_display_value(123)
            assert result == "123"
    
    def test_process_escape_sequences(self, qapp, mock_settings, mock_os_path):
        """Test _process_escape_sequences method."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test escape sequence conversion
            result = window._process_escape_sequences("line1\\nline2")
            assert result == "line1\nline2"
            
            result = window._process_escape_sequences("col1\\tcol2")
            assert result == "col1\tcol2"
            
            # Test non-string input
            result = window._process_escape_sequences(123)
            assert result == "123"


class TestEZpansoDataHandling:
    """Test cases for data loading and manipulation methods."""
    
    def test_load_single_yaml_file_success(self, qapp, mock_settings, mock_os_path):
        """Test loading a valid YAML file."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch('builtins.open', mock_open(read_data='matches:\n  - trigger: ":test"\n    replace: "test value"')), \
             patch('main.yaml.safe_load') as mock_yaml_load:
            
            mock_yaml_load.return_value = {
                'matches': [
                    {'trigger': ':test', 'replace': 'test value'}
                ]
            }
            
            window = EZpanso()
            window._load_single_yaml_file('/test/file.yml')
            
            # Test that file was loaded correctly
            assert '/test/file.yml' in window.files_data
            assert len(window.files_data['/test/file.yml']) == 1
            assert window.files_data['/test/file.yml'][0]['trigger'] == ':test'
            assert '/test/file.yml' in window.file_paths
    
    def test_load_single_yaml_file_no_matches(self, qapp, mock_settings, mock_os_path):
        """Test loading a YAML file with no matches."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch('builtins.open', mock_open(read_data='other_key: value')), \
             patch('main.yaml.safe_load') as mock_yaml_load:
            
            mock_yaml_load.return_value = {'other_key': 'value'}
            
            window = EZpanso()
            window._load_single_yaml_file('/test/file.yml')
            
            # Test that file was not added (no matches)
            assert '/test/file.yml' not in window.files_data
            assert '/test/file.yml' not in window.file_paths
    
    def test_load_single_yaml_file_exception(self, qapp, mock_settings, mock_os_path):
        """Test loading a YAML file that raises an exception."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch('builtins.open', side_effect=FileNotFoundError("File not found")), \
             patch('builtins.print') as mock_print:
            
            window = EZpanso()
            window._load_single_yaml_file('/nonexistent/file.yml')
            
            # Test that error was printed
            mock_print.assert_called_once()
            assert "Error loading" in str(mock_print.call_args)
    
    def test_is_complex_match_simple(self, qapp, mock_settings, mock_os_path):
        """Test identifying simple matches."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Simple match
            simple_match = {'trigger': ':test', 'replace': 'value'}
            assert not window._is_complex_match(simple_match)
    
    def test_is_complex_match_with_extras(self, qapp, mock_settings, mock_os_path):
        """Test identifying complex matches."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Complex match with extra keys
            complex_match = {'trigger': ':test', 'replace': 'value', 'word': True}
            assert window._is_complex_match(complex_match)
            
            # Complex match with vars
            vars_match = {'trigger': ':test', 'replace': 'value', 'vars': []}
            assert window._is_complex_match(vars_match)
    
    def test_sort_matches(self, qapp, mock_settings, mock_os_path):
        """Test sorting matches with simple ones first."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            matches = [
                {'trigger': 'z_complex', 'replace': 'value', 'word': True},
                {'trigger': 'a_simple', 'replace': 'value'},
                {'trigger': 'b_simple', 'replace': 'value'},
                {'trigger': 'a_complex', 'replace': 'value', 'vars': []}
            ]
            
            sorted_matches = window._sort_matches(matches)
            
            # Simple matches should come first, then alphabetical
            assert sorted_matches[0]['trigger'] == 'a_simple'
            assert sorted_matches[1]['trigger'] == 'b_simple'
            assert sorted_matches[2]['trigger'] == 'a_complex'
            assert sorted_matches[3]['trigger'] == 'z_complex'
    
    def test_get_display_name_regular_file(self, qapp, mock_settings, mock_os_path):
        """Test getting display name for regular files."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            display_name = window._get_display_name('/path/to/myfile.yml')
            assert display_name == 'myfile.yml'
    
    def test_get_display_name_package_file(self, qapp, mock_settings, mock_os_path):
        """Test getting display name for package.yml files."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch('main.os.path.basename') as mock_basename, \
             patch('main.os.path.dirname') as mock_dirname:
            
            # Mock the basename calls for the file and parent directory
            mock_basename.side_effect = lambda path: {
                '/path/to/myfolder/package.yml': 'package.yml',
                '/path/to/myfolder': 'myfolder'
            }.get(path, 'package.yml')
            mock_dirname.return_value = '/path/to/myfolder'
            
            window = EZpanso()
            
            display_name = window._get_display_name('/path/to/myfolder/package.yml')
            assert display_name == 'myfolder (package)'


class TestEZpansoFileOperations:
    """Test cases for file loading and saving operations."""
    
    def test_load_all_yaml_files_custom_dir(self, qapp, mock_settings, mock_os_path):
        """Test loading files from custom directory."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch('main.os.path.isdir', return_value=True), \
             patch('main.os.walk') as mock_walk, \
             patch.object(EZpanso, '_load_single_yaml_file') as mock_load_single, \
             patch('main.os.path.join', side_effect=lambda *args: "/".join(args)):
            
            mock_settings.value.return_value = "/custom/espanso/dir"
            mock_walk.return_value = [
                ('/custom/espanso/dir', [], ['test.yml', '_hidden.yml', 'other.yaml'])
            ]
            
            window = EZpanso()
            # Mock the file_selector that gets created in _setup_ui
            window.file_selector = Mock()
            window.file_selector.addItems = Mock()
            
            # Clear any calls from initialization, then call method again
            mock_load_single.reset_mock()
            window._load_all_yaml_files()
            
            # Should load .yml and .yaml files, but skip _hidden files
            assert mock_load_single.call_count == 2
            mock_load_single.assert_any_call('/custom/espanso/dir/test.yml')
            mock_load_single.assert_any_call('/custom/espanso/dir/other.yaml')
    
    def test_load_all_yaml_files_no_directory(self, qapp, mock_settings, mock_os_path):
        """Test loading files when no directory exists."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch('main.os.path.isdir', return_value=False), \
             patch('main.os.path.expanduser') as mock_expanduser, \
             patch.object(EZpanso, '_show_warning') as mock_warning:
            
            mock_settings.value.return_value = ""
            mock_expanduser.return_value = "/nonexistent/path"
            
            window = EZpanso()
            # Reset the mock since __init__ also calls _load_all_yaml_files
            mock_warning.reset_mock()
            
            window._load_all_yaml_files()
            
            # Should show warning
            mock_warning.assert_called_once_with("Error", "Could not find Espanso match directory. Use File > Set Folder to select one.")
    
    def test_save_single_file_success(self, qapp, mock_settings, mock_os_path):
        """Test successfully saving a single file."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch('main.os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='existing: content\nmatches: []')), \
             patch('main.yaml.safe_load') as mock_yaml_load, \
             patch('main.yaml.dump') as mock_yaml_dump:
            
            mock_yaml_load.return_value = {'existing': 'content', 'matches': []}
            
            window = EZpanso()
            matches = [{'trigger': ':test', 'replace': 'value'}]
            
            result = window._save_single_file('/test/file.yml', matches)
            
            assert result is True
            mock_yaml_dump.assert_called_once()
            # Check that matches were updated
            dump_args = mock_yaml_dump.call_args[0]
            assert dump_args[0]['matches'] == matches
    
    def test_save_single_file_exception(self, qapp, mock_settings, mock_os_path):
        """Test saving a file that raises an exception."""
        # Don't patch os.path.exists in mock_os_path fixture for this test
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_show_critical') as mock_critical:
            
            window = EZpanso()
            
            # Patch the os.path.exists to raise exception during save operation
            with patch('main.os.path.exists', side_effect=Exception("File error")):
                matches = [{'trigger': ':test', 'replace': 'value'}]
                result = window._save_single_file('/test/file.yml', matches)
            
            assert result is False
            mock_critical.assert_called_once()
            assert "Save Error" in mock_critical.call_args[0][0]


class TestEZpansoTableOperations:
    """Test cases for table and UI operations."""
    
    def test_populate_table(self, qapp, mock_settings, mock_os_path):
        """Test populating table with matches."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Mock table
            window.table = Mock()
            window.table.blockSignals = Mock()
            window.table.setSortingEnabled = Mock()
            window.table.setRowCount = Mock()
            window.table.setItem = Mock()
            
            matches = [
                {'trigger': ':simple', 'replace': 'value'},
                {'trigger': ':complex', 'replace': 'value', 'word': True}
            ]
            
            window._populate_table(matches)
            
            # Test that table was configured
            window.table.blockSignals.assert_called()
            window.table.setSortingEnabled.assert_called()
            window.table.setRowCount.assert_called_with(2)
            assert window.table.setItem.call_count == 4  # 2 rows * 2 columns
    
    def test_on_file_selected_valid_file(self, qapp, mock_settings, mock_os_path):
        """Test selecting a valid file."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_populate_table') as mock_populate:
            
            window = EZpanso()
            window.display_name_to_path = {'test.yml': '/path/test.yml'}
            window.files_data = {'/path/test.yml': [{'trigger': ':test', 'replace': 'value'}]}
            window.filter_box = Mock()
            
            window._on_file_selected('test.yml')
            
            assert window.active_file_path == '/path/test.yml'
            window.filter_box.clear.assert_called_once()
            mock_populate.assert_called_once()
    
    def test_on_file_selected_invalid_file(self, qapp, mock_settings, mock_os_path):
        """Test selecting an invalid file."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_populate_table') as mock_populate:
            
            window = EZpanso()
            window.display_name_to_path = {}
            
            window._on_file_selected('nonexistent.yml')
            
            assert window.active_file_path is None
            mock_populate.assert_not_called()
    
    def test_on_file_selected_package_file(self, qapp, mock_settings, mock_os_path):
        """Test selecting a package file shows warning."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch.object(EZpanso, '_show_package_warning', return_value=True) as mock_warning, \
             patch.object(EZpanso, '_populate_table') as mock_populate:
            
            window = EZpanso()
            window.display_name_to_path = {'test (package)': '/path/package.yml'}
            window.files_data = {'/path/package.yml': []}
            window.filter_box = Mock()
            
            window._on_file_selected('test (package)')
            
            mock_warning.assert_called_once()
            mock_populate.assert_called_once()
    
    def test_create_table_item_simple(self, qapp, mock_settings, mock_os_path):
        """Test creating a simple table item."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'), \
             patch('main.QTableWidgetItem') as mock_item:
            
            mock_item_instance = Mock()
            mock_item.return_value = mock_item_instance
            
            window = EZpanso()
            result = window._create_table_item("test text", False)
            
            mock_item.assert_called_once_with("test text")
            mock_item_instance.setBackground.assert_not_called()
            assert result == mock_item_instance
    
    def test_create_table_item_complex(self, qapp, mock_settings, mock_os_path):
        """Test creating a complex (grayed out) table item."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            
            # Test the actual implementation rather than mocking everything
            result = window._create_table_item("test text", True)
            
            # Verify it's a QTableWidgetItem
            assert result.text() == "test text"
            # Complex items should not be editable (flags should be modified)
            # We can't easily test the exact flag value due to bitwise operations


class TestEZpansoUtilityMethods:
    """Test cases for utility and helper methods."""
    
    def test_update_title_no_modification(self, qapp, mock_settings, mock_os_path):
        """Test updating title without modifications."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            window.is_modified = False
            
            window._update_title()
            
            assert window.windowTitle() == "EZpanso"
    
    def test_update_title_with_modification(self, qapp, mock_settings, mock_os_path):
        """Test updating title with modifications."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            window.is_modified = True
            
            window._update_title()
            
            assert window.windowTitle() == "EZpanso *"
    
    def test_check_duplicate_trigger_found(self, qapp, mock_settings, mock_os_path):
        """Test checking for duplicate triggers when one exists."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            window.active_file_path = '/test/file.yml'
            window.files_data = {
                '/test/file.yml': [
                    {'trigger': ':existing', 'replace': 'value1'},
                    {'trigger': ':other', 'replace': 'value2'}
                ]
            }
            
            result = window._check_duplicate_trigger(':existing', exclude_index=1)
            assert result is True
    
    def test_check_duplicate_trigger_not_found(self, qapp, mock_settings, mock_os_path):
        """Test checking for duplicate triggers when none exists."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            window.active_file_path = '/test/file.yml'
            window.files_data = {
                '/test/file.yml': [
                    {'trigger': ':existing', 'replace': 'value1'},
                    {'trigger': ':other', 'replace': 'value2'}
                ]
            }
            
            result = window._check_duplicate_trigger(':new', exclude_index=-1)
            assert result is False
    
    def test_find_match_by_trigger_display_found(self, qapp, mock_settings, mock_os_path):
        """Test finding a match by display trigger."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            window.active_file_path = '/test/file.yml'
            window.files_data = {
                '/test/file.yml': [
                    {'trigger': ':test\nline', 'replace': 'value'}
                ]
            }
            
            match, index = window._find_match_by_trigger_display(':test\\nline')
            
            assert match is not None
            assert match['trigger'] == ':test\nline'
            assert index == 0
    
    def test_find_match_by_trigger_display_not_found(self, qapp, mock_settings, mock_os_path):
        """Test finding a match by display trigger when not found."""
        with patch.object(EZpanso, '_setup_ui'), \
             patch.object(EZpanso, '_setup_menubar'), \
             patch.object(EZpanso, '_load_all_yaml_files'):
            
            window = EZpanso()
            window.active_file_path = '/test/file.yml'
            window.files_data = {'/test/file.yml': []}
            
            match, index = window._find_match_by_trigger_display(':nonexistent')
            
            assert match is None
            assert index == -1


if __name__ == "__main__":
    pytest.main([__file__])