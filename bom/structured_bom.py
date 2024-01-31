import copy
import csv
import json

import yaml

from item.structured_item import StructuredBomItem
from item.tree_counter import TreeCounter
from logger import LoggerManager

from .bom import BOM, TableColors

logger = LoggerManager.get_logger()


class StructuredBOM(BOM):
    def __init__(self, name):
        super(StructuredBOM, self).__init__(name)
        self.tree = {}
        self.flattened = {}

    def clear_tree(self):
        self.tree = {}

    @classmethod
    def from_tree(cls, name, tree) -> "StructuredBOM":
        obj = cls(name)
        obj._rebuild_tree(tree)
        return obj

    @classmethod
    def from_file(cls, path) -> "StructuredBOM":
        return super(StructuredBOM, cls).from_file(path)

    @classmethod
    def from_csv(cls, path) -> "StructuredBOM":
        obj = super(StructuredBOM, cls).from_csv(path)
        obj._build_tree()
        return obj

    @classmethod
    def from_xlsx(cls, path) -> "StructuredBOM":
        obj = super(StructuredBOM, cls).from_xlsx(path)
        obj._build_tree()
        return obj

    def create_item(self, line):
        return StructuredBomItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return StructuredBomItem.from_item(item, header)

    @classmethod
    def concat_tree(cls, others) -> "StructuredBOM":
        name = " + ".join([o.name for o in others])
        super_tree = {}
        all_items = []

        super_tree_num = 1
        for other in others:
            for tree_num, subtree in other.tree.items():
                super_tree[str(super_tree_num)] = subtree
                super_tree_num += 1
            all_items.extend(other.items)

        obj = cls(name)
        obj._rebuild_tree(super_tree)
        return obj

    def _rebuild_tree(self, tree):
        if len(tree) == 0:
            return
        tree_counter = TreeCounter()

        def get_items(tree_num, subtree, item, level):
            item = self.recreate_item(item)
            tree_num, parent_tree_num = tree_counter.get_tree_num(level)
            item.tree_num = tree_num
            item.parent_num = parent_tree_num
            self.append(item)

        self.apply_fn(get_items, tree)
        self._build_tree()

    def set_branch(self, obj, tree_num, tree=None):
        if tree is None:  # supply a default value
            tree = self.tree
        split_num = tree_num.split(".")
        curr_num = split_num.pop(0)  # get top level of tree num
        if (
            curr_num not in tree
        ):  # if top level doesn't exist, initialize a top level branch
            if len(split_num) == 0:
                tree[curr_num] = [
                    obj,
                    {},
                ]  # if the obj is at the top level, put it there and exit
                return
            else:
                tree[curr_num] = [None, {}]

        for level_index in split_num:  # for all remaining levels in the tree num,
            tree = tree[curr_num]  # recurse into the next level of the tree
            assert isinstance(tree, list) and len(tree) == 2, "%s, %s" % (
                tree_num,
                tree,
            )  # all children should be a list of size 2
            curr_num += "." + level_index  # create the tree num from the level index
            if (
                curr_num not in tree[1]
            ):  # if the current tree_num isn't in the item's children,
                tree[1][curr_num] = [
                    None,
                    {},
                ]  # create an empty subtree with the item's number as the key
            tree = tree[1]  # recurse to the next tree
        # if len(tree[curr_num]) > 0:
        #     tree[curr_num] = [obj, tree[curr_num]]
        # else:
        #     tree[curr_num] = [obj, {}]
        if tree[curr_num][0] is not None:
            raise ValueError(
                "Duplicate tree numbers in %s detected. %s tried to override %s with num %s"
                % (self.name, obj, tree[curr_num][0], tree_num)
            )
        tree[curr_num][0] = obj

    def get_item(self, key_value, key_name="tree_num", subtree=None):
        if key_name == "tree_num":
            tree_nums = [key_value]
        else:
            tree_nums = []
            for item in self.items:
                if item.__dict__[key_name] == key_value:
                    tree_nums.append(item.tree_num)
        results = []
        for tree_num in tree_nums:
            result = self.branch_from_tree_num(tree_num, subtree)
            results.append(result)
        return results

    def branch_from_tree_num(self, tree_num, subtree=None):
        split_num = tree_num.split(".")
        if subtree is None:
            subtree = self.tree
        curr_num = ""
        for level_index in split_num:
            if len(curr_num) == 0:
                curr_num = level_index
            else:
                curr_num += "." + level_index

            subtree = subtree[curr_num]
            if curr_num != tree_num:
                subtree = subtree[1]

        return subtree  # subtree is now a tuple: (item, subtree: dict)

    def _build_tree(self):
        if len(self.tree) != 0:
            raise ValueError(
                "%s tree is not empty. Please clear it with clear_tree() first"
            )
        self._preprocess_tree_num()
        for index, item in enumerate(self.items):
            assert isinstance(
                item, StructuredBomItem
            ), "Encountered an invalid item (%s: %s)" % (type(item), item)
            self.set_branch(item, item.tree_num, self.tree)
            self._set_flattened_item(item)
        self._link_parents()

    def _set_flattened_item(self, item):
        if item.quantity is None:
            quantity = 0
        else:
            quantity = item.quantity
        if item not in self.flattened:
            self.flattened[item] = quantity
        else:
            self.flattened[item] += quantity

    def find_in_flattened(self, key, key_name):
        for item in self.flattened:
            if key == item.__dict__[key_name]:
                return item, self.flattened[item]
        return None

    def _preprocess_tree_num(self):
        for item in self.items:
            item._parse_tree_num()

    def _link_parents(self):
        for item in self.items:
            if item.parent_num:
                item.parent = self.branch_from_tree_num(item.parent_num)[0]

    def iter_tree(self, subtree=None, level=0):
        if subtree is None:
            subtree = self.tree
        for tree_num in subtree:
            item = subtree[tree_num][0]
            yield tree_num, subtree, item, level
            yield from self.iter_tree(subtree[tree_num][1], level + 1)

    def _iter_tree_with_fn(self, callback, subtree=None, level=0):
        if subtree is None:
            subtree = self.tree

        for tree_num in subtree:
            callback(tree_num, subtree, subtree[tree_num][0], level)
            if isinstance(subtree[tree_num], list) and len(subtree[tree_num][1]) > 0:
                self._iter_tree_with_fn(callback, subtree[tree_num][1], level + 1)

    def apply_fn(self, callback, tree=None, create_new_tree=False):
        if tree is None:
            tree = self.tree
        if create_new_tree:
            copy_tree = copy.deepcopy(tree)
        else:
            copy_tree = tree
        self._iter_tree_with_fn(callback, copy_tree)
        return copy_tree

    def to_json(self, path, tree=None):
        def jsonify(tree_num, subtree, item, level):
            if isinstance(item, StructuredBomItem):
                item_str = item.to_json()
            else:
                item_str = ""

            if len(subtree[tree_num][1]) == 0:
                subtree[tree_num] = item_str
            else:
                subtree[tree_num][0] = item_str
            # subtree[tree_num][0] = item_str

        json_tree = self.apply_fn(jsonify, tree, create_new_tree=True)

        self._dump_to_json(path, json_tree)

    def flattened_to_csv(self, path):
        flattened = copy.deepcopy(self.flattened)
        # output = []
        header_list = next(iter(flattened.keys())).get_preparsed_header()
        output = [header_list]
        for counter, (item, quantity) in enumerate(flattened.items()):
            item.tree_num = counter + 1
            item.level = 1
            item.quantity = quantity
            output.append(item.to_list())
        self._dump_to_csv(path, output)

    def to_csv(self, path):
        # output = []
        header_list = self.items[0].get_preparsed_header()
        output = [header_list]
        for item in self.items:
            output.append(item.to_list())
        self._dump_to_csv(path, output)

    def _dump_to_csv(self, path, obj):
        assert path.endswith(".csv")
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            for row in obj:
                writer.writerow(row)

    def _dump_to_json(self, path, obj):
        assert path.endswith(".json")
        with open(path, "w") as file:
            json.dump(obj, file, indent=4)

    def _dump_to_yaml(self, path, obj):
        assert path.endswith(".yaml")
        with open(path, "w") as file:
            yaml.safe_dump(obj, file)

    def assemblies_only(self):
        assemblies_tree = {}

        def filter_assemblies(tree_num, subtree, item, level):
            if len(subtree[tree_num][1]) > 0:  # and item.category == "ASM":
                self.set_branch(item, tree_num, assemblies_tree)

        self.apply_fn(filter_assemblies)
        return assemblies_tree

    def _get_top_level_list(self):
        if len(self.tree) == 1:
            first_key = list(self.tree.keys())[0]
            item, subtree = self.tree[first_key]
        else:
            subtree = self.tree

        items = []
        for tree_num in subtree:
            item, _ = subtree[tree_num]
            items.append(item)
        return items

    def top_level(self):
        raise NotImplementedError

    def diff_subassembly(self, this_subtree, other_subtree):
        my_items = [branch[0] for branch in this_subtree.values()]
        other_items = [branch[0] for branch in other_subtree.values()]
        my_items.sort()
        other_items.sort()

        common_parts_self = []
        common_parts_other = []
        common_parts_diff_attrs = []
        self_only = []
        for item in my_items:
            if item is None or item.category in self.ignored_categories:
                continue
            if item in other_items:
                common_parts_self.append(item)

                other_index = other_items.index(item)
                other_item = other_items[other_index]
                common_parts_other.append(other_item)

                common_parts_diff_attrs.append(
                    item.diff(other_item, self.item_diff_names)
                )
            else:
                self_only.append(item)

        other_only = []
        for other_item in other_items:
            if other_item is None or other_item.category in self.ignored_categories:
                continue
            if other_item not in my_items:
                other_only.append(other_item)
        return (
            common_parts_self,
            common_parts_other,
            common_parts_diff_attrs,
            self_only,
            other_only,
        )

    def _diff(
        self, diff_report, this_tree, other_tree, toplevel_other=None, parent_num=""
    ):
        if toplevel_other is None:
            toplevel_other = other_tree

        branch_report = self.diff_subassembly(this_tree, other_tree)
        # if len(this_tree) > 0:
        #     some_item = next(iter(this_tree.values()))[0]
        # else:
        #     print(branch_report)
        #     return

        # if some_item.parent is None:
        #     report_tree_num = "1"
        # else:
        #     report_tree_num = "1." + some_item.parent_num
        self.set_branch(branch_report, parent_num, diff_report)
        common_parts_self = branch_report[0]
        common_parts_other = branch_report[1]
        for self_item, other_item in zip(common_parts_self, common_parts_other):
            tree_num = self_item.tree_num
            other_tree_num = other_item.tree_num

            next_item, next_tree = self.branch_from_tree_num(tree_num, self.tree)
            other_next_item, other_next_tree = self.branch_from_tree_num(
                other_tree_num, toplevel_other
            )

            # if other_next_item.category in ("CBL", "PCA", "CON"):
            #     continue

            if len(next_tree) > 0 or len(other_next_tree) > 0:
                self._diff(
                    diff_report, next_tree, other_next_tree, toplevel_other, tree_num
                )

    def diff(self, other):
        # compare assembly structure. Do parents match? Use item hash comparison
        # if an assembly branch matches, compare items in assembly
        assert isinstance(other, StructuredBOM)

        diff_report = {}
        self._diff(diff_report, self.tree, other.tree)
        return diff_report

    def diff_report_to_str(
        self, diff_report, other, show_common=False, skip_attrs=None
    ):
        report_str = "%s (%s)\t%s (%s)\n" % (
            self.name,
            len(self.items),
            other.name,
            len(other.items),
        )
        for tree_num, subtree, item, level in self.iter_tree(diff_report):
            tabs = "\t" * level
            common_parts_self = item[0]
            common_parts_other = item[1]
            common_parts_diff_attrs = item[2]
            self_only = item[3]
            other_only = item[4]
            if len(tree_num) > 0:
                assembly_item = self.branch_from_tree_num(tree_num)[0]
                report_str += "%s---- %s\t%s\t%s ----\n" % (
                    tabs,
                    tree_num,
                    assembly_item,
                    assembly_item.description,
                )
            else:
                report_str += "%s---- %s\tTop Level ----\n" % (tabs, tree_num)

            tabs = "\t" * (level + 1)
            for self_item, other_item, diff_attrs in zip(
                common_parts_self, common_parts_other, common_parts_diff_attrs
            ):
                if show_common or len(common_parts_diff_attrs) > 0:
                    report_str += "%s%s\t\t%s\t\t%s" % (
                        tabs,
                        self_item,
                        other_item,
                        self_item.description,
                    )
                    if len(common_parts_diff_attrs) > 0:
                        for attr_name in diff_attrs:
                            if skip_attrs is not None and attr_name in skip_attrs:
                                continue
                            report_str += "\t\t %s: %s != %s" % (
                                attr_name,
                                getattr(self_item, attr_name),
                                getattr(other_item, attr_name),
                            )
                    report_str += "\n"
            no_differences = True
            for subitem in self_only:
                no_differences = False
                report_str += "%s%s\t\t------\t\t%s\n" % (
                    tabs,
                    subitem,
                    subitem.description,
                )
            for subitem in other_only:
                no_differences = False
                report_str += "%s------         \t\t%s\t\t%s\n" % (
                    tabs,
                    subitem,
                    subitem.description,
                )
            if no_differences:
                report_str += "%sBOMs match\n" % tabs
            report_str += "\n"
        return report_str

    def diff_report_to_yaml(self, path, diff_report, other):
        def yamlify(tree_num, subtree, subreport, level):
            if len(tree_num) > 0:
                assembly_item = self.branch_from_tree_num(tree_num)[0]
                header = "%s\t%s\t%s" % (
                    tree_num,
                    assembly_item,
                    assembly_item.description,
                )
            else:
                header = "Top Level"
            # common_parts = item[1]
            self_only_report = []
            other_only_report = []

            # common_parts_self = subreport[0]
            # common_parts_other = subreport[1]
            # common_parts_diff_attrs = subreport[2]
            self_only = subreport[3]
            other_only = subreport[4]

            for item in self_only:
                self_only_report.append(
                    "%s\t%s\t%s" % (item.tree_num, item, item.description)
                )
            for item in other_only:
                other_only_report.append(
                    "%s\t%s\t%s" % (item.tree_num, item, item.description)
                )

            yaml_subreport = {
                "header": header,
                self.name: self_only_report,
                other.name: other_only_report,
            }

            if len(subtree[tree_num][1]) == 0:
                subtree[tree_num] = yaml_subreport
            else:
                subtree[tree_num][0] = yaml_subreport
            # subtree[tree_num][0] = item_str

        yaml_tree = self.apply_fn(yamlify, diff_report, create_new_tree=True)
        self._dump_to_yaml(path, yaml_tree)

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
        self._fill_to_length(first_row, header_length)
        color_mapping.append([TableColors.TITLE for _ in range(len(second_row))])
        report.append(second_row)

        for tree_num, subtree, item, level in self.iter_tree(diff_report):
            if len(tree_num) > 0:
                assembly_item = self.branch_from_tree_num(tree_num)[0]
                # report.append([" ".join(assembly_item.to_list_str())])
                row = [
                    assembly_item.tree_num,
                    assembly_item.get_primary(),
                    assembly_item.description,
                ]
                self._fill_to_length(row, header_length)

                report.append(row)
                color_mapping.append(
                    [TableColors.SUB_ASSEMBLY for _ in range(len(row))]
                )
            else:
                assembly_item = None
                row = ["Top Level"]
                self._fill_to_length(row, header_length)

                report.append(row)
                color_mapping.append(
                    [TableColors.SUB_ASSEMBLY for _ in range(len(row))]
                )
            no_differences = self._diff_toplevel_to_table(
                item, show_common, report, color_mapping
            )

            if no_differences:
                if assembly_item is None:
                    assembly_item_code = "top level"
                else:
                    assembly_item_code = assembly_item.get_primary()
                bom_match_row = ["", "BOMs match for %s" % assembly_item_code]
                self._fill_to_length(bom_match_row, header_length)
                report.append(bom_match_row)

                bom_match_colors = [TableColors.BLANK]
                bom_match_colors.extend(
                    [TableColors.LEFT_MATCH for _ in range(len(self.item_show_names))]
                )
                bom_match_colors.extend(
                    [TableColors.RIGHT_MATCH for _ in range(len(self.item_show_names))]
                )
                color_mapping.append(bom_match_colors)

            # else:
            #     if assembly_item:  # display top level item in diff report
            #         print("%s\t%s" % (assembly_item.propel_number, assembly_item.description))

        return report, color_mapping

    def diff_report_to_csv(self, path, diff_report, other, show_common=False):
        report, color_mapping = self.diff_report_to_table(
            diff_report, other, show_common
        )
        self._dump_to_csv(path, report)

    def __str__(self):
        s = ""
        for tree_num, subtree, item, level in self.iter_tree():
            item_str = item.to_list_str()
            # s += "%s%s\n" % (("\t" * level), "\t".join(item_str))
            s += "\t".join(item_str) + "\n"
        return s
