from .item import Item


class StructuredBomItem(Item):
    MAX_PARENT = 0

    def __init__(self, header):
        super(StructuredBomItem, self).__init__(header)
        self.tree_num = ""
        self.level = 0

        self.parent = None

    @staticmethod
    def convert_item_no(x):
        if isinstance(x, float):
            if int(x) == x:
                x = str(int(x))
            else:
                x = str(x)
        return x

    def _parse_tree_num(self):
        num_split = self.tree_num.split(".")
        self.parent_num = ".".join(num_split[:-1])
        self.level = len(num_split)
        top_level = int(num_split[0])
        if self.__class__.MAX_PARENT < top_level:
            self.__class__.MAX_PARENT = top_level

    def to_list(self, *names):
        list_item = super(StructuredBomItem, self).to_list(*names)
        if self.parent is not None:
            list_item.append(self.parent.item_code)
            list_item.append(self.parent_num)
        return list_item

    def get_preparsed_header(self):
        header = super(StructuredBomItem, self).get_preparsed_header()

        header.append("Parent Item Code")
        header.append("Parent #")
        return header

    @classmethod
    def from_line(cls, header, line, primary_prop_name=None):
        obj = super(StructuredBomItem, cls).from_line(header, line, primary_prop_name)
        obj._assign_tree_num()
        return obj

    @classmethod
    def from_item(cls, other, header=None):
        obj = super(StructuredBomItem, cls).from_item(other, header)
        obj._assign_tree_num()
        return obj

    def _assign_tree_num(self):
        if len(self.tree_num) != 0:
            return
        self.__class__.MAX_PARENT += 1
        self.tree_num = str(self.__class__.MAX_PARENT)
