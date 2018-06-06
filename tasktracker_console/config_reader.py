import configparser
from os import path

from tasktracker_core import utils

class ConfigReader():

    DEFAULT_CONFIG_PATH = utils.get_file_in_home_folder('tm.conf')

    config_path = DEFAULT_CONFIG_PATH

    def __init__(self):
        self.username = None
        self.db_path = None
        self.high_log_path = None
        self.low_log_path = None
        self.high_log_level = None
        self.low_log_level = None
        self.enable_logging = None
        self.enable_high_logging = None
        self.enable_low_logging = None

    def read_config(self):
        config = configparser.ConfigParser()

        try:
            config.read(self.config_path)
        except FileNotFoundError:
            # Logging
            return

        if 'user' in config:
            user_config = config['user']
            self.username = user_config.get('name')

        if 'database' in config:
            database_config = config['database']
            self.db_path = database_config.get('path')

        if 'logger' in config:
            logger_config = config['logger']
            self.high_log_path = logger_config.get('high_log_path')
            self.low_log_path = logger_config.get('low_log_path')
            self.high_log_level = logger_config.get('high_log_level')
            self.low_log_level = logger_config.get('low_log_level')
            self.enable_logging = logger_config.getboolean('enable_logging')
            self.enable_high_logging = logger_config.getboolean('enable_high_logging')
            self.enable_low_logging = logger_config.getboolean('enable_low_logging')

        return config

    def write_username_in_config(self, username):
        config = self.read_config()
        if config is None:
            config = configparser.ConfigParser()

        config['user'] = {'name': username}

        with open(self.config_path, 'w') as config_file:
            config.write(config_file)
