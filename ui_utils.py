from PyQt6.QtWidgets import QMessageBox, QWidget
from typing import Optional

class UIHelpers:
    @staticmethod
    def create_preview_text(text: str, max_len: int = 50) -> str:
        """
        Creates a preview of the text, truncating if necessary.
        """
        if not text:
            return ""
        if len(text) > max_len:
            return text[:max_len-3] + "..."
        return text.replace("\n", " ") # Replace newlines for single-line preview

    @staticmethod
    def create_confirmation_dialog(parent: Optional[QWidget], title: str, text: str) -> QMessageBox.StandardButton:
        """
        Creates and shows a confirmation dialog.
        Returns the button clicked by the user.
        """
        return QMessageBox.question(
            parent,
            title,
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

    @staticmethod
    def show_error_message(parent: Optional[QWidget], message: str, title: str = "Error") -> None:
        """
        Displays an error message box.
        """
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def show_warning_message(parent: Optional[QWidget], message: str, title: str = "Warning") -> None:
        """
        Displays a warning message box.
        """
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_info_message(parent: Optional[QWidget], message: str, title: str = "Information") -> None:
        """
        Displays an informational message box.
        """
        QMessageBox.information(parent, title, message)