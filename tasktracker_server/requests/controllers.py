from tasktracker_server.model.task import Task, Status, Priority
from tasktracker_server.model.user import User
from tasktracker_server.model.plan import Plan
from tasktracker_server.storage.sqlite_peewee_adapters import TaskStorageAdapter, UserStorageAdapter, PlanStorageAdapter
from tasktracker_server import console_response

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

class TaskController():

    _task_storage = TaskStorageAdapter()
    _plan_storage = PlanStorageAdapter()

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
    def add_plan(cls, tid, start=None, end=None, shift=None, exclude=None):        
        cls.validate_time(start, end)

        cls._plan_storage.connect()

        plan = Plan()
        plan.tid = tid
        plan.start = start
        plan.end = end
        plan.shift = shift
        plan.exclude = exclude

        success = cls._plan_storage.save_plan(plan)
        cls._plan_storage.disconnect()
        return success

    @classmethod
    def remove_plan(cls, plan_id):
        cls._plan_storage.connect()
        success = cls._plan_storage.remove_plan(plan_id)
        cls._task_storage.disconnect()
        return success

    @classmethod
    def edit_plan(cls, plan_id, start=-1, end=-1, shift=-1, exclude=-1):
        cls._plan_storage.connect()

        plan_field_dict = {Plan.Field.plan_id: plan_id}
        if start is not -1:
            plan_field_dict[Plan.Field.start] = start
        if end is not -1:
            plan_field_dict[Plan.Field.end] = end
        if shift is not -1:
            plan_field_dict[Plan.Field.shift] = shift
        if exclude is not -1:
            plan_field_dict[Plan.Field.exclude] = exclude

        success = cls._plan_storage.edit_plan(plan_field_dict)
        cls._plan_storage.disconnect()
        return success

    @classmethod
    def fetch_plans(cls, tid=None, time_range=None):
        cls._plan_storage.connect()
        plans = cls._plan_storage.get_plans(tid, time_range)
        cls._plan_storage.disconnect()
        return plans

    @classmethod
    def fetch_tasks(cls, uid=None, parent_tid=None, tid=None, title=None, description=None,
                        priority=None, status=None, notificate_supposed_start=None, 
                        notificate_supposed_end=None, notificate_deadline=None, time_range=None):
        if isinstance(priority, str):
            priority = Priority.from_str(priority)
        if isinstance(status, str):
            status = Status.from_str(status)

        filter = TaskStorageAdapter.Filter()
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

        cls._task_storage.connect()
        tasks = cls._task_storage.get_tasks(filter)
        cls._task_storage.disconnect()
        return tasks

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
        
        cls._task_storage.connect()

        if parent_tid != -1:
            cls.validate_parent_tid(parent_tid, task_id)

        if supposed_start_time == -1 or supposed_end_time == -1 or deadline_time == -1:
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
                deadline_time = task.deadline_time
            cls.validate_task_time(temp_start_time, temp_end_time, temp_deadline)

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

class UserController():

    _storage_adapter = UserStorageAdapter()

    @classmethod
    def save_user(cls, login=None, user_id=-1):
        if user_id is None:
            user_id = -1

        user = User()
        if user_id >= 0:
            user.user_id = user_id
        user.login = login

        cls._storage_adapter.connect()
        exists = cls._storage_adapter.check_user_existence(login)
        if not exists:
            success = cls._storage_adapter.save_user(user)
            cls._storage_adapter.disconnect()
            return success
        else:
            cls._storage_adapter.disconnect()
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

        cls._storage_adapter.connect()
        success = cls._storage_adapter.get_users(filter)
        cls._storage_adapter.disconnect()
        return success

    @classmethod
    def delete_user(cls, user_id):
        cls._storage_adapter.connect()
        success = cls._storage_adapter.delete_user(user_id)
        cls._storage_adapter.disconnect()
        return success

    @classmethod
    def edit_user(cls, user_id, login=-1, online=-1):
        user_field_dict = {User.Field.uid: user_id}
        if login is not -1:
            user_field_dict[User.Field.login] = login
        if online is not -1:
            user_field_dict[User.Field.online] = online

        cls._storage_adapter.connect()

        if login is not -1 and login is not None:
            exists = cls._storage_adapter.check_user_existence(login)
            if not exists:
                cls._storage_adapter.disconnect()
                raise UserNotExistsError(login)

        success = cls._storage_adapter.edit_user(user_field_dict)
        cls._storage_adapter.disconnect()
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

class PlanController():

    _plan_storage = PlanStorageAdapter()
    _task_storage = TaskStorageAdapter()

    @classmethod
    def attach_plan(cls, tid, shift, end=None):
        cls._plan_storage.connect()
        plan = Plan()
        plan.tid = tid
        plan.shift = shift
        plan.end = end
        success = cls._plan_storage.save_plan(plan)
        cls._plan_storage.disconnect()
        return success

    @classmethod
    def delete_repeats_from_plan_by_number(cls, plan_id, number):
        cls._plan_storage.connect()
        success = cls._plan_storage.delete_plan_repeat(plan_id, number)
        cls._plan_storage.disconnect()
        return success

    @classmethod
    def delete_repeats_from_plan_by_time_range(cls, plan_id, time_range):
        cls._plan_storage.connect()
        cls._task_storage.connect()
        plan = cls._storage_adapter.get_plans(plan_id=plan_id)
        
        filter = TaskStorageAdapter.Filter()
        filter.tid(plan.tid)
        tasks = cls._task_storage.get_tasks(filter)