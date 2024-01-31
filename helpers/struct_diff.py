import openpyxl

from bom import PropelStructured, SolidworksBOM
from bom.propel_bom import PropelBOM
from bom.solidworks_bom import SolidworksStructured

from .directory_manager import *
from .xlsx_converter import report_to_xlsx


def report_struct_diff(
    solid_bom: SolidworksStructured, propel_bom: PropelStructured, show_common=False
):
    # solid_bom.flattened_to_csv("output_boms/solidworks_flat.csv")
    solid_bom.to_json(OUTPUT_BOMS + "/solidworks.json")
    solid_assem_bom = solid_bom.from_tree(solid_bom.name, solid_bom.assemblies_only())
    solid_assem_bom.to_json(OUTPUT_BOMS + "/solidworks-assemblies.json")
    # solid_assem_bom.flattened_to_csv(OUTPUT_BOMS + "/solidworks-assemblies.csv")
    solid_assem_bom = SolidworksBOM.from_list(
        solid_assem_bom.name, solid_assem_bom.flattened
    )

    # propel_bom.flattened_to_csv("output_boms/propel_flat.csv")
    propel_bom.to_json(OUTPUT_BOMS + "/propel.json")
    propel_assem_bom = propel_bom.from_tree(
        propel_bom.name, propel_bom.assemblies_only()
    )
    propel_assem_bom.to_json(OUTPUT_BOMS + "/propel-assemblies.json")
    # propel_assem_bom.flattened_to_csv(OUTPUT_BOMS + "/propel-assemblies.csv")
    propel_assem_bom = PropelBOM.from_list(
        propel_assem_bom.name, propel_assem_bom.flattened
    )

    diff_report = solid_bom.diff(propel_bom)
    # with open(OUTPUT_BOMS + "/diff-report.txt", 'w') as file:
    #     file.write(solid_bom.diff_report_to_str(diff_report, propel_bom, show_common))

    # diff_report_path = OUTPUT_BOMS + "/diff-report.csv"
    # solid_bom.diff_report_to_csv(diff_report_path, diff_report, propel_bom, show_common)
    # print("Diff report written to: %s" % diff_report_path)

    output_path = OUTPUT_FORMS + "/%s + %s structured diff.xlsx" % (
        solid_bom.name,
        propel_bom.name,
    )
    report, color_mapping = solid_bom.diff_report_to_table(
        diff_report, propel_bom, show_common
    )
    workbook = report_to_xlsx(report, color_mapping, "Structured Diff", path=None)

    toplevel_diff_report = solid_assem_bom.diff(propel_assem_bom)
    report, color_mapping = solid_assem_bom.diff_report_to_table(
        toplevel_diff_report, propel_assem_bom, show_common
    )
    report_to_xlsx(report, color_mapping, "Top Level", path=None, workbook=workbook)

    workbook.save(output_path)
