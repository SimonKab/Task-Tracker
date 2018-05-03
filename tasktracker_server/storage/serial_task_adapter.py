from ..model.task import Task
import json
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


class TaskStorageAdapter():

    _DEFAULT_DB_NAME = 'task.db'
    _DEFAULT_ID_NAME = 'id.db'

    def __init__(self, db_name=_DEFAULT_DB_NAME, id_db_name=_DEFAULT_ID_NAME):
        self.db_name = db_name
        self.id_db_name = id_db_name

    def _read_tasks_from_db(self):
        tasks = []
        with open(self.db_name, 'a+') as db:
            db.seek(0)
            json_db_content = db.read()
            if len(json_db_content) == 0:
                raw_data = []
            else:
                raw_data = json.loads(json_db_content)

            for raw_task in raw_data:
                task = Task()
                task.__dict__ = raw_task
                tasks.append(task)

        return tasks

    def _write_tasks_in_db(self, tasks):
        tasks_dic = [task.__dict__ for task in tasks]
        json_task_db = json.dumps(tasks_dic)
        with open(self.db_name, 'w') as task_db_file:
            task_db_file.write(json_task_db)

    def get_tasks(self, filter=None):

        def perform_filtering(task):
            for attr, val in filter.items():
                if hasattr(task, attr):
                    if str(getattr(task, attr)) != str(val):
                        return True
            return False   
        
        tasks = self._read_tasks_from_db()

        if filter is None:
            return tasks

        tasks = [task for task in filterfalse(perform_filtering, tasks)]
        return tasks
        
    def save_task(self, task, resolve_tid=True):
        if resolve_tid:
            task.tid = self._create_next_task_id()

        tasks = self._read_tasks_from_db()
        for task_in_db in tasks:
            if task_in_db.tid == task.tid:
                raise TidAlreadyExists(task.tid)  

        tasks.append(task)
        self._write_tasks_in_db(tasks)
    
    def remove_task(self, task_id):
        tasks = self._read_tasks_from_db()
        
        for task_in_db in tasks:
            if task_in_db.tid == task.tid:
                raise TidAlreadyExists(task.tid)  

        tasks = [task for task in tasks if task.tid != task_id]
        self._write_tasks_in_db(tasks)

    def edit_task(self, edit_task):
        tasks = self._read_tasks_from_db()
        tasks = [task for task in tasks if task.tid != edit_task.tid]
        tasks.append(edit_task)
        self._write_tasks_in_db(tasks)

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