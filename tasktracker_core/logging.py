'''Logging behaviour of core

Allow to customize default logger or initialize fully custom logger

Module defines root logger for core with name "core". All other loggers
will be children of this root logger. Library creates a lot of 
subloggers with different names for different tasks. Existing of root logger
allows to configure only one logger

You can use default logger with specific params or initialize your
specific logger

LoggerConfig class manage root logger of package

Use get_logger function with specific logger name to get sublogger of root logger
'''

import logging
import logging.config
import os

from tasktracker_core import utils

class LoggerConfig():
    '''Manage root logger of package

    Default root logger separate message in two groups: low and high
    Low group is not important, regular information that usually used for
    debug and info purposes. By default messages with level INFO and lower
    is transfered in low group
    High group is important and very important messages like errors and warnings
    By default messages with levels WARNING and higher is transfere in high group
    Division into low and high allow to separate primary messages from others
    that allow you to see the most important first
    Low group is recorded in low.log in home directory by default
    High group is recorded in high.log in home directory by default
    Default logger consider all types of messages

    You can change this params by specifying levels and paths of loggers.

    high_log_path - path to high group
    low_log_path - path to low group

    high_log_level - level from which messages will be treated as high group
    low_log_level - level to which messages will be treated as low group

    Also you can disable either high or low group
    Set high_logging_enabled to False to disable high logging
    Set low_logging_enabled to False to disable low logging

    To disable logging at all set logging_enabled to False
    This field will block logging even in fully custom root logger

    If you want to set your own logger with model of logging different 
    from default, init logger with name 'core' and set custom_logger_enabled to True
    In this case function get_core_root_logger will not try to specify default
    behaviour of logger, saving you custom behaviour
    If you want to change some specific params of default logger you can call
    get_core_root_logger and change params in returned logger
    To roll back logger to default settings just set custom_logger_enabled to False
    and logger will be setted to default with next call of get_core_root_logger
    '''


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
    def _init_default_logger(cls, logger):
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
        '''Convert string representation of level to python logging level

        You can use this method to convert words 'CRITICAL', 'ERROR', 'WARNING',
        'INFO', 'DEBUG', 'NOTSET' to appropriate logging levels.
        You can use this in databases or config files
        '''
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
        '''Initialize root logger of library with name 'core'

        Checks if custom_logger_enabled is True. 
        In this case gets logger with name 'core' and returns. 
        Otherwise initialize default logger with name 'core' and returns

        If logging_enabled is False disables logger, even if it's not default logger

        Sets level of the most root logger of whole app (getLogger() returns) to DEBUG
        '''
        logging.getLogger().setLevel(logging.DEBUG)

        core_logger = logging.getLogger('core')
        if not cls.custom_logger_enabled:
            cls._init_default_logger(core_logger)

        if cls.logging_enabled:
            logging.disable(logging.NOTSET)
        else:
            logging.disable(logging.CRITICAL)

        return core_logger

def get_logger(name):
    '''Returns sublogger of root 'core' logger with specific name'''
    core_root = LoggerConfig.get_core_root_logger()
    return core_root.getChild(name)