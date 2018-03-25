from ..model.task import Task
import json
import os

class TaskStorageAdapter():

    @staticmethod
    def get_tasks():
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
        return tasks

    @staticmethod
    def save_task(task):
        tasks = TaskStorageAdapter.get_tasks()
        tasks.append(task)

        dic = [task.__dict__ for task in tasks]

        db = open('task.db', 'w')
        json_representation = json.dumps(dic)
        db.write(json_representation)
        db.close()

        return True