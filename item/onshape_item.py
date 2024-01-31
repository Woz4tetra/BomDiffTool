from .common_filters import get_filters
from .header_filter import HeaderFilter
from .item import Item
from .structured_item import StructuredBomItem

HEADER_FILTER_NAMES = (
    "name",
    "item_code",
    "revision",
    "quantity",
    "category",
    "suggested_vendor",
    "vendor_pn",
    "suggested_manufacturer",
    "manufacturer_pn",
)


class OnshapeItem(Item):
    def __init__(self, header):
        super(OnshapeItem, self).__init__(header)

        self.header_filters = get_filters(*HEADER_FILTER_NAMES)


class StructuredOnshapeItem(StructuredBomItem):
    def __init__(self, header):
        super(StructuredOnshapeItem, self).__init__(header)
        self.header_filters = get_filters(*HEADER_FILTER_NAMES)
        self.header_filters.extend(
            [
                HeaderFilter("tree_num", ("Item",), self.convert_item_no, True),
            ]
        )
