import os
from itertools import filterfalse

from peewee import *

from tasktracker_core.model.task import Task, Status
from tasktracker_core.model.user import User
from tasktracker_core.model.plan import Plan
from tasktracker_core.model.project import Project
from tasktracker_core import logging
from tasktracker_core import utils

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

class ProjectTableModel(BaseTableModel):
    pid = AutoField(primary_key=True)
    creator = ForeignKeyField(UserTableModel, backref='projects')
    name = TextField(null=True)

    def to_project(self):
        project = Project()
        project.pid = self.pid
        user_table_model = self.creator
        if user_table_model is not None:
            project.creator = user_table_model.uid
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
        table_name = 'project_relations'

_DEFAULT_DB_FILE_PATH = utils.get_file_in_home_folder('tasktracker.db')

class TaskTableModel(BaseTableModel):
    tid = IntegerField(primary_key=True)
    pid = ForeignKeyField(ProjectTableModel, backref='tasks')
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
        if task_field == Task.Field.pid:
            self.pid = value
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
        project_table_model = self.pid
        if project_table_model is not None:
            task.pid = project_table_model.pid
        task.parent_tid = self.parent_tid
        user_table_model = self.uid
        if user_table_model is not None:
            task.uid = user_table_model.uid
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

class StorageAdapter():

    def __init__(self, db_file=_DEFAULT_DB_FILE_PATH, db=None):
        if db_file is None:
            db_file = _DEFAULT_DB_FILE_PATH

        if db is None:
            self.db = SqliteDatabase(db_file)
            _db_proxy.initialize(self.db)
        else:
            self.db = db

        self.db_file = db_file

        if not self._is_database_exists():
            self._create_db()

    def _is_database_exists(self):
        if self.db_file == ':memory:':
            # if db is in memory, we should init it always, so return False
            # to say that database need to be initialized
            return False

        try:
            open(self.db_file, 'r').close()
        except FileNotFoundError:
            return False
        return True

    def _create_db(self):
        if self.db_file != ':memory:':
            utils.create_file_if_not_exists(self.db_file)

        tables = [TaskTableModel, UserTableModel, 
            PlanTableModel, PlanRelationsTableModel, 
            ProjectTableModel, ProjectRelationsTableModel]
        self.db.create_tables(tables)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def is_connected(self):
        return True

    def _raise_if_disconnected(self):
        pass

class TaskStorageAdapter(StorageAdapter):

    _log_tag = 'TaskStorageAdapter'

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
                            pid=task.pid,
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
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('Task was saved: {}'.format(task_to_save.__data__))
        return success

    def get_last_saved_task(self):
        task_model = TaskTableModel.select().order_by(TaskTableModel.tid.desc()).get()
        if task_model is not None:
            return task_model.to_task()

    def remove_task(self, tid):
        plan_storage = PlanStorageAdapter(self.db_file, self.db)
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
            else:
                logging.get_logger(self._log_tag).info('Task was removed: {}'.format(tid_to_delete))

            child_tasks = TaskTableModel.select().where(TaskTableModel.parent_tid == tid_to_delete)
            for child_task in child_tasks:
                tasks_to_delete.append(child_task.tid)

        return True

    def edit_task_from_model(self, task):
        task_to_edit = TaskTableModel.select().where(TaskTableModel.tid == task.tid)[0]
        task_to_edit.pid = task.pid
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
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('Task was edited: %s', task_to_edit.__data__)
        return success

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

        def pid(self, pid):
            self._filter.append(TaskTableModel.pid == pid)

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

    _log_tag = 'PlanStorageAdapter'

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
            logging.get_logger(self._log_tag).info(('For {} excludes were recalculated '
                'due start time shift changed').format(plan_id))
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
        logging.get_logger(self._log_tag).info('Plan was saved: {}'.format(plan_to_save.__data__))

        plan_common_relation = PlanRelationsTableModel(plan_id=plan_to_save.plan_id,
                                                    tid=plan.tid,
                                                    number=None,
                                                    kind=PlanRelationsTableModel.Kind.COMMON)
        rows_modified = plan_common_relation.save()
        if rows_modified != 1:
            return False
        logging.get_logger(self._log_tag).info('Plan common relation was added: {}'.format(plan_common_relation.__data__))

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
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('Repeat {} was deleted in plan {}'.format(number, plan_id))
        return success

    def edit_plan_repeat(self, plan_id, number, tid):
        type = self.get_exclude_type(plan_id, number)
        if type != None:
            self.restore_plan_repeat(plan_id, number)
        plan_deleted_relations = PlanRelationsTableModel(plan_id=plan_id,
                                tid=tid,
                                number=number,
                                kind=PlanRelationsTableModel.Kind.EDITED)
        rows_modified = plan_deleted_relations.save()
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('Repeat {} in plan {} was edited: {}'\
                .format(number, plan_id, plan_deleted_relations.__data__))
        return success

    def chagne_edit_plan_repeat_to_delete(self, plan_id, number):
        success = self.restore_plan_repeat(plan_id, number)
        if not success:
            return False
        return self.delete_plan_repeat(plan_id, number)

    def restore_plan_repeat(self, plan_id, number):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id)
            & (PlanRelationsTableModel.number == number))
        rows_deleted = PlanRelationsTableModel.delete().where(conditions).execute()
        success = rows_deleted != -1
        if success:
            logging.get_logger(self._log_tag).info('Repeat {} in plan {} was restored'.format(number, plan_id))    
        return success

    def restore_all_repeats(self, plan_id):
        conditions = ((PlanRelationsTableModel.plan_id == plan_id) 
                & (PlanRelationsTableModel.kind != PlanRelationsTableModel.Kind.COMMON))
        rows_deleted = PlanRelationsTableModel.delete().where(conditions).execute()
        success = rows_deleted != 0
        if success:
            logging.get_logger(self._log_tag).info('All repeats in plan {} were restore'.format(plan_id))
        return success

    def remove_plan(self, plan_id):
        rows_deleted = PlanTableModel.delete().where(PlanTableModel.plan_id == plan_id).execute()
        relations = PlanRelationsTableModel.select().where(PlanRelationsTableModel.plan_id == plan_id)
        if len(relations) != 0:
            task_storage = TaskStorageAdapter(self.db_file, self.db)
            for relation in relations:
                if relation.tid is not None:
                    TaskTableModel.delete().where(TaskTableModel.tid == relation.tid).execute()

        PlanRelationsTableModel.delete().where(PlanRelationsTableModel.plan_id == plan_id).execute()
        success = rows_deleted == 1
        if success:
            logging.get_logger(self._log_tag).info('Plan {} was deleted'.format(plan_id))
        return success

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
                logging.get_logger(self._log_tag).info('End of plan {} was changed to {}'.format(plan_id, end))

        if Plan.Field.shift in plan_field_dict:
            shift = plan_field_dict[Plan.Field.shift]
            plan_models = PlanTableModel.select().where(PlanTableModel.plan_id == plan_id)
            for plan_model in plan_models:
                old_shift = plan_model.shift
                plan_model.shift = shift
                rows_modified = plan_model.save()
                if rows_modified != 1:
                    return False
                logging.get_logger(self._log_tag).info('Shift of plan {} was changed to {}'.format(plan_id, shift))
            
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
                    logging.get_logger(self._log_tag).info('Repeat {} was shifted'.format(number))
                else:
                    relation.delete_instance()
                    logging.get_logger(self._log_tag).info('Repeat {} was removed'.format(number))

        return True


class UserStorageAdapter(StorageAdapter):

    _log_tag = 'UserStorageAdapter'

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
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('User {} was saved'.format(user_to_save.__data__))
        return success

    def get_last_saved_user(self):
        user_model = UserTableModel.select().order_by(UserTableModel.uid.desc()).get()
        if user_model is not None:
            return user_model.to_user()

    def delete_user(self, uid):
        task_adapter = TaskStorageAdapter(self.db_file, self.db)
        filter = TaskStorageAdapter.Filter()
        filter.uid(uid)
        tasks = task_adapter.get_tasks(filter)
        for task in tasks:
            task_adapter.remove_task(task.tid)

        rows_deleted = UserTableModel.delete().where(UserTableModel.uid == uid).execute()
        success = rows_deleted == 1
        if success:
            logging.get_logger(self._log_tag).info('User {} was deleted'.format(uid))
        return success

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

        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('User {} was edited'.format(user_to_edit.__data__))
        return success

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

    _log_tag = 'ProjectStorageAdapter'

    def save_project(self, project):
        project_model = ProjectTableModel(creator=project.creator, name=project.name)
        rows_modified = project_model.save()
        return rows_modified == 1

    def _get_all_relations(self):
        return ProjectRelationsTableModel.select()

    def get_projects(self, uid, name=None, pid=None):
        projects = []
        
        project_table_models = ProjectTableModel.select().where(ProjectTableModel.creator == uid)
        for project_model in project_table_models:
            project = self._get_project_by_id(project_model.pid)
            if project is not None:
                projects.append(project)

        admin_projects = self.get_all_admin_third_party_projects(uid)
        guest_projects = self.get_all_guest_third_party_projects(uid)

        projects.extend(admin_projects)
        projects.extend(guest_projects)

        result = []
        for project in projects:
            include = True
            if name is not None:
                if project.name != name:
                    include = False
            if pid is not None and include:
                if project.pid != pid:
                    include = False
            if include:
                result.append(project)

        return result

    def get_all_admin_third_party_projects(self, uid):
        admin_project_models = ProjectRelationsTableModel.select().where((ProjectRelationsTableModel.uid == uid)
                            & (ProjectRelationsTableModel.kind == ProjectRelationsTableModel.Kind.ADMIN))

        projects = []
        if len(admin_project_models) != 0:
            for admin_project_model in admin_project_models:
                project = self._get_project_by_id(admin_project_model.pid)
                projects.append(project)
        return projects

    def get_all_guest_third_party_projects(self, uid):
        guest_project_models = ProjectRelationsTableModel.select().where((ProjectRelationsTableModel.uid == uid)
                            & (ProjectRelationsTableModel.kind == ProjectRelationsTableModel.Kind.GUEST))

        projects = []
        if len(guest_project_models) != 0:
            for guest_project_model in guest_project_models:
                project = self._get_project_by_id(guest_project_model.pid)
                projects.append(project)
        return projects

    def _get_project_by_id(self, pid):
        project_models = ProjectTableModel.select().where(ProjectTableModel.pid == pid)
        if len(project_models) == 0:
            return None
        project_model = project_models[0]

        project = project_model.to_project()

        admin_project_models = ProjectRelationsTableModel.select()\
                            .where(((ProjectRelationsTableModel.pid == pid)
                            & (ProjectRelationsTableModel.kind == ProjectRelationsTableModel.Kind.ADMIN)))
        if len(admin_project_models) != 0:
            admin_uids = []
            for admin_project_model in admin_project_models:
                admin_uids.append(admin_project_model.uid.uid)
            project.admins = admin_uids

        guest_project_models = ProjectRelationsTableModel.select()\
                            .where(((ProjectRelationsTableModel.pid == pid)
                            & (ProjectRelationsTableModel.kind == ProjectRelationsTableModel.Kind.GUEST)))
        if len(guest_project_models) != 0:
            guest_uids = []
            for guest_project_model in guest_project_models:
                guest_uids.append(guest_project_model.uid.uid)
            project.guests = guest_uids

        return project

    def remove_project(self, pid):
        ProjectRelationsTableModel.delete().where(ProjectRelationsTableModel.pid == pid).execute()
        rows_deleted = ProjectTableModel.delete().where(ProjectTableModel.pid == pid).execute()
        success = rows_deleted != 0
        if success:
            logging.get_logger(self._log_tag).info('Project {} was removed'.format(pid))
        return success

    def edit_project(self, project_fields_dict):
        pid = project_fields_dict[Project.Field.pid]
        project_models = ProjectTableModel.select().where(ProjectTableModel.pid == pid)
        if len(project_models) == 0:
            return False
        project_model = project_models[0]
        if Project.Field.name in project_fields_dict:
            project_model.name = project_fields_dict[Project.Field.name]
            rows_modified = project_model.save()
            success = rows_modified == 1
            if success:
                logging.get_logger(self._log_tag).info('Project {} was edited'.format(project_model.__data__))
            return success

        return True

    def get_user_kind(self, pid, uid):
        projects = self.get_projects(uid, pid=pid)
        if len(projects) == 0:
            return None
        return projects[0].get_user_kind(uid)

    def add_admin_to_project(self, pid, uid):
        project_raltion_model = ProjectRelationsTableModel(pid=pid, 
                                    uid=uid, kind=ProjectRelationsTableModel.Kind.ADMIN)
        rows_modified = project_raltion_model.save()
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('Admin {} was invited in project {}'.format(uid, pid))
        return success

    def remove_admin_from_project(self, pid, uid):
        filter = TaskStorageAdapter.Filter()
        filter.pid(pid)
        filter.uid(uid)
        task_storage = TaskStorageAdapter(self.db_file, self.db)
        tasks = task_storage.get_tasks(filter)
        if tasks is not None and len(tasks) != 0:
            projects = self.get_projects(uid=uid, pid=pid)
            project = projects[0]
            for task in tasks:
                task.uid = project.creator
                success = task_storage.edit_task_from_model(task)
                if not success:
                    return False

        conditions = (ProjectRelationsTableModel.pid == pid & ProjectRelationsTableModel.uid == uid
                        & ProjectRelationsTableModel.kind == ProjectRelationsTableModel.Kind.ADMIN)
        rows_deleted = ProjectRelationsTableModel.delete().where(conditions).execute()
        success = rows_deleted == 1
        if success:
            logging.get_logger(self._log_tag).info('Admin {} was removed from project {}'.format(uid, pid))
        return success

    def add_guest_to_project(self, pid, uid):
        project_raltion_model = ProjectRelationsTableModel(pid=pid, 
                                    uid=uid, kind=ProjectRelationsTableModel.Kind.GUEST)
        rows_modified = project_raltion_model.save()
        success = rows_modified == 1
        if success:
            logging.get_logger(self._log_tag).info('Guest {} was invited in project {}'.format(uid, pid))
        return success

    def remove_guest_from_project(self, pid, uid):
        conditions = (ProjectRelationsTableModel.pid == pid & ProjectRelationsTableModel.uid == uid
                        & ProjectRelationsTableModel.kind == ProjectRelationsTableModel.Kind.GUEST)
        rows_deleted = ProjectRelationsTableModel.delete().where(conditions).execute()
        success = rows_deleted == 1
        if success:
            logging.get_logger(self._log_tag).info('Guest {} was removed from project {}'.format(uid, pid))
        return success