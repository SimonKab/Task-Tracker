import unittest
import datetime

from tasktracker_core import utils

class TestUtil(unittest.TestCase):

    def test_parse_full_simple_date(self):
        arg = '2-3-2018'
        result_of_parse = utils.parse_date(arg)
        correct_result = datetime.datetime.strptime(arg, "%d-%m-%Y")
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_relative_today_date(self):
        arg = 'today'
        correct_result = utils.today()
        result_of_parse = utils.parse_date(arg)
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_relative_today_plus_2_date(self):
        arg = 'today+2'
        correct_result = utils.today() + datetime.timedelta(days=2)
        result_of_parse = utils.parse_date(arg)
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_relative_today_minus_2_date(self):
        arg = 'today-2'
        correct_result = utils.today() - datetime.timedelta(days=2)
        result_of_parse = utils.parse_date(arg)
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_full_simple_time(self):
        arg = '2:30'
        result_of_parse = utils.parse_time(arg)
        correct_result = datetime.datetime.strptime(arg, "%H:%M").time()
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_relative_now_time(self):
        arg = 'now'
        correct_result = utils.now().time()
        result_of_parse = utils.parse_time(arg)
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_relative_now_plus_2_time(self):
        arg = 'now+2'
        today_with_time = datetime.datetime.combine(utils.today(), utils.now().time())
        correct_result = (today_with_time + datetime.timedelta(hours=int(2))).time()
        result_of_parse = utils.parse_time(arg)
        self.assertEqual(result_of_parse, correct_result)

    def test_parse_relative_now_minus_2_time(self):
        arg = 'now-2'
        today_with_time = datetime.datetime.combine(utils.today(), utils.now().time())
        correct_result = (today_with_time - datetime.timedelta(hours=int(2))).time()
        result_of_parse = utils.parse_time(arg)
        self.assertEqual(result_of_parse, correct_result)