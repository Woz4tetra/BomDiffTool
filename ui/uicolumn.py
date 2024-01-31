import os
import platform
import tkinter as tk
from tkinter import filedialog, messagebox

from bom import OnshapeStructured, PropelStructured, SolidworksStructured, StructuredBOM
from logger import LoggerManager

from .tool_tip import create_tool_tip

logger = LoggerManager.get_logger()

BOM_TYPES = {
    "solidworks": SolidworksStructured,
    "propel": PropelStructured,
    "onshape": OnshapeStructured,
    "generic": StructuredBOM,
}

BOM_KEYS = ["solidworks", "propel", "onshape", "generic"]
BOM_VALUES = {key: i for i, key in enumerate(BOM_KEYS)}


class UiColumn:
    def __init__(self, window, column, start_row, config):
        logger.debug("Creating UI column %s" % column)
        self.entry = None
        self.label = None
        self.open_button = None
        self.radio_buttons = []
        self.to_json_button = None

        self.config = config

        self.window = window
        self.column = column
        self.start_row = start_row

        self.entry_text = tk.StringVar()
        self.label_text = tk.StringVar()
        self.bom_type_info_text = tk.StringVar()
        self.bom_type_var = tk.IntVar()

        self.entry_text.trace(
            "w",
            lambda name, index, mode, string_var=self.entry_text: self.entry_callback(
                string_var
            ),
        )
        logger.debug("%s UI column created successfully" % self.log_prefix())

    def make(self):
        self.make_label()
        self.make_entry()
        self.make_open_button()
        self.make_info_label()
        self.make_bom_type_selector()
        self.make_extra_buttons()

    def make_extra_buttons(self):
        button_frame = tk.Frame(master=self.window)
        button_frame.grid(
            row=self.start_row + 5, column=self.column, sticky="n", padx=5, pady=5
        )
        self.make_to_json_button(button_frame)
        self.make_flatten_button(button_frame)

    def make_entry(self):
        entry_frame = tk.Frame(master=self.window, relief=tk.RAISED, borderwidth=1)
        entry_frame.grid(
            row=self.start_row + 1, column=self.column, padx=5, pady=5, sticky="nwe"
        )
        self.entry = tk.Entry(master=entry_frame, textvariable=self.entry_text)
        self.entry.pack(fill=tk.X)

    def entry_callback(self, string_var):
        path = string_var.get()
        text = os.path.basename(path)
        self.update_label(text)
        logger.debug("%s Entry callback: %s" % (self.log_prefix(), path))

    def make_label(self):
        self.default_label_text()

        label_frame = tk.Frame(
            master=self.window,
            # relief=tk.RAISED,
            borderwidth=1,
        )
        label_frame.grid(row=self.start_row, column=self.column)
        self.label = tk.Label(master=label_frame, textvariable=self.label_text)
        self.label.pack(fill=tk.X)

    def default_label_text(self):
        text = "Left BOM" if self.column == 0 else "Right BOM"
        self.label_text.set(text)
        logger.debug("%s Set label to default: %s" % (self.log_prefix(), text))

    def get_column_name(self):
        if self.column == 0:
            return "left"
        elif self.column == 1:
            return "right"
        else:
            return "unknown"

    def log_prefix(self):
        return "[%s]" % self.get_column_name()

    def make_open_button(self):
        button_frame = tk.Frame(master=self.window, relief=tk.RAISED, borderwidth=1)
        button_frame.grid(row=self.start_row + 2, column=self.column, padx=5, pady=5)
        self.open_button = tk.Button(
            master=button_frame, text="Browse", command=self.open_button_fn
        )
        self.open_button.pack()

    def make_info_label(self):
        label_frame = tk.Frame(
            master=self.window,
            # relief=tk.RAISED,
            borderwidth=1,
        )
        label_frame.grid(row=self.start_row + 3, column=self.column)
        self.label = tk.Label(master=label_frame, textvariable=self.bom_type_info_text)
        self.bom_type_info_text.set("BOM Structure")
        self.label.pack(fill=tk.X)

    def make_bom_type_selector(self):
        type_frame = tk.Frame(
            master=self.window,
            # relief=tk.RAISED,
            borderwidth=1,
        )
        tool_tips = {
            "solidworks": "For BOMs that use a tree number to indicate structure\n"
            "ex. 1 is the top level. Items 1.1, 1.2, and so on belong to 1\n"
            "This system is utilized by Solidworks",
            "propel": "For BOMs that use a level number to indicate structure\n"
            "ex. 0 is the top level. 1 indicates items belong to the item at level 0\n"
            "This system is utilized by Propel PLM",
            "onshape": "For BOMs that use a tree number to indicate structure\n"
            "ex. 1 is the top level. Items 1.1, 1.2, and so on belong to 1\n"
            "This system is utilized by Onshape",
        }
        type_frame.grid(row=self.start_row + 4, column=self.column, padx=5, pady=5)
        for i, key in enumerate(BOM_KEYS):
            self.radio_buttons.append(
                tk.Radiobutton(
                    master=type_frame,
                    text=key.capitalize(),
                    padx=20,
                    variable=self.bom_type_var,
                    value=i + 1,
                )
            )
            self.radio_buttons[-1].pack(anchor=tk.W)
            tool_tip = tool_tips.get(key, None)
            if tool_tip is not None:
                create_tool_tip(self.radio_buttons[-1], tool_tip)

    def make_to_json_button(self, button_frame):
        self.to_json_button = tk.Button(
            master=button_frame, text="To JSON", command=self.to_json_button_fn
        )
        self.to_json_button.pack(side="left", padx=5)

    def make_flatten_button(self, button_frame):
        self.to_json_button = tk.Button(
            master=button_frame, text="Flatten", command=self.flatten_button_fn
        )
        self.to_json_button.pack(side="left", padx=5)

    def update_label(self, text=None):
        if text is None or len(text) == 0:
            self.default_label_text()
        else:
            self.label_text.set(text)
            logger.debug("%s Set label: %s" % (self.log_prefix(), text))

    def open_button_fn(self):
        logger.debug("%s Open button callback" % self.log_prefix())
        default_path = self.config.get_default_load_dir()
        text_path = self.entry_text.get()
        path = None
        while len(text_path) > 0:
            if os.path.isdir(text_path):
                path = text_path
                break
            else:
                text_path = os.path.dirname(text_path)
        if path is None:
            path = default_path
        if platform.system() == "Darwin":  # macOS
            path = filedialog.askopenfilename(
                initialdir=path,
                title="Select A File",
                # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
                filetype=(("all files", "*.*"),),
            )
        elif platform.system() == "Windows":  # Windows
            path = filedialog.askopenfilename(
                initialdir=path,
                title="Select A File",
                # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
                filetype=(("all files", "*.*"),),
            )
        else:  # linux variants
            path = filedialog.askopenfilename(
                initialdir=path,
                title="Select A File",
                filetypes=(("all files", "*.*"),),
            )

        if len(path) == 0:
            logger.debug("%s Canceling open" % self.log_prefix())
            return
        logger.debug("%s Selected open path: %s" % (self.log_prefix(), path))
        # self.entry.delete(0)
        # self.entry.insert(0, path)
        self.entry_text.set(path)

        text = os.path.basename(path)
        self.update_label(text)

    def to_json_button_fn(self):
        logger.debug("To JSON button callback")
        bom = self.load_bom(self.get_path())
        if bom is None:
            return

        default_name = os.path.splitext(bom.name)[0] + ".json"
        default_path = self.config.get_default_save_dir()
        if platform.system() == "Darwin":  # macOS
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Export to JSON",
                filetype=(("JSON", "*.json"),),
                initialfile=default_name,
            )
        elif platform.system() == "Windows":  # Windows
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Export to JSON",
                # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
                filetype=(("JSON", "*.json"),),
                initialfile=default_name,
            )
        else:  # linux variants
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Export to JSON",
                filetypes=(("JSON", "*.json"),),
                initialfile=default_name,
            )

        if len(output_path) == 0:
            logger.debug("Canceling JSON export")
            return

        try:
            bom.to_json(output_path)
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while flattening BOM! See logs for details.\n%s"
                % str(e),
            )
            return False

    def flatten_button_fn(self):
        logger.debug("Flatten button callback")
        bom = self.load_bom(self.get_path())
        if bom is None:
            return

        default_name = os.path.splitext(bom.name)[0] + "-flattened.csv"
        default_path = self.config.get_default_save_dir()
        if platform.system() == "Darwin":  # macOS
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Flatten BOM",
                filetype=(("CSV", "*.csv"),),
                initialfile=default_name,
            )
        elif platform.system() == "Windows":  # Windows
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Flatten BOM",
                # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
                filetype=(("CSV", "*.csv"),),
                initialfile=default_name,
            )
        else:  # linux variants
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Flatten BOM",
                filetypes=(("CSV", "*.csv"),),
                initialfile=default_name,
            )

        if len(output_path) == 0:
            logger.debug("Canceling flatten export")
            return

        try:
            bom.flattened_to_csv(output_path)
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while analyzing BOMs! See logs for details.\n%s"
                % str(e),
            )
            return False

    def get_path(self):
        return self.entry.get()

    def get_bom_type(self):
        value = self.bom_type_var.get()
        bom_type = BOM_KEYS[value - 1]

        logger.debug("%s BOM type: %s" % (self.log_prefix(), bom_type))
        return bom_type

    def set_bom_type(self, name):
        name = name.lower()
        logger.debug("%s setting BOM type: %s" % (self.log_prefix(), name))
        self.bom_type_var.set(BOM_VALUES[name] + 1)

    def set_entry_text(self, text):
        self.entry_text.set(text)

    def get_entry_text(self):
        return self.entry_text.get()

    def load_bom(self, path, skip_checks=False):
        logger.debug("%s Attempting to open BOM from %s" % (self.log_prefix(), path))

        try:
            bom_type = self.get_bom_type()
            bom = BOM_TYPES[bom_type].from_file(path)
            logger.debug(
                "%s Opened %s BOM from %s" % (self.log_prefix(), bom_type, path)
            )

            bom.set_diff_props(self.config.diff_properties)
            return bom
        except BaseException as e:
            if skip_checks:
                raise
            else:
                logger.error("%s %s" % (self.log_prefix(), str(e)), exc_info=True)
                messagebox.showerror(
                    "Error",
                    "An error occurred while loading BOMs! See logs for details.\n%s"
                    % str(e),
                )
                return None
