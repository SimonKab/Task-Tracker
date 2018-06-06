import logging
import logging.config
import os

from tasktracker_core import utils

class LoggerConfig():

    DEFAULT_PATH_HIGH = utils.get_file_in_home_folder('high.log')
    DEFAULT_PATH_LOW = utils.get_file_in_home_folder('low.log')

    logging_enabled = True
    high_logging_enabled = True
    low_logging_enabled = True
    custom_logger_enabled = False

    high_log_path = DEFAULT_PATH_HIGH
    low_log_path = DEFAULT_PATH_LOW

    high_log_level = logging.WARNING
    low_log_level = logging.INFO

    class LowLoggingFilter(logging.Filter):
        def filter(self, record):
            return record.levelno <= LoggerConfig.low_log_level

    class HighLoggingFilter(logging.Filter):
        def filter(self, record):
            return record.levelno >= LoggerConfig.high_log_level

    @classmethod
    def init_default_logger(cls, logger):
        utils.create_file_if_not_exists(cls.high_log_path)
        utils.create_file_if_not_exists(cls.low_log_path)

        formatter = logging.Formatter('%(asctime)s, %(name)s, [%(levelname)s]: %(message)s')

        file_high_logging_handler = logging.FileHandler(cls.high_log_path)
        file_high_logging_handler.addFilter(cls.HighLoggingFilter())
        file_high_logging_handler.setLevel(logging.NOTSET)
        file_high_logging_handler.setFormatter(formatter)

        file_low_logging_handler = logging.FileHandler(cls.low_log_path)
        file_low_logging_handler.addFilter(cls.LowLoggingFilter())
        file_low_logging_handler.setLevel(logging.NOTSET)
        file_low_logging_handler.setFormatter(formatter)

        logger.setLevel(logging.NOTSET)
        if cls.high_logging_enabled:
            logger.addHandler(file_high_logging_handler)
        if cls.low_logging_enabled:
            logger.addHandler(file_low_logging_handler)

    @staticmethod
    def get_logger_level_by_str(str_level):
        if str_level == 'CRITICAL':
            return logging.CRITICAL
        if str_level == 'ERROR':
            return logging.ERROR
        if str_level == 'WARNING':
            return logging.WARNING
        if str_level == 'INFO':
            return logging.INFO
        if str_level == 'DEBUG':
            return logging.DEBUG
        if str_level == 'NOTSET':
            return logging.NOTSET

    @classmethod
    def get_core_root_logger(cls):
        logging.getLogger().setLevel(logging.DEBUG)

        core_logger = logging.getLogger('core')
        if not cls.custom_logger_enabled:
            cls.init_default_logger(core_logger)

        if cls.logging_enabled:
            logging.disable(logging.NOTSET)
        else:
            logging.disable(logging.CRITICAL)

        return core_logger

def get_logger(name):
    core_root = LoggerConfig.get_core_root_logger()
    return core_root.getChild(name)