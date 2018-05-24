import unittest
import os
import datetime

from tasktracker_project.tasktracker_core.storage.sqlite_peewee_adapters import ProjectStorageAdapter
from tasktracker_project.tasktracker_core.storage.sqlite_peewee_adapters import UserStorageAdapter
from tasktracker_project.tasktracker_core.model.task import Task
from tasktracker_project.tasktracker_core.model.project import Project
from tasktracker_project.tasktracker_core.model.user import User
from tasktracker_project.tasktracker_core.model.plan import Plan
from tasktracker_project.tasktracker_core import utils

_TEST_DB = ':memory:'

class TestProject(unittest.TestCase):

    def setUp(self):
        self.storage = ProjectStorageAdapter(_TEST_DB)
        self.user_storage = UserStorageAdapter(_TEST_DB)
    
    def test_save_get_project(self):
        project = Project()
        project.creator = 1
        project.name = 'Test'

        user = User()
        user.login = 'test'
        self.user_storage.save_user(user)

        success = self.storage.save_project(project)
        self.assertEqual(success, True)

        projects_in_db = self.storage.get_projects(1)
        self.assertEqual(len(projects_in_db), 1)

        project.pid = 1
        self.assertEqual(project, projects_in_db[0])

    def test_save_edit_get_project(self):
        project = Project()
        project.creator = 1
        project.name = 'Test'

        user = User()
        user.login = 'test'
        self.user_storage.save_user(user)

        self.storage.save_project(project)

        project_fields = {Project.Field.pid: 1, Project.Field.name: 'New test'}
        success = self.storage.edit_project(project_fields)
        self.assertEqual(success, True)

        projects_in_db = self.storage.get_projects(1)
        self.assertEqual(len(projects_in_db), 1)

        project.pid = 1
        project.name = 'New test'
        self.assertEqual(project, projects_in_db[0])

    def test_save_remove_get_project(self):
        project1 = Project()
        project1.creator = 1
        project1.name = 'Test 1'

        project2 = Project()
        project2.creator = 1
        project2.name = 'Test 2'

        user = User()
        user.login = 'test'
        self.user_storage.save_user(user)

        self.storage.save_project(project1)
        self.storage.save_project(project2)

        success = self.storage.remove_project(2)
        self.assertEqual(success, True)

        projects_in_db = self.storage.get_projects(1)
        self.assertEqual(len(projects_in_db), 1)

        project1.pid = 1
        self.assertEqual(project1, projects_in_db[0])



    # def tearDown(self):
    #     os.remove(_TEST_DB)