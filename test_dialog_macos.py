#!/usr/bin/env python3
"""
Test script specifically for testing NSException fixes in dialogs on macOS.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
import logging

# Import the dialog from our improved main
from main import NewCategoryDialog, EditSnippetDialog
from data_model import Snippet

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DialogTestWindow(QMainWindow):
    """Test window for dialog functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Test - macOS NSException Fix")
        self.setGeometry(100, 100, 400, 300)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test buttons
        new_category_btn = QPushButton("Test New Category Dialog")
        new_category_btn.clicked.connect(self.test_new_category_dialog)
        layout.addWidget(new_category_btn)
        
        edit_snippet_btn = QPushButton("Test Edit Snippet Dialog")
        edit_snippet_btn.clicked.connect(self.test_edit_snippet_dialog)
        layout.addWidget(edit_snippet_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def test_new_category_dialog(self):
        """Test the NewCategoryDialog for NSException issues."""
        logger.info("Testing NewCategoryDialog...")
        
        dialog = None
        try:
            # Create a test directory path
            test_dir = os.path.expanduser("~/Desktop")
            
            # Create dialog with enhanced macOS safety
            dialog = NewCategoryDialog(self, test_dir)
            
            logger.info("Dialog created successfully")
            
            # Show the dialog
            result = dialog.exec()
            
            if result and dialog.result:
                logger.info(f"Dialog result: {dialog.result}")
            else:
                logger.info("Dialog cancelled or no result")
                
        except Exception as e:
            logger.error(f"Error in NewCategoryDialog test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure cleanup
            if dialog is not None:
                try:
                    dialog.close()
                    dialog.deleteLater()
                except Exception as cleanup_error:
                    logger.warning(f"Error during dialog cleanup: {cleanup_error}")
    
    def test_edit_snippet_dialog(self):
        """Test the EditSnippetDialog for NSException issues."""
        logger.info("Testing EditSnippetDialog...")
        
        dialog = None
        try:
            # Create a test snippet
            test_snippet = Snippet("test", "Test replacement text", "/tmp/test.yml")
            
            # Create dialog with enhanced macOS safety
            dialog = EditSnippetDialog(self, "Test Edit Snippet", test_snippet)
            
            logger.info("Edit dialog created successfully")
            
            # Show the dialog
            result = dialog.exec()
            
            if result and dialog.result:
                logger.info(f"Edit dialog result: {dialog.result}")
            else:
                logger.info("Edit dialog cancelled or no result")
                
        except Exception as e:
            logger.error(f"Error in EditSnippetDialog test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Ensure cleanup
            if dialog is not None:
                try:
                    dialog.close()
                    dialog.deleteLater()
                except Exception as cleanup_error:
                    logger.warning(f"Error during dialog cleanup: {cleanup_error}")

def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # macOS-specific settings to prevent NSExceptions
    app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
    app.setAttribute(Qt.ApplicationAttribute.AA_NativeWindows, False)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings, True)
    
    # Set style
    app.setStyle("Fusion")
    
    try:
        window = DialogTestWindow()
        window.show()
        
        logger.info("Test window started. Click buttons to test dialogs for NSException issues.")
        
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Test application failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
