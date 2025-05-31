#!/usr/bin/env python3
"""
Test script to verify NSException fix for QComboBox operations on macOS.
This script tests the specific operations that were causing crashes.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QComboBox, QLabel
from PyQt6.QtCore import Qt

class TestNSExceptionFix(QMainWindow):
    """Test window to verify NSException fixes."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NSException Fix Test - QComboBox Operations")
        self.setGeometry(100, 100, 500, 400)
        
        # Set up UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Set up the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test QComboBox
        self.combo = QComboBox()
        self.combo.setMinimumWidth(300)
        layout.addWidget(QLabel("Test QComboBox:"))
        layout.addWidget(self.combo)
        
        # Test buttons
        btn_test_add_items = QPushButton("Test addItems() - Old Method (Problematic)")
        btn_test_add_items.clicked.connect(self.test_add_items_old)
        layout.addWidget(btn_test_add_items)
        
        btn_test_safe_populate = QPushButton("Test Safe Population - New Method")
        btn_test_safe_populate.clicked.connect(self.test_safe_populate)
        layout.addWidget(btn_test_safe_populate)
        
        btn_clear = QPushButton("Clear ComboBox")
        btn_clear.clicked.connect(self.clear_combo)
        layout.addWidget(btn_clear)
        
        # Status label
        self.status_label = QLabel("Ready to test...")
        layout.addWidget(self.status_label)
        
    def test_add_items_old(self):
        """Test the old addItems() method that was causing NSException."""
        try:
            self.status_label.setText("Testing old addItems() method...")
            self.combo.clear()
            
            # This was the problematic call
            test_items = ["Category 1", "Category 2", "Category 3"]
            self.combo.addItems(test_items)
            
            # Add separator and option
            self.combo.insertSeparator(len(test_items))
            self.combo.addItem("Add new Category...")
            
            self.status_label.setText("✅ Old method succeeded (unexpected!)")
        except Exception as e:
            self.status_label.setText(f"❌ Old method failed: {str(e)}")
            
    def test_safe_populate(self):
        """Test the new safe population method."""
        try:
            self.status_label.setText("Testing safe population method...")
            self.combo.clear()
            
            # Use the safe population method
            test_items = ["Category 1", "Category 2", "Category 3"]
            self._safely_populate_combo(test_items)
            
            self.status_label.setText("✅ Safe method succeeded!")
        except Exception as e:
            self.status_label.setText(f"❌ Safe method failed: {str(e)}")
            
    def _safely_populate_combo(self, display_names):
        """Safe method to populate combo box (copied from main_improved.py)."""
        try:
            # Block signals temporarily to prevent recursive calls
            self.combo.blockSignals(True)
            
            # Add categories one by one instead of using addItems()
            if display_names:
                for name in display_names:
                    if name and isinstance(name, str):
                        self.combo.addItem(name)
                
                # Add separator only if we have valid categories
                if self.combo.count() > 0:
                    self.combo.insertSeparator(self.combo.count())
            
            # Always add the "Add new Category..." option at the end
            self.combo.addItem("Add new Category...")
            
        except Exception as e:
            print(f"Error in safe populate: {e}")
            # Fallback
            try:
                self.combo.clear()
                self.combo.addItem("Add new Category...")
            except Exception as fallback_error:
                print(f"Critical error in fallback: {fallback_error}")
        finally:
            # Always re-enable signals
            self.combo.blockSignals(False)
            
    def clear_combo(self):
        """Clear the combo box."""
        try:
            self.combo.clear()
            self.status_label.setText("ComboBox cleared")
        except Exception as e:
            self.status_label.setText(f"Error clearing: {str(e)}")

def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Set macOS-specific attributes (same as in main_improved.py)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    app.setAttribute(Qt.ApplicationAttribute.AA_NativeWindows, False)
    
    window = TestNSExceptionFix()
    window.show()
    
    print("Test application started. Try both methods to see the difference.")
    print("If the old method crashes with NSException, we've confirmed the fix works.")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
