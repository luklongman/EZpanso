# main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from datetime import datetime
import platform
import threading
import queue # For thread communication
from typing import Dict, List, Any, Optional, Callable, Tuple
import uuid # For unique new snippet IDs if needed before save

# Local imports
import constants as C
from data_model import Snippet
from ui_dialogs import EditSnippetDialog, NewCategoryDialog
import file_handler


class EspansoManagerApp:
    def __init__(self, root_tk: tk.Tk):
        self.root: tk.Tk = root_tk
        self.root.title(C.TITLE_APP)
        self.root.geometry("1400x800")

        self.espanso_config_dir: str = ""
        # In-memory store for snippets, keyed by full file path
        self.snippets_by_file_path: Dict[str, List[Snippet]] = {}
        # Maps display names in combobox to full file paths
        self.category_dropdown_map: Dict[str, str] = {}
        self.active_file_path: Optional[str] = None

        self.current_sort_column: Optional[str] = None
        self.current_sort_reverse: bool = False
        
        self.loading_thread: Optional[threading.Thread] = None
        self.saving_thread: Optional[threading.Thread] = None
        self.thread_queue: queue.Queue = queue.Queue() # For results from threads

        self._create_widgets()
        self._setup_keyboard_shortcuts()  # Set up keyboard shortcuts
        self.root.after(100, self._process_thread_queue) # Start polling queue
        self._load_initial_config()

    def _setup_keyboard_shortcuts(self) -> None:
        """Set up all keyboard shortcuts."""
        # File operations
        self.root.bind_all("<Command-s>", lambda event: self._save_all_changes_thread())
        self.root.bind_all("<Control-s>", lambda event: self._save_all_changes_thread())
        self.root.bind("<F5>", lambda event: self.refresh_all_categories_prompt())

        # Category and snippet operations
        self.root.bind_all("<Command-n>", lambda event: self._add_snippet_from_entry_fields())
        self.root.bind_all("<Command-Shift-N>", lambda event: self._handle_new_category_dialog())
        
        # TreeView navigation and selection
        self.tree.bind("<Up>", lambda event: self._handle_up_down_key("up"))
        self.tree.bind("<Down>", lambda event: self._handle_up_down_key("down"))
        self.tree.bind("<Shift-Up>", lambda event: self._handle_shift_up_down("up"))
        self.tree.bind("<Shift-Down>", lambda event: self._handle_shift_up_down("down"))
        self.tree.bind("<Return>", lambda event: self._handle_return_key())
        self.tree.bind("<Escape>", lambda event: self._handle_escape_key())
        
        # Configure repeat delay and rate for better keyboard responsiveness
        self.root.tk.call('tk', 'scaling', 1.0)  # Ensure consistent scaling
        self.root.tk.call('set', 'tk::Priv(textRepeatDelay)', 200)  # Faster initial repeat
        self.root.tk.call('set', 'tk::Priv(textRepeatInterval)', 30)  # Faster repeat rate

    def _set_busy_cursor(self, busy: bool = True) -> None:
        """Helper to set/unset busy cursor and manage UI interaction."""
        if busy:
            self.root.config(cursor="watch")
            # Potentially disable parts of the UI here
            if hasattr(self, 'category_dropdown'): # Check if widgets are created
                self.category_dropdown.config(state=tk.DISABLED)
                self.new_category_button.config(state=tk.DISABLED)
                self.remove_category_button.config(state=tk.DISABLED)
                self.add_new_snippet_button.config(state=tk.DISABLED)
                self.remove_snippet_button.config(state=tk.DISABLED)
                if self.filemenu: self.filemenu.entryconfig("Save All Changes (Cmd/Ctrl+S)", state=tk.DISABLED)

        else:
            self.root.config(cursor="")
            if hasattr(self, 'category_dropdown'):
                self.category_dropdown.config(state="readonly") # Or tk.NORMAL if editable
                self.new_category_button.config(state=tk.NORMAL)
                self.remove_category_button.config(state=tk.NORMAL)
                self.add_new_snippet_button.config(state=tk.NORMAL)
                self.remove_snippet_button.config(state=tk.NORMAL)
                if self.filemenu: self.filemenu.entryconfig("Save All Changes (Cmd/Ctrl+S)", state=tk.NORMAL)

        self.root.update_idletasks()

    def _update_status_bar(self, message: str) -> None:
        self.status_bar_text.set(message)
        # Only call update_idletasks() if really needed
        if message.startswith(("Loading", "Saving", "Creating", "Removing")):
            self.root.update_idletasks()

    def _process_thread_queue(self) -> None:
        """Process messages from worker threads via the queue."""
        try:
            while True: # Process all messages currently in queue
                message_type, data = self.thread_queue.get_nowait()
                
                if message_type == "load_complete":
                    self._handle_load_complete(data)
                elif message_type == "save_complete":
                    self._handle_save_complete(data)
                elif message_type == "create_category_complete":
                    self._handle_create_category_complete(data)
                elif message_type == "remove_category_complete":
                    self._handle_remove_category_complete(data)
                # Add other message types as needed

                self.thread_queue.task_done() # Signal that the item is processed
        except queue.Empty:
            pass # No messages in queue
        finally:
            # Reschedule after processing current batch or if queue was empty
            self.root.after(100, self._process_thread_queue)

    # --- Threaded Operation Callers ---

    def _load_initial_config(self) -> None:
        self._set_busy_cursor(True)
        self._update_status_bar(C.MSG_LOADING_INITIAL_CONFIG)
        
        default_path = file_handler.get_default_espanso_config_path()
        if default_path and os.path.isdir(default_path):
            self.espanso_config_dir = default_path
            self._start_load_data_thread(self.espanso_config_dir)
        else:
            self._update_status_bar(C.MSG_DEFAULT_DIR_NOT_FOUND)
            messagebox.showinfo("Info", C.MSG_DEFAULT_DIR_NOT_FOUND, parent=self.root)
            self._set_busy_cursor(False) # Release cursor if no load started


    def _start_load_data_thread(self, directory_path: str, select_display_name: Optional[str] = None) -> None:
        if self.loading_thread and self.loading_thread.is_alive():
            messagebox.showwarning("Busy", "Already loading data. Please wait.", parent=self.root)
            return

        self._set_busy_cursor(True)
        self._update_status_bar(C.MSG_LOADING_CATEGORIES)
        
        self.loading_thread = threading.Thread(
            target=self._load_data_worker,
            args=(directory_path, select_display_name),
            daemon=True
        )
        self.loading_thread.start()

    def _load_data_worker(self, directory_path: str, select_display_name: Optional[str]) -> None:
        """Worker function to load data in a separate thread."""
        loaded_data = file_handler.load_espanso_data(directory_path)
        # Add select_display_name to the data to pass it to the handler
        loaded_data['select_display_name_after_load'] = select_display_name
        self.thread_queue.put(("load_complete", loaded_data))


    def _handle_load_complete(self, data: Dict[str, Any]) -> None:
        """Handles the data received after loading thread finishes."""
        self._set_busy_cursor(False) # Release cursor first

        load_errors = data.get("errors", [])
        if load_errors:
            for file_path_err, err_msg in load_errors:
                if file_path_err: # Specific file error
                    messagebox.showerror("Load Error", f"Error in {os.path.basename(file_path_err)}:\n{err_msg}", parent=self.root)
                else: # General error (e.g., directory not found)
                     messagebox.showerror("Load Error", err_msg, parent=self.root)


        self.snippets_by_file_path = data.get("snippets_by_file", {})
        self.category_dropdown_map = data.get("category_dropdown_map", {})
        category_display_names = data.get("category_display_names", [])
        total_snippets = data.get("total_snippets_loaded", 0)
        select_display_name_after_load = data.get('select_display_name_after_load')

        self.category_dropdown['values'] = category_display_names

        if category_display_names:
            current_selection = self.category_var.get()
            if select_display_name_after_load and select_display_name_after_load in category_display_names:
                self.category_var.set(select_display_name_after_load)
            elif current_selection and current_selection in category_display_names:
                 self.category_var.set(current_selection) # Keep current if still valid
            else:
                self.category_var.set(category_display_names[0])
            
            self.on_category_selected() # This will populate tree and update status
            self._update_status_bar(C.MSG_LOADED_SNIPPETS_COUNT.format(
                snippet_count=total_snippets, category_count=len(category_display_names)
            ))
        else:
            self.category_var.set("")
            self.active_file_path = None
            self._clear_treeview()
            self._update_status_bar(C.MSG_NO_YAML_FILES_FOUND.format(self.espanso_config_dir))
            
        # Refresh tree sort indicators
        self._update_treeview_sort_indicators()


    def _save_all_changes_thread(self) -> None:
        if not self.espanso_config_dir:
            messagebox.showerror("Error", C.ERROR_ESPANSO_DIR_NOT_SET, parent=self.root)
            return
        
        if self.saving_thread and self.saving_thread.is_alive():
            messagebox.showwarning("Busy", "Already saving changes. Please wait.", parent=self.root)
            return

        self._set_busy_cursor(True)
        self._update_status_bar(C.MSG_SAVING_ALL_CHANGES)

        # Create a deep copy of the data to be saved to avoid race conditions
        # if the main data structure is modified while saving.
        # Snippet objects themselves contain original_yaml_entry which is what's saved.
        data_to_save = {fp: list(snips) for fp, snips in self.snippets_by_file_path.items()}

        self.saving_thread = threading.Thread(
            target=self._save_data_worker,
            args=(data_to_save,),
            daemon=True
        )
        self.saving_thread.start()

    def _save_data_worker(self, snippets_data: Dict[str, List[Snippet]]) -> None:
        """Worker function to save all changes."""
        num_files_processed = 0
        save_errors: List[str] = []

        for file_path, snippets_list in snippets_data.items():
            # Check if this file_path is still relevant (e.g., category not deleted during save prep)
            # This check is a bit redundant if data_to_save is a snapshot, but good for safety.
            # if file_path not in self.snippets_by_file_path:  # This needs to access main thread data, avoid
            #    continue

            success, error_msg = file_handler.save_espanso_file(file_path, snippets_list)
            if success:
                num_files_processed += 1
            else:
                if error_msg: save_errors.append(error_msg)
        
        self.thread_queue.put(("save_complete", {
            "num_files_processed": num_files_processed,
            "errors": save_errors,
            "saved_data_keys": list(snippets_data.keys()) # To identify which snippets had flags reset
        }))

    def _handle_save_complete(self, data: Dict[str, Any]) -> None:
        """Handles the result after saving thread finishes."""
        self._set_busy_cursor(False)
        num_files_processed = data.get("num_files_processed", 0)
        save_errors = data.get("errors", [])
        saved_data_keys = data.get("saved_data_keys", [])


        if save_errors:
            for err_msg in save_errors:
                messagebox.showerror("Save Error", err_msg, parent=self.root)
        
        if num_files_processed > 0:
            # Reset modification flags only for snippets that were part of the saved data
            for file_path_key in saved_data_keys:
                if file_path_key in self.snippets_by_file_path:
                    for snippet in self.snippets_by_file_path[file_path_key]:
                        snippet.is_new = False
                        snippet.is_modified = False
            
            self._update_status_bar(C.MSG_SAVE_SUCCESSFUL_COUNT.format(count=num_files_processed))
            messagebox.showinfo("Save Successful", C.MSG_SAVE_SUCCESSFUL_COUNT.format(count=num_files_processed), parent=self.root)
            self.on_category_selected() # Refresh view, especially mtime in status
        elif not save_errors: # No files processed and no errors (e.g. nothing to save)
            self._update_status_bar("No changes to save.")
        else: # Errors occurred, and maybe some files processed
             self._update_status_bar(C.MSG_SAVE_ERROR_UNEXPECTED)


    # --- GUI Creation ---
    def _create_widgets(self) -> None:
        menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(menubar, tearoff=0) # Store to manage state
        self.filemenu.add_command(label="Open Espanso Dir", command=self.select_espanso_directory_dialog)
        self.filemenu.add_command(label=C.MENU_FILE_REFRESH, command=self.refresh_all_categories_prompt)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=C.MENU_FILE_NEW_SNIPPET, command=self._add_snippet_from_entry_fields)
        self.filemenu.add_command(label=C.MENU_FILE_NEW_CATEGORY, command=self._handle_new_category_dialog)
        self.filemenu.add_separator()
        self.filemenu.add_command(label=C.MENU_FILE_SAVE, command=self._save_all_changes_thread)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=menubar)

        # Key bindings
        self.root.bind_all("<Command-s>", lambda event: self._save_all_changes_thread())
        self.root.bind_all("<Control-s>", lambda event: self._save_all_changes_thread())
        self.root.bind("<F5>", lambda event: self.refresh_all_categories_prompt())

        # Top Action Frame (Category Selection)
        top_action_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        top_action_frame.pack(expand=False, fill=tk.X)

        ttk.Label(top_action_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 2))
        self.category_var = tk.StringVar()
        self.category_dropdown = ttk.Combobox(top_action_frame, textvariable=self.category_var, state="readonly", width=35)
        self.category_dropdown.pack(side=tk.LEFT, padx=(0, 5))
        self.category_dropdown.bind("<<ComboboxSelected>>", self.on_category_selected)

        self.new_category_button = ttk.Button(top_action_frame, text="New Category", command=self._handle_new_category_dialog)
        self.new_category_button.pack(side=tk.LEFT, padx=2)

        self.remove_category_button = ttk.Button(top_action_frame, text="Remove Selected Category", command=self._handle_remove_category_dialog)
        self.remove_category_button.pack(side=tk.LEFT, padx=2)

        # Main Content Frame (Treeview)
        main_content_frame = ttk.Frame(self.root, padding=(10, 5, 10, 0))
        main_content_frame.pack(expand=True, fill=tk.BOTH)

        self.tree = ttk.Treeview(main_content_frame, columns=C.TREEVIEW_COLUMNS, show="headings", selectmode="extended", style="Custom.Treeview")
        style = ttk.Style()
        style.configure("Custom.Treeview", 
                       rowheight=30, 
                       font=('Arial', 12),
                       background='white',  # Set default background
                       fieldbackground='white')  # Set background for empty areas
        style.configure("Custom.Treeview.Heading", 
                       font=('Arial', 12, 'bold'),
                       relief='flat')  # Flatter look for headers
        
        # Optimize performance by reducing visual updates
        self.tree.configure(takefocus=1)  # Enable keyboard navigation
        
        # Configure colors with better contrast
        style.map('Custom.Treeview',
                 background=[('selected', '#0078d7'),
                           ('!selected', '')],
                 foreground=[('selected', 'white')],
                 relief=[('selected', 'solid')])  # Better selection visibility
        self.tree.tag_configure('oddrow', background='#f0f0f0')  # Lighter gray for better contrast
        
        # Configure wider columns
        col_widths = {C.COL_TRIGGER: 350, C.COL_REPLACE: 800}
        for col in C.TREEVIEW_COLUMNS:
            self.tree.heading(col, text=col.title(), command=lambda c=col: self._sort_column(c))
            self.tree.column(col, width=col_widths[col], stretch=True)

        v_scroll = ttk.Scrollbar(main_content_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(main_content_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        main_content_frame.grid_rowconfigure(0, weight=1)
        main_content_frame.grid_columnconfigure(0, weight=1)
        self.tree.bind("<Double-1>", self._on_double_click_edit)

        # Snippet Entry Frame (New Snippet)
        snippet_entry_frame = ttk.Frame(self.root, padding=(10, 5, 10, 5))
        snippet_entry_frame.pack(expand=False, fill=tk.X)

        ttk.Label(snippet_entry_frame, text="New Trigger:").grid(row=0, column=0, padx=(0, 2), pady=2, sticky="w")
        self.new_trigger_entry = ttk.Entry(snippet_entry_frame)
        self.new_trigger_entry.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        ttk.Label(snippet_entry_frame, text="New Replace:").grid(row=1, column=0, padx=(0, 2), pady=2, sticky="nw")
        self.new_replace_text = tk.Text(snippet_entry_frame, height=3, wrap=tk.WORD)
        self.new_replace_text.grid(row=1, column=1, columnspan=3, padx=2, pady=2, sticky="ew")

        self.add_new_snippet_button = ttk.Button(snippet_entry_frame, text="Add This Snippet", command=self._add_snippet_from_entry_fields)
        self.add_new_snippet_button.grid(row=0, column=2, rowspan=2, padx=(5, 0), pady=2, sticky="ns")

        snippet_entry_frame.grid_columnconfigure(1, weight=1)

        self.remove_snippet_button = ttk.Button(self.root, text="Remove Selected Snippet(s)", command=self._remove_selected_snippets)
        self.remove_snippet_button.pack(pady=(0, 5), padx=10, fill=tk.X)
        
        # Status Bar
        self.status_bar_text = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self._update_status_bar(C.MSG_WELCOME)


    # --- UI Event Handlers & Logic ---
    def select_espanso_directory_dialog(self) -> None:
        if self.loading_thread and self.loading_thread.is_alive():
             messagebox.showwarning("Busy", "Cannot change directory while loading. Please wait.", parent=self.root)
             return
        self._update_status_bar(C.MSG_SELECTING_DIR)
        dir_path = filedialog.askdirectory(title="Select Espanso Match Directory", initialdir=os.path.expanduser("~"))
        if dir_path:
            self.espanso_config_dir = dir_path
            # Clear existing data before loading new
            self.snippets_by_file_path.clear()
            self.category_dropdown_map.clear()
            self.category_var.set("")
            self._clear_treeview()
            self._start_load_data_thread(self.espanso_config_dir)
        else:
            self._update_status_bar(C.MSG_DIR_SELECTION_CANCELLED)

    def _has_unsaved_changes(self) -> bool:
        """Checks if there are any unsaved new or modified snippets."""
        for snippets_list in self.snippets_by_file_path.values():
            if any(s.is_new or s.is_modified for s in snippets_list):
                return True
        return False

    def refresh_all_categories_prompt(self) -> None:
        if not self.espanso_config_dir:
            messagebox.showerror("Error", C.ERROR_ESPANSO_DIR_NOT_SET, parent=self.root)
            return
        if self.loading_thread and self.loading_thread.is_alive():
             messagebox.showwarning("Busy", "Cannot refresh while loading. Please wait.", parent=self.root)
             return

        if self._has_unsaved_changes():
            if not messagebox.askyesno("Unsaved Changes", C.CONFIRM_UNSAVED_REFRESH, parent=self.root):
                return
        
        self._update_status_bar(C.MSG_REFRESHING_DATA)
        current_selected_display_name = self.category_var.get()
        self._start_load_data_thread(self.espanso_config_dir, select_display_name=current_selected_display_name)


    def on_category_selected(self, event: Optional[tk.Event] = None) -> None:
        """Handles selection change in the category dropdown."""
        # This method is now primarily for UI update based on already loaded data
        selected_display_name: str = self.category_var.get()
        if not selected_display_name:
            self.active_file_path = None
            self._clear_treeview()
            self._update_status_bar(C.MSG_NO_CATEGORY_SELECTED)
            return

        self.active_file_path = self.category_dropdown_map.get(selected_display_name)
        if self.active_file_path:
            self._populate_treeview_for_active_category()
            # Status bar is updated within _populate_treeview_for_active_category
        else:
            self._clear_treeview()
            self._update_status_bar(C.MSG_ERROR_FINDING_FILE_FOR_CATEGORY.format(selected_display_name))
        
        # Reset sort when category changes, or apply current sort if needed
        # For simplicity, let's reset. User can re-click header to sort.
        self.current_sort_column = None
        self.current_sort_reverse = False
        self._update_treeview_sort_indicators()


    def _clear_treeview(self) -> None:
        """Clears all items from the treeview."""
        if self.tree.get_children():
            self.tree.delete(*self.tree.get_children())

    def _populate_treeview_for_active_category(self) -> None:
        """Populates the treeview with snippets from the active category."""
        # Disable treeview updates temporarily for better performance
        self.tree.configure(selectmode='none')
        self.tree.update_idletasks()
        
        self._clear_treeview()
        selected_display_name = self.category_var.get()

        if not self.active_file_path or self.active_file_path not in self.snippets_by_file_path:
            if selected_display_name:
                self._update_status_bar(C.MSG_CATEGORY_NO_SNIPPETS.format(category_name=selected_display_name))
            # else: status handled by on_category_selected if no category is selected
            self.tree.configure(selectmode='extended')
            return

        snippets_list = self.snippets_by_file_path.get(self.active_file_path, [])
        
        # Apply sorting if a sort column is set
        if self.current_sort_column and snippets_list:
            key_func: Callable[[Snippet], str]
            if self.current_sort_column == C.COL_TRIGGER:
                key_func = lambda s: s.trigger.lower()
            elif self.current_sort_column == C.COL_REPLACE:
                key_func = lambda s: s.replace_text.lower()
            else: # Should not happen if current_sort_column is validated
                key_func = lambda s: s.trigger.lower() 
            
            try:
                snippets_list.sort(key=key_func, reverse=self.current_sort_reverse)
            except Exception as e: # Catch any sorting error, e.g. if data is unexpectedly not string
                print(f"Error during sort: {e}")


        for idx, snippet_obj in enumerate(snippets_list):
            values = snippet_obj.get_display_values_for_tree()
            # Ensure tree_item_iid_str is always set
            if not snippet_obj.tree_item_iid_str:
                 # Fallback if IID wasn't set during load (e.g. for newly added unsaved snippets)
                 snippet_obj.tree_item_iid_str = f"{C.NEW_SNIPPET_ID_PREFIX}{uuid.uuid4()}"

            # Apply alternating row colors
            tags = ('oddrow',) if idx % 2 else ()
            self.tree.insert("", tk.END, values=values, iid=snippet_obj.tree_item_iid_str, tags=tags)
        
        # Re-enable selection and update UI
        self.tree.configure(selectmode='extended')
        self.tree.update_idletasks()
        
        # Update status bar
        if self.active_file_path:
            try:
                mtime_ts = os.path.getmtime(self.active_file_path)
                mtime_str = datetime.fromtimestamp(mtime_ts).strftime('%Y-%m-%d %H:%M:%S')
                self._update_status_bar(C.MSG_CATEGORY_DISPLAY.format(
                    category_name=selected_display_name,
                    snippet_count=len(snippets_list),
                    mtime=mtime_str
                ))
            except FileNotFoundError:
                 self._update_status_bar(C.MSG_CATEGORY_FILE_NOT_FOUND.format(
                    category_name=selected_display_name, snippet_count=len(snippets_list)
                ))
            except Exception: # Catch other potential os.path.getmtime errors
                 self._update_status_bar(C.MSG_CATEGORY_MODIFIED_UNKNOWN.format(
                    category_name=selected_display_name, snippet_count=len(snippets_list)
                ))
        elif selected_display_name: # Active path not set, but a category is selected (e.g. error case)
            self._update_status_bar(C.MSG_CATEGORY_NO_SNIPPETS.format(category_name=selected_display_name))


    def _add_snippet_from_entry_fields(self) -> None:
        if not self.active_file_path:
            messagebox.showerror("Error", C.ERROR_NO_CATEGORY_TO_ADD_SNIPPET, parent=self.root)
            return

        trigger: str = self.new_trigger_entry.get().strip()
        replace_text: str = self.new_replace_text.get("1.0", tk.END).strip()

        if not trigger:
            messagebox.showerror("Error", C.ERROR_TRIGGER_EMPTY, parent=self.root)
            return

        snippets_list_for_file = self.snippets_by_file_path.get(self.active_file_path)
        if snippets_list_for_file is None: # Should not happen if active_file_path is set
            messagebox.showerror("Error", "Internal error: Snippet list not found for active category.", parent=self.root)
            return

        if any(s.trigger == trigger for s in snippets_list_for_file):
            messagebox.showerror("Error", C.ERROR_TRIGGER_EXISTS.format(trigger), parent=self.root)
            return

        new_snippet = Snippet(
            trigger=trigger,
            replace_text=replace_text,
            file_path=self.active_file_path
        )
        new_snippet.is_new = True
        new_snippet.tree_item_iid_str = f"{C.NEW_SNIPPET_ID_PREFIX}{uuid.uuid4()}" # Unique ID for tree
        
        snippets_list_for_file.append(new_snippet)
        self._populate_treeview_for_active_category() # Repopulate to include the new snippet and apply sort
        
        if self.tree.exists(new_snippet.tree_item_iid_str):
            self.tree.selection_set(new_snippet.tree_item_iid_str)
            self.tree.see(new_snippet.tree_item_iid_str)
        
        self.new_trigger_entry.delete(0, tk.END)
        self.new_replace_text.delete("1.0", tk.END)
        # Status bar is updated by _populate_treeview_for_active_category


    def _on_double_click_edit(self, event: tk.Event) -> None:
        if not self.active_file_path: return
        
        selected_item_iid: str = self.tree.focus() # Gets the IID of the focused item
        if not selected_item_iid: return

        snippets_list = self.snippets_by_file_path.get(self.active_file_path)
        if snippets_list is None: return

        selected_snippet: Optional[Snippet] = None
        for snip in snippets_list:
            if snip.tree_item_iid_str == selected_item_iid:
                selected_snippet = snip
                break
        
        if not selected_snippet:
            messagebox.showerror("Error", C.ERROR_COULD_NOT_FIND_SNIPPET, parent=self.root)
            return

        dialog = EditSnippetDialog(self.root, C.TITLE_EDIT_SNIPPET.format(selected_snippet.trigger), existing_snippet=selected_snippet)
        if dialog.result: # result is a dict if dialog was applied successfully
            updated_data = dialog.result
            
            # Check for trigger collision only if trigger changed
            if selected_snippet.trigger != updated_data[C.COL_TRIGGER]:
                if any(s != selected_snippet and s.trigger == updated_data[C.COL_TRIGGER] for s in snippets_list):
                    messagebox.showerror("Error", C.ERROR_ANOTHER_TRIGGER_EXISTS.format(updated_data[C.COL_TRIGGER]), parent=self.root)
                    return # Don't apply change

            if selected_snippet.mark_modified(updated_data[C.COL_TRIGGER], updated_data[C.COL_REPLACE]):
                self._populate_treeview_for_active_category() # Repopulate to reflect changes and sorting
                if self.tree.exists(selected_snippet.tree_item_iid_str):
                    self.tree.selection_set(selected_snippet.tree_item_iid_str)
                    self.tree.see(selected_snippet.tree_item_iid_str)
                # Status bar updated by _populate_treeview


    def _remove_selected_snippets(self) -> None:
        if not self.active_file_path:
            messagebox.showinfo("Info", "No category selected.", parent=self.root)
            return

        selected_item_iids: Tuple[str, ...] = self.tree.selection() # Returns a tuple of IIDs
        if not selected_item_iids:
            messagebox.showinfo("Info", "No snippet selected to remove.", parent=self.root)
            return
        
        category_name = self.category_var.get()
        if not messagebox.askyesno("Confirm Deletion", C.CONFIRM_REMOVE_SNIPPETS.format(count=len(selected_item_iids), category_name=category_name), parent=self.root):
            return

        snippets_list_for_file = self.snippets_by_file_path.get(self.active_file_path)
        if snippets_list_for_file is None: return # Should not happen

        # It's safer to build a list of snippets to remove and then remove them
        # to avoid issues with modifying a list while iterating over it (though not directly done here).
        snippets_to_remove_objs: List[Snippet] = []
        for iid in selected_item_iids:
            for snip in snippets_list_for_file:
                if snip.tree_item_iid_str == iid:
                    snippets_to_remove_objs.append(snip)
                    break # Found snippet for this IID
        
        num_removed = 0
        for snip_to_remove in snippets_to_remove_objs:
            try:
                snippets_list_for_file.remove(snip_to_remove)
                num_removed += 1
            except ValueError:
                # Snippet might have been removed by another concurrent action (unlikely in single-threaded GUI part)
                # Or IID mismatch if data is out of sync.
                print(f"Warning: Snippet with IID {snip_to_remove.tree_item_iid_str} not found in list for removal.")


        if num_removed > 0:
            self._populate_treeview_for_active_category()
            # Status bar updated by _populate_treeview_for_active_category
            # Mark the containing file as modified if any existing (non-new) snippet was removed
            # This is implicitly handled because the list of snippets changes, and save_all_changes saves the current state.


    def _sort_column(self, col_name: str) -> None:
        if not self.active_file_path or not self.snippets_by_file_path.get(self.active_file_path):
            return

        snippets_list = self.snippets_by_file_path.get(self.active_file_path)
        if not snippets_list: return

        if self.current_sort_column == col_name:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = col_name
            self.current_sort_reverse = False # Default to ascending for new column

        # The actual sorting is now done within _populate_treeview_for_active_category
        self._populate_treeview_for_active_category() 
        self._update_treeview_sort_indicators()

    def _update_treeview_sort_indicators(self) -> None:
        """Updates the sort indicators (arrows) in the treeview column headers."""
        for col_h_id in C.TREEVIEW_COLUMNS:
            text = col_h_id.title()
            if col_h_id == self.current_sort_column:
                text += C.SORT_DESC_INDICATOR if self.current_sort_reverse else C.SORT_ASC_INDICATOR
            self.tree.heading(col_h_id, text=text, command=lambda c=col_h_id: self._sort_column(c))


    # --- Category Management (Dialogs and Threaded Workers) ---
    def _handle_new_category_dialog(self) -> None:
        if not self.espanso_config_dir:
            messagebox.showerror("Error", C.ERROR_OPEN_ESPANSO_DIR_FIRST, parent=self.root)
            return
        if self.loading_thread and self.loading_thread.is_alive() or \
           self.saving_thread and self.saving_thread.is_alive():
            messagebox.showwarning("Busy","Cannot create category while another operation is in progress.", parent=self.root)
            return

        dialog = NewCategoryDialog(self.root, C.TITLE_NEW_CATEGORY, self.espanso_config_dir)
        if dialog.result:
            new_file_path = dialog.result["file_path"]
            self._set_busy_cursor(True)
            self._update_status_bar(C.MSG_CREATING_CATEGORY)
            
            # Start a thread for file creation
            create_thread = threading.Thread(
                target=self._create_category_worker,
                args=(new_file_path, dialog.result["display_name"]),
                daemon=True
            )
            create_thread.start()

    def _create_category_worker(self, file_path: str, display_name: str) -> None:
        """Worker thread for creating a new category file."""
        success, error_msg = file_handler.create_empty_category_file(file_path)
        self.thread_queue.put(("create_category_complete", {
            "success": success,
            "error_message": error_msg,
            "file_path": file_path,
            "display_name": display_name
        }))

    def _handle_create_category_complete(self, data: Dict[str, Any]) -> None:
        """Handles result from create category worker thread."""
        self._set_busy_cursor(False)
        success = data["success"]
        error_msg = data["error_message"]
        new_file_path = data["file_path"]
        new_display_name = data["display_name"]

        if success:
            # Add to in-memory store immediately
            self.snippets_by_file_path[new_file_path] = []
            self.category_dropdown_map[new_display_name] = new_file_path
            
            # Reload all categories to update dropdown and select the new one
            self._start_load_data_thread(self.espanso_config_dir, select_display_name=new_display_name)
            self._update_status_bar(C.MSG_CREATED_NEW_CATEGORY.format(new_display_name))
        else:
            messagebox.showerror("Error", error_msg or C.MSG_FAILED_CREATE_CATEGORY, parent=self.root)
            self._update_status_bar(C.MSG_FAILED_CREATE_CATEGORY)


    def _handle_remove_category_dialog(self) -> None:
        selected_display_name: str = self.category_var.get()
        if not selected_display_name:
            messagebox.showerror("Error", C.ERROR_NO_CATEGORY_TO_REMOVE, parent=self.root)
            return
        if self.loading_thread and self.loading_thread.is_alive() or \
           self.saving_thread and self.saving_thread.is_alive():
            messagebox.showwarning("Busy","Cannot remove category while another operation is in progress.", parent=self.root)
            return

        file_path_to_remove = self.category_dropdown_map.get(selected_display_name)
        if not file_path_to_remove:
            messagebox.showerror("Error", C.ERROR_INTERNAL_NO_FILE_FOR_CATEGORY, parent=self.root)
            return

        if not messagebox.askyesno("Confirm Deletion", C.CONFIRM_DELETE_CATEGORY.format(category_name=selected_display_name), parent=self.root):
            return
        
        self._set_busy_cursor(True)
        self._update_status_bar(C.MSG_REMOVING_CATEGORY.format(selected_display_name))

        # Start a thread for file deletion
        delete_thread = threading.Thread(
            target=self._remove_category_worker,
            args=(file_path_to_remove, selected_display_name),
            daemon=True
        )
        delete_thread.start()

    def _remove_category_worker(self, file_path: str, display_name: str) -> None:
        """Worker thread for deleting a category file."""
        success, error_msg = file_handler.delete_category_file(file_path)
        self.thread_queue.put(("remove_category_complete", {
            "success": success,
            "error_message": error_msg,
            "file_path": file_path,
            "display_name": display_name
        }))

    def _handle_remove_category_complete(self, data: Dict[str, Any]) -> None:
        """Handles result from remove category worker thread."""
        self._set_busy_cursor(False)
        success = data["success"]
        error_msg = data["error_message"]
        removed_file_path = data["file_path"]
        removed_display_name = data["display_name"]

        if success:
            # Remove from in-memory store
            if removed_display_name in self.category_dropdown_map:
                del self.category_dropdown_map[removed_display_name]
            if removed_file_path in self.snippets_by_file_path:
                del self.snippets_by_file_path[removed_file_path]
            
            if self.active_file_path == removed_file_path:
                self.active_file_path = None
            
            # Reload categories to update dropdown and view
            self._start_load_data_thread(self.espanso_config_dir) # Select first available
            self._update_status_bar(C.MSG_CATEGORY_DELETED.format(removed_display_name))
        else:
            messagebox.showerror("Error", error_msg or C.MSG_FAILED_DELETE_CATEGORY.format(removed_display_name), parent=self.root)
            self._update_status_bar(C.MSG_FAILED_DELETE_CATEGORY.format(removed_display_name))


    def on_closing(self) -> None:
        """Handles the window close event."""
        if self._has_unsaved_changes():
            if messagebox.askyesno("Unsaved Changes", C.CONFIRM_UNSAVED_QUIT, parent=self.root):
                self.root.destroy()
            else:
                return # Do not close
        else:
            self.root.destroy()

    def _handle_up_down_key(self, direction: str) -> str:
        """Handle Up/Down key navigation in treeview."""
        selection = self.tree.selection()
        if not selection:
            # If no selection, select first/last item
            items = self.tree.get_children()
            if not items:
                return "break"
            to_select = items[0] if direction == "down" else items[-1]
            self.tree.selection_set(to_select)
            self.tree.see(to_select)
        else:
            # Get current selection
            current = selection[0]
            items = self.tree.get_children()
            idx = items.index(current)
            
            # Calculate new index
            if direction == "up":
                new_idx = max(0, idx - 1)
            else:  # down
                new_idx = min(len(items) - 1, idx + 1)
            
            # Set new selection
            new_item = items[new_idx]
            self.tree.selection_set(new_item)
            self.tree.see(new_item)
        return "break"  # Prevent default handler

    def _handle_shift_up_down(self, direction: str) -> str:
        """Handle Shift+Up/Down for multiple selection in treeview."""
        selection = self.tree.selection()
        items = self.tree.get_children()
        
        if not selection:
            # If no selection, behave like normal up/down
            return self._handle_up_down_key(direction)
            
        # Get current focus
        current = self.tree.focus()
        if not current:
            return "break"
            
        # Find adjacent item
        idx = items.index(current)
        if direction == "up":
            new_idx = max(0, idx - 1)
        else:  # down
            new_idx = min(len(items) - 1, idx + 1)
            
        new_item = items[new_idx]
        
        # Toggle selection of adjacent item
        if new_item in selection:
            self.tree.selection_remove(new_item)
        else:
            self.tree.selection_add(new_item)
            
        self.tree.focus(new_item)
        self.tree.see(new_item)
        return "break"

    def _handle_return_key(self) -> str:
        """Handle Return key to edit the selected snippet."""
        if len(self.tree.selection()) == 1:  # Only edit if exactly one item is selected
            self._on_double_click_edit(None)  # None for event as we don't need it
        return "break"

    def _handle_escape_key(self) -> str:
        """Handle Escape key to clear selection."""
        self.tree.selection_remove(*self.tree.selection())
        return "break"
        
if __name__ == "__main__":
    root = tk.Tk()
    app = EspansoManagerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()