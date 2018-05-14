from ..model.task import Task
from ..model.user import User
from ..model.plan import Plan
import os
from itertools import filterfalse
from peewee import *

class TidAlreadyExistsError(Exception):

    def __init__(self, tid):
        message = 'Tid {} already exists'.format(tid)
        super().__init__(message)

class TidNotExistsError(Exception):

    def __init__(self, tid):
        message = 'Tid {} not exists'.format(tid)
        super().__init__(message)

_db_proxy = Proxy()

class BaseTableModel(Model):

    class Meta:
        database = _db_proxy

class UserTableModel(BaseTableModel):
    uid = IntegerField(primary_key=True)
    login = TextField(null=True)
    password = TextField(null=True)
    online = BooleanField(null=True)

    def map_user_attr(self, user_field, value):
        if user_field == User.Field.uid:
            self.uid = value
        if user_field == User.Field.login:
            self.login = value
        if user_field == User.Field.password:
            self.password = value
        if user_field == User.Field.online:
            self.online = value

    def to_user(self):
        user = User()
        user.uid = self.uid
        user.login = self.login
        user.password = self.password
        user.online = self.online
        return user

    class Meta:
        table_name = 'user'

class TaskTableModel(BaseTableModel):
    tid = IntegerField(primary_key=True)
    uid = ForeignKeyField(UserTableModel, backref='tasks', null=True)
    title = TextField(null=True)
    description = TextField(null=True)
    supposed_start_time = IntegerField(null=True)
    supposed_end_time = IntegerField(null=True)
    deadline_time = IntegerField(null=True)
    parent_tid = IntegerField(null=True)
    priority = IntegerField(null=True)
    status = IntegerField(null=True)
    notificate_supposed_start = BooleanField()
    notificate_supposed_end = BooleanField()
    notificate_deadline = BooleanField()
    plan_tid = IntegerField(null=True)

    def map_task_attr(self, task_field, value):
        if task_field == Task.Field.tid:
            self.tid = value
        if task_field == Task.Field.parent_tid:
            self.parent_tid = value
        if task_field == Task.Field.uid:
            self.uid = value
        if task_field == Task.Field.title:
            self.title = value
        if task_field == Task.Field.description:
            self.description = value
        if task_field == Task.Field.supposed_start_time:
            self.supposed_start_time = value
        if task_field == Task.Field.supposed_end_time:
            self.supposed_end_time = value
        if task_field == Task.Field.deadline_time:
            self.deadline_time = value
        if task_field == Task.Field.priority:
            self.priority = value
        if task_field == Task.Field.status:
            self.status = value
        if task_field == Task.Field.notificate_supposed_start:
            self.notificate_supposed_start = value
        if task_field == Task.Field.notificate_supposed_end:
            self.notificate_supposed_end = value
        if task_field == Task.Field.notificate_deadline:
            self.notificate_deadline = value

    def to_task(self):
        task = Task()
        task.tid = self.tid
        task.parent_tid = self.parent_tid
        userTableModel = self.uid
        if userTableModel is not None:
            task.uid = userTableModel.uid
        task.title = self.title
        task.description = self.description
        task.supposed_start_time = self.supposed_start_time
        task.supposed_end_time = self.supposed_end_time
        task.deadline_time = self.deadline_time
        task.priority = self.priority
        task.status = self.status
        task.notificate_supposed_start = self.notificate_supposed_start
        task.notificate_supposed_end = self.notificate_supposed_end
        task.notificate_deadline = self.notificate_deadline
        return task

    class Meta:
        table_name = 'task'

class PlanTableModel(BaseTableModel):
    plan_id = AutoField(primary_key=True)
    start = IntegerField(null=False)
    end = IntegerField(null=True)
    shift = IntegerField(null=False)

    def map_plan_attr(self, plan_field, value):
        if plan_field == Plan.Field.plan_id:
            self.plan_id = value
        if plan_field == Plan.Field.start:
            self.start_time = value
        if plan_field == Plan.Field.end:
            self.end_time = value
        if plan_field == Plan.Field.shift:
            self.shift = value

    def to_plan(self):
        plan = Plan()
        plan.plan_id = self.plan_id
        plan.start = self.start
        plan.end = self.end
        plan.shift = self.shift
        return plan

    class Meta:
        table_name = 'plan'

class PlanRelationsTableModel(BaseTableModel):
    relation_id = AutoField(primary_key=True)
    plan_id = ForeignKeyField(PlanTableModel, backref='relations')
    tid = ForeignKeyField(TaskTableModel, null=True, backref='relations')
    number = IntegerField(null=True)
    kind = IntegerField(null=True)

    class Kind():
        COMMON = 0
        EDITED = 1
        DELETED = 2

    class Meta:
        table_name = 'plan_relations'

_DEFAULT_DB_NAME = 'tasktracker.db'

class StorageAdapter():

    def __init__(self, db_file=_DEFAULT_DB_NAME):
        if db_file is None:
            db_file = _DEFAULT_DB_NAME

        self.db = SqliteDatabase(db_file)
        self.db_file = db_file
        self.connections_opened = 0

        _db_proxy.initialize(self.db)

    def _is_database_exists(self):
        try:
            open(self.db_file, 'r').close()
        except FileNotFoundError:
            return False
        return True

    def _create_db(self):
        tables = [TaskTableModel, UserTableModel, PlanTableModel, PlanRelationsTableModel]
        self.db.create_tables(tables)

    def connect(self):
        if not self._is_database_exists():
            self._create_db()
        self.db.connect(reuse_if_open=True)
        self.connections_opened += 1

    def disconnect(self):
        self.connections_opened -= 1
        if self.connections_opened <= 0:
            self.db.close()

    def is_connected(self):
        return not self.db.is_closed()

    def _raise_if_disconnected(self):
        if not self.is_connected():
            raise ValueError("There is not a connection")

class TaskStorageAdapter(StorageAdapter):

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def get_tasks(self, filter=None):
        self._raise_if_disconnected()

        if filter is None:
            task_table_models = TaskTableModel.select()
        else:
            conditions = filter.to_peewee_conditions()
            if conditions is None or len(conditions) == 0:
                task_table_models = TaskTableModel.select()
            else:
                task_table_models = TaskTableModel.select().where(*conditions)

        tasks = [task_model.to_task() for task_model in task_table_models]
        return tasks
        
    def save_task(self, task, auto_tid=True):
        self._raise_if_disconnected()

        task_to_save = TaskTableModel(uid=task.uid,
                            parent_tid=task.parent_tid,
                            title=task.title, 
                            description=task.description,
                            supposed_start_time=task.supposed_start_time,
                            supposed_end_time=task.supposed_end_time,
                            deadline_time=task.deadline_time,
                            priority=task.priority,
                            status=task.status,
                            notificate_supposed_start=task.notificate_supposed_start,
                            notificate_supposed_end=task.notificate_supposed_end,
                            notificate_deadline=task.notificate_deadline)
        rows_modified = task_to_save.save()
        
        return rows_modified == 1
    
    def remove_task(self, tid):
        self._raise_if_disconnected()

        rows_deleted = TaskTableModel.delete().where(TaskTableModel.tid == tid).execute()
        if rows_deleted == 0:
            return False
        TaskTableModel.delete().where(TaskTableModel.parent_tid == tid).execute()    
        PlanTableModel.delete().where(PlanTableModel.tid == tid).execute()

        return True

    def edit_task(self, task_field_dict):
        self._raise_if_disconnected()

        tid = task_field_dict[Task.Field.tid]
        task_to_edit = TaskTableModel.select().where(TaskTableModel.tid == tid)[0]
        for field, value in task_field_dict.items():
            if field == Task.Field.tid:
                continue
            task_to_edit.map_task_attr(field, value)
        rows_modified = task_to_edit.save()

        return rows_modified == 1

    class Filter():

        def __init__(self):
            self._filter = []

        def tid(self, tid):
            self._filter.append(TaskTableModel.tid == tid)

        def parent_tid(self, parent_tid):
            self._filter.append(TaskTableModel.parent_tid == parent_tid)

        def uid(self, uid):
            self._filter.append(TaskTableModel.uid == uid)

        def title(self, title):
            self._filter.append(TaskTableModel.title == title)

        def description(self, description):
            self._filter.append(TaskTableModel.description == description)

        def priority(self, priority):
            self._filter.append(TaskTableModel.priority == priority)

        def status(self, status):
            self._filter.append(TaskTableModel.status == status)

        def notificate_supposed_start(self, notificate_supposed_start):
            self._filter.append(TaskTableModel.notificate_supposed_start == notificate_supposed_start)

        def notificate_supposed_end(self, notificate_supposed_end):
            self._filter.append(TaskTableModel.notificate_supposed_end == notificate_supposed_end)

        def notificate_deadline(self, notificate_deadline):
            self._filter.append(TaskTableModel.notificate_deadline == notificate_deadline)

        def plan_tid(self, plan_tid):
            self._filter.append(TaskTableModel.plan_tid == plan_tid)

        def filter_range(self, start_time, end_time):
            self._filter.append(((TaskTableModel.supposed_end_time > start_time)
                                | (TaskTableModel.supposed_start_time > start_time)
                                | (TaskTableModel.deadline_time > start_time))
                                & ((TaskTableModel.supposed_end_time < end_time)
                                | (TaskTableModel.supposed_start_time < end_time)
                                | (TaskTableModel.deadline_time < end_time)))

        def to_peewee_conditions(self):
            return self._filter

class PlanStorageAdapter(StorageAdapter):

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def get_plans(self, common_tid=None, time_range=None):
        self._raise_if_disconnected()

        if common_tid is not None:
            relations = PlanRelationsTableModel.select().where(PlanRelationsTableModel.tid == common_tid)
            plans = []
            for relation in relations:
                plan = self._get_plan_by_id(relation.plan_id)
                plans.append(plan)
            return plans

        plans = [plan_model.to_plan() for plan_model in PlanTableModel.select()]
        return plans

    def get_relations(self):
        return PlanRelationsTableModel.select().join(TaskTableModel)       
    
    def _get_plan_by_id(self, plan_id):
        plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
        plan = plan_models[0].to_plan()
        relations = PlanRelationsTableModel.select().join(TaskTableModel)
        for relation in relations:
            print(relation)
        print(len(relations))
        plan.exclude = []
        for relation in relations:
            if relation.kind == PlanRelationsTableModel.Kind.COMMON:
                plan.tid = relation.tid
            else:
                plan.exclude.append(relation.number)
        return plan

    def save_plan(self, plan):
        self._raise_if_disconnected()

        plan_to_save = PlanTableModel(start=plan.start,
                                end=plan.end,
                                shift=plan.shift)
        rows_modified = plan_to_save.save()
        if rows_modified != 1:
            return False

        plan_common_relation = PlanRelationsTableModel(plan_id=plan_to_save.plan_id,
                                                    tid=plan.tid,
                                                    number=None,
                                                    kind=PlanRelationsTableModel.Kind.COMMON)
        rows_modified = plan_common_relation.save()
        if rows_modified != 1:
            return False

        if plan.exclude is not None and len(plan.exclude) != 0:
            for exclude_number in plan.exclude:
                plan_deleted_relations = PlanRelationsTableModel(plan_id=plan_to_save.plan_id,
                                                    tid=None,
                                                    number=exclude_number,
                                                    kind=PlanRelationsTableModel.Kind.DELETED)
                rows_modified = plan_deleted_relations.save()
                if rows_modified != 1:
                    return False
        
        return True

    def remove_plan(self, plan_id):
        self._raise_if_disconnected()

        rows_deleted = PlanTableModel.delete().where(PlanTableModel.tid == tid).execute()
        if rows_deleted == 0:
            return False

    def edit_plan(self, plan_field_dict):
        self._raise_if_disconnected()

        plan_id = plan_field_dict[Plan.Field.plan_id]
        plan_to_edit = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)[0]
        for field, value in plan_field_dict.items():
            if field == Plan.Field.plan_id:
                continue
            if field == Plan.Field.exclude:
                value = ':'.join(value)
            plan_to_edit.map_task_attr(field, value)
        rows_modified = plan_to_edit.save()

class UserStorageAdapter(StorageAdapter):

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def check_user_existence(self, login):
        self._raise_if_disconnected()

        count = len(UserTableModel.select().where(UserTableModel.login == login))
        return count != 0

    def get_users(self, filter=None):
        self._raise_if_disconnected()

        if filter is None:
            user_table_models = UserTableModel.select()
        else:
            conditions = filter.to_peewee_conditions()
            if conditions is None or len(conditions) == 0:
                user_table_models = UserTableModel.select()
            else:
                user_table_models = UserTableModel.select().where(*conditions)
        users = [user_model.to_user() for user_model in user_table_models]

        return users

    def save_user(self, user):
        self._raise_if_disconnected()

        user_to_save = UserTableModel(login=user.login,
                            password=user.password,
                            online=user.online)
        rows_modified = user_to_save.save()
        
        return rows_modified == 1

    def delete_user(self, uid):
        self._raise_if_disconnected()

        rows_deleted = UserTableModel.delete().where(UserTableModel.uid == uid).execute()
        if rows_deleted != 1:
            return False
        TaskTableModel.delete().where(TaskTableModel.uid == uid).execute()
        return True

    def edit_user(self, user_field_dict):
        self._raise_if_disconnected()

        uid = user_field_dict[User.Field.uid]
        user_to_edit = UserTableModel.select().where(UserTableModel.uid == uid)[0]
        for field, value in user_field_dict.items():
            if field == Task.Field.uid:
                continue
            user_to_edit.map_user_attr(field, value)
        rows_modified = user_to_edit.save()

        return rows_modified == 1

    class Filter():

        def __init__(self):
            self._filter = []

        def uid(self, uid):
            self._filter.append(UserTableModel.uid == uid)

        def login(self, login):
            self._filter.append(UserTableModel.login == login)

        def online(self, online):
            self._filter.append(UserTableModel.online == online)

        def to_peewee_conditions(self):
            return self._filter