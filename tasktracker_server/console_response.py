import datetime


def show_tasks_in_console(tasks):
    data = [[str(task.tid), str(task.parent_tid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time)] for task in tasks]
    data.insert(0, ['TID', 'PARENT', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE'])
    print_in_groups(data)

def show_full_tasks_in_console(tasks):
    data = [[str(task.tid), str(task.uid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time)] for task in tasks]
    data.insert(0, ['TID', 'UID', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE'])
    print_in_groups(data)

def show_users_in_console(users):
    data = [[str(user.uid), user.login, user.online] for user in users]
    data.insert(0, ['UID', 'LOGIN', 'ONLINE'])
    print_in_groups(data)

def show_common_ok(message=None):
    if message is None:
        print('OK')
    else:
        print('OK. {}'.format(message))

def show_common_error(message=None):
    if message is None:
        print('Error')
    else:
        print('Error. {}'.format(message))

def show_welcome(login):
    print('Welcome, {}'.format(login))

def show_good_bye(login):
    print('Good Bye, {}'.format(login))

def show_already_login(login):
    print('You are already login as {}. Please, logout'.format(login))

def show_noone_login():
    print('You are not login yet')

def show_invalid_time_range_error(start, end):
    start_timestamp = timestamp_to_display(start)
    end_timestamp = timestamp_to_display(end)
    message = 'Invalid time range: [{}, {}]'.format(start_timestamp, end_timestamp)
    show_common_error(message)

def show_invalid_parent_id_error(parent_tid):
    show_common_error('Invalid parent id: {}'.format(parent_tid))

def timestamp_to_display(timestamp):
    if timestamp is not None:
        return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y')

def print_in_grid(data):
    max_width = []
    count = len(data[0])
    for i in range(count):
        max = 0
        for d in data:
            if d[i] is None:
                d[i] = 'None'
            if len(d[i]) > max:
                max = len(d[i])
        max_width.append(max + 2)
    ri = 0
    for row in data:
        for i in range(count):
            if row[i] is None:
                row[i] = 'None'
            print(row[i].ljust(max_width[i]), '| ', end='')
        print('')
        if ri == 0: 
            print('')
        ri += 1

def print_in_groups(data):
    max = 0
    for h in data[0]:
        if len(h) > max:
            max = len(h)
    max += 2
    for d in data[1:]:
        for i in range(len(data[0])):
            print(data[0][i].ljust(max), '| ', d[i])
        print('')