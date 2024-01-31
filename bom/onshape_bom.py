from bom.solidworks_bom import SolidworksBOM
from bom.structured_bom import StructuredBOM
from item.onshape_item import OnshapeItem, StructuredOnshapeItem

from .bom import BOM


class OnshapeBOM(BOM):
    def __init__(self, name):
        super(OnshapeBOM, self).__init__(name)

    def create_item(self, line):
        return OnshapeItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return OnshapeItem.from_item(item, header)


class OnshapeStructured(StructuredBOM):
    def __init__(self, name):
        super(OnshapeStructured, self).__init__(name)

    def create_item(self, line):
        return StructuredOnshapeItem.from_line(self.header, line)

    def recreate_item(self, item, header=None):
        return StructuredOnshapeItem.from_item(item, header)

    def top_level(self) -> SolidworksBOM:
        items = self._get_top_level_list()
        return SolidworksBOM.from_list(self.name, items)
