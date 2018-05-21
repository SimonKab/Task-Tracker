from tasktracker_server.model.task import Task, Status, Priority
from tasktracker_server.model.user import User, SuperUser
from tasktracker_server.model.plan import Plan
from tasktracker_server.storage.sqlite_peewee_adapters import TaskStorageAdapter, UserStorageAdapter, PlanStorageAdapter

import copy
import datetime

class InvalidTimeError(Exception):

    def __init__(self, start, end):
        super().__init__('Invalid time range')
        self.start = start
        self.end = end

class InvalidParentId(Exception):

    def __init__(self, parent_tid):
        super().__init__('Invalid parent tid: {}'.format(parent_tid))
        self.parent_tid = parent_tid

class UserAlreadyExistsError(Exception):

    def __init__(self, user_name):
        super().__init__('User with name {} already exists'.format(user_name))
        self.user_name = user_name

class UserNotExistsError(Exception):

    def __init__(self, user_name):
        super().__init__('User with name {} is not exist'.format(user_name))
        self.user_name = user_name

class NotAuthenticatedError(Exception):

    def __init__(self, user_name):
        super().__init__('User was not authenticated')

class Controller():

    _user_login_id = None

    _plan_storage = PlanStorageAdapter()
    _task_storage = TaskStorageAdapter()
    _user_storage = UserStorageAdapter()

    _not_edit_field_flag = object()

    @classmethod
    def init_storage_adapters(cls, plan_storage_adapter=None,
                              task_storage_adapter=None,
                              user_storage_adapter=None):
        if plan_storage_adapter is not None:
            cls._plan_storage = plan_storage_adapter()
        if task_storage_adapter is not None:
            cls._task_storage = task_storage_adapter()
        if user_storage_adapter is not None:
            cls._user_storage = user_storage_adapter()

    # def __init__(self, login):
    #     authentication(login)

    def authentication(cls, login):
        if isinstance(login, SuperUser):
            _user_login_id = login.uid
            return True

        users = UserController.fetch_user()
        for user in users:
            if user.login == login:
                _user_login_id = user.uid
                return True

        return False

class TaskController(Controller):

    @classmethod
    def save_task(cls, 
                  uid, 
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

        # loose connection in failed validation

        cls._task_storage.connect()

        cls.validate_task_time(supposed_start, supposed_end, deadline_time)
        cls.validate_parent_tid(parent_tid)

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

        # TODO: validation
        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        task = Task()
        if task_id >= 0:
            task.tid = task_id
        task.uid = uid
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

        success = cls._task_storage.save_task(task)
        cls._task_storage.disconnect()
        return success

    @classmethod
    def fetch_tasks(cls, uid=None, parent_tid=None, tid=None, title=None, description=None,
                        priority=None, status=None, notificate_supposed_start=None, 
                        notificate_supposed_end=None, notificate_deadline=None, time_range=None):
        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        filter = cls._task_storage.Filter()
        if uid is not None:
            filter.uid(uid)
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

        tasks = cls._task_storage.get_tasks(filter)
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
    def get_plan_tasks_by_time_range(cls, plan_id, time_range):
        numbers = PlanController.get_repeats_by_time_range(plan_id, time_range)
        if numbers is None:
            return []

        return cls.get_plan_tasks_by_numbers(plan_id, numbers)

    @classmethod
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
                        result_tasks.append(cls.fetch_tasks(tid=tid)[0])

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
    def remove_task(cls, task_id):
        cls._task_storage.connect()
        success = cls._task_storage.remove_task(task_id)
        cls._task_storage.disconnect()
        return success

    @classmethod
    def edit_task(cls, task_id, parent_tid=-1, title=-1, description=-1,
                    supposed_start_time=-1, supposed_end_time=-1, deadline_time=-1,
                    priority=-1, status=-1, notificate_supposed_start=-1, 
                    notificate_supposed_end=-1, notificate_deadline=-1):
        
        plan_controller = PlanController()
        plans = plan_controller.get_plan_for_common_task(task_id)
        # not status validation

        if parent_tid != -1:
            cls.validate_parent_tid(parent_tid, task_id)

        if supposed_start_time != -1 or supposed_end_time != -1 or deadline_time != -1:
            filter = TaskStorageAdapter.Filter()
            filter.tid(task_id)
            task = cls._task_storage.get_tasks(filter)[0]
            temp_start_time = supposed_start_time
            temp_end_time = supposed_end_time
            temp_deadline = deadline_time
            if temp_start_time == -1:
                temp_start_time = task.supposed_start_time
            if temp_end_time == -1:
                temp_end_time = task.supposed_end_time
            if deadline_time == -1:
                temp_deadline = task.deadline_time

            cls.validate_task_time(temp_start_time, temp_end_time, temp_deadline)

            for plan in plans:
                success = plan_controller.restore_all_repeats(plan.plan_id)      
                if not success:
                    return False      

        # TODO: validation
        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        if status is None:
            status = Status.PENDING

        if priority is None:
            priority = Priority.NORMAL

        if status is not -1:
            filter = TaskStorageAdapter.Filter()
            filter.parent_tid(task_id)
            tasks = cls._task_storage.get_tasks(filter)
            for task in tasks:
                cls.edit_task(task.tid, status=status)

        task_field_dict = {Task.Field.tid: task_id}
        if parent_tid is not -1:
            task_field_dict[Task.Field.parent_tid] = parent_tid
        if title is not -1:
            task_field_dict[Task.Field.title] = title
        if description is not -1:
            task_field_dict[Task.Field.description] = description
        if supposed_start_time is not -1:
            task_field_dict[Task.Field.supposed_start_time] = supposed_start_time
        if supposed_end_time is not -1:
            task_field_dict[Task.Field.supposed_end_time] = supposed_end_time
        if deadline_time is not -1:
            task_field_dict[Task.Field.deadline_time] = deadline_time
        if parent_tid is not -1:
            task_field_dict[Task.Field.parent_tid] = parent_tid
        if priority is not -1:
            task_field_dict[Task.Field.priority] = priority
        if status is not -1:
            task_field_dict[Task.Field.status] = status
        if notificate_supposed_start is not -1:
            task_field_dict[Task.Field.notificate_supposed_start] = notificate_supposed_start
        if notificate_supposed_end is not -1:
            task_field_dict[Task.Field.notificate_supposed_end] = notificate_supposed_end
        if notificate_deadline is not -1:
            task_field_dict[Task.Field.notificate_deadline] = notificate_deadline

        success = cls._task_storage.edit_task(task_field_dict)
        cls._task_storage.disconnect()
        return success

    @classmethod
    def validate_time(cls, start, end):
        def is_first_bigger(first, second):
            if first == None or second == None:
                return False
            return first > second

        if start != -1 and end != -1:
            if is_first_bigger(start, end):
                raise InvalidTimeError(start_time, end_time)

    @classmethod
    def validate_task_time(cls, start_time, end_time, deadline_time):
        cls.validate_time(start_time, end_time)
        cls.validate_time(end_time, deadline_time)
        cls.validate_time(start_time, deadline_time)

    @classmethod
    def validate_parent_tid(cls, parent_tid, child_tid=-1):
        if parent_tid == None:
            return

        if parent_tid == child_tid:
            raise InvalidParentId(parent_tid)

        filter = TaskStorageAdapter.Filter()
        filter.tid(parent_tid)
        tasks = cls._task_storage.get_tasks(filter)
        if len(tasks) == 0:
            raise InvalidParentId(parent_tid)

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

        success = cls._user_storage.get_users(filter)
        return success

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

    @classmethod
    def login_user(cls, user_name):
        return cls._change_user_state(user_name, True)

    @classmethod
    def logout_user(cls, user_name):
        return cls._change_user_state(user_name, False)

    @classmethod
    def _change_user_state(cls, user_name, online):
        users_with_name = cls.fetch_user(login = user_name)
        if len(users_with_name) == 0:
            raise UserNotExistsError(user_name)

        for user in users_with_name:
            success = cls.edit_user(user_id = user.uid, online = online)
            if not success:
                return False
        return True

class PlanController(Controller):

    @classmethod
    def attach_plan(cls, tid, shift, end=None):
        plan = Plan()
        plan.tid = tid
        plan.shift = shift
        plan.end = end
        success = cls._plan_storage.save_plan(plan)
        return success

    @classmethod
    def edit_plan(cls, plan_id, shift=None, end=None):
        success = cls._plan_storage.edit_plan(plan_id, end, shift)
        return success

    @classmethod
    def shift_start(cls, plan_id, shift_time):
        success = cls._plan_storage.recalculate_exclude_when_start_time_shifted(plan_id, shift_time)
        return success

    @classmethod
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
    def is_task_planned(cls, tid):
        plans = cls._plan_storage.get_plans(common_tid=tid)
        return plans is not None and len(plans) != 0

    @classmethod
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
    def delete_plan(cls, plan_id):
        success = cls._plan_storage.remove_plan(plan_id)
        return success

    @classmethod
    def restore_all_repeats(cls, plan_id):
        success = cls._plan_storage.restore_all_repeats(plan_id)
        return success

    @classmethod
    def restore_repeat(cls, plan_id, number):
        success = cls._plan_storage.restore_repeat(plan_id, number)
        return success

    @classmethod
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
    def get_plan_for_common_task(cls, common_tid):
        plans = cls._plan_storage.get_plans(common_tid=common_tid)
        return plans

    @classmethod
    def get_plan_for_edit_repeat_task(cls, edit_repeat_tid):
        plans = cls._plan_storage.get_plans(edit_repeat_tid=edit_repeat_tid)
        return plans

    @classmethod
    def get_exclude_type(cls, plan_id, number):
        exclude_type = cls._plan_storage.get_exclude_type(plan_id, number)
        return exclude_type

    @classmethod
    def get_tid_for_edit_repeat(cls, plan_id, number):
        tid = cls._plan_storage.get_tid_for_edit_repeat(plan_id, number)
        return tid

    @classmethod
    def get_plans_by_id(cls, plan_id):
        plans = cls._plan_storage.get_plans(plan_id=plan_id)
        return plans

    @classmethod
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

        # check if start and end not None

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

def timestamp_to_display(timestamp):
    if timestamp is not None:
        return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y')
