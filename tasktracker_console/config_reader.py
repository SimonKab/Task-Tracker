'''Configuration reader of console application

Configuration file is a file like INI in Windows. 
It means markup rules specified by standard Python library "configparser"

There are three groups: user, database and logger

In user group there is only one item: name. It is name of primary user.
All operations will be performed on its behalf

In database group there is only one item: path. It is path to database file

In logger group there are seven items:
enable_logging - available or not logging
enable_high_logging - available or not high logging in default logger
enable_low_logging - available or not low logging in default logger
high_log_path - path to high log file
low_log_path - path to low log file
high_log_level - level of high logging (see logging module)
low_log_level - level of low_logging (see logging module)

All read information stored in ConfigReader class
'''

import configparser
from os import path

from tasktracker_core import utils

class ConfigReader():
    '''Reads configuration file

    You can set configuration file to proccess by config_path field
    By default config file will be searched in home directory 
    which core library specifies

    Object of class stores information aboud configuration of app

    read_config method reads and fills object with config information
    write_username_in_config methos updates primary user name
    '''

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
        '''Reads and fills object with config information

        Returns config object of configparser.ConfigParser. 
        You can use it to retrieve data that ConfigReader can not retrieve
        '''
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
        '''Write current login user name to config file'''
        config = self.read_config()
        if config is None:
            config = configparser.ConfigParser()

        config['user'] = {'name': username}

        with open(self.config_path, 'w') as config_file:
            config.write(config_file)
