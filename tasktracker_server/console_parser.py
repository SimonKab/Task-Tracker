from .requests.controllers import TaskController, UserController
from .requests.controllers import InvalidTimeError, InvalidParentId
from .requests.controllers import UserAlreadyExistsError, UserNotExistsError
from tasktracker_server import console_response
import argparse
import datetime
import re

class Parser:
    PREFIX = '--'

    ACTION = 'action'
    SHOW = 'show'
    ADD = 'add'
    DELETE = 'delete'
    EDIT = 'edit'

    TASK = 'task'
    TASK_TID = 'tid'
    TASK_TITLE = 'title'
    TASK_DESCRIPTION = 'descr'
    TASK_START_TIME = 'start'
    TASK_END_TIME = 'end'
    TASK_DEADLINE = 'deadline'
    TASK_PARENT_ID = 'parent'
    TASK_DELETE = 'delete'

    OVERALL_TASK = 'overall_task'

    USER = 'user'
    USER_UID = 'uid'
    USER_LOGIN = 'login'
    USER_ONLINE = 'online'
    USER_OFFLINE = 'offline'
    USER_DELETE = 'delete'

    LOGIN = 'login'
    LOGOUT = 'logout'

    _with_prefix = None

    @staticmethod
    def prefix():
        if Parser._with_prefix is None:
            Parser._with_prefix = Parser()
            for attr in dir(Parser):
                if str(attr).isupper():
                    value = getattr(Parser, attr)
                    setattr(Parser._with_prefix, attr, Parser.PREFIX + value)
            
        return Parser._with_prefix

def parse():
    parser = argparse.ArgumentParser(prefix_chars=Parser.PREFIX, 
        description="Hello) It's task tracker")
    root_subparsers = parser.add_subparsers(dest=Parser.ACTION)
    
    init_task_parser(root_subparsers)
    init_overall_task_parser(root_subparsers)
    init_user_parser(root_subparsers)
    init_login_parser(root_subparsers)
    init_logout_parser(root_subparsers)

    parsed = parser.parse_args()
    check_is_parsed_valid(parsed)

    proccess_parsed(parsed)

def check_is_parsed_valid(parsed):
    check_is_delete_list_valid(parsed)
    check_is_online_offline_together(parsed)

def check_is_delete_list_valid(parsed):
    delete = getattr(parsed, Parser.TASK_DELETE, None)
    if delete is None:
        return
    for delete_arg in delete:
        if getattr(parsed, delete_arg, None) is not None:
            msg = "{0} is not valid arg".format(delete_arg)
            raise argparse.ArgumentTypeError(msg)

def check_is_online_offline_together(parsed):
    online = getattr(parsed, Parser.USER_ONLINE, None)
    offline = getattr(parsed, Parser.USER_OFFLINE, None)
    if online and offline:
        msg = 'Online and offline modes were specified together'
        raise argparse.ArgumentTypeError(msg)

def delete_arg(arg):
    valid_delete_arg_list = [Parser.TASK_TITLE, Parser.TASK_DESCRIPTION,
                            Parser.TASK_START_TIME, Parser.TASK_END_TIME,
                            Parser.TASK_DEADLINE, Parser.TASK_PARENT_ID,
                            Parser.USER_LOGIN]
    if not arg in valid_delete_arg_list:
        raise argparse.ArgumentTypeError("{0} is not valid arg".format(arg))

    return arg

def time_arg(arg):
    try:
        simple_date = re.match('[0-9]+-[0-9]+-[0-9]+', arg)
        if simple_date is not None:
            return datetime.datetime.strptime(arg, "%d-%m-%Y")

        relative_date = re.match('today(([+-])([0-9]+))?$', arg)
        if relative_date is not None:
            sign = relative_date.group(2)
            shift = relative_date.group(3)
            today = datetime.datetime.today()
            if sign == '+':
                return today + datetime.timedelta(days=int(shift))
            elif sign == '-':
                return today - datetime.timedelta(days=int(shift))
            else:
                return today
        else:
            raise ValueError
        
    except ValueError:
        msg = ('Not a valid date: {0}. Please, write date in format like '
                '[Day]-[Month]-[Year] or today[+-][shift]').format(arg)
        raise argparse.ArgumentTypeError(msg)

def init_task_parser(root):
    task_parser = root.add_parser(Parser.TASK)
    task_root_subparser = task_parser.add_subparsers(dest=Parser.TASK)

    add_task_parser = task_root_subparser.add_parser(Parser.ADD)
    add_task_parser.add_argument(Parser.prefix().TASK_TID, 
        type=int)
    add_task_parser.add_argument(Parser.prefix().TASK_TITLE, 
        type=str, required=True)
    add_task_parser.add_argument(Parser.prefix().TASK_DESCRIPTION, 
        type=str)
    add_task_parser.add_argument(Parser.prefix().TASK_START_TIME, 
        type=time_arg)
    add_task_parser.add_argument(Parser.prefix().TASK_END_TIME, 
        type=time_arg)
    add_task_parser.add_argument(Parser.prefix().TASK_DEADLINE, 
        type=time_arg)
    add_task_parser.add_argument(Parser.prefix().TASK_PARENT_ID,
        type=int)

    show_task_parser = task_root_subparser.add_parser(Parser.SHOW)
    show_task_parser.add_argument(Parser.prefix().TASK_TID, 
        type=int)
    show_task_parser.add_argument(Parser.prefix().TASK_TITLE, 
        type=str)
    show_task_parser.add_argument(Parser.prefix().TASK_DESCRIPTION, 
        type=str)
    show_task_parser.add_argument(Parser.prefix().TASK_START_TIME, 
        type=time_arg)
    show_task_parser.add_argument(Parser.prefix().TASK_END_TIME, 
        type=time_arg)
    show_task_parser.add_argument(Parser.prefix().TASK_DEADLINE, 
        type=time_arg)
    show_task_parser.add_argument(Parser.prefix().TASK_PARENT_ID,
        type=int)

    delete_task_parser = task_root_subparser.add_parser(Parser.DELETE)
    delete_task_parser.add_argument(Parser.prefix().TASK_TID, 
        type=int, required=True)

    edit_task_parser = task_root_subparser.add_parser(Parser.EDIT)
    edit_task_parser.add_argument(Parser.prefix().TASK_TID, 
        type=int, required=True)
    edit_task_parser.add_argument(Parser.prefix().TASK_TITLE, 
        type=str)
    edit_task_parser.add_argument(Parser.prefix().TASK_DESCRIPTION, 
        type=str)
    edit_task_parser.add_argument(Parser.prefix().TASK_START_TIME, 
        type=time_arg)
    edit_task_parser.add_argument(Parser.prefix().TASK_END_TIME, 
        type=time_arg)
    edit_task_parser.add_argument(Parser.prefix().TASK_DEADLINE, 
        type=time_arg)
    edit_task_parser.add_argument(Parser.prefix().TASK_PARENT_ID,
        type=int)
    edit_task_parser.add_argument(Parser.prefix().DELETE, 
        type=delete_arg, nargs='+')

def init_overall_task_parser(root):
    overall_task_parser = root.add_parser(Parser.OVERALL_TASK)
    overall_task_parser.add_argument(Parser.OVERALL_TASK, action='store_true')

def init_user_parser(root):
    user_parser = root.add_parser(Parser.USER)
    user_root_subparser = user_parser.add_subparsers(dest=Parser.USER)

    add_user_parser = user_root_subparser.add_parser(Parser.ADD)
    add_user_parser.add_argument(Parser.prefix().USER_UID,
        type=int)
    add_user_parser.add_argument(Parser.prefix().USER_LOGIN,
        type=str, required=True)

    show_user_parser = user_root_subparser.add_parser(Parser.SHOW)
    show_user_parser.add_argument(Parser.prefix().USER_UID,
        type=int)
    show_user_parser.add_argument(Parser.prefix().USER_LOGIN,
        type=str)
    show_user_parser.add_argument(Parser.prefix().USER_ONLINE,
        action='store_true')
    show_user_parser.add_argument(Parser.prefix().USER_OFFLINE,
        action='store_true')

    delete_user_parser = user_root_subparser.add_parser(Parser.DELETE)
    delete_user_parser.add_argument(Parser.prefix().USER_UID)

    edit_user_parser = user_root_subparser.add_parser(Parser.EDIT)
    edit_user_parser.add_argument(Parser.prefix().USER_UID,
        type=int)
    edit_user_parser.add_argument(Parser.prefix().USER_LOGIN,
        type=str)
    edit_user_parser.add_argument(Parser.prefix().DELETE, 
        type=delete_arg, nargs='+')

def init_login_parser(root):
    login_parser = root.add_parser(Parser.LOGIN)
    login_parser.add_argument(Parser.LOGIN, type=str)

def init_logout_parser(root):
    logout_parser = root.add_parser(Parser.LOGOUT)
    logout_parser.add_argument(Parser.LOGOUT, action='store_true')

def proccess_parsed(parsed):
    if parsed.action == Parser.TASK:
        proccess_task(parsed)
    if parsed.action == Parser.USER:
        proccess_user(parsed)
    if parsed.action == Parser.LOGIN:
        proccess_login(parsed)
    if parsed.action == Parser.LOGOUT:
        proccess_logout(parsed)
    if parsed.action == Parser.OVERALL_TASK:
        proccess_overall_task(parsed)

def proccess_task(parsed):
    if parsed.task == Parser.ADD:
        proccess_task_add(parsed)
    if parsed.task == Parser.SHOW:
        proccess_task_show(parsed)
    if parsed.task == Parser.DELETE:
        proccess_task_delete(parsed)
    if parsed.task == Parser.EDIT:
        proccess_task_edit(parsed)
    if parsed.task is None:
        proccess_task_show(parsed)

def proccess_task_add(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    if tid is not None: tid = int(int)
    title = getattr(parsed, Parser.TASK_TITLE, None)
    description = getattr(parsed, Parser.TASK_DESCRIPTION, None)
    start_time = getattr(parsed, Parser.TASK_START_TIME, None)
    end_time = getattr(parsed, Parser.TASK_END_TIME, None)
    deadline_time = getattr(parsed, Parser.TASK_DEADLINE, None)
    parent = getattr(parsed, Parser.TASK_PARENT_ID, None)

    start_time_millis = datetime_to_milliseconds(start_time)
    end_time_millis = datetime_to_milliseconds(end_time)
    deadline_time_millis = datetime_to_milliseconds(deadline_time)

    try:
        users = UserController.fetch_user(online=True)
        if len(users) == 0:
            console_response.show_noone_login()
            return
        
        success = TaskController.save_task(users[0].uid, parent, title, description,
            start_time_millis, end_time_millis, deadline_time_millis, tid)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('Task was not added')
    except InvalidTimeError as error:
        console_response.show_invalid_time_range_error(error.start, error.end)
    except InvalidParentId as error:
        console_response.show_invalid_parent_id_error(error.parent_tid)

def proccess_task_show(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    title = getattr(parsed, Parser.TASK_TITLE, None)
    descr = getattr(parsed, Parser.TASK_DESCRIPTION, None)
    parent = getattr(parsed, Parser.TASK_PARENT_ID, None)

    users = UserController.fetch_user(online=True)
    if len(users) == 0:
        console_response.show_noone_login()
        return

    tasks = TaskController.fetch_tasks(uid=users[0].uid, parent_tid=parent,
                                     tid=tid, title=title, description=descr)
    if tasks is not None:
        console_response.show_tasks_in_console(tasks)
    else:
        console_response.show_common_error()

def proccess_task_delete(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)

    success = TaskController.remove_task(tid)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Task was not deleted')

def proccess_task_edit(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    if tid is None:
        raise ValueError('tid is None in task edit')
    
    title = getattr(parsed, Parser.TASK_TITLE, None)
    description = getattr(parsed, Parser.TASK_DESCRIPTION, None)
    start_time = getattr(parsed, Parser.TASK_START_TIME, None)
    end_time = getattr(parsed, Parser.TASK_END_TIME, None)
    deadline_time = getattr(parsed, Parser.TASK_DEADLINE, None)
    delete = getattr(parsed, Parser.DELETE, None)
    parent = getattr(parsed, Parser.TASK_PARENT_ID, None)

    args = {}
    if title is not None:
        args['title'] = title
    if description is not None:
        args['description'] = description
    if start_time is not None:
        args['supposed_start_time'] = datetime_to_milliseconds(start_time)
    if end_time is not None:
        args['supposed_end_time'] = datetime_to_milliseconds(end_time)
    if deadline_time is not None:
        args['deadline_time'] = datetime_to_milliseconds(deadline_time)
    if parent is not None:
        args['parent_tid'] = parent

    if delete is not None:
        for to_delete in delete:
            if to_delete == Parser.TASK_TITLE:
                args['title'] = None
            if to_delete == Parser.TASK_DESCRIPTION:
                args['description'] = None
            if to_delete == Parser.TASK_START_TIME:
                args['supposed_start_time'] = None
            if to_delete == Parser.TASK_END_TIME:
                args['supposed_end_time'] = None
            if to_delete == Parser.TASK_DEADLINE:
                args['deadline_time'] = None
            if to_delete == Parser.TASK_PARENT_ID:
                args['parent_tid'] = None

    try:
        success = TaskController.edit_task(int(tid), **args)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('Task was not edited')
    except InvalidTimeError as error:
        console_response.show_invalid_time_range_error(error.start, error.end)
    except InvalidParentId as error:
        console_response.show_invalid_parent_id_error(error.parent_tid)

def proccess_overall_task(parsed):
    tasks = TaskController.fetch_tasks()
    if tasks is not None:
        console_response.show_full_tasks_in_console(tasks)
    else:
        console_response.show_common_error()

def proccess_user(parsed):
    if parsed.user == Parser.ADD:
        proccess_user_add(parsed)
    if parsed.user == Parser.SHOW:
        proccess_user_show(parsed)
    if parsed.user == Parser.DELETE:
        proccess_user_delete(parsed)
    if parsed.user == Parser.EDIT:
        proccess_user_edit(parsed)
    if parsed.user is None:
        proccess_user_show(parsed)

def proccess_user_add(parsed):
    uid = getattr(parsed, Parser.USER_UID, None)
    if uid is not None: uid = int(uid)
    login = getattr(parsed, Parser.USER_LOGIN, None)

    try:
        success = UserController.save_user(login, uid)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('User was not added')
    except UserAlreadyExistsError as error:
        print(error)

def proccess_user_show(parsed):
    uid = getattr(parsed, Parser.USER_UID, None)
    login = getattr(parsed, Parser.USER_LOGIN, None)
    online = getattr(parsed, Parser.USER_ONLINE, None)
    offline = getattr(parsed, Parser.USER_OFFLINE, None)

    online_filter = None
    if online:
        online_filter = True
    if offline:
        online_filter = False

    users = UserController.fetch_user(uid, login, online_filter)
    if users is not None:
        console_response.show_users_in_console(users)
    else:
        console_response.show_common_error()

def proccess_user_delete(parsed):
    uid = getattr(parsed, Parser.USER_UID, None)
    if uid is not None: uid = int(uid)
    
    success = UserController.delete_user(uid)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('User was not deleted')

def proccess_user_edit(parsed):
    uid = getattr(parsed, Parser.USER_UID, None)
    if uid is not None: uid = int(uid)
    login = getattr(parsed, Parser.USER_LOGIN, None)
    delete = getattr(parsed, Parser.DELETE, None)

    args = {}
    if login is not None:
        args['login'] = login

    if delete is not None:
        if Parser.USER_LOGIN in delete:
            args['login'] = None

    try:
        success = UserController.edit_user(uid, **args)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('User was not edited')
    except UserNotExistsError as error:
        print(error)

def proccess_login(parsed):
    login = getattr(parsed, Parser.LOGIN, None)
    try:
        users_online = UserController.fetch_user(online=True)
        if len(users_online) != 0:
            console_response.show_already_login(users_online[0].login)
            return

        success = UserController.login_user(login)
        if success:
            console_response.show_welcome(login)
        else:
            console_response.show_common_error()
    except UserNotExistsError as error:
        print(error)

def proccess_logout(parsed):
    try:
        users_online = UserController.fetch_user(online=True)
        if len(users_online) == 0:
            console_response.show_noone_login()
            return

        login = users_online[0].login
        success = UserController.logout_user(login)
        if success:
            console_response.show_good_bye(login)
        else:
            console_response.show_common_error()
    except UserNotExistsError as error:
        print(error)

def datetime_to_milliseconds(datetime_inst):
    if datetime_inst is None:
        return None
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (datetime_inst - epoch).total_seconds() * 1000.0
