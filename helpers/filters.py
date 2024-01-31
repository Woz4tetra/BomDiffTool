import csv
import re

import yaml

from bom import PropelStructured
from bom.solidworks_bom import SolidworksStructured
from bom.structured_bom import StructuredBOM
from item import CODE_CATEGORIES, NAME_CATEGORIES
from logger import LoggerManager

logger = LoggerManager.get_logger()


MCMASTER_REGEX = r"(MCM|McMaster|Carr)"


def is_mcmaster(manufacturer: str):
    return re.search(MCMASTER_REGEX, manufacturer, re.IGNORECASE)


def filter_for_mcmaster(struct_bom: SolidworksStructured):
    count = 0
    report = []
    for item in struct_bom.flattened:
        if is_mcmaster(item.manufacturer):
            report.append(item)
            # print("\t".join(item.to_list_str()))
            count += 1
    # print(count)
    return report


def generate_mcmaster_list(solid_bom, propel_bom):
    with open("output_boms/mcmaster-items.csv", "w", newline="") as file:
        writer = csv.writer(file)
        # header = None
        header = [
            "DESCRIPTION",
            "ITEM NUMBER",
            "ACCOUNT NAME",
            "MFR. PART NUMBER",
            "PROCUREMENT TYPE",
            "CATEGORY",
            "REVISION",
        ]
        writer.writerow(header)
        ignore_list = [
            # "103035",
            # "103272",
            # "103231",
            # "104552",
            # "103195",
            # "104017",
            # "104320",
            # "103274",
            # "103254",
            # "104314",
            # "104070",
            # "103253",
            # "104037",
            # "103248",
            # "105066",
            # "102775",
            # "102773",
            # "103379",
            # "104010",
            # "103493",
        ]

        for item in filter_for_mcmaster(solid_bom):
            results = propel_bom.get_item(item.propel_number, "propel_number")
            if len(results) == 0:
                logger.warn("'%s' is not in propel BOM" % item)
                continue
            propel_item, subtree = results[0]
            # if header is None:
            #     header = propel_item.get_header_list()
            #     writer.writerow(header)

            if item.propel_number in ignore_list:
                continue
            if is_mcmaster(propel_item.manufacturer):
                continue

            propel_item.manufacturer = "McMaster-Carr"
            propel_item.mfg_number = item.mfg_number
            propel_item.category = CODE_CATEGORIES[propel_item.category]
            try:
                propel_item.revision = propel_item.convert_rev(
                    int(propel_item.revision) + 1
                )
            except ValueError:
                pass
            row = propel_item.to_list(
                [
                    "description",
                    "item number",
                    "manufacturer name",
                    "manufacturer part name",
                    "procurement type",
                    "category name",
                    "revision",
                ]
            )
            writer.writerow(row)


def filter_for_no_category(struct_bom: SolidworksStructured):
    count = 0
    for item in struct_bom.flattened:
        if item.category == "XXX" and item.propel_number != "XXXXXX":
            print("\t".join(item.to_list_str()))
            count += 1
    print(count)


def filter_for_cosmetic_suspects(struct_bom: PropelStructured):
    count = 0
    with open("propel_boms/cosmetic-filters.yaml") as file:
        cosmetic_filters = yaml.safe_load(file)
    part_num_blacklist = cosmetic_filters["part_num_blacklist"]
    assemblies_blacklist = cosmetic_filters["assemblies_blacklist"]
    categories_blacklist = cosmetic_filters["categories_blacklist"]

    part_num_blacklist.extend(assemblies_blacklist)
    assemblies_blacklist_tree_nums = []
    for propel_num in assemblies_blacklist:
        results = struct_bom.get_item(propel_num, "propel_number")
        item, subtree = results[0]
        print(item.tree_num, item)
        assemblies_blacklist_tree_nums.append(item.tree_num)

    report = []
    for item in struct_bom.flattened:
        if item.category in categories_blacklist:
            continue
        if item.propel_number in part_num_blacklist:
            continue
        # if not item.has_attachments:
        #     continue
        if item.procurement_type != "MTS":
            continue
        if item.parent is not None:
            blacklisted_asm_found = False
            for tree_num in assemblies_blacklist_tree_nums:
                if tree_num in item.parent.tree_num:
                    blacklisted_asm_found = True
                    break
            if blacklisted_asm_found:
                continue
        # print("\t".join(item.to_list_str()))
        report.append(item)
        count += 1
    print(count)
    return report


def generate_cosmetic_list(
    propel_bom: PropelStructured, solid_bom: SolidworksStructured
):
    report = filter_for_cosmetic_suspects(propel_bom)
    with open("output_boms/cosmetic-items.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "description",
                "category name",
                "item number",
                "revision",
                "owner",
                "material",
                "finish",
            ]
        )
        for item in report:
            results = solid_bom.get_item(item.propel_number, "propel_number")
            row = item.to_list(
                ["description", "category name", "item number", "revision", "owner"]
            )
            if len(results) > 0:
                solid_item, subtree = results[0]
                row.extend(solid_item.to_list(["material", "finish"]))
                finish = solid_item.finish.strip().upper()
                row.append(len(finish) > 0 and finish not in ("NONE", "N/A"))
            writer.writerow(row)


def report_instances(bom: StructuredBOM, key, key_name="tree_num"):
    results = bom.get_item(key, key_name)
    print("\t".join(results[0][0].to_list_str()))
    sum_qty = 0
    for item, subtree in results:
        print(
            "\t%s\t%s\t%s"
            % (item.parent.item_code, item.quantity, item.parent.description)
        )
        sum_qty += item.quantity
    print("Sum:", sum_qty)


CONSUMABLE_REGEX = r"(CNSM|ADH|LUB)"
# CONSUMABLE_DESC_REGEX = r"(HEATSHRINK|VHB)"
CONSUMABLE_DESC_REGEX = r"(HEATSHRINK)"


def is_consumable(item):
    category = item.category
    description = item.description
    if re.search(CONSUMABLE_REGEX, category, re.IGNORECASE):
        return True
    if re.search(CONSUMABLE_DESC_REGEX, description, re.IGNORECASE):
        return True

    return False


def filter_for_consumables(items):
    count = 0
    report = []
    for item in items:
        if is_consumable(item):
            report.append(item)
            # print("\t".join(item.to_list()))
            count += 1
    print(count)
    return report
