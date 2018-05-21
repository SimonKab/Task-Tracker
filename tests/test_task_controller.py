import unittest
import datetime

from tasktracker_server.requests.controllers import TaskController, Controller
from tasktracker_server.model.task import Task, Status, Priority
from tasktracker_server.model.plan import Plan
from tasktracker_server import utils

class TestTaskController(unittest.TestCase):

    def setUp(self):
        self.controller = TaskController()

    def test_get_plan_tasks_by_time_range(self):

        class PlanStorageAdapterMock():
            
            def get_plans(self, plan_id):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = utils.create_shift_in_millis(datetime.timedelta(days=3))
                plan.exclude = [5]
                return [plan]

        class TaskStorageAdapterMock():
            
            class Filter():

                def tid(self, tid):
                    pass

            def get_tasks(self, filter):
                task = Task()
                task.tid = 1
                task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
                task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=2))
                return [task]

        Controller.init_storage_adapters(PlanStorageAdapterMock, TaskStorageAdapterMock)

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=10)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=17)))
        tasks = self.controller.get_plan_tasks_by_time_range(1, time_range)
        self.assertEqual(len(tasks), 2)

        task1 = Task()
        task1.tid = 1
        task1.supposed_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=9))
        task1.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=11))

        self.assertEqual(task1, tasks[0])

        task2 = Task()
        task2.tid = 1
        task2.supposed_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=12))
        task2.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=14))

        self.assertEqual(task2, tasks[1])