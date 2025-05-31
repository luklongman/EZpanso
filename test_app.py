#!/usr/bin/env python3
"""
Test script to verify the improved EZpanso application starts without errors.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from PyQt6.QtWidgets import QApplication
    from main_improved import EZpanso
    import logging
    
    # Set up logging to see any issues
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    def test_app_startup():
        """Test that the app can start and load data without errors."""
        app = QApplication(sys.argv)
        
        try:
            # Create the main window
            window = EZpanso()
            
            # Check that it loaded some data
            if window.snippets_by_file_path:
                print(f"✅ Successfully loaded {len(window.snippets_by_file_path)} category files")
                
                # Check categories
                categories = list(window.category_dropdown_map.keys())
                print(f"✅ Categories found: {categories}")
                
                # Check if active file path is set
                if window.active_file_path:
                    print(f"✅ Active file path set: {os.path.basename(window.active_file_path)}")
                    
                    # Check snippets count
                    snippets = window._get_active_snippets()
                    print(f"✅ Active category has {len(snippets)} snippets")
                else:
                    print("ℹ️  No active file path set (this is normal on first load)")
            else:
                print("⚠️  No category files loaded")
            
            # Don't show the window, just test the initialization
            print("✅ Application startup test completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during startup: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            app.quit()
    
    if __name__ == "__main__":
        success = test_app_startup()
        sys.exit(0 if success else 1)
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure PyQt6 is installed: pip install PyQt6")
    sys.exit(1)
