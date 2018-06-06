import logging
import logging.config
from os import path
import os

from tasktracker_core import utils

class LoggerConfig():

    DEFAULT_PATH_HIGH = path.join(utils.get_home_folder(), 'high.log')
    DEFAULT_PATH_LOW = path.join(utils.get_home_folder(), 'low.log')

    logging_enabled = False
    custom_logger_enabled = False

    high_log_path = DEFAULT_PATH_HIGH
    low_log_path = DEFAULT_PATH_LOW

    high_log_level = logging.WARNING
    low_log_level = logging.INFO

    class LowLoggingFilter(logging.Filter):
        def filter(self, record):
            return record.levelno <= LoggerConfig._low_log_level

    class HighLoggingFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= LoggerConfig._high_log_level

    @classmethod
    def init_default_logger(cls, logger):
        def check_and_create_logger_files(path):
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            try:
                open(path, 'r').close()
            except FileNotFoundError:
                open(path, 'w').close()

        check_and_create_logger_files(cls._high_log_path)
        check_and_create_logger_files(cls._low_log_path)

        formatter = logging.Formatter('%(asctime)s, %(name)s, [%(levelname)s]: %(message)s')

        file_high_logging_handler = logging.FileHandler(cls._high_log_path)
        file_high_logging_handler.addFilter(cls.HighLoggingFilter())
        file_high_logging_handler.setLevel(logging.NOTSET)
        file_high_logging_handler.setFormatter(formatter)

        file_low_logging_handler = logging.FileHandler(cls._low_log_path)
        file_low_logging_handler.addFilter(cls.LowLoggingFilter())
        file_low_logging_handler.setLevel(logging.NOTSET)
        file_low_logging_handler.setFormatter(formatter)

        logger.setLevel(logging.NOTSET)
        logger.addHandler(file_high_logging_handler)
        logger.addHandler(file_low_logging_handler)

    @classmethod
    def get_core_root_logger(cls):
        core_logger = logging.getLogger('core')
        if not cls._custom_logger_enabled:
            cls.init_default_logger(core_logger)

        if cls._logging_enabled:
            logging.disable(logging.NOTSET)
        else:
            logging.disable(logging.CRITICAL)

        return core_logger

def get_logger(name):
    core_root = LoggerConfig.get_core_root_logger()
    return core_root.getChild(name)