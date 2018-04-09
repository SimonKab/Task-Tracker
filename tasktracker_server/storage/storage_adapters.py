from ..model.task import Task
import json
import os

class TaskStorageAdapter():

    @staticmethod
    def get_tasks(filter):
        tasks = []
        if os.path.exists('task.db'):
            db = open('task.db', 'r')
            try:
                raw_data = json.loads(db.read())
                for raw_task in raw_data:
                    task = Task()
                    task.__dict__ = raw_task
                    tasks.append(task)
            except json.JSONDecodeError:
                print("JSON decode ERROR")
            db.close()

        for i in reversed(range(len(tasks))):
            task = tasks[i]
            for arg, val in filter.items():
                if hasattr(task, arg):
                    if not str(getattr(task, arg)) == str(val):
                        del tasks[i]

        return tasks

    @staticmethod
    def save_task(task, resolve_tid=True):
        tasks = TaskStorageAdapter.get_tasks()
        tasks.append(task)

        if resolve_tid:
            task.tid = TaskStorageAdapter.create_next_task_id()

        tasks_dic = [task.__dict__ for task in tasks]

        task_db_file = open('task.db', 'w')
        json_task_db = json.dumps(tasks_dic)
        task_db_file.write(json_task_db)
        task_db_file.close()

        return True
    
    @staticmethod
    def remove_task(task_id):
        tasks = TaskStorageAdapter.get_tasks()

        tasks_dic = []
        for task in tasks:
            if not task.tid == task_id:
                tasks_dic.append(task.__dict__)

        task_db_file = open('task.db', 'w')
        json_task_db = json.dumps(tasks_dic)
        task_db_file.write(json_task_db)
        task_db_file.close()

    @staticmethod
    def edit_task(edit_task):
        tasks = TaskStorageAdapter.get_tasks()

        tasks_dic = []
        for task in tasks:
            if task.tid == edit_task.tid:
                tasks_dic.append(edit_task.__dict__)
            else:
                tasks_dic.append(task.__dict__)

        task_db_file = open('task.db', 'w')
        json_task_db = json.dumps(tasks_dic)
        task_db_file.write(json_task_db)
        task_db_file.close()

    @staticmethod
    def is_task_id_present(task_id):
        tasks = TaskStorageAdapter.get_tasks()

        present = False
        for task in tasks:
            if task.tid == task_id:
                present = True
                break

        return present

    @staticmethod
    def create_next_task_id():
        try:
            id_db_file = open('id.db', 'r')
        except FileNotFoundError:
            id_db_file = open('id.db', 'w+')

        json_id_db_file_content = str(id_db_file.read())
        if len(json_id_db_file_content) == 0:
            id_db_file_content = {'task':'0'}
        else:
            id_db_file_content = json.loads(json_id_db_file_content)

        task_id = int(id_db_file_content.get('task', '0'))
        id_db_file_content['task'] = task_id + 1

        json_id_db_file_content = json.dumps(id_db_file_content)
        id_db_file.close()
        id_db_file = open('id.db', 'w')
        id_db_file.write(json_id_db_file_content)
        id_db_file.close()

        return task_id