# constants.py

# Treeview columns
COL_TRIGGER = "trigger"
COL_REPLACE = "replace"
TREEVIEW_COLUMNS = (COL_TRIGGER, COL_REPLACE)

# Sort indicators
SORT_ASC_INDICATOR = " ▲"
SORT_DESC_INDICATOR = " ▼"

# Default Espanso Paths (keys are platform.system() outputs)
DEFAULT_ESPANSO_PATHS = {
    "Darwin": "~/Library/Application Support/espanso/match",
    "Linux": "~/.config/espanso/match" # XDG_CONFIG_HOME will be checked first in file_handler
}

# YAML structure
YAML_MATCHES_KEY = "matches"

# Status Bar Messages
MSG_WELCOME = "Welcome to EZpanso."
MSG_LOADING_INITIAL_CONFIG = "Loading initial configuration..."
MSG_DEFAULT_DIR_NOT_FOUND = "Default Espanso config directory not found. Select via File > Open Espanso Dir."
MSG_SELECTING_DIR = "Selecting Espanso directory..."
MSG_DIR_SELECTION_CANCELLED = "Directory selection cancelled."
MSG_REFRESHING_DATA = "Refreshing data..."
MSG_DATA_REFRESHED = "Data refreshed."
MSG_LOADING_FILES = "Loading files..."
MSG_NO_YAML_FILES_FOUND = "No YAML files found in {}."
MSG_LOADED_SNIPPETS_COUNT = "Loaded {snippet_count} snippets from {file_count} files."
MSG_NO_FILE_SELECTED = "No file selected."
MSG_ERROR_FINDING_FILE_FOR_FILE = "Error: Could not find file for file {}."
MSG_FILE_DISPLAY = "File: {file_name} ({snippet_count} snippets) | Modified: {mtime}"
MSG_FILE_FILE_NOT_FOUND = "File: {file_name} (File not found, {snippet_count} in memory)"
MSG_FILE_MODIFIED_UNKNOWN = "File: {file_name} ({snippet_count} snippets) | Modified: Unknown"
MSG_FILE_NO_SNIPPETS = "File: {file_name} (No snippets to display or error)"
MSG_SAVING_ALL_CHANGES = "Saving all changes..."
MSG_SAVE_SUCCESSFUL_COUNT = "Successfully saved changes to {count} file(s)."
MSG_SAVE_ERROR_UNEXPECTED = "Save operation failed with an unexpected error."
MSG_CREATING_FILE = "Creating new file..."
MSG_CREATED_NEW_FILE = "Created new file: {}. Add snippets and save."
MSG_FAILED_CREATE_FILE = "Failed to create new file."
MSG_REMOVING_FILE = "Removing file '{}'..."
MSG_FILE_DELETED = "File '{}' deleted."
MSG_FAILED_DELETE_FILE = "Failed to delete file '{}'."
MSG_LOAD_ERROR = "Error during data loading"

# Confirmations
CONFIRM_UNSAVED_REFRESH = "Unsaved changes exist. Refresh and lose them?"
CONFIRM_UNSAVED_QUIT = "Unsaved changes exist. Quit without saving?"
CONFIRM_REMOVE_SNIPPETS = "Remove {count} snippet(s) from {file_name}?\nThis is permanent upon saving."
CONFIRM_DELETE_FILE = "Permanently delete the file '{file_name}' and all its snippets?"

# Titles
TITLE_APP = "EZpanso - Espanso Manager"
TITLE_EDIT_SNIPPET = "Edit Snippet: {}"
TITLE_NEW_FILE = "New File"

# Keyboard Shortcuts
SHORTCUT_ADD = "Ctrl+N"  # Platform will automatically map to Command on macOS
SHORTCUT_NEW_FILE = "Ctrl+Shift+N"
SHORTCUT_SAVE = "Ctrl+S"
SHORTCUT_REFRESH = "F5"
SHORTCUT_EDIT = "Return"
SHORTCUT_DELETE = "Delete"
SHORTCUT_DELETE_FILE = "Shift+Delete"
SHORTCUT_CANCEL = "Escape"
SHORTCUT_MOVE_UP = "Up"
SHORTCUT_MOVE_DOWN = "Down"
SHORTCUT_MULTI_SELECT = "Shift+Up/Down"

# Keyboard behavior settings
KEY_REPEAT_DELAY = 200  # Milliseconds before key starts repeating
KEY_REPEAT_INTERVAL = 30  # Milliseconds between repeats

# Menu Labels
MENU_FILE_SAVE = "Save All Changes ({})".format(SHORTCUT_SAVE)
MENU_FILE_REFRESH = "Refresh Data ({})".format(SHORTCUT_REFRESH)
MENU_FILE_ADD = "Add ({})".format(SHORTCUT_ADD)
MENU_FILE_NEW_FILE = "New File ({})".format(SHORTCUT_NEW_FILE)

# Button Labels with Shortcuts
BTN_NEW_SNIPPET = "New Snippet (⌘N)"
BTN_EDIT_SNIPPET = "Edit (↵)"
BTN_DELETE_SNIPPET = "Delete (⌫)"
BTN_DELETE_FILE = "Delete File (⇧⌫)"
BTN_ESPANSO_HUB = "Espanso Hub"
BTN_SAVE_ALL = "Save All"

# Dropdown Options
DROPDOWN_CREATE_NEW_FILE = "➕ Create new file (⌘⇧N)"
DROPDOWN_SELECT_MATCH_FOLDER = "📁 Select match folder..."

# Errors
ERROR_TRIGGER_EMPTY = "Trigger cannot be empty."
ERROR_TRIGGER_EXISTS = "Trigger '{}' already exists in this file."
ERROR_FILE_NAME_EMPTY = "File name cannot be empty."
ERROR_FILE_NAME_INVALID_CHARS = "File name contains invalid characters."
ERROR_FILE_NO_EXTENSION = "Do not include .yml or .yaml extension; it will be added."
ERROR_FILE_FILE_EXISTS = "A file '{}' already exists."
ERROR_ESPANSO_DIR_NOT_SET = "Espanso directory not set."
ERROR_COULD_NOT_FIND_SNIPPET = "Could not find selected snippet data."
ERROR_ANOTHER_TRIGGER_EXISTS = "Another trigger '{}' already exists in this file."
ERROR_NO_FILE_TO_ADD_SNIPPET = "No file selected to add snippet to."
ERROR_NO_FILE_TO_REMOVE = "No file selected to remove."
ERROR_INTERNAL_NO_FILE_FOR_FILE = "Internal error: Cannot find file for selected file."
ERROR_OPEN_ESPANSO_DIR_FIRST = "Please open an Espanso directory first."
ERROR_NO_SNIPPET_SELECTED_EDIT = "No snippet selected to edit."
ERROR_NO_SNIPPET_SELECTED_DELETE = "No snippet selected to delete."
ERROR_ESPANSO_DIR_NOT_FOUND = "Espanso configuration directory not found."

# Messages
MSG_CONFIRM_DELETE_SNIPPET_TITLE = "Confirm Delete"
MSG_CONFIRM_DELETE_SNIPPET_TEXT = "Are you sure you want to delete the selected snippet(s)?"
MSG_CONFIRM_DELETE_FILE_TITLE = "Confirm Delete File"
MSG_CONFIRM_DELETE_FILE_TEXT = "Are you sure you want to delete the file '{filename}' and all its snippets?"
MSG_UNSAVED_CHANGES_TITLE = "Unsaved Changes"
MSG_UNSAVED_CHANGES_TEXT = "You have unsaved changes. Would you like to save them before exiting?"

# Misc
NEW_SNIPPET_ID_PREFIX = "new_snippet_"
TEMP_EZ_FOLDER_NAME = "temp-ez"
URL_ESPANSO_HUB = "https://espanso.org/hub/"