import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont

import os
import shutil
import threading
from datetime import datetime

from csv_handler import CSVHandler
from database import Database
from logger import read_logs, clear_logs, log_action

PAGE_SIZE = 500

class InventoryApp:

    def __init__(self, root):

        self.root = root
        self.root.title("InvMS : Inventory Management")
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)

        self.db = Database()
        self.csv_handler = CSVHandler()

        self.show_all_columns = False
        self.setup_ui()

    def import_csv(self):               # runs in a background thread so the UI stays responsive
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not file_path:
            return

        self.import_btn.config(state="disabled", text="Importing…")         # Disable button while import is running
        self.status_var.set("Importing CSV, please wait…")
        self.root.update_idletasks()

        def _do_import():
            try:
                table_name = self.csv_handler.import_csv(file_path)
                self.root.after(0, lambda: self._on_import_done(table_name))                # Schedule UI update back on the main thread

            except Exception as exc:
                self.root.after(0,
                    lambda e=exc: (
                        messagebox.showerror("Error", str(e)),
                        self.import_btn.config(state="normal", text="Import CSV"),
                        self.status_var.set("Import failed.")
                    )
                )

        threading.Thread(target=_do_import, daemon=True).start()

    def _on_import_done(self, table_name):                  # Called on the main thread once the background import finishes.
        self.import_btn.config(state="normal", text="Import CSV")   
        self.create_table_tab(table_name)
        self.status_var.set(f"Imported : {table_name}")
        messagebox.showinfo("Success", "CSV Imported Successfully")

    def create_table_tab(self, table_name):
        frame = tk.Frame(self.notebook)
        self.notebook.add(frame, text=table_name)

        x_scroll = ttk.Scrollbar(frame, orient="horizontal")
        y_scroll = ttk.Scrollbar(frame, orient="vertical")

        tree = ttk.Treeview(frame,
            xscrollcommand=x_scroll.set,
            yscrollcommand=y_scroll.set
        )

        x_scroll.config(command=tree.xview)
        y_scroll.config(command=tree.yview)

        x_scroll.pack(side="bottom", fill="x")
        y_scroll.pack(side="right",  fill="y")
        tree.pack(fill="both", expand=True)

        columns = self.db.get_columns(table_name)

        tree["columns"] = columns
        tree["show"]    = "headings"

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=143, minwidth=85, anchor="center", stretch=False)

        tree.table_name = table_name
        frame.tree      = tree

        # Pagination state attached to the tree widget
        tree._page_offset = 0
        tree._all_loaded  = False
        self.load_tree_data(tree, table_name)
        self.hide_columns(tree)

        # Load more rows when user scrolls near the bottom
        tree.bind("<MouseWheel>",       lambda e, t=tree: self._check_load_more(t))
        tree.bind("<Button-4>",         lambda e, t=tree: self._check_load_more(t))
        tree.bind("<Button-5>",         lambda e, t=tree: self._check_load_more(t))
        tree.bind("<KeyRelease-Next>",  lambda e, t=tree: self._check_load_more(t))

    def load_tree_data(self, tree, table_name, reset=True):     # LOAD TREE DATA  — paginated (only PAGE_SIZE rows at a time)
        if reset:
            for item in tree.get_children():
                tree.delete(item)
            tree._page_offset = 0
            tree._all_loaded  = False

        rows = self.db.fetch_page(table_name, offset=tree._page_offset, limit=PAGE_SIZE)

        for row in rows:
            tree.insert("", "end", values=row)

        tree._page_offset += len(rows)

        if len(rows) < PAGE_SIZE:
            tree._all_loaded = True

        total = self.db.count_rows(table_name)
        self.status_var.set(f"{table_name} — showing {min(tree._page_offset, total)} of {total} records")

    def _check_load_more(self, tree):                   # Load the next page when the user is close to the last visible row.
        if tree._all_loaded:
            return

        children = tree.get_children()
        if not children:
            return

        last_visible = tree.bbox(children[-1])
        if last_visible:                        # row is actually in view
            self.load_tree_data(tree, tree.table_name, reset=False)

    def hide_columns(self, tree):           # COLUMN VISIBILITY
        columns = tree["columns"]
        visible = []

        if "id" in columns:
            visible.append("id")

        for col in columns:
            if "inv" in col.lower() or "inventory" in col.lower():
                visible.append(col)
                break

        tree["displaycolumns"] = visible

    def toggle_columns(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        tree = self.notebook.nametowidget(current_tab).tree

        if not self.show_all_columns:
            tree["displaycolumns"] = tree["columns"]
            self.show_all_columns  = True
            self.show_btn.config(text="Hide Data")
        else:
            self.hide_columns(tree)
            self.show_all_columns = False
            self.show_btn.config(text="Show Data")

    def search_data(self, event=None):                              #SEARCH
        current_tab = self.notebook.select()
        if not current_tab:
            return

        tree        = self.notebook.nametowidget(current_tab).tree
        table_name  = tree.table_name
        search_text = self.search_var.get().strip()

        for item in tree.get_children():
            tree.delete(item)

        if not search_text:
            tree._page_offset = 0
            tree._all_loaded  = False
            self.load_tree_data(tree, table_name)
            return

        rows = self.db.search(table_name, search_text)

        for row in rows:
            tree.insert("", "end", values=row)
            
        tree._all_loaded = True             # Mark as fully loaded so scroll-pagination doesn't interfere
        self.status_var.set(f"Records Found : {len(rows)}")

    def clear_search(self):
        self.search_var.set("")
        self.search_data()

    # REFRESH
    def refresh_current_tab(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        tree       = self.notebook.nametowidget(current_tab).tree
        table_name = tree.table_name

        self.load_tree_data(tree, table_name, reset=True)

        if not self.show_all_columns:
            self.hide_columns(tree)

    # ADD RECORD
    def save_record(self, table_name, entries, window):
        data = {col: entry.get().strip() for col, entry in entries.items()}

        try:
            self.db.insert_row(table_name, data)

            inv_no = next(
                (v for k, v in data.items() if "inv" in k.lower()), ""
            )
            log_action("ADD RECORD", f"Table={table_name} | Inv No={inv_no}")

            self.refresh_current_tab()
            self.status_var.set("Record Added Successfully")
            window.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_add_window(self, table_name, columns):
        win = tk.Toplevel(self.root)
        win.title(f"Add Record - {table_name}")
        win.geometry("500x500")
        win.transient(self.root)
        win.grab_set()

        entries    = {}
        form_frame = tk.Frame(win)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)

        for col in columns:
            row = tk.Frame(form_frame)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=col, width=20, anchor="w").pack(side="left")
            ent = tk.Entry(row)
            ent.pack(side="left", fill="x", expand=True)
            entries[col] = ent

        tk.Button(
            win,
            text="Save Record",
            width=15,
            command=lambda: self.save_record(table_name, entries, win)
        ).pack(pady=10)

    def add_record(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        tree       = self.notebook.nametowidget(current_tab).tree
        table_name = tree.table_name
        columns    = self.db.get_columns(table_name)

        editable = [c for c in columns if c not in ("id", "last_modified")]
        self.open_add_window(table_name, editable)

    # EDIT RECORD
    def update_record(self, table_name, record_id, entries, window):
        updated_data = {col: entry.get().strip() for col, entry in entries.items()}

        try:
            self.db.update_row(table_name, record_id, updated_data)
            log_action("EDIT RECORD", f"Table={table_name} | ID={record_id}")
            self.refresh_current_tab()
            self.status_var.set("Record Updated Successfully")
            window.destroy()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def open_edit_window(self, table_name, columns, values):
        win = tk.Toplevel(self.root)
        win.title(f"Edit Record - {table_name}")
        win.geometry("500x500")
        win.transient(self.root)
        win.grab_set()
        entries    = {}
        form_frame = tk.Frame(win)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        record_id   = values[0]
        value_index = 1

        for col in columns:
            if col in ("id", "last_modified"):
                continue

            row = tk.Frame(form_frame)
            row.pack(fill="x", pady=5)
            tk.Label(row, text=col, width=20, anchor="w").pack(side="left")
            entry = tk.Entry(row)
            entry.pack(side="left", fill="x", expand=True)

            if value_index < len(values):
                entry.insert(0, str(values[value_index]))

            entries[col]  = entry
            value_index  += 1

        tk.Button(
            win,
            text="Update Record",
            command=lambda: self.update_record(table_name, record_id, entries, win)
        ).pack(pady=10)

    def edit_record(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        tree     = self.notebook.nametowidget(current_tab).tree
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Select a record first.")
            return

        values     = tree.item(selected[0])["values"]
        table_name = tree.table_name
        columns    = self.db.get_columns(table_name)

        self.open_edit_window(table_name, columns, values)

    # DELETE RECORD

    def delete_record(self):
        current_tab = self.notebook.select()
        if not current_tab:
            return

        tree     = self.notebook.nametowidget(current_tab).tree
        selected = tree.selection()

        if not selected:
            messagebox.showwarning("Warning", "Please select a record.")
            return

        if not messagebox.askyesno("Delete Record", "Are you sure you want to delete this record?"):
            return

        values = tree.item(selected[0])["values"]
        if not values:
            return

        record_id = values[0]

        try:
            self.db.delete_row(tree.table_name, record_id)
            log_action("DELETE RECORD", f"Table={tree.table_name} | ID={record_id}")
            self.refresh_current_tab()
            self.status_var.set(f"Record {record_id} Deleted")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # EXPORT CSV
    def export_csv(self):
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showwarning("Warning", "No tab selected.")
            return

        tree       = self.notebook.nametowidget(current_tab).tree
        table_name = tree.table_name

        file_path = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile=f"{table_name}.csv"
        )

        if not file_path:
            return
        try:
            self.csv_handler.export_csv(table_name, file_path)
            log_action("EXPORT CSV", f"Table={table_name} | File={file_path}")
            self.status_var.set(f"Exported : {table_name}")
            messagebox.showinfo("Success", "CSV Exported Successfully")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # BACKUP DATABASE
    def backup_database(self):
        try:
            os.makedirs("backups", exist_ok=True)
            timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join("backups", f"inventory_{timestamp}.db")

            shutil.copy("inventory.db", backup_file)
            log_action("DATABASE BACKUP", backup_file)

            self.status_var.set("Database Backup Created")
            messagebox.showinfo("Success", f"Backup Created\n\n{backup_file}")

        except Exception as e:
            messagebox.showerror("Backup Error", str(e))

    # LOGS WINDOW
    def view_logs(self):
        log_window = tk.Toplevel(self.root)
        log_window.title("Activity Logs")
        log_window.geometry("800x500")

        text_frame = tk.Frame(log_window)
        text_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_area = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set)
        text_area.pack(fill="both", expand=True)
        scrollbar.config(command=text_area.yview)

        text_area.insert("1.0", read_logs())
        text_area.config(state="disabled")

        btn_frame = tk.Frame(log_window)
        btn_frame.pack(fill="x", pady=5)

        tk.Button(
            btn_frame,
            text="Clear Logs",
            command=lambda: self.clear_logs_window(text_area)
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Close",
            command=log_window.destroy
        ).pack(side="right", padx=10)

    def clear_logs_window(self, text_widget):
        if not messagebox.askyesno("Clear Logs", "Delete all activity logs?"):
            return
        clear_logs()
        log_action("LOGS CLEARED")

        text_widget.config(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", read_logs())
        text_widget.config(state="disabled")

        self.status_var.set("Logs Cleared")

    # UI SETUP
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#2C3E50", height=50)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(True)

        tk.Label(
            header_frame,
            text="InvMS : Inventory Management",
            bg="#2C3E50",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=15)

        # Search frame
        search_frame = tk.Frame(self.root)
        search_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(search_frame, text="Search :").pack(side="left")

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.search_data)

        tk.Button(
            search_frame,
            text="Clear",
            command=self.clear_search
        ).pack(side="left", padx=5)

        # Button frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        self.show_btn = tk.Button(
            btn_frame, text="Show Data", width=12, command=self.toggle_columns
        )
        self.show_btn.pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Add", width=12, command=self.add_record
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Edit", width=12, command=self.edit_record
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Delete", width=12, command=self.delete_record
        ).pack(side="left", padx=5)

        self.import_btn = tk.Button(
            btn_frame, text="Import CSV", width=12, command=self.import_csv
        )
        self.import_btn.pack(side="left", padx=5)

        tk.Button(
            btn_frame, text="Export CSV", width=12, command=self.export_csv
        ).pack(side="left", padx=5)

        # Advance menu
        advance_btn = tk.Menubutton(btn_frame, text="Advance", relief="raised")
        advance_btn.pack(side="left", padx=5)

        advance_menu = tk.Menu(advance_btn, tearoff=0)
        advance_menu.add_command(label="Backup Database", command=self.backup_database)
        advance_menu.add_command(label="View Logs",       command=self.view_logs)
        advance_btn.config(menu=advance_menu)

        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)  # bound ONCE

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief="sunken",
            anchor="w"
        ).pack(fill="x", side="bottom")

    # TAB CHANGE
    def on_tab_change(self, event=None):
        # Called once per real tab change (binding is set up once in setup_ui).
        self.search_data()

# =============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app  = InventoryApp(root)
    root.mainloop()