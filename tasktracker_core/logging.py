import logging
import os

DEFAULT_PATH_HIGH = 'info/high.log'
DEFAULT_PATH_LOW = 'info/low.log'

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
NOTSET = logging.NOTSET
logging.getLogger().setLevel(logging.DEBUG)

def get_logger(name):
    def check_and_create_logger_files(path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        try:
            open(path, 'r').close()
        except FileNotFoundError:
            open(path, 'w').close()

    check_and_create_logger_files(DEFAULT_PATH_HIGH)
    check_and_create_logger_files(DEFAULT_PATH_LOW)

    formatter = logging.Formatter('%(asctime)s, %(name)s, [%(levelname)s]: %(message)s')

    file_high_logging_handler = logging.FileHandler(DEFAULT_PATH_HIGH)
    file_high_logging_handler.addFilter(HighLoggingFilter())
    file_high_logging_handler.setLevel(logging.DEBUG)
    file_high_logging_handler.setFormatter(formatter)

    file_low_logging_handler = logging.FileHandler(DEFAULT_PATH_LOW)
    file_low_logging_handler.addFilter(LowLoggingFilter())
    file_low_logging_handler.setLevel(logging.DEBUG)
    file_low_logging_handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(file_high_logging_handler)
    log.addHandler(file_low_logging_handler)

    return log

class LowLoggingFilter(logging.Filter):
    def filter(self, record):
        return record.levelno <= logging.INFO

class HighLoggingFilter(logging.Filter):
    def filter(self, record):
        return record.levelno > logging.INFO