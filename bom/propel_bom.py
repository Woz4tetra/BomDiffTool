from bom.bom import BOM
from item.propel_item import PropelItem, StructuredPropelItem

from .structured_bom import StructuredBOM


class PropelBOM(BOM):
    def __init__(self, name):
        super(PropelBOM, self).__init__(name)

    def create_item(self, line):
        return PropelItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return PropelItem.from_item(item, header)


class PropelStructured(StructuredBOM):
    def __init__(self, name):
        super(PropelStructured, self).__init__(name)

    def _preprocess_tree_num(self):
        min_level = min(self.items, key=lambda item: item.level).level
        StructuredPropelItem.set_tree_counter(min_level)

        super(PropelStructured, self)._preprocess_tree_num()

    def create_item(self, line):
        return StructuredPropelItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return StructuredPropelItem.from_item(item, header)

    def top_level(self) -> PropelBOM:
        items = self._get_top_level_list()
        return PropelBOM.from_list(self.name, items)
