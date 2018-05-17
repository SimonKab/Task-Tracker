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