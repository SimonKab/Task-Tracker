import unittest
import datetime

from tasktracker_core.requests.controllers import ProjectController, UserController, Controller
from tasktracker_core.model.task import Task, Status, Priority
from tasktracker_core.model.project import Project
from tasktracker_core.model.user import User
from tasktracker_core.model.plan import Plan
from tasktracker_core import utils

class TestProject(unittest.TestCase):

    def setUp(self):
        self.controllers = ProjectController()
        self.user_controller = UserController()

    def test_default_project_created_when_new_user_added(self):

        class ProjectStorageAdapterMock():

            _saved_project = None

            def save_project(self, project):
                self.__class__._saved_project = project
                return True

        class UserStorageAdapterMock():

            _saved_user = None

            def save_user(self, user):
                self.__class__._saved_user = user
                self.__class__._saved_user.uid = 1
                return True

            def check_user_existence(self, login):
                return False

            def get_last_saved_user(self):
                return self._saved_user

        Controller.init_storage_adapters(user_storage_adapter=UserStorageAdapterMock,
                              project_storage_adapter=ProjectStorageAdapterMock)

        user = User()
        user.login = 'new'
        self.user_controller.save_user(user)

        project = Project()
        project.creator = 1
        project.name = Project.default_project_name
        self.assertEqual(project, ProjectStorageAdapterMock._saved_project)

