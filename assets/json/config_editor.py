#!/usr/bin/env python3
"""
Game Config Editor
===================

A lightweight GUI for editing large data-driven JSON config files like the
one used by this game (Item, Emitter, Explosion, Missile, Sound, ...).

Design goals
------------
- Sits ABOVE raw JSON editing: you browse Category -> Entry -> Fields,
  and edit each field with an appropriate widget (text box, checkbox,
  list editor, reference picker) instead of hand-typing braces and commas.
- Sits BELOW a fully custom per-category UI: every category is handled
  generically by reading its "$DATA_TYPE" schema block. Add a new field to
  a schema, or a whole new category, and the editor already understands it
  -- no code changes needed.
- Never takes control away: every entry also has a "Raw JSON" tab (full
  text control), and any field present in the data but not declared in the
  schema still shows up, editable, under "Other fields".

Extra tools
-----------
- "Link..." buttons next to string fields let you insert a "#Category.ID"
  reference by picking from existing entries, instead of typing it by hand.
- Tools > Find broken references scans the whole file for "#Category.ID"
  strings that don't point at anything that exists.
- Renaming/deleting an entry warns you if other entries reference it.
- Saving writes a ".bak" copy of the previous file next to it.

Run
---
    python3 config_editor.py [path/to/config.json]

Requires only the Python standard library (tkinter).
"""

import copy
import json
import os
import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

SCHEMA_KEY = "$DATA_TYPE"
NON_CATEGORY_KEYS = {"ConfigVersion"}
REF_RE = re.compile(r"^#([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)$")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def is_ref(value):
    return isinstance(value, str) and bool(REF_RE.match(value))


def parse_ref(value):
    m = REF_RE.match(value) if isinstance(value, str) else None
    return (m.group(1), m.group(2)) if m else None


def default_for_type(ftype):
    if ftype == "String":
        return ""
    if ftype == "Integer":
        return 0
    if ftype == "Float":
        return 0.0
    if ftype == "Boolean":
        return False
    if ftype == "Object":
        return {}
    if isinstance(ftype, str) and ftype.startswith("List:"):
        return []
    return None


def coerce_scalar(text, ftype):
    text = text if isinstance(text, str) else str(text)
    if ftype == "Integer":
        try:
            return int(text)
        except ValueError:
            return text
    if ftype == "Float":
        try:
            return float(text)
        except ValueError:
            return text
    if ftype == "Boolean":
        return text.strip().lower() in ("true", "1", "yes")
    return text


def _contains_value(node, needle):
    if isinstance(node, dict):
        return any(_contains_value(v, needle) for v in node.values())
    if isinstance(node, list):
        return any(_contains_value(v, needle) for v in node)
    return node == needle


# ---------------------------------------------------------------------------
# data layer
# ---------------------------------------------------------------------------

class ConfigStore:
    """Wraps the loaded JSON and provides category/entry/schema helpers."""

    def __init__(self, path=None):
        self.path = None
        self.data = {}
        if path:
            self.load(path)

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.path = path

    def save(self, path=None):
        path = path or self.path
        if not path:
            raise ValueError("No path to save to")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    backup = f.read()
                with open(path + ".bak", "w", encoding="utf-8") as f:
                    f.write(backup)
            except OSError:
                pass
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        self.path = path

    def categories(self):
        return sorted(
            k for k, v in self.data.items()
            if k not in NON_CATEGORY_KEYS and isinstance(v, dict)
        )

    def schema(self, category):
        return self.data.get(category, {}).get(SCHEMA_KEY, {})

    def entry_ids(self, category):
        cat = self.data.get(category, {})
        return sorted(k for k in cat.keys() if k != SCHEMA_KEY)

    def get_entry(self, category, entry_id):
        return self.data[category][entry_id]

    def set_entry(self, category, entry_id, value):
        self.data.setdefault(category, {})[entry_id] = value

    def delete_entry(self, category, entry_id):
        del self.data[category][entry_id]

    def rename_entry(self, category, old_id, new_id):
        cat = self.data[category]
        if new_id in cat:
            raise ValueError(f"'{new_id}' already exists in {category}")
        entry = cat.pop(old_id)
        if isinstance(entry, dict) and "ID" in entry:
            entry["ID"] = new_id
        cat[new_id] = entry

    def new_entry_from_schema(self, category, entry_id):
        schema = self.schema(category)
        entry = {field: default_for_type(ftype) for field, ftype in schema.items()}
        if "ID" in entry:
            entry["ID"] = entry_id
        return entry

    def ref_targets(self, category, entry_id):
        """Entries elsewhere in the config that reference this one."""
        needle = f"#{category}.{entry_id}"
        hits = []
        for cat, block in self.data.items():
            if not isinstance(block, dict):
                continue
            for eid, entry in block.items():
                if eid == SCHEMA_KEY:
                    continue
                if _contains_value(entry, needle):
                    hits.append((cat, eid))
        return hits

    def find_broken_references(self):
        broken = []

        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    walk(v, path + [k])
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, path + [f"[{i}]"])
            elif is_ref(node):
                cat, eid = parse_ref(node)
                if cat not in self.data or eid not in self.data.get(cat, {}):
                    broken.append((".".join(path), node))

        for cat, block in self.data.items():
            if cat in NON_CATEGORY_KEYS or not isinstance(block, dict):
                continue
            for eid, entry in block.items():
                if eid == SCHEMA_KEY:
                    continue
                walk(entry, [cat, eid])
        return broken


# ---------------------------------------------------------------------------
# small dialogs
# ---------------------------------------------------------------------------

class ReferencePickerDialog:
    """Modal dialog: pick Category + Entry, returns '#Category.ID' or None."""

    @staticmethod
    def ask(parent, app, preselect_category=None):
        win = tk.Toplevel(parent)
        win.title("Insert reference")
        win.transient(parent)
        win.grab_set()
        win.resizable(False, False)
        result = {"value": None}

        cats = app.store.categories()

        ttk.Label(win, text="Category:").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 2))
        cat_var = tk.StringVar(value=preselect_category if preselect_category in cats
                                else (cats[0] if cats else ""))
        cat_cb = ttk.Combobox(win, textvariable=cat_var, values=cats, state="readonly", width=32)
        cat_cb.grid(row=0, column=1, padx=8, pady=(8, 2))

        ttk.Label(win, text="Entry:").grid(row=1, column=0, sticky="w", padx=8, pady=2)
        id_var = tk.StringVar()
        id_cb = ttk.Combobox(win, textvariable=id_var, values=[], state="readonly", width=32)
        id_cb.grid(row=1, column=1, padx=8, pady=2)

        def refresh_ids(*_):
            ids = app.store.entry_ids(cat_var.get()) if cat_var.get() else []
            id_cb["values"] = ids
            id_var.set(ids[0] if ids else "")

        cat_cb.bind("<<ComboboxSelected>>", refresh_ids)
        refresh_ids()

        def on_ok():
            if cat_var.get() and id_var.get():
                result["value"] = f"#{cat_var.get()}.{id_var.get()}"
            win.destroy()

        btns = ttk.Frame(win)
        btns.grid(row=2, column=0, columnspan=2, pady=8)
        ttk.Button(btns, text="Insert", command=on_ok).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=4)
        win.bind("<Return>", lambda e: on_ok())
        win.bind("<Escape>", lambda e: win.destroy())

        win.wait_window()
        return result["value"]


class ValueDialog:
    """Modal dialog: edit a single scalar value, with an optional Link button."""

    @staticmethod
    def ask(parent, app, title, initial, item_type="String"):
        win = tk.Toplevel(parent)
        win.title(title)
        win.transient(parent)
        win.grab_set()
        result = {"value": None}

        ttk.Label(win, text=f"Value ({item_type}):").pack(anchor="w", padx=8, pady=(8, 0))
        var = tk.StringVar(value=initial)
        entry = ttk.Entry(win, textvariable=var, width=50)
        entry.pack(fill="x", padx=8, pady=4)
        entry.focus_set()
        entry.select_range(0, "end")

        def do_link():
            pre = parse_ref(var.get())
            ref = ReferencePickerDialog.ask(win, app, preselect_category=pre[0] if pre else None)
            if ref:
                var.set(ref)

        if item_type == "String":
            ttk.Button(win, text="Link reference...", command=do_link).pack(anchor="w", padx=8)

        def on_ok():
            result["value"] = var.get()
            win.destroy()

        btns = ttk.Frame(win)
        btns.pack(fill="x", padx=8, pady=8)
        ttk.Button(btns, text="OK", command=on_ok).pack(side="right")
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right", padx=(0, 4))
        win.bind("<Return>", lambda e: on_ok())
        win.bind("<Escape>", lambda e: win.destroy())

        win.wait_window()
        return result["value"]


# ---------------------------------------------------------------------------
# field widgets
# ---------------------------------------------------------------------------

class ListEditorFrame(ttk.Frame):
    """Editor for a List:<Type> field: listbox + add/edit/remove/move."""

    def __init__(self, master, item_type, values, app):
        super().__init__(master)
        self.item_type = item_type
        self.app = app

        self.listbox = tk.Listbox(self, height=5, exportselection=False)
        self.listbox.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.listbox.yview)
        sb.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=sb.set)

        btns = ttk.Frame(self)
        btns.pack(side="left", fill="y", padx=(4, 0))
        ttk.Button(btns, text="Add", width=8, command=self.add_item).pack(fill="x")
        ttk.Button(btns, text="Edit", width=8, command=self.edit_item).pack(fill="x")
        ttk.Button(btns, text="Remove", width=8, command=self.remove_item).pack(fill="x")
        ttk.Button(btns, text="Up", width=8, command=lambda: self.move(-1)).pack(fill="x")
        ttk.Button(btns, text="Down", width=8, command=lambda: self.move(1)).pack(fill="x")

        for v in values or []:
            self.listbox.insert("end", str(v))
        self.listbox.bind("<Double-Button-1>", lambda e: self.edit_item())

    def add_item(self):
        val = ValueDialog.ask(self, self.app, "New item", "", item_type=self.item_type)
        if val is not None:
            self.listbox.insert("end", val)

    def edit_item(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        val = ValueDialog.ask(self, self.app, "Edit item", self.listbox.get(idx), item_type=self.item_type)
        if val is not None:
            self.listbox.delete(idx)
            self.listbox.insert(idx, val)
            self.listbox.selection_set(idx)

    def remove_item(self):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.delete(sel[0])

    def move(self, direction):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        new_idx = idx + direction
        if 0 <= new_idx < self.listbox.size():
            val = self.listbox.get(idx)
            self.listbox.delete(idx)
            self.listbox.insert(new_idx, val)
            self.listbox.selection_set(new_idx)

    def get_values(self):
        return [coerce_scalar(v, self.item_type) for v in self.listbox.get(0, "end")]


class RawJsonFrame(ttk.Frame):
    """Full-control raw JSON view/edit for the current entry."""

    def __init__(self, master, entry_data):
        super().__init__(master)
        self.text = tk.Text(self, wrap="none", undo=True)
        self.text.insert("1.0", json.dumps(entry_data, indent=2))
        ysb = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        xsb = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def get_data(self):
        return json.loads(self.text.get("1.0", "end"))


class EntryFormFrame(ttk.Frame):
    """Auto-generated form for one entry, built from its category's schema."""

    def __init__(self, master, app, category, entry_id, entry_data):
        super().__init__(master)
        self.app = app
        self.category = category
        self.entry_id = entry_id
        self.schema = app.store.schema(category)
        self.entry_data = entry_data
        self.field_widgets = {}   # field -> getter()
        self.extra_rows = {}      # key -> StringVar
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_inner_config(_):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", on_inner_config)

        def on_canvas_config(e):
            canvas.itemconfig(window, width=e.width)
        canvas.bind("<Configure>", on_canvas_config)

        def wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        def wheel_linux(e):
            canvas.yview_scroll(-1 if e.num == 4 else 1, "units")

        def bind_wheel(_):
            canvas.bind_all("<MouseWheel>", wheel)
            canvas.bind_all("<Button-4>", wheel_linux)
            canvas.bind_all("<Button-5>", wheel_linux)

        def unbind_wheel(_):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", bind_wheel)
        canvas.bind("<Leave>", unbind_wheel)

        row = 0
        ttk.Label(inner, text=f"{self.category} - schema fields", font=("", 10, "bold")) \
            .grid(row=row, column=0, columnspan=3, sticky="w", pady=(4, 6))
        row += 1

        for field, ftype in self.schema.items():
            row = self._add_field_row(inner, row, field, ftype,
                                       self.entry_data.get(field, default_for_type(ftype)))

        row += 1
        ttk.Separator(inner, orient="horizontal").grid(row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1
        header_row = row
        ttk.Label(inner, text="Other fields (not declared in schema)", font=("", 10, "bold")) \
            .grid(row=row, column=0, columnspan=2, sticky="w")
        ttk.Button(inner, text="+ Add field", command=self._add_extra_field_prompt) \
            .grid(row=header_row, column=2, sticky="e")
        row += 1

        self.extra_container = ttk.Frame(inner)
        self.extra_container.grid(row=row, column=0, columnspan=3, sticky="ew")

        for key, value in self.entry_data.items():
            if key in self.schema:
                continue
            self._add_extra_row(key, value)

        inner.grid_columnconfigure(1, weight=1)

    def _add_field_row(self, parent, row, field, ftype, value):
        ttk.Label(parent, text=field).grid(row=row, column=0, sticky="nw", padx=(4, 8), pady=3)
        wrap = ttk.Frame(parent)
        wrap.grid(row=row, column=1, columnspan=2, sticky="ew", pady=3)

        if ftype == "Boolean":
            var = tk.BooleanVar(value=bool(value))
            ttk.Checkbutton(wrap, variable=var).pack(side="left")
            self.field_widgets[field] = (lambda v=var: v.get())

        elif ftype == "Object":
            text = tk.Text(wrap, height=3, width=50, wrap="word")
            text.insert("1.0", json.dumps(value, indent=2) if value not in (None, "") else "{}")
            text.pack(side="left", fill="x", expand=True)
            self.field_widgets[field] = (lambda t=text: self._parse_json_or_text(t.get("1.0", "end")))

        elif isinstance(ftype, str) and ftype.startswith("List:"):
            item_type = ftype.split(":", 1)[1]
            lst = ListEditorFrame(wrap, item_type, value if isinstance(value, list) else [], self.app)
            lst.pack(fill="x", expand=True)
            self.field_widgets[field] = lst.get_values

        else:  # String / Integer / Float / anything else -> plain entry
            var = tk.StringVar(value="" if value is None else str(value))
            entry = ttk.Entry(wrap, textvariable=var)
            entry.pack(side="left", fill="x", expand=True)
            if ftype == "String":
                ttk.Button(wrap, text="Link...", width=7,
                           command=lambda v=var: self._link(v)).pack(side="left", padx=(4, 0))
            self.field_widgets[field] = (lambda v=var, t=ftype: coerce_scalar(v.get(), t))

        return row + 1

    def _link(self, var):
        pre = parse_ref(var.get())
        ref = ReferencePickerDialog.ask(self, self.app, preselect_category=pre[0] if pre else None)
        if ref:
            var.set(ref)

    @staticmethod
    def _parse_json_or_text(text):
        text = text.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def _add_extra_field_prompt(self):
        key = simpledialog.askstring("Add field", "New field name:", parent=self)
        if not key:
            return
        if key in self.schema or key in self.extra_rows:
            messagebox.showwarning("Field exists", f"'{key}' already exists on this entry.")
            return
        self._add_extra_row(key, "")

    def _add_extra_row(self, key, value):
        row_frame = ttk.Frame(self.extra_container)
        row_frame.pack(fill="x", pady=2)
        ttk.Label(row_frame, text=key, width=22).pack(side="left")
        text_value = value if isinstance(value, str) else json.dumps(value)
        var = tk.StringVar(value=text_value)
        ttk.Entry(row_frame, textvariable=var).pack(side="left", fill="x", expand=True, padx=4)

        def remove():
            row_frame.destroy()
            del self.extra_rows[key]

        ttk.Button(row_frame, text="x", width=3, command=remove).pack(side="left")
        self.extra_rows[key] = var

    def get_data(self):
        data = {}
        for field in self.schema:
            getter = self.field_widgets[field]
            try:
                data[field] = getter()
            except Exception as e:
                raise ValueError(f"Field '{field}': {e}")
        for key, var in self.extra_rows.items():
            raw = var.get()
            try:
                data[key] = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                data[key] = raw
        return data


# ---------------------------------------------------------------------------
# main app
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self, initial_path=None):
        super().__init__()
        self.title("Game Config Editor")
        self.geometry("1250x780")
        self.store = ConfigStore()
        self.current_category = None
        self.current_entry_id = None
        self._cat_names = []
        self._entry_ids_shown = []
        self.form_frame = None
        self.raw_frame = None

        self._build_menu()
        self._build_layout()

        if initial_path:
            self.load_file(initial_path)

    # ---- menu ----
    def _build_menu(self):
        menubar = tk.Menu(self)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        filemenu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        filemenu.add_command(label="Save As...", command=self.save_file_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=filemenu)

        toolsmenu = tk.Menu(menubar, tearoff=0)
        toolsmenu.add_command(label="Find broken references...", command=self.find_broken_refs)
        menubar.add_cascade(label="Tools", menu=toolsmenu)

        self.config(menu=menubar)
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())

    # ---- layout ----
    def _build_layout(self):
        self.status_var = tk.StringVar(value="No file loaded")
        ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken") \
            .pack(side="bottom", fill="x")

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # categories
        cat_frame = ttk.Frame(paned, width=200)
        ttk.Label(cat_frame, text="Categories", font=("", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        self.cat_list = tk.Listbox(cat_frame, exportselection=False)
        self.cat_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.cat_list.bind("<<ListboxSelect>>", self.on_category_select)
        paned.add(cat_frame, weight=0)

        # entries
        entry_frame = ttk.Frame(paned, width=260)
        ttk.Label(entry_frame, text="Entries", font=("", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_entry_list())
        ttk.Entry(entry_frame, textvariable=self.search_var).pack(fill="x", padx=4)
        self.entry_list = tk.Listbox(entry_frame, exportselection=False)
        self.entry_list.pack(fill="both", expand=True, padx=4, pady=4)
        self.entry_list.bind("<<ListboxSelect>>", self.on_entry_select)

        entry_btns = ttk.Frame(entry_frame)
        entry_btns.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Button(entry_btns, text="New", command=self.new_entry).pack(side="left", expand=True, fill="x")
        ttk.Button(entry_btns, text="Duplicate", command=self.duplicate_entry).pack(side="left", expand=True, fill="x")
        ttk.Button(entry_btns, text="Rename", command=self.rename_entry).pack(side="left", expand=True, fill="x")
        ttk.Button(entry_btns, text="Delete", command=self.delete_entry).pack(side="left", expand=True, fill="x")
        paned.add(entry_frame, weight=0)

        # detail
        detail_frame = ttk.Frame(paned)
        top_bar = ttk.Frame(detail_frame)
        top_bar.pack(fill="x", padx=4, pady=4)
        self.detail_title = ttk.Label(top_bar, text="(select an entry)", font=("", 11, "bold"))
        self.detail_title.pack(side="left")
        ttk.Button(top_bar, text="References...", command=self.show_references).pack(side="right")
        ttk.Button(top_bar, text="Apply changes", command=self.apply_changes).pack(side="right", padx=4)

        self.detail_notebook = ttk.Notebook(detail_frame)
        self.detail_notebook.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        paned.add(detail_frame, weight=1)

    # ---- file ops ----
    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            self.load_file(path)

    def load_file(self, path):
        try:
            self.store.load(path)
        except Exception as e:
            messagebox.showerror("Failed to open", str(e))
            return
        self.title(f"Game Config Editor - {os.path.basename(path)}")
        self.status_var.set(f"Loaded {path}")
        self.refresh_category_list()
        self.clear_detail()

    def save_file(self):
        if not self.store.path:
            return self.save_file_as()
        try:
            self.store.save()
        except Exception as e:
            messagebox.showerror("Failed to save", str(e))
            return
        self.status_var.set(f"Saved {self.store.path}")

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if path:
            try:
                self.store.save(path)
            except Exception as e:
                messagebox.showerror("Failed to save", str(e))
                return
            self.title(f"Game Config Editor - {os.path.basename(path)}")
            self.status_var.set(f"Saved {path}")

    # ---- categories ----
    def refresh_category_list(self):
        self.cat_list.delete(0, "end")
        self._cat_names = self.store.categories()
        for c in self._cat_names:
            self.cat_list.insert("end", f"{c} ({len(self.store.entry_ids(c))})")

    def on_category_select(self, _event=None):
        sel = self.cat_list.curselection()
        if not sel:
            return
        self.current_category = self._cat_names[sel[0]]
        self.search_var.set("")
        self.refresh_entry_list()
        self.clear_detail()

    # ---- entries ----
    def refresh_entry_list(self):
        self.entry_list.delete(0, "end")
        if not self.current_category:
            self._entry_ids_shown = []
            return
        q = self.search_var.get().lower().strip()
        ids = self.store.entry_ids(self.current_category)
        self._entry_ids_shown = [i for i in ids if q in i.lower()] if q else ids
        for i in self._entry_ids_shown:
            self.entry_list.insert("end", i)

    def on_entry_select(self, _event=None):
        sel = self.entry_list.curselection()
        if not sel or not self.current_category:
            return
        self.load_entry(self.current_category, self._entry_ids_shown[sel[0]])

    def load_entry(self, category, entry_id):
        self.current_entry_id = entry_id
        entry_data = self.store.get_entry(category, entry_id)
        self.detail_title.config(text=f"{category} / {entry_id}")

        for tab in self.detail_notebook.tabs():
            self.detail_notebook.forget(tab)

        self.form_frame = EntryFormFrame(self.detail_notebook, self, category, entry_id, copy.deepcopy(entry_data))
        self.raw_frame = RawJsonFrame(self.detail_notebook, entry_data)
        self.detail_notebook.add(self.form_frame, text="Form")
        self.detail_notebook.add(self.raw_frame, text="Raw JSON")

    def clear_detail(self):
        self.current_entry_id = None
        self.detail_title.config(text="(select an entry)")
        for tab in self.detail_notebook.tabs():
            self.detail_notebook.forget(tab)

    def new_entry(self):
        if not self.current_category:
            messagebox.showinfo("Pick a category", "Select a category first.")
            return
        entry_id = simpledialog.askstring("New entry", "New entry ID:", parent=self)
        if not entry_id:
            return
        if entry_id in self.store.entry_ids(self.current_category):
            messagebox.showerror("Duplicate ID", f"'{entry_id}' already exists.")
            return
        self.store.set_entry(self.current_category, entry_id,
                              self.store.new_entry_from_schema(self.current_category, entry_id))
        self.refresh_category_list()
        self._select_entry_by_id(entry_id)

    def duplicate_entry(self):
        if not (self.current_category and self.current_entry_id):
            return
        new_id = simpledialog.askstring("Duplicate entry", "ID for the copy:", parent=self)
        if not new_id:
            return
        if new_id in self.store.entry_ids(self.current_category):
            messagebox.showerror("Duplicate ID", f"'{new_id}' already exists.")
            return
        data = copy.deepcopy(self.store.get_entry(self.current_category, self.current_entry_id))
        if isinstance(data, dict) and "ID" in data:
            data["ID"] = new_id
        self.store.set_entry(self.current_category, new_id, data)
        self.refresh_category_list()
        self._select_entry_by_id(new_id)

    def rename_entry(self):
        if not (self.current_category and self.current_entry_id):
            return
        new_id = simpledialog.askstring("Rename entry", "New ID:",
                                         initialvalue=self.current_entry_id, parent=self)
        if not new_id or new_id == self.current_entry_id:
            return
        refs = self.store.ref_targets(self.current_category, self.current_entry_id)
        if refs and not messagebox.askyesno(
                "Referenced elsewhere",
                f"'{self.current_entry_id}' is referenced by {len(refs)} other "
                f"entr{'y' if len(refs) == 1 else 'ies'}.\n"
                "Renaming will NOT update those references automatically.\n\nContinue anyway?"):
            return
        try:
            self.store.rename_entry(self.current_category, self.current_entry_id, new_id)
        except ValueError as e:
            messagebox.showerror("Rename failed", str(e))
            return
        self._select_entry_by_id(new_id)

    def delete_entry(self):
        if not (self.current_category and self.current_entry_id):
            return
        refs = self.store.ref_targets(self.current_category, self.current_entry_id)
        warn = f"\n\nWarning: referenced by {len(refs)} other entr{'y' if len(refs) == 1 else 'ies'}." if refs else ""
        if not messagebox.askyesno("Delete entry", f"Delete '{self.current_entry_id}'?{warn}"):
            return
        self.store.delete_entry(self.current_category, self.current_entry_id)
        self.refresh_category_list()
        self.refresh_entry_list()
        self.clear_detail()

    def _select_entry_by_id(self, entry_id):
        self.refresh_entry_list()
        if entry_id in self._entry_ids_shown:
            idx = self._entry_ids_shown.index(entry_id)
            self.entry_list.selection_clear(0, "end")
            self.entry_list.selection_set(idx)
            self.entry_list.see(idx)
            self.load_entry(self.current_category, entry_id)

    # ---- apply / references ----
    def apply_changes(self):
        if not (self.current_category and self.current_entry_id):
            return
        active_tab = self.detail_notebook.index(self.detail_notebook.select())
        try:
            data = self.raw_frame.get_data() if active_tab == 1 else self.form_frame.get_data()
        except Exception as e:
            messagebox.showerror("Invalid data", str(e))
            return
        self.store.set_entry(self.current_category, self.current_entry_id, data)
        self.status_var.set(
            f"Applied changes to {self.current_category}/{self.current_entry_id} "
            f"(in memory only -- use File > Save to write to disk)")
        self.load_entry(self.current_category, self.current_entry_id)

    def show_references(self):
        if not (self.current_category and self.current_entry_id):
            return
        refs = self.store.ref_targets(self.current_category, self.current_entry_id)
        if not refs:
            messagebox.showinfo("References", "No other entry references this one.")
            return
        messagebox.showinfo("Referenced by", "\n".join(f"{c} / {e}" for c, e in sorted(refs)))

    def find_broken_refs(self):
        if not self.store.data:
            messagebox.showinfo("No file", "Open a config file first.")
            return
        broken = self.store.find_broken_references()
        win = tk.Toplevel(self)
        win.title("Broken references")
        win.geometry("750x400")
        text = tk.Text(win, wrap="none")
        text.pack(fill="both", expand=True)
        if not broken:
            text.insert("end", "No broken references found.")
        else:
            for path, ref in broken:
                text.insert("end", f"{path}  ->  {ref}\n")
        text.config(state="disabled")


def main():
    initial = sys.argv[1] if len(sys.argv) > 1 else None
    App(initial).mainloop()


if __name__ == "__main__":
    main()