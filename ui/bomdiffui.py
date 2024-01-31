import os
import platform
import pprint
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

from bom import OnshapeBOM, PropelBOM, PropelStructured, SolidworksBOM
from helpers.xlsx_converter import report_to_xlsx
from item.common_filters import create_filters_from_config
from item.item import Item
from logger import LoggerManager
from ui.settingsui import SettingsUi
from ui.uicolumn import UiColumn

from .config import Config

logger = LoggerManager.get_logger()


BOM_TYPES = {
    "solidworks": SolidworksBOM,
    "propel": PropelBOM,
    "onshape": OnshapeBOM,
    "generic": PropelBOM,
}


class BomDiffUI:
    def __init__(self, window):
        self.window = window

        for col_index in range(2):
            self.window.columnconfigure(col_index, weight=1, minsize=200)
            self.window.rowconfigure(col_index, weight=1, minsize=20)

        self.default_config_path = "./settings.yaml"
        try:
            self.config = Config(self.default_config_path)
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while loading config! See logs for details.\n%s"
                % str(e),
            )

        self.diff_button = None
        self.show_common_button = None
        self.show_common_var = tk.IntVar()
        self.show_common_var.set(1)

        self.settings_button = None
        self.save_settings_button = None
        self.walkthrough_button = None
        self.concat_button = None

        self.left_column = UiColumn(self.window, 0, 1, self.config)
        self.right_column = UiColumn(self.window, 1, 1, self.config)
        self.settings_ui = SettingsUi(self.window, self, self.config)

        self.button_frame = tk.Frame(
            master=self.window,
            # relief=tk.RAISED,
            # borderwidth=1
        )
        self.button_frame.grid(row=8, column=0, sticky="W", padx=5, pady=5)

        self.left_column.make()
        self.right_column.make()

        self.make_submit_button()
        self.make_concat_button()
        self.make_show_common_checkbox(7)
        self.make_settings_button()
        # self.make_save_settings_button()
        # self.make_walkthrough_button()

        self.load_config()

    def load_config(self, path=None, override_ui=True):
        if path is None:
            path = self.default_config_path
        try:
            logger.debug("Loading config from %s" % path)
            self.config.load(path)

            logger.debug("Config:\n%s" % str(pprint.pformat(self.config.to_dict())))

            if override_ui:
                self.left_column.set_entry_text(self.config.left_bom)
                self.right_column.set_entry_text(self.config.right_bom)

                self.left_column.set_bom_type(self.config.left_type)
                self.right_column.set_bom_type(self.config.right_type)
                self.set_show_common(self.config.show_common)

            create_filters_from_config(self.config.filters)

            logger.debug("UI elements updated from config")
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while loading config! See logs for details.\n%s"
                % str(e),
            )
            return False

    def save_config(self, path):
        logger.debug("Save config to %s" % path)
        self.config.left_bom = self.left_column.get_entry_text()
        self.config.right_bom = self.right_column.get_entry_text()

        self.config.left_type = self.left_column.get_bom_type()
        self.config.right_type = self.right_column.get_bom_type()
        self.config.show_common = self.show_common()

        self.config.save(path)
        logger.debug("Save config successful")

    def make_settings_button(self):
        settings_frame = tk.Frame(master=self.window, relief=tk.RAISED, borderwidth=1)
        settings_frame.grid(row=0, column=0, sticky="W", padx=5, pady=5)
        self.settings_button = tk.Button(
            master=settings_frame, text="Settings", command=self.settings_button_fn
        )
        self.settings_button.pack(side="left")

    def make_walkthrough_button(self):
        walkthrough_frame = tk.Frame(
            master=self.window, relief=tk.RAISED, borderwidth=1
        )
        walkthrough_frame.grid(row=0, column=1, sticky="E", padx=5, pady=5)
        self.walkthrough_button = tk.Button(
            master=walkthrough_frame,
            text="Walkthrough",
            command=self.walkthrough_button_fn,
        )
        self.walkthrough_button.pack(side="left")

    def make_submit_button(self):
        # button_frame = tk.Frame(
        #     master=self.toplevel_window,
        #     relief=tk.RAISED,
        #     borderwidth=1
        # )
        # button_frame.grid(row=row, column=0, padx=5, pady=5, columnspan=2)
        self.diff_button = tk.Button(
            master=self.button_frame, text="Diff", command=self.submit_button_fn
        )
        self.diff_button.pack(side="left", padx=5)

    def make_concat_button(self):
        self.concat_button = tk.Button(
            master=self.button_frame, text="Concatenate", command=self.concat_button_fn
        )
        self.concat_button.pack(side="left", padx=5)

    def make_show_common_checkbox(self, row):
        checkbox_frame = tk.Frame(
            master=self.window,
            # relief=tk.RAISED,
            # borderwidth=1
        )
        checkbox_frame.grid(row=row, column=0, padx=5, pady=5, columnspan=2)
        self.show_common_button = tk.Checkbutton(
            master=checkbox_frame,
            text="Show common items",
            variable=self.show_common_var,
        )
        self.show_common_button.pack()

    def check_inputs(self):
        logger.debug("Checking for valid input")
        left_path = self.left_column.get_path()
        right_path = self.right_column.get_path()
        left_type = self.left_column.get_bom_type()
        right_type = self.right_column.get_bom_type()

        logger.debug("left_path: %s" % left_path)
        logger.debug("right_path: %s" % right_path)
        logger.debug("left_type: %s" % left_type)
        logger.debug("right_type: %s" % right_type)

        errors = []
        if not os.path.isfile(left_path):
            errors.append("Left path is invalid")
        if not os.path.isfile(right_path):
            errors.append("Right path is invalid")

        if left_type == "unknown":
            errors.append("Left bom type not selected")

        if right_type == "unknown":
            errors.append("Right bom type not selected")

        if len(errors) == 0:
            logger.debug("Inputs are valid.")
            return left_path, right_path, left_type, right_type
        else:
            error_msg = "\n".join(errors)
            logger.debug("Invalid input!\n%s" % error_msg)
            messagebox.showerror("Invalid input!", error_msg)
            return None

    def show_common(self):
        return bool(self.show_common_var.get())

    def set_show_common(self, value):
        self.show_common_var.set(int(value))

    def open_with_app(self, filepath):
        if platform.system() == "Darwin":  # macOS
            logger.debug("Opening %s in Finder" % filepath)
            subprocess.call(("open", filepath))
        elif platform.system() == "Windows":  # Windows
            logger.debug("Opening %s in Windows file explorer" % filepath)
            os.startfile(filepath)
        else:  # linux variants
            logger.debug("Opening %s in file explorer" % filepath)
            subprocess.call(("xdg-open", filepath))

    def savedir_dialog(self):
        default_path = self.config.get_default_save_dir()
        logger.debug("Save dir dialog. Default dir: %s" % default_path)
        output_path = filedialog.askdirectory(
            initialdir=default_path,
            title="Save to folder",
        )
        return output_path

    def report_struct_diff(
        self, left_bom, right_bom, left_type, right_type, output_path
    ):
        logger.debug("Attempting a diff on %s and %s" % (left_bom.name, right_bom.name))

        left_top_level_cls = BOM_TYPES[left_type]
        right_top_level_cls = BOM_TYPES[right_type]

        try:
            logger.debug("Getting diff props")
            left_bom.set_diff_props(self.settings_ui.get_diff_props())
            left_bom.set_show_props(self.settings_ui.get_show_props())
            left_bom.set_ignored_categories(self.settings_ui.get_ignored_categories())

            right_bom.set_diff_props(self.settings_ui.get_diff_props())
            right_bom.set_show_props(self.settings_ui.get_show_props())
            right_bom.set_ignored_categories(self.settings_ui.get_ignored_categories())

            logger.debug("Diff props: %s" % left_bom.item_diff_names)
            logger.debug("Show props: %s" % left_bom.item_show_names)

            logger.debug("Diffing left and right")
            diff_report = left_bom.diff(right_bom)

            logger.debug("Generating table")
            report, color_mapping = left_bom.diff_report_to_table(
                diff_report, right_bom, self.show_common()
            )

            logger.debug("Generating xlsx")
            workbook = report_to_xlsx(report, color_mapping, "Diff", path=None)

            logger.debug("Creating assembly only bom for left")
            left_assem_bom = left_bom.from_tree(
                left_bom.name, left_bom.assemblies_only()
            )
            left_assem_bom = left_top_level_cls.from_list(
                left_assem_bom.name, left_assem_bom.flattened
            )
            left_assem_bom.set_diff_props(self.settings_ui.get_diff_props())
            left_assem_bom.set_show_props(self.settings_ui.get_show_props())
            left_assem_bom.set_ignored_categories(
                self.settings_ui.get_ignored_categories()
            )

            logger.debug("Creating assembly only bom for right")
            right_assem_bom = right_bom.from_tree(
                right_bom.name, right_bom.assemblies_only()
            )
            right_assem_bom = right_top_level_cls.from_list(
                right_assem_bom.name, right_assem_bom.flattened
            )
            right_assem_bom.set_diff_props(self.settings_ui.get_diff_props())
            right_assem_bom.set_show_props(self.settings_ui.get_show_props())
            right_assem_bom.set_ignored_categories(
                self.settings_ui.get_ignored_categories()
            )

            logger.debug("Diffing assembly only left and right")
            toplevel_diff_report = left_assem_bom.diff(right_assem_bom)

            logger.debug("Generating table")
            report, color_mapping = left_assem_bom.diff_report_to_table(
                toplevel_diff_report, right_assem_bom, self.show_common()
            )
            logger.debug("Generating xlsx")
            report_to_xlsx(
                report, color_mapping, "Assemblies only", path=None, workbook=workbook
            )

            logger.debug("Saving workbook")
            workbook.save(output_path)
            return True
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while analyzing BOMs! See logs for details.\n%s"
                % str(e),
            )
            return False

    def get_boms(self):
        logger.debug("Getting both BOMs")
        self.load_config(override_ui=False)

        result = self.check_inputs()
        if result is None:
            return None

        left_path, right_path, left_type, right_type = result
        try:
            logger.debug("Loading left BOM")
            left_bom = self.left_column.load_bom(left_path, skip_checks=True)

            logger.debug("Loading right BOM")
            right_bom = self.right_column.load_bom(right_path, skip_checks=True)
            return left_bom, right_bom, left_type, right_type
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while loading BOMs! See logs for details.\n%s"
                % str(e),
            )
            return None

    def submit_button_fn(self):
        logger.debug("Submit button callback")

        try:
            logger.debug("Getting primary prop")
            Item.set_primary_prop(self.settings_ui.get_primary_prop())
            Item.set_equivalent_mapping(self.config.equivalent_items)
            logger.debug("Primary prop name: %s" % Item.item_primary_prop)
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while setting primary comparison property! See logs for details.\n%s"
                % str(e),
            )
            return None

        result = self.get_boms()
        if result is None:
            return

        left_bom, right_bom, left_type, right_type = result

        default_name = "%s + %s diff.xlsx" % (left_bom.name, right_bom.name)

        default_path = self.config.get_default_save_dir()
        logger.debug(
            "Save report as dialog. Default dir: %s. Default name: %s"
            % (default_path, default_name)
        )
        if platform.system() == "Darwin":  # macOS
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Save report as",
                filetype=(
                    ("Excel 2007", "*.xlsx"),
                    ("Comma Separated Values", "*.csv"),
                ),
                initialfile=default_name,
            )
        elif platform.system() == "Windows":  # Windows
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Save report as",
                # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
                filetype=(
                    ("Excel 2007", "*.xlsx"),
                    ("Comma Separated Values", "*.csv"),
                ),
                initialfile=default_name,
            )
        else:  # linux variants
            output_path = filedialog.asksaveasfilename(
                initialdir=default_path,
                title="Save report as",
                filetypes=(
                    ("Excel 2007", "*.xlsx"),
                    ("Comma Separated Values", "*.csv"),
                ),
                initialfile=default_name,
            )

        if len(output_path) == 0:
            logger.debug("Canceling diff")
            return

        success = self.report_struct_diff(
            left_bom, right_bom, left_type, right_type, output_path
        )
        if not success:
            return
        answer = messagebox.askyesno("Success!", "Open generated file?")

        if answer:
            logger.debug("Opening associated app")
            self.open_with_app(output_path)

    def settings_button_fn(self):
        self.settings_ui.open()

    def walkthrough_button_fn(self):
        win = tk.Toplevel()
        win.title("Warning")
        message = "Do something"
        tk.Label(win, text=message).pack()
        tk.Button(win, text="Ok", command=win.destroy).pack()

    def concat_button_fn(self):
        logger.debug("Concat button callback")
        result = self.get_boms()
        if result is None:
            return

        left_bom, right_bom, left_type, right_type = result
        left_name = os.path.splitext(left_bom.name)[0]
        right_name = os.path.splitext(right_bom.name)[0]

        logger.debug("Concatenating %s and %s" % (left_bom.name, right_bom.name))
        default_name = "%s and %s.csv" % (left_name, right_name)

        default_path = self.config.get_default_save_dir()
        logger.debug(
            "Save concat BOM as dialog. Default dir: %s. Default name: %s"
            % (default_path, default_name)
        )
        output_path = filedialog.asksaveasfilename(
            initialdir=default_path,
            title="Save concatenated BOMs as",
            # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
            filetype=(("Comma Separated Values", "*.csv"),),
            initialfile=default_name,
        )

        if len(output_path) == 0:
            logger.debug("Canceling concat")
            return

        try:
            logger.debug(
                "Running concat tree on %s and %s" % (left_bom.name, right_bom.name)
            )
            concat_bom = PropelStructured.concat_tree([left_bom, right_bom])

            logger.debug("Saving to CSV: %s" % output_path)
            concat_bom.to_csv(output_path)
        except BaseException as e:
            logger.error(str(e), exc_info=True)
            messagebox.showerror(
                "Error",
                "An error occurred while concatenating BOMs! See logs for details.\n%s"
                % str(e),
            )

    def load_settings_button_fn(self):
        logger.debug("Settings button callback")
        output_path = filedialog.askopenfilename(
            initialdir=".",
            title="Settings location",
            # filetype=(("jpeg files", "*.jpg"), ("all files", "*.*"))
            filetypes=(("Yaml", "*.yaml"),),
        )
        if len(output_path) > 0:
            self.load_config(output_path, override_ui=False)

    def save_settings_as_button_fn(self):
        logger.debug("Save settings as button callback")
        default_path = "."
        output_path = filedialog.asksaveasfilename(
            initialdir=default_path,
            title="Save settings",
            filetypes=(("Yaml", "*.yaml"),),
            initialfile="settings.yaml",
        )
        if len(output_path) > 0:
            self.save_config(output_path)

    def save_settings_button_fn(self):
        logger.debug("Save settings button callback")
        output_path = self.config.path
        self.save_config(output_path)
