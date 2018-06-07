'''Provide simple and routine functionality

All functionality presented:
Converting datetime to milliseconds
Shifting datetime
Creating time range with length of day
Retrieve today datetime with 0 hour and 0 minutes
Retrieve now datetime withoud microseconds

Parse string representation of datetime

Retrieve home folder path
Creating file with specified path
'''

import datetime
import re
from pathlib import Path
import platform
from os import path, makedirs

def datetime_to_milliseconds(datetime_inst):
    if datetime_inst is None:
        return None
    if isinstance(datetime_inst, list):
        datetime_inst = datetime_inst[0]
    epoch = datetime.datetime.utcfromtimestamp(0)
    return int((datetime_inst - epoch).total_seconds() * 1000.0)

def create_shift(delta):
    '''Returns start of epoch + delta'''
    return datetime.datetime.utcfromtimestamp(0) + delta

def create_shift_in_millis(delta):
    return datetime_to_milliseconds(create_shift(delta))

def shift_datetime_in_millis(datetime, delta):
    return datetime_to_milliseconds(datetime + delta)

def get_time_range_of_day(datetime_inst):
    '''For datetime 15.06.2018 20:40 returns (15.06.2018 0:00, 16.06.2018 0:00)'''
    start_day = datetime.datetime(datetime_inst.year, datetime_inst.month, datetime_inst.day)
    end_day = start_day + datetime.timedelta(days=1)
    return (start_day, end_day)

def today():
    '''For datetime 15.06.2018 20:40 returns 15.06.2018 0:00''' 
    return datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

def now():
    '''Current time with microseconds set to 0''' 
    return datetime.datetime.now().replace(microsecond=0)

def parse_date(arg, relative_support=True):
    '''Parse date like [0-9]-[0-9]-[0-9] and today[+-][0-9]'''
    simple_date = re.match('[0-9]+-[0-9]+-[0-9]+', arg)
    if simple_date is not None:
        return datetime.datetime.strptime(arg, "%d-%m-%Y")

    if relative_support:
        relative_date = re.match('today(([+-])([0-9]+))?$', arg)
        if relative_date is not None:
            sign = relative_date.group(2)
            shift = relative_date.group(3)
            today_d = today()
            if sign == '+':
                return today_d + datetime.timedelta(days=int(shift))
            elif sign == '-':
                return today_d - datetime.timedelta(days=int(shift))
            else:
                return today_d

    return None

def parse_time(arg, relative_support=True):
    '''Parse date like [0-9]:[0-9] and now[+-][0-9]'''
    simple_time = re.match('[0-9]+:[0-9]+', arg)
    if simple_time is not None:
        return datetime.datetime.strptime(arg, "%H:%M").time()

    if relative_support:
        relative_time = re.match('now(([+-])([0-9]+))?$', arg)
        if relative_time is not None:
            sign = relative_time.group(2)
            shift = relative_time.group(3)
            now_d = now().time()
            today_with_time = datetime.datetime.combine(today(), now_d)
            if sign == '+':
                return (today_with_time + datetime.timedelta(hours=int(shift))).time()
            elif sign == '-':
                return (today_with_time - datetime.timedelta(hours=int(shift))).time()
            else:
                return now_d

    return None

def get_home_folder():
    '''Returns home folder of library in Linux system only: $HOME/tasktracker''' 
    if platform.system() == 'Linux':
        return path.join(str(Path.home()), 'tasktracker')

def get_file_in_home_folder(file_name):
    '''Joins home folder with specified file name'''
    return path.join(get_home_folder(), file_name)

def create_file_if_not_exists(file_path):
    if not path.exists(path.dirname(file_path)):
        makedirs(path.dirname(file_path))

    try:
        open(file_path, 'r').close()
    except FileNotFoundError:
        open(file_path, 'w').close()