import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import yaml # Requires PyYAML: pip install PyYAML
from datetime import datetime
import platform

# --- Data Model ---
class Snippet:
    """Represents a single Espanso snippet."""
    def __init__(self, trigger, replace_text, file_path, original_yaml_entry=None):
        self.trigger = str(trigger) if trigger is not None else ""
        self.replace_text = str(replace_text) if replace_text is not None else ""
        self.file_path = file_path # Full path to the YML file this snippet belongs to
        
        # Store the full original dict to preserve other keys (e.g., label, vars)
        # This entry is what gets written back to YAML.
        if original_yaml_entry is None:
            self.original_yaml_entry = {'trigger': self.trigger, 'replace': self.replace_text}
        else:
            self.original_yaml_entry = original_yaml_entry
            # Ensure trigger and replace are strings for consistency
            self.original_yaml_entry['trigger'] = str(self.original_yaml_entry.get('trigger', ''))
            self.original_yaml_entry['replace'] = str(self.original_yaml_entry.get('replace', ''))

        self.tree_item_id = None  # To link Treeview item with this object in a specific tab
        
        # State flags
        self.is_new = False
        self.is_modified = False

    def get_display_values_for_tree(self):
        """Values to display in the Treeview columns for this snippet."""
        first_line_replace = self.replace_text.splitlines()[0] if self.replace_text else ""
        if len(self.replace_text.splitlines()) > 1:
            first_line_replace += "..."
        return (self.trigger, first_line_replace)

    def mark_modified(self, new_trigger, new_replace_text):
        """Updates snippet and marks as modified if changes occurred."""
        if self.trigger != new_trigger or self.replace_text != new_replace_text:
            self.trigger = new_trigger
            self.replace_text = new_replace_text
            # Update the original_yaml_entry for saving
            self.original_yaml_entry['trigger'] = new_trigger
            self.original_yaml_entry['replace'] = new_replace_text
            if not self.is_new:
                self.is_modified = True
            return True
        return False

# --- Dialogs ---
class SnippetDialog(simpledialog.Dialog):
    """Dialog for adding or editing a snippet. Category/file is implicit from active tab."""
    def __init__(self, parent, title, existing_snippet=None):
        self.snippet_data = existing_snippet # This is a Snippet object
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Trigger:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.trigger_entry = ttk.Entry(master, width=50)
        self.trigger_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        if self.snippet_data:
            self.trigger_entry.insert(0, self.snippet_data.trigger)

        ttk.Label(master, text="Replace:").grid(row=1, column=0, sticky="nw", padx=5, pady=2)
        self.replace_text = tk.Text(master, width=50, height=10, wrap=tk.WORD)
        self.replace_text.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        if self.snippet_data:
            self.replace_text.insert(tk.END, self.snippet_data.replace_text)
        
        master.grid_columnconfigure(1, weight=1)
        return self.trigger_entry # initial focus

    def apply(self):
        trigger = self.trigger_entry.get().strip()
        replace = self.replace_text.get("1.0", tk.END).strip()

        if not trigger:
            messagebox.showerror("Error", "Trigger cannot be empty.", parent=self)
            self.result = None 
            return
        
        self.result = {"trigger": trigger, "replace_text": replace}

class NewFileDialog(simpledialog.Dialog):
    """Dialog for creating a new Espanso YAML file."""
    def __init__(self, parent, title, espanso_match_dir):
        self.espanso_match_dir = espanso_match_dir
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="New File Name (e.g., 'my_snippets'):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = ttk.Entry(master, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        # Optional: Add subdirectory support here later if needed
        # ttk.Label(master, text="Subdirectory (optional, relative to match dir):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        # self.subdir_entry = ttk.Entry(master, width=40)
        # self.subdir_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        master.grid_columnconfigure(1, weight=1)
        return self.name_entry

    def validate_filename(self, name):
        if not name:
            return False, "Filename cannot be empty."
        if any(c in name for c in r'/\:*?"<>|'): # Basic invalid char check
            return False, "Filename contains invalid characters."
        if name.endswith(".yml") or name.endswith(".yaml"):
            return False, "Do not include .yml or .yaml extension; it will be added."
        return True, ""

    def apply(self):
        raw_name = self.name_entry.get().strip()
        # subdir = self.subdir_entry.get().strip() # For future subdirectory support

        is_valid, error_msg = self.validate_filename(raw_name)
        if not is_valid:
            messagebox.showerror("Invalid Filename", error_msg, parent=self)
            self.result = None
            return

        filename = f"{raw_name}.yml"
        # For now, create in the root of the match directory.
        # Later, can use `subdir` to place it deeper.
        # target_dir = os.path.join(self.espanso_match_dir, subdir)
        target_dir = self.espanso_match_dir 
        
        file_path = os.path.join(target_dir, filename)

        if os.path.exists(file_path):
            messagebox.showerror("Error", f"File '{filename}' already exists in the match directory.", parent=self)
            self.result = None
            return
        
        self.result = {"file_path": file_path, "display_name": raw_name}


# --- Main Application ---
class EspansoManagerApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("Espanso Manager (Tabbed)")
        self.root.geometry("1200x700") 

        self.espanso_config_dir = ""
        # self.all_snippets = [] # Replaced by snippets_by_file_path
        self.snippets_by_file_path = {} # Key: full_file_path, Value: list of Snippet objects for that file
        self.tab_data_map = {}          # Key: tab_id (from notebook), Value: dict with file_path, tree, display_name, file_mtime
        
        self.current_sort_column = None # Per-tab sorting state is more complex, this will be for active tab
        self.current_sort_reverse = False

        self.create_widgets()
        self.load_initial_config()

    def get_default_espanso_config_path(self):
        system = platform.system()
        if system == "Darwin":
            return os.path.expanduser("~/Library/Application Support/espanso/match")
        elif system == "Linux":
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                return os.path.join(xdg_config_home, "espanso/match")
            return os.path.expanduser("~/.config/espanso/match")
        return None

    def create_widgets(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Espanso Dir", command=self.select_espanso_directory)
        filemenu.add_command(label="Refresh Data (F5)", command=self.refresh_all_tabs)
        filemenu.add_separator()
        filemenu.add_command(label="Save All Changes (Cmd/Ctrl+S)", command=self.save_all_changes)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

        self.root.bind_all("<Command-s>", lambda event: self.save_all_changes())
        self.root.bind_all("<Control-s>", lambda event: self.save_all_changes())
        self.root.bind("<F5>", lambda event: self.refresh_all_tabs())

        top_frame = ttk.Frame(self.root, padding=(10,10,10,0))
        top_frame.pack(expand=False, fill=tk.X)

        self.add_button = ttk.Button(top_frame, text="Add Snippet to Tab", command=self.add_snippet_to_active_tab)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.remove_button = ttk.Button(top_frame, text="Remove Selected from Tab", command=self.remove_selected_snippet_from_active_tab)
        self.remove_button.pack(side=tk.LEFT, padx=5)
        
        self.new_file_button = ttk.Button(top_frame, text="New File/Category", command=self.handle_new_file_creation)
        self.new_file_button.pack(side=tk.LEFT, padx=5)

        main_frame = ttk.Frame(self.root, padding=(10,0,10,10)) # Less top padding as it's in top_frame
        main_frame.pack(expand=True, fill=tk.BOTH)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill=tk.BOTH)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        self.status_bar_text = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar("Welcome to Espanso Manager.")

    def update_status_bar(self, message):
        self.status_bar_text.set(message)

    def load_initial_config(self):
        default_path = self.get_default_espanso_config_path()
        if default_path and os.path.isdir(default_path):
            self.espanso_config_dir = default_path
            self.load_all_files_into_tabs()
        else:
            self.update_status_bar("Default Espanso config directory not found. Select via File > Open Espanso Dir.")
            messagebox.showinfo("Info", "Default Espanso config directory not found. Use 'File > Open Espanso Dir'.", parent=self.root)

    def select_espanso_directory(self):
        dir_path = filedialog.askdirectory(title="Select Espanso Match Directory", initialdir=os.path.expanduser("~"))
        if dir_path:
            if os.path.basename(dir_path) != "match":
                messagebox.showwarning("Warning", "Selected directory isn't named 'match'. Ensure it's correct.", parent=self.root)
            self.espanso_config_dir = dir_path
            self.load_all_files_into_tabs()
        else:
            self.update_status_bar("Directory selection cancelled.")

    def refresh_all_tabs(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Espanso directory not set.", parent=self.root)
            return
        
        # Check for unsaved changes before refresh
        has_unsaved = False
        for snippets_list in self.snippets_by_file_path.values():
            if any(s.is_new or s.is_modified for s in snippets_list):
                has_unsaved = True
                break
        if has_unsaved:
            if not messagebox.askyesno("Unsaved Changes", "Unsaved changes exist. Refresh and lose them?", parent=self.root):
                return
        
        self.load_all_files_into_tabs()
        self.update_status_bar("Data refreshed.")


    def load_all_files_into_tabs(self):
        if not self.espanso_config_dir or not os.path.isdir(self.espanso_config_dir):
            self.update_status_bar("Espanso directory not set or invalid.")
            return

        # Clear existing tabs and data
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.snippets_by_file_path.clear()
        self.tab_data_map.clear()

        file_count = 0
        snippet_count_total = 0

        for root_dir, _, files in os.walk(self.espanso_config_dir):
            for filename in files:
                if filename.endswith((".yml", ".yaml")):
                    file_path = os.path.join(root_dir, filename)
                    relative_path = os.path.relpath(file_path, self.espanso_config_dir) # Used for tab title
                    
                    current_file_snippets = []
                    self.snippets_by_file_path[file_path] = current_file_snippets # Initialize list for this file
                    
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))

                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = yaml.safe_load(f)
                        
                        if content and isinstance(content, dict) and "matches" in content:
                            matches_list_yaml = content.get("matches", [])
                            if isinstance(matches_list_yaml, list):
                                for entry in matches_list_yaml:
                                    if isinstance(entry, dict) and "trigger" in entry: # 'replace' is optional for some types
                                        snippet = Snippet(
                                            trigger=entry.get("trigger"),
                                            replace_text=entry.get("replace"), # Can be None
                                            file_path=file_path,
                                            original_yaml_entry=entry.copy()
                                        )
                                        current_file_snippets.append(snippet)
                                        snippet_count_total += 1
                            else:
                                print(f"Warning: 'matches' in {filename} is not a list.")
                        
                        self.add_tab_for_file(file_path, relative_path, file_mtime, current_file_snippets)
                        file_count += 1

                    except yaml.YAMLError as e:
                        messagebox.showerror("YAML Error", f"Error parsing {relative_path}:\n{e}", parent=self.root)
                    except Exception as e:
                        messagebox.showerror("Error", f"Error reading {relative_path}:\n{e}", parent=self.root)
        
        if not self.notebook.tabs(): # If no files found or all failed
             self.update_status_bar(f"No YAML files found in {self.espanso_config_dir}.")
        else:
            # Trigger tab change for the first tab to update status bar correctly
            first_tab_id = self.notebook.tabs()[0]
            self.notebook.select(first_tab_id) # This should trigger on_tab_changed
            # If on_tab_changed isn't triggered automatically by programmatic select on init, call manually:
            if self.tab_data_map.get(first_tab_id):
                 self.on_tab_changed(None) # Pass dummy event
            else: # Fallback if tab map not ready
                 self.update_status_bar(f"Loaded {snippet_count_total} snippets in {file_count} file(s).")


    def add_tab_for_file(self, file_path, display_name, file_mtime, snippets_list_ref, select_tab=False):
        """Adds a new tab to the notebook for a given file."""
        tab_frame = ttk.Frame(self.notebook, padding=5)
        self.notebook.add(tab_frame, text=display_name)
        tab_id = self.notebook.tabs()[-1] # Get ID of the newly added tab

        columns = ("trigger", "replace")
        tree = ttk.Treeview(tab_frame, columns=columns, show="headings", selectmode="extended")
        col_widths = {"trigger": 300, "replace": 600}
        for col in columns:
            tree.heading(col, text=col.title(), command=lambda c=col, tid=tab_id: self.sort_column_in_tab(c, tid))
            tree.column(col, width=col_widths[col], stretch=True)
        
        v_scroll = ttk.Scrollbar(tab_frame, orient=tk.VERTICAL, command=tree.yview)
        h_scroll = ttk.Scrollbar(tab_frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(0, weight=1)

        tree.bind("<Double-1>", lambda event, tid=tab_id: self.on_double_click_edit_in_tab(event, tid))
        
        self.tab_data_map[tab_id] = {
            "file_path": file_path,
            "display_name": display_name,
            "tree": tree,
            "file_mtime": file_mtime
        }
        # snippets_list_ref is already in self.snippets_by_file_path[file_path]
        self.populate_treeview_for_tab(tree, snippets_list_ref)

        if select_tab:
            self.notebook.select(tab_id)
        return tab_id


    def populate_treeview_for_tab(self, tree, snippets_list):
        for item in tree.get_children():
            tree.delete(item)
        
        for i, snippet in enumerate(snippets_list):
            values = snippet.get_display_values_for_tree()
            # Use a unique IID for each snippet within this tree
            tree_item_id = tree.insert("", tk.END, values=values, iid=f"file_snippet_{i}")
            snippet.tree_item_id = tree_item_id # This might be an issue if snippet is in multiple views; it's not here.

    def get_active_tab_info(self):
        """Returns the data dict for the currently active tab, or None."""
        try:
            current_tab_id = self.notebook.select()
            if current_tab_id:
                return self.tab_data_map.get(current_tab_id)
        except tk.TclError: # No tab selected or notebook empty
            return None
        return None

    def on_tab_changed(self, event): # event can be None if called manually
        active_tab_info = self.get_active_tab_info()
        if active_tab_info:
            file_path = active_tab_info["file_path"]
            display_name = active_tab_info["display_name"]
            mtime = active_tab_info["file_mtime"]
            snippets_list = self.snippets_by_file_path.get(file_path, [])
            self.update_status_bar(f"File: {display_name} ({len(snippets_list)} snippets) | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            # Reset sort state for new tab to avoid confusion, or implement per-tab sort state
            self.current_sort_column = None 
            self.current_sort_reverse = False
        else:
            self.update_status_bar("No file tab selected.")

    def add_snippet_to_active_tab(self):
        active_tab_info = self.get_active_tab_info()
        if not active_tab_info:
            messagebox.showerror("Error", "No active file tab selected.", parent=self.root)
            return

        dialog = SnippetDialog(self.root, "Add New Snippet")
        if dialog.result:
            data = dialog.result # Contains 'trigger', 'replace_text'
            active_file_path = active_tab_info["file_path"]
            snippets_list_for_file = self.snippets_by_file_path[active_file_path]

            # Check for duplicate trigger in the current file
            if any(s.trigger == data["trigger"] for s in snippets_list_for_file):
                messagebox.showerror("Error", f"Trigger '{data['trigger']}' already exists in {active_tab_info['display_name']}.", parent=self.root)
                return

            new_snippet = Snippet(
                trigger=data["trigger"],
                replace_text=data["replace_text"],
                file_path=active_file_path
                # original_yaml_entry will be created by default in Snippet constructor
            )
            new_snippet.is_new = True
            
            snippets_list_for_file.append(new_snippet)
            self.populate_treeview_for_tab(active_tab_info["tree"], snippets_list_for_file)
            
            # Auto-select and scroll
            if new_snippet.tree_item_id and active_tab_info["tree"].exists(new_snippet.tree_item_id):
                active_tab_info["tree"].selection_set(new_snippet.tree_item_id)
                active_tab_info["tree"].see(new_snippet.tree_item_id)
            self.update_status_bar(f"Added '{data['trigger']}' to {active_tab_info['display_name']}. Save changes.")


    def on_double_click_edit_in_tab(self, event, tab_id):
        tab_info = self.tab_data_map.get(tab_id)
        if not tab_info: return

        tree = tab_info["tree"]
        selected_item_id = tree.focus()
        if not selected_item_id: return

        snippets_list_for_file = self.snippets_by_file_path[tab_info["file_path"]]
        selected_snippet = None
        # Find by tree_item_id (which we set as "file_snippet_{index}")
        try:
            # This relies on the iid format. A more robust way would be to store a map or iterate.
            idx = int(selected_item_id.split("_")[-1])
            selected_snippet = snippets_list_for_file[idx]
        except (ValueError, IndexError):
             # Fallback: iterate to find by tree_item_id if IID isn't index based as expected
            for snip in snippets_list_for_file:
                if snip.tree_item_id == selected_item_id:
                    selected_snippet = snip
                    break
        
        if not selected_snippet:
            messagebox.showerror("Error", "Could not find selected snippet data.", parent=self.root)
            return

        dialog = SnippetDialog(self.root, f"Edit Snippet: {selected_snippet.trigger}", existing_snippet=selected_snippet)
        if dialog.result:
            updated_data = dialog.result # 'trigger', 'replace_text'
            
            # Check for trigger collision if trigger changed
            if selected_snippet.trigger != updated_data["trigger"]:
                if any(s != selected_snippet and s.trigger == updated_data["trigger"] for s in snippets_list_for_file):
                    messagebox.showerror("Error", f"Trigger '{updated_data['trigger']}' already exists in this file.", parent=self.root)
                    return

            if selected_snippet.mark_modified(updated_data["trigger"], updated_data["replace_text"]):
                self.populate_treeview_for_tab(tree, snippets_list_for_file)
                # Re-select and see
                if selected_snippet.tree_item_id and tree.exists(selected_snippet.tree_item_id):
                    tree.selection_set(selected_snippet.tree_item_id)
                    tree.see(selected_snippet.tree_item_id)
                self.update_status_bar(f"Modified '{selected_snippet.trigger}'. Save changes.")


    def remove_selected_snippet_from_active_tab(self):
        active_tab_info = self.get_active_tab_info()
        if not active_tab_info:
            messagebox.showinfo("Info", "No active tab selected.", parent=self.root)
            return

        tree = active_tab_info["tree"]
        selected_item_ids = tree.selection()
        if not selected_item_ids:
            messagebox.showinfo("Info", "No snippet selected in the active tab.", parent=self.root)
            return

        if not messagebox.askyesno("Confirm Deletion", f"Remove {len(selected_item_ids)} snippet(s) from {active_tab_info['display_name']}?\nThis is permanent upon saving.", parent=self.root):
            return

        snippets_list_for_file = self.snippets_by_file_path[active_tab_info["file_path"]]
        
        # Collect snippets to remove based on tree selection.
        # Need to map tree IIDs back to list indices carefully, especially if sorted.
        # It's safer to remove from a copy or iterate carefully.
        indices_to_remove = []
        for item_id in selected_item_ids:
            try:
                # This simple index mapping from IID works if tree is not sorted or if IIDs are stable.
                # If sorting changes IIDs or their meaning, this needs to be more robust.
                # For now, assume IIDs are "file_snippet_{original_index_at_population}"
                idx = int(item_id.split("_")[-1]) 
                indices_to_remove.append(idx)
            except (ValueError, IndexError):
                # Fallback: if IID is not index, find the snippet object by iterating
                # This part is tricky if tree_item_id is not perfectly managed.
                # For now, we assume the simple index based IID.
                print(f"Warning: Could not map tree item ID {item_id} to an index directly.")
                # A more robust way: iterate all snippets in list, find one with matching tree_item_id, then remove that object.
                # This is safer if tree_item_id is reliably unique per snippet object.
                found_snippet = None
                for snip_idx, snip_obj in enumerate(snippets_list_for_file):
                    if snip_obj.tree_item_id == item_id:
                        indices_to_remove.append(snip_idx) # Store index to remove
                        break
        
        # Remove by index, highest first to avoid shifting issues
        indices_to_remove.sort(reverse=True)
        num_removed = 0
        for idx in indices_to_remove:
            if 0 <= idx < len(snippets_list_for_file):
                removed_snippet = snippets_list_for_file.pop(idx)
                # If not new, its removal means the file is dirty.
                # This is implicitly handled as the list of snippets for the file changes.
                num_removed +=1
            else:
                print(f"Warning: Stale index {idx} during removal.")


        if num_removed > 0:
            self.populate_treeview_for_tab(tree, snippets_list_for_file)
            self.update_status_bar(f"Removed {num_removed} snippet(s) from {active_tab_info['display_name']}. Save changes.")


    def save_all_changes(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Espanso directory not set.", parent=self.root)
            return

        num_files_processed = 0
        for file_path, snippets_list in self.snippets_by_file_path.items():
            # Check if this file actually needs saving (any new/modified snippets, or if snippets were removed)
            # A simple check: if the file exists, compare current state to a hypothetical saved state.
            # More simply: if any snippet is_new, is_modified, or if the count of snippets differs from loaded.
            # For now, we rewrite if the file is in our map, to handle deletions too.
            # A more refined check could be added later.

            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                # Prepare the list of matches for YAML
                matches_yaml_list = [s.original_yaml_entry for s in snippets_list]

                # Read existing full file content to preserve other top-level keys
                # This is a simplified approach. True comment/style preservation is hard with PyYAML.
                file_content_to_write = {}
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f_read:
                            file_content_to_write = yaml.safe_load(f_read)
                            if not isinstance(file_content_to_write, dict):
                                file_content_to_write = {} 
                    except Exception: # On read error, start with fresh dict
                        file_content_to_write = {}
                
                # Update or set the 'matches' list
                file_content_to_write['matches'] = matches_yaml_list
                
                # If matches list is empty and no other keys, write "matches: []"
                if not file_content_to_write and not matches_yaml_list:
                    file_content_to_write = {'matches': []}


                with open(file_path, 'w', encoding='utf-8') as f_write:
                    yaml.dump(file_content_to_write, f_write, sort_keys=False, allow_unicode=True, default_flow_style=False, Dumper=yaml.SafeDumper)
                
                num_files_processed += 1
                
                # Update mtime for the tab if it's currently loaded
                for tab_id, tab_data in self.tab_data_map.items():
                    if tab_data["file_path"] == file_path:
                        tab_data["file_mtime"] = datetime.fromtimestamp(os.path.getmtime(file_path))
                        break
            
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving {os.path.basename(file_path)}:\n{e}", parent=self.root)
                return # Stop on first error

        # Reset modification flags for all snippets in all files
        for snippets_list in self.snippets_by_file_path.values():
            for snippet in snippets_list:
                snippet.is_new = False
                snippet.is_modified = False
        
        self.update_status_bar(f"Successfully saved changes to {num_files_processed} file(s).")
        # No need to reload all tabs, just update mtimes and clear flags.
        # Refresh current tab's status bar message
        self.on_tab_changed(None) 
        messagebox.showinfo("Save Successful", f"Changes saved to {num_files_processed} file(s).", parent=self.root)


    def sort_column_in_tab(self, col_name, tab_id):
        tab_info = self.tab_data_map.get(tab_id)
        if not tab_info: return

        tree = tab_info["tree"]
        snippets_list = self.snippets_by_file_path.get(tab_info["file_path"])
        if not snippets_list: return

        if self.current_sort_column == col_name: # Using app-wide sort state for active tab
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = col_name
            self.current_sort_reverse = False

        if col_name == "trigger":
            key_func = lambda s: s.trigger.lower()
        elif col_name == "replace":
            key_func = lambda s: s.replace_text.lower()
        else:
            return

        snippets_list.sort(key=key_func, reverse=self.current_sort_reverse)
        self.populate_treeview_for_tab(tree, snippets_list)

        # Update column headers in the specific tree
        for col_h in tree["columns"]:
            text = col_h.title()
            if col_h == self.current_sort_column: # Check against the column name passed
                text += " " + ("▼" if self.current_sort_reverse else "▲")
            tree.heading(col_h, text=text, command=lambda c=col_h, tid=tab_id: self.sort_column_in_tab(c, tid))


    def handle_new_file_creation(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Please open an Espanso directory first.", parent=self.root)
            return

        dialog = NewFileDialog(self.root, "Create New Espanso File", self.espanso_config_dir)
        if dialog.result:
            new_file_path = dialog.result["file_path"]
            display_name = dialog.result["display_name"] # This is just filename stem for now

            # Create the file on disk immediately as an empty match file
            try:
                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                with open(new_file_path, 'w', encoding='utf-8') as f:
                    yaml.dump({'matches': []}, f, sort_keys=False)
                
                # Add to internal tracking and create a tab
                self.snippets_by_file_path[new_file_path] = []
                new_file_mtime = datetime.fromtimestamp(os.path.getmtime(new_file_path))
                
                # Use relpath for tab title if it's inside espanso_config_dir
                try:
                    tab_display_name = os.path.relpath(new_file_path, self.espanso_config_dir)
                except ValueError: # if new_file_path is not under espanso_config_dir (should not happen with current logic)
                    tab_display_name = os.path.basename(new_file_path)

                self.add_tab_for_file(new_file_path, tab_display_name, new_file_mtime, self.snippets_by_file_path[new_file_path], select_tab=True)
                self.update_status_bar(f"Created new file: {tab_display_name}. Add snippets and save.")

            except Exception as e:
                messagebox.showerror("Error", f"Could not create file {new_file_path}:\n{e}", parent=self.root)


    def on_closing(self):
        has_unsaved = False
        for snippets_list in self.snippets_by_file_path.values():
            if any(s.is_new or s.is_modified for s in snippets_list):
                has_unsaved = True
                break
        
        if has_unsaved:
            if messagebox.askyesno("Unsaved Changes", "Unsaved changes exist. Quit without saving?", parent=self.root):
                self.root.destroy()
            # else: user chose not to quit
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = EspansoManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
