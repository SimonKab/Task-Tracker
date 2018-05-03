import unittest
from tasktracker_server.storage.sqlite_adapters import TaskStorageAdapter
from tasktracker_server.model.task import Task
import os
import sqlite3

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
        
        self.storage.save_task(test_task)
        self.storage.save_task(test_task)

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
        
        self.storage.save_task(test_task_1)
        self.storage.save_task(test_task_2)
        self.storage.save_task(test_task_1)

        tasks_in_sqlite = self.storage.get_tasks({'title': 'vfdmk'})
        self.assertEqual(len(tasks_in_sqlite), 2)

        test_task_1.tid = 1
        self.assertEqual(tasks_in_sqlite[0], test_task_1)

        test_task_1.tid = 3
        self.assertEqual(tasks_in_sqlite[1], test_task_1)

    def test_save_get_title_tid_descr_filtered_tasks(self):
        test_task_1 = Task()
        test_task_1.title = 'vfdmk'
        test_task_1.description = 'vvkjndk'
        test_task_1.deadline_time = 23233

        test_task_2 = Task()
        test_task_2.title = 'lmlkmlkml'
        test_task_2.description = 'vvkjndk'
        test_task_2.deadline_time = 23233
        
        self.storage.save_task(test_task_1)
        self.storage.save_task(test_task_2)
        self.storage.save_task(test_task_1)

        tasks_in_sqlite = self.storage.get_tasks({'title': 'vfdmk'})
        self.assertEqual(len(tasks_in_sqlite), 2)

        test_task_1.tid = 1
        self.assertEqual(tasks_in_sqlite[0], test_task_1)

        test_task_1.tid = 3
        self.assertEqual(tasks_in_sqlite[1], test_task_1)
    
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

        self.storage.remove_task(tasks_in_db[0].tid)

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

        self.storage.save_task(test_task)
        self.storage.save_task(test_task)

        tasks_in_db = self.storage.get_tasks()

        edited_test_task.tid = tasks_in_db[0].tid
        self.storage.edit_task(edited_test_task)

        tasks_in_db_after_edit = self.storage.get_tasks()

        self.assertEqual(len(tasks_in_db_after_edit), 2)
        self.assertEqual(tasks_in_db_after_edit[0], edited_test_task)
        self.assertEqual(tasks_in_db_after_edit[1], tasks_in_db[1])

    def test_delete_not_existing_task(self):
        pass

    def test_use_without_connection(self):
        self.storage.disconnect()

        connected = self.storage.is_connected()
        self.assertEqual(connected, False)

        with self.assertRaises(ValueError):
            self.storage.disconnect()

        with self.assertRaises(ValueError):
            self.storage.get_tasks()

        with self.assertRaises(ValueError):
            task = Task()
            self.storage.save_task(task)

        with self.assertRaises(ValueError):
            self.storage.remove_task(0)

        with self.assertRaises(ValueError):
            task = Task()
            self.storage.edit_task(task)

    def tearDown(self):
        if self.storage.is_connected():
            self.storage.disconnect()
        os.remove(_TEST_DB)