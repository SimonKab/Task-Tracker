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
    is_plan = IntegerField(null=True)

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
    end = IntegerField(null=True)
    shift = IntegerField(null=False)

    def map_plan_attr(self, plan_field, value):
        if plan_field == Plan.Field.plan_id:
            self.plan_id = value
        if plan_field == Plan.Field.end:
            self.end_time = value
        if plan_field == Plan.Field.shift:
            self.shift = value

    def to_plan(self):
        plan = Plan()
        plan.plan_id = self.plan_id
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
        child_tasks = TaskTableModel.select().where(TaskTableModel.parent_tid == tid)
        for child_task in child_tasks:
            self.remove_task(child_task.tid)  

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

    class PlanExcludeKind():
        EDITED = 1
        DELETED = 2

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def get_plans(self, plan_id=None, common_tid=None, edit_repeat_tid=None):
        self._raise_if_disconnected()

        if plan_id is not None:
            return self._get_plan_by_id(plan_id)

        if common_tid is not None:
            condition = ((PlanRelationsTableModel.tid == common_tid) 
                & (PlanRelationsTableModel.kind == PlanRelationsTableModel.Kind.COMMON))
            relations = PlanRelationsTableModel.select().where(condition)
            plans = []
            for relation in relations:
                plan = self._get_plan_by_id(relation.plan_id)
                plans.append(plan)
            return plans

        if edit_repeat_tid is not None:
            condition = ((PlanRelationsTableModel.tid == edit_repeat_tid) 
                & (PlanRelationsTableModel.kind == PlanRelationsTableModel.Kind.EDITED))
            relations = PlanRelationsTableModel.select().where(condition)
            plans = []
            for relation in relations:
                plan = self._get_plan_by_id(relation.plan_id)
                plans.append(plan)
            return plans

        plans = [plan_model.to_plan() for plan_model in PlanTableModel.select()]
        return plans

    def get_exclude_type(self, plan_id, number):
        self._raise_if_disconnected()

        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.number == number))
        relations = PlanRelationsTableModel.select().where(conditions)
        if len(relations) != 1:
            return None
        
        if relations[0].kind == PlanRelationsTableModel.Kind.DELETED:
            return self.PlanExcludeKind.DELETED
        if relations[0].kind == PlanRelationsTableModel.Kind.EDITED:
            return self.PlanExcludeKind.EDITED
        return None

    def recalculate_exclude_when_start_time_shifted(self, plan_id, start_time_shift):
        self._raise_if_disconnected()

        plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
        shift = plan_models[0].shift
        if start_time_shift % shift == 0:
            conditions = ((PlanRelationsTableModel.plan_id == plan_id) 
                & (PlanRelationsTableModel.kind != PlanRelationsTableModel.Kind.COMMON))
            relations = PlanRelationsTableModel.select().where(conditions)
            for relation in relations:
                relation.number -= start_time_shift / shift
                if relation.number < 0:
                    relation.delete_instance()
                else:
                    rows_modified = relation.save()
                    if rows_modified != 1:
                        return False
        else:
            conditions = ((PlanRelationsTableModel.plan_id == plan_id) 
                & (PlanRelationsTableModel.kind != PlanRelationsTableModel.Kind.COMMON))
            rows_deleted = PlanRelationsTableModel.delete().where(conditions).execute()
            if rows_deleted < 0:
                return False

        return True

    def _get_plan_by_id(self, plan_id):
        plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
        if len(plan_models) == 0:
            return None
        plan = plan_models[0].to_plan()
        relations = PlanRelationsTableModel.select().where(PlanRelationsTableModel.plan_id == plan_id)
        plan.exclude = []
        for relation in relations:
            if relation.kind == PlanRelationsTableModel.Kind.COMMON:
                plan.tid = relation.tid.tid
            else:
                plan.exclude.append(relation.number)
        return plan

    def save_plan(self, plan):
        self._raise_if_disconnected()

        plan_to_save = PlanTableModel(end=plan.end,
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
                success = self.delete_plan_repeat(plan_to_save.plan_id, exclude_number)
                if not success:
                    return False
        
        return True

    def delete_plan_repeat(self, plan_id, number):
        plan_deleted_relations = PlanRelationsTableModel(plan_id=plan_id,
                                tid=None,
                                number=number,
                                kind=PlanRelationsTableModel.Kind.DELETED)
        rows_modified = plan_deleted_relations.save()
        return rows_modified == 1

    def edit_plan_repeat(self, plan_id, number, tid):
        plan_deleted_relations = PlanRelationsTableModel(plan_id=plan_id,
                                tid=tid,
                                number=number,
                                kind=PlanRelationsTableModel.Kind.EDITED)
        rows_modified = plan_deleted_relations.save()
        return rows_modified == 1 

    def restore_plan_repeat(self, plan_id, number):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.number == number))
        rows_deleted = PlanRelationsTableModel.delete().where(conditions).execute()
        return rows_deleted != -1

    def remove_plan(self, plan_id):
        self._raise_if_disconnected()

        rows_deleted = PlanTableModel.delete().where(PlanTableModel.plan_id == plan_id).execute()
        PlanRelationsTableModel.delete().where(PlanRelationsTableModel.plan_id == plan_id).execute()
        return rows_deleted == 1

    def edit_plan(self, plan_id, end=None, shift=None):
        self._raise_if_disconnected()

        if end is not None:
            plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
            for plan_model in plan_models:
                plan_model.end = end
                rows_modified = plan_model.save()
                if rows_modified != 1:
                    return False

        if shift is not None:
            plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
            for plan_model in plan_models:
                old_shift = plan_model.shift
                plan_model.shift = shift
                rows_modified = plan_model.save()
                if rows_modified != 1:
                    return False
            
            conditions = ((PlanRelationsTableModel.plan_id == plan_id)
                & (PlanRelationsTableModel.kind != PlanRelationsTableModel.Kind.COMMON))
            relations = PlanRelationsTableModel.select().where(conditions)
            for relation in relations:
                number = relation.number
                if (number * old_shift) % shift == 0:
                    relation.number = (number * old_shift) / shift
                    rows_modified = relation.save()
                    if rows_modified != 1:
                        return False
                else:
                    relation.delete_instance()

        return True


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