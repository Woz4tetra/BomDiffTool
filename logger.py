import logging
import datetime
from logging import handlers


class MyFormatter(logging.Formatter):
    converter = datetime.datetime.fromtimestamp

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            s = ct.strftime("%Y-%m-%dT%H:%M:%S,%f")
            # s = "%s,%03d" % (t, record.msecs)
        return s


class LoggerManager:
    logger = None

    def __init__(self):
        raise Exception("{} is class only".format(self.__class__.__name__))

    @classmethod
    def get_logger(cls):
        log_config = dict(
            name="bom_diff",
            level=logging.DEBUG,
            file_name="bom_diff.log",
            format="%(levelname)s\t%(asctime)s\t[%(name)s, %(filename)s:%(lineno)d]\t%(message)s"
        )
        log_config["path"] = "./" + log_config["file_name"]

        if cls.logger is not None:
            return cls.logger
        cls.logger = cls._create_logger(**log_config)
        return cls.logger

    @staticmethod
    def _create_logger(**kwargs):
        name = kwargs["name"]
        path = kwargs["path"]
        level = kwargs["level"]
        format = kwargs["format"]
        # suffix = kwargs["suffix"]

        logger = logging.getLogger(name)
        logger.setLevel(level)

        formatter = MyFormatter(format)

        file_handler = logging.FileHandler(path, mode='w')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # rotate_handle = handlers.TimedRotatingFileHandler(
        #     path,
        #     when="midnight", interval=1
        # )
        # rotate_handle.setLevel(level)
        # rotate_handle.setFormatter(formatter)
        # rotate_handle.suffix = suffix
        # logger.addHandler(rotate_handle)

        print_handle = logging.StreamHandler()
        print_handle.setLevel(level)
        print_handle.setFormatter(formatter)
        logger.addHandler(print_handle)

        return logger
