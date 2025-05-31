import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import yaml # Requires PyYAML: pip install PyYAML
from datetime import datetime
import platform

# --- Data Model ---
class Snippet:
    """Represents a single Espanso snippet."""
    def __init__(self, trigger, replace_text, file_path, category, last_modified_timestamp, original_yaml_entry=None):
        self.trigger = str(trigger) if trigger is not None else ""
        self.replace_text = str(replace_text) if replace_text is not None else ""
        self.file_path = file_path
        self.category = category  # filename without .yml
        self.last_modified_timestamp = last_modified_timestamp  # file's mtime (datetime object)
        
        # Store the full original dict to preserve other keys (e.g., label, vars)
        if original_yaml_entry is None:
            self.original_yaml_entry = {'trigger': self.trigger, 'replace': self.replace_text}
        else:
            self.original_yaml_entry = original_yaml_entry
            # Ensure trigger and replace are strings for consistency, even if loaded as other types
            self.original_yaml_entry['trigger'] = str(self.original_yaml_entry.get('trigger', ''))
            self.original_yaml_entry['replace'] = str(self.original_yaml_entry.get('replace', ''))


        self.tree_item_id = None  # To link Treeview item with this object
        
        # State flags
        self.is_new = False
        self.is_modified = False
        # Deletion is handled by removing from the list, not a flag here

    def get_display_values(self):
        """Values to display in the Treeview."""
        # Display only the first line of replace_text in treeview for brevity
        first_line_replace = self.replace_text.splitlines()[0] if self.replace_text else ""
        if len(self.replace_text.splitlines()) > 1:
            first_line_replace += "..."

        return (
            self.category,
            self.trigger,
            first_line_replace, # Show only first line or truncated
            self.file_path,
            self.last_modified_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )

    def mark_modified(self, new_trigger, new_replace_text):
        """Updates snippet and marks as modified if changes occurred."""
        if self.trigger != new_trigger or self.replace_text != new_replace_text:
            self.trigger = new_trigger
            self.replace_text = new_replace_text
            # Update the original_yaml_entry as well for saving
            self.original_yaml_entry['trigger'] = new_trigger
            self.original_yaml_entry['replace'] = new_replace_text
            if not self.is_new: # Don't mark as modified if it's already new
                self.is_modified = True
            return True
        return False

# --- Dialogs ---
class SnippetDialog(simpledialog.Dialog):
    """Dialog for adding or editing a snippet."""
    def __init__(self, parent, title, existing_snippet=None, categories=None, espanso_dir=""):
        self.snippet_data = existing_snippet
        self.categories = categories if categories else []
        self.espanso_dir = espanso_dir
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Category:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.category_var = tk.StringVar()
        if self.snippet_data:
            self.category_var.set(self.snippet_data.category)
        
        self.category_combo = ttk.Combobox(master, textvariable=self.category_var, values=self.categories, width=47)
        self.category_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        if not self.categories and not self.snippet_data: # If adding first snippet and no categories exist
            self.category_var.set("base") # Default to 'base'

        ttk.Label(master, text="Trigger:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.trigger_entry = ttk.Entry(master, width=50)
        self.trigger_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if self.snippet_data:
            self.trigger_entry.insert(0, self.snippet_data.trigger)

        ttk.Label(master, text="Replace:").grid(row=2, column=0, sticky="nw", padx=5, pady=2)
        self.replace_text = tk.Text(master, width=50, height=10, wrap=tk.WORD)
        self.replace_text.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
        if self.snippet_data:
            self.replace_text.insert(tk.END, self.snippet_data.replace_text)
        
        master.grid_columnconfigure(1, weight=1) # Make entry and text expandable
        return self.trigger_entry # initial focus

    def apply(self):
        trigger = self.trigger_entry.get().strip()
        replace = self.replace_text.get("1.0", tk.END).strip() # Get all text, strip trailing newline
        category = self.category_var.get().strip()

        if not trigger:
            messagebox.showerror("Error", "Trigger cannot be empty.", parent=self)
            self.result = None # Stay in dialog
            return
        
        if not category:
            messagebox.showerror("Error", "Category cannot be empty.", parent=self)
            self.result = None # Stay in dialog
            return

        file_path = os.path.join(self.espanso_dir, f"{category}.yml")

        self.result = {
            "trigger": trigger,
            "replace_text": replace,
            "category": category,
            "file_path": file_path
        }

# --- Main Application ---
class EspansoManagerApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("Espanso Manager")
        self.set_app_icon()
        self.root.geometry("1200x700") 

        self.espanso_config_dir = ""
        self.all_snippets = []  # List of Snippet objects
        self.file_modification_times = {}
        self.current_sort_column = None
        self.current_sort_reverse = False

        self.create_widgets()
        # Initialize save button state
        self.update_save_button_state()
        self.load_initial_config()

    def set_app_icon(self):
        """Set the application icon based on the current platform."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "logo.ico")
            if os.path.exists(icon_path):
                if platform.system() == "Darwin":
                    try:
                        # Try the macOS specific method first
                        self.root.iconbitmap(bitmap=f"@{icon_path}")
                    except:
                        # If that fails, try without the @ symbol
                        try:
                            self.root.iconbitmap(icon_path)
                        except:
                            # If both methods fail, silently continue
                            pass
                else:
                    self.root.iconbitmap(icon_path)
        except Exception as e:
            # Just print the error and continue
            print(f"Could not set application icon: {e}")
            pass  # Don't let icon issues prevent the app from starting

    def get_default_espanso_config_path(self):
        """Gets the default Espanso match directory based on OS."""
        system = platform.system()
        if system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/espanso/match")
        elif system == "Linux":
            # Check XDG_CONFIG_HOME first, then default ~/.config
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                return os.path.join(xdg_config_home, "espanso/match")
            return os.path.expanduser("~/.config/espanso/match")
        # Add Windows path if needed, though user specified macOS
        # elif system == "Windows":
        # return os.path.expanduser("~/AppData/Roaming/espanso/match") 
        return None # Unknown OS

    def create_widgets(self):
        # Menu
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Espanso Dir", command=self.select_espanso_directory)
        filemenu.add_command(label="Refresh Data (F5)", command=self.refresh_data)
        filemenu.add_separator()
        filemenu.add_command(label="Save All Changes (Cmd/Ctrl+S)", command=self.save_all_changes)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

        # Bindings for shortcuts
        self.root.bind_all("<Command-s>", lambda event: self.save_all_changes()) # macOS
        self.root.bind_all("<Control-s>", lambda event: self.save_all_changes()) # Windows/Linux
        self.root.bind("<F5>", lambda event: self.refresh_data())


        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Treeview for spreadsheet
        columns = ("category", "trigger", "replace", "file_location", "updated_at")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")

        col_widths = {"category": 120, "trigger": 200, "replace": 350, "file_location": 250, "updated_at": 150}

        for col in columns:
            self.tree.heading(col, text=col.replace("_", " ").title(), command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=col_widths[col], stretch=True if col in ["trigger", "replace"] else tk.NO)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click_edit)

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10) # Spans across tree and scrollbar col

        self.add_button = ttk.Button(button_frame, text="Add Snippet", command=self.add_snippet_dialog_handler)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.remove_button = ttk.Button(button_frame, text="Remove Selected Snippet", command=self.remove_selected_snippet)
        self.remove_button.pack(side=tk.LEFT, padx=5)

        self.new_category_button = ttk.Button(button_frame, text="New Category", command=self.create_new_category)
        self.new_category_button.pack(side=tk.LEFT, padx=5)

        # Add save button on the right side
        self.save_button = ttk.Button(button_frame, text="Save Changes", command=self.save_all_changes)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        self.status_bar_text = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar(f"Welcome to Espanso Manager. {len(self.all_snippets)} snippets loaded.")


    def update_status_bar(self, message):
        self.status_bar_text.set(message)

    def load_initial_config(self):
        default_path = self.get_default_espanso_config_path()
        if default_path and os.path.isdir(default_path):
            self.espanso_config_dir = default_path
            self.load_config_data()
        else:
            self.update_status_bar("Default Espanso config directory not found. Please select it via File > Open Espanso Dir.")
            messagebox.showinfo("Info", "Default Espanso config directory not found or not accessible.\nPlease use 'File > Open Espanso Dir' to select your Espanso 'match' directory.", parent=self.root)


    def select_espanso_directory(self):
        dir_path = filedialog.askdirectory(title="Select Espanso Match Directory", initialdir=os.path.expanduser("~"))
        if dir_path:
            if os.path.basename(dir_path) != "match": # Basic check, could be more robust
                messagebox.showwarning("Warning", "The selected directory doesn't look like an Espanso 'match' directory. Ensure it contains your .yml configuration files.", parent=self.root)
            self.espanso_config_dir = dir_path
            self.load_config_data()
        else:
            self.update_status_bar("Directory selection cancelled.")

    def refresh_data(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Espanso directory not set. Please open one first.", parent=self.root)
            return
        # Warn about unsaved changes before refresh
        if any(s.is_new or s.is_modified for s in self.all_snippets):
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Are you sure you want to refresh and lose them?", parent=self.root):
                return
        self.load_config_data()
        self.update_status_bar(f"Data refreshed. {len(self.all_snippets)} snippets loaded.")


    def load_yaml_file(self, file_path):
        """Load and parse a YAML file, returning the content and last modified time."""
        try:
            mtime_ts = os.path.getmtime(file_path)
            last_modified = datetime.fromtimestamp(mtime_ts)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
            return content, last_modified
        except yaml.YAMLError as e:
            messagebox.showerror("YAML Error", f"Error parsing {os.path.basename(file_path)}:\n{e}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading {os.path.basename(file_path)}:\n{e}", parent=self.root)
        return None, None

    def process_matches_list(self, matches_list, file_path, category, last_modified):
        """Process a list of matches from a YAML file and create Snippet objects."""
        snippets = []
        if isinstance(matches_list, list):
            for entry in matches_list:
                if isinstance(entry, dict) and "trigger" in entry and "replace" in entry:
                    snippet = Snippet(
                        trigger=entry.get("trigger"),
                        replace_text=entry.get("replace"),
                        file_path=file_path,
                        category=category,
                        last_modified_timestamp=last_modified,
                        original_yaml_entry=entry.copy()
                    )
                    snippets.append(snippet)
                else:
                    print(f"Skipping malformed match entry in {category}: {entry}")
        return snippets

    def load_config_data(self):
        if not self.espanso_config_dir or not os.path.isdir(self.espanso_config_dir):
            self.update_status_bar("Espanso directory not set or invalid.")
            return

        self.all_snippets.clear()
        self.file_modification_times.clear()

        for filename in os.listdir(self.espanso_config_dir):
            if filename.endswith((".yml", ".yaml")):
                file_path = os.path.join(self.espanso_config_dir, filename)
                category = os.path.splitext(filename)[0]
                
                content, last_modified = self.load_yaml_file(file_path)
                if content and last_modified:
                    self.file_modification_times[file_path] = last_modified
                    
                    if isinstance(content, dict) and "matches" in content:
                        new_snippets = self.process_matches_list(
                            content["matches"], 
                            file_path, 
                            category, 
                            last_modified
                        )
                        self.all_snippets.extend(new_snippets)
        
        self.populate_treeview()
        self.update_status_bar(f"Loaded {len(self.all_snippets)} snippets from {self.espanso_config_dir}")


    def update_save_button_state(self):
        """Update the save button state based on whether there are unsaved changes."""
        has_changes = any(s.is_new or s.is_modified for s in self.all_snippets)
        self.save_button.state(['!disabled'] if has_changes else ['disabled'])

    def populate_treeview(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add new items
        for i, snippet in enumerate(self.all_snippets):
            values = snippet.get_display_values()
            tree_item_id = self.tree.insert("", tk.END, values=values, iid=f"snippet_{i}")
            snippet.tree_item_id = tree_item_id
        
        # Update save button state
        self.update_save_button_state()

    def get_categories(self):
        """Returns a sorted list of unique category names."""
        categories = sorted(list(set(s.category for s in self.all_snippets)))
        if not categories and self.espanso_config_dir: # If no snippets yet, but dir is set
            # Check for existing .yml files that might be empty or non-match files
            # to suggest as categories
            for filename in os.listdir(self.espanso_config_dir):
                 if filename.endswith((".yml", ".yaml")):
                    cat_name = os.path.splitext(filename)[0]
                    if cat_name not in categories:
                        categories.append(cat_name)
            categories = sorted(list(set(categories))) # Ensure uniqueness and sort
        return categories


    def add_snippet_dialog_handler(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Please open an Espanso directory first.", parent=self.root)
            return

        dialog = SnippetDialog(self.root, "Add New Snippet", categories=self.get_categories(), espanso_dir=self.espanso_config_dir)
        if dialog.result:
            data = dialog.result
            
            # Check if snippet with same trigger and category already exists
            for s in self.all_snippets:
                if s.category == data["category"] and s.trigger == data["trigger"]:
                    messagebox.showerror("Error", f"A snippet with trigger '{data['trigger']}' already exists in category '{data['category']}'.", parent=self.root)
                    return

            new_snippet = Snippet(
                trigger=data["trigger"],
                replace_text=data["replace_text"],
                file_path=data["file_path"],
                category=data["category"],
                last_modified_timestamp=datetime.now() # Will be updated on save from file mtime
            )
            new_snippet.is_new = True
            self.all_snippets.append(new_snippet)
            self.populate_treeview() # Refresh view
            # Auto-select and scroll to the new item
            if new_snippet.tree_item_id:
                self.tree.selection_set(new_snippet.tree_item_id)
                self.tree.see(new_snippet.tree_item_id)
            self.update_status_bar(f"Added new snippet for trigger '{data['trigger']}'. Remember to save.")


    def on_double_click_edit(self, event):
        selected_item_id = self.tree.focus() # Get focused item (double-clicked)
        if not selected_item_id:
            return

        # Find the snippet object corresponding to the selected tree item
        selected_snippet = None
        for snippet in self.all_snippets:
            if snippet.tree_item_id == selected_item_id:
                selected_snippet = snippet
                break
        
        if not selected_snippet:
            messagebox.showerror("Error", "Could not find the selected snippet data.", parent=self.root)
            return

        dialog = SnippetDialog(self.root, f"Edit Snippet: {selected_snippet.trigger}", existing_snippet=selected_snippet, categories=self.get_categories(), espanso_dir=self.espanso_config_dir)
        if dialog.result:
            updated_data = dialog.result
            
            # Check for trigger collision if trigger or category changed
            if (selected_snippet.trigger != updated_data["trigger"] or selected_snippet.category != updated_data["category"]):
                for s in self.all_snippets:
                    if s != selected_snippet and s.category == updated_data["category"] and s.trigger == updated_data["trigger"]:
                        messagebox.showerror("Error", f"Another snippet with trigger '{updated_data['trigger']}' already exists in category '{updated_data['category']}'.", parent=self.root)
                        return

            # Update the snippet
            modified = selected_snippet.mark_modified(updated_data["trigger"], updated_data["replace_text"])
            
            # If category (and thus file_path) changed
            if selected_snippet.category != updated_data["category"]:
                selected_snippet.category = updated_data["category"]
                selected_snippet.file_path = updated_data["file_path"]
                if not selected_snippet.is_new: # Mark as modified if category changed
                    selected_snippet.is_modified = True 
                modified = True

            if modified:
                self.populate_treeview() # Refresh view to show changes
                # Re-select the edited item
                if selected_snippet.tree_item_id: # tree_item_id might change if we re-iid on populate
                    # We need a stable way to find the item after repopulating or update its values directly
                    # For simplicity, just repopulate. User might lose exact scroll position.
                    # To fix this, find it again:
                    for i, snip in enumerate(self.all_snippets):
                        if snip == selected_snippet: # Relies on object identity
                            new_tree_id = f"snippet_{i}" # Assuming IID is index based
                            if self.tree.exists(new_tree_id):
                                self.tree.selection_set(new_tree_id)
                                self.tree.see(new_tree_id)
                            break
                self.update_status_bar(f"Snippet '{selected_snippet.trigger}' modified. Remember to save.")


    def remove_selected_snippet(self):
        selected_item_ids = self.tree.selection() # Can be multiple
        if not selected_item_ids:
            messagebox.showinfo("Info", "No snippet selected to remove.", parent=self.root)
            return

        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to remove {len(selected_item_ids)} selected snippet(s)?\nThis action will be permanent upon saving.", parent=self.root):
            return

        snippets_to_remove = []
        for item_id in selected_item_ids:
            for snippet in self.all_snippets:
                if snippet.tree_item_id == item_id:
                    snippets_to_remove.append(snippet)
                    break
        
        num_removed = 0
        for snippet_to_remove in snippets_to_remove:
            self.all_snippets.remove(snippet_to_remove) # Remove from main data list
            # If it was a new, unsaved snippet, it's just gone.
            # If it was an existing snippet, its file will be marked for saving (implicitly, as its content changes)
            # To explicitly mark a file for resaving even if all its snippets are removed,
            # we might need a more complex tracking of "dirty files".
            # For now, saving will rewrite files based on remaining snippets.
            # If a snippet was not new, its removal means its parent file needs saving.
            if not snippet_to_remove.is_new:
                 # Find a placeholder or any other snippet from the same file to mark modified
                 # This is a bit tricky. The save logic groups by file_path.
                 # A simpler way is to have a set of "dirty_files"
                 # For now, saving will naturally rewrite files if their content has changed.
                 pass # The file will be rewritten if its list of snippets changes.
            num_removed += 1

        self.populate_treeview() # Refresh view
        self.update_status_bar(f"Removed {num_removed} snippet(s). Remember to save changes.")


    def save_yaml_file(self, file_path, matches_list):
        """Save snippets to a YAML file while preserving other content."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Try to preserve existing content
            existing_content = {}
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_content = yaml.safe_load(f) or {}
                        if not isinstance(existing_content, dict):
                            existing_content = {}
                except Exception:
                    existing_content = {}
            
            # Update matches list
            existing_content['matches'] = matches_list or []
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(existing_content, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving {os.path.basename(file_path)}:\n{e}", parent=self.root)
            return False

    def save_all_changes(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Espanso directory not set.", parent=self.root)
            return

        # Group snippets by file_path
        files_to_save = {}
        for snippet in self.all_snippets:
            files_to_save.setdefault(snippet.file_path, []).append(snippet.original_yaml_entry)

        # Handle files that were loaded but now have no snippets
        empty_files = set(self.file_modification_times.keys()) - set(files_to_save.keys())
        for file_path in empty_files:
            files_to_save[file_path] = []

        # Save all files
        num_files_saved = sum(
            1 for file_path, matches in files_to_save.items()
            if self.save_yaml_file(file_path, matches)
        )

        if num_files_saved == len(files_to_save):
            # Reset modification flags after successful save
            for snippet in self.all_snippets:
                snippet.is_new = snippet.is_modified = False
            
            # Reload data and update UI
            self.load_config_data()
            self.update_save_button_state()
            self.update_status_bar(f"Successfully saved changes to {num_files_saved} file(s).")
            messagebox.showinfo("Save Successful", f"Successfully saved changes to {num_files_saved} file(s).", parent=self.root)
        else:
            self.update_status_bar("Some files could not be saved. Check error messages.")


    def sort_column(self, col_name):
        """Sorts the treeview by the clicked column."""
        if not self.all_snippets:
            return

        # Determine sort order
        if self.current_sort_column == col_name:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = col_name
            self.current_sort_reverse = False

        # Define sort key based on column
        if col_name == "category":
            key_func = lambda s: s.category.lower()
        elif col_name == "trigger":
            key_func = lambda s: s.trigger.lower()
        elif col_name == "replace":
            key_func = lambda s: s.replace_text.lower() # Sort by full replace text
        elif col_name == "file_location":
            key_func = lambda s: s.file_path.lower()
        elif col_name == "updated_at":
            key_func = lambda s: s.last_modified_timestamp
        else:
            return # Should not happen

        self.all_snippets.sort(key=key_func, reverse=self.current_sort_reverse)
        self.populate_treeview()

        # Update column header to indicate sort direction (optional visual cue)
        for col in self.tree["columns"]:
            text = col.replace("_", " ").title()
            if col == self.current_sort_column:
                text += " " + ("▼" if self.current_sort_reverse else "▲")
            self.tree.heading(col, text=text) # Re-set heading to refresh command if it was there
            # Re-apply command after changing text
            self.tree.heading(col, command=lambda c=col: self.sort_column(c))

    def on_closing(self):
        if any(s.is_new or s.is_modified for s in self.all_snippets):
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to quit without saving?", parent=self.root):
                self.root.destroy()
            else:
                return # Don't close
        else:
            self.root.destroy()

    def create_new_category(self):
        """Create a new category file."""
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Please open an Espanso directory first.", parent=self.root)
            return

        # Ask for category name
        category_name = simpledialog.askstring(
            "New Category", 
            "Enter new category name (without .yml extension):",
            parent=self.root
        )
        
        if not category_name:
            return

        # Clean the category name (remove spaces, special characters)
        category_name = "".join(c for c in category_name if c.isalnum() or c in "-_").lower()
        if not category_name:
            messagebox.showerror("Error", "Invalid category name.", parent=self.root)
            return

        # Check if category already exists
        file_path = os.path.join(self.espanso_config_dir, f"{category_name}.yml")
        if os.path.exists(file_path):
            messagebox.showerror(
                "Error", 
                f"Category '{category_name}' already exists.", 
                parent=self.root
            )
            return

        # Create the new category file with basic structure
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump({'matches': []}, f, sort_keys=False, allow_unicode=True, default_flow_style=False)
            
            self.update_status_bar(f"Created new category: {category_name}")
            
            # Refresh the data to show the new category
            self.refresh_data()

            # Get the updated category list
            categories = self.get_categories()

            # Update any open SnippetDialog comboboxes
            for child in self.root.winfo_children():
                if isinstance(child, tk.Toplevel):
                    for widget in child.winfo_children():
                        if isinstance(widget, ttk.Combobox) and "category" in str(widget).lower():
                            widget['values'] = categories
            
            # Optionally, open the add snippet dialog with the new category pre-selected
            if messagebox.askyesno(
                "New Category", 
                f"Category '{category_name}' created. Would you like to add a snippet to it now?",
                parent=self.root
            ):
                dialog = SnippetDialog(
                    self.root,
                    "Add New Snippet",
                    categories=categories,  # Pass updated categories list
                    espanso_dir=self.espanso_config_dir
                )
                if hasattr(dialog, 'category_var'):  # Set the new category as selected
                    dialog.category_var.set(category_name)
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to create category file: {e}",
                parent=self.root
            )

if __name__ == "__main__":
    print("Starting Espanso Manager...")
    root = tk.Tk()
    print("Created root window")
    try:
        app = EspansoManagerApp(root)
        print("Created app instance")
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        print("Starting mainloop...")
        root.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        raise  # Re-raise the exception to see the full traceback
