import os
import platform
import logging

logger = logging.getLogger(__name__)

def get_default_espanso_config_path() -> str:
    """
    Tries to determine the default Espanso match directory path based on the OS.
    Returns the path to the 'match' directory if found, otherwise an empty string.
    """
    system = platform.system()
    espanso_config_dir = ""

    if system == "Linux":
        # Common paths for Espanso on Linux
        possible_paths = [
            os.path.expanduser("~/.config/espanso"),
            os.path.expanduser("~/.espanso") # Older versions or custom
        ]
    elif system == "Darwin": # macOS
        possible_paths = [
            os.path.expanduser("~/Library/Application Support/espanso"),
            # For versions installed via Homebrew, config might be elsewhere
            # but typically 'espanso path' command is the source of truth.
            # This function provides a best-guess default.
            os.path.expanduser("~/.config/espanso") # Less common but possible
        ]
    elif system == "Windows":
        possible_paths = [
            os.path.join(os.getenv("APPDATA", ""), "espanso"),
            os.path.join(os.getenv("LOCALAPPDATA", ""), "espanso") # Less common
        ]
    else:
        logger.warning(f"Unsupported operating system: {system}")
        return ""

    for path_option in possible_paths:
        if os.path.isdir(path_option):
            espanso_config_dir = path_option
            break
    
    if not espanso_config_dir:
        logger.warning("Could not automatically determine Espanso config directory.")
        return ""

    match_dir = os.path.join(espanso_config_dir, "match")
    if os.path.isdir(match_dir):
        logger.info(f"Found Espanso match directory at: {match_dir}")
        return match_dir
    else:
        # Fallback for older espanso versions or different structures where 'user' might be used
        user_dir = os.path.join(espanso_config_dir, "user")
        if os.path.isdir(user_dir):
            logger.info(f"Found Espanso user directory (fallback for match) at: {user_dir}")
            return user_dir
        logger.warning(f"Espanso config directory found at '{espanso_config_dir}', but 'match' or 'user' sub-directory not found.")
        return ""

if __name__ == '__main__':
    # For testing the function
    print(f"Detected Espanso match/user path: {get_default_espanso_config_path()}")