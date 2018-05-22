import datetime

def datetime_to_milliseconds(datetime_inst):
    if datetime_inst is None:
        return None
    epoch = datetime.datetime.utcfromtimestamp(0)
    return int((datetime_inst - epoch).total_seconds() * 1000.0)

def create_shift(delta):
    return datetime.datetime.utcfromtimestamp(0) + delta

def create_shift_in_millis(delta):
    return datetime_to_milliseconds(create_shift(delta))

def shift_datetime_in_millis(datetime, delta):
    return datetime_to_milliseconds(datetime + delta)

def get_time_range_of_day(datetime_inst):
    start_day = datetime.datetime(datetime_inst.year, datetime_inst.month, datetime_inst.day)
    end_day = start_day + datetime.timedelta(days=1)
    return (start_day, end_day)

def today():
    return datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

def now():
    return datetime.datetime.now()