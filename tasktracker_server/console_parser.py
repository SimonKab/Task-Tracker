from . import console_response
from .requests.controllers import TaskController, UserController
from .requests.controllers import InvalidTimeError, InvalidParentId
from .requests.controllers import UserAlreadyExistsError, UserNotExistsError
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
    TASK_PRIORITY = 'priority'
    TASK_STATUS = 'status'
    TASK_NOTIFICATE_START = 'notificate_start'
    TASK_NOTIFICATE_END = 'notificate_end'
    TASK_NOTIFICATE_DEADLINE = 'not_notificate_deadline'
    TASK_NOT_NOTIFICATE_START = 'not_notificate_start'
    TASK_NOT_NOTIFICATE_END = 'not_notificate_end'
    TASK_NOT_NOTIFICATE_DEADLINE = 'notificate_deadline'
    TASK_TIME = 'time'
    TASK_DELETE = 'delete'

    PLAN = 'plan'
    PLAN_ID = 'plan_id'
    PLAN_TID = 'tid'
    PLAN_START = 'start'
    PLAN_END = 'end'
    PLAN_SHIFT = 'shift'
    PLAN_EXCLUDE = 'exclude'

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
        value = getattr(parsed, delete_arg, None)
        if value is not None and value is not False:
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
                            Parser.USER_LOGIN, Parser.TASK_PRIORITY,
                            Parser.TASK_STATUS, Parser.TASK_NOTIFICATE_START,
                            Parser.TASK_NOTIFICATE_END, Parser.TASK_NOTIFICATE_DEADLINE,
                            Parser.PLAN_START, Parser.PLAN_END,
                            Parser.PLAN_EXCLUDE]
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

def time_shift_arg(arg):
    try:
        shift = re.match('(([0-9])*d)?(([0-9])*m)?(([0-9])*y)?', arg)
        if shift is not None:
            days = shift.group(2)
            months = shift.group(4)
            years = shift.group(6)
            if days is None: days = 0
            if months is None: months = 0
            if years is None: years = 0
            epoch = datetime.datetime.utcfromtimestamp(0)
            return epoch + datetime.timedelta(int(days)) + datetime.timedelta(int(months)) + datetime.timedelta(int(years))
        else:
            raise ValueError

    except ValueError:
        msg = ('Not a valid shift: {}. Please, write shift in formal like '
                '[Days]d[Months]m[Years]y').format(arg)
        raise argparse.ArgumentTypeError(msg)

def nargs_range_action(min, max):
    class RangeNargsAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if not min <= len(values) <= max:
                message='argument "{}" requires between {} and {} arguments'.format(
                    self.dest, min, max)
                raise argparse.ArgumentTypeError(message)
            setattr(namespace, self.dest, values)
    return RangeNargsAction

def init_task_parser(root):
    task_parser = root.add_parser(Parser.TASK)
    task_root_subparser = task_parser.add_subparsers(dest=Parser.TASK)

    init_plan_parser(task_root_subparser)

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
    add_task_parser.add_argument(Parser.prefix().TASK_PRIORITY,
        choices=['low', 'normal', 'high', 'highest'])
    add_task_parser.add_argument(Parser.prefix().TASK_STATUS,
        choices=['pending', 'active', 'completed', 'overdue'])
    add_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_START,
        action='store_true')
    add_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_END,
        action='store_true')
    add_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_DEADLINE,
        action='store_true')

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
    show_task_parser.add_argument(Parser.prefix().TASK_PRIORITY,
        choices=['low', 'normal', 'high', 'highest'])
    show_task_parser.add_argument(Parser.prefix().TASK_STATUS,
        choices=['pending', 'active', 'completed', 'overdue'])
    show_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_START,
        action='store_true')
    show_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_END,
        action='store_true')
    show_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_DEADLINE,
        action='store_true')
    show_task_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_START,
        action='store_true')
    show_task_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_END,
        action='store_true')
    show_task_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_DEADLINE,
        action='store_true')
    show_task_parser.add_argument(Parser.prefix().TASK_TIME,
        type=time_arg, nargs='+', action=nargs_range_action(1, 2))

    # TODO: Is it need?
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
    edit_task_parser.add_argument(Parser.prefix().TASK_PRIORITY,
        choices=['low', 'normal', 'high', 'highest'])
    edit_task_parser.add_argument(Parser.prefix().TASK_STATUS,
        choices=['pending', 'active', 'completed', 'overdue'])
    edit_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_START,
        action='store_true')
    edit_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_END,
        action='store_true')
    edit_task_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_DEADLINE,
        action='store_true')
    edit_task_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_START,
        action='store_true')
    edit_task_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_END,
        action='store_true')
    edit_task_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_DEADLINE,
        action='store_true')
    edit_task_parser.add_argument(Parser.prefix().DELETE, 
        type=delete_arg, nargs='+')

def init_plan_parser(root):
    plan_parser = root.add_parser(Parser.PLAN)
    plan_root_subparser = plan_parser.add_subparsers(dest=Parser.PLAN)

    add_plan_parser = plan_root_subparser.add_parser(Parser.ADD)
    add_plan_parser.add_argument(Parser.prefix().PLAN_TID, 
        type=int, required=True)
    add_plan_parser.add_argument(Parser.prefix().PLAN_START, 
        type=time_arg)
    add_plan_parser.add_argument(Parser.prefix().PLAN_END, 
        type=time_arg)
    add_plan_parser.add_argument(Parser.prefix().PLAN_SHIFT, 
        type=time_shift_arg, required=True)
    add_plan_parser.add_argument(Parser.prefix().PLAN_EXCLUDE, 
        type=time_arg, nargs='+')

    delete_plan_parser = plan_root_subparser.add_parser(Parser.DELETE)
    delete_plan_parser.add_argument(Parser.prefix().PLAN_ID, 
        type=int, required=True)

    edit_plan_parser = plan_root_subparser.add_parser(Parser.EDIT)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_ID,
        type=int, required=True)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_TID,
        type=int)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_START, 
        type=str)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_END, 
        type=str)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_SHIFT, 
        type=time_shift_arg)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_EXCLUDE, 
        type=time_arg, nargs='+')
    edit_plan_parser.add_argument(Parser.prefix().DELETE, 
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
    if parsed.task == Parser.PLAN:
        proccess_plan(parsed)
    if parsed.task is None:
        proccess_task_show(parsed)

def proccess_plan(parsed):
    if parsed.plan == Parser.ADD:
        proccess_plan_add(parsed)
    if parsed.plan == Parser.DELETE:
        proccess_plan_remove(parsed)
    if parsed.plan == Parser.EDIT:
        proccess_plan_edit(parsed)

def proccess_task_add(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    if tid is not None: tid = int(int)
    title = getattr(parsed, Parser.TASK_TITLE, None)
    description = getattr(parsed, Parser.TASK_DESCRIPTION, None)
    start_time = getattr(parsed, Parser.TASK_START_TIME, None)
    end_time = getattr(parsed, Parser.TASK_END_TIME, None)
    deadline_time = getattr(parsed, Parser.TASK_DEADLINE, None)
    parent = getattr(parsed, Parser.TASK_PARENT_ID, None)
    priority = getattr(parsed, Parser.TASK_PRIORITY, None)
    status = getattr(parsed, Parser.TASK_STATUS, None)
    notificate_start = getattr(parsed, Parser.TASK_NOTIFICATE_START, None)
    notificate_end = getattr(parsed, Parser.TASK_NOTIFICATE_END, None)
    notificate_deadline = getattr(parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)

    start_time_millis = datetime_to_milliseconds(start_time)
    end_time_millis = datetime_to_milliseconds(end_time)
    deadline_time_millis = datetime_to_milliseconds(deadline_time)

    try:
        users = UserController.fetch_user(online=True)
        if len(users) == 0:
            console_response.show_noone_login()
            return
        
        success = TaskController.save_task(users[0].uid, parent, title, description,
            start_time_millis, end_time_millis, deadline_time_millis, priority,
            status, notificate_start, notificate_end, notificate_deadline, tid)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('Task was not added')
    except InvalidTimeError as error:
        console_response.show_invalid_time_range_error(error.start, error.end)
    except InvalidParentId as error:
        console_response.show_invalid_parent_id_error(error.parent_tid)

def proccess_plan_add(parsed):
    tid = getattr(parsed, Parser.PLAN_TID, None)
    start = getattr(parsed, Parser.PLAN_START, None)
    end = getattr(parsed, Parser.PLAN_END, None)
    shift = getattr(parsed, Parser.PLAN_SHIFT, None)
    exclude = getattr(parsed, Parser.PLAN_EXCLUDE, None)

    if exclude is not None:
        exclude = [datetime_to_milliseconds(exclude_time) for exclude_time in exclude]

    success = TaskController.add_plan(tid, datetime_to_milliseconds(start), 
                                    datetime_to_milliseconds(end), 
                                    datetime_to_milliseconds(shift), exclude)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Plan was not added')

def proccess_plan_remove(parsed):
    plan_id = getattr(parsed, Parser.PLAN_ID, None)

    success = TaskController.remove_plan(tid, plan_id)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Plan was not deleted')

def proccess_plan_edit(parsed):
    plan_id = getattr(parsed, Parser.PLAN_ID, None)
    tid = getattr(parsed, Parser.PLAN_TID, None)
    start = getattr(parsed, Parser.PLAN_START, None)
    end = getattr(parsed, Parser.PLAN_END, None)
    shift = getattr(parsed, Parser.PLAN_SHIFT, None)
    exclude = getattr(parsed, Parser.PLAN_EXCLUDE, None)
    delete = getattr(parsed, Parser.DELETE, None)

    if exclude is not None:
        exclude = [datetime_to_milliseconds(exclude_time) for exclude_time in exclude]

    args = {}
    if tid is not None:
        args['tid'] = tid
    if start is not None:
        args['start'] = datetime_to_milliseconds(start)
    if end is not None:
        args['end'] = datetime_to_milliseconds(end)
    if shift is not None:
        args['shift'] = datetime_to_milliseconds(shift)
    if exclude is not None:
        args['exclude'] = exclude

    if delete is not None:
        for to_delete in delete:
            if to_delete == Parser.PLAN_START:
                args['start'] = None
            if to_delete == Parser.PLAN_END:
                args['end'] = None
            if to_delete == Parser.PLAN_EXCLUDE:
                args['exclude'] = None
 

    success = TaskController.edit_plan(plan_id, **args)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Plan was not edited')

def proccess_task_show(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    title = getattr(parsed, Parser.TASK_TITLE, None)
    descr = getattr(parsed, Parser.TASK_DESCRIPTION, None)
    parent = getattr(parsed, Parser.TASK_PARENT_ID, None)
    priority = getattr(parsed, Parser.TASK_PRIORITY, None)
    status = getattr(parsed, Parser.TASK_STATUS, None)
    notificate_start_parser = getattr(parsed, Parser.TASK_NOTIFICATE_START, None)
    notificate_end_parser = getattr(parsed, Parser.TASK_NOTIFICATE_END, None)
    notificate_deadline_parser = getattr(parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)
    not_notificate_start_parser = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_START, None)
    not_notificate_end_parser = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_END, None)
    not_notificate_deadline_parser = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_DEADLINE, None)
    time_to_show = getattr(parsed, Parser.TASK_TIME, None)

    # FUCK

    notificate_supposed_start =  None
    if notificate_start_parser:
        notificate_supposed_start = True
    if not_notificate_start_parser:
        notificate_supposed_start = False
    notificate_supposed_end =  None
    if notificate_end_parser:
        notificate_supposed_end = True
    if not_notificate_end_parser:
        notificate_supposed_end = False
    notificate_deadline =  None
    if notificate_deadline_parser:
        notificate_deadline = True
    if not_notificate_deadline_parser:
        notificate_deadline = False

    users = UserController.fetch_user(online=True)
    if len(users) == 0:
        console_response.show_noone_login()
        return

    time_range = None
    if time_to_show is not None:
        if len(time_to_show) == 1:
        # TEST 
            # time_to_show.append(datetime.datetime(time_to_show[0].year, time_to_show[0].month, 
            #                                 time_to_show[0].day + 1, time_to_show[0].hour,
            #                                 time_to_show[0].minute, time_to_show[0].second))
            time_to_show.append(time_to_show[0] + datetime.timedelta(days=1))
        time_range = (datetime_to_milliseconds(time_to_show[0]), 
                        datetime_to_milliseconds(time_to_show[1]))

    tasks = TaskController.fetch_tasks(uid=users[0].uid, parent_tid=parent,
                                     tid=tid, title=title, description=descr,
                                     priority=priority, status=status,
                                     notificate_supposed_start=notificate_supposed_start,
                                     notificate_supposed_end=notificate_supposed_end,
                                     notificate_deadline=notificate_deadline,
                                     time_range=time_range)
    if tasks is not None:
        console_response.show_tasks_like_tree_in_console(tasks)
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
    priority = getattr(parsed, Parser.TASK_PRIORITY, None)
    status = getattr(parsed, Parser.TASK_STATUS, None)
    notificate_start = getattr(parsed, Parser.TASK_NOTIFICATE_START, None)
    notificate_end = getattr(parsed, Parser.TASK_NOTIFICATE_END, None)
    notificate_deadline = getattr(parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)
    not_notificate_start = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_START, None)
    not_notificate_end = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_END, None)
    not_notificate_deadline = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_DEADLINE, None)

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
    if priority is not None:
        args['priority'] = priority
    if status is not None:
        args['status'] = status
    if notificate_start is True:
        args['notificate_supposed_start'] = notificate_start
    if notificate_end is True:
        args['notificate_supposed_end'] = notificate_end
    if notificate_deadline is True:
        args['notificate_deadline'] = notificate_deadline
    if not_notificate_start is True:
        args['notificate_supposed_start'] = not_notificate_start
    if not_notificate_end is True:
        args['notificate_supposed_end'] = not_notificate_end
    if not_notificate_deadline is True:
        args['notificate_deadline'] = not_notificate_deadline

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
            if to_delete == Parser.TASK_PRIORITY:
                args['priority'] = None
            if to_delete == Parser.TASK_STATUS:
                args['status'] = None
            if to_delete == Parser.TASK_NOTIFICATE_START:
                args['notificate_supposed_start'] = False
            if to_delete == Parser.TASK_NOTIFICATE_END:
                args['notificate_supposed_end'] = False
            if to_delete == Parser.TASK_NOTIFICATE_DEADLINE:
                args['notificate_deadline'] = False

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
