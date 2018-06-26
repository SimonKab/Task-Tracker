from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.core.exceptions import PermissionDenied

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.conf import settings

import datetime
import pytz

from .forms import TaskForm, ProjectForm

from tasktracker_core.requests.controllers import (Controller, 
                                                   TaskController, 
                                                   ProjectController, 
                                                   UserController,
                                                   AuthenticationError)
from tasktracker_core import utils
from tasktracker_core.model.task import Status
from tasktracker_core.model.project import Project

class VisualTaskData():

    def __init__(self):
        self.tid = 0
        self.uid = None
        self.pid = None
        self.parent_tid = None
        self.title = None
        self.description = None
        self.priority = None
        self.status = None
        self.supposed_start_time = None
        self.supposed_end_time = None
        self.deadline_time = None
        self.notificate_supposed_start = False
        self.notificate_supposed_end = False
        self.notificate_deadline = False

    @staticmethod
    def timestamp_to_display(timestamp):
            if timestamp is not None:
                unaware = datetime.datetime.utcfromtimestamp(timestamp / 1000.0)
                unaware_utc = unaware.replace(tzinfo=pytz.utc)
                aware = unaware_utc.astimezone(pytz.timezone(settings.TIME_ZONE))
                return aware.strftime('%d.%m.%Y %H:%M')

    @classmethod
    def from_lib_task(cls, lib_task):
        visual_task = VisualTaskData()
        
        visual_task.tid = lib_task.tid
        visual_task.uid = lib_task.uid
        visual_task.pid = lib_task.pid
        visual_task.parent_tid = lib_task.parent_tid
        visual_task.title = lib_task.title
        visual_task.description = lib_task.description
        visual_task.priority = lib_task.priority
        visual_task.status = lib_task.status
        visual_task.notificate_supposed_start = lib_task.notificate_supposed_start
        visual_task.notificate_supposed_end = lib_task.notificate_supposed_end
        visual_task.notificate_deadline = lib_task.notificate_deadline

        visual_task.supposed_start_time = cls.timestamp_to_display(lib_task.supposed_start_time)
        visual_task.supposed_end_time = cls.timestamp_to_display(lib_task.supposed_end_time)
        visual_task.deadline_time = cls.timestamp_to_display(lib_task.deadline_time)

        return visual_task

    def get_project_name(self):
        projects = ProjectController.fetch_projects(pid=self.pid)
        if projects is not None and len(projects) != 0:
            return projects[0].name

class VisualProjectData():

    def __init__(self):
        self.pid = None
        self.creator = None
        self.name = None
        self.admins = None
        self.guests = None

    @classmethod
    def from_lib_project(cls, lib_project):
        visual_project = VisualProjectData()

        visual_project.pid = lib_project.pid
        visual_project.creator = lib_project.creator
        visual_project.name = lib_project.name
        visual_project.admins = lib_project.admins
        visual_project.guests = lib_project.guests

        return visual_project

    def get_participiant_names_and_status(self):
        def get_user_names_kinds_list(user_id_list, user_kind):
            user_names_kinds_list = []
            for user_id in user_id_list:
                user = UserController.fetch_user(uid=user_id)
                if user is not None and len(user) != 0:
                    user_names_kinds_list.append((user[0].login, user_kind))
            return user_names_kinds_list

        participiants = []
        if self.creator is not None:
            participiants += get_user_names_kinds_list([self.creator], Project.UserKind.CREATOR)

        if self.admins is not None:
            participiants += get_user_names_kinds_list(self.admins, Project.UserKind.ADMIN)

        if self.guests is not None:
            participiants += get_user_names_kinds_list(self.guests, Project.UserKind.GUEST)

        return participiants

    @staticmethod
    def normalize_visual_names(visual_names):
        def add_login_to_project_name(project):
            users = UserController.fetch_user(project.creator)
            if users is not None and len(users) != 0:
                project.name += " ({})".format(users[0].login)

        for head in range(len(visual_names)):
            for rest in range(head + 1, len(visual_names)):
                first = visual_names[head]
                second = visual_names[rest]
                if first.name == second.name:
                    add_login_to_project_name(first)
                    add_login_to_project_name(second)

def relogin_lib(method):
    def check(request, *args, **kwargs):
        if (request.user.is_authenticated
            and not Controller.is_authenticated()):
            Controller.authentication_by_login(request.user.username)
        return method(request, *args, **kwargs)
    return check

def log_in_user(request, username, password):
    try:
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            Controller.authentication_by_login(username)
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
    except AuthenticationError:
        auth_logout(request)
        request.session['login_library_error_message'] = 'Login or passwrod is not valid'
        return HttpResponseRedirect(reverse('core:index')) 
    except PermissionDenied:
        pass

    return HttpResponseRedirect(reverse('core:index')) 

def index(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')
            return log_in_user(request, username, raw_password)
    else:
        form = AuthenticationForm()

    common_error = None
    error_message = request.session.pop('login_library_error_message', None)
    if error_message is not None:
        common_error = [error_message]
    
    if len(form.errors) > 0:
        common_error = form.errors.get('__all__')
    return render(request, 'core/index.html', {'form': form, 'common_error': common_error})

def register(request):
    if request.method == "POST":
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            UserController.save_user(login=username)

            raw_password = form.cleaned_data.get('password1')
            return log_in_user(request, username, raw_password)
    else:
        form = UserCreationForm()

    return render(request, 'core/register.html', {'form': form})

@login_required
def logout(request):
    auth_logout(request)
    Controller.logout()
    return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)

@login_required
@relogin_lib
def projects_list(request):
    if request.method == "POST":
        username = request.POST.get('username')
        pid = request.POST.get('pid')
        action = request.POST.get('action')
        status = request.POST.get('status')
        show_project = request.POST.get('show')

        if show_project is not None:
            return HttpResponseRedirect(reverse('core:project_tasks', args=[show_project]))

        if (username is not None and len(username) != 0   
            and pid is not None):     
            users = UserController.fetch_user(login=username)
            if users is not None and len(users) != 0:
                user = users[0]
                if action == 'invite':
                    if status == 'admin':
                        ProjectController.invite_user_to_project(int(pid), user.uid, admin=True)
                    if status == 'guest':
                        ProjectController.invite_user_to_project(int(pid), user.uid, guest=True)
                if action == 'exclude':
                    ProjectController.exclude_user_from_project(int(pid), user.uid)

    projects = ProjectController.fetch_projects()
    visual_projects = [VisualProjectData.from_lib_project(project) for project in projects]
    VisualProjectData.normalize_visual_names(visual_projects)
    return render(request, 'core/projects_list.html', {'projects':visual_projects})

def _project_change_common(request, on_project_changed, initial_project=None):
    if request.method == "POST":
        form = ProjectForm(data=request.POST)
        if form.is_valid():
            name = form.cleaned_data.get('name')

            on_project_changed(name)

            return HttpResponseRedirect(reverse('core:projects_list'))
    else:
        form = ProjectForm()
        if initial_project is not None:
            form.fields['name'].initial = initial_project.name

    return render(request, 'core/add_project.html', {'form': form})

@login_required
@relogin_lib
def add_project(request):
    def on_project_created(name):
        ProjectController.save_project(name)

    return _project_change_common(request, on_project_created)

@login_required
@relogin_lib
def edit_project(request, project_id):
    def on_project_edited(name):
        ProjectController.edit_project(project_id, name)

    projects = ProjectController.fetch_projects(pid=project_id)
    if projects is None or len(projects) == 0:
        raise Http404

    return _project_change_common(request, on_project_edited, projects[0])

@login_required
@relogin_lib
def delete_project(request, project_id):
    projects = ProjectController.fetch_projects(pid=project_id)
    if projects is None or len(projects) == 0:
        raise Http404

    ProjectController.remove_project(project_id)
    return HttpResponseRedirect(reverse('core:projects_list'))

@login_required
@relogin_lib
def project_tasks(request, project_id):
    request.session['pid'] = project_id

    if request.method == "POST":
        up_status = request.POST.get('status_up')
        if up_status is not None:
            status, tid = tuple(up_status.split(','))
            status = Status.to_str(Status.raise_status(Status.from_str(status)))
            TaskController.edit_task(tid, status=status)
        down_status = request.POST.get('status_down')
        if down_status is not None:
            status, tid = tuple(down_status.split(','))
            status = Status.to_str(Status.downgrade_status(Status.from_str(status)))
            TaskController.edit_task(tid, status=status)
        back = request.POST.get('back')
        if back is not None:
            return HttpResponseRedirect(reverse('core:projects_list'))

    projects = ProjectController.fetch_projects(pid=project_id)
    back_text = None
    if projects is not None and len(projects) != 0:
        back_text = projects[0].name

    tasks = TaskController.fetch_tasks(pid=project_id)
    tasks = list(reversed(tasks))
    visual_tasks = [VisualTaskData.from_lib_task(task) for task in tasks]
    return render(request, 'core/projects_task_list.html', {'tasks':visual_tasks, 'back_text': back_text})

@login_required
@relogin_lib
def all_tasks(request):
    if request.method == "POST":
        up_status = request.POST.get('status_up')
        if up_status is not None:
            status, tid = tuple(up_status.split(','))
            status = Status.to_str(Status.raise_status(Status.from_str(status)))
            TaskController.edit_task(tid, status=status)
        down_status = request.POST.get('status_down')
        if down_status is not None:
            status, tid = tuple(down_status.split(','))
            status = Status.to_str(Status.downgrade_status(Status.from_str(status)))
            TaskController.edit_task(tid, status=status)

    tasks = TaskController.fetch_tasks()
    tasks = list(reversed(tasks))

    visual_tasks = [VisualTaskData.from_lib_task(task) for task in tasks]

    return render(request, 'core/all_tasks_list.html', {'tasks':visual_tasks})

def _task_change_common(request, on_task_changed, initial_task=None):
    def to_utc(datetime_object):
        if datetime_object is not None:
            return datetime_object.astimezone(pytz.utc).replace(tzinfo=None)

    projects = ProjectController.fetch_projects()
    visual_projects = [VisualProjectData.from_lib_project(project) for project in projects]
    VisualProjectData.normalize_visual_names(visual_projects)

    if request.method == "POST":
        form = TaskForm(data=request.POST)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            description = form.cleaned_data.get('description')
            priority = form.cleaned_data.get('priority')
            supposed_start = form.cleaned_data.get('supposed_start')
            supposed_end = form.cleaned_data.get('supposed_end')
            deadline = form.cleaned_data.get('deadline')
            project_pid = int(form.cleaned_data.get('project'))

            supposed_start = to_utc(supposed_start)
            supposed_end = to_utc(supposed_end)
            deadline = to_utc(deadline)

            supposed_start = utils.datetime_to_milliseconds(supposed_start)
            supposed_end = utils.datetime_to_milliseconds(supposed_end)
            deadline = utils.datetime_to_milliseconds(deadline)

            on_task_changed(title, description, priority, supposed_start, 
                supposed_end, deadline, project_pid)

            return HttpResponseRedirect(reverse('core:project_tasks', args=[project_pid]))
    else:
        form = TaskForm()
        if initial_task is not None:
            form.fields['title'].initial = initial_task.title
            form.fields['description'].initial = initial_task.description
            form.fields['priority'].initial = initial_task.priority

            supposed_start = VisualTaskData.timestamp_to_display(initial_task.supposed_start_time)
            supposed_end = VisualTaskData.timestamp_to_display(initial_task.supposed_end_time)
            deadline = VisualTaskData.timestamp_to_display(initial_task.deadline_time)
            
            form.fields['supposed_start'].initial = supposed_start
            form.fields['supposed_end'].initial = supposed_end
            form.fields['deadline'].initial = deadline

            form.fields['project'].initial = initial_task.project_id
        else:
            pid = request.session.get('pid')
            if pid is not None:
                form.fields['project'].initial = str(pid)
            else:
                for project in projects:
                    if project.name == Project.default_project_name:
                        form.fields['project'].initial = str(project.pid)
                        break
    
    return render(request, 'core/add_task.html', {'form': form, 'projects': visual_projects})

@login_required
@relogin_lib
def add_task(request, project_id=None):
    def on_task_created(title, description, priority, supposed_start,
                        supposed_end, deadline, project_pid):
        TaskController.save_task(pid=project_pid, title=title, description=description,
                                     priority=priority, supposed_start=supposed_start,
                                     supposed_end=supposed_end, deadline_time=deadline)

    return _task_change_common(request, on_task_created)

@login_required
@relogin_lib
def edit_task(request, task_id):
    tasks = TaskController.fetch_tasks(tid=task_id)
    if tasks is None or len(tasks) == 0:
        raise Http404
    initial_task = tasks[0]

    def on_task_edited(title, description, priority, supposed_start,
                        supposed_end, deadline, project_pid):
        TaskController.edit_task(task_id, pid=project_pid, title=title, description=description,
                                     priority=priority, supposed_start_time=supposed_start,
                                     supposed_end_time=supposed_end, deadline_time=deadline)

    return _task_change_common(request, on_task_edited, initial_task)

@login_required
@relogin_lib
def delete_task(request, task_id):
    tasks = TaskController.fetch_tasks(tid=task_id)
    if tasks is None or len(tasks) == 0:
        raise Http404

    TaskController.remove_task(task_id)

    pid = request.session.get('pid')
    if pid is not None:
        return HttpResponseRedirect(reverse('core:project_tasks', args=[pid]))
    else:
        return HttpResponseRedirect(reverse('core:projects_list'))

def temp(request):
    return render(request, 'core/temp.html')