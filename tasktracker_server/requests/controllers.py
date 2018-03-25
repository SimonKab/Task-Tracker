from tasktracker_server.model.task import Task
from tasktracker_server.storage.storage_adapters import TaskStorageAdapter

class TaskController():

    @staticmethod
    def save_task(id, name, description):
        task = Task()
        task.tid = id
        task.title = name
        task.description = description
        TaskStorageAdapter.save_task(task)

    @staticmethod
    def get_all_tasks():
        tasks = TaskStorageAdapter.get_tasks()
        return tasks