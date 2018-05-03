from ..model.task import Task
import sqlite3
import os
from itertools import filterfalse

class TidAlreadyExistsError(Exception):

    def __init__(self, tid):
        message = 'Tid {} already exists'.format(tid)
        super().__init__(message)

class TidNotExistsError(Exception):

    def __init__(self, tid):
        message = 'Tid {} not exists'.format(tid)
        super().__init__(message)

class DatabaseTaskTable:

    NAME = 'task'

    TID = ('tid', 'integer primary key')
    UID = ('uid', 'integer')
    RESPONSIBLE_UID = ('responsible_uid', 'integer')
    PID = ('pid', 'integer')
    PARENT_TID = ('parent_tid', 'integer')
    TITLE = ('title', 'text')
    DESCRIPTION = ('description', 'text')
    PRIORITY = ('priority', 'integer')
    STATUS = ('status', 'integer')
    SUPPOSED_START_TIME = ('supposed_start_time', 'integer')
    SUPPOSED_END_TIME = ('supposed_end_time', 'integer')
    DEADLINE_TIME = ('deadline_time', 'integer')
    ACTUAL_START_TIME = ('actual_start_time', 'integer')
    ACTUAL_END_TIME = ('actual_end_time', 'integer')
    NOTIFICATE_SUPPOSED_START = ('notificate_supposed_start', 'integer')
    NOTIFICATE_SUPPOSED_END = ('notificate_supposed_end', 'integer')
    NOTIFICATE_DEADLINE = ('notificate_deadline', 'integer')

    ACTIVE_COLUMNS = [TID, UID, RESPONSIBLE_UID, PID, 
                    PARENT_TID, TITLE, DESCRIPTION, 
                    PRIORITY, STATUS, SUPPOSED_START_TIME, 
                    SUPPOSED_END_TIME, DEADLINE_TIME, 
                    ACTUAL_START_TIME, ACTUAL_END_TIME,
                    NOTIFICATE_SUPPOSED_START, 
                    NOTIFICATE_SUPPOSED_END,
                    NOTIFICATE_DEADLINE]

    @classmethod
    def prepare_task_members(cls, task, auto_tid):
        notificate_supposed_start = int(task.notificate_supposed_start)
        notificate_supposed_end = int(task.notificate_supposed_end)
        notificate_deadline = int(task.notificate_deadline)

        data =  {cls.map_task_attr(task.uid): task.uid, 
                cls.map_task_attr(task.responsible_uid): task.responsible_uid, 
                cls.map_task_attr(task.pid): task.pid, 
                cls.map_task_attr(task.parent_tid): task.parent_tid, 
                cls.map_task_attr(task.title): task.title, 
                cls.map_task_attr(task.description): task.description, 
                cls.map_task_attr(task.priority): task.priority, 
                cls.map_task_attr(task.status): task.status, 
                cls.map_task_attr(task.supposed_start_time): task.supposed_start_time, 
                cls.map_task_attr(task.supposed_end_time): task.supposed_end_time, 
                cls.map_task_attr(task.deadline_time): task.deadline_time, 
                cls.map_task_attr(task.actual_start_time): task.actual_start_time, 
                cls.map_task_attr(task.actual_end_time): task.actual_end_time,
                cls.map_task_attr(task.notificate_supposed_start): notificate_supposed_start, 
                cls.map_task_attr(task.notificate_supposed_end): notificate_supposed_end,
                cls.map_task_attr(task.notificate_deadline): notificate_deadline}
        if not auto_tid:
            data[map_task_attr(task.tid)] = task.tid
        return data

    @classmethod
    def map_task_attr(cls, task_attr):
        if task_attr == task.tid:
            return cls.TID[0]
        if task_attr == task.uid:
            return cls.UID[0]
        if task_attr == task.responsible_uid:
            return cls.RESPONSIBLE_UID[0]
        if task_attr == task.pid:
            return cls.PID[0]
        if task_attr == task.parent_tid:
            return cls.PARENT_TID[0]
        if task_attr == task.title:
            return cls.title[0]
        if task_attr == task.description:
            return cls.DESCRIPTION[0]
        if task_attr == task.priority:
            return cls.PRIORITY[0]
        if task_attr == task.status:
            return cls.STATUS[0]
        if task_attr == task.supposed_start_time:
            return cls.SUPPOSED_START_TIME[0]
        if task_attr == task.supposed_end_time:
            return cls.SUPPOSED_END_TIME[0]
        if task_attr == task.deadline_time:
            return cls.DEADLINE_TIME[0]
        if task_attr == task.actual_start_time:
            return cls.ACTUAL_START_TIME[0]
        if task_attr == task.actual_end_time:
            return cls.ACTUAL_END_TIME[0]
        if task_attr == task.notificate_supposed_start:
            return cls.NOTIFICATE_SUPPOSED_START[0]
        if task_attr == task.notificate_supposed_end:
            return cls.NOTIFICATE_SUPPOSED_END[0]
        if task_attr == task.notificate_deadline:
            return cls.NOTIFICATE_DEADLINE[0]

    @classmethod
    def create_task_from_sqlite_row(cls, row):
        notificate_supposed_start = bool(row[cls.map_task_attr(task.notificate_supposed_start)])
        notificate_supposed_end = bool(row[cls.map_task_attr(task.notificate_supposed_end)])
        notificate_deadline = bool(row[cls.map_task_attr(task.notificate_deadline)])

        task = Task()
        task.tid = row[cls.map_task_attr(task.tid)]
        task.uid = row[cls.map_task_attr(task.uid)]
        task.responsible_uid = row[cls.map_task_attr(task.responsible_uid)]
        task.pid = row[cls.map_task_attr(task.pid)]
        task.parent_tid = row[cls.map_task_attr(task.parent_tid)]
        task.title = row[cls.map_task_attr(task.title)]
        task.description = row[cls.map_task_attr(task.description)]
        task.priority = row[cls.map_task_attr(task.priority)]
        task.status = row[cls.map_task_attr(task.status)]
        task.supposed_start_time = row[cls.map_task_attr(task.supposed_start_time)]
        task.supposed_end_time = row[cls.map_task_attr(task.supposed_end_time)]
        task.deadline_time = row[cls.map_task_attr(task.deadline_time)]
        task.actual_start_time = row[cls.map_task_attr(task.actual_start_time)]
        task.actual_end_time = row[cls.map_task_attr(task.actual_end_time)]
        task.notificate_supposed_start = notificate_supposed_start
        task.notificate_supposed_end = notificate_supposed_end
        task.notificate_deadline = notificate_deadline
        return task

class DatabaseHelper():

    def __init__(self, db_name):
        self.db_name = db_name

    def create(self):
        with sqlite3.connect(self.db_name) as connection:
            self._create_task_table(connection)            

    def _create_task_table(self, connection):
        def zip_column_in_str(column):
            c_name = column[0]
            c_type = column[1]
            return '{} {}'.format(c_name, c_type)

        sqlite_task_table_columns = ','.join(map(zip_column_in_str, 
            DatabaseTaskTable.ACTIVE_COLUMNS))
        connection.execute('create table task({})'.format(sqlite_task_table_columns))

    def is_database_exists(self):
        try:
            open(self.db_name, 'r').close()
        except FileNotFoundError:
            return False
        return True

    def update(self, db_version, expected_version):
        pass

class StorageAdapter():

    _first_calling = True

    _DEFAULT_DB_NAME = 'tasktracker.db'

    _DATABASE_VERSION = 0

    def __init__(self, db_name, db_helper_class):
        self.db_name = db_name

        db_helper = db_helper_class(db_name)
        self.db_helper = db_helper

        if not db_helper.is_database_exists():
            db_helper.create()
            self._set_db_version(self._DATABASE_VERSION)

        db_version = self._get_db_version()
        if db_version != self._DATABASE_VERSION:
            db_helper.update(db_version, _DATABASE_VERSION)

    def _get_db_version(self):
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.execute("pragma user_version")
            db_version = cursor.fetchall()[0][0]

        connection.close()
        return db_version

    def _set_db_version(self, db_version):
        with sqlite3.connect(self.db_name) as connection:
            connection.execute("pragma user_version = {}".format(db_version))
        connection.close()

class TaskStorageAdapter(StorageAdapter):

    def __init__(self, db_name=StorageAdapter._DEFAULT_DB_NAME, 
        db_helper_class=DatabaseHelper):
        super().__init__(db_name, db_helper_class)

    def connect(self):
        self.connection = sqlite3.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row

    def disconnect(self):
        self._raise_if_disconnect()
        self.connection.close()
        del self.connection

    def is_connected(self):
        try:
            self._raise_if_disconnect()
        except ValueError:
            return False

        return True

    def _raise_if_disconnect(self):
        try:
            self.connection
        except AttributeError:
            raise ValueError("There isn't a connection")

    def get_tasks(self, filter=None):
        self._raise_if_disconnect()

        query = 'select * from task'
        if filter is not None:
            data = ','.join(['{}=(?)'.format(key) for key in filter.keys()])
            query += ' where {}'.format(data)
        with self.connection:
            if filter is None:
                cursor = self.connection.execute(query)
            else:
                cursor = self.connection.execute(query, list(filter.values()))
            cursor_content = cursor.fetchall()
            tasks = []
            for raw_task in cursor_content:
                task = DatabaseTaskTable.create_task_from_sqlite_row(raw_task)
                tasks.append(task)

        return tasks
        
    def save_task(self, task, auto_tid=True):
        self._raise_if_disconnect()

        prepared_dict = DatabaseTaskTable.prepare_task_members(task, auto_tid)
        data_placeholder = ('?,' * len(prepared_dict))[0:-1]
        columns = ','.join(list(prepared_dict.keys()))
        query = 'insert into task({}) values ({})'.format(columns, data_placeholder)
        with self.connection:
            self.connection.execute(query, list(prepared_dict.values()))
    
    def remove_task(self, task_id):
        self._raise_if_disconnect()

        query = 'delete from task where {}=(?)'.format(DatabaseTaskTable.TID[0])
        with self.connection:
            self.connection.execute(query, [task_id])

    def edit_task(self, edit_task):
        self._raise_if_disconnect()

        prepared_dict = DatabaseTaskTable.prepare_task_members(edit_task, True)
        data = ','.join(['{}=(?)'.format(key) for key in prepared_dict.keys()])
        query = 'update task set {} where {}=(?)'.format(data, DatabaseTaskTable.TID[0])
        with self.connection:
            self.connection.execute(query, list(prepared_dict.values()) + [edit_task.tid])

    def is_task_id_present(self, task_id):
        tasks = self.get_tasks()

        present = False
        for task in tasks:
            if task.tid == task_id:
                present = True
                break

        return present

    def _create_next_task_id(self):
        with open(self.id_db_name, 'a+') as id_db_file:
            id_db_file.seek(0)
            json_id_db_file_content = id_db_file.read()
            if len(json_id_db_file_content) == 0:
                id_db_file_content = {}
            else:
                id_db_file_content = json.loads(json_id_db_file_content)

            task_id = int(id_db_file_content.get('task', '0'))
            id_db_file_content['task'] = task_id + 1

            json_id_db_file_content = json.dumps(id_db_file_content)
            id_db_file.truncate(0)
            id_db_file.write(json_id_db_file_content)

        return task_id