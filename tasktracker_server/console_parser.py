from . import console_response
from .requests.controllers import Controller, TaskController, UserController, PlanController, ProjectController
from .requests.controllers import InvalidTimeError, InvalidParentIdError, TaskTrackerError
from .requests.controllers import UserAlreadyExistsError, UserNotExistsError, NotAuthenticatedError
from .requests.controllers import InvalidProjectIdError
from . import utils
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
    TASK_PID = 'pid'
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

    FORCE = 'force'

    PLAN = 'plan'
    PLAN_ID = 'plan_id'
    PLAN_TID = 'tid'
    PLAN_START = 'start'
    PLAN_END = 'end'
    PLAN_SHIFT = 'shift'
    PLAN_EXCLUDE = 'exclude'
    PLAN_REPEATS = 'repeats'

    PROJECT = 'project'
    PROJECT_ID = 'pid'
    PROJECT_CREATOR = 'creator'
    PROJECT_NAME = 'name'
    PROJECT_INVITE = 'invite'
    PROJECT_EXCLUDE = 'exclude'
    PROJECT_KIND_ADMIN = 'admin'
    PROJECT_KIND_GUEST = 'guest'

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

def write_current_login(login):
    with open('login', 'w') as file:
      file.write(login)

def read_current_login():
    try:
        open('login', 'r').close()
    except FileNotFoundError:
        open('login', 'w').close()

    with open('login', 'r') as file:
      login = file.readline()

    return login

def parse():
    login = read_current_login()
    if login is not None and len(login) != 0:
        users = UserController.fetch_user(login=login)
        if users is not None and len(users) != 0:
            Controller.authentication(users[0].uid)

    if Controller.is_authenticated():
        TaskController.find_overdue_tasks(utils.datetime_to_milliseconds(utils.now()))

    parser = argparse.ArgumentParser(prefix_chars=Parser.PREFIX,
                                     description="Hello) It's task tracker")
    
    root_subparsers = parser.add_subparsers(dest=Parser.ACTION)

    init_task_parser(root_subparsers)
    init_overall_task_parser(root_subparsers)
    init_user_parser(root_subparsers)
    init_login_parser(root_subparsers)
    init_project_parser(root_subparsers)

    parsed = parser.parse_args()
    check_is_parsed_valid(parsed)

    try:
        proccess_parsed(parsed)
    except NotAuthenticatedError as error:
        console_response.show_common_error(error)
    except TaskTrackerError as error:
        console_response.show_common_error(error)

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

def get_time_arg(relative_support=True):
  def time_arg(arg):
      try:
          date = utils.parse_date(arg, relative_support)
          time = utils.parse_time(arg, relative_support)

          if date is None and time is None:
              raise ValueError
          else:
              return date if date is not None else time

      except ValueError:
          msg = ('Not a valid date: {0}. Please, write date in format like '
                 '[Day]-[Month]-[Year] or today[+-][shift in days] and '
                 '[Hour]-[Minute] or now[+-][shift in hours]').format(arg)
          raise argparse.ArgumentTypeError(msg)
  return time_arg

def time_shift_arg(arg):
    try:
        shift = re.match('(([0-9]+)d)?(([0-9]+)m)?(([0-9]+)y)?', arg)
        if shift is not None:
            days = shift.group(2)
            months = shift.group(4)
            years = shift.group(6)
            if days is None:
                days = 0
            if months is None:
                months = 0
            if years is None:
                years = 0
            
            epoch = datetime.datetime.utcfromtimestamp(0)

            days_timedelta = datetime.timedelta(days=int(days))
            months_timedelta = datetime.timedelta(days=int(months)*30) 
            years_timedelta = datetime.timedelta(days=int(years)*365)

            return epoch + days_timedelta + months_timedelta + years_timedelta
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
                message = 'argument "{}" requires between {} and {} arguments'.format(
                    self.dest, min, max)
                raise argparse.ArgumentError(None, message)
            setattr(namespace, self.dest, values)
    return RangeNargsAction

def time_collect_action(double=False):
    class RangeNargsAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            left_limit = 1
            right_limit = 2 if not double else 4
            if not left_limit <= len(values) <= right_limit:
                message = 'argument "{}" requires between {} and {} arguments'.format(
                    self.dest, left_limit, right_limit)
                raise argparse.ArgumentError(None, message)

            def combine_pair(value1, value2):
                if type(value1) == type(value2):
                    return None
                date = value1
                time = value2
                if isinstance(date, datetime.time):
                    t = date
                    date = time
                    time = t
                if date is None:
                    date = utils.today()
                if time is None:
                    time = datetime.time()
                return datetime.datetime.combine(date, time)

            if not double:
                if len(values) == 1:
                    values.append(None)
                result = combine_pair(values[0], values[1])
                if result is None:
                    message = ("Incorrect date or time. It's seems you typed "
                        "[date] [date] or [time] [time]")
                    raise argparse.ArgumentError(None, message)
            else:
                if len(values) == 1:
                    if isinstance(values[0], datetime.date):
                        day = values[0]
                        next_day = day + datetime.timedelta(days=1)
                        result = [combine_pair(day, None), 
                                  combine_pair(next_day, None)]
                    else:
                        values.append(None)
                if len(values) == 2:
                    if ((isinstance(values[0], datetime.date)
                        and isinstance(values[1], datetime.date))
                        or (isinstance(values[0], datetime.time)
                        and isinstance(values[1], datetime.time))):
                        values.insert(1, None)
                        values.append(None)
                    else:
                        result = [combine_pair(values[0], values[1])]
                if len(values) == 3:
                    values.append(None)
                if len(values) == 4:
                    result = [combine_pair(values[0], values[1]), 
                      combine_pair(values[2], values[3])]
                if None in result:
                    message = ("Incorrect date or time. It's seems you typed "
                        "[date] [date] or [time] [time]")
                    raise argparse.ArgumentError(None, message)

            setattr(namespace, self.dest, result)
    return RangeNargsAction

def init_task_parser(root):
    task_parser = root.add_parser(Parser.TASK)
    task_root_subparser = task_parser.add_subparsers(dest=Parser.TASK)

    init_plan_parser(task_root_subparser)

    add_task_parser = task_root_subparser.add_parser(Parser.ADD)
    add_task_parser.add_argument(Parser.prefix().TASK_PID,
                                 type=int)
    add_task_parser.add_argument(Parser.prefix().TASK_TITLE,
                                 type=str, required=True)
    add_task_parser.add_argument(Parser.prefix().TASK_DESCRIPTION,
                                 type=str)
    add_task_parser.add_argument(Parser.prefix().TASK_START_TIME,
                                 type=get_time_arg(), 
                                 nargs='+', action=time_collect_action())
    add_task_parser.add_argument(Parser.prefix().TASK_END_TIME,
                                 type=get_time_arg(), 
                                 nargs='+', action=time_collect_action())
    add_task_parser.add_argument(Parser.prefix().TASK_DEADLINE,
                                 type=get_time_arg(), 
                                 nargs='+', action=time_collect_action())
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
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
    show_task_parser.add_argument(Parser.prefix().TASK_END_TIME,
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
    show_task_parser.add_argument(Parser.prefix().TASK_DEADLINE,
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
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
                                  type=get_time_arg(), 
                                  nargs='+', action=time_collect_action(True))

    # TODO: Is it need?
    show_task_parser.add_argument(Parser.prefix().TASK_PARENT_ID,
                                  type=int)

    delete_task_parser = task_root_subparser.add_parser(Parser.DELETE)
    delete_task_parser.add_argument(Parser.prefix().TASK_TID,
                                    type=int, required=True)

    edit_task_parser = task_root_subparser.add_parser(Parser.EDIT)
    edit_task_parser.add_argument(Parser.prefix().TASK_TID,
                                  type=int, required=True)
    edit_task_parser.add_argument(Parser.prefix().TASK_PID,
                                  type=int)
    edit_task_parser.add_argument(Parser.prefix().TASK_TITLE,
                                  type=str)
    edit_task_parser.add_argument(Parser.prefix().TASK_DESCRIPTION,
                                  type=str)
    edit_task_parser.add_argument(Parser.prefix().TASK_START_TIME,
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
    edit_task_parser.add_argument(Parser.prefix().TASK_END_TIME,
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
    edit_task_parser.add_argument(Parser.prefix().TASK_DEADLINE,
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
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
    edit_task_parser.add_argument(Parser.prefix().FORCE, action='store_true')
    edit_task_parser.add_argument(Parser.prefix().DELETE,
                                  type=delete_arg, nargs='+')


def init_plan_parser(root):
    plan_parser = root.add_parser(Parser.PLAN)
    plan_root_subparser = plan_parser.add_subparsers(dest=Parser.PLAN)

    add_plan_parser = plan_root_subparser.add_parser(Parser.ADD)
    add_plan_parser.add_argument(Parser.prefix().PLAN_TID,
                                 type=int, required=True)
    add_plan_parser.add_argument(Parser.prefix().PLAN_END,
                                 type=get_time_arg(),
                                 nargs='+', action=time_collect_action())
    add_plan_parser.add_argument(Parser.prefix().PLAN_SHIFT,
                                 type=time_shift_arg, required=True)
    add_plan_parser.add_argument(Parser.prefix().PLAN_EXCLUDE,
                                 type=get_time_arg(False), nargs='+')

    delete_plan_parser = plan_root_subparser.add_parser(Parser.DELETE)
    delete_plan_parser.add_argument(Parser.prefix().PLAN_ID,
                                    type=int, required=True)

    show_plan_parser = plan_root_subparser.add_parser(Parser.SHOW)
    group = show_plan_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(Parser.prefix().PLAN_ID,
                                    type=int)
    group.add_argument(Parser.prefix().PLAN_TID,
                                    type=int)
    show_plan_parser.add_argument(Parser.prefix().PLAN_REPEATS,
                                  type=int)

    edit_plan_parser = plan_root_subparser.add_parser(Parser.EDIT)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_ID,
                                  type=int, required=True)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_END,
                                  type=get_time_arg(),
                                  nargs='+', action=time_collect_action())
    edit_plan_parser.add_argument(Parser.prefix().PLAN_SHIFT,
                                  type=time_shift_arg)
    edit_plan_parser.add_argument(Parser.prefix().PLAN_EXCLUDE,
                                  type=get_time_arg(False), nargs='+')
    edit_plan_parser.add_argument(Parser.prefix().DELETE,
                                  type=delete_arg, nargs='+')

    edit_plan_subparsers = edit_plan_parser.add_subparsers(dest=Parser.PLAN_REPEATS)
    edit_repeat_parser = edit_plan_subparsers.add_parser(Parser.PLAN_REPEATS)
    edit_repeat_parser.add_argument(Parser.PLAN_REPEATS,
                                  type=int)
    edit_repeat_parser.add_argument(Parser.prefix().TASK_PRIORITY,
                                  choices=['low', 'normal', 'high', 'highest'])
    edit_repeat_parser.add_argument(Parser.prefix().TASK_STATUS,
                                  choices=['pending', 'active', 'completed', 'overdue'])
    edit_repeat_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_START,
                                  action='store_true')
    edit_repeat_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_END,
                                  action='store_true')
    edit_repeat_parser.add_argument(Parser.prefix().TASK_NOTIFICATE_DEADLINE,
                                  action='store_true')
    edit_repeat_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_START,
                                  action='store_true')
    edit_repeat_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_END,
                                  action='store_true')
    edit_repeat_parser.add_argument(Parser.prefix().TASK_NOT_NOTIFICATE_DEADLINE,
                                  action='store_true')
    edit_repeat_parser.add_argument(Parser.prefix().DELETE,
                                  type=delete_arg, nargs='+')
    edit_repeat_parser.set_defaults(edit='repeats')

def init_overall_task_parser(root):
    overall_task_parser = root.add_parser(Parser.OVERALL_TASK)
    overall_task_parser.add_argument(Parser.OVERALL_TASK, action='store_true')

def init_project_parser(root):
    project_parser = root.add_parser(Parser.PROJECT)
    project_root_subparser = project_parser.add_subparsers(dest=Parser.PROJECT)

    add_project_parser = project_root_subparser.add_parser(Parser.ADD)
    add_project_parser.add_argument(Parser.prefix().PROJECT_NAME, 
                                    type=str, required=True)

    show_project_parser = project_root_subparser.add_parser(Parser.SHOW)
    group = show_project_parser.add_mutually_exclusive_group()
    group.add_argument(Parser.prefix().PROJECT_ID, 
                                     type=int)
    group.add_argument(Parser.prefix().PROJECT_NAME, 
                                     type=str)

    delete_project_parser = project_root_subparser.add_parser(Parser.DELETE)
    delete_project_parser.add_argument(Parser.prefix().PROJECT_ID, 
                                     type=int, required=True)
    
    edit_project_parser = project_root_subparser.add_parser(Parser.EDIT)
    edit_project_parser.add_argument(Parser.prefix().PROJECT_ID, 
                                     type=int, required=True)
    edit_project_parser.add_argument(Parser.prefix().PROJECT_NAME,
                                     type=str)

    invite_project_parser = project_root_subparser.add_parser(Parser.PROJECT_INVITE)
    invite_project_parser.add_argument(Parser.prefix().PROJECT_ID,
                                       type=int, required=True)
    invite_project_parser.add_argument(Parser.prefix().USER_UID,
                                       type=int, required=True)
    group = invite_project_parser.add_mutually_exclusive_group(required=True)
    group.add_argument(Parser.prefix().PROJECT_KIND_GUEST, action='store_true')
    group.add_argument(Parser.prefix().PROJECT_KIND_ADMIN, action='store_true')

    exclude_project_parser = project_root_subparser.add_parser(Parser.PROJECT_EXCLUDE)
    exclude_project_parser.add_argument(Parser.prefix().PROJECT_ID,
                                       type=int, required=True)
    exclude_project_parser.add_argument(Parser.prefix().USER_UID,
                                       type=int, required=True)

def init_user_parser(root):
    user_parser = root.add_parser(Parser.USER)
    user_root_subparser = user_parser.add_subparsers(dest=Parser.USER)

    add_user_parser = user_root_subparser.add_parser(Parser.ADD)
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

def proccess_parsed(parsed):
    if parsed.action == Parser.TASK:
        proccess_task(parsed)
    if parsed.action == Parser.USER:
        proccess_user(parsed)
    if parsed.action == Parser.LOGIN:
        proccess_login(parsed)
    if parsed.action == Parser.OVERALL_TASK:
        proccess_overall_task(parsed)
    if parsed.action == Parser.PROJECT:
        proccess_project(parsed)

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
        proccess_task_show_common(parsed)

def proccess_plan(parsed):
    if parsed.plan == Parser.ADD:
        proccess_plan_add(parsed)
    if parsed.plan == Parser.DELETE:
        proccess_plan_remove(parsed)
    if parsed.plan == Parser.EDIT:
        if getattr(parsed, Parser.EDIT, None) == Parser.PLAN_REPEATS:
            proccess_repeat_edit(parsed)
        else:
            proccess_plan_edit(parsed)
    if parsed.plan == Parser.SHOW:
        proccess_plan_show(parsed)

def proccess_plan_add(parsed):
    tid = getattr(parsed, Parser.PLAN_TID, None)
    end = getattr(parsed, Parser.PLAN_END, None)
    shift = getattr(parsed, Parser.PLAN_SHIFT, None)

    shift_time_millis = utils.datetime_to_milliseconds(shift)

    success = PlanController.attach_plan(tid, shift_time_millis, end)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Plan was not added')

def proccess_plan_remove(parsed):
    plan_id = getattr(parsed, Parser.PLAN_ID, None)

    success = PlanController.delete_plan(plan_id)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Plan was not deleted')

def proccess_plan_show(parsed):
    plan_id = getattr(parsed, Parser.PLAN_ID, None)
    tid = getattr(parsed, Parser.PLAN_TID, None)
    repeats = getattr(parsed, Parser.PLAN_REPEATS, None)

    if tid is not None:
        plans = PlanController.get_plan_for_common_task(tid)
        edit_plans = PlanController.get_plan_for_edit_repeat_task(tid)
        plans.extend(edit_plans)
        if len(plans) != 0:
            console_response.show_plan_in_console(plans)

    if plan_id is not None:
        plans = PlanController.get_plans_by_id(plan_id)
        if len(plans) != 0:
            console_response.show_plan_in_console(plans)

    if repeats is not None:
        tasks = TaskController.get_plan_tasks_by_numbers(plan_id, range(repeats))
        if len(tasks) != 0:
            console_response.show_tasks_in_console(tasks)

def proccess_plan_edit(parsed):
    plan_id = getattr(parsed, Parser.PLAN_ID, None)
    end = getattr(parsed, Parser.PLAN_END, None)
    shift = getattr(parsed, Parser.PLAN_SHIFT, None)
    exclude = getattr(parsed, Parser.PLAN_EXCLUDE, None)
    delete = getattr(parsed, Parser.DELETE, None)

    end_time_millis = utils.datetime_to_milliseconds(end)
    shift_time_millis = utils.datetime_to_milliseconds(shift)

    success = True

    if shift_time_millis is not None:
        success = PlanController.edit_plan(plan_id, shift=shift_time_millis)

    if end_time_millis is not None:
        success = PlanController.edit_plan(plan_id, end=end_time_millis)

    if exclude is not None:
        for exclude_datetime in exclude:
            exclude_time_millis = utils.datetime_to_milliseconds(exclude_datetime)
            success = PlanController.delete_repeats_from_plan_by_time_range(plan_id, (exclude_time_millis, ))

    if delete is not None:
        for to_delete in delete:
            if to_delete == Parser.PLAN_END:
                success = PlanController.edit_plan(plan_id, end=None)
            if to_delete == Parser.PLAN_EXCLUDE:
                success = PlanController.restore_all_repeats(plan_id)

    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Plan was not edited')

def proccess_repeat_edit(parsed):
    plan_id = getattr(parsed, Parser.PLAN_ID, None)
    repeat = getattr(parsed, Parser.PLAN_REPEATS, None)
    priority = getattr(parsed, Parser.TASK_PRIORITY, None)
    status = getattr(parsed, Parser.TASK_STATUS, None)
    notificate_start = getattr(parsed, Parser.TASK_NOTIFICATE_START, None)
    notificate_end = getattr(parsed, Parser.TASK_NOTIFICATE_END, None)
    notificate_deadline = getattr(
        parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)
    not_notificate_start = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_START, None)
    not_notificate_end = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_END, None)
    not_notificate_deadline = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_DEADLINE, None)
    delete = getattr(parsed, Parser.DELETE, None)

    args = {}
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

    success = PlanController.edit_repeat_by_number(plan_id, repeat, **args)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Repeat was not edited')

def proccess_task_show_common(parsed):
    now = utils.datetime_to_milliseconds(utils.now())
    
    tasks = TaskController.get_task_with_notifications_to_time(now)
    if tasks is not None and len(tasks) != 0:
        console_response.show_notifications_in_console(tasks)

    tasks = TaskController.get_overdue_tasks(now)
    if tasks is not None and len(tasks) != 0:
        console_response.show_overdue_in_console(tasks)

    time_range = (utils.datetime_to_milliseconds(utils.today()), 
                  utils.shift_datetime_in_millis(utils.today(), datetime.timedelta(days=1)))
    tasks = TaskController.fetch_tasks(time_range=time_range)
    if tasks is not None and len(tasks) != 0:
        console_response.show_tasks_like_tree_in_console(tasks)
    tasks = TaskController.fetch_tasks(timeless=True)
    if tasks is not None and len(tasks) != 0:
        console_response.show_tasks_like_tree_in_console(tasks)

def proccess_task_add(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    if tid is not None:
        tid = int(int)
    pid = getattr(parsed, Parser.TASK_PID, None)
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
    notificate_deadline = getattr(
        parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)

    start_time_millis = utils.datetime_to_milliseconds(start_time)
    end_time_millis = utils.datetime_to_milliseconds(end_time)
    deadline_time_millis = utils.datetime_to_milliseconds(deadline_time)

    try:
        success = TaskController.save_task(pid, parent, title, description,
                                           start_time_millis, end_time_millis, deadline_time_millis, priority,
                                           status, notificate_start, notificate_end, notificate_deadline, tid)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('Task was not added')
    except InvalidTimeError as error:
        console_response.show_invalid_time_range_error(error.start, error.end)
    # except TaskTrackerError as error:
    #     console_response.show_common_error(error)

def proccess_task_show(parsed):
    tid = getattr(parsed, Parser.TASK_TID, None)
    title = getattr(parsed, Parser.TASK_TITLE, None)
    descr = getattr(parsed, Parser.TASK_DESCRIPTION, None)
    parent = getattr(parsed, Parser.TASK_PARENT_ID, None)
    priority = getattr(parsed, Parser.TASK_PRIORITY, None)
    status = getattr(parsed, Parser.TASK_STATUS, None)
    notificate_start_parser = getattr(
        parsed, Parser.TASK_NOTIFICATE_START, None)
    notificate_end_parser = getattr(parsed, Parser.TASK_NOTIFICATE_END, None)
    notificate_deadline_parser = getattr(
        parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)
    not_notificate_start_parser = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_START, None)
    not_notificate_end_parser = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_END, None)
    not_notificate_deadline_parser = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_DEADLINE, None)
    time_to_show = getattr(parsed, Parser.TASK_TIME, None)

    notificate_supposed_start = None
    if notificate_start_parser:
        notificate_supposed_start = True
    if not_notificate_start_parser:
        notificate_supposed_start = False
    notificate_supposed_end = None
    if notificate_end_parser:
        notificate_supposed_end = True
    if not_notificate_end_parser:
        notificate_supposed_end = False
    notificate_deadline = None
    if notificate_deadline_parser:
        notificate_deadline = True
    if not_notificate_deadline_parser:
        notificate_deadline = False

    time_range = None
    if time_to_show is not None:
        if len(time_to_show) == 1:
            time_range = (utils.datetime_to_milliseconds(time_to_show[0]), )
        else:
            time_range = (utils.datetime_to_milliseconds(time_to_show[0]),
                          utils.datetime_to_milliseconds(time_to_show[1]))

    tasks = TaskController.fetch_tasks(parent_tid=parent,
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
    pid = getattr(parsed, Parser.TASK_PID, None)
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
    notificate_deadline = getattr(
        parsed, Parser.TASK_NOTIFICATE_DEADLINE, None)
    not_notificate_start = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_START, None)
    not_notificate_end = getattr(parsed, Parser.TASK_NOT_NOTIFICATE_END, None)
    not_notificate_deadline = getattr(
        parsed, Parser.TASK_NOT_NOTIFICATE_DEADLINE, None)

    force = getattr(parsed, Parser.FORCE, None)

    args = {}
    if title is not None:
        args['title'] = title
    if pid is not None:
        args['pid'] = pid
    if description is not None:
        args['description'] = description
    if start_time is not None:
        args['supposed_start_time'] = utils.datetime_to_milliseconds(start_time)
    if end_time is not None:
        args['supposed_end_time'] = utils.datetime_to_milliseconds(end_time)
    if deadline_time is not None:
        args['deadline_time'] = utils.datetime_to_milliseconds(deadline_time)
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
            if to_delete == Parser.TASK_PID:
                args['pid'] = None
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
        success = TaskController.edit_task(int(tid), **args, force=force)
        if success:
            console_response.show_common_ok()
        else:
            console_response.show_common_error('Task was not edited')
    except InvalidTimeError as error:
        console_response.show_invalid_time_range_error(error.start, error.end)

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
    if uid is not None:
        uid = int(uid)
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
    current = read_current_login()
    for user in users:
        if user.login == current:
            user.online = True
    if users is not None:
        console_response.show_users_in_console(users)
    else:
        console_response.show_common_error()


def proccess_user_delete(parsed):
    uid = getattr(parsed, Parser.USER_UID, None)
    if uid is not None:
        uid = int(uid)

    success = UserController.delete_user(uid)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('User was not deleted')


def proccess_user_edit(parsed):
    uid = getattr(parsed, Parser.USER_UID, None)
    if uid is not None:
        uid = int(uid)
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
    except UserAlreadyExistsError as error:
        print(error)

def proccess_project(parsed):
    if parsed.project == Parser.ADD:
        proccess_project_add(parsed)
    if parsed.project == Parser.SHOW:
        proccess_project_show(parsed)
    if parsed.project == Parser.DELETE:
        proccess_project_delete(parsed)
    if parsed.project == Parser.EDIT:
        proccess_project_edit(parsed)
    if parsed.project == Parser.PROJECT_INVITE:
        proccess_project_invite(parsed)
    if parsed.project == Parser.PROJECT_EXCLUDE:
        proccess_project_exclude(parsed)
    if parsed.project is None:
        proccess_project_show(parsed)

def proccess_project_add(parsed):
    name = getattr(parsed, Parser.PROJECT_NAME, None)
    
    success = ProjectController.save_project(name)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Project was not added')

def proccess_project_show(parsed):
    pid = getattr(parsed, Parser.PROJECT_ID, None)
    name = getattr(parsed, Parser.PROJECT_NAME, None)
    
    if name is not None:
        projects = ProjectController.fetch_projects(name=name)
        if projects is None or len(projects) == 0:
            console_response.show_common_error('Project is not exists')
        pid = projects[0].pid

    if pid is not None:
        try:
            tasks = TaskController.fetch_tasks(pid=pid)
            if tasks is not None:
                console_response.show_tasks_like_tree_in_console(tasks)

        except InvalidProjectIdError as error:
          console_response.show_common_error(error)

        return

    projects = ProjectController.fetch_projects()
    if projects is not None:
        console_response.show_projects_for_user(projects, Controller.get_authenticated_id())

def proccess_project_delete(parsed):
    pid = getattr(parsed, Parser.PROJECT_ID, None)

    success = ProjectController.remove_project(pid)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Project was not removed')

def proccess_project_edit(parsed):
    pid = getattr(parsed, Parser.PROJECT_ID, None)
    name = getattr(parsed, Parser.PROJECT_NAME, None)

    if name is not None:
        success = ProjectController.edit_project(pid, name)
    else:
        success = ProjectController.edit_project(pid)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('Project was not edited')

def proccess_project_invite(parsed):
    pid = getattr(parsed, Parser.PROJECT_ID, None)
    uid = getattr(parsed, Parser.USER_UID, None)
    admin = getattr(parsed, Parser.PROJECT_KIND_ADMIN, None)
    guest = getattr(parsed, Parser.PROJECT_KIND_GUEST, None)

    success = ProjectController.invite_user_to_project(pid=pid, uid=uid, 
                                                       admin=admin, guest=guest)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('User was not invited')

def proccess_project_exclude(parsed):
    pid = getattr(parsed, Parser.PROJECT_ID, None)
    uid = getattr(parsed, Parser.USER_UID, None)

    success = ProjectController.exclude_user_from_project(pid=pid, uid=uid)
    if success:
        console_response.show_common_ok()
    else:
        console_response.show_common_error('User was not excluded')

def proccess_login(parsed):
    login = getattr(parsed, Parser.LOGIN, None)
    users = UserController.fetch_user(login=login)
    if users is not None and len(users) != 0:
        write_current_login(login)
    else:
        console_response.show_common_error('User {} not exists'.format(login))