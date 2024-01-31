from bom.structured_bom import StructuredBOM
from item.solidworks_item import SolidworksItem, StructuredSolidworksItem

from .bom import BOM


class SolidworksBOM(BOM):
    def __init__(self, name):
        super(SolidworksBOM, self).__init__(name)

    def create_item(self, line):
        return SolidworksItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return SolidworksItem.from_item(item, header)


class SolidworksStructured(StructuredBOM):
    def __init__(self, name):
        super(SolidworksStructured, self).__init__(name)

    def create_item(self, line):
        return StructuredSolidworksItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return StructuredSolidworksItem.from_item(item, header)

    def top_level(self) -> SolidworksBOM:
        items = self._get_top_level_list()
        return SolidworksBOM.from_list(self.name, items)
