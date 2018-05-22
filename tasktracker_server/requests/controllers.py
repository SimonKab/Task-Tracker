from tasktracker_server.model.task import Task, Status, Priority
from tasktracker_server.model.user import User, SuperUser
from tasktracker_server.model.plan import Plan
from tasktracker_server.model.project import Project
from tasktracker_server.storage.sqlite_peewee_adapters import TaskStorageAdapter
from tasktracker_server.storage.sqlite_peewee_adapters import UserStorageAdapter
from tasktracker_server.storage.sqlite_peewee_adapters import PlanStorageAdapter
from tasktracker_server.storage.sqlite_peewee_adapters import ProjectStorageAdapter
import tasktracker_server.utils as utils

import copy
import datetime

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
        msg = 'Invalid parent tid: {}. '.format(parent_tid)
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

class Controller():

    class Validator():

        def run(self):
            for attr in dir(self):
                if attr.startswith('validate_'):
                    method = getattr(self, attr)
                    method()

    _user_login_id = None

    _plan_storage = PlanStorageAdapter()
    _task_storage = TaskStorageAdapter()
    _user_storage = UserStorageAdapter()
    _project_storage = ProjectStorageAdapter()

    _not_edit_field_flag = object()

    @classmethod
    def init_storage_adapters(cls, plan_storage_adapter=None,
                              task_storage_adapter=None,
                              user_storage_adapter=None,
                              _project_storage_adapter=None):
        if plan_storage_adapter is not None:
            cls._plan_storage = plan_storage_adapter()
        if task_storage_adapter is not None:
            cls._task_storage = task_storage_adapter()
        if user_storage_adapter is not None:
            cls._user_storage = user_storage_adapter()

    @classmethod
    def authentication(cls, user_id):
        users = UserController.fetch_user(uid=user_id)
        success = users is not None and len(users) != 0
        if success:
            cls._user_login_id = user_id
        else:
            raise AuthenticationError()
        return success

    @staticmethod
    def require_authentication(method):
        def check(*args, **kwargs):
            if Controller._user_login_id is None:
                raise NotAuthenticatedError()
            return method(*args, **kwargs)
        return check

class TaskController(Controller):

    class TaskValidator(Controller.Validator):

        def __init__(self, task, controller, for_edit=False, force=False):
            self.task = task
            self.controller = controller
            self.for_edit = for_edit
            self.force = force

        def validate_task_time(self):
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
            if self.task.parent_tid == None:
                return

            if self.task.parent_tid == self.task.tid:
                raise InvalidParentIdError(parent_tid)

            filter = TaskStorageAdapter.Filter()
            filter.tid(self.task.parent_tid)
            tasks = self.controller._task_storage.get_tasks(filter)
            if len(tasks) == 0:
                raise InvalidParentIdError(self.task.parent_tid)

            parent_task = tasks[0]

            if self.task.priority is None:
                self.tasks.priority = parent_task.priority

            if self.task.priority != parent_task.priority:
                msg = 'Wrong priority. Parent priority: {}, child \
                    priority: {}'.format(parent_task.priority, self.task.priority)
                raise InvalidParentIdError(self.task.parent_tid, msg)

            if self.task.status is None:
                self.task.status = parent_task.status

            if (parent_task.status == Status.COMPLETED
                    and self.task.status != Status.COMPLETED):
                msg = 'Wrong parent status. Task status has to be completed because parent status is completed'
                raise InvalidParentIdError(self.task.parent_tid, msg)    

            if (parent_task.status == Status.ACTIVE 
                and self.task.status == Status.PENDING):
                msg = 'Wrong parent status. You try to add pending subtask to active task'
                raise InvalidParentIdError(self.task.parent_tid, msg)

            if (parent_task.status == Status.OVERDUE
                and self.task.status != Status.OVERDUE):
                msg = 'Wrong parent status. Task status has to be overdue because parent status is overdue'
                raise InvalidParentIdError(self.task.parent_tid, msg)

            parent_task_time_range = parent_task.get_time_range()
            task_time_range = self.task.get_time_range()
            if len(task_time_range) == 0:
                self.task.supposed_start_time = parent_task.supposed_start_time
                self.task.supposed_end_time = parent_task.supposed_end_time
                self.task.deadline_time = parent_task.deadline_time
            if len(parent_task_time_range) == 2:
                if not self.task.is_task_inside_of_range(parent_task_time_range):
                    msg = 'Wrong time. Child task time is wider than parent'
                    raise InvalidParentIdError(self.task.parent_tid, msg)
            if len(parent_task_time_range) == 1:
                if len(task_time_range) == 2:
                    msg = 'Wrong time. Child task time is wider than parent'
                    raise InvalidParentIdError(self.task.parent_tid, msg)
                if len(task_time_range) == 1:
                    if task_time_range != parent_task_time_range:
                        msg = 'Wrong time. Child task time is wider than parent'
                        raise InvalidParentIdError(self.task.parent_tid, msg)    

            planned = PlanController.is_task_planned(self.task.parent_tid)
            if planned:
                msg = 'Parent can not be planned'
                raise InvalidParentIdError(self.task.parent_tid, msg)

        def validate_status_time_relations(self):

            if self.force:
                return

            today = utils.datetime_to_milliseconds(utils.today())
            task_time_range = self.task.get_time_range()
            if len(task_time_range) != 0:
                if (self.task.is_before_time((today, ))
                    and not self.task.only_start()):
                    if (self.task.status == Status.PENDING
                        or self.task.status == Status.ACTIVE):
                        msg = ('Wrong status. You can not set status as pending '
                            'or active if task is in the past')
                        raise InvalidStatusError(Status.to_str(self.task.status), msg)
                else:
                    if self.task.status == Status.OVERDUE:
                        msg = ('Wrong status. You can not set status as overdue'
                            'if task is not in the past')
                        raise InvalidStatusError(Status.to_str(self.task.status), msg)

        def validate_plan_edit_task(self):

            plans = PlanController.get_plan_for_edit_repeat_task(self.task.tid)
            if plans is not None and len(plans) != 0:
                raise EditPlanRepeatEditTaskError()

    @classmethod
    @Controller.require_authentication
    def save_task(cls,
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

        task = Task()
        if task_id >= 0:
            task.tid = task_id
        task.uid = cls._user_login_id
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

        validator = cls.TaskValidator(task, cls)
        validator.run()

        success = cls._task_storage.save_task(task)
        return success

    @classmethod
    @Controller.require_authentication
    def get_task_with_notifications_to_time(cls, time):
        filter = cls._task_storage.Filter()
        filter.uid(cls._user_login_id)
        filter.one_of_notificate()
        filter.to_time(time)
        filter.not_completed()
        tasks = cls._task_storage.get_tasks(filter)

        return tasks

    @classmethod
    @Controller.require_authentication
    def get_overdue_tasks(cls, time):
        filter = cls._task_storage.Filter()
        filter.uid(cls._user_login_id)
        filter.to_time(time)
        filter.status(Status.OVERDUE)
        tasks = cls._task_storage.get_tasks(filter)
        return tasks

    @classmethod
    @Controller.require_authentication
    def find_overdue_tasks(cls, time):
        filter = cls._task_storage.Filter()
        filter.uid(cls._user_login_id)
        filter.overdue_by_time(time)
        tasks = cls._task_storage.get_tasks(filter)
        for task in tasks:
            plans = PlanController.get_plan_for_common_task(task.tid)
            if plans is not None and len(plans) != 0:
                for plan in plans:
                    time_range = (task.get_left_border(), time)
                    plan_repeats = PlanController.get_repeats_by_time_range(plan.plan_id, time_range)
                    for repeat in plan_repeats:
                        PlanController.edit_repeat_by_number(plan.plan_id, repeat, status=Status.OVERDUE)
                return

            edit_plans = PlanController.get_plan_for_edit_repeat_task(task.tid)
            if edit_plans is not None and len(edit_plans) != 0:
                for plan in edit_plans:
                    repeat = PlanController.get_repeat_number_for_task(task)
                    PlanController.edit_repeat_by_number(plan.plan_id, repeat, status=Status.OVERDUE)
                return
            
            print(task.tid)
            cls.edit_task(task.tid, status=Status.OVERDUE)

    @classmethod
    @Controller.require_authentication
    def fetch_tasks(cls, parent_tid=None, tid=None, title=None, description=None,
                        priority=None, status=None, notificate_supposed_start=None, 
                        notificate_supposed_end=None, notificate_deadline=None, 
                        time_range=None, timeless=None):
        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        filter = cls._task_storage.Filter()
        filter.uid(cls._user_login_id)
        if tid is not None:
            filter.tid(tid)
        if parent_tid is not None:
            filter.parent_tid(parent_tid)
        if title is not None:
            filter.title(title)
        if description is not None:
            filter.description(description)
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
            filter.filter_range(*time_range)
        if timeless:
            filter.timeless()

        tasks = cls._task_storage.get_tasks(filter)
        if time_range is None:
            reverse_task = tasks[::-1]
            for i in range(len(reverse_task)):
                task = reverse_task[i]
                plans = PlanController.get_plan_for_common_task(task.tid)
                if plans is not None and len(plans) != 0:
                    tasks.remove(task)
                    tasks.append(cls.get_most_valuable_task(plans[0].plan_id))

        if time_range is not None:
            plans = PlanController.get_plans_by_time_range(time_range)
            plan_tid_ids = []
            for plan in plans:
                if plan.tid in plan_tid_ids:
                    continue
                plan_tid_ids.append(plan.tid)
                plan_tasks = cls.get_plan_tasks_by_time_range(plan.plan_id, time_range)
                if tasks is None:
                    tasks = []
                tasks.extend(plan_tasks)
        return tasks

    @classmethod
    @Controller.require_authentication
    def get_most_valuable_task(cls, plan_id):
        number = 0
        while True:
            tasks = cls.get_plan_tasks_by_numbers(plan_id, [number])
            if tasks is None or len(tasks) == 0:
                return None
            if tasks[0].status != Status.OVERDUE:
                return tasks[0]
            number += 1

    @classmethod
    @Controller.require_authentication
    def get_plan_tasks_by_time_range(cls, plan_id, time_range):
        numbers = PlanController.get_repeats_by_time_range(plan_id, time_range)
        if numbers is None:
            return []

        return cls.get_plan_tasks_by_numbers(plan_id, numbers)

    @classmethod
    @Controller.require_authentication
    def get_plan_tasks_by_numbers(cls, plan_id, numbers):
        plans = cls._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return []
        plan = plans[0]

        filter = cls._task_storage.Filter()
        filter.tid(plan.tid)
        tasks = cls._task_storage.get_tasks(filter)
        if tasks is None or len(tasks) == 0:
            return []
        task = tasks[0]

        result_tasks = []

        if plan.exclude is not None:
            numbers = list(numbers)
            plan_controller = PlanController()
            for exclude_number in plan.exclude:
                if exclude_number in numbers:
                    numbers.remove(exclude_number)
                    tid = plan_controller.get_tid_for_edit_repeat(plan.plan_id, exclude_number)
                    if tid is not None:
                        edit_tasks = cls.fetch_tasks(tid=tid)
                        if edit_tasks is not None and len(edit_tasks) != 0:
                            result_tasks.append(edit_tasks[0])

        shift_time_array = []
        for number in numbers:
            allowable = PlanController.is_allowable_repeat(number, plan, task)
            if allowable:
                shift_time_array.append(plan.shift*number)

        for shift_time in shift_time_array:
            new_task = copy.deepcopy(task)
            new_task.shift_time(shift_time)
            result_tasks.append(new_task)

        return result_tasks

    @classmethod
    @Controller.require_authentication
    def remove_task(cls, task_id):
        cls._task_storage.connect()
        success = cls._task_storage.remove_task(task_id)
        cls._task_storage.disconnect()
        return success

    @classmethod
    @Controller.require_authentication
    def edit_task(cls, task_id, parent_tid=Controller._not_edit_field_flag, 
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

        filter = TaskStorageAdapter.Filter()
        filter.tid(task_id)
        tasks = cls._task_storage.get_tasks(filter)
        if tasks is None or len(tasks) == 0:
            return False
        task = tasks[0]

        if supposed_start_time != -1 or supposed_end_time != -1 or deadline_time != -1:
            plan_controller = PlanController()
            plans = plan_controller.get_plan_for_common_task(task_id)
            for plan in plans:
                success = plan_controller.restore_all_repeats(plan.plan_id)      
                if not success:
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
        childer = cls._task_storage.get_tasks(filter)

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

        task_validator = cls.TaskValidator(task, cls, force=force)
        task_validator.run()

        success = cls._task_storage.edit_task_from_model(task)
        if success:
            for child in childer:
                if status is not Controller._not_edit_field_flag:
                    cls.edit_task(child.tid, status=status)
                if priority is not Controller._not_edit_field_flag:
                    cls.edit_task(child.tid, priority=priority)
        return success

class UserController(Controller):

    @classmethod
    def save_user(cls, login=None, user_id=-1):
        if user_id is None:
            user_id = -1

        user = User()
        if user_id >= 0:
            user.user_id = user_id
        user.login = login

        exists = cls._user_storage.check_user_existence(login)
        if not exists:
            ProjectCon
            success = cls._user_storage.save_user(user)
            return success
        else:
            raise UserAlreadyExistsError(login)

    @classmethod
    def fetch_user(cls, uid=None, login=None, online=None):
        filter = UserStorageAdapter.Filter()
        if uid is not None:
            filter.uid(uid)
        if login is not None:
            filter.login(login)
        if online is not None:
            filter.online(online)

        users = cls._user_storage.get_users(filter)
        return users

    @classmethod
    def delete_user(cls, user_id):
        success = cls._user_storage.delete_user(user_id)
        return success

    @classmethod
    def edit_user(cls, user_id, login=-1, online=-1):
        user_field_dict = {User.Field.uid: user_id}
        if login is not -1:
            user_field_dict[User.Field.login] = login
        if online is not -1:
            user_field_dict[User.Field.online] = online

        if login is not -1 and login is not None:
            exists = cls._user_storage.check_user_existence(login)
            if not exists:
                raise UserNotExistsError(login)

        success = cls._user_storage.edit_user(user_field_dict)
        return success

class PlanController(Controller):

    @classmethod
    @Controller.require_authentication
    def attach_plan(cls, tid, shift, end=None):
        task = TaskController.fetch_tasks(tid=tid)[0]
        if len(task.get_time_range()) == 0:
            return False
        if task.parent_tid is not None:
            return False
        child_taks = TaskController.fetch_tasks(parent_tid=tid)
        if child_taks is not None and len(child_taks) != 0:
            return False

        plan = Plan()
        plan.tid = tid
        plan.shift = shift
        plan.end = end
        success = cls._plan_storage.save_plan(plan)
        return success

    @classmethod
    @Controller.require_authentication
    def edit_plan(cls, plan_id, shift=Controller._not_edit_field_flag, 
                end=Controller._not_edit_field_flag):
        attr = {Plan.Field.plan_id: plan_id}
        if shift is not Controller._not_edit_field_flag:
            attr[Plan.Field.shift] = shift
        if end is not Controller._not_edit_field_flag:
            attr[Plan.Field.end] = end
        success = cls._plan_storage.edit_plan(attr)
        return success

    @classmethod
    @Controller.require_authentication
    def shift_start(cls, plan_id, shift_time):
        success = cls._plan_storage.recalculate_exclude_when_start_time_shifted(plan_id, shift_time)
        return success

    @classmethod
    @Controller.require_authentication
    def edit_repeat_by_number(cls, plan_id, number, 
                              status=Controller._not_edit_field_flag, 
                              priority=Controller._not_edit_field_flag, 
                              notificate_supposed_start=Controller._not_edit_field_flag, 
                              notificate_supposed_end=Controller._not_edit_field_flag, 
                              notificate_deadline=Controller._not_edit_field_flag):
        
        plans = cls._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return False
        plan = plans[0]

        task_controller = TaskController()
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

        tid = cls.get_tid_for_edit_repeat(plan.plan_id, number)
        if tid is not None:
            success = cls._task_storage.remove_task(tid)
            if not success:
                return False

        success = cls._task_storage.save_task(task)
        if not success:
            return False

        edited_task = cls._task_storage.get_last_saved_task()

        success = cls._plan_storage.edit_plan_repeat(plan.plan_id, number, edited_task.tid)
        return success

    @classmethod
    @Controller.require_authentication
    def is_task_planned(cls, tid):
        plans = cls.get_plan_for_common_task(tid)
        edit_plans = cls.get_plan_for_edit_repeat_task(tid)
        plans += edit_plans
        return plans is not None and len(plans) != 0

    @classmethod
    @Controller.require_authentication
    def delete_repeats_from_plan_by_number(cls, plan_id, number):
        edit_tid = cls.get_tid_for_edit_repeat(plan_id, number)
        type = cls._plan_storage.get_exclude_type(plan_id, number)
        if type == Plan.PlanExcludeKind.DELETED:
            return True
        if edit_tid is not None:
            task_controller = TaskController()
            task_controller.remove_task(edit_tid)
        success = cls._plan_storage.delete_plan_repeat(plan_id, number)
        return success

    @classmethod
    @Controller.require_authentication
    def delete_repeats_from_plan_by_time_range(cls, plan_id, time_range):
        repeats = cls.get_repeats_by_time_range(plan_id, time_range, with_exclude=True)
        if repeats is None:
            return False

        for number in repeats:
            success = cls.delete_repeats_from_plan_by_number(plan_id, number)
            if not success:
                return False

        return True

    @classmethod
    @Controller.require_authentication
    def delete_plan(cls, plan_id):
        success = cls._plan_storage.remove_plan(plan_id)
        return success

    @classmethod
    @Controller.require_authentication
    def restore_all_repeats(cls, plan_id):
        success = cls._plan_storage.restore_all_repeats(plan_id)
        return success

    @classmethod
    @Controller.require_authentication
    def restore_repeat(cls, plan_id, number):
        success = cls._plan_storage.restore_repeat(plan_id, number)
        return success

    @classmethod
    @Controller.require_authentication
    def restore_repeats_in_time_range(cls, plan_id, time_range):
        repeats = cls.get_repeats_by_time_range(time_range)
        if repeats is None:
            return False

        for number in repeats:
            success = cls.restore_repeat(plan_id, number)
            if not success:
                return False

        return True

    @classmethod
    @Controller.require_authentication
    def get_plan_for_common_task(cls, common_tid):
        plans = cls._plan_storage.get_plans(common_tid=common_tid)
        return plans

    @classmethod
    @Controller.require_authentication
    def get_plan_for_edit_repeat_task(cls, edit_repeat_tid):
        plans = cls._plan_storage.get_plans(edit_repeat_tid=edit_repeat_tid)
        return plans

    @classmethod
    @Controller.require_authentication
    def get_exclude_type(cls, plan_id, number):
        exclude_type = cls._plan_storage.get_exclude_type(plan_id, number)
        return exclude_type

    @classmethod
    @Controller.require_authentication
    def get_tid_for_edit_repeat(cls, plan_id, number):
        tid = cls._plan_storage.get_tid_for_edit_repeat(plan_id, number)
        return tid

    @classmethod
    @Controller.require_authentication
    def get_plans_by_id(cls, plan_id):
        plans = cls._plan_storage.get_plans(plan_id=plan_id)
        return plans

    @classmethod
    @Controller.require_authentication
    def get_plans_by_time_range(cls, time_range):
        plans = cls._plan_storage.get_plans()
        if plans is None:
            return []

        result_plans = []
        for plan in plans:
            repeats = cls.get_repeats_by_time_range(plan.plan_id, time_range)
            if repeats is not None and len(repeats) > 0:
                result_plans.append(plan)
        return result_plans

    @classmethod
    @Controller.require_authentication
    def get_repeat_number_for_task(cls, plan_id, task):
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

        repeats = cls.get_repeats_by_time_range(plan_id, (start, end), True, True)
        if len(repeats) == 0:
            return None
        return repeats[0]

    @staticmethod
    def is_allowable_repeat(number, plan, task):
        temp_task = copy.deepcopy(task)
        temp_task.shift_time(number*plan.shift)

        before_end = (plan.end is None 
            or not temp_task.is_after_time((plan.end, )))

        in_exclude = (plan.exclude is not None and 
            number in plan.exclude)

        return before_end and not in_exclude

    @classmethod
    @Controller.require_authentication
    def get_repeats_by_time_range(cls, plan_id, time_range, strong=False,
                                  with_exclude=False):
        plans = cls._plan_storage.get_plans(plan_id=plan_id)
        if plans is None or len(plans) == 0:
            return []
        plan = plans[0]

        filter = TaskStorageAdapter.Filter()
        filter.tid(plan.tid)
        task = cls._task_storage.get_tasks(filter)[0]

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

    def add_project(name):


def timestamp_to_display(timestamp):
    if timestamp is not None:
        return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y')
