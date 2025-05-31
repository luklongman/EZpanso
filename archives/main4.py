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
        
        if original_yaml_entry is None:
            self.original_yaml_entry = {'trigger': self.trigger, 'replace': self.replace_text}
        else:
            self.original_yaml_entry = original_yaml_entry
            self.original_yaml_entry['trigger'] = str(self.original_yaml_entry.get('trigger', ''))
            self.original_yaml_entry['replace'] = str(self.original_yaml_entry.get('replace', ''))

        self.tree_item_iid_str = None # String version of id(self) used as IID in Treeview
        
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
            self.original_yaml_entry['trigger'] = new_trigger
            self.original_yaml_entry['replace'] = new_replace_text
            if not self.is_new:
                self.is_modified = True
            return True
        return False

# --- Dialogs ---
class EditSnippetDialog(simpledialog.Dialog):
    """Dialog for *editing* an existing snippet."""
    def __init__(self, parent, title, existing_snippet): 
        self.snippet_data = existing_snippet 
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Trigger:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.trigger_entry = ttk.Entry(master, width=50)
        self.trigger_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        self.trigger_entry.insert(0, self.snippet_data.trigger)

        ttk.Label(master, text="Replace:").grid(row=1, column=0, sticky="nw", padx=5, pady=2)
        self.replace_text_widget = tk.Text(master, width=50, height=10, wrap=tk.WORD) 
        self.replace_text_widget.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
        self.replace_text_widget.insert(tk.END, self.snippet_data.replace_text)
        
        master.grid_columnconfigure(1, weight=1)
        return self.trigger_entry 

    def apply(self):
        trigger = self.trigger_entry.get().strip()
        replace = self.replace_text_widget.get("1.0", tk.END).strip()

        if not trigger:
            messagebox.showerror("Error", "Trigger cannot be empty.", parent=self)
            self.result = None 
            return
        
        self.result = {"trigger": trigger, "replace_text": replace}

class NewCategoryDialog(simpledialog.Dialog): 
    """Dialog for creating a new Espanso YAML file (category)."""
    def __init__(self, parent, title, espanso_match_dir):
        self.espanso_match_dir = espanso_match_dir
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="New Category Name (e.g., 'my_work_snippets'):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.name_entry = ttk.Entry(master, width=40)
        self.name_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        
        master.grid_columnconfigure(1, weight=1)
        return self.name_entry

    def validate_filename(self, name):
        if not name:
            return False, "Category name cannot be empty."
        if any(c in name for c in r'/\:*?"<>|'): 
            return False, "Category name contains invalid characters."
        if name.endswith((".yml", ".yaml")):
            return False, "Do not include .yml or .yaml extension; it will be added."
        return True, ""

    def apply(self):
        raw_name = self.name_entry.get().strip()
        is_valid, error_msg = self.validate_filename(raw_name)
        if not is_valid:
            messagebox.showerror("Invalid Category Name", error_msg, parent=self)
            self.result = None
            return

        filename = f"{raw_name}.yml"
        file_path = os.path.join(self.espanso_match_dir, filename)

        if os.path.exists(file_path):
            messagebox.showerror("Error", f"A category file '{filename}' already exists.", parent=self)
            self.result = None
            return
        
        self.result = {"file_path": file_path, "display_name": filename}


# --- Main Application ---
class EspansoManagerApp:
    def __init__(self, root_tk):
        self.root = root_tk
        self.root.title("Espanso Manager") 
        self.root.geometry("1200x700") 

        self.espanso_config_dir = ""
        self.snippets_by_file_path = {} 
        self.category_dropdown_map = {} 
        self.active_file_path = None    

        self.current_sort_column = None
        self.current_sort_reverse = False

        self.create_widgets()
        self.load_initial_config()

    def get_default_espanso_config_path(self):
        system = platform.system()
        if system == "Darwin": # macOS
            return os.path.expanduser("~/Library/Application Support/espanso/match")
        elif system == "Linux":
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                return os.path.join(xdg_config_home, "espanso/match")
            return os.path.expanduser("~/.config/espanso/match")
        return None # Unknown OS or not implemented

    def create_widgets(self):
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open Espanso Dir", command=self.select_espanso_directory)
        filemenu.add_command(label="Refresh Data (F5)", command=self.refresh_all_categories)
        filemenu.add_separator()
        filemenu.add_command(label="Save All Changes (Cmd/Ctrl+S)", command=self.save_all_changes)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=filemenu)
        self.root.config(menu=menubar)

        self.root.bind_all("<Command-s>", lambda event: self.save_all_changes())
        self.root.bind_all("<Control-s>", lambda event: self.save_all_changes())
        self.root.bind("<F5>", lambda event: self.refresh_all_categories())

        top_action_frame = ttk.Frame(self.root, padding=(10,10,10,0))
        top_action_frame.pack(expand=False, fill=tk.X)

        ttk.Label(top_action_frame, text="Category:").pack(side=tk.LEFT, padx=(0,2))
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(top_action_frame, textvariable=self.category_var, state="readonly", width=35)
        self.category_dropdown.pack(side=tk.LEFT, padx=(0,5))
        self.category_dropdown.bind("<<ComboboxSelected>>", self.on_category_selected)

        self.new_category_button = ttk.Button(top_action_frame, text="New Category", command=self.handle_new_category_creation)
        self.new_category_button.pack(side=tk.LEFT, padx=2)

        self.remove_category_button = ttk.Button(top_action_frame, text="Remove Selected Category", command=self.handle_remove_category)
        self.remove_category_button.pack(side=tk.LEFT, padx=2)
        
        main_content_frame = ttk.Frame(self.root, padding=(10,5,10,0))
        main_content_frame.pack(expand=True, fill=tk.BOTH)

        columns = ("trigger", "replace")
        self.tree = ttk.Treeview(main_content_frame, columns=columns, show="headings", selectmode="extended")
        col_widths = {"trigger": 300, "replace": 600} 
        for col in columns:
            self.tree.heading(col, text=col.title(), command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=col_widths[col], stretch=True)
        
        v_scroll = ttk.Scrollbar(main_content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(main_content_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        main_content_frame.grid_rowconfigure(0, weight=1)
        main_content_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.on_double_click_edit)

        snippet_entry_frame = ttk.Frame(self.root, padding=(10,5,10,5)) 
        snippet_entry_frame.pack(expand=False, fill=tk.X)

        ttk.Label(snippet_entry_frame, text="New Trigger:").grid(row=0, column=0, padx=(0,2), pady=2, sticky="w")
        self.new_trigger_entry = ttk.Entry(snippet_entry_frame) 
        self.new_trigger_entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        ttk.Label(snippet_entry_frame, text="New Replace:").grid(row=1, column=0, padx=(0,2), pady=2, sticky="nw") 
        self.new_replace_text = tk.Text(snippet_entry_frame, height=3, wrap=tk.WORD) 
        self.new_replace_text.grid(row=1, column=1, columnspan=3, padx=2, pady=2, sticky="ew") 

        self.add_new_snippet_button = ttk.Button(snippet_entry_frame, text="Add This Snippet", command=self.add_snippet_from_entry_fields)
        self.add_new_snippet_button.grid(row=0, column=2, rowspan=2, padx=(5,0), pady=2, sticky="ns") 

        snippet_entry_frame.grid_columnconfigure(1, weight=1) 
        snippet_entry_frame.grid_columnconfigure(3, minsize=0) 

        self.remove_snippet_button = ttk.Button(self.root, text="Remove Selected Snippet(s) from Category", command=self.remove_selected_snippet)
        self.remove_snippet_button.pack(pady=(0,5), padx=10, fill=tk.X)

        self.status_bar_text = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.update_status_bar("Welcome to Espanso Manager.")

    def _set_busy_cursor(self, busy=True):
        """Helper to set/unset busy cursor."""
        if busy:
            self.root.config(cursor="watch")
        else:
            self.root.config(cursor="")
        self.root.update_idletasks()


    def update_status_bar(self, message):
        self.status_bar_text.set(message)
        self.root.update_idletasks() # Ensure status bar updates immediately

    def load_initial_config(self):
        self._set_busy_cursor(True)
        self.update_status_bar("Loading initial configuration...")
        try:
            default_path = self.get_default_espanso_config_path()
            if default_path and os.path.isdir(default_path):
                self.espanso_config_dir = default_path
                self.load_all_categories_into_dropdown() # This will set its own status
            else:
                self.update_status_bar("Default Espanso config directory not found. Select via File > Open Espanso Dir.")
                messagebox.showinfo("Info", "Default Espanso config directory not found. Use 'File > Open Espanso Dir'.", parent=self.root)
        finally:
            self._set_busy_cursor(False)


    def select_espanso_directory(self):
        self._set_busy_cursor(True)
        self.update_status_bar("Selecting Espanso directory...")
        try:
            dir_path = filedialog.askdirectory(title="Select Espanso Match Directory", initialdir=os.path.expanduser("~"))
            if dir_path:
                self.espanso_config_dir = dir_path
                self.load_all_categories_into_dropdown() # This handles its own status messages
            else:
                self.update_status_bar("Directory selection cancelled.")
        finally:
            self._set_busy_cursor(False)


    def refresh_all_categories(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Espanso directory not set.", parent=self.root)
            return
        
        has_unsaved = False
        for snippets_list in self.snippets_by_file_path.values():
            if any(s.is_new or s.is_modified for s in snippets_list):
                has_unsaved = True
                break
        if has_unsaved:
            if not messagebox.askyesno("Unsaved Changes", "Unsaved changes exist. Refresh and lose them?", parent=self.root):
                return
        
        self._set_busy_cursor(True)
        self.update_status_bar("Refreshing data...")
        try:
            current_selected_display_name = self.category_var.get()
            self.load_all_categories_into_dropdown(select_display_name=current_selected_display_name)
            self.update_status_bar("Data refreshed.")
        finally:
            self._set_busy_cursor(False)


    def load_all_categories_into_dropdown(self, select_display_name=None):
        self._set_busy_cursor(True)
        self.update_status_bar("Loading categories...")
        try:
            if not self.espanso_config_dir or not os.path.isdir(self.espanso_config_dir):
                self.update_status_bar("Espanso directory not set or invalid.")
                self.category_dropdown['values'] = []
                self.category_var.set("")
                self.active_file_path = None
                self.snippets_by_file_path.clear()
                self.category_dropdown_map.clear()
                self.populate_treeview_for_active_category() 
                return

            self.snippets_by_file_path.clear()
            self.category_dropdown_map.clear()
            
            category_display_names = []
            snippet_count_total = 0

            for root_dir, _, files in os.walk(self.espanso_config_dir):
                for filename in sorted(files): 
                    if filename.endswith((".yml", ".yaml")):
                        file_path = os.path.join(root_dir, filename)
                        display_name = os.path.relpath(file_path, self.espanso_config_dir)
                        
                        self.category_dropdown_map[display_name] = file_path
                        category_display_names.append(display_name)
                        
                        current_file_snippets = []
                        self.snippets_by_file_path[file_path] = current_file_snippets
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = yaml.safe_load(f)
                            
                            if content and isinstance(content, dict) and "matches" in content:
                                matches_list_yaml = content.get("matches", [])
                                if isinstance(matches_list_yaml, list):
                                    for entry in matches_list_yaml:
                                        if isinstance(entry, dict) and "trigger" in entry:
                                            snippet = Snippet(
                                                trigger=entry.get("trigger"),
                                                replace_text=entry.get("replace"),
                                                file_path=file_path,
                                                original_yaml_entry=entry.copy()
                                            )
                                            snippet.tree_item_iid_str = str(id(snippet)) 
                                            current_file_snippets.append(snippet)
                                            snippet_count_total += 1
                        except Exception as e:
                            messagebox.showerror("Error", f"Error processing {display_name}:\n{e}", parent=self.root)
                            if display_name in self.category_dropdown_map: del self.category_dropdown_map[display_name]
                            if display_name in category_display_names: category_display_names.remove(display_name)
                            if file_path in self.snippets_by_file_path: del self.snippets_by_file_path[file_path]

            self.category_dropdown['values'] = sorted(category_display_names)

            if category_display_names:
                if select_display_name and select_display_name in category_display_names:
                    self.category_var.set(select_display_name)
                else:
                    self.category_var.set(category_display_names[0]) 
                self.on_category_selected(called_from_load=True) # Pass flag to avoid double status update
            else:
                self.category_var.set("")
                self.active_file_path = None
                self.populate_treeview_for_active_category() 
                self.update_status_bar(f"No YAML category files found in {self.espanso_config_dir}.")
            
            if not (select_display_name and category_display_names):
                 self.update_status_bar(f"Loaded {snippet_count_total} snippets from {len(category_display_names)} categories.")
        finally:
            self._set_busy_cursor(False)


    def on_category_selected(self, event=None, called_from_load=False):
        self._set_busy_cursor(True)
        # Status will be updated within this block or by populate_treeview
        try:
            selected_display_name = self.category_var.get()
            if not selected_display_name:
                self.active_file_path = None
                self.populate_treeview_for_active_category() 
                if not called_from_load: self.update_status_bar("No category selected.")
                return

            self.active_file_path = self.category_dropdown_map.get(selected_display_name)
            if self.active_file_path:
                self.populate_treeview_for_active_category() # This will update status based on content
                # Status update now primarily handled in populate_treeview or its callers
            else: 
                if not called_from_load: self.update_status_bar(f"Error: Could not find file for category {selected_display_name}.")
                self.populate_treeview_for_active_category() 
            
            self.current_sort_column = None 
            self.current_sort_reverse = False
        finally:
            self._set_busy_cursor(False)


    def populate_treeview_for_active_category(self):
        # Efficiently delete all existing items
        if self.tree.get_children(): # Check if there are any children to delete
            self.tree.delete(*self.tree.get_children())
        
        if not self.active_file_path or self.active_file_path not in self.snippets_by_file_path:
            selected_display_name = self.category_var.get()
            if selected_display_name: # If a category is selected but no data (e.g. error)
                 self.update_status_bar(f"Category: {selected_display_name} (No snippets to display or error)")
            # else: status already handled by caller (e.g. "No category selected")
            return

        snippets_list = self.snippets_by_file_path[self.active_file_path]
        for snippet_obj in snippets_list:
            values = snippet_obj.get_display_values_for_tree()
            if not snippet_obj.tree_item_iid_str: snippet_obj.tree_item_iid_str = str(id(snippet_obj))
            self.tree.insert("", tk.END, values=values, iid=snippet_obj.tree_item_iid_str)
        
        # Update status after populating
        selected_display_name = self.category_var.get()
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(self.active_file_path))
            self.update_status_bar(f"Category: {selected_display_name} ({len(snippets_list)} snippets) | Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        except FileNotFoundError:
             self.update_status_bar(f"Category: {selected_display_name} (File not found, {len(snippets_list)} in memory)")
        except Exception: # Catch other potential os.path.getmtime errors
             self.update_status_bar(f"Category: {selected_display_name} ({len(snippets_list)} snippets) | Modified: Unknown")


    def add_snippet_from_entry_fields(self):
        if not self.active_file_path:
            messagebox.showerror("Error", "No category selected to add snippet to.", parent=self.root)
            return

        trigger = self.new_trigger_entry.get().strip()
        replace_text = self.new_replace_text.get("1.0", tk.END).strip()

        if not trigger:
            messagebox.showerror("Error", "Trigger cannot be empty.", parent=self.root)
            return

        snippets_list_for_file = self.snippets_by_file_path[self.active_file_path]
        if any(s.trigger == trigger for s in snippets_list_for_file):
            messagebox.showerror("Error", f"Trigger '{trigger}' already exists in this category.", parent=self.root)
            return

        new_snippet = Snippet(
            trigger=trigger,
            replace_text=replace_text,
            file_path=self.active_file_path
        )
        new_snippet.is_new = True
        new_snippet.tree_item_iid_str = str(id(new_snippet)) 
        
        snippets_list_for_file.append(new_snippet)
        self.populate_treeview_for_active_category() 
        
        if self.tree.exists(new_snippet.tree_item_iid_str):
            self.tree.selection_set(new_snippet.tree_item_iid_str)
            self.tree.see(new_snippet.tree_item_iid_str)
        
        self.new_trigger_entry.delete(0, tk.END)
        self.new_replace_text.delete("1.0", tk.END)
        # Status bar is updated by populate_treeview


    def on_double_click_edit(self, event):
        if not self.active_file_path: return
        
        selected_item_iid = self.tree.focus()
        if not selected_item_iid: return

        snippets_list = self.snippets_by_file_path.get(self.active_file_path, [])
        selected_snippet = None
        for snip in snippets_list:
            if snip.tree_item_iid_str == selected_item_iid:
                selected_snippet = snip
                break
        
        if not selected_snippet:
            messagebox.showerror("Error", "Could not find selected snippet data.", parent=self.root)
            return

        dialog = EditSnippetDialog(self.root, f"Edit Snippet: {selected_snippet.trigger}", existing_snippet=selected_snippet)
        if dialog.result:
            updated_data = dialog.result
            
            if selected_snippet.trigger != updated_data["trigger"]:
                if any(s != selected_snippet and s.trigger == updated_data["trigger"] for s in snippets_list):
                    messagebox.showerror("Error", f"Another trigger '{updated_data['trigger']}' already exists in this category.", parent=self.root)
                    return

            if selected_snippet.mark_modified(updated_data["trigger"], updated_data["replace_text"]):
                self.populate_treeview_for_active_category()
                if self.tree.exists(selected_snippet.tree_item_iid_str): 
                    self.tree.selection_set(selected_snippet.tree_item_iid_str)
                    self.tree.see(selected_snippet.tree_item_iid_str)
                # Status bar updated by populate_treeview


    def remove_selected_snippet(self):
        if not self.active_file_path:
            messagebox.showinfo("Info", "No category selected.", parent=self.root)
            return

        selected_item_iids = self.tree.selection()
        if not selected_item_iids:
            messagebox.showinfo("Info", "No snippet selected to remove.", parent=self.root)
            return

        if not messagebox.askyesno("Confirm Deletion", f"Remove {len(selected_item_iids)} snippet(s) from {self.category_var.get()}?\nThis is permanent upon saving.", parent=self.root):
            return

        snippets_list_for_file = self.snippets_by_file_path[self.active_file_path]
        
        snippets_to_remove_objs = []
        for iid in selected_item_iids:
            for snip in snippets_list_for_file:
                if snip.tree_item_iid_str == iid:
                    snippets_to_remove_objs.append(snip)
                    break
        
        num_removed = 0
        for snip_to_remove in snippets_to_remove_objs:
            snippets_list_for_file.remove(snip_to_remove)
            num_removed +=1

        if num_removed > 0:
            self.populate_treeview_for_active_category()
            # Status bar updated by populate_treeview


    def save_all_changes(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Espanso directory not set.", parent=self.root)
            return

        self._set_busy_cursor(True)
        self.update_status_bar("Saving all changes...")
        num_files_processed = 0
        try:
            for file_path, snippets_list in self.snippets_by_file_path.items():
                if file_path not in self.snippets_by_file_path: 
                    continue

                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    matches_yaml_list = [s.original_yaml_entry for s in snippets_list]
                    file_content_to_write = {}
                    
                    if os.path.exists(file_path): 
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f_read:
                                file_content_to_write = yaml.safe_load(f_read)
                                if not isinstance(file_content_to_write, dict):
                                    file_content_to_write = {} 
                        except Exception: 
                            file_content_to_write = {}
                    
                    file_content_to_write['matches'] = matches_yaml_list
                    
                    if not file_content_to_write and not matches_yaml_list : 
                         file_content_to_write = {'matches': []}
                    if 'matches' not in file_content_to_write: 
                        file_content_to_write['matches'] = []

                    with open(file_path, 'w', encoding='utf-8') as f_write:
                        yaml.dump(file_content_to_write, f_write, sort_keys=False, allow_unicode=True, default_flow_style=False, Dumper=yaml.SafeDumper)
                    
                    num_files_processed += 1
                
                except Exception as e_file: # Error saving a specific file
                    messagebox.showerror("Save Error", f"Error saving {os.path.basename(file_path)}:\n{e_file}", parent=self.root)
                    # Optionally, decide if you want to stop all saves or continue with others
                    # For now, it continues, but the error is shown.

            for snippets_list_val in self.snippets_by_file_path.values():
                for snippet in snippets_list_val:
                    snippet.is_new = False
                    snippet.is_modified = False
            
            self.update_status_bar(f"Successfully saved changes to {num_files_processed} file(s).")
            self.on_category_selected() # Refresh status bar for current category mtime
            messagebox.showinfo("Save Successful", f"Changes saved to {num_files_processed} file(s).", parent=self.root)
        except Exception as e_main: # Catch any unexpected error during the save all loop
             messagebox.showerror("Save Error", f"An unexpected error occurred during save all:\n{e_main}", parent=self.root)
             self.update_status_bar("Save operation failed with an unexpected error.")
        finally:
            self._set_busy_cursor(False)


    def sort_column(self, col_name):
        if not self.active_file_path or not self.snippets_by_file_path.get(self.active_file_path):
            return

        snippets_list = self.snippets_by_file_path[self.active_file_path]
        if not snippets_list: return

        if self.current_sort_column == col_name:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = col_name
            self.current_sort_reverse = False

        if col_name == "trigger": key_func = lambda s: s.trigger.lower()
        elif col_name == "replace": key_func = lambda s: s.replace_text.lower()
        else: return

        self._set_busy_cursor(True)
        try:
            snippets_list.sort(key=key_func, reverse=self.current_sort_reverse)
            self.populate_treeview_for_active_category() # This will update status

            for col_h in self.tree["columns"]:
                text = col_h.title()
                if col_h == self.current_sort_column:
                    text += " " + ("▼" if self.current_sort_reverse else "▲")
                self.tree.heading(col_h, text=text, command=lambda c=col_h: self.sort_column(c))
        finally:
            self._set_busy_cursor(False)


    def handle_new_category_creation(self):
        if not self.espanso_config_dir:
            messagebox.showerror("Error", "Please open an Espanso directory first.", parent=self.root)
            return

        dialog = NewCategoryDialog(self.root, "Create New Espanso Category File", self.espanso_config_dir)
        if dialog.result:
            self._set_busy_cursor(True)
            self.update_status_bar("Creating new category...")
            try:
                new_file_path = dialog.result["file_path"]
                new_display_name = dialog.result["display_name"] 

                os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
                with open(new_file_path, 'w', encoding='utf-8') as f:
                    yaml.dump({'matches': []}, f, sort_keys=False) 
                
                self.snippets_by_file_path[new_file_path] = []
                self.category_dropdown_map[new_display_name] = new_file_path
                
                self.load_all_categories_into_dropdown(select_display_name=new_display_name)
                # Status updated by load_all_categories
                self.update_status_bar(f"Created new category: {new_display_name}. Add snippets and save.")


            except Exception as e:
                messagebox.showerror("Error", f"Could not create category file {new_display_name}:\n{e}", parent=self.root)
                self.update_status_bar("Failed to create new category.")
            finally:
                self._set_busy_cursor(False)

    def handle_remove_category(self):
        selected_display_name = self.category_var.get()
        if not selected_display_name:
            messagebox.showerror("Error", "No category selected to remove.", parent=self.root)
            return

        file_path_to_remove = self.category_dropdown_map.get(selected_display_name)
        if not file_path_to_remove: 
            messagebox.showerror("Error", "Internal error: Cannot find file for selected category.", parent=self.root)
            return

        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to permanently delete the category file '{selected_display_name}' and all its snippets?\nThis action cannot be undone.", parent=self.root):
            return
        
        self._set_busy_cursor(True)
        self.update_status_bar(f"Removing category '{selected_display_name}'...")
        try:
            if os.path.exists(file_path_to_remove):
                os.remove(file_path_to_remove)
            
            if selected_display_name in self.category_dropdown_map:
                del self.category_dropdown_map[selected_display_name]
            if file_path_to_remove in self.snippets_by_file_path:
                del self.snippets_by_file_path[file_path_to_remove]
            
            self.active_file_path = None 
            self.load_all_categories_into_dropdown() 
            self.update_status_bar(f"Category '{selected_display_name}' deleted.")

        except Exception as e:
            messagebox.showerror("Error", f"Could not delete category file {selected_display_name}:\n{e}", parent=self.root)
            self.update_status_bar(f"Failed to delete category '{selected_display_name}'.")
        finally:
            self._set_busy_cursor(False)


    def on_closing(self):
        has_unsaved = False
        for snippets_list in self.snippets_by_file_path.values():
            if any(s.is_new or s.is_modified for s in snippets_list):
                has_unsaved = True
                break
        
        if has_unsaved:
            if messagebox.askyesno("Unsaved Changes", "Unsaved changes exist. Quit without saving?", parent=self.root):
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EspansoManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
