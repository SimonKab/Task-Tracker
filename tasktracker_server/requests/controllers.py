from tasktracker_server.model.task import Task
from tasktracker_server.storage.storage_adapters import TaskStorageAdapter
from tasktracker_server import console_response

class TaskController():

    @staticmethod
    def save_task(title, description, task_id = -1):
        task_id_present = TaskStorageAdapter.is_task_id_present(task_id)
        if task_id_present:
            console_response.show_task_id_present_error(task_id)
            return

        task = Task()
        if task_id >= 0:
            task.tid = task_id
        task.title = title
        task.description = description
        TaskStorageAdapter.save_task(task, task_id < 0)

    @staticmethod
    def fetch_tasks(tid=None, title=None, description=None):
        filter = {}
        if tid is not None:
            filter['tid'] = tid
        if title is not None:
            filter['title'] = title
        if description is not None:
            filter['description'] = description
        tasks = TaskStorageAdapter.get_tasks(filter)
        console_response.show_tasks_in_console(tasks)

    @staticmethod
    def remove_task(task_id):
        task_id_present = TaskStorageAdapter.is_task_id_present(task_id)
        if task_id_present:
            TaskStorageAdapter.remove_task(task_id)
        else:
            console_response.show_task_id_not_present_error(task_id)

    @staticmethod
    def edit_task(task_id, delete, title=None, description=None):
        task_id_present = TaskStorageAdapter.is_task_id_present(task_id)
        if not task_id_present:
            console_response.show_task_id_not_present_error(task_id)
            return

        tasks = TaskStorageAdapter.get_tasks(tid=task_id)
        for task in tasks:
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            for to_delete in delete:
                setattr(task, to_delete, None)
            TaskStorageAdapter.edit_task(task)