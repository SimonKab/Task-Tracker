from ..model.task import Task, Status
from ..model.user import User
from ..model.plan import Plan
from ..model.project import Project
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

class ProjectTableModel(BaseTableModel):
    pid = AutoField(primary_key=True)
    creator = ForeignKeyField(UserTableModel, backref='projects')
    name = TextField(null=True)

    def to_project(self):
        project = Project()
        project.pid = self.pid
        project.creator = self.creator
        project.name = self.name
        return project

    class Meta:
        table_name = 'project'

class ProjectRelationsTableModel(BaseTableModel):
    relation_id = AutoField(primary_key=True)
    pid = ForeignKeyField(ProjectTableModel, backref='project_relations')
    uid = ForeignKeyField(UserTableModel, backref='project_relations')
    kind = IntegerField(null=False)

    class Kind():
        ADMIN = 0
        GUEST = 1

    class Meta:
        table_name = 'project'

_DEFAULT_DB_NAME = 'tasktracker.db'

class StorageAdapter():

    def __init__(self, db_file=_DEFAULT_DB_NAME):
        if db_file is None:
            db_file = _DEFAULT_DB_NAME

        self.db = SqliteDatabase(db_file)
        self.db_file = db_file
        self.connections_opened = 0

        _db_proxy.initialize(self.db)

        if not self._is_database_exists():
            self._create_db()

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
        # self.db.connect(reuse_if_open=True)
        # self.connections_opened += 1
        pass

    def disconnect(self):
        # self.connections_opened -= 1
        # if self.connections_opened <= 0:
        #     self.db.close()
        pass

    def is_connected(self):
        # return not self.db.is_closed()
        return True

    def _raise_if_disconnected(self):
        # if not self.is_connected():
        #     raise ValueError("Connection is not established")
        pass

class TaskStorageAdapter(StorageAdapter):

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def get_tasks(self, filter=None):
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
    
    def get_last_saved_task(self):
        task_model = TaskTableModel.select().order_by(TaskTableModel.tid.desc()).get()
        if task_model is not None:
            return task_model.to_task()

    def remove_task(self, tid):
        plan_storage = PlanStorageAdapter(self.db_file)
        plans = plan_storage.get_plans(common_tid=tid)
        if plans is not None and len(plans) != 0:
            for plan in plans:
                success = plan_storage.remove_plan(plan.plan_id)
                return success

        plans = plan_storage.get_plans(edit_repeat_tid=tid)
        if plans is not None and len(plans) != 0:
            for plan in plans:
                number = plan_storage.get_number_for_edit_repeat_by_tid(plan.plan_id, tid)
                success = plan_storage.restore_plan_repeat(plan.plan_id, number)
                if not success:
                    return False
            

        tasks_to_delete = [tid]
        while len(tasks_to_delete) != 0:
            tid_to_delete = tasks_to_delete.pop(0)

            rows_deleted = TaskTableModel.delete().where(TaskTableModel.tid == tid_to_delete).execute()
            if rows_deleted == 0:
                return False

            child_tasks = TaskTableModel.select().where(TaskTableModel.parent_tid == tid_to_delete)
            for child_task in child_tasks:
                tasks_to_delete.append(child_task.tid)

        return True

    def edit_task_from_model(self, task):
        task_to_edit = TaskTableModel.select().where(TaskTableModel.tid == task.tid)[0]
        task_to_edit.uid = task.uid
        task_to_edit.parent_tid = task.parent_tid
        task_to_edit.title = task.title
        task_to_edit.description = task.description
        task_to_edit.supposed_start_time = task.supposed_start_time
        task_to_edit.supposed_end_time = task.supposed_end_time
        task_to_edit.deadline_time = task.deadline_time
        task_to_edit.priority = task.priority
        task_to_edit.status = task.status
        task_to_edit.notificate_supposed_start = task.notificate_supposed_start
        task_to_edit.notificate_supposed_end = task.notificate_supposed_end
        task_to_edit.notificate_deadline = task.notificate_deadline
        
        rows_modified = task_to_edit.save()
        return rows_modified == 1

    def edit_task(self, task_field_dict):
        tid = task_field_dict[Task.Field.tid]
        tasks_to_edit = TaskTableModel.select().where(TaskTableModel.tid == tid)
        if len(tasks_to_edit) == 0:
            return False
        task_to_edit = tasks_to_edit[0]
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

        def one_of_notificate(self):
            self._filter.append((TaskTableModel.notificate_supposed_start == True)
                                | (TaskTableModel.notificate_supposed_end == True)
                                | (TaskTableModel.notificate_deadline == True))

        def to_time(self, time):
            self._filter.append((TaskTableModel.supposed_end_time < time)
                                | (TaskTableModel.supposed_start_time < time)
                                | (TaskTableModel.deadline_time < time))

        def not_completed(self):
            self._filter.append((TaskTableModel.status == Status.ACTIVE)
                                | (TaskTableModel.status == Status.PENDING)
                                | (TaskTableModel.status == Status.OVERDUE))

        def plan_tid(self, plan_tid):
            self._filter.append(TaskTableModel.plan_tid == plan_tid)

        def overdue_by_time(self, time):
            start_before = (~(TaskTableModel.supposed_start_time >> None)
                                & (TaskTableModel.supposed_start_time < time))
            end_before = (~(TaskTableModel.supposed_end_time >> None)
                                & (TaskTableModel.supposed_end_time < time))
            deadline_before = (~(TaskTableModel.deadline_time >> None)
                                & (TaskTableModel.deadline_time < time))
            only_end = (TaskTableModel.supposed_start_time >> None)
            self._filter.append((only_end & (end_before | deadline_before))
                                | (start_before & (end_before | deadline_before)))

        def filter_range(self, start_time, end_time):
            start_before_end = (~(TaskTableModel.supposed_start_time >> None)
                                & (TaskTableModel.supposed_start_time <= end_time))
            end_after_start = (~(TaskTableModel.supposed_end_time >> None)
                                & (TaskTableModel.supposed_end_time >= start_time))
            deadline_after_start = (~(TaskTableModel.deadline_time >> None)
                                & (TaskTableModel.deadline_time >= start_time))
            only_start = ((TaskTableModel.supposed_end_time >> None) 
                            & (TaskTableModel.deadline_time >> None))
            only_end = (TaskTableModel.supposed_start_time >> None)
            self._filter.append((only_start & start_before_end)
                                | (only_end & (end_after_start | deadline_after_start))
                                | (start_before_end & (end_after_start | deadline_after_start)))

        def timeless(self):
            self._filter.append((TaskTableModel.supposed_end_time == None)
                                & (TaskTableModel.supposed_start_time == None)
                                & (TaskTableModel.deadline_time == None))

        def to_peewee_conditions(self):
            return self._filter

class PlanStorageAdapter(StorageAdapter):

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def _get_all_relations(self):
        return PlanRelationsTableModel.select()

    def get_plans(self, plan_id=None, common_tid=None, edit_repeat_tid=None):
        plans = []

        if plan_id is not None:
            plan = self._get_plan_by_id(plan_id)
            if plan is not None:
                plans.append(plan)
            return plans

        if common_tid is not None:
            condition = ((PlanRelationsTableModel.tid == common_tid) 
                & (PlanRelationsTableModel.kind == PlanRelationsTableModel.Kind.COMMON))
            relations = PlanRelationsTableModel.select().where(condition)
            for relation in relations:
                plan = self._get_plan_by_id(relation.plan_id)
                if plan is not None:
                    plans.append(plan)
            return plans

        if edit_repeat_tid is not None:
            condition = ((PlanRelationsTableModel.tid == edit_repeat_tid) 
                & (PlanRelationsTableModel.kind == PlanRelationsTableModel.Kind.EDITED))
            relations = PlanRelationsTableModel.select().where(condition)
            for relation in relations:
                plan = self._get_plan_by_id(relation.plan_id)
                if plan is not None:
                    plans.append(plan)
            return plans

        plans = [plan_model.to_plan() for plan_model in PlanTableModel.select()]
        return plans

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

    def get_exclude_type(self, plan_id, number):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.number == number))
        relations = PlanRelationsTableModel.select().where(conditions)
        if len(relations) != 1:
            return None
        
        if relations[0].kind == PlanRelationsTableModel.Kind.DELETED:
            return Plan.PlanExcludeKind.DELETED
        if relations[0].kind == PlanRelationsTableModel.Kind.EDITED:
            return Plan.PlanExcludeKind.EDITED
        return None

    def get_number_for_edit_repeat_by_tid(self, plan_id, edit_tid):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.tid == edit_tid)
            & (PlanRelationsTableModel.kind == PlanRelationsTableModel.Kind.EDITED))
        relations = PlanRelationsTableModel.select().where(conditions)
        if len(relations) == 0:
            return None
        return relations[0].number

    def get_tid_for_edit_repeat(self, plan_id, number):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.number == number))
        relations = PlanRelationsTableModel.select().where(conditions)
        if len(relations) != 1:
            return None
        if relations[0].kind != PlanRelationsTableModel.Kind.EDITED:
            return None

        return relations[0].tid

    def recalculate_exclude_when_start_time_shifted(self, plan_id, start_time_shift):
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
            return self.restore_all_repeats(plan_id)

        return True

    def save_plan(self, plan):
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
        type = self.get_exclude_type(plan_id, number)
        if type != None:
            self.restore_plan_repeat(plan_id, number)
        plan_deleted_relations = PlanRelationsTableModel(plan_id=plan_id,
                                tid=tid,
                                number=number,
                                kind=PlanRelationsTableModel.Kind.EDITED)
        rows_modified = plan_deleted_relations.save()
        return rows_modified == 1

    def chagne_edit_plan_repeat_to_delete(self, plan_id, number):
        success = self.restore_plan_repeat(plan_id, number)
        if not success:
            return False
        return self.delete_plan_repeat(plan_id, number)

    def restore_plan_repeat(self, plan_id, number):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.number == number))
        rows_deleted = PlanRelationsTableModel.delete().where(conditions).execute()
        return rows_deleted != -1

    def restore_all_repeats(self, plan_id):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id) 
                & (PlanRelationsTableModel.kind != PlanRelationsTableModel.Kind.COMMON))
        rows_deleted = PlanRelationsTableModel.delete().where(conditions).execute()
        return True

    def remove_plan(self, plan_id):
        rows_deleted = PlanTableModel.delete().where(PlanTableModel.plan_id == plan_id).execute()
        relations = PlanRelationsTableModel.select().where(PlanRelationsTableModel.plan_id == plan_id)
        if len(relations) != 0:
            task_storage = TaskStorageAdapter(self.db_file)
            for relation in relations:
                if relation.tid is not None:
                    TaskTableModel.delete().where(TaskTableModel.tid == relation.tid).execute()

        PlanRelationsTableModel.delete().where(PlanRelationsTableModel.plan_id == plan_id).execute()
        return rows_deleted == 1

    def edit_plan(self, plan_field_dict):
        plan_id = plan_field_dict[Plan.Field.plan_id]

        if Plan.Field.end in plan_field_dict:
            end = plan_field_dict[Plan.Field.end]
            plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
            for plan_model in plan_models:
                plan_model.end = end
                rows_modified = plan_model.save()
                if rows_modified != 1:
                    return False

        if Plan.Field.shift in plan_field_dict:
            shift = plan_field_dict[Plan.Field.shift]
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
        count = len(UserTableModel.select().where(UserTableModel.login == login))
        return count != 0

    def get_users(self, filter=None):
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
        user_to_save = UserTableModel(login=user.login,
                            password=user.password,
                            online=user.online)
        rows_modified = user_to_save.save()
        
        return rows_modified == 1

    def delete_user(self, uid):
        task_adapter = TaskStorageAdapter(self.db_file)
        filter = TaskStorageAdapter.Filter()
        filter.uid(uid)
        tasks = task_adapter.get_tasks(filter)
        for task in tasks:
            task_adapter.remove_task(task.tid)

        rows_deleted = UserTableModel.delete().where(UserTableModel.uid == uid).execute()
        return rows_deleted == 1

    def edit_user(self, user_field_dict):
        uid = user_field_dict[User.Field.uid]
        users_to_edit = UserTableModel.select().where(UserTableModel.uid == uid)
        if len(users_to_edit) == 0:
            return False
        user_to_edit = users_to_edit[0]
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

class ProjectStorageAdapter(StorageAdapter):

    def __init__(self, db_name=None):
        super().__init__(db_name)

    def add_project(self, project):
        project_model = ProjectTableModel(uid=project.uid, name=project.name)
        rows_modified = project_model.save()
        return rows_modified == 1

    def get_project(self, filter):
        if filter is None:
            project_table_models = ProjectTableModel.select()
        else:
            conditions = filter.to_peewee_conditions()
            if conditions is None or len(conditions) == 0:
                project_table_models = ProjectTableModel.select()
            else:
                project_table_models = ProjectTableModel.select().where(*conditions)

        projects = [project_model.to_project() for project_model in project_table_models]
        return projects

    def remove_project(self, pid):
        rows_deleted = ProjectTableModel.delete().where(ProjectTableModel.pid == pid).execute()
        return rows_deleted != 0

    def update_project(self, pid, name=None):
        project_models = ProjectTableModel.select().where(ProjectTableModel.pid == pid)
        if len(project_models) == 0:
            return False
        project_model = project_models[0]
        if name is not None:
            project_model.name = name
            rows_modified = project_model.save()
            return rows_modified == 1

        return True

    class Filter():

        def __init__(self):
            self._filter = []

        def pid(self, pid):
            self._filter.append(ProjectTableModel.pid == pid)

        def name(self, name):
            self._filter.append(ProjectTableModel.name == name)

        def creator(self, uid):
            self._filter.append(ProjectTableModel.creator == uid)

        def to_peewee_conditions(self):
            return self._filter