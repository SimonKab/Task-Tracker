import unittest
import datetime

from tasktracker_server.model.task import Task
from tasktracker_server import utils

class TestTask(unittest.TestCase):

    def test_shift_task_forward(self):
        task = Task()
        task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=4))

        shift_time = utils.create_shift_in_millis(datetime.timedelta(days=4))
        task.shift_time(shift_time)

        test_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=4))
        test_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=8))

        if test_start_time - task.supposed_start_time == 1:
            test_start_time -= 1

        if test_end_time - task.supposed_end_time == 1:
            test_end_time -= 1

        self.assertEqual(task.supposed_start_time, test_start_time)
        self.assertEqual(task.supposed_end_time, test_end_time)
        self.assertEqual(task.deadline_time, None)

    def test_shift_task_backward(self):
        task = Task()
        task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=4))

        shift_time = utils.create_shift_in_millis(datetime.timedelta(days=-4))
        task.shift_time(shift_time)

        test_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=-4))
        test_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=0))

        if test_start_time - task.supposed_start_time == 1:
            test_start_time -= 1

        if test_end_time - task.supposed_end_time == 1:
            test_end_time -= 1

        self.assertEqual(task.supposed_start_time, test_start_time)
        self.assertEqual(task.supposed_end_time, test_end_time)
        self.assertEqual(task.deadline_time, None)

    def test_is_after_time(self):
        task = Task()
        task.supposed_start_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=9))
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=10))

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=5)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=8)))
        is_after = task.is_after_time(time_range)
        self.assertEqual(is_after, True)

    def test_is_before_time(self):
        task = Task()
        task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=3))

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=5)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=8)))
        is_before = task.is_before_time(time_range)
        self.assertEqual(is_before, True)

    def test_is_time_overlap(self):
        task = Task()
        task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=6))

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=5)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=8)))

        is_overlap = task.is_time_overlap(time_range)
        self.assertEqual(is_overlap, True)

    def test_is_time_overlap_fully(self):
        task = Task()
        task.supposed_start_time = utils.datetime_to_milliseconds(datetime.datetime.today())
        task.supposed_end_time = utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=6))

        time_range = (utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=0)),
                      utils.shift_datetime_in_millis(datetime.datetime.today(), datetime.timedelta(days=6)))

        is_overlap = task.is_time_overlap_fully(time_range)
        self.assertEqual(is_overlap, True)