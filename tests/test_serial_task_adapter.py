import unittest
from tasktracker_server.storage.serial_task_adapter import TaskStorageAdapter
from tasktracker_server.model.task import Task
import os
import json
import pprint


_TEST_ID_DB = 'test_id.db'
_TEST_DB = 'test_task.db'

class TestTaskNewId(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(id_db_name=_TEST_ID_DB)

    def test_create_next_task_id(self):
        id_zero = self.storage._create_next_task_id()
        self.assertEqual(id_zero, 0)

        id_one = self.storage._create_next_task_id()
        self.assertEqual(id_one, 1)

        id_two = self.storage._create_next_task_id()
        self.assertEqual(id_two, 2)

        id_three = self.storage._create_next_task_id()
        self.assertEqual(id_three, 3)

        with open(_TEST_ID_DB, 'r') as id_db:
            id_db_content = json.loads(id_db.read())
            if 'task' not in id_db_content:
                raise ValueError('There is no task field inside db')

            task_count = 0
            for key, val in id_db_content.items():
                if key == 'task':
                    if val != 4:
                        raise ValueError('Wrong id number for task: {}'.format(val))
                    task_count += 1
            if task_count != 1:
                raise ValueError('Wrong task field count inside db: {}'.format(task_count))        

    def tearDown(self):
        os.remove(_TEST_ID_DB)

class TestEmptyTaskDb(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)

    def test_get_tasks_empty_list(self):
        tasks = self.storage.get_tasks()
        self.assertListEqual(tasks, [])

    def tearDown(self):
        os.remove(_TEST_DB)

class TestGetFromTaskDb(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)
        self._db_content = [{'tid': 0, 'title': 'zero', 'supposed_start_time': 2343434334434, 'deadline_time': 34980483508450},
                    {'tid': 1, 'title': 'first', 'supposed_start_time': 66556566565, 'deadline_time': 5345454545454},
                    {'tid': 2, 'title': 'second', 'supposed_start_time': 34334554, 'deadline_time': 34980483508450},
                    {'tid': 3, 'title': 'third', 'supposed_start_time': 344545353453, 'deadline_time': 34980483508450}]
        with open(_TEST_DB, 'w') as test_db:
            test_db.write(json.dumps(self._db_content))

    def test_get_all_tasks(self):
        tasks = self.storage.get_tasks()

        test_tasks = []
        for raw_test_task in self._db_content:
            task = Task()
            task.__dict__ = raw_test_task
            test_tasks.append(task)

        self.assertListEqual(tasks, test_tasks)

    def test_get_tasks_by_id(self):
        filter = {'tid': 0}
        tasks = self.storage.get_tasks(filter)

        test_task = Task()
        test_task.__dict__ = self._db_content[0]

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], test_task)

    def test_get_tasks_by_title(self):
        filter = {'title': 'first'}
        tasks = self.storage.get_tasks(filter)

        test_task = Task()
        test_task.__dict__ = self._db_content[1]

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], test_task)

    def test_get_tasks_by_deadline_time(self):
        filter = {'deadline_time': 34980483508450}
        tasks = self.storage.get_tasks(filter)

        task_zero = Task()
        task_zero.__dict__ = self._db_content[0]
        task_second = Task()
        task_second.__dict__ = self._db_content[2]
        task_third = Task()
        task_third.__dict__ = self._db_content[3]
        test_tasks = [task_zero, task_second, task_third]

        self.assertEqual(len(tasks), 3)
        self.assertListEqual(tasks, test_tasks)

    def tearDown(self):
        os.remove(_TEST_DB)

class TestAddToTaskDb(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)

    def test_add_task(self):
        task = Task()
        task.title = 'title'
        task.description = 'description'
        task.supposed_start_time = 40390934804
        task.supposed_end_time = 439039409009
        task.deadline_time = 49890438034980

        self.storage.save_task(task)

        test_task = Task()
        with open(_TEST_DB, 'r') as db:
            db_content = json.loads(db.read())
            self.assertEqual(len(db_content), 1)
            
            test_task.__dict__ = db_content[0]

        self.assertEqual(task, test_task)
        

    def tearDown(self):
        os.remove(_TEST_DB)

class TestEditInTaskDb(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)
        self._db_content = [{'tid': 0, 'title': 'zero', 'supposed_start_time': 2343434334434, 'deadline_time': 34980483508450},
                    {'tid': 1, 'title': 'first', 'supposed_start_time': 66556566565, 'deadline_time': 5345454545454},
                    {'tid': 2, 'title': 'second', 'supposed_start_time': 34334554, 'deadline_time': 34980483508450},
                    {'tid': 3, 'title': 'third', 'supposed_start_time': 344545353453, 'deadline_time': 34980483508450}]
        with open(_TEST_DB, 'w') as test_db:
            test_db.write(json.dumps(self._db_content))

    def test_edit_task(self):
        task = Task()
        task.tid = 1
        task.title = 'title'
        task.description = 'description'
        task.supposed_start_time = 40390934804
        task.supposed_end_time = 439039409009
        task.deadline_time = 49890438034980

        self.storage.edit_task(task)

        task_zero = Task()
        task_zero.__dict__ = self._db_content[0]
        task_second = Task()
        task_second.__dict__ = self._db_content[2]
        task_third = Task()
        task_third.__dict__ = self._db_content[3]
        supposed_db_content = [task_zero, task_second, task_third, task]

        with open(_TEST_DB, 'r') as db:
            db_content = json.loads(db.read())
            self.assertEqual(len(db_content), 4)
           
            real_db_content = []
            for task_in_db in db_content:
                test_task = Task()
                test_task.__dict__ = task_in_db
                real_db_content.append(test_task)

        self.assertListEqual(supposed_db_content, real_db_content)
        

    def tearDown(self):
        os.remove(_TEST_DB)


class TestRemoveFromTaskDb(unittest.TestCase):

    def setUp(self):
        self.storage = TaskStorageAdapter(_TEST_DB)
        self._db_content = [{'tid': 0, 'title': 'zero', 'supposed_start_time': 2343434334434, 'deadline_time': 34980483508450},
                    {'tid': 1, 'title': 'first', 'supposed_start_time': 66556566565, 'deadline_time': 5345454545454},
                    {'tid': 2, 'title': 'second', 'supposed_start_time': 34334554, 'deadline_time': 34980483508450},
                    {'tid': 3, 'title': 'third', 'supposed_start_time': 344545353453, 'deadline_time': 34980483508450}]
        with open(_TEST_DB, 'w') as test_db:
            test_db.write(json.dumps(self._db_content))

    def test_remove_task(self):
        self.storage.remove_task(1)

        task_zero = Task()
        task_zero.__dict__ = self._db_content[0]
        task_second = Task()
        task_second.__dict__ = self._db_content[2]
        task_third = Task()
        task_third.__dict__ = self._db_content[3]
        supposed_db_content = [task_zero, task_second, task_third]

        with open(_TEST_DB, 'r') as db:
            db_content = json.loads(db.read())
            self.assertEqual(len(db_content), 3)
           
            real_db_content = []
            for task_in_db in db_content:
                test_task = Task()
                test_task.__dict__ = task_in_db
                real_db_content.append(test_task)

        self.assertListEqual(supposed_db_content, real_db_content)
        

    def tearDown(self):
        os.remove(_TEST_DB)