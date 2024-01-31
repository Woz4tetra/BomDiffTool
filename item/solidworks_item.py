from item.header_filter import HeaderFilter
from item.structured_item import StructuredBomItem

from .common_filters import get_filters
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


class SolidworksItem(Item):
    def __init__(self, header):
        super(SolidworksItem, self).__init__(header)

        self.header_filters = get_filters(*HEADER_FILTER_NAMES)


class StructuredSolidworksItem(StructuredBomItem):
    def __init__(self, header):
        super(StructuredSolidworksItem, self).__init__(header)
        self.header_filters = get_filters(*HEADER_FILTER_NAMES)
        self.header_filters.extend(
            [
                HeaderFilter(
                    "tree_num",
                    ("ITEM NO.", "Level", "#", "Tree Num"),
                    self.convert_item_no,
                    True,
                ),
            ]
        )
