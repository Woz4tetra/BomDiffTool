import tkinter as tk

from .bomdiffui import BomDiffUI
from . import VERSION
from logger import LoggerManager

logger = LoggerManager.get_logger()


class MainUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.tk.call('tk', 'scaling', 1.5)
        self.window.wm_title("BOM Diff Tool %s" % VERSION)
        # self.tab_control = ttk.Notebook(self.toplevel_window)

        # self.bom_diff_tab = ttk.Frame(self.tab_control)
        # self.eco_generator_tab = ttk.Frame(self.tab_control)

        # self.tab_control.add(self.bom_diff_tab, text="BOM diff")
        # self.tab_control.add(self.eco_generator_tab, text="Material Disposition")
        # self.tab_control.pack(expand=1, fill="both")

        # self.bom_diff_ui = BomDiffUI(self.bom_diff_tab)
        self.bom_diff_ui = BomDiffUI(self.window)

    def run_tk(self):
        logger.debug("App is starting")
        self.window.mainloop()
