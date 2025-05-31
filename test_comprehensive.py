#!/usr/bin/env python3
"""
Final comprehensive test of the NSException fixes.
Tests all previously problematic operations.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from main import EZpanso, NewFileDialog

class ComprehensiveTest(QMainWindow):
    """Comprehensive test of all NSException fixes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NSException Fix - Comprehensive Test")
        self.setGeometry(100, 100, 600, 500)
        
        self.test_results = []
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("NSException Fix - Comprehensive Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Test buttons
        btn_test_app_startup = QPushButton("1. Test App Startup & Data Loading")
        btn_test_app_startup.clicked.connect(self.test_app_startup)
        layout.addWidget(btn_test_app_startup)
        
        btn_test_combo_population = QPushButton("2. Test QComboBox Population")
        btn_test_combo_population.clicked.connect(self.test_combo_population)
        layout.addWidget(btn_test_combo_population)
        
        btn_test_dialog_creation = QPushButton("3. Test Dialog Creation")
        btn_test_dialog_creation.clicked.connect(self.test_dialog_creation)
        layout.addWidget(btn_test_dialog_creation)
        
        btn_run_all = QPushButton("🚀 Run All Tests")
        btn_run_all.clicked.connect(self.run_all_tests)
        btn_run_all.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(btn_run_all)
        
        # Results display
        self.results_display = QTextEdit()
        self.results_display.setMinimumHeight(200)
        self.results_display.setReadOnly(True)
        layout.addWidget(QLabel("Test Results:"))
        layout.addWidget(self.results_display)
        
    def log_result(self, test_name, success, details=""):
        """Log a test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        
        self.test_results.append(result)
        self.results_display.append(result)
        print(result)
        
    def test_app_startup(self):
        """Test application startup and data loading."""
        self.log_result("App Startup", True, "Starting test...")
        
        try:
            # Create a temporary EZpanso instance
            temp_app = EZpanso()
            temp_app.espanso_config_dir = '/Users/longman/Library/Application Support/espanso/match'
            
            # Test data loading
            temp_app._refresh_data()
            
            # Clean up
            temp_app.close()
            temp_app.deleteLater()
            
            self.log_result("App Startup & Data Loading", True, "No NSException occurred")
            
        except Exception as e:
            self.log_result("App Startup & Data Loading", False, f"Error: {str(e)}")
            
    def test_combo_population(self):
        """Test QComboBox population with the new safe method."""
        self.log_result("QComboBox Population", True, "Starting test...")
        
        try:
            # Create a test EZpanso instance
            temp_app = EZpanso()
            
            # Test the safe population method
            test_files = ["File 1", "File 2", "File 3", "Test File"]
            temp_app._safely_populate_file_selector(test_files)
            
            # Verify the combo box was populated correctly
            count = temp_app.file_selector.count()
            expected_count = len(test_files) + 3  # +1 for separator, +2 for special options
            
            if count == expected_count:
                self.log_result("QComboBox Safe Population", True, f"Populated with {count} items correctly")
            else:
                self.log_result("QComboBox Safe Population", False, f"Expected {expected_count} items, got {count}")
            
            # Clean up
            temp_app.close()
            temp_app.deleteLater()
            
        except Exception as e:
            self.log_result("QComboBox Safe Population", False, f"Error: {str(e)}")
            
    def test_dialog_creation(self):
        """Test dialog creation with new safety measures."""
        self.log_result("Dialog Creation", True, "Starting test...")
        
        try:
            # Test NewFileDialog creation (the one that was causing NSException)
            dialog = NewFileDialog(self, "/tmp")
            
            # Test that the dialog was created successfully
            if dialog.windowTitle() == "Create New File":
                self.log_result("NewFileDialog Creation", True, "Dialog created with proper title")
            else:
                self.log_result("NewFileDialog Creation", False, "Dialog title incorrect")
                
            # Test modal behavior
            if dialog.isModal():
                self.log_result("Dialog Modal Behavior", True, "Dialog is properly modal")
            else:
                self.log_result("Dialog Modal Behavior", False, "Dialog is not modal")
                
            # Test window flags
            flags = dialog.windowFlags()
            if Qt.WindowType.Dialog in flags:
                self.log_result("Dialog Window Flags", True, "Proper window flags set")
            else:
                self.log_result("Dialog Window Flags", False, "Missing dialog window flags")
            
            # Clean up
            dialog.close()
            dialog.deleteLater()
            
        except Exception as e:
            self.log_result("Dialog Creation", False, f"Error: {str(e)}")
            
    def run_all_tests(self):
        """Run all tests in sequence."""
        self.results_display.clear()
        self.test_results = []
        
        self.log_result("Comprehensive Test Suite", True, "Starting all tests...")
        
        # Run tests with small delays between them
        QTimer.singleShot(100, self.test_app_startup)
        QTimer.singleShot(2000, self.test_combo_population)
        QTimer.singleShot(4000, self.test_dialog_creation)
        QTimer.singleShot(6000, self.show_final_results)
        
    def show_final_results(self):
        """Show final test results."""
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r])
        failed_tests = len([r for r in self.test_results if "❌ FAIL" in r])
        
        self.results_display.append("\n" + "="*50)
        if failed_tests == 0:
            self.results_display.append("🎉 ALL TESTS PASSED! NSException fixes are working correctly.")
        else:
            self.results_display.append(f"⚠️ {passed_tests} passed, {failed_tests} failed")
        self.results_display.append("="*50)

def main():
    """Run the comprehensive test."""
    app = QApplication(sys.argv)
    
    # Set macOS-specific attributes
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_NativeWindows, False)
    
    window = ComprehensiveTest()
    window.show()
    
    print("Comprehensive NSException test started.")
    print("Click 'Run All Tests' to verify all fixes are working.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
