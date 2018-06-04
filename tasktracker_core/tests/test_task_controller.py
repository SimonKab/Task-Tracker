import unittest
import datetime

from tasktracker_core.requests.controllers import TaskController, Controller, InvalidParentIdError
from tasktracker_core.model.task import Task, Status, Priority
from tasktracker_core.model.plan import Plan
from tasktracker_core.model.user import User
from tasktracker_core.model.project import Project
from tasktracker_core import utils

class TestTaskController(unittest.TestCase):

    def setUp(self):
        self.controller = TaskController()

    def test_save_invalide_task_parent_id(self):

        class TaskStorageAdapterMock():
            
            class Filter():

                def tid(self, tid):
                    pass

            def get_tasks(self, filter):
                return []

            def save_task(self, task):
                pass

        class ProjectStorageAdapterMock():

            def get_projects(self, uid, name=None, pid=None):
                project = Project()
                project.creator = 1
                project.name = Project.default_project_name
                return [project]

        class UserStorageAdapterMock():

            def get_users(self, uid):
                user = User()
                return [user]

        Controller.init_storage_adapters(task_storage_adapter=TaskStorageAdapterMock,
                                         user_storage_adapter=UserStorageAdapterMock,
                                         project_storage_adapter=ProjectStorageAdapterMock)
        Controller.authentication(1)

        with self.assertRaises(InvalidParentIdError):
            TaskController.save_task(parent_tid=3)


    def test_get_plan_tasks_by_time_range(self):

        class PlanStorageAdapterMock():
            
            def get_plans(self, plan_id):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = 3000
                plan.exclude = [5]
                return [plan]

        class TaskStorageAdapterMock():
            
            class Filter():

                def tid(self, tid):
                    pass

            def get_tasks(self, filter):
                task = Task()
                task.tid = 1
                task.supposed_start_time = 0
                task.supposed_end_time = 2000
                return [task]

        class ProjectStorageAdapterMock():

            def get_projects(self, uid, name=None, pid=None):
                project = Project()
                project.creator = 1
                project.name = Project.default_project_name
                return [project]

        class UserStorageAdapterMock():

            def get_users(self, uid):
                user = User()
                return [user]

        Controller.init_storage_adapters(PlanStorageAdapterMock, 
            TaskStorageAdapterMock, UserStorageAdapterMock, ProjectStorageAdapterMock)
        Controller.authentication(1)

        time_range = (10000, 17000)
        tasks = self.controller.get_plan_tasks_by_time_range(1, time_range)
        self.assertEqual(len(tasks), 2)

        task1 = Task()
        task1.tid = 1
        task1.supposed_start_time = 9000
        task1.supposed_end_time = 11000

        self.assertEqual(task1.__dict__, tasks[0].__dict__)

        task2 = Task()
        task2.tid = 1
        task2.supposed_start_time = 12000
        task2.supposed_end_time = 14000

        self.assertEqual(task2, tasks[1])