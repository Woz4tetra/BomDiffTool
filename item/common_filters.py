import re

from . import NAME_CATEGORIES
from .header_filter import HeaderFilter

# description = HeaderFilter("description", "Description", str, False)
# quantity = HeaderFilter("quantity", Item.is_qty, Item.convert_qty, False)
# propel_number = HeaderFilter("propel_number", ("PropelPN", "Item #", "Item Number"), Item.code_or_number, False)
# item_code = HeaderFilter("item_code", ("Item Code",), str, False)
# item_id = HeaderFilter("item_id", ("Item ID",), str, False)
# category = HeaderFilter("category", ("Category Name", "CAT", "Category"), Item.convert_cat, False)
# revision = HeaderFilter("revision", ("Revision", "Rev"), Item.convert_rev)
#
# pdm_number = HeaderFilter("pdm_number", ("Number", "PDM Number"), Item.str_int)
# filename = HeaderFilter("filename", ("SW-File Name(File Name)", "File Name"), str)
# configuration = HeaderFilter("configuration", "SW-Configuration Name(Configuration Name)", str)
# material = HeaderFilter("material", "Material", str)
# finish = HeaderFilter("finish", "Finish", str)
# manufacturer = HeaderFilter("manufacturer", ("MFG", "Manufacturer Name"), str)
# mfg_number = HeaderFilter("mfg_number", ("MFG Number", "Manufacturer Part Name"), str)
# procurement_type = HeaderFilter("procurement_type", "Procurement Type", str)
# has_attachments = HeaderFilter("has_attachments", "Has Attachments", Item.convert_bool)
# owner = HeaderFilter("owner", "Owner", str)
#
# propel_number.add_equivalent_hfs(item_code, item_id)


def convert_cat(x):
    if type(x) == str and len(x) > 0:
        if x in NAME_CATEGORIES:
            return NAME_CATEGORIES[x]
        else:
            return x
    else:
        return "XXX"


def str_int(x):
    try:
        return str(int(x))
    except ValueError:
        return "XXXXXX"


def convert_rev(x):
    try:
        return "%02d" % int(x)
    except ValueError:
        return x


def convert_bool(x):
    if type(x) == str:
        if x.upper() == "TRUE":
            return True
        elif x.upper() == "FALSE":
            return False
    else:
        return bool(x)


def code_or_number(x):
    try:
        return str(int(x))
    except ValueError:
        return x


def is_qty(x):
    return "qty" in x or "quantity" in x


def convert_qty(x):
    if type(x) == int:
        return x
    if type(x) == float:
        return int(x)
    try:
        match = re.search(r"(\d*)", x)
        if match:
            return int(match.group(1))
    except ValueError:
        pass

    return x


def remove_newlines(x):
    if type(x) == str:
        return x.replace("\n", "").strip()
    else:
        return x


def convert_level(x):
    if type(x) == str:
        x = x.strip()
        if "," in x:
            return int(x.split(",")[0])
        else:
            try:
                return int(x)
            except ValueError:
                return None
    elif type(x) == float:
        return int(x)
    else:
        return x


def is_propel_number(x):
    # used to check if the string only contained digits,
    # but now propel numbers can have letters in them
    return type(x) == str


def is_revision(x):
    if type(x) == str and x.isdigit():
        return True
    elif type(x) == int:
        return True
    return False


COMMON_FILTERS = {}
FILTER_MAP = {
    "__is_qty__": is_qty,
    "__is_propel_number__": is_propel_number,
    "__is_revision__": is_revision,
}
PARSER_MAP = {
    "convert_cat": convert_cat,
    "str_int": str_int,
    "convert_rev": convert_rev,
    "convert_bool": convert_bool,
    "code_or_number": code_or_number,
    "convert_qty": convert_qty,
    "remove_newlines": remove_newlines,
    "convert_level": convert_level,
    "str": str,
    "int": int,
    "float": float,
}


def create_filters_from_config(config_filters):
    global COMMON_FILTERS
    equivalent_hfs = {}
    for name, config_filter in config_filters.items():
        filters = []
        for index, filt in enumerate(config_filter.filters):
            if filt in FILTER_MAP:
                filt = FILTER_MAP[filt]
            filters.append(filt)
        parser = str
        if config_filter.type in PARSER_MAP:
            parser = PARSER_MAP[config_filter.type]
        hf = HeaderFilter(name, filters, parser, config_filter.is_critical)
        if len(config_filter.equivalent_to) > 0:
            equivalent_hfs[name] = config_filter.equivalent_to

        COMMON_FILTERS[name] = hf

    for name, equivalent_to in equivalent_hfs.items():
        hf = COMMON_FILTERS[name]
        equivalent_to_hfs = [COMMON_FILTERS[name] for name in equivalent_to]
        hf.add_equivalent_hfs(*equivalent_to_hfs)


def get_common_filters():
    filters = []
    for name in COMMON_FILTERS:
        filters.append(COMMON_FILTERS[name])
    return filters


def get_filters(*names):
    filters = []
    for name in names:
        if name in COMMON_FILTERS:
            filters.append(COMMON_FILTERS[name])
    return filters
