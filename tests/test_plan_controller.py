import unittest
import datetime

from tasktracker_server.requests.controllers import PlanController
from tasktracker_server.model.task import Task
from tasktracker_server.model.plan import Plan
from tasktracker_server import utils

class TestPlanController(unittest.TestCase):

    def setUp(self):
        self.controller = PlanController()

    def test_delete_repeats_from_plan_by_time_range(self):

        class PlanStorageAdapterMock():
            
            _deleted_numbers = []

            def connect(self):
                pass

            def get_plans(self, plan_id):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = utils.create_shift_in_millis(datetime.timedelta(days=3))
                return plan

            def delete_plan_repeat(self, plan_id, number):
                if plan_id == 1:
                    self._deleted_numbers.append(number)

            def disconnect(self):
                pass

        class TaskStorageAdapterMock():
            
            def connect(self):
                pass

            def get_tasks(self, filter):
                task = Task()
                task.tid = 1
                task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
                task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=3))
                return task

            def disconnect(self):
                pass

        PlanController.init_storage_adapters(PlanStorageAdapterMock, TaskStorageAdapterMock)

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=10)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=20)))
        success = self.controller.delete_repeats_from_plan_by_time_range(1, time_range)
        self.assertEqual(success, True)

        deleted_numbers = PlanStorageAdapterMock._deleted_numbers
        self.assertEqual(deleted_numbers, [4, 5, 6, 7])