import os
import csv
import yaml
from pathlib import Path

from logger import LoggerManager

logger = LoggerManager.get_logger()


class FilterConfig:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.filters = kwargs.get("filters", [])
        self.type = kwargs.get("type", "")
        self.is_critical = kwargs.get("is_critical", False)
        self.equivalent_to = kwargs.get("equivalent_to", [])

    def __repr__(self):
        props_str = ", ".join([str(key) + "=" + str(value) for key, value in self.__dict__.items()])
        return "%s(%s)" % (self.__class__.__name__, props_str)

    def to_dict(self):
        return {
            "name": self.name,
            "filters": self.filters,
            "type": self.type,
            "is_critical": self.is_critical,
            "equivalent_to": self.equivalent_to,
        }


class Config:
    def __init__(self, path):
        self.path = path

        self.left_bom = ""
        self.right_bom = ""
        self.left_type = ""
        self.right_type = ""
        self.show_common = False
        self.default_save_dir = "~"
        self.default_load_dir = "~"
        self.diff_properties = None
        self.show_properties = None
        self.primary_prop = "Item Number"
        self.ignored_categories = None
        self.filters = {}
        self.equivalent_items = []
        self.all_property_names = []

        if os.path.isfile(self.path):
            logger.debug("Loading config from %s" % repr(self.path))
            self.load(self.path)

        logger.debug("All props: %s" % self.all_property_names)

    def load(self, path):
        self.path = Path(path)
        with open(path) as file:
            config = yaml.safe_load(file)
        if config is None:
            config = {}

        self.left_bom = config.get("left_bom", self.left_bom)
        self.right_bom = config.get("right_bom", self.right_bom)
        self.left_type = config.get("left_type", self.left_type)
        self.right_type = config.get("right_type", self.right_type)
        self.show_common = config.get("show_common", self.show_common)
        self.default_save_dir = config.get("default_save_dir", self.default_save_dir)
        self.default_load_dir = config.get("default_load_dir", self.default_load_dir)
        self.ignored_categories = config.get("ignored_categories", [])

        diff_properties = config.get("diff_properties", self.diff_properties)
        self.diff_properties = self.parse_properties(diff_properties)

        show_properties = config.get("show_properties", self.show_properties)
        self.show_properties = self.parse_properties(show_properties)

        self.filters = self.parse_filters(config.get("filters", self.filters))
        self.all_property_names = [name for name in self.filters]

        self.equivalent_items = self.load_csv(self.path.parent / "equivalent_items.csv")

        primary_prop = config.get("primary_prop", self.primary_prop)
        results = self.parse_properties([primary_prop])
        if len(results) == 0:
            raise ValueError("'%s' is an invalid property name" % primary_prop)
        self.primary_prop = results[0]

    def load_csv(self, path):
        with open(path) as file:
            reader = csv.reader(file)
            table = list(reader)
        return table

    def parse_filters(self, filter_config: dict):
        key = ""
        configs = {}
        try:
            for key, value in filter_config.items():
                config = FilterConfig()
                config.name = key
                config.type = value.get("type", config.type)
                config.filters = value.get("filters", config.filters)
                config.is_critical = value.get("is_critical", config.is_critical)
                config.equivalent_to = value.get("equivalent_to", config.equivalent_to)
                configs[key] = config
        except BaseException as e:
            raise ValueError(
                "Failed to load filters config. Exception was '%s: %s'.%s" % (
                    e.__class__.__name__, str(e),
                    "" if not key else " Exception occurred with key '%s'" % key)
            )
        logger.debug("Loaded filter configs: %s" % repr(configs))
        return configs

    def parse_properties(self, diff_properties):
        logger.debug("Parsing properties: %s" % repr(diff_properties))
        if diff_properties is None:
            diff_properties = []
        assert type(diff_properties) == list or type(diff_properties) == tuple, str(type(diff_properties))

        matched_properties = []
        lowered_names = [x.lower() for x in self.all_property_names]
        for name in diff_properties:
            name = name.lower()
            if name in lowered_names:
                matched_name = self.all_property_names[lowered_names.index(name)]
                matched_properties.append(matched_name)
        logger.debug("Matched properties: %s" % repr(matched_properties))
        return matched_properties

    def to_dict(self):
        return {
            "left_bom": self.left_bom,
            "right_bom": self.right_bom,
            "left_type": self.left_type,
            "right_type": self.right_type,
            "show_common": self.show_common,
            "default_save_dir": self.default_save_dir,
            "default_load_dir": self.default_load_dir,
            "diff_properties": self.diff_properties,
            "show_properties": self.show_properties,
            "primary_prop": self.primary_prop,
            "ignored_categories": self.ignored_categories,
            "filters": {name: config_filter.to_dict() for name, config_filter in self.filters.items()},
        }

    def save(self, path):
        with open(path, 'w') as file:
            yaml.dump(self.to_dict(), file)

    def get_dialog_dir(self, config_dir):
        if config_dir is None:
            config_dir = "~"
        config_dir = os.path.expanduser(config_dir)
        if not os.path.isdir(config_dir):
            logger.debug("Dialog dir is not a directory: %s" % repr(config_dir))
            config_dir = os.path.expanduser("~")
        config_dir = config_dir.replace("\\", os.sep)
        config_dir = config_dir.replace("/", os.sep)
        logger.debug("Dialog dir: %s" % repr(config_dir))
        return config_dir

    def get_default_save_dir(self):
        logger.debug("Getting save dir")
        return self.get_dialog_dir(self.default_save_dir)

    def get_default_load_dir(self):
        logger.debug("Getting load dir")
        return self.get_dialog_dir(self.default_load_dir)

    def get_ignored_categories_str(self):
        return ", ".join(self.ignored_categories)
