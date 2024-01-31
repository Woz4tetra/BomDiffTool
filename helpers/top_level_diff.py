from bom.bom import BOM
from .xlsx_converter import report_to_xlsx
from .directory_manager import *


def report_top_level_diff(bom1: BOM, bom2: BOM, print_report=True, show_common=True):
    diff_report = bom1.diff(bom2)
    if print_report:
        report_str = bom1.diff_report_to_str(diff_report, bom2, show_common, skip_attrs=("revision",))
        print(report_str)

    report, color_mapping = bom1.diff_report_to_table(diff_report, bom2, show_common)
    output_path = OUTPUT_FORMS + "/%s + %s diff.xlsx" % (bom1.name, bom2.name)
    return report_to_xlsx(report, color_mapping, "Diff", output_path)
