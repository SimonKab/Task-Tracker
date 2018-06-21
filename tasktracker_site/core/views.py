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

from .forms import TaskForm

from tasktracker_core.requests.controllers import (Controller, 
                                                   TaskController, 
                                                   ProjectController, 
                                                   UserController,
                                                   AuthenticationError)
from tasktracker_core import utils
from tasktracker_core.model.task import Status

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
def tasks(request):
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

    projects = ProjectController.fetch_projects()
    projects_titles = [project.name for project in projects]

    tasks = TaskController.fetch_tasks()
    tasks = list(reversed(tasks))

    visual_tasks = [VisualTaskData.from_lib_task(task) for task in tasks]


    return render(request, 'core/tasks.html', {'projects':projects_titles, 'tasks':visual_tasks})

def _task_change_common(request, on_task_changed, initial_task=None):
    def to_utc(datetime_object):
        if datetime_object is not None:
            return datetime_object.astimezone(pytz.utc).replace(tzinfo=None)

    if request.method == "POST":
        form = TaskForm(data=request.POST)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            description = form.cleaned_data.get('description')
            priority = form.cleaned_data.get('priority')
            supposed_start = form.cleaned_data.get('supposed_start')
            supposed_end = form.cleaned_data.get('supposed_end')
            deadline = form.cleaned_data.get('deadline')


            supposed_start = to_utc(supposed_start)
            supposed_end = to_utc(supposed_end)
            deadline = to_utc(deadline)

            supposed_start = utils.datetime_to_milliseconds(supposed_start)
            supposed_end = utils.datetime_to_milliseconds(supposed_end)
            deadline = utils.datetime_to_milliseconds(deadline)

            on_task_changed(title, description, priority, supposed_start, 
                supposed_end, deadline)

            return HttpResponseRedirect(reverse('core:tasks'))
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

    return render(request, 'core/add_task.html', {'form': form})

@login_required
@relogin_lib
def add_task(request):
    def on_task_created(title, description, priority, supposed_start,
                        supposed_end, deadline):
        TaskController.save_task(title=title, description=description,
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
                        supposed_end, deadline):
        TaskController.edit_task(task_id, title=title, description=description,
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

    return HttpResponseRedirect(reverse('core:tasks'))

def temp(request):
    return render(request, 'core/temp.html')