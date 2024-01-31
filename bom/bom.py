import csv
import os

import xlrd

from item import (
    CODE_CATEGORIES,
    CODE_CATEGORIES_LOWER,
    NAME_CATEGORIES,
    NAME_CATEGORIES_LOWER,
)
from item.item import Item
from logger import LoggerManager

logger = LoggerManager.get_logger()


class BOM:
    def __init__(self, name):
        self.name = name
        self.items = []
        self.items_set = set()
        self.header = {}
        self.item_diff_names = ["Item Code", "Description", "Qty"]

        # items that show on the diff report but aren't necessarily compared against each other
        self.item_show_names = ["Item Code", "Description", "Qty", "Revision"]
        self.ignored_categories = []

    def create_header(self, header):
        return {key: index for index, key in enumerate(header)}

    def append(self, item):
        if item:
            self.items.append(item)
            # if item in self.items_set:
            #     logger.warn("item is listed twice in %s: %s" % (self.name, item))
            self.items_set.add(item)

    @classmethod
    def from_file(cls, path):
        if path.endswith(".csv"):
            return cls.from_csv(path)
        elif path.endswith(".xlsx"):
            return cls.from_xlsx(path)
        else:
            raise NotImplementedError("Unsupported file type: %s" % path)

    @classmethod
    def from_xlsx(cls, path):
        obj = cls(os.path.basename(path))
        workbook = xlrd.open_workbook(path)
        sheet = workbook.sheet_by_index(0)

        obj.header = obj.create_header(sheet.row_values(0))
        obj.header = {str(key): value for key, value in obj.header.items()}
        for row_num in range(1, sheet.nrows):
            line = sheet.row_values(row_num)
            item = obj.create_item(line)
            obj.append(item)
        return obj

    @classmethod
    def from_csv(cls, path):
        obj = cls(os.path.basename(path))
        file, reader, first_row = obj._attempt_to_open(path)
        obj.header = obj.create_header(first_row)
        for line in reader:
            item = obj.create_item(line)
            obj.append(item)
        file.close()
        return obj

    def _attempt_to_open(self, path):
        encoding_attempts = ["utf-8", None, "utf-16", "cp1252"]
        exception = None
        for encoding in encoding_attempts:
            file = None
            try:
                file = open(path, encoding=encoding)
                reader = csv.reader(file)
                first_row = next(reader)
                return file, reader, first_row
            except BaseException as e:
                if file is not None:
                    file.close()
                exception = e
        if exception is not None:
            raise exception

    @classmethod
    def from_list(cls, name, l, header=None):
        obj = cls(name)
        if header is None:
            header = cls._get_common_header(l)

        for item in l:
            obj.append(obj.recreate_item(item, header))
        return obj

    def create_item(self, line):
        return Item.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return Item.from_item(item, header)

    @classmethod
    def _get_common_header(cls, items):
        common_header = []
        for item in items:
            for index, name in enumerate(item.get_preparsed_header()):
                if name not in common_header:
                    common_header.insert(index, name)
        return common_header

    def set_diff_props(self, new_props):
        if (isinstance(new_props, (list, tuple))) and len(new_props) > 0:
            self.item_diff_names = new_props

    def set_show_props(self, new_props):
        assert isinstance(new_props, (list, tuple)), str(type(new_props))

        self.item_show_names = new_props

        # all names being diff'd should be shown
        for index, name in enumerate(self.item_diff_names):
            if name not in self.item_show_names:
                self.item_show_names.insert(index, name)

    def set_ignored_categories(self, categories: list):
        for category in categories:
            category = category.lower()
            if category in NAME_CATEGORIES_LOWER:
                # NAME_CATEGORIES_LOWER maps to normal case category names
                # NAME_CATEGORIES maps to category codes
                category = NAME_CATEGORIES[NAME_CATEGORIES_LOWER[category]]
            if category in CODE_CATEGORIES_LOWER:
                category = CODE_CATEGORIES_LOWER[category]
            if category not in CODE_CATEGORIES:
                continue
            self.ignored_categories.append(category)

    def diff(self, other):
        assert isinstance(other, BOM)

        common_parts_self = []
        common_parts_other = []
        common_parts_diff_attrs = []
        item_ids = [id(x) for x in self.items]
        other_ids = [id(x) for x in other.items]
        for item in sorted(self.items_set.intersection(other.items_set)):
            if id(item) in item_ids:
                index = other.items.index(item)
                other_item = other.items[index]
                common_parts_self.append(item)
                common_parts_other.append(other_item)
            elif id(item) in other_ids:
                index = self.items.index(item)
                other_item = self.items[index]
                common_parts_other.append(item)
                common_parts_self.append(other_item)
            else:
                common_parts_diff_attrs.append([])
                continue
            common_parts_diff_attrs.append(item.diff(other_item, self.item_diff_names))

        assert (
            len(common_parts_self)
            == len(common_parts_other)
            == len(common_parts_diff_attrs)
        )
        # common_parts_self.sort()
        # common_parts_other.sort()

        self_only = []
        for item in self.items_set.difference(other.items_set):
            self_only.append(item)
        self_only.sort()

        other_only = []
        for item in other.items_set.difference(self.items_set):
            other_only.append(item)
        other_only.sort()

        diff_report = (
            common_parts_self,
            common_parts_other,
            common_parts_diff_attrs,
            self_only,
            other_only,
        )
        return diff_report

    @staticmethod
    def _fill_to_length(l, length):
        l.extend(["" for _ in range(length - len(l))])

    def diff_report_to_str(
        self, diff_report, other, show_common=False, skip_attrs=None
    ):
        (
            common_parts_1,
            common_parts_2,
            common_parts_diff_attrs,
            bom1_only,
            bom2_only,
        ) = diff_report
        report_str = "\n%s (%s)\t%s (%s)\n" % (
            self.name,
            len(self.items),
            other.name,
            len(other.items),
        )
        for item1, item2, diff_attrs in zip(
            common_parts_1, common_parts_2, common_parts_diff_attrs
        ):
            if show_common or len(diff_attrs) > 0:
                report_str += "%s\t\t\t%s\t\t%s" % (item1, item2, item1.description)

            if len(diff_attrs) > 0:
                for attr_name in diff_attrs:
                    if skip_attrs is not None and attr_name in skip_attrs:
                        continue
                    report_str += "\t\t %s: %s != %s" % (
                        attr_name,
                        getattr(item1, attr_name),
                        getattr(item2, attr_name),
                    )

                # try:
                #     qty_diff = item1.quantity - item2.quantity
                # except TypeError:
                #     qty_diff = "???"
                # report_str += "\t\t QTY diff: %s - %s = %s" % (item1.quantity, item2.quantity, qty_diff)
            if show_common or len(diff_attrs) > 0:
                report_str += "\n"
        no_differences = True
        for item in bom2_only:
            no_differences = False
            report_str += "------         \t\t%s\t\t\t%s\n" % (item, item.description)
        for item in bom1_only:
            no_differences = False
            report_str += "%s\t\t\t------\t\t%s\n" % (item, item.description)
        if no_differences:
            report_str += "BOMs match\n"

        return report_str

    def diff_report_to_table(self, diff_report, other, show_common=False):
        header_length = 1 + len(self.item_show_names) * 2
        first_row = ["", "%s (%s)" % (self.name, len(self.items))]
        for _ in range(len(self.item_show_names)):
            first_row.append("")
        first_row.append("%s (%s)" % (other.name, len(other.items)))
        self._fill_to_length(first_row, header_length)
        report = [first_row]
        color_mapping = [[TableColors.TITLE for _ in range(len(first_row))]]

        second_row = ["#"] + self.item_show_names + self.item_show_names
        self._fill_to_length(second_row, header_length)
        color_mapping.append([TableColors.TITLE for _ in range(len(second_row))])
        report.append(second_row)

        no_differences = self._diff_toplevel_to_table(
            diff_report, show_common, report, color_mapping
        )
        if no_differences:
            bom_match_row = ["", "BOMs match for %s" % self.name]
            self._fill_to_length(bom_match_row, header_length)
            report.append(bom_match_row)
            color_mapping.append([TableColors.BLANK for _ in range(len(bom_match_row))])
        return report, color_mapping

    def _get_attr_from_name(self, item, name):
        header_filter_match = item.get_header_filter_match(name)
        if header_filter_match is None:
            return None
        return header_filter_match.attribute_name

    def _append_common_diff_rows(
        self, item, diff_attrs, row, color_row, diff_color, match_color, show_color
    ):
        for name in self.item_show_names:
            attr_name = self._get_attr_from_name(item, name)
            if attr_name is None:
                # color_row.append(diff_color)
                row.append("")
                # continue
            else:
                row.append(str(getattr(item, attr_name)))

            if name in self.item_diff_names:
                if attr_name in diff_attrs:
                    color_row.append(diff_color)
                else:
                    color_row.append(match_color)
            else:
                color_row.append(show_color)

    def _append_only_diff_rows(self, item, row, color_row, diff_color):
        for name in self.item_show_names:
            attr_name = self._get_attr_from_name(item, name)
            if attr_name is None:
                color_row.append(diff_color)
                row.append("")
                continue

            row.append(getattr(item, attr_name))
            color_row.append(diff_color)

    def _append_only_empty_diff_rows(self, row, color_row, diff_color):
        for _ in self.item_show_names:
            row.append("")
            color_row.append(diff_color)

    def _append_tree_num(self, item, row, color_row):
        row.append(item.tree_num if hasattr(item, "tree_num") else "")
        color_row.append(TableColors.BLANK)

    def _diff_toplevel_to_table(
        self, diff_report, show_common, report: list, color_mapping: list
    ):
        common_parts_self = diff_report[0]
        common_parts_other = diff_report[1]
        common_parts_diff_attrs = diff_report[2]
        self_only = diff_report[3]
        other_only = diff_report[4]

        no_differences = True
        for self_item, other_item, diff_attrs in zip(
            common_parts_self, common_parts_other, common_parts_diff_attrs
        ):
            if show_common or len(diff_attrs) > 0:
                if len(diff_attrs) > 0:
                    no_differences = False
                row = []
                color_row = []
                self._append_tree_num(self_item, row, color_row)
                self._append_common_diff_rows(
                    self_item,
                    diff_attrs,
                    row,
                    color_row,
                    TableColors.LEFT_DIFF,
                    TableColors.LEFT_MATCH,
                    TableColors.LEFT_SHOW,
                )
                self._append_common_diff_rows(
                    other_item,
                    diff_attrs,
                    row,
                    color_row,
                    TableColors.RIGHT_DIFF,
                    TableColors.RIGHT_MATCH,
                    TableColors.RIGHT_SHOW,
                )
                report.append(row)
                color_mapping.append(color_row)

        for subitem in self_only:
            no_differences = False
            row = []
            color_row = []
            self._append_tree_num(subitem, row, color_row)

            self._append_only_diff_rows(subitem, row, color_row, TableColors.LEFT_DIFF)
            self._append_only_empty_diff_rows(row, color_row, TableColors.LEFT_DIFF)

            report.append(row)
            color_mapping.append(color_row)
        for subitem in other_only:
            no_differences = False
            row = []
            color_row = []
            self._append_tree_num(subitem, row, color_row)

            self._append_only_empty_diff_rows(row, color_row, TableColors.RIGHT_DIFF)
            self._append_only_diff_rows(subitem, row, color_row, TableColors.RIGHT_DIFF)

            report.append(row)
            color_mapping.append(color_row)

        return no_differences

    def extend(self, other, add_quantities=True):
        for other_item in other.items:
            if other_item in self.items_set:
                if add_quantities:
                    index = self.items.index(other_item)
                    self.items[index].quantity += other_item.quantity
            else:
                self.append(other_item)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, item):
        return self.items[item]


class TableColors:
    BLANK = 0
    TITLE = 1
    SUB_ASSEMBLY = 2
    LEFT_MATCH = 3
    LEFT_DIFF = 4
    RIGHT_MATCH = 5
    RIGHT_DIFF = 6
    LEFT_SHOW = 7
    RIGHT_SHOW = 8
