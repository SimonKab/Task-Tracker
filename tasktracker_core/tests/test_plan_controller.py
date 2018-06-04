import unittest
import datetime

from tasktracker_core.requests.controllers import PlanController, Controller
from tasktracker_core.model.task import Task, Status, Priority
from tasktracker_core.model.plan import Plan
from tasktracker_core.model.user import User
from tasktracker_core.model.project import Project
from tasktracker_core import utils

class TestPlanController(unittest.TestCase):

    def setUp(self):
        self.controller = PlanController()

    def test_delete_repeats_from_plan_by_time_range(self):

        class PlanStorageAdapterMock():
            
            _deleted_numbers = []

            def get_plans(self, plan_id):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = utils.create_shift_in_millis(datetime.timedelta(days=3))
                return [plan]

            def delete_plan_repeat(self, plan_id, number):
                if plan_id == 1:
                    self._deleted_numbers.append(number)
                    return True
                return False

            def get_tid_for_edit_repeat(self, plan_id, number):
                return None

            def get_exclude_type(self, plan_id, number):
                return None

        class TaskStorageAdapterMock():

            def get_tasks(self, filter):
                task = Task()
                task.tid = 1
                task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
                task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=3))
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

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=10)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=20)))
        success = self.controller.delete_repeats_from_plan_by_time_range(1, time_range)
        self.assertEqual(success, True)

        deleted_numbers = PlanStorageAdapterMock._deleted_numbers
        self.assertEqual(deleted_numbers, [3, 4, 5, 6])

    def test_get_repeats_by_time_range(self):

        class PlanStorageAdapterMock():
            
            _deleted_numbers = []

            def get_plans(self, plan_id):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = utils.create_shift_in_millis(datetime.timedelta(days=3))
                plan.exclude = [4, 5]
                return [plan]

        class TaskStorageAdapterMock():

            def get_tasks(self, filter):
                task = Task()
                task.tid = 1
                task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
                task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=3))
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

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=10)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=20)))
        repeats = self.controller.get_repeats_by_time_range(1, time_range)
        self.assertEqual(repeats, [3, 6])

    def test_edit_repeat_by_number(self):

        class PlanStorageAdapterMock():
            
            _plan_id = None
            _number = None
            _tid = None

            def get_plans(self, plan_id=None, common_tid=None):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = utils.create_shift_in_millis(datetime.timedelta(days=3))
                plan.exclude = [5]
                return [plan]

            def edit_plan_repeat(self, plan_id, number, tid):
                self.__class__._plan_id = plan_id
                self.__class__._number = number
                self.__class__._tid = tid
                return True

            def get_tid_for_edit_repeat(self, plan_id, number):
                return 2

        class TaskStorageAdapterMock():

            _saved_task = None

            _removed_tid = None

            class Filter():

                def tid(self, tid):
                    self._tid = tid

                def uid(self, uid):
                    self._uid = uid

            def get_tasks(self, filter):
                tid = getattr(filter, '_tid', None)
                if tid is not None and tid == 1:
                    task = Task()
                    task.tid = 1
                    task.status = Status.PENDING
                    task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
                    task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=2))
                    task.notificate_supposed_start=False
                    return [task]
                if tid is not None and tid == 2:
                    task = Task()
                    task.tid = 2
                    task.status = Status.PENDING
                    task.supposed_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=9))
                    task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=11))
                    task.notificate_deadline=True
                    return [task]
                return []

            def remove_task(self, tid):
                self.__class__._removed_tid = tid
                return True

            def save_task(self, task):
                self.__class__._saved_task = task
                return True

            def get_last_saved_task(self):
                self._saved_task.tid = 3
                return self._saved_task

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

        success = self.controller.edit_repeat_by_number(1, 3, status=Status.COMPLETED,
                                              notificate_supposed_start=True)
        self.assertEqual(success, True)

        task = Task()
        task.tid = 3
        task.status = Status.COMPLETED
        task.supposed_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=9))
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=11))
        task.notificate_supposed_start=True

        if task.supposed_start_time - TaskStorageAdapterMock._saved_task.supposed_start_time == 1:
            task.supposed_start_time -= 1
        if task.supposed_end_time - TaskStorageAdapterMock._saved_task.supposed_end_time == 1:
            task.supposed_end_time -= 1

        self.assertEqual(TaskStorageAdapterMock._saved_task.__dict__, task.__dict__)
        self.assertEqual(TaskStorageAdapterMock._removed_tid, 2)
        self.assertEqual(PlanStorageAdapterMock._plan_id, 1)
        self.assertEqual(PlanStorageAdapterMock._number, 3)
        self.assertEqual(PlanStorageAdapterMock._tid, 3)

    def test_get_repeats_by_time_range(self):

        class PlanStorageAdapterMock():
            
            def get_plans(self, plan_id):
                plan = Plan()
                plan.tid = 1
                plan.plan_id = 1
                plan.shift = utils.create_shift_in_millis(datetime.timedelta(days=3))
                plan.exclude = [5]
                plan.end = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=10))
                return [plan]

        class TaskStorageAdapterMock():

            _saved_task = None

            def get_tasks(self, filter):
                task = Task()
                task.tid = 1
                task.status = Status.PENDING
                task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
                task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=2))
                task.notificate_supposed_start=False
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

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=8)),
                    utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=30)))
        repeats = self.controller.get_repeats_by_time_range(1, time_range)
        self.assertEqual(repeats, [2, 3])

def timestamp_to_display(timestamp):
    if timestamp is not None:
        return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y')