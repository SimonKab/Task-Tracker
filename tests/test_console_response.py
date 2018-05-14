import unittest
import tasktracker_server.console_response as console_response
from tasktracker_server.model.task import Task

class OutputTest(unittest.TestCase):

    def test_build_tree(self):
        task_1 = Task()
        task_1.tid = 0
        task_1.parent_tid = None

        task_2 = Task()
        task_2.tid = 1
        task_2.parent_tid = 0

        task_3 = Task()
        task_3.tid = 2
        task_3.parent_tid = 0

        task_4 = Task()
        task_4.tid = 3
        task_4.parent_tid = 2

        task_5 = Task()
        task_5.tid = 4
        task_5.parent_tid = 3

        test_tree = [(0, task_1), (1, task_2), (1, task_3), (2, task_4), (3, task_5)]

        result_tree = []
        console_response.build_tree([task_5, task_2, task_3, task_1, task_4], result_tree)

        self.assertListEqual(test_tree, result_tree)



