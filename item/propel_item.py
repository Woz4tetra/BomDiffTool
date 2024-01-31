from item.header_filter import HeaderFilter
from item.structured_item import StructuredBomItem
from item.tree_counter import TreeCounter

from .common_filters import convert_level, get_filters
from .item import Item

HEADER_FILTER_NAMES = (
    "description",
    "quantity",
    "propel_number",
    "item_code",
    "item_id",
    "category",
    "revision",
    "pdm_number",
    "filename",
    "configuration",
    "material",
    "finish",
    "manufacturer",
    "mfg_number",
    "procurement_type",
    "has_attachments",
    "owner",
)


class PropelItem(Item):
    def __init__(self, header):
        super(PropelItem, self).__init__(header)

        self.header_filters = get_filters(*HEADER_FILTER_NAMES)


class StructuredPropelItem(StructuredBomItem):
    _tree_counter = None

    def __init__(self, header):
        super(StructuredPropelItem, self).__init__(header)
        self.header_filters = get_filters(*HEADER_FILTER_NAMES)
        self.header_filters.extend(
            [
                HeaderFilter("level", "Level", convert_level, True),
                HeaderFilter("tree_num", ("ITEM NO.", "#", "Tree Num"), str),
            ]
        )

    def _parse_tree_num(self):
        if len(self.tree_num) == 0:
            assert self.level is not None
            assert self._tree_counter is not None
            self.tree_num, self.parent_num = self._tree_counter.get_tree_num(self.level)
        else:
            super(StructuredPropelItem, self)._parse_tree_num()

    @classmethod
    def from_line(cls, header, line, primary_prop_name=None):
        obj = super(StructuredBomItem, cls).from_line(header, line, primary_prop_name)

        if obj.level is None:
            return None
        else:
            return obj

    @classmethod
    def set_tree_counter(cls, min_level):
        cls._tree_counter = TreeCounter(min_level)
