from .common_filters import get_common_filters, is_propel_number, remove_newlines


class Item:
    PROPEL_NUM_DEFAULT = "XXXXXX"
    CATEGORY_DEFAULT = "XXX"
    REVISION_DEFAULT = "XX"
    item_primary_prop = "propel_number"
    equivalent_items = []

    def __init__(self, header):
        self.header = header
        self.propel_number = self.PROPEL_NUM_DEFAULT
        self.item_code = ""
        self.item_id = ""
        self.category = self.CATEGORY_DEFAULT
        self.revision = self.REVISION_DEFAULT
        self.description = ""
        self.quantity = 0
        self.primary_prop = "propel_number"

        self.header_filters = (
            get_common_filters()
        )  # match strings/functions when looking for attribute in header

    @classmethod
    def set_equivalent_mapping(cls, equivalent_items):
        cls.equivalent_items = equivalent_items

    @classmethod
    def set_primary_prop(cls, new_prop):
        cls.item_primary_prop = new_prop

    def _check_for_item_code(self):
        # check if the found propel number is actually an item code
        # CAT-XXXXXX
        # (P.S. if you rename another column to item code, this tool will still work. It will use that column as the
        # primary comparison instead)
        components = None
        if len(self.item_id) > 0 and "-" in self.item_id:
            components = self.item_id.split("-")
        elif len(self.item_code) > 0 and "-" in self.item_code:
            components = self.item_code.split("-")

        if components is not None:
            self._parse_split_item_components(components)

        self._update_code_and_id()

    def _parse_split_item_components(self, components):
        category = components[0]
        propel_number = components[1]
        if len(components) > 2:
            revision = components[2]
        else:
            revision = self.revision

        # if category not in CODE_CATEGORIES:
        #     print("WARNING: invalid category: %s" % category)
        if not is_propel_number(propel_number):
            # raise ValueError("Invalid propel number: %s" % propel_number)
            print("WARNING: Invalid propel number: %s" % propel_number)
        # if not self.is_revision(revision):
        #     print("WARNING: invalid revision: %s" % revision)

        # print("%s-%s-%s\t%s-%s-%s" % (
        #     category, propel_number, revision, self.category, self.propel_number, self.revision))

        if self.category == self.CATEGORY_DEFAULT:
            self.category = category
        else:
            # assert self.category == category, "%s != %s" % (self.category, category)
            pass  # Solidworks item ID is updated manually and is usually incorrect
        if self.propel_number == self.PROPEL_NUM_DEFAULT:
            self.propel_number = propel_number
        else:
            # assert self.propel_number == propel_number, "%s != %s" % (self.propel_number, propel_number)
            pass  # propel assigns PCBs as having 'PCB' in the propel number...
        if self.revision == self.REVISION_DEFAULT:
            self.revision = revision
        else:
            # assert self.revision == revision, "%s != %s" % (self.revision, revision)
            pass  # propel's revision assignment in the item id can differ from the revision column...

    def _update_code_and_id(self):
        if (
            self.category in self.propel_number
        ):  # PCBs have the category in the item number
            self.item_code = self.propel_number
        else:
            self.item_code = "%s-%s" % (self.category, self.propel_number)
        self.item_id = "%s-%s" % (self.item_code, self.revision)

    def get_header_filter_match(self, name):
        header_filter_match = None
        for header_filter in self.header_filters:
            if bool(header_filter.filter_fn(name)):
                header_filter_match = header_filter
                break
        return header_filter_match

    @classmethod
    def from_line(cls, header, line, primary_prop_name=None):
        if primary_prop_name is None:
            primary_prop_name = cls.item_primary_prop
        # assert len(header) == len(line), "%s != %s" % (len(header), len(line))
        obj = cls(header)

        critical_keys_found = {
            f.attribute_name: False for f in obj.header_filters if f.is_critical
        }
        attributes_set = set()
        primary_prop_found = False
        primary_header_filter = obj.get_header_filter_match(primary_prop_name)

        for name, index in header.items():
            header_filter_match = obj.get_header_filter_match(name)
            if (
                header_filter_match is None
                or header_filter_match.attribute_name in attributes_set
            ):
                continue
            attr_name = header_filter_match.attribute_name

            if not primary_prop_found:
                if (
                    primary_header_filter is not None
                    and primary_header_filter == header_filter_match
                ):
                    primary_prop_found = True
                    obj.primary_prop = primary_header_filter.attribute_name
                    # print("Selected primary prop:", obj.primary_prop)

            if attr_name in critical_keys_found:
                critical_keys_found[attr_name] = True
            if index >= len(line):
                obj.__dict__[attr_name] = None
                continue
            try:
                element = remove_newlines(line[index])
                value = header_filter_match.parser_fn(element)
                # if header_key in obj.__dict__ and obj.__dict__[header_key] != value:
                #     print("%s already found. Overriding value" % header_key)
                #     print(obj.__dict__[header_key], value)
                obj.__dict__[attr_name] = value
                attributes_set.add(attr_name)
            except ValueError as e:
                obj.__dict__[attr_name] = None
                # print(name, line, e)
                raise ValueError(
                    "Failed to parse for attribute '%s' with matched header name '%s': %s"
                    % (attr_name, name, str(e))
                )

        if not primary_prop_found:
            raise ValueError(
                "Primary comparison attribute '%s' not found in header '%s'"
                % (primary_prop_name, header)
            )

        if not all(critical_keys_found.values()):
            error_str = ""
            for key, found in critical_keys_found.items():
                if not found:
                    error_str += "\t" + key + "\n"
            raise ValueError(
                "Critical attributes not found in header '%s':\n%s"
                % (header, error_str)
            )

        obj._check_for_item_code()

        return obj

    @classmethod
    def from_item(cls, other, header=None):
        assert isinstance(other, Item), "Encountered an invalid item (%s: %s)" % (
            type(other),
            other,
        )
        if header is None:
            header = other.header
        obj = cls(header)
        for f in obj.header_filters:
            if hasattr(other, f.attribute_name):
                other_attr = getattr(other, f.attribute_name)
                setattr(obj, f.attribute_name, other_attr)
        obj.primary_prop = other.primary_prop
        return obj

    def get_primary(self):
        return getattr(self, self.primary_prop)

    def parse_equivalent_items(self):
        header_filter = self.get_header_filter_match(self.item_primary_prop)
        parsed_equivalence_mapping = []
        for items in self.equivalent_items:
            if not (type(items) == list or type(items) == tuple):
                print("Ignoring equivalence item that isn't a list: %s" % items)
                continue
            equivalence = []
            for value in items:
                value = header_filter.parser_fn(value)
                equivalence.append(value)
            parsed_equivalence_mapping.append(equivalence)
        return parsed_equivalence_mapping

    def get_equivalent(self, other):
        assert isinstance(other, Item), "Encountered an invalid item (%s: %s)" % (
            type(other),
            other,
        )

        equivalence_mapping = self.parse_equivalent_items()
        for mapping in equivalence_mapping:
            if other.get_primary() in mapping:
                return mapping[0]
        return None

    def __eq__(self, other):
        if isinstance(other, Item):
            return hash(self) == hash(other)
        return False

    def __lt__(self, other):
        if isinstance(other, Item):
            return self.get_primary() < other.get_primary()
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, Item):
            return self.get_primary() != other.get_primary()
        else:
            return False

    def to_json(self):
        return (
            "{description}, "
            "QTY: {quantity}, "
            "{category}-{propel_number}".format(**self.__dict__)
        )

    def to_list(self, *names):
        if len(names) == 0:
            names = self.get_header()
        l = []
        for name in names:
            l.append(self.__dict__[name])

        return l

    def get_header(self):
        return [f.attribute_name for f in self.header_filters]

    def get_preparsed_header(self):
        header = []
        for f in self.header_filters:
            header.append(f.attribute_name)

        return header

    def to_list_str(self, *names):
        return list(map(str, self.to_list(*names)))

    def diff(self, other, diff_names):
        assert isinstance(other, Item), other.__class__.__name__
        diff_prop_names = []

        for name in diff_names:
            header_filter_match = self.get_header_filter_match(name)
            other_header_filter_match = other.get_header_filter_match(name)
            if (
                header_filter_match is None and other_header_filter_match is None
            ):  # neither match the name. Ignore it
                continue
            if (
                header_filter_match is not None
                and other_header_filter_match is not None
            ):
                attr_name = header_filter_match.attribute_name
                assert (
                    header_filter_match.attribute_name
                    == other_header_filter_match.attribute_name
                ), "%s != %s" % (
                    header_filter_match.attribute_name,
                    other_header_filter_match.attribute_name,
                )
            else:
                # if either header_filter_match or other_header_filter_match is not None, this statement will return
                # the object that isn't None
                matched_filter = header_filter_match or other_header_filter_match
                attr_name = matched_filter.attribute_name
            if getattr(self, attr_name) != getattr(other, attr_name):
                diff_prop_names.append(attr_name)

        return diff_prop_names

    def __hash__(self):
        equivalent_prop = self.get_equivalent(self)
        if equivalent_prop is None:
            return hash(self.get_primary())
        else:
            return hash(equivalent_prop)

    def __str__(self):
        return str(self.get_primary())

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.get_primary())
