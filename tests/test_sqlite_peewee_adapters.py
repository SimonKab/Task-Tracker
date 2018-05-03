import unittest
from tasktracker_server.storage.sqlite_peewee_adapters import TaskStorageAdapter, UserStorageAdapter
from tasktracker_server.model.task import Task
from tasktracker_server.model.user import User
import os
import sqlite3

_TEST_DB = 'test_tasktracker.db'

class TestCommon(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)

    def test_connect_disconnect(self):
        self.storage.connect()
        self.storage.disconnect()

    def test_disconnect_when_not_connect(self):
        self.storage.disconnect()

    def test_is_single_connected(self):
        self.storage.connect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, True)

        self.storage.disconnect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, False)

    def test_is_multi_connected(self):
        self.storage.connect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, True)

        self.storage.connect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, True)

        self.storage.connect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, True)

        self.storage.disconnect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, True)

        self.storage.disconnect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, True)

        self.storage.disconnect()
        is_connected = self.storage.is_connected()
        self.assertEqual(is_connected, False)

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

        success = self.storage.save_task(test_task)
        self.assertEqual(success, True)
        success = self.storage.save_task(test_task)
        self.assertEqual(success, True)

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