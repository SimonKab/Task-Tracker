import datetime

from tasktracker_project.tasktracker_core.model.task import Task, Priority, Status
from tasktracker_project.tasktracker_core.model.project import Project
from tasktracker_project.tasktracker_core.model.user import User
from tasktracker_project.tasktracker_core.requests.controllers import TaskController
from tasktracker_project.tasktracker_core.requests.controllers import PlanController
from tasktracker_project.tasktracker_core.requests.controllers import ProjectController
from tasktracker_project.tasktracker_core.requests.controllers import UserController

def show_tasks_in_console(tasks, shift=0):
    data = [[str(task.tid), str(task.pid), str(task.parent_tid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time),
            Priority.to_str(task.priority),
            Status.to_str(task.status),
            task.notificate_supposed_start,
            task.notificate_supposed_end,
            task.notificate_deadline] for task in tasks]
    data.insert(0, ['TID', 'PID', 'PARENT', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE',
                    'PRIORITY', 'STATUS', 'NOTIFICATE START', 'NOTIFICATE END', 'NOTIFICATE DEADLINE', 
                    'PLANNED (plan id)', 'EDIT PLANS (plan id)', 'NUMBER IN PLANS'])
    
    for i in range(len(tasks)):
        task = tasks[i]
        projects = ProjectController.fetch_projects(pid=task.pid)
        if projects is not None and len(projects) != 0:
            projects_str = ','.join([project.name for project in projects])
            data[i+1][1] += ' ({})'.format(projects_str)

    plan_controller = PlanController()
    for i in range(len(tasks)):
        task = tasks[i]
        plans = plan_controller.get_plan_for_common_task(task.tid)
        if len(plans) > 0:
            plans_ids = ','.join([str(plan.plan_id) for plan in plans])
            data[i+1].append(plans_ids)
        else:
            data[i+1].append(str(None))
        edited_plans = plan_controller.get_plan_for_edit_repeat_task(task.tid)
        if len(edited_plans) > 0:
            plans_ids = ','.join([str(plan.plan_id) for plan in edited_plans])
            data[i+1].append(plans_ids)
        else:
            data[i+1].append(str(None))

        all_plans = plans + edited_plans
        if len(all_plans) > 0:
            repeats = []
            for plan in all_plans:
                repeat = plan_controller.get_repeat_number_for_task(plan.plan_id, task)
                if repeat is not None:
                    repeats.append(str(repeat))
            numbers = ','.join(repeats)
            data[i+1].append(numbers)
        else:
            data[i+1].append(str(None))
        
    print_in_groups(data, shift)

def show_notifications_in_console(tasks):
    print('///////////////////////////////////////////')
    print('\t\tNOTIFICATIONS')
    print('///////////////////////////////////////////')
    print('')

    data = [[str(task.tid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time)] for task in tasks]
    data.insert(0, ['TID', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE', 'NUMBER IN PLANS'])

    plan_controller = PlanController()
    for i in range(len(tasks)):
        task = tasks[i]

        plans = plan_controller.get_plan_for_common_task(task.tid)
        edited_plans = plan_controller.get_plan_for_edit_repeat_task(task.tid)

        all_plans = plans + edited_plans
        if len(all_plans) > 0:
            repeats = []
            for plan in all_plans:
                repeat = plan_controller.get_repeat_number_for_task(plan.plan_id, task)
                if repeat is not None:
                    repeats.append(str(repeat))
            numbers = ','.join(repeats)
            data[i+1].append(numbers)
        else:
            data[i+1].append(str(None))

    print_in_groups(data, 0)

def show_projects(projects):
    data = [[str(project.pid), project.name, project] for project in projects]
    data.insert(0, ['PID', 'NAME'])
    print_in_groups(data, 0)

def show_projects_for_user(projects, uid):
    data = [[str(project.pid), project.name] for project in projects]
    data.insert(0, ['PID', 'NAME', 'STATUS', 'PARTICIPIANTS'])
    for i in range(len(projects)):
        project = projects[i]
        user_kind = project.get_user_kind(uid)
        if uid == project.creator:
            user_kind_str = 'creator'
        elif user_kind == Project.UserKind.ADMIN:
            user_kind_str = 'admin'
        else:
            user_kind_str = 'guest'
        data[i+1].append(user_kind_str)

        participiants = str()
        participiants += "Admins: "
        admins = [project.creator]
        if project.admins is not None:
            admins.extend(project.admins)
        
        for admin_id in admins:
            users = UserController.fetch_user(uid=admin_id)
            if users is not None and len(users) != 0:
                user = users[0]
                participiants += '{} ({}) '.format(user.uid, user.login)
                
        if project.guests is not None:
            participiants += "Guests: "
            for guest_id in project.guests:
                users = UserController.fetch_user(uid=guest_id)
                if users is not None and len(users) != 0:
                    user = users[0]
                    participiants += '{} ({}) '.format(user.uid, user.login)

        data[i+1].append(participiants)
    print_in_groups(data, 0)

def show_overdue_in_console(tasks):
    print('///////////////////////////////////////////')
    print('\t\tOVERDUE')
    print('///////////////////////////////////////////')
    print('')

    data = [[str(task.tid), task.title, task.description, 
            timestamp_to_display(task.supposed_start_time), 
            timestamp_to_display(task.supposed_end_time),
            timestamp_to_display(task.deadline_time)] for task in tasks]
    data.insert(0, ['TID', 'TITLE', 'DESCRIPTION', 'SUPPOSED_START', 'SUPPOSED_END', 'DEADLINE', 'NUMBER IN PLANS'])

    plan_controller = PlanController()
    for i in range(len(tasks)):
        task = tasks[i]

        plans = plan_controller.get_plan_for_common_task(task.tid)
        edited_plans = plan_controller.get_plan_for_edit_repeat_task(task.tid)

        all_plans = plans + edited_plans
        if len(all_plans) > 0:
            repeats = []
            for plan in all_plans:
                repeat = plan_controller.get_repeat_number_for_task(plan.plan_id, task)
                if repeat is not None:
                    repeats.append(str(repeat))
            numbers = ','.join(repeats)
            data[i+1].append(numbers)
        else:
            data[i+1].append(str(None))

    print_in_groups(data, 0)

def show_plan_in_console(plans):
    data = [[str(plan.plan_id), str(plan.tid), 
            shift_to_display(plan.shift),
            timestamp_to_display(plan.end),
            ','.join(map(str, plan.exclude))] for plan in plans]
    data.insert(0, ['PLAN ID', 'TID', 'SHIFT', 'END', 'EXCLUDE_NUMBERS'])
    print_in_groups(data, 0)

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
        return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y %H:%M')

def shift_to_display(shift):
    if shift is not None:
        return str(datetime.timedelta(milliseconds=shift))

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