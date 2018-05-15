from .model.task import Task, Priority, Status
from .requests.controllers import TaskController
import datetime

def show_tasks_in_console(tasks, shift=0):
    data = [[str(task.tid), str(task.parent_tid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time),
            Priority.to_str(task.priority),
            Status.to_str(task.status),
            task.notificate_supposed_start,
            task.notificate_supposed_end,
            task.notificate_deadline] for task in tasks]
    data.insert(0, ['TID', 'PARENT', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE',
                    'PRIORITY', 'STATUS', 'NOTIFICATE START', 'NOTIFICATE END', 'NOTIFICATE DEADLINE'])
    print_in_groups(data, shift)

def show_full_tasks_in_console(tasks):
    plans = TaskController.fetch_plans(1)
    for p in plans:
        print(p.tid)
    data = [[str(task.tid), str(task.uid), str(task.parent_tid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time),
            Priority.to_str(task.priority),
            Status.to_str(task.status),
            task.notificate_supposed_start,
            task.notificate_supposed_end,
            task.notificate_deadline] for task in tasks]
    for item in data:
        plans = TaskController.fetch_plans(int(item[0]))
        str_representation = str()
        for plan in plans:
            str_plan = 'S: {} E: {} SH: {} EXCL: {}'.format(timestamp_to_display(plan.start), 
                timestamp_to_display(plan.end), timestamp_to_display(plan.shift), plan.exclude)
            str_representation += str_plan + '; '
        item.append(str_representation)

    data.insert(0, ['TID', 'UID', 'PARENT', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE',
                    'PRIORITY', 'STATUS', 'NOTIFICATE START', 'NOTIFICATE END', 'NOTIFICATE DEADLINE', 'PLAN'])
    print_in_groups(data)

def show_tasks_like_tree_in_console(tasks):
    tree = []
    build_tree(tasks, tree)
    for level, task in tree:
        show_tasks_in_console([task], level*5)

def build_tree(tasks, tree, tid=None, level=0):
    for task in tasks:
        if task.parent_tid == tid:
            tree.append((level, task))
            build_tree(tasks, tree, task.tid, level+1)

def show_users_in_console(users):
    data = [[str(user.uid), user.login, user.online] for user in users]
    data.insert(0, ['UID', 'LOGIN', 'ONLINE'])
    print_in_groups(data)

def show_common_ok(message=None):
    if message is None:
        pass
    else:
        print('{}'.format(message))

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

def print_in_grid(data, shift=0):
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
            print(' '*shift, row[i].ljust(max_width[i]), '| ', end='')
        print('')
        if ri == 0: 
            print('')
        ri += 1

def print_in_groups(data, shift=0):
    max = 0
    for h in data[0]:
        if len(h) > max:
            max = len(h)
    max += 2
    for d in data[1:]:
        for i in range(len(data[0])):
            print(' '*shift, data[0][i].ljust(max), '| ', d[i])
        print('')