class HeaderFilter:
    def __init__(self, attribute_name, filters, parser_fn, is_critical=False):
        self.attribute_name = attribute_name
        self._supplied_filters = filters
        self.parser_fn = parser_fn
        self.is_critical = is_critical
        self.equivalent_hfs = []

    def filter_fn(self, header_entry):
        if header_entry == self.attribute_name:
            return True
        for supplied_filter in self._supplied_filters:
            if type(supplied_filter) == str:
                if header_entry.lower() == supplied_filter.lower():
                    return True
            elif callable(supplied_filter):
                if supplied_filter(header_entry):
                    return True

        return False

    def add_equivalent_hfs(self, *header_filters):
        for hf in header_filters:
            if not isinstance(hf, self.__class__):
                raise ValueError(
                    "Supplied value is not '%s': %s" % (self.__class__, hf)
                )
            self.equivalent_hfs.append(hf)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.attribute_name == other.attribute_name:
            return True
        if len(self.equivalent_hfs) > 0:
            for header_filter in self.equivalent_hfs:
                if header_filter.attribute_name == other.attribute_name:
                    return True

        return False
