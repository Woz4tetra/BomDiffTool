import re
import pprint
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

from logger import LoggerManager
from .config import Config
from .tool_tip import create_tool_tip

logger = LoggerManager.get_logger()


class SettingsUi:
    def __init__(self, window, parent_ui, config):
        self.toplevel_window = window
        self.window = None

        # self.tab_control = ttk.Notebook(self.toplevel_window)
        #
        # self.paths_tab = ttk.Frame(self.tab_control)
        # self.properties_tab = ttk.Frame(self.tab_control)
        # self.equivalence_tab = ttk.Frame(self.tab_control)
        #
        # self.tab_control.add(self.paths_tab, text="Paths")
        # self.tab_control.add(self.properties_tab, text="Properties")
        # self.tab_control.add(self.equivalence_tab, text="Equivalence")
        # self.tab_control.pack(expand=1, fill="both")

        # assigned externally
        # noinspection PyTypeChecker
        self.config = config  # type: Config

        self.parent_ui = parent_ui

        self.diff_checkbox_vars = [tk.IntVar() for _ in range(len(self.config.all_property_names))]
        self.show_checkbox_vars = [tk.IntVar() for _ in range(len(self.config.all_property_names))]

        self.primary_radio_btn_var = tk.IntVar()
        self.primary_radio_btn_var.set(0)

        self.diff_checkboxes = []
        self.show_checkboxes = []
        self.primary_radio_btns = []

        self.load_entry_text = tk.StringVar()
        self.save_entry_text = tk.StringVar()
        self.ignored_categories_text = tk.StringVar()

    def get_window_state(self):
        state = "closed"
        if self.window is None:
            state = "not created"
        else:
            try:
                if self.window.state() == "normal":
                    state = "open"
            except tk.TclError:
                state = "remake window"

        logger.debug("Window state: %s" % state)
        return state

    def open(self):
        try:
            window_state = self.get_window_state()
            if window_state == "open":
                self.window.focus()
            elif window_state == "not created" or window_state == "remake window":
                self.make_settings_window()
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror("Error", "Failed to open settings window! See logs for details.\n%s" % str(e))

    def make_settings_window(self):
        logger.debug("Making settings window")
        self.window = tk.Toplevel(self.toplevel_window)
        # col_index = 0
        self.window.columnconfigure(0, weight=1, minsize=50)
        self.window.columnconfigure(1, weight=1, minsize=300)
        self.window.columnconfigure(2, weight=1, minsize=70)
        # for col_index in range(1, 2):
        #     self.window.columnconfigure(col_index, weight=1, minsize=300)
        #     self.window.rowconfigure(col_index, weight=1, minsize=20)

        button_frame = tk.Frame(master=self.window)
        button_frame.grid(row=0, column=0, sticky="W", padx=5, pady=5)
        self.make_save_settings_button(button_frame)
        self.make_save_and_close_settings_button(button_frame)
        self.make_save_settings_as_button(button_frame)
        self.make_load_settings_button(button_frame)

        self.make_label(self.window, 1, 0, "Default Load Folder")
        self.make_entry(1, 1, self.load_entry_text, self.config.get_default_load_dir(), self.load_dir_entry_callback)
        self.make_open_button(1, 2, self.open_load_button_fn)

        self.make_label(self.window, 2, 0, "Default Save Folder")
        self.make_entry(2, 1, self.save_entry_text, self.config.get_default_save_dir(), self.save_dir_entry_callback)
        self.make_open_button(2, 2, self.open_save_button_fn)

        self.make_label(self.window, 3, 0, "Ignored categories (; or , delimited)")
        self.make_entry(3, 1, self.ignored_categories_text, self.config.get_ignored_categories_str(),
                        self.ignored_categories_entry_callback)

        properies_frame = tk.Frame(
            master=self.window,
            # relief=tk.RAISED,
            # borderwidth=1
        )
        properies_frame.grid(row=6, column=0, padx=20, pady=1, sticky="W", columnspan=3)
        self.make_label(properies_frame, 5, 0, "Primary\ncompare")
        self.make_label(properies_frame, 5, 1, "Properties to compare")
        self.make_label(properies_frame, 5, 2, "Properties to show")
        next_row, self.show_checkboxes = self.make_radiobuttons(properies_frame, 6, 0)
        next_row, self.diff_checkboxes = self.make_checkboxes(properies_frame, 6, 1, self.diff_checkbox_vars)
        next_row, self.show_checkboxes = self.make_checkboxes(properies_frame, 6, 2, self.show_checkbox_vars)
        self.update_ui_settings()

    def make_checkboxes(self, window, row, column, checkboxes):
        next_row = len(self.config.all_property_names) + row
        checkbox_objs = []
        for index, name in enumerate(self.config.all_property_names):
            checkbox_frame = tk.Frame(
                master=window,
                # relief=tk.RAISED,
                # borderwidth=1
            )
            checkbox_var = checkboxes[index]
            checkbox_frame.grid(row=index + row, column=column, padx=20, pady=1, sticky="W")
            checkbox = tk.Checkbutton(master=checkbox_frame, text=name, variable=checkbox_var,
                                      command=self.update_checkbox_fn)
            checkbox.pack(side="left")
            checkbox_objs.append(checkbox)
        return next_row, checkbox_objs

    def make_radiobuttons(self, window, row, column):
        next_row = len(self.config.all_property_names) + row
        radio_btn_objs = []
        for index, name in enumerate(self.config.all_property_names):
            radio_btn_frame = tk.Frame(
                master=window,
                # relief=tk.RAISED,
                # borderwidth=1
            )
            radio_btn_frame.grid(row=index + row, column=column, padx=1, pady=1, sticky="NESW")
            radio_btn = tk.Radiobutton(master=radio_btn_frame, text="", padx=20,
                                       variable=self.primary_radio_btn_var, value=index)
            radio_btn.pack(anchor=tk.CENTER)
            radio_btn_objs.append(radio_btn)
            create_tool_tip(radio_btn, "Property to use when checking if an item\n"
                                       "is unique when comparing to another item")
        return next_row, radio_btn_objs

    def make_save_settings_button(self, frame):
        tk.Button(master=frame, text="Save", command=self.save_settings_button_fn).pack(side="left", padx=5)

    def make_save_and_close_settings_button(self, frame):
        tk.Button(master=frame, text="Save and Close", command=self.save_and_close_settings_button_fn). \
            pack(side="left", padx=5)

    def make_save_settings_as_button(self, frame):
        tk.Button(master=frame, text="Save As", command=self.save_settings_as_button_fn). \
            pack(side="left", padx=5)

    def make_load_settings_button(self, frame):
        tk.Button(master=frame, text="Load", command=self.load_settings_button_fn).pack(side="left", padx=5)

    def save_settings_button_fn(self):
        logger.debug("Save settings callback")
        self.refresh_config()
        self.parent_ui.save_settings_button_fn()

    def save_and_close_settings_button_fn(self):
        logger.debug("Save and close settings callback")
        self.save_settings_button_fn()
        self.close_window()

    def save_settings_as_button_fn(self):
        logger.debug("Save settings as callback")
        self.refresh_config()
        self.parent_ui.save_settings_as_button_fn()

    def load_settings_button_fn(self):
        logger.debug("Load settings callback")
        self.parent_ui.load_settings_button_fn()
        self.update_ui_settings()

    def log_checkbox_states(self, name, checkbox_vars):
        states = [str(var.get()) for var in checkbox_vars]
        logger.debug("%s checkbox states: %s" % (name, ", ".join(states)))

    def update_checkbox_fn(self):
        logger.debug("Update checkbox callback")
        for index, var in enumerate(self.diff_checkbox_vars):
            if var.get() == 1:
                self.show_checkbox_vars[index].set(1)
                self.show_checkboxes[index].config(state=tk.DISABLED)
            else:
                self.show_checkboxes[index].config(state=tk.NORMAL)
        self.log_checkbox_states("Diff", self.diff_checkbox_vars)
        self.log_checkbox_states("Show", self.show_checkbox_vars)

    def update_ui_settings(self):
        for index in range(len(self.config.all_property_names)):
            self.diff_checkbox_vars[index].set(0)
            self.show_checkbox_vars[index].set(0)

        for name in self.config.diff_properties:
            index = self.config.all_property_names.index(name)
            self.diff_checkbox_vars[index].set(1)
            self.show_checkbox_vars[index].set(1)
            self.show_checkboxes[index].config(state=tk.DISABLED)

        for name in self.config.show_properties:
            index = self.config.all_property_names.index(name)
            self.show_checkbox_vars[index].set(1)

        self.primary_radio_btn_var.set(self.config.all_property_names.index(self.config.primary_prop))

        self.ignored_categories_text.set(self.config.get_ignored_categories_str())

        self.log_checkbox_states("Diff", self.diff_checkbox_vars)
        self.log_checkbox_states("Show", self.show_checkbox_vars)
        self.get_primary_prop()  # trigger log message
        self.get_ignored_categories()  # trigger log message

    def refresh_config(self):
        logger.debug("Refreshing config")
        self.config.default_load_dir = self.load_entry_text.get()
        self.config.default_save_dir = self.save_entry_text.get()
        self.config.diff_properties = self.get_diff_props()
        self.config.show_properties = self.get_show_props()
        self.config.primary_prop = self.get_primary_prop()
        self.config.ignored_categories = self.get_ignored_categories()
        logger.debug("Config:\n%s" % str(pprint.pformat(self.config.to_dict())))

    def get_primary_prop(self):
        if self.get_window_state() != "not created":
            index = self.primary_radio_btn_var.get()
            self.config.primary_prop = self.config.all_property_names[index]

        logger.debug("Primary prop name: %s" % self.config.primary_prop)
        return self.config.primary_prop

    def get_diff_props(self):
        if self.get_window_state() != "not created":
            names = []
            for index, var in enumerate(self.diff_checkbox_vars):
                if var.get() == 1:
                    names.append(self.config.all_property_names[index])

            logger.debug("Getting diff props from checkboxes")
            self.config.diff_properties = names

        logger.debug("Diff props: %s" % self.config.diff_properties)
        return self.config.diff_properties

    def get_show_props(self):
        if self.get_window_state() != "not created":
            names = []
            for index, var in enumerate(self.show_checkbox_vars):
                if var.get() == 1:
                    names.append(self.config.all_property_names[index])
            self.config.show_properties = names

            logger.debug("Getting show props from checkboxes")

        logger.debug("Show props: %s" % self.config.show_properties)
        return self.config.show_properties

    def get_ignored_categories(self):
        if self.get_window_state() != "not created":
            self.config.ignored_categories = self.parse_ignored_categories_str()
            logger.debug("Getting ignored categories from text entry")

        logger.debug("Ignored categories: %s" % self.config.ignored_categories)
        return self.config.ignored_categories

    def make_label(self, window, row, column, text):
        label_frame = tk.Frame(
            master=window,
            # relief=tk.RAISED,
            borderwidth=1
        )
        label_frame.grid(row=row, column=column, sticky="e")
        tk.Label(master=label_frame, text=text).pack(fill=tk.X)

    def make_entry(self, row, column, entry_var, text, entry_callback):
        entry_frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        entry_frame.grid(row=row, column=column, padx=5, pady=5, sticky='nwe')
        tk.Entry(master=entry_frame, textvariable=entry_var).pack(fill=tk.X)
        entry_var.set(text)
        entry_var.trace("w", lambda name, index, mode, string_var=entry_var: entry_callback(string_var))

    def make_open_button(self, row, column, button_fn):
        button_frame = tk.Frame(
            master=self.window,
            relief=tk.RAISED,
            borderwidth=1
        )
        button_frame.grid(row=row, column=column, padx=5, pady=5)
        tk.Button(master=button_frame, text="Browse", command=button_fn).pack()

    def open_load_button_fn(self):
        default_path = self.config.get_default_load_dir()
        logger.debug("Select default load dialog. Default dir: %s" % default_path)
        output_path = filedialog.askdirectory(
            initialdir=default_path, title="Default BOM load folder",
        )
        if len(output_path) > 0:
            self.config.default_load_dir = output_path
            self.load_entry_text.set(output_path)
        else:
            logger.debug("User didn't select path")

    def open_save_button_fn(self):
        default_path = self.config.get_default_save_dir()
        logger.debug("Select default save dialog. Default dir: %s" % default_path)
        output_path = filedialog.askdirectory(
            initialdir=default_path, title="Default file save folder",
        )
        if len(output_path) > 0:
            self.config.default_save_dir = output_path
            self.save_entry_text.set(output_path)
        else:
            logger.debug("User didn't select path")

    def load_dir_entry_callback(self, string_var):
        self.config.default_load_dir = string_var.get()
        logger.debug("Load dir entry callback: %s" % (self.config.default_load_dir))

    def save_dir_entry_callback(self, string_var):
        self.config.default_save_dir = string_var.get()
        logger.debug("Save dir entry callback: %s" % (self.config.default_save_dir))

    def parse_ignored_categories_str(self, string_var=None):
        if string_var is None:
            string_var = self.ignored_categories_text
        categories_str = string_var.get()
        str_split = re.split(r";|,|\n", categories_str)
        if len(str_split) == 1 and len(str_split[0]) == 0:
            str_split.pop()
        for index, entry in enumerate(str_split):
            str_split[index] = entry.strip()
        return str_split

    def ignored_categories_entry_callback(self, string_var):
        self.config.ignored_categories = self.parse_ignored_categories_str(string_var)

    def close_window(self):
        self.window.destroy()
        logger.debug("Closed settings window")
