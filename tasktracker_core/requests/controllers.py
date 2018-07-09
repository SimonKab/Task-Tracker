'''Defines functionality of library

Provide controllers for tasks, projects, users and plans
Defines errors. All errors of library are inherited from TaskTrackerError

Controller is a parent class for all controllers. Provide authentication of user
TaskController manage tasks
PlanController manage plans of tasks
UserController manage users
ProjectController manage projects
'''

import copy
import datetime

from tasktracker_core.model.task import Task, Status, Priority
from tasktracker_core.model.user import User, SuperUser
from tasktracker_core.model.plan import Plan
from tasktracker_core.model.project import Project
from tasktracker_core.storage.sqlite_peewee_adapters import TaskStorageAdapter
from tasktracker_core.storage.sqlite_peewee_adapters import UserStorageAdapter
from tasktracker_core.storage.sqlite_peewee_adapters import PlanStorageAdapter
from tasktracker_core.storage.sqlite_peewee_adapters import ProjectStorageAdapter
import tasktracker_core.utils as utils
import tasktracker_core.logging as logging

class TaskTrackerError(Exception):
    pass

class EditPlanRepeatEditTaskError(TaskTrackerError):

    def __init__(self):
        super().__init__(('Task can not be edited this way because it '
            'belongs to plan. Use plan menu for this instead'))

class InvalidTimeError(TaskTrackerError):

    def __init__(self, start, end):
        super().__init__('Invalid time range')
        self.start = start
        self.end = end

class InvalidParentIdError(TaskTrackerError):

    def __init__(self, parent_tid, explanation=None):
        msg = ''
        if explanation is not None:
            msg += explanation
        super().__init__(msg)
        self.parent_tid = parent_tid

class InvalidStatusError(TaskTrackerError):

    def __init__(self, status, explanation=None):
        msg = 'Invalid status: {}. '.format(status)
        if explanation is not None:
            msg += explanation
        super().__init__(msg)
        self.status = status

class InvalidProjectIdError(TaskTrackerError):

    def __init__(self, pid, explanation=None):
        msg = ''
        if explanation is not None:
            msg += explanation
        super().__init__(msg)
        self.pid = pid    

class UserAlreadyExistsError(TaskTrackerError):

    def __init__(self, user_name):
        super().__init__('User with name {} already exists'.format(user_name))
        self.user_name = user_name

class UserNotExistsError(TaskTrackerError):

    def __init__(self, user_name):
        super().__init__('User with name {} is not exist'.format(user_name))
        self.user_name = user_name

class AuthenticationError(TaskTrackerError):

    def __init__(self):
        super().__init__('User was not authenticated')

class NotAuthenticatedError(TaskTrackerError):

    def __init__(self):
        super().__init__('User was not authenticated')

class PermissionDenied(TaskTrackerError):

    def __init__(self):
        super().__init__('Permission denied')


class Controller():
    '''Root class for controllers. All controllers should inherit it

    Handle authentication of user
    '''

    class Validator():
        '''Root class for validators

        Contains single method run. Run method checks all attributes
        of class and ran which starts with 'validate_'
        '''

        def run(self):
            ''' Ran methods with names starts on 'validate_'
            '''
            for attr in dir(self):
                if attr.startswith('validate_'):
                    method = getattr(self, attr)
                    method()

    _log_tag = 'Controller'

    _not_edit_field_flag = object()

    def __init__(self, controller=None):
        if controller is not None:
            self._user_login_id = controller._user_login_id

            self._plan_storage = controller._plan_storage
            self._task_storage = controller._task_storage
            self._user_storage = controller._user_storage
            self._project_storage = controller._project_storage
        else:
            self._user_login_id = None

            self._plan_storage = PlanStorageAdapter()
            self._task_storage = TaskStorageAdapter()
            self._user_storage = UserStorageAdapter()
            self._project_storage = ProjectStorageAdapter()
    
    def set_database_file(self, db_file):        
        self._plan_storage = PlanStorageAdapter(db_file=db_file)
        self._task_storage = TaskStorageAdapter(db_file=db_file)
        self._user_storage = UserStorageAdapter(db_file=db_file)
        self._project_storage = ProjectStorageAdapter(db_file=db_file)

    def init_storage_adapters(self, plan_storage_adapter=None,
                              task_storage_adapter=None,
                              user_storage_adapter=None,
                              project_storage_adapter=None):
        '''Let to install custom storage adapters. 

        If an adapter will transmitted with None, default adapter
        will be installed
        '''
        if plan_storage_adapter is None:
            self._plan_storage = PlanStorageAdapter()
        else:
            self._plan_storage = plan_storage_adapter()
        if task_storage_adapter is None:
            self._task_storage = TaskStorageAdapter()
        else:
            self._task_storage = task_storage_adapter()
        if user_storage_adapter is None:
            self._user_storage = UserStorageAdapter()
        else:
            self._user_storage = user_storage_adapter()
        if project_storage_adapter is None:
            self._project_storage = ProjectStorageAdapter()
        else:
            self._project_storage = project_storage_adapter()

    
    def _internal_authentication(self, users, provided_user_id=None, provided_user_login=None):
        '''Authenticate user object. For internal use only
        '''

        success = users is not None and len(users) != 0
        if success:
            authenticated_user_id = users[0].uid
            logging.get_logger(self._log_tag).info('Authenticated {}'.format(authenticated_user_id))
            self._user_login_id = authenticated_user_id
        else:
            message = ''
            if provided_user_id is not None:
                message = 'Authentication error for id {}'.format(provided_user_id)
            if provided_user_login is not None:
                message = 'Authentication error for login {}'.format(provided_user_login)
            logging.get_logger(self._log_tag).error(message)
            raise AuthenticationError()
        return success

    
    def authentication(self, user_id):
        '''Let user to be authenticated by it's id

        If user will not be authenticated most controllers will not be working
        Throws AuthenticationError when user id was not found in database
        '''

        controller = UserController(self)
        users = controller.fetch_user(uid=user_id)
        return self._internal_authentication(users, provided_user_id=user_id)

    
    def authentication_by_login(self, login):
        '''Let user to be authenticated by it's username

        If user will not be authenticated most controllers will not be working
        Throws AuthenticationError when user id was not found in database
        '''

        controller = UserController(self)
        users = controller.fetch_user(login=login)
        return self._internal_authentication(users, provided_user_login=login)

    
    def logout(self):
        self._user_login_id = None
        return True

    @staticmethod
    def require_authentication(method):
        '''Decorator for methods of controller

        Decorator serves for methods which need user to be authenticated
        If it is not so, throws NotAuthenticatedError
        '''

        def check(self, *args, **kwargs):
            # TODO
            if isinstance(self, Controller):
                if not self.is_authenticated():
                    raise NotAuthenticatedError()
            return method(self, *args, **kwargs)
        return check

    
    def is_authenticated(self):
        return self._user_login_id != None

    
    def get_authenticated_id(self):
        '''Returns id of authenticated user or None if nobody was authenticated'''

        return self._user_login_id

class TaskController(Controller):
    '''Controller for tasks

    Manage all work with tasks. Save, edit, get, remove single tasks.
    Get plan repeats like tasks. 
    If you need more about plans look at PlanController
    '''

    _log_tag = 'TaskController'

    class TaskValidator(Controller.Validator):
        '''Validate tasks

        Validate task time, parent tid, pid, status-time relations
        and additions validate tasks which represent edited repeats of plans
        '''

        def __init__(self, task, controller, for_edit=False, force=False):
            self.task = task
            self.controller = controller
            self.for_edit = for_edit
            self.force = force

        def validate_task_time(self):
            ''' Validated task time limits
            
            Throws InvalideTimeError if time limits are broken.
            For instance, start is after end 
            '''
            self.simple_validate_time(self.task.supposed_start_time, self.task.supposed_end_time)
            self.simple_validate_time(self.task.supposed_end_time, self.task.deadline_time)
            self.simple_validate_time(self.task.supposed_start_time, self.task.deadline_time)

        @staticmethod
        def simple_validate_time(start, end):
            def is_first_bigger(first, second):
                if first == None or second == None:
                    return False
                return first > second

            if start != -1 and end != -1:
                if is_first_bigger(start, end):
                    raise InvalidTimeError(start, end)

        def validate_parent_tid(self):
            '''Validate parent-child relations

            Throws InvalidateParentIdError in next cases:
            1) Parent tid is not exists
            2) Parent tid is child tid. A loop
            3) Priority of child is not equals to priority of parent
            4) Parent has status completed but child is not
            5) Parent has status overdue but child is not
            6) Child task time range is not inside of parent time range. 
            For example, parent has time [10.05.2018, 12.05.2018] but
            child has time [11.05.2018, 13.05.2018]
            7) You can not create a planned parent
            '''
            if self.task.parent_tid == None:
                return

            if self.task.parent_tid == self.task.tid:
                logging.get_logger(self.controller._log_tag).error('Wrong parent. Trying to connect task to itself')
                raise InvalidParentIdError(parent_tid)

            filter = TaskStorageAdapter.Filter()
            filter.tid(self.task.parent_tid)
            tasks = self.controller._task_storage.get_tasks(filter)
            if len(tasks) == 0:
                logging.get_logger(self.controller._log_tag).error('Wrong parent. Parent does not exist')
                raise InvalidParentIdError(self.task.parent_tid)

            parent_task = tasks[0]

            if self.task.priority is None:
                self.tasks.priority = parent_task.priority

            if self.task.priority != parent_task.priority:
                msg = 'Wrong priority. Parent priority: {}, child \
                    priority: {}'.format(Priority.to_str(parent_task.priority), Priority.to_str(self.task.priority))
                logging.get_logger(self.controller._log_tag).error('Priority is not equal to parent priority')
                raise InvalidParentIdError(self.task.parent_tid, msg)

            if self.task.status is None:
                self.task.status = parent_task.status

            if (parent_task.status == Status.COMPLETED
                    and self.task.status != Status.COMPLETED):
                msg = 'Wrong parent status. Task status has to be completed because parent status is completed'
                logging.get_logger(self.controller._log_tag).error('Trying to connect not completed task with complete parent')
                raise InvalidParentIdError(self.task.parent_tid, msg)    

            if (parent_task.status == Status.ACTIVE 
                and self.task.status == Status.PENDING):
                self.task.status = parent_task.status
                # msg = 'Wrong parent status. You try to add pending subtask to active task'
                # raise InvalidParentIdError(self.task.parent_tid, msg)

            if (parent_task.status == Status.OVERDUE
                and self.task.status != Status.OVERDUE):
                msg = 'Wrong parent status. Task status has to be overdue because parent status is overdue'
                logging.get_logger(self.controller._log_tag).error('Trying to connect not overdue task with overdue parent')
                raise InvalidParentIdError(self.task.parent_tid, msg)

            parent_task_time_range = parent_task.get_time_range()
            task_time_range = self.task.get_time_range()
            if len(task_time_range) == 0:
                self.task.supposed_start_time = parent_task.supposed_start_time
                self.task.supposed_end_time = parent_task.supposed_end_time
                self.task.deadline_time = parent_task.deadline_time
            if len(parent_task_time_range) == 2:
                print(self.task.supposed_start_time, self.task.supposed_end_time, parent_task_time_range)
                if not self.task.is_task_inside_of_range_parent(parent_task_time_range):
                    logging.get_logger(self.controller._log_tag).error('Child task is wider')
                    msg = 'Wrong time. Child task time is wider than parent'
                    raise InvalidParentIdError(self.task.parent_tid, msg)
            if len(parent_task_time_range) == 1:
                print(self.task.get_time_range(), parent_task_time_range)
                if parent_task.supposed_start_time is None:
                    if not self.task.is_before_time(parent_task_time_range, True):
                        logging.get_logger(self.controller._log_tag).error('Child task is wider')
                        msg = 'Wrong time. Child task time is wider than parent'
                        raise InvalidParentIdError(self.task.parent_tid, msg)  
                else:
                    if not self.task.is_after_time(parent_task_time_range, True):
                        logging.get_logger(self.controller._log_tag).error('Child task is wider')
                        msg = 'Wrong time. Child task time is wider than parent'
                        raise InvalidParentIdError(self.task.parent_tid, msg)  

            planned = PlanController(self.controller).is_task_planned(self.task.parent_tid)
            if planned:
                logging.get_logger(self.controller._log_tag).error('Trying to create planned parent')
                msg = 'Parent can not be planned'
                raise InvalidParentIdError(self.task.parent_tid, msg)

        def validate_pid(self):
            ''' Validate project id

            Throws InvalidProjectIdError if project is not exist
            '''
            projects = ProjectController(self.controller).fetch_projects(pid=self.task.pid)
            if projects is None or len(projects) == 0:
                logging.get_logger(self.controller._log_tag).error('Trying to connect with non-existent project')
                raise InvalidProjectIdError(self.task.pid)

        def validate_status_time_relations(self):
            '''Validate if status corresponds time

            Throws InvalidStatusError if status is pending or active when
            time is before today or if status is overdue when time is
            after today
            '''
            if self.force:
                return

            def timestamp_to_display(timestamp):
                if timestamp is not None:
                    return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y %H:%M')


            now = utils.datetime_to_milliseconds(utils.now())
            task_time_range = self.task.get_time_range()
            if len(task_time_range) != 0:
                print('hello', timestamp_to_display(now), timestamp_to_display(self.task.supposed_end_time), self.task.is_before_time((now, )))
                if (self.task.is_before_time((now, ))
                    and not self.task.only_start()):
                    if (self.task.status == Status.PENDING
                        or self.task.status == Status.ACTIVE):
                        logging.get_logger(self.controller._log_tag).error(('Trying to set status as pending or active ' 
                            'when task is in the past'))
                        msg = ('Wrong status. You can not set status as pending '
                            'or active if task is in the past')
                        raise InvalidStatusError(Status.to_str(self.task.status), msg)
                else:
                    if self.task.status == Status.OVERDUE:
                        logging.get_logger(self.controller._log_tag).error(('Trying to set status as overdue ' 
                            'when task is in the past'))
                        msg = ('Wrong status. You can not set status as overdue'
                            'if task is not in the past')
                        raise InvalidStatusError(Status.to_str(self.task.status), msg)

        def validate_plan_edit_task(self):
            '''Validate tasks which are edits of repeats of plans 

            If task is edit of repeat of plan, we need to use plan menu instead
            '''

            plans = PlanController(self.controller).get_plan_for_edit_repeat_task(self.task.tid)
            if plans is not None and len(plans) != 0:
                logging.get_logger(self.controller._log_tag).error('Trying to change edit repeat not through plan menu')
                raise EditPlanRepeatEditTaskError()

    
    @Controller.require_authentication
    def save_task(self,
                  pid=None,
                  parent_tid=None, 
                  title=None, 
                  description=None, 
                  supposed_start=None, 
                  supposed_end=None, 
                  deadline_time=None, 
                  priority=None, 
                  status=None,
                  notificate_supposed_start=None, 
                  notificate_supposed_end=None,
                  notificate_deadline=None, task_id=-1):
        '''Save task

        Priority and status can be string. 
        In this case special transforms will occure

        If pid is None, default project will be used
        '''

        if pid is None:
            default_project = ProjectController(self).get_default_project_for_user(self._user_login_id)
            if default_project is None:
                return False
            pid = default_project.pid

        UserController(self).check_project_available(self._user_login_id, pid, True)

        if task_id is None:
            task_id = -1

        if status is None:
            status = Status.PENDING

        if priority is None:
            priority = Priority.NORMAL

        if notificate_supposed_start is None:
            notificate_supposed_start = False

        if notificate_supposed_end is None:
            notificate_supposed_end = False

        if notificate_deadline is None:
            notificate_deadline = False

        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        if isinstance(supposed_start, datetime.datetime):
            supposed_start = utils.datetime_to_milliseconds(supposed_start)

        if isinstance(supposed_end, datetime.datetime):
            supposed_end = utils.datetime_to_milliseconds(supposed_end)

        if isinstance(deadline_time, datetime.datetime):
            deadline_time = utils.datetime_to_milliseconds(deadline_time)

        task = Task()
        if task_id >= 0:
            task.tid = task_id
        task.pid = pid
        task.uid = self._user_login_id
        task.title = title
        task.parent_tid = parent_tid
        task.description = description
        task.supposed_start_time = supposed_start
        task.supposed_end_time = supposed_end
        task.deadline_time = deadline_time
        task.priority = priority
        task.status = status
        task.notificate_supposed_start = notificate_supposed_start
        task.notificate_supposed_end = notificate_supposed_end
        task.notificate_deadline = notificate_deadline

        validator = self.TaskValidator(task, self)
        validator.run()

        success = self._task_storage.save_task(task)
        return success


    
    @Controller.require_authentication
    def get_last_saved_task_tid(self):
        return self._task_storage.get_last_saved_task().tid


    
    @Controller.require_authentication
    def get_task_with_notifications_to_time(self, time):
        '''Return all tasks which need notifications to release
        '''
        filter = self._task_storage.Filter()
        filter.uid(self._user_login_id)
        filter.one_of_notificate()
        filter.to_time(time)
        filter.not_completed()
        tasks = self._task_storage.get_tasks(filter)

        return tasks

    
    @Controller.require_authentication
    def get_overdue_tasks(self, time):
        '''Return all tasks with status overdue before today'''
        filter = self._task_storage.Filter()
        filter.uid(self._user_login_id)
        filter.to_time(time)
        filter.status(Status.OVERDUE)
        tasks = self._task_storage.get_tasks(filter)
        return tasks

    
    @Controller.require_authentication
    def find_overdue_tasks(self, time):
        '''Refresh info about overdue tasks

        Method checks single tasks and planned tasks.
        Call overdue repeats of planned tasks to chenge their status
        '''
        logging.get_logger(self._log_tag).info('Find overdue tasks command starts')

        filter = self._task_storage.Filter()
        filter.uid(self._user_login_id)
        filter.overdue_by_time(time)
        tasks = self._task_storage.get_tasks(filter)
        for task in tasks:
            plans = PlanController(self).get_plan_for_common_task(task.tid)
            if plans is not None and len(plans) != 0:
                for plan in plans:
                    time_range = (task.get_left_border(), time)
                    plan_repeats = PlanController(self).get_repeats_by_time_range(plan.plan_id, time_range)
                    for repeat in plan_repeats:
                        PlanController(self).edit_repeat_by_number(plan.plan_id, repeat, status=Status.OVERDUE)
                return

            edit_plans = PlanController(self).get_plan_for_edit_repeat_task(task.tid)
            if edit_plans is not None and len(edit_plans) != 0:
                for plan in edit_plans:
                    repeat = PlanController(self).get_repeat_number_for_task(task)
                    PlanController(self).edit_repeat_by_number(plan.plan_id, repeat, status=Status.OVERDUE)
                return
            
            self.edit_task(task.tid, status=Status.OVERDUE)

            logging.get_logger(self._log_tag).info('Find overdue tasks command finnished')

    
    @Controller.require_authentication
    def fetch_tasks(self, pid=None, parent_tid=None, tid=None, title=None, description=None,
                        priority=None, status=None, notificate_supposed_start=None, 
                        notificate_supposed_end=None, notificate_deadline=None, 
                        time_range=None, timeless=None):
        '''Fetches tasks

        If pid was specified, tasks will be fetched from projects but not by
        user id. Otherwise authorised user id will be used
        If there are plan tasks, their repeats and edits will be fetched
        '''

        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        filter = self._task_storage.Filter()
        if pid is not None:
            UserController(self).check_project_available(self._user_login_id, pid)
            filter.pid(pid)
        else:
            filter.uid(self._user_login_id)
            
        if tid is not None:
            filter.tid(tid)
        if parent_tid is not None:
            filter.parent_tid(parent_tid)
        # if title is not None:
        #     filter.title(title)
        # if description is not None:
        #     filter.description(description)
        if priority is not None:
            filter.priority(priority)
        if status is not None:
            filter.status(status)
        if notificate_supposed_start is not None:
            filter.notificate_supposed_start(notificate_supposed_start)
        if notificate_supposed_end is not None:
            filter.notificate_supposed_end(notificate_supposed_end)
        if notificate_deadline is not None:
            filter.notificate_deadline(notificate_deadline)
        if time_range is not None:
            filter_time_range = time_range
            if len(filter_time_range) == 1:
                filter_time_range = (filter_time_range[0], filter_time_range[0])
            filter.filter_range(*filter_time_range)
        if timeless:
            filter.timeless()

        tasks = self._task_storage.get_tasks(filter)

        reverse_task = tasks[::-1]
        for i in range(len(reverse_task)):
            task = reverse_task[i]
            plans = PlanController(self).get_plan_for_common_task(task.tid)
            if plans is not None and len(plans) != 0:
                tasks.remove(task)
                if time_range is None:
                    most_valuable_task = self.get_most_valuable_task(plans[0].plan_id)
                    if most_valuable_task is not None:
                        logging.get_logger(self._log_tag).info(('Task {} was defined as planned. '
                            'Most valuable for it is {}').format(task.tid, most_valuable_task.__dict__))
                        tasks.append(most_valuable_task)

        print('PLANS', time_range)
        if time_range is not None:
            plans = PlanController(self).get_plans_by_time_range(time_range)
            plan_tid_ids = []
            print('PLANS', plans)
            for plan in plans:
                print('PLANS', 'HERE')
                if plan.tid in plan_tid_ids:
                    continue
                plan_tid_ids.append(plan.tid)
                plan_tasks = self.get_plan_tasks_by_time_range(plan.plan_id, time_range)
                print('PLANS', plan_tasks)
                if tasks is None:
                    tasks = []
                tasks.extend(plan_tasks)

        print('PLANS 1', tasks)

        if title is not None:
            for i in range(len(tasks)-1, -1, -1):
                if title not in tasks[i].title:
                    del tasks[i]
        if description is not None:
            for i in range(len(tasks)-1, -1, -1):
                if (tasks[i].description is not None and
                    description not in tasks[i].description):
                    del tasks[i]

        return tasks

    
    @Controller.require_authentication
    def get_most_valuable_task(self, plan_id):
        '''Returns the first not overdue repeat or None of there is not so'''
        number = 0
        while True:
            tasks = self.get_plan_tasks_by_numbers(plan_id, [number])
            if tasks is None or len(tasks) == 0:
                return None
            if tasks[0].status != Status.OVERDUE:
                return tasks[0]
            number += 1

    
    @Controller.require_authentication
    def get_plan_tasks_by_time_range(self, plan_id, time_range):
        '''Returns tasks representations of repeats of sepcified plan

        See get_plan_tasks_by_numbers() for more information
        '''
        numbers = PlanController(self).get_repeats_by_time_range(plan_id, time_range)
        if numbers is None:
            return []

        return self.get_plan_tasks_by_numbers(plan_id, numbers)

    
    @Controller.require_authentication
    def get_plan_tasks_by_numbers(self, plan_id, numbers):
        '''Returns task representations of repeats of specified plan

        Returns simple task representations and edits.
        Simple representations is common task of plan but with new time range
        If plan repeat was deleted, the method does not return it
        If there is not repeats to return, empty list will be return
        '''

        plans = self._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return []
        plan = plans[0]

        print("PLAN", plan_id, plan.tid)

        filter = self._task_storage.Filter()
        filter.tid(plan.tid)
        tasks = self._task_storage.get_tasks(filter)
        print(tasks)
        if tasks is None or len(tasks) == 0:
            return []
        task = tasks[0]

        result_tasks = []

        if plan.exclude is not None:
            numbers = list(numbers)
            plan_controller = PlanController(self)
            for exclude_number in plan.exclude:
                if exclude_number in numbers:
                    numbers.remove(exclude_number)
                    tid = plan_controller.get_tid_for_edit_repeat(plan.plan_id, exclude_number)
                    if tid is not None:
                        edit_tasks = self.fetch_tasks(tid=tid)
                        if edit_tasks is not None and len(edit_tasks) != 0:
                            result_tasks.append(edit_tasks[0])

        shift_time_array = []
        for number in numbers:
            allowable = PlanController(self).is_allowable_repeat(number, plan, task)
            if allowable:
                shift_time_array.append(plan.shift*number)

        for shift_time in shift_time_array:
            new_task = copy.deepcopy(task)
            new_task.shift_time(shift_time)
            result_tasks.append(new_task)

        return result_tasks

    
    @Controller.require_authentication
    def remove_task(self, task_id):
        '''Remove task from database
        '''
        UserController(self).check_task_available(self._user_login_id, task_id, True)

        success = self._task_storage.remove_task(task_id)
        return success

    
    @Controller.require_authentication
    def edit_task(self, task_id, pid=Controller._not_edit_field_flag,
                  parent_tid=Controller._not_edit_field_flag, 
                  title=Controller._not_edit_field_flag, 
                  description=Controller._not_edit_field_flag,
                  supposed_start_time=Controller._not_edit_field_flag, 
                  supposed_end_time=Controller._not_edit_field_flag, 
                  deadline_time=Controller._not_edit_field_flag,
                  priority=Controller._not_edit_field_flag, 
                  status=Controller._not_edit_field_flag, 
                  notificate_supposed_start=Controller._not_edit_field_flag, 
                  notificate_supposed_end=Controller._not_edit_field_flag, 
                  notificate_deadline=Controller._not_edit_field_flag,
                  force=False):
        '''Edit task

        If edititing task is plan common task and time not shifted
        on plan shift, all excludes will be restored
        If pid is not specified, default pid for user will be used
        If edititing task is parent task and status and/or priority are changed
        all childrens will be notified about their parent changes
        '''

        UserController(self).check_task_available(self._user_login_id, task_id, True)

        filter = TaskStorageAdapter.Filter()
        filter.tid(task_id)
        tasks = self._task_storage.get_tasks(filter)
        if tasks is None or len(tasks) == 0:
            return False
        task = tasks[0]

        if supposed_start_time != -1 or supposed_end_time != -1 or deadline_time != -1:
            plan_controller = PlanController(self)
            plans = plan_controller.get_plan_for_common_task(task_id)
            for plan in plans:
                plan_controller.restore_all_repeats(plan.plan_id)      

        if status is not Controller._not_edit_field_flag:
            plan_controller = PlanController(self)
            plans = plan_controller.get_plan_for_common_task(task_id)
            if plans is not None and len(plans) != 0:
                return False

        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        if status is None:
            status = Status.PENDING

        if priority is None:
            priority = Priority.NORMAL

        filter = TaskStorageAdapter.Filter()
        filter.parent_tid(task_id)
        childer = self._task_storage.get_tasks(filter)

        if pid is not Controller._not_edit_field_flag:
            if pid is None:
                default_project = ProjectController(self).get_default_project_for_user(self._user_login_id)
                if default_project is None:
                    return False
                pid = default_project.pid
            task.pid = pid
        if parent_tid is not Controller._not_edit_field_flag:
            task.parent_tid = parent_tid
        if title is not Controller._not_edit_field_flag:
            task.title = title
        if description is not Controller._not_edit_field_flag:
            task.description = description
        if supposed_start_time is not Controller._not_edit_field_flag:
            task.supposed_start_time = supposed_start_time
        if supposed_end_time is not Controller._not_edit_field_flag:
            task.supposed_end_time = supposed_end_time
        if deadline_time is not Controller._not_edit_field_flag:
            task.deadline_time = deadline_time
        if priority is not Controller._not_edit_field_flag:
            task.priority = priority
        if status is not Controller._not_edit_field_flag:
            task.status = status
        if notificate_supposed_start is not Controller._not_edit_field_flag:
            task.notificate_supposed_start = notificate_supposed_start
        if notificate_supposed_end is not Controller._not_edit_field_flag:
            task.notificate_supposed_end = notificate_supposed_end
        if notificate_deadline is not Controller._not_edit_field_flag:
            task.notificate_deadline = notificate_deadline

        task_validator = self.TaskValidator(task, self, force=force)
        task_validator.run()

        success = self._task_storage.edit_task_from_model(task)
        if success:
            for child in childer:
                if status is not Controller._not_edit_field_flag:
                    self.edit_task(child.tid, status=status)
                if priority is not Controller._not_edit_field_flag:
                    self.edit_task(child.tid, priority=priority)
        return success

class UserController(Controller):
    '''User controllers

    Manage CRUD of users. Also check if task, plan or project is acceccable
    for specified user
    All methods does not need authentication of user
    '''

    _log_tag = 'UserController'

    
    def save_user(self, login=None, user_id=-1):
        '''Save user

        If user already exists, UserAlreadyExistsError will be raised
        '''

        if user_id is None:
            user_id = -1

        user = User()
        if user_id >= 0:
            user.user_id = user_id
        user.login = login

        exists = self._user_storage.check_user_existence(login)
        if not exists:
            success = self._user_storage.save_user(user)

            project = Project()
            project.creator = self._user_storage.get_last_saved_user().uid
            project.name = Project.default_project_name
            self._project_storage.save_project(project)

            return success
        else:
            raise UserAlreadyExistsError(login)

    
    def fetch_user(self, uid=None, login=None, online=None):
        '''Return users by specified params'''

        filter = UserStorageAdapter.Filter()
        if uid is not None:
            filter.uid(uid)
        if login is not None:
            filter.login(login)
        if online is not None:
            filter.online(online)

        users = self._user_storage.get_users(filter)
        return users

    
    def delete_user(self, user_id):
        '''Delete user and related projects

        User can delete only itself
        '''

        projects = self._project_storage.get_projects(user_id)
        for project in projects:
            if project.creator == user_id:
                ProjectController(self).remove_project_for_user(user_id, project.pid)

        ProjectController(self).fetch_projects()
        success = self._user_storage.delete_user(user_id)
        return success

    
    def edit_user(self, user_id, login=-1, online=-1):
        '''Edit user

        if specified login already exists in database, UserAlreadyExistsError
        will be raised
        '''

        user_field_dict = {User.Field.uid: user_id}
        if login is not -1:
            user_field_dict[User.Field.login] = login
        if online is not -1:
            user_field_dict[User.Field.online] = online

        if login is not -1 and login is not None:
            exists = self._user_storage.check_user_existence(login)
            if exists:
                logging.get_logger(self._log_tag).error('Trying to add already exist user')
                raise UserAlreadyExistsError(login)

        success = self._user_storage.edit_user(user_field_dict)
        return success

    
    def check_task_available(self, uid, tid, edit=False):
        '''Check task for availability for specified user

        First method checks in which project tid located.
        If it is not located in a project method check user is of task
        and specified user is. If they are not equals, 
        PersmissionDenied will be raised.
        If there is project, checks if user is guest if project and raise
        PermissionDenied if it is so. Than checks if user is participiant
        of project and raise PermissionDenied if it is so
        '''
        filter = TaskStorageAdapter.Filter()
        filter.tid(tid)
        tasks = self._task_storage.get_tasks(filter)
        if tasks is not None and len(tasks) != 0:
            task = tasks[0]
            projects = ProjectController(self).fetch_projects(pid=task.pid)
            if projects is not None and len(projects) != 0:
                project = projects[0]
                user_kind = project.get_user_kind(uid)
                if edit and user_kind == Project.UserKind.GUEST:
                    logging.get_logger(self._log_tag).error('Trying to edit task by guest')
                    raise PermissionDenied()
                if user_kind is None:
                    logging.get_logger(self._log_tag).error('Trying to access task which does not belong to user')
                    raise PermissionDenied()
            elif task.uid != uid:
                logging.get_logger(self._log_tag).error('Trying to access task which does not belong to user')
                raise PermissionDenied()                
                    

    
    def check_plan_available(self, uid, plan_id, edit=False):
        '''Checks plan availability by checking availability
        of related task
        '''

        plans = self._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return
        plan = plans[0]
        self.check_task_available(uid, plan.tid, edit)

    
    def check_project_available(self, uid, pid, edit=False):
        '''Check project availability

        If user is not participiant of project, PermissionDenied will be raised
        Edit flag need to specify action in which the checking is performing
        If edit flag is set in True and user is guest of project
        PersmissionDenied will be raised
        '''

        projects = self._project_storage.get_projects(uid=uid, pid=pid)
        if projects is not None and len(projects) != 0:
            project = projects[0]
            user_kind = project.get_user_kind(uid)
            if user_kind is None:
                logging.get_logger(self._log_tag).error('Trying to access project which does not belong to user')
                raise PermissionDenied()
            if edit and user_kind == Project.UserKind.GUEST:
                logging.get_logger(self._log_tag).error('Trying to edit project by guest')
                raise PermissionDenied()

class PlanController(Controller):
    '''Controller for plans
    
    Manage CRUD of plans and a lot of other stuff like:
    gettting repeats by specified params, excluding and editing repeats
    restoring repeats and other
    '''

    _log_tag = 'PlanController'

    
    @Controller.require_authentication
    def attach_plan(self, tid, shift, end=None):
        '''Create and attach new plan with sift and mey be end to task
        '''

        UserController(self).check_task_available(self._user_login_id, tid, True)

        task = TaskController(self).fetch_tasks(tid=tid)[0]
        if len(task.get_time_range()) == 0:
            return False
        if task.parent_tid is not None:
            return False
        child_taks = TaskController(self).fetch_tasks(parent_tid=tid)
        if child_taks is not None and len(child_taks) != 0:
            return False

        plan = Plan()
        plan.tid = tid
        plan.shift = shift
        plan.end = end
        success = self._plan_storage.save_plan(plan)
        return success

    
    @Controller.require_authentication
    def edit_plan(self, plan_id, shift=Controller._not_edit_field_flag, 
                end=Controller._not_edit_field_flag):
        '''Edit shift and end of plan
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        attr = {Plan.Field.plan_id: plan_id}
        if shift is not Controller._not_edit_field_flag:
            attr[Plan.Field.shift] = shift
        if end is not Controller._not_edit_field_flag:
            attr[Plan.Field.end] = end
        success = self._plan_storage.edit_plan(attr)
        return success

    
    @Controller.require_authentication
    def shift_start(self, plan_id, shift_time):
        '''Shifts start of plan.

        If plan is shifted on plans shift time excludes will be recalculated.
        Otherwise all excludes will be restored
        '''

        success = self._plan_storage.recalculate_exclude_when_start_time_shifted(plan_id, shift_time)
        return success

    
    @Controller.require_authentication
    def edit_repeat_by_number(self, plan_id, number, 
                              status=Controller._not_edit_field_flag, 
                              priority=Controller._not_edit_field_flag, 
                              notificate_supposed_start=Controller._not_edit_field_flag, 
                              notificate_supposed_end=Controller._not_edit_field_flag, 
                              notificate_deadline=Controller._not_edit_field_flag):
        '''Edit specified repeat by number

        You can not change all params of task. Only status, priority and
        notifications are available for edititng. Because other task params
        conflict with idea of planned task

        Creates real edited task in db with connection to plan
        '''
        
        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        plans = self._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return False
        plan = plans[0]

        task_controller = TaskController(self)
        tasks = task_controller.get_plan_tasks_by_numbers(plan.plan_id, [number])
        if tasks is None or len(tasks) != 1:
            return False
        task = tasks[0]

        if isinstance(status, str):
            status = Status.from_str(status)
        if isinstance(priority, str):
            priority = Priority.from_str(priority)

        if status is not Controller._not_edit_field_flag:
            task.status = status
        if priority is not Controller._not_edit_field_flag:
            task.priority = priority
        if notificate_supposed_start is not Controller._not_edit_field_flag:
            task.notificate_supposed_start = notificate_supposed_start
        if notificate_supposed_end is not Controller._not_edit_field_flag:
            task.notificate_supposed_end = notificate_supposed_end
        if notificate_deadline is not Controller._not_edit_field_flag:
            task.notificate_deadline = notificate_deadline

        tid = self.get_tid_for_edit_repeat(plan.plan_id, number)
        if tid is not None:
            success = self._task_storage.remove_task(tid)
            if not success:
                return False

        success = self._task_storage.save_task(task)
        if not success:
            return False

        edited_task = self._task_storage.get_last_saved_task()

        success = self._plan_storage.edit_plan_repeat(plan.plan_id, number, edited_task.tid)
        return success

    
    @Controller.require_authentication
    def is_task_planned(self, tid):
        '''Checks if task connects with a plan
        '''

        # UserController.check_plan_available(self._user_login_id, plan_id)

        plans = self.get_plan_for_common_task(tid)
        edit_plans = self.get_plan_for_edit_repeat_task(tid)
        plans += edit_plans
        return plans is not None and len(plans) != 0

    
    @Controller.require_authentication
    def delete_repeats_from_plan_by_number(self, plan_id, number):
        '''Deletes repeats from plan by number

        If number is edited task, the task will be deleted
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        edit_tid = self.get_tid_for_edit_repeat(plan_id, number)
        type = self._plan_storage.get_exclude_type(plan_id, number)
        if type == Plan.PlanExcludeKind.DELETED:
            return True
        if edit_tid is not None:
            task_controller = TaskController(self)
            task_controller.remove_task(edit_tid)
        success = self._plan_storage.delete_plan_repeat(plan_id, number)
        return success

    
    @Controller.require_authentication
    def delete_repeats_from_plan_by_time_range(self, plan_id, time_range):
        '''Delete repeats from plan by time range

        It is combination of get_repeats_by_time_range() 
        and delete_repeats_from_plan_by_number()
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        repeats = self.get_repeats_by_time_range(plan_id, time_range, with_exclude=True)
        if repeats is None:
            return False

        for number in repeats:
            success = self.delete_repeats_from_plan_by_number(plan_id, number)
            if not success:
                return False

        return True

    
    @Controller.require_authentication
    def delete_plan(self, plan_id):
        '''Deletes plan and all related tasks
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        success = self._plan_storage.remove_plan(plan_id)
        return success

    
    @Controller.require_authentication
    def restore_all_repeats(self, plan_id):
        '''Restores all repeats of plan

        If repeat is edit task it will be deleted
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        success = self._plan_storage.restore_all_repeats(plan_id)
        return success

    
    @Controller.require_authentication
    def restore_repeat(self, plan_id, number):
        '''Restores specified repeat of plan

        If repeat is edit task it will be deleted
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        success = self._plan_storage.restore_plan_repeat(plan_id, number)
        return success

    
    @Controller.require_authentication
    def restore_repeats_in_time_range(self, plan_id, time_range):
        '''Resotres repeats in time range

        It is combination of get_repeats_by_time_range() and 
        restore_repeat()
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id, True)

        repeats = self.get_repeats_by_time_range(time_range)
        if repeats is None:
            return False

        for number in repeats:
            success = self.restore_repeat(plan_id, number)
            if not success:
                return False

        return True

    
    @Controller.require_authentication
    def get_plan_for_common_task(self, common_tid):
        '''Returns plan for common task
        '''

        UserController(self).check_task_available(self._user_login_id, common_tid)

        plans = self._plan_storage.get_plans(common_tid=common_tid)
        return plans

    
    @Controller.require_authentication
    def get_plan_for_edit_repeat_task(self, edit_repeat_tid):
        '''Returns plans by task if the task is edit of repeat of a plan
        '''

        UserController(self).check_task_available(self._user_login_id, edit_repeat_tid)

        plans = self._plan_storage.get_plans(edit_repeat_tid=edit_repeat_tid)
        return plans

    
    @Controller.require_authentication
    def get_exclude_type(self, plan_id, number):
        '''Return type of exclude

        Excludes can be either DELETED or EDITED
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id)

        exclude_type = self._plan_storage.get_exclude_type(plan_id, number)
        return exclude_type

    
    @Controller.require_authentication
    def get_tid_for_edit_repeat(self, plan_id, number):
        '''Returns task if for repeat if the repeat was edited
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id)

        tid = self._plan_storage.get_tid_for_edit_repeat(plan_id, number)
        return tid

    
    @Controller.require_authentication
    def get_plans_by_id(self, plan_id):
        '''Returns plan by plan id
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id)

        plans = self._plan_storage.get_plans(plan_id=plan_id)
        return plans

    
    @Controller.require_authentication
    def get_plans_by_time_range(self, time_range):
        '''Check existent plans and returns plans 
        which have repeats in time range
        '''

        plans = self._plan_storage.get_plans()
        if plans is None:
            return []

        result_plans = []
        for plan in plans:
            try:
                repeats = self.get_repeats_by_time_range(plan.plan_id, time_range)
                if repeats is not None and len(repeats) > 0:
                    result_plans.append(plan)
            except PermissionDenied:
                pass
        return result_plans

    
    @Controller.require_authentication
    def get_repeat_number_for_task(self, plan_id, task):
        '''Returns repeat number of specified task
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id)

        start = task.supposed_start_time
        if start is None:
            start = task.supposed_end_time
        if start is None:
            start = task.deadline_time
        end = task.deadline_time
        if end is None:
            end = task.supposed_end_time
        if end is None:
            end = task.supposed_start_time

        repeats = self.get_repeats_by_time_range(plan_id, (start, end), True, True)
        if len(repeats) == 0:
            return None
        return repeats[0]

    @staticmethod
    def is_allowable_repeat(number, plan, task):
        '''Check if task represents allowable repeat

        Allowable means that task is not after end of plan
        and repeat of the task is not excluded
        '''

        temp_task = copy.deepcopy(task)
        temp_task.shift_time(number*plan.shift)

        before_end = (plan.end is None 
            or not temp_task.is_after_time((plan.end, )))

        in_exclude = (plan.exclude is not None and 
            number in plan.exclude)

        return before_end and not in_exclude

    
    @Controller.require_authentication
    def get_time_for_repeat(self, plan_id, number):
        UserController(self).check_plan_available(self._user_login_id, plan_id)

        plans = self._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return None
        plan = plans[0]

        filter = TaskStorageAdapter.Filter()
        filter.tid(plan.tid)
        task = self._task_storage.get_tasks(filter)[0]

        for i in range(number):
            task.shift_time(plan.shift)

        return task.get_time_range()

    
    @Controller.require_authentication
    def get_repeats_by_time_range(self, plan_id, time_range, strong=False,
                                  with_exclude=False):
        '''Returns repeats of plan which located insife of time range

        If strong flag is set, only repeats with which located fully inside
        range will be fetched. Otherwise if time range cover repeat time partially
        the repeat will be fetched
        '''

        UserController(self).check_plan_available(self._user_login_id, plan_id)

        plans = self._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return []
        plan = plans[0]

        filter = TaskStorageAdapter.Filter()
        filter.tid(plan.tid)
        task = self._task_storage.get_tasks(filter)[0]

        is_after = task.is_after_time(time_range)
        if not is_after:
            repeats_numbers = []
            number = 0
            while not task.is_after_time(time_range):
                before_end = (plan.end is None 
                    or not task.is_after_time((plan.end, )))
                if not before_end:
                    break

                in_exclude = (not with_exclude 
                    and plan.exclude is not None 
                    and number in plan.exclude)

                if strong:
                    is_overlap = task.is_time_overlap_fully(time_range)
                else:
                    is_overlap = task.is_time_overlap(time_range)

                if is_overlap and not in_exclude:
                    repeats_numbers.append(number)

                number += 1
                task.shift_time(plan.shift)

            return repeats_numbers

        return []

class ProjectController(Controller):
    '''Controller for project

    Manage CRUD and invite and exclide methods for admin and guest
    '''

    _log_tag = 'ProjectController'

    
    @Controller.require_authentication
    def save_project(self, name):
        '''Saves new project
        '''

        exist_projects = self.fetch_projects(name=name)
        if exist_projects is not None and len(exist_projects) != 0:
            return False

        project = Project()
        project.creator = self._user_login_id
        project.name = name
        success = self._project_storage.save_project(project)
        return success

    
    @Controller.require_authentication
    def get_default_project_for_user(self, uid):
        '''Returns default project for user
        '''

        projects = self.fetch_projects()
        for project in projects:
            if project.name == Project.default_project_name:
                return project
        return None

    
    @Controller.require_authentication
    def fetch_projects(self, pid=None, name=None):
        '''Returns projects by specified params
        '''

        projects = self._project_storage.get_projects(self._user_login_id, name, pid)
        return projects

    
    def remove_project_for_user(self, uid, pid):
        '''Removes a project for specified user

        For internal use only
        '''

        default_project = self.get_default_project_for_user(self._user_login_id)
        if default_project is not None and default_project.pid == pid:
            return False

        tasks = TaskController(self).fetch_tasks(pid=pid)
        if tasks is not None:
            for task in tasks:
                TaskController(self).remove_task(task.tid)
        
        success = self._project_storage.remove_project(pid)
        return success

    
    @Controller.require_authentication
    def remove_project(self, pid):
        '''Removes project of authenticated user
        '''

        UserController(self).check_project_available(self._user_login_id, pid, True)
        return self.remove_project_for_user(self._user_login_id, pid)

    
    @Controller.require_authentication
    def edit_project(self, pid, name=Controller._not_edit_field_flag):
        '''Edit project
        '''

        UserController(self).check_project_available(self._user_login_id, pid, True)

        default_project = self.get_default_project_for_user(self._user_login_id)
        if default_project is not None and default_project.pid == pid:
            return False

        args = {Project.Field.pid: pid}
        if name is not Controller._not_edit_field_flag:
            args[Project.Field.name] = name
        success = self._project_storage.edit_project(args)
        return success

    
    @Controller.require_authentication
    def invite_user_to_project(self, pid, uid, admin=False, guest=False):
        '''Invites admin or guest to project

        Action can not be performed is next cases:
        1) user is not exists
        2) project is not exists
        3) trying to invite user which already invited
        4) trying to invite yourself
        '''

        UserController(self).check_project_available(self._user_login_id, pid, True)

        if (admin and guest) or (not admin and not guest):
            return False

        users = UserController(self).fetch_user(uid=uid)
        if users is None or len(users) == 0:
            logging.get_logger(self._log_tag).warning('Trying to invite non-existent user')
            return False

        projects = self.fetch_projects(pid=pid)
        if projects is None or len(projects) == 0:
            logging.get_logger(self._log_tag).warning('Trying to invite into non-existent project')
            return False

        project = projects[0]
        invite_kind = project.get_user_kind(uid)
        if invite_kind is not None:
            logging.get_logger(self._log_tag).warning('Trying to invite user which already invited')
            return False

        if uid == self._user_login_id:
            logging.get_logger(self._log_tag).warning('Trying to invite authenticated user')
            return False

        if admin:
            success = self._project_storage.add_admin_to_project(pid, uid)
            return success

        if guest:
            success = self._project_storage.add_guest_to_project(pid, uid)
            return success

    
    @Controller.require_authentication
    def exclude_user_from_project(self, pid, uid):
        '''Excludes admin or guest from project

        Action can not be performed is next cases:
        1) user is not exists
        2) project is not exists
        3) trying to exclude a participiant by guest
        4) trying to exclude a project creator
        '''

        UserController(self).check_project_available(self._user_login_id, pid)

        users = UserController(self).fetch_user(uid=uid)
        if users is None or len(users) == 0:
            logging.get_logger(self._log_tag).warning('Trying to exclude non-existent user')
            return False

        user_kind = self._project_storage.get_user_kind(pid, uid)
        if user_kind is None:
            logging.get_logger(self._log_tag).warning('Trying to exclude user which not invited')
            return False

        projects = ProjectController(self).fetch_projects(pid=pid)
        if projects is None or len(projects) == 0:
            logging.get_logger(self._log_tag).warning('Trying to exclude from non-existent project')
            return False
        
        project = projects[0]
        current_kind = project.get_user_kind(self._user_login_id)
        if current_kind == Project.UserKind.GUEST and uid != self._user_login_id:
            logging.get_logger(self._log_tag).error(('Trying to exclude a participiant by guest '
                'and this participiant is not himself'))
            raise PermissionDenied
        if project.creator == uid:
            logging.get_logger(self._log_tag).error('Trying to exclude project creator')
            raise PermissionDenied

        if user_kind == Project.UserKind.ADMIN:
            success = self._project_storage.remove_admin_from_project(pid, uid)
        else:
            success = self._project_storage.remove_guest_from_project(pid, uid)
        return success
