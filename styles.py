#!/usr/bin/env python3
"""
EZpanso Styling Constants

This module contains all PyQt6 stylesheet constants used throughout the EZpanso application.
Centralizing styles here improves maintainability and ensures visual consistency.
"""

# Color Palette Constants
PRIMARY_COLOR = "#007acc"
PRIMARY_HOVER_COLOR = "#005c99"
PRIMARY_PRESSED_COLOR = "#004080"

WARNING_COLOR = "#ff9500"
WARNING_HOVER_COLOR = "#e6840e"
WARNING_PRESSED_COLOR = "#cc7300"

BORDER_COLOR = "#ddd"
BORDER_HOVER_COLOR = "#999"
BORDER_PRESSED_COLOR = "#666"

TEXT_COLOR = "#333"
MUTED_TEXT_COLOR = "#666"
BACKGROUND_COLOR = "white"
HOVER_BACKGROUND_COLOR = "#f8f8f8"
PRESSED_BACKGROUND_COLOR = "#eee"

WARNING_BACKGROUND_COLOR = "#fff3cd"
WARNING_BORDER_COLOR = "#ffeaa7"

# Basic Component Styles
BUTTON_STYLE = f"""
    QPushButton {{
        padding: 4px 8px;
        font-size: 11px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 2px;
        background-color: {BACKGROUND_COLOR};
        color: {TEXT_COLOR};
        min-width: 60px;
    }}
    QPushButton:hover {{
        border-color: {BORDER_HOVER_COLOR};
        background-color: {HOVER_BACKGROUND_COLOR};
    }}
    QPushButton:pressed {{
        background-color: {PRESSED_BACKGROUND_COLOR};
    }}
"""

PRIMARY_BUTTON_STYLE = f"""
    QPushButton {{
        padding: 4px 8px;
        font-size: 11px;
        border: 1px solid {PRIMARY_COLOR};
        border-radius: 2px;
        background-color: {PRIMARY_COLOR};
        color: white;
        min-width: 60px;
    }}
    QPushButton:hover {{
        background-color: {PRIMARY_HOVER_COLOR};
        border-color: {PRIMARY_HOVER_COLOR};
    }}
    QPushButton:pressed {{
        background-color: {PRIMARY_PRESSED_COLOR};
    }}
"""

WARNING_BUTTON_STYLE = f"""
    QPushButton {{
        padding: 10px 20px;
        font-size: 12px;
        font-weight: bold;
        border: 1px solid {WARNING_COLOR};
        border-radius: 4px;
        background-color: {WARNING_COLOR}; 
        color: white;
        min-width: 100px;
    }}
    QPushButton:hover {{
        background-color: {WARNING_HOVER_COLOR};
        border-color: {WARNING_HOVER_COLOR};
    }}
    QPushButton:pressed {{
        background-color: {WARNING_PRESSED_COLOR};
    }}
"""

INPUT_STYLE = f"""
    QLineEdit {{
        padding: 4px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 2px;
        font-size: 11px;
        background-color: {BACKGROUND_COLOR};
    }}
    QLineEdit:focus {{
        border-color: {PRIMARY_COLOR};
    }}
"""

# Label Styles
LABEL_STYLE = f"font-weight: bold; color: {TEXT_COLOR}; font-size: 11px;"

INFO_LABEL_STYLE = f"color: {MUTED_TEXT_COLOR}; font-size: 10px; margin: 5px 0;"

INFO_LABEL_MULTILINE_STYLE = f"color: {MUTED_TEXT_COLOR}; font-size: 10px; margin: 5px 0; line-height: 1.3;"

ABOUT_LABEL_STYLE = f"color: {MUTED_TEXT_COLOR}; font-size: 11px; line-height: 1.4;"

WARNING_ICON_STYLE = f"font-size: 32px; color: {WARNING_COLOR};"

# Complex Component Styles
WARNING_TEXT_BACKGROUND_STYLE = f"""
    QLabel {{
        padding: 15px;
        background-color: {WARNING_BACKGROUND_COLOR};
        border: 1px solid {WARNING_BORDER_COLOR};
        border-radius: 6px;
        line-height: 1.6;
    }}
"""

CHECKBOX_STYLE = f"""
    QCheckBox {{
        font-size: 12px;
        color: {MUTED_TEXT_COLOR};
        padding: 5px;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
    }}
    QCheckBox::indicator:unchecked {{
        border: 1px solid #ccc;
        border-radius: 3px;
        background-color: white;
    }}
    QCheckBox::indicator:checked {{
        border: 1px solid {PRIMARY_COLOR};
        border-radius: 3px;
        background-color: {PRIMARY_COLOR};
        image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEzLjg1IDQuMTVMMTAuNSA3LjVMNy4xNSA0LjE1TDguNSAyLjhMMTAuNSA0LjhMMTIuNSAyLjhMMTMuODUgNC4xNVoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPg==);
    }}
"""

MESSAGE_BOX_STYLE = f"""
    QMessageBox {{
        border: 1px solid #ccc;
        min-width: 300px;
    }}
    QMessageBox QLabel {{
        color: {TEXT_COLOR};
        font-size: 12px;
        padding: 15px;
        line-height: 1.5;
        margin: 5px;
    }}
    QMessageBox QPushButton {{
        padding: 4px 8px;
        font-size: 11px;
        border: 1px solid {BORDER_COLOR};
        border-radius: 2px;
        color: {TEXT_COLOR};
        min-width: 60px;
        margin: 2px;
    }}
    QMessageBox QPushButton:hover {{
        border-color: {BORDER_HOVER_COLOR};
    }}
    QMessageBox QPushButton:pressed {{
        border-color: {BORDER_PRESSED_COLOR};
    }}
    QMessageBox QPushButton:default {{
        border: 1px solid {PRIMARY_COLOR};
        background-color: {PRIMARY_COLOR};
        color: white;
    }}
    QMessageBox QPushButton:default:hover {{
        background-color: {PRIMARY_HOVER_COLOR};
        border-color: {PRIMARY_HOVER_COLOR};
    }}
    QMessageBox QPushButton:default:pressed {{
        background-color: {PRIMARY_PRESSED_COLOR};
    }}
"""

# Disabled Button Style (for save button when no changes)
DISABLED_BUTTON_STYLE = """
    QPushButton {
        padding: 4px 8px;
        font-size: 11px;
        border: 1px solid #ddd;
        border-radius: 2px;
        background-color: #f0f0f0;
        color: #999;
        min-width: 60px;
    }
"""
