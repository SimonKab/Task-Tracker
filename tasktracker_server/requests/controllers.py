from tasktracker_server.model.task import Task
from tasktracker_server.model.user import User
from tasktracker_server.storage.sqlite_peewee_adapters import TaskStorageAdapter, UserStorageAdapter
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

    _storage_adapter = TaskStorageAdapter()

    @classmethod
    def save_task(cls, uid, parent_tid=None, title=None, description=None, supposed_start=None, 
        supposed_end=None, deadline_time=None, task_id=-1):
        if task_id is None:
            task_id = -1

        cls._storage_adapter.connect()

        cls.validate_time(supposed_start, supposed_end, deadline_time)
        cls.validate_parent_tid(parent_tid)

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

        success = cls._storage_adapter.save_task(task)
        cls._storage_adapter.disconnect()
        return success

    @classmethod
    def fetch_tasks(cls, uid=None, parent_tid=None, tid=None, title=None, description=None):
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

        cls._storage_adapter.connect()
        tasks = cls._storage_adapter.get_tasks(filter)
        cls._storage_adapter.disconnect()
        return tasks

    @classmethod
    def remove_task(cls, task_id):
        cls._storage_adapter.connect()
        success = cls._storage_adapter.remove_task(task_id)
        cls._storage_adapter.disconnect()
        return success

    @classmethod
    def edit_task(cls, task_id, parent_tid=-1, title=-1, description=-1,
                    supposed_start_time=-1, supposed_end_time=-1, deadline_time=-1):
        
        cls._storage_adapter.connect()

        cls.validate_time(supposed_start_time, supposed_end_time, deadline_time)
        cls.validate_parent_tid(parent_tid)

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

        success = cls._storage_adapter.edit_task(task_field_dict)
        cls._storage_adapter.disconnect()
        return success

    @staticmethod
    def validate_time(start_time, end_time, deadline_time):
        def is_first_bigger(first, second):
            if first == None or second == None:
                return False
            return first > second

        if is_first_bigger(start_time, end_time):
            raise InvalidTimeError(start_time, end_time)
        if is_first_bigger(end_time, deadline_time):
            raise InvalidTimeError(end_time, deadline_time)
        if is_first_bigger(start_time, deadline_time):
            raise InvalidTimeError(start_time, deadline_time)

    @classmethod
    def validate_parent_tid(cls, parent_tid):
        filter = TaskStorageAdapter.Filter()
        filter.tid(parent_tid)
        tasks = cls._storage_adapter.get_tasks(filter)
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