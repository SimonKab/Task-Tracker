import unittest
from tasktracker_server.storage.sqlite_peewee_adapters import TaskStorageAdapter, UserStorageAdapter, PlanStorageAdapter
from tasktracker_server.model.task import Task
from tasktracker_server.model.user import User
from tasktracker_server.model.plan import Plan
from tasktracker_server import utils
import os
import datetime

_TEST_DB = 'test_tasktracker.db'

class TestTask(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)
        self.storage.connect()

    def test_save_get_tasks(self):
        test_task = Task()
        test_task.title = 'vfdmk'
        test_task.description = 'vvkjndk'
        test_task.deadline_time = 23233
        
        success = self.storage.save_task(test_task)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task)
        self.assertEqual(success, True)

        tasks_in_sqlite = self.storage.get_tasks()
        self.assertEqual(len(tasks_in_sqlite), 2)

        test_task.tid = 1
        self.assertEqual(tasks_in_sqlite[0], test_task)
        test_task.tid = 2
        self.assertEqual(tasks_in_sqlite[1], test_task)

    def test_save_get_title_filtered_tasks(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'lmlkmlkml'
        test_task_2.description = 'vvkjndk'
        test_task_2.deadline_time = 23233
        
        success = self.storage.save_task(test_task_1)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task_2)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task_1)
        self.assertEqual(success, True)

        filter = TaskStorageAdapter.Filter()
        filter.title('vfdmk')
        tasks_in_sqlite = self.storage.get_tasks(filter)
        self.assertEqual(len(tasks_in_sqlite), 2)

        test_task_1.tid = 1
        self.assertEqual(tasks_in_sqlite[0], test_task_1)

        test_task_1.tid = 3
        self.assertEqual(tasks_in_sqlite[1], test_task_1)

    def test_save_get_title_descr_filtered_tasks(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'lmlkmlkml'
        test_task_2.description = 'vvkjndk'
        test_task_2.deadline_time = 23233

        test_task_3 = Task()
        test_task_3.title = 'vfdmk'
        test_task_3.description = 'vvkjndk232332'
        test_task_3.deadline_time = 23233
        
        success = self.storage.save_task(test_task_1)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task_2)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task_3)
        self.assertEqual(success, True)

        filter = TaskStorageAdapter.Filter()
        filter.title('vfdmk')
        filter.description('vvkjndk232332')
        tasks_in_sqlite = self.storage.get_tasks(filter)
        self.assertEqual(len(tasks_in_sqlite), 1)

        test_task_3.tid = 3
        self.assertEqual(tasks_in_sqlite[0], test_task_3)

    def test_save_get_all_filtered_tasks(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        success = self.storage.save_task(test_task_1)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task_1)
        self.assertEqual(success, True)

        filter = TaskStorageAdapter.Filter()
        filter.title('2344243')
        tasks_in_sqlite = self.storage.get_tasks(filter)
        self.assertEqual(len(tasks_in_sqlite), 0)
    
    def test_save_remove_get_tasks(self):
        test_task = Task()
        test_task.title = 'flkmerfkl'
        test_task.description = 'lkfmelkf'
        test_task.supposed_start_time = 232332
        test_task.supposed_end_time = 3423
        test_task.deadline_time = 2442324
        test_task.notificate_deadline = True

        self.storage.save_task(test_task)
        self.storage.save_task(test_task)

        tasks_in_db = self.storage.get_tasks()

        success = self.storage.remove_task(tasks_in_db[0].tid)
        self.assertEqual(success, True)

        tasks_in_db_after_delete = self.storage.get_tasks()

        self.assertEqual(len(tasks_in_db_after_delete), 1)
        self.assertEqual(tasks_in_db_after_delete[0], tasks_in_db[1])

    def test_save_edit_get_tasks(self):
        test_task = Task()
        test_task.title = 'flkmerfkl'
        test_task.description = 'lkfmelkf'
        test_task.supposed_start_time = 232332
        test_task.supposed_end_time = 3423
        test_task.deadline_time = 2442324
        test_task.notificate_deadline = True

        edited_test_task = Task()
        edited_test_task.title = 'efnkrjf'
        edited_test_task.description = '23323223'
        edited_test_task.supposed_start_time = 232332
        edited_test_task.supposed_end_time = 23443
        edited_test_task.deadline_time = 2442324
        edited_test_task.notificate_deadline = False

        success = self.storage.save_task(test_task)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task)
        self.assertEqual(success, True)

        tasks_in_db = self.storage.get_tasks()

        edited_test_task.tid = tasks_in_db[0].tid
        success = self.storage.edit_task({Task.Field.tid: tasks_in_db[0].tid, 
                                Task.Field.title: 'efnkrjf', 
                                Task.Field.description: '23323223',
                                Task.Field.supposed_start_time: 232332,
                                Task.Field.supposed_end_time: 23443,
                                Task.Field.deadline_time: 2442324,
                                Task.Field.notificate_deadline: False})
        self.assertEqual(success, True)

        tasks_in_db_after_edit = self.storage.get_tasks()

        self.assertEqual(len(tasks_in_db_after_edit), 2)
        self.assertEqual(tasks_in_db_after_edit[0], edited_test_task)
        self.assertEqual(tasks_in_db_after_edit[1], tasks_in_db[1])

    def tearDown(self):
        if self.storage.is_connected():
            self.storage.disconnect()
        os.remove(_TEST_DB)

class TestTaskParentTid(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)
        self.storage.connect()    

    def test_save_get_single_parent_tid(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'lmlkmlkml'
        test_task_2.description = 'vvkjndk'
        test_task_2.deadline_time = 23233

        test_task_3 = Task()
        test_task_3.title = 'vfdmk'
        test_task_3.description = 'vvkjndk232332'
        test_task_3.deadline_time = 23233

        test_task_4 = Task()
        test_task_4.title = 'vfdmk'
        test_task_4.description = 'vvkjndk232332'
        test_task_4.deadline_time = 23233

        self.storage.save_task(test_task_1)
        test_task_2.parent_tid = 1
        test_task_3.parent_tid = 1
        self.storage.save_task(test_task_2)
        self.storage.save_task(test_task_3)
        self.storage.save_task(test_task_4)

        filter = TaskStorageAdapter.Filter()
        filter.parent_tid(1)
        tasks_with_parent_1 = self.storage.get_tasks(filter)
        self.assertEqual(len(tasks_with_parent_1), 2)

        test_task_2.tid = 2
        test_task_3.tid = 3
        self.assertEqual(tasks_with_parent_1[0], test_task_2)
        self.assertEqual(tasks_with_parent_1[1], test_task_3)

    def test_save_remove_get_single_parent_tid(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'lmlkmlkml'
        test_task_2.description = 'vvkjndk'
        test_task_2.deadline_time = 23233
        test_task_2.parent_tid = 1

        test_task_3 = Task()
        test_task_3.title = 'vfdmk'
        test_task_3.description = 'vvkjndk232332'
        test_task_3.deadline_time = 23233
        test_task_3.parent_tid = 1

        test_task_4 = Task()
        test_task_4.title = 'vfdmk'
        test_task_4.description = 'vvkjndk232332'
        test_task_4.deadline_time = 23233

        self.storage.save_task(test_task_1)
        self.storage.save_task(test_task_2)
        self.storage.save_task(test_task_3)
        self.storage.save_task(test_task_4)

        success = self.storage.remove_task(1)
        self.assertEqual(success, True)

        tasks_in_db = self.storage.get_tasks()
        self.assertEqual(len(tasks_in_db), 1)

        test_task_4.tid = 4
        self.assertEqual(tasks_in_db[0], test_task_4)

    def test_save_remove_get_multi_parent_tid(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'lmlkmlkml'
        test_task_2.description = 'vvkjndk'
        test_task_2.deadline_time = 23233

        test_task_3 = Task()
        test_task_3.title = 'vfdmk'
        test_task_3.description = 'vvkjndk232332'
        test_task_3.deadline_time = 23233

        test_task_4 = Task()
        test_task_4.title = 'vfdmk'
        test_task_4.description = 'vvkjndk232332'
        test_task_4.deadline_time = 23233

        self.storage.save_task(test_task_1)
        test_task_2.parent_tid = 1
        test_task_3.parent_tid = 2
        test_task_4.parent_tid = 2
        self.storage.save_task(test_task_2)
        self.storage.save_task(test_task_3)
        self.storage.save_task(test_task_4)

        success = self.storage.remove_task(1)
        self.assertEqual(success, True)

        tasks_in_db = self.storage.get_tasks()
        self.assertEqual(len(tasks_in_db), 0)

    def tearDown(self):
        if self.storage.is_connected():
            self.storage.disconnect()
        os.remove(_TEST_DB)

class TestUser(unittest.TestCase):

    def setUp(self):
        self.storage = UserStorageAdapter(_TEST_DB)
        self.storage.connect()

    def test_save_get_users(self):
        test_user = User()
        test_user.login = 'new login'
        test_user.password = '12345667'
        
        success = self.storage.save_user(test_user)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user)
        self.assertEqual(success, True)

        users_in_db = self.storage.get_users()
        self.assertEqual(len(users_in_db), 2)

        test_user.uid = 1
        self.assertEqual(users_in_db[0], test_user)
        test_user.uid = 2
        self.assertEqual(users_in_db[1], test_user)

    def test_save_get_login_filtered_users(self):
        test_user_1 = User()
        test_user_1.login = 'first login'
        test_user_1.password = '12345667'

        test_user_2 = User()
        test_user_2.login = 'second login'
        test_user_2.password = '12345667'
        
        success = self.storage.save_user(test_user_1)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user_2)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user_1)
        self.assertEqual(success, True)

        filter = UserStorageAdapter.Filter()
        filter.login('first login')
        users_in_db = self.storage.get_users(filter)
        self.assertEqual(len(users_in_db), 2)

        test_user_1.uid = 1
        self.assertEqual(users_in_db[0], test_user_1)

        test_user_1.uid = 3
        self.assertEqual(users_in_db[1], test_user_1)

    def test_save_get_login_online_filtered_users(self):
        test_user_1 = User()
        test_user_1.login = 'first login'
        test_user_1.password = '12345667'
        test_user_1.online = True

        test_user_2 = User()
        test_user_2.login = 'second login'
        test_user_2.password = '12345667'
        test_user_2.online = False

        test_user_3 = User()
        test_user_3.login = 'third login'
        test_user_3.password = '12345667'
        test_user_3.online = True

        success = self.storage.save_user(test_user_1)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user_2)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user_3)
        self.assertEqual(success, True)

        filter = UserStorageAdapter.Filter()
        filter.login('second login')
        filter.online(False)
        users_in_db = self.storage.get_users(filter)
        self.assertEqual(len(users_in_db), 1)

        test_user_2.uid = 2
        self.assertEqual(users_in_db[0], test_user_2)

    def test_save_get_all_filtered_users(self):
        test_user_1 = User()
        test_user_1.login = 'first login'
        test_user_1.password = '12345667'
        test_user_1.online = True

        success = self.storage.save_user(test_user_1)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user_1)
        self.assertEqual(success, True)

        filter = UserStorageAdapter.Filter()
        filter.login('first login')
        filter.online(False)    
        users_in_db = self.storage.get_users(filter)
        self.assertEqual(len(users_in_db), 0)
    
    def test_save_remove_get_users(self):
        test_user = User()
        test_user.login = 'login'
        test_user.password = '12345667'
        test_user.online = True

        success = self.storage.save_user(test_user)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user)
        self.assertEqual(success, True)

        users_in_db = self.storage.get_users()

        success = self.storage.delete_user(users_in_db[0].uid)
        self.assertEqual(success, True)

        users_in_db_after_delete = self.storage.get_users()

        self.assertEqual(len(users_in_db_after_delete), 1)
        self.assertEqual(users_in_db_after_delete[0], users_in_db[1])

    def test_save_edit_get_tasks(self):
        test_user = User()
        test_user.login = 'login'
        test_user.password = '12345667'
        test_user.online = True

        edited_test_user = User()
        edited_test_user.uid = 1
        edited_test_user.login = 'login 2'
        edited_test_user.password = '12345667'
        edited_test_user.online = False

        success = self.storage.save_user(test_user)
        self.assertEqual(success, True)
        success = self.storage.save_user(test_user)
        self.assertEqual(success, True)

        users_in_db = self.storage.get_users()

        success = self.storage.edit_user({User.Field.uid: 1,
                                        User.Field.login: 'login 2', 
                                        User.Field.online: False})
        self.assertEqual(success, True)

        users_in_db_after_edit = self.storage.get_users()

        self.assertEqual(len(users_in_db_after_edit), 2)
        self.assertEqual(users_in_db_after_edit[0], edited_test_user)
        self.assertEqual(users_in_db_after_edit[1], users_in_db[1])

    def tearDown(self):
        if self.storage.is_connected():
            self.storage.disconnect()
        os.remove(_TEST_DB)

class TestTaskUser(unittest.TestCase):

    def setUp(self):
        self.storage_task = TaskStorageAdapter(_TEST_DB)
        self.storage_task.connect()
        self.storage_user = UserStorageAdapter(_TEST_DB)
        self.storage_user.connect()

    def test_save_get_user_task(self):
        test_task = Task()
        test_task.title = 'title 1'
        test_task.description = 'description 1'
        test_task.deadline_time = 23233

        test_user = User()
        test_user.login = 'new login'
        test_user.password = '12345667'
        test_user.online = True

        self.storage_user.save_user(test_user)
        test_user.uid = self.storage_user.get_users()[0].uid
        test_task.uid = test_user.uid
        self.storage_task.save_task(test_task)

        filter = TaskStorageAdapter.Filter()
        filter.uid(test_user.uid)
        tasks_in_db = self.storage_task.get_tasks(filter)
        self.assertEqual(len(tasks_in_db), 1)

        test_task.tid = tasks_in_db[0].tid
        self.assertEqual(test_task, tasks_in_db[0])

    def test_save_task_remove_user(self):
        test_task_1 = Task()
        test_task_1.title = 'title 1'
        test_task_1.description = 'description 1'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'title 2'
        test_task_2.description = 'description 1'
        test_task_2.deadline_time = 23233

        test_user = User()
        test_user.login = 'new login'
        test_user.password = '12345667'
        test_user.online = True

        self.storage_user.save_user(test_user)
        test_user.uid = self.storage_user.get_users()[0].uid
        test_task_1.uid = test_user.uid
        self.storage_task.save_task(test_task_1)
        self.storage_task.save_task(test_task_2)

        self.storage_user.delete_user(test_user.uid)

        tasks_in_db = self.storage_task.get_tasks()
        self.assertEqual(len(tasks_in_db), 1)

        test_task_2.tid = tasks_in_db[0].tid
        self.assertEqual(test_task_2, tasks_in_db[0])

    def tearDown(self):
        if self.storage_task.is_connected():
            self.storage_task.disconnect()
        if self.storage_user.is_connected():
            self.storage_user.disconnect()
        os.remove(_TEST_DB)

class TestPlan(unittest.TestCase):

    def setUp(self):
        self.storage_plan = PlanStorageAdapter(_TEST_DB)
        self.storage_plan.connect()
        self.storage_task = TaskStorageAdapter(_TEST_DB)
        self.storage_task.connect()

    def test_save_plan(self):
        task1 = Task()
        task1.title = 'Title 1'

        task2 = Task()
        task2.title = 'Title 2'

        self.storage_task.save_task(task1)
        self.storage_task.save_task(task2)

        plan = Plan()
        plan.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan.exclude = [3, 5]
        plan.tid = 2

        success = self.storage_plan.save_plan(plan)
        self.assertEqual(success, True)

    def test_get_plans_for_common_tid(self):
        task1 = Task()
        task1.title = 'Title 1'

        task2 = Task()
        task2.title = 'Title 2'

        self.storage_task.save_task(task1)
        self.storage_task.save_task(task2)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = [3, 5]
        plan1.tid = 2

        plan2 = Plan()
        plan2.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=4))
        plan2.exclude = [2, 8]
        plan2.tid = 1

        self.storage_plan.save_plan(plan1)
        self.storage_plan.save_plan(plan2)

        plans = self.storage_plan.get_plans(common_tid=1)
        self.assertEqual(len(plans), 1)

        plan2.plan_id = 2

        self.assertEqual(plans[0], plan2)

    def test_plans_delete_repeat(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = [3, 5]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        self.storage_plan.delete_plan_repeat(1, 8)

        plan_in_database = self.storage_plan.get_plans(plan_id=1)[0]

        plan1.plan_id = 1
        plan1.exclude.append(8)

        self.assertEqual(plan_in_database, plan1)

    def test_plans_restore_repeat(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = [3, 5]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        self.storage_plan.delete_plan_repeat(1, 8)
        success = self.storage_plan.restore_plan_repeat(1, 8)
        self.assertEqual(success, True)
        
        plan_in_database = self.storage_plan.get_plans(plan_id=1)[0]

        plan1.plan_id = 1
        self.assertEqual(plan_in_database, plan1)

    def test_plans_edit_repeat(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = []
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        task2 = Task()
        task2.title = 'Title 2'

        self.storage_task.save_task(task2)

        success = self.storage_plan.edit_plan_repeat(1, 8, 2)
        self.assertEqual(success, True)

        plan_in_db = self.storage_plan.get_plans(1)[0]

        plan1.plan_id = 1
        plan1.exclude.append(8)
        self.assertEqual(plan_in_db, plan1)

    def test_exclude_delete_type(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = []
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        self.storage_plan.delete_plan_repeat(1, 8)
        exclude_type = self.storage_plan.get_exclude_type(1, 8)
        self.assertEqual(exclude_type, Plan.PlanExcludeKind.DELETED)

    def test_exclude_edit_type(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        task2 = Task()
        task2.title = 'Title 2'

        self.storage_task.save_task(task2)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = []
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        self.storage_plan.edit_plan_repeat(1, 8, 2)
        exclude_type = self.storage_plan.get_exclude_type(1, 8)
        self.assertEqual(exclude_type, Plan.PlanExcludeKind.EDITED)

    def test_make_shift_bigger(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        plan1.exclude = [0, 1, 2, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        new_shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=6))
        success = self.storage_plan.edit_plan(1, shift=new_shift)
        self.assertEqual(success, True)

        plans = self.storage_plan.get_plans(plan_id=1)[0]

        plan1.plan_id = 1
        plan1.shift = new_shift
        plan1.exclude = [0, 1, 2]
        self.assertEqual(plans, plan1)

    def test_make_shift_smaller(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=10))
        plan1.exclude = [0, 1, 3, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        new_shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=3))
        success = self.storage_plan.edit_plan(1, shift=new_shift)
        self.assertEqual(success, True)

        plans = self.storage_plan.get_plans(plan_id=1)[0]

        plan1.plan_id = 1
        plan1.shift = new_shift
        plan1.exclude = [0, 10]
        self.assertEqual(plans, plan1)

    def test_remove_plan(self):
        task1 = Task()
        task1.title = 'Title 1'

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=10))
        plan1.exclude = [0, 1, 3, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        success = self.storage_plan.remove_plan(1)
        self.assertEqual(success, True)
        
        plans = self.storage_plan.get_plans(plan_id=1)
        self.assertEqual(plans, [])

    def test_recalculate_exclude_when_start_time_shifted_forward(self):
        task1 = Task()
        task1.title = 'Title 1'
        task1.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=2))
        plan1.exclude = [0, 1, 3, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        new_time = utils.datetime_to_milliseconds(datetime.datetime.today() + datetime.timedelta(days=4))
        self.storage_task.edit_task({Task.Field.tid: 1, Task.Field.supposed_start_time: new_time})

        start_time_shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=4))
        success = self.storage_plan.recalculate_exclude_when_start_time_shifted(1, start_time_shift)
        self.assertEqual(success, True)

        plan = self.storage_plan.get_plans(plan_id=1)[0]
        plan1.plan_id = 1
        plan1.exclude = [1, 2]
        self.assertEqual(plan, plan1)

    def test_recalculate_exclude_when_start_time_shifted_differ(self):
        task1 = Task()
        task1.title = 'Title 1'
        task1.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=2))
        plan1.exclude = [0, 1, 3, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        new_time = utils.datetime_to_milliseconds(datetime.datetime.today() + datetime.timedelta(days=1))
        self.storage_task.edit_task({Task.Field.tid: 1, Task.Field.supposed_start_time: new_time})

        start_time_shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=1))
        success = self.storage_plan.recalculate_exclude_when_start_time_shifted(1, start_time_shift)
        self.assertEqual(success, True)

        plan = self.storage_plan.get_plans(plan_id=1)[0]
        plan1.plan_id = 1
        plan1.exclude = []
        self.assertEqual(plan, plan1)

    def test_recalculate_exclude_when_start_time_shifted_backward(self):
        task1 = Task()
        task1.title = 'Title 1'
        task1.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())

        self.storage_task.save_task(task1)

        plan1 = Plan()
        plan1.shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=2))
        plan1.exclude = [0, 1, 3, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        new_time = utils.datetime_to_milliseconds(datetime.datetime.today() - datetime.timedelta(days=4))
        self.storage_task.edit_task({Task.Field.tid: 1, Task.Field.supposed_start_time: new_time})

        start_time_shift = utils.datetime_to_milliseconds(datetime.datetime.utcfromtimestamp(0) + datetime.timedelta(days=4))
        success = self.storage_plan.recalculate_exclude_when_start_time_shifted(1, -start_time_shift)
        self.assertEqual(success, True)

        plan = self.storage_plan.get_plans(plan_id=1)[0]
        plan1.plan_id = 1
        plan1.exclude = [2, 3, 5, 6]
        self.assertEqual(plan, plan1)

    def test_remove_task_when_its_common_for_plan(self):

        task1 = Task()
        task1.title = 'Title 1'
        task1.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())

        task2 = Task()
        task2.title = 'Title 2'
        task2.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())

        self.storage_task.save_task(task1)
        self.storage_task.save_task(task2)

        plan1 = Plan()
        plan1.shift = utils.create_shift_in_millis(datetime.timedelta(days=2))
        plan1.exclude = [0, 1, 3, 4]
        plan1.tid = 1

        self.storage_plan.save_plan(plan1)

        success = self.storage_task.remove_task(1)
        self.assertEqual(success, True)

        tasks = self.storage_task.get_tasks()
        self.assertEqual(len(tasks), 1)

        task2.tid = 2
        self.assertEqual(tasks[0], task2)

        plans = self.storage_plan.get_plans()
        self.assertEqual(len(plans), 0)

    def tearDown(self):
        self.storage_plan.disconnect()
        self.storage_task.disconnect()
        os.remove(_TEST_DB)
