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

from django.contrib import messages

import datetime
import pytz

from .forms import TaskForm, ProjectForm, TaskSearchForm

from . import utils

from tasktracker_core.requests.controllers import (Controller, 
                                                   TaskController, 
                                                   ProjectController, 
                                                   UserController,
                                                   PlanController,
                                                   AuthenticationError)
from tasktracker_core import utils as lib_utils
from tasktracker_core.model.task import Priority, Status
from tasktracker_core.model.project import Project
from tasktracker_core.model.plan import Plan

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

        self.parent = None
        self.childs = None

        self.plan = None
        self.common = None
        self.edit = None
        self.repeat = None

        self.depth = None

        self.controller = None

    @staticmethod
    def timestamp_to_display(timestamp):
        if timestamp is not None:
            unaware = datetime.datetime.utcfromtimestamp(timestamp / 1000.0)
            # unaware_utc = unaware.replace(tzinfo=pytz.utc)
            # aware = unaware_utc.astimezone(pytz.timezone(settings.TIME_ZONE))
            return unaware.strftime('%d.%m.%Y %H:%M')

    @classmethod
    def from_lib_task(cls, controller, lib_task, depth=None):
        visual_task = VisualTaskData()
        visual_task.controller = controller

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

        if lib_task.parent_tid is not None:
            parent_tasks = TaskController(controller).fetch_tasks(tid=lib_task.parent_tid)
            if parent_tasks is not None and len(parent_tasks) != 0:
                visual_task.parent = parent_tasks[0]

        child_tasks = TaskController(controller).fetch_tasks(parent_tid=lib_task.tid)
        if child_tasks is not None and len(child_tasks) != 0:
            visual_task.childs = child_tasks

        if depth is not None:
            visual_task.depth = depth

        plans = PlanController(controller).get_plan_for_common_task(lib_task.tid)
        if plans is not None and len(plans) != 0:
            visual_task.plan = VisualPlanData.from_lib_plan(controller, plans[0])
            visual_task.common = True
        edit_plans = PlanController(controller).get_plan_for_edit_repeat_task(lib_task.tid)
        if edit_plans is not None and len(edit_plans) != 0:
            visual_task.plan = VisualPlanData.from_lib_plan(controller, edit_plans[0])
            visual_task.edit = True

        plans = plans if plans is not None and len(plans) != 0 else edit_plans
        if plans is not None and len(plans) != 0:
            repeat = PlanController(controller).get_repeat_number_for_task(plans[0].plan_id, lib_task)
            visual_task.repeat = repeat

        return visual_task

    def get_project_name(self):
        projects = ProjectController(self.controller).fetch_projects(pid=self.pid)
        if projects is not None and len(projects) != 0:
            return projects[0].name

class VisualPlanData():

    def __init__(self):
        self.plan_id = None
        self.shift = None
        self.end = None
        self.excludes = None

        self.controller = None

    @staticmethod
    def parse_shift(shift):
        years = shift // (365*30*24*60*60000)
        shift -= years * 365*30*24*60*60000
        months = shift // (30*24*60*60000)
        shift -= months * 30*24*60*60000
        days = shift // (24*60*60000)
        shift -= days * 24*60*60000
        hours = shift // (60*60000)
        shift -= hours * 60*60000
        minutes = shift // (60000)
        shift -= minutes * 60000
        return years, months, days, hours, minutes

    @staticmethod
    def shift_to_display(shift):
        if shift is None:
            return None

        years, months, days, hours, minutes = VisualPlanData.parse_shift(shift)        
        
        string_representation = ''
        if minutes != 0:
            string_representation = 'minutes {}'.format(minutes)
        if hours != 0:
            string_representation = 'hours {} '.format(hours) + string_representation
        if days != 0:
            string_representation = 'days {} '.format(days) + string_representation
        if months != 0:
            string_representation = 'months {} '.format(months) + string_representation
        if years != 0:
            string_representation = 'years {} '.format(years) + string_representation

        return string_representation

    @classmethod
    def from_lib_plan(cls, controller, lib_plan):
        visual_plan = VisualPlanData()
        visual_plan.controller = controller

        visual_plan.plan_id = lib_plan.plan_id
        visual_plan.shift = lib_plan.shift
        visual_plan.end = lib_plan.end

        if lib_plan.exclude is not None and len(lib_plan.exclude) != 0:
            visual_plan.excludes = []
            for exclude in lib_plan.exclude:
                exclude_obj = cls.Exclude()
                exclude_obj.repeat = exclude
                exclude_obj.kind = PlanController(controller).get_exclude_type(lib_plan.plan_id, exclude)
                if exclude_obj.kind == Plan.PlanExcludeKind.EDITED:
                    exclude_obj.tid = PlanController(controller).get_tid_for_edit_repeat(lib_plan.plan_id, exclude)
                    if exclude_obj.tid is not None:
                        exclude_obj.tid = exclude_obj.tid.tid
                time_range = PlanController(controller).get_time_for_repeat(lib_plan.plan_id, exclude)
                if len(time_range) == 2:
                    exclude_obj.time = (VisualTaskData.timestamp_to_display(time_range[0]), VisualTaskData.timestamp_to_display(time_range[1]))
                else:
                    exclude_obj.time = (VisualTaskData.timestamp_to_display(time_range[0]), )
                visual_plan.excludes.append(exclude_obj)

        if visual_plan.shift is not None:
            visual_plan.shift = cls.shift_to_display(visual_plan.shift)

        return visual_plan

    class Exclude():

        def __init__(self):
            self.repeat = None
            self.kind = None
            self.tid = None
            self.time = None

class VisualProjectData():

    def __init__(self):
        self.pid = None
        self.creator = None
        self.name = None
        self.admins = None
        self.guests = None

        self.controller = None

    @classmethod
    def from_lib_project(cls, controller, lib_project):
        visual_project = VisualProjectData()
        visual_project.controller = controller

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
                user = UserController(self.controller).fetch_user(uid=user_id)
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
    def normalize_visual_names(visual_names, controller):
        def add_login_to_project_name(project):
            users = UserController(controller).fetch_user(project.creator)
            if users is not None and len(users) != 0:
                project.name += " ({})".format(users[0].login)

        for head in range(len(visual_names)):
            for rest in range(head + 1, len(visual_names)):
                first = visual_names[head]
                second = visual_names[rest]
                if first.name == second.name:
                    add_login_to_project_name(first)
                    add_login_to_project_name(second)

def require_lib(method):
    def check(request, *args, **kwargs):
        controller = Controller()
        controller.authentication_by_login(request.user.username)
        result = method(controller, request, *args, **kwargs)
        controller.logout()
        return result
    return check

def log_in_user(request, username, password):
    try:
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
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
            UserController().save_user(login=username)

            raw_password = form.cleaned_data.get('password1')
            return log_in_user(request, username, raw_password)
    else:
        form = UserCreationForm()

    return render(request, 'core/register.html', {'form': form})

@login_required
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)

def filter(tasks, condition):
    res_tasks = []
    for task in tasks:
        if condition(task):
            res_tasks.append(task)
    return res_tasks

def sort_time(tasks):
    timeless = filter(tasks, lambda t: len(t.get_time_range()) == 0)
    not_timeless = filter(tasks, lambda t: len(t.get_time_range()) != 0)
    return not_timeless + timeless

def filter_priority(tasks):
    highest = filter(tasks, lambda t: t.priority == Priority.HIGHEST)
    highest = sort_time(highest)
    high = filter(tasks, lambda t: t.priority == Priority.HIGH)
    high = sort_time(high)
    normal = filter(tasks, lambda t: t.priority == Priority.NORMAL)
    normal = sort_time(normal)
    low = filter(tasks, lambda t: t.priority == Priority.LOW)
    low = sort_time(low)
    return highest + high + normal + low

def filter_status(tasks):
    overdue = filter(tasks, lambda t: t.status == Status.OVERDUE)
    print(overdue)
    overdue = filter_priority(overdue)
    active = filter(tasks, lambda t: t.status == Status.ACTIVE)
    active = filter_priority(active)
    pending = filter(tasks, lambda t: t.status == Status.PENDING)
    pending = filter_priority(pending)
    completed = filter(tasks, lambda t: t.status == Status.COMPLETED)
    completed = filter_priority(completed)
    return overdue + active + pending + completed

@login_required
@require_lib
def home(controller, request):
    if request.session.get('parent_task') is not None:
            request.session.pop('parent_task')

    now = lib_utils.datetime_to_milliseconds(lib_utils.now())

    TaskController(controller).find_overdue_tasks(now)

    if request.method == "POST":
        up_status = request.POST.get('status_up')
        if up_status is not None:
            status, tid = tuple(up_status.split(','))
            status = Status.to_str(Status.raise_status(Status.from_str(status)))
            parts = tid.split('_')
            repeat = None
            plan_id = None
            if len(parts) == 1:
                tid = int(tid)
            if len(parts) == 3:
                tid = int(parts[0])
                plan_id = int(parts[1])
                repeat = int(parts[2])
            if repeat is None:
                TaskController(controller).edit_task(tid, status=status)
            else:
                PlanController(controller).edit_repeat_by_number(plan_id, repeat, status=status)
        down_status = request.POST.get('status_down')
        if down_status is not None:
            status, tid = tuple(down_status.split(','))
            status = Status.to_str(Status.downgrade_status(Status.from_str(status)))
            parts = tid.split('_')
            repeat = None
            plan_id = None
            if len(parts) == 1:
                tid = int(tid)
            if len(parts) == 3:
                tid = int(parts[0])
                plan_id = int(parts[1])
                repeat = int(parts[2])
            if repeat is None:
                TaskController(controller).edit_task(tid, status=status)
            else:
                PlanController(controller).edit_repeat_by_number(plan_id, repeat, status=status)
        add_subtask = request.POST.get('add_subtask')
        if add_subtask is not None:
            request.session['parent_task'] = add_subtask
            return HttpResponseRedirect(reverse('core:add_task'))

    time_range = (lib_utils.datetime_to_milliseconds(lib_utils.today()), 
                  lib_utils.shift_datetime_in_millis(lib_utils.today(), datetime.timedelta(days=1)))
    tasks = []
    tasks += TaskController(controller).get_overdue_tasks(now)
    tasks += TaskController(controller).fetch_tasks(time_range=time_range)
    tasks += TaskController(controller).fetch_tasks(timeless=True)
    for i, task in enumerate(tasks):
        for j in range(len(tasks)-1, i, -1) :
            if task.tid == tasks[j].tid and task.status == Status.OVERDUE:
                del tasks[j]

    tasks = filter_status(tasks)

    visual_tasks = [VisualTaskData.from_lib_task(controller, task) for task in tasks]

    return render(request, 'core/home.html', {'tasks': visual_tasks})

@login_required
@require_lib
def projects_list(controller, request):
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
            users = UserController(controller).fetch_user(login=username)
            if users is not None and len(users) != 0:
                user = users[0]
                if action == 'invite':
                    if status == 'admin':
                        ProjectController(controller).invite_user_to_project(int(pid), user.uid, admin=True)
                    if status == 'guest':
                        ProjectController(controller).invite_user_to_project(int(pid), user.uid, guest=True)
                if action == 'exclude':
                    ProjectController(controller).exclude_user_from_project(int(pid), user.uid)

    projects = ProjectController(controller).fetch_projects()
    visual_projects = [VisualProjectData.from_lib_project(controller, project) for project in projects]
    VisualProjectData.normalize_visual_names(visual_projects, controller)
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
@require_lib
def add_project(controller, request):
    def on_project_created(name):
        ProjectController(controller).save_project(name)

    return _project_change_common(request, on_project_created)

@login_required
@require_lib
def edit_project(controller, request, project_id):
    def on_project_edited(name):
        ProjectController(controller).edit_project(project_id, name)

    projects = ProjectController(controller).fetch_projects(pid=project_id)
    if projects is None or len(projects) == 0:
        raise Http404

    return _project_change_common(request, on_project_edited, projects[0])

@login_required
@require_lib
def delete_project(controller, request, project_id):
    projects = ProjectController(controller).fetch_projects(pid=project_id)
    if projects is None or len(projects) == 0:
        raise Http404

    project = projects[0]
    if project.name == 'Default':
        return HttpResponseRedirect(reverse('core:projects_list'))

    ProjectController(controller).remove_project(project_id)
    return HttpResponseRedirect(reverse('core:projects_list'))

@login_required
@require_lib
def project_tasks(controller, request, project_id):
    request.session['pid'] = project_id
    
    if request.session.get('parent_task') is not None:
        request.session.pop('parent_task')

    if request.method == "POST":
        up_status = request.POST.get('status_up')
        if up_status is not None:
            status, tid = tuple(up_status.split(','))
            status = Status.to_str(Status.raise_status(Status.from_str(status)))
            TaskController(controller).edit_task(tid, status=status)
        down_status = request.POST.get('status_down')
        if down_status is not None:
            status, tid = tuple(down_status.split(','))
            status = Status.to_str(Status.downgrade_status(Status.from_str(status)))
            TaskController(controller).edit_task(tid, status=status)
        back = request.POST.get('back')
        if back is not None:
            return HttpResponseRedirect(reverse('core:projects_list'))
        add_subtask = request.POST.get('add_subtask')
        if add_subtask is not None:
            request.session['parent_task'] = add_subtask
            return HttpResponseRedirect(reverse('core:add_task'))

    projects = ProjectController(controller).fetch_projects(pid=project_id)
    back_text = None
    if projects is not None and len(projects) != 0:
        back_text = projects[0].name

    tasks = TaskController(controller).fetch_tasks(pid=project_id)
    tasks = list(reversed(tasks))
    visual_tasks = [VisualTaskData.from_lib_task(controller, task) for task in tasks]
    return render(request, 'core/projects_task_list.html', {'tasks':visual_tasks, 'back_text': back_text})

@login_required
@require_lib
def search(controller, request):
    def to_utc(datetime_object):
        if datetime_object is not None:
            return datetime_object.replace(tzinfo=None)

    if request.session.get('parent_task') is not None:
        request.session.pop('parent_task')

    projects = ProjectController(controller).fetch_projects()
    visual_projects = [VisualProjectData.from_lib_project(controller, project) for project in projects]
    VisualProjectData.normalize_visual_names(visual_projects, controller)

    if request.method == "POST":
        up_status = request.POST.get('status_up')
        if up_status is not None:
            status, tid = tuple(up_status.split(','))
            status = Status.to_str(Status.raise_status(Status.from_str(status)))
            parts = tid.split('_')
            repeat = None
            plan_id = None
            if len(parts) == 1:
                tid = int(tid)
            if len(parts) == 3:
                tid = int(parts[0])
                plan_id = int(parts[1])
                repeat = int(parts[2])
            if repeat is None:
                TaskController(controller).edit_task(tid, status=status)
            else:
                PlanController(controller).edit_repeat_by_number(plan_id, repeat, status=status)
        down_status = request.POST.get('status_down')
        if down_status is not None:
            status, tid = tuple(down_status.split(','))
            status = Status.to_str(Status.downgrade_status(Status.from_str(status)))
            parts = tid.split('_')
            repeat = None
            plan_id = None
            if len(parts) == 1:
                tid = int(tid)
            if len(parts) == 3:
                tid = int(parts[0])
                plan_id = int(parts[1])
                repeat = int(parts[2])
            if repeat is None:
                TaskController(controller).edit_task(tid, status=status)
            else:
                PlanController(controller).edit_repeat_by_number(plan_id, repeat, status=status)
        add_subtask = request.POST.get('add_subtask')
        if add_subtask is not None:
            request.session['parent_task'] = add_subtask
            return HttpResponseRedirect(reverse('core:add_task'))
        
        form = TaskSearchForm(data=request.POST)
        if form.is_valid():
            title = form.cleaned_data.get('title')
            if len(title) == 0:
                title = None
            
            description = form.cleaned_data.get('description')
            if len(description) == 0:
                description = None
            
            priority_list = form.cleaned_data.get('priority')
            if len(priority_list) == 0:
                priority_list = None
            else:
                priority_list = [Priority.from_str(priority) for priority in priority_list]
            
            status_list = form.cleaned_data.get('status')
            if len(status_list) == 0:
                status_list = None
            else:
                status_list = [Status.from_str(status) for status in status_list]

            supposed_start = form.cleaned_data.get('supposed_start')
            supposed_end = form.cleaned_data.get('supposed_end')
            deadline = form.cleaned_data.get('deadline')

            project_pid = request.POST.getlist('project')
            form.projects = project_pid                

            supposed_start = to_utc(supposed_start)
            supposed_end = to_utc(supposed_end)
            deadline = to_utc(deadline)

            supposed_start = lib_utils.datetime_to_milliseconds(supposed_start)
            supposed_end = lib_utils.datetime_to_milliseconds(supposed_end)
            deadline = lib_utils.datetime_to_milliseconds(deadline)

            time_range = utils.get_time_range(supposed_start, supposed_end, deadline)

            print('TEST', time_range)

            timeless = form.cleaned_data.get('timeless')
            if timeless == 'true':
                timeless = True
            else:
                timeless = None

            if project_pid is None or len(project_pid) == 0:
            
                tasks = TaskController(controller).fetch_tasks(title=title, description=description,
                                               priority=priority_list, status=status_list,
                                               time_range=time_range, timeless=timeless)
            else:
                project_pid = [int(p) for p in project_pid]
                tasks = []
                for p in project_pid:
                    tasks += TaskController(controller).fetch_tasks(pid=p, title=title, description=description,
                                               priority=priority_list, status=status_list,
                                               time_range=time_range, timeless=timeless)   
        else:
            tasks = TaskController(controller).fetch_tasks()   
    else:
        form = TaskSearchForm()
        tasks = TaskController(controller).fetch_tasks()

    tasks = list(reversed(tasks))
    visual_tasks = [VisualTaskData.from_lib_task(controller, task) for task in tasks]
    
    return render(request, 'core/search.html', {'form':form, 'tasks':visual_tasks, 'projects': visual_projects})

def _task_change_common(controller, request, on_task_changed, plan_id=None, repeat=None, initial_task=None):
    def to_utc(datetime_object):
        if datetime_object is not None:
            return datetime_object.replace(tzinfo=None)

    def timestamp_to_display(timestamp):
        if timestamp is not None:
            return datetime.datetime.utcfromtimestamp(timestamp / 1000.0).strftime('%d-%m-%Y %H:%M')

    projects = ProjectController(controller).fetch_projects()
    visual_projects = [VisualProjectData.from_lib_project(controller, project) for project in projects]
    VisualProjectData.normalize_visual_names(visual_projects, controller)

    if request.method == "POST":
        form = TaskForm(data=request.POST)

        cancel_parent = request.POST.get('cancel_parent')
        if cancel_parent is not None:
            request.session.pop('parent_task')
        elif form.is_valid():
            title = form.cleaned_data.get('title')
            description = form.cleaned_data.get('description')
            priority = form.cleaned_data.get('priority')
            supposed_start = form.cleaned_data.get('supposed_start')
            supposed_end = form.cleaned_data.get('supposed_end')
            deadline = form.cleaned_data.get('deadline')
            project_pid = int(form.cleaned_data.get('project'))

            shift_milliseconds = 0
            plan_minute = form.cleaned_data.get('plan_minute')
            if plan_minute is not None:
                plan_minute = int(plan_minute)
                shift_milliseconds += plan_minute*60000
            plan_hour = form.cleaned_data.get('plan_hour')
            if plan_hour is not None:
                plan_hour = int(plan_hour)
                shift_milliseconds += plan_hour*60*60000
            plan_day = form.cleaned_data.get('plan_day')
            if plan_day is not None:
                plan_day = int(plan_day)
                shift_milliseconds += plan_day*24*60*60000
            plan_month = form.cleaned_data.get('plan_month')
            if plan_month is not None:
                plan_month = int(plan_month)
                shift_milliseconds += plan_month*30*24*60*60000
            plan_year = form.cleaned_data.get('plan_year')
            if plan_year is not None:
                plan_year = int(plan_year)
                shift_milliseconds += plan_year*365*30*24*60*60000

            print('t', supposed_end)

            supposed_start = to_utc(supposed_start)
            supposed_end = to_utc(supposed_end)
            deadline = to_utc(deadline)

            print('t', supposed_end)

            supposed_start = lib_utils.datetime_to_milliseconds(supposed_start)
            supposed_end = lib_utils.datetime_to_milliseconds(supposed_end)
            deadline = lib_utils.datetime_to_milliseconds(deadline)

            print('t', timestamp_to_display(supposed_end))

            on_task_changed(title, description, priority, supposed_start, 
                supposed_end, deadline, project_pid, shift_milliseconds)

            return HttpResponseRedirect(reverse('core:project_tasks', args=[project_pid]))
    else:
        form = TaskForm()
        if initial_task is not None:
            form.fields['title'].initial = initial_task.title
            form.fields['description'].initial = initial_task.description
            form.fields['priority'].initial = Priority.to_str(initial_task.priority)

            supposed_start = VisualTaskData.timestamp_to_display(initial_task.supposed_start_time)
            supposed_end = VisualTaskData.timestamp_to_display(initial_task.supposed_end_time)
            deadline = VisualTaskData.timestamp_to_display(initial_task.deadline_time)
            
            form.fields['supposed_start'].initial = supposed_start
            form.fields['supposed_end'].initial = supposed_end
            form.fields['deadline'].initial = deadline

            form.fields['project'].initial = str(initial_task.pid)

            plans = PlanController(controller).get_plan_for_common_task(initial_task.tid)
            if plans is not None and len(plans) != 0:
                years, months, days, hours, minutes = VisualPlanData.parse_shift(plans[0].shift)
                if minutes != 0:
                    form.fields['plan_minute'].initial = minutes
                if hours != 0:
                    form.fields['plan_hour'].initial = hours
                if days != 0:
                    form.fields['plan_day'].initial = days
                if months != 0:
                    form.fields['plan_month'].initial = months
                if years != 0:
                    form.fields['plan_year'].initial = years
        else:
            pid = request.session.get('pid')
            if pid is not None:
                form.fields['project'].initial = str(pid)
            else:
                for project in projects:
                    if project.name == Project.default_project_name:
                        form.fields['project'].initial = str(project.pid)
                        break
    
    parent_task = None
    if initial_task is None:
        parent_tid = request.session.get('parent_task')
        if parent_tid is not None:
            lib_task = TaskController(controller).fetch_tasks(tid=parent_tid)
            if lib_task is not None and len(lib_task) != 0:
                parent_task = VisualTaskData.from_lib_task(controller, lib_task[0])
    else:
        if request.session.get('parent_task') is not None:
            request.session.pop('parent_task')

    return render(request, 'core/add_task.html', {'form': form, 'projects': visual_projects, 
                                                'parent_task': parent_task, 'repeat': repeat})

@login_required
@require_lib
def add_task(controller, request, project_id=None):
    def on_task_created(title, description, priority, supposed_start,
                        supposed_end, deadline, project_pid, shift_milliseconds):
        parent_task = request.session.get('parent_task')
        TaskController(controller).save_task(pid=project_pid, parent_tid=parent_task, title=title, 
                                    description=description,
                                     priority=priority, supposed_start=supposed_start,
                                     supposed_end=supposed_end, deadline_time=deadline)

        if shift_milliseconds is not None and shift_milliseconds != 0:
            tid = TaskController(controller).get_last_saved_task_tid()
            PlanController(controller).attach_plan(tid, shift_milliseconds)

    return _task_change_common(controller, request, on_task_created)

@login_required
@require_lib
def edit_task(controller, request, task_id):
    parts = task_id.split('_')
    repeat = None
    plan_id = None
    if len(parts) == 1:
        task_id = int(task_id)
    if len(parts) == 3:
        task_id = int(parts[0])
        plan_id = int(parts[1])
        repeat = int(parts[2])

    tasks = TaskController(controller).fetch_tasks(tid=task_id)
    if tasks is None or len(tasks) == 0:
        raise Http404
    initial_task = tasks[0]

    def on_task_edited(title, description, priority, supposed_start,
                        supposed_end, deadline, project_pid, shift_milliseconds):
        if plan_id is None:
            if initial_task.status == Status.OVERDUE:
                TaskController(controller).edit_task(task_id, pid=project_pid, title=title, description=description,
                                     priority=priority, supposed_start_time=supposed_start,
                                     supposed_end_time=supposed_end, deadline_time=deadline, status=Status.PENDING)
            else:
                TaskController(controller).edit_task(task_id, pid=project_pid, title=title, description=description,
                                     priority=priority, supposed_start_time=supposed_start,
                                     supposed_end_time=supposed_end, deadline_time=deadline)

            if shift_milliseconds is not None and shift_milliseconds != 0:
                plans = PlanController(controller).get_plan_for_common_task(task_id)
                if plans is None or len(plans) == 0:
                    tid = TaskController(controller).get_last_saved_task_tid()
                    PlanController(controller).attach_plan(tid, shift_milliseconds)
                else:
                    plan = plans[0]
                    PlanController(controller).edit_plan(plan.plan_id, shift=shift_milliseconds)
        else:
            if Priority.to_str(initial_task.priority) != priority:
                PlanController(controller).edit_repeat_by_number(plan_id, repeat, priority=priority)

    return _task_change_common(controller, request, on_task_edited, plan_id, repeat, initial_task)

@login_required
@require_lib
def delete_task(controller, request, task_id):
    parts = task_id.split('_')
    if len(parts) == 1:

        task_id = int(task_id)
        tasks = TaskController(controller).fetch_tasks(tid=task_id)
        if tasks is None or len(tasks) == 0:
            raise Http404

        TaskController(controller).remove_task(task_id)

        pid = request.session.get('pid')
        if pid is not None:
            return HttpResponseRedirect(reverse('core:project_tasks', args=[pid]))
        else:
            return HttpResponseRedirect(reverse('core:projects_list'))
    if len(parts) == 3:
        parts = task_id.split('_')
        repeat = None
        plan_id = None
        if len(parts) == 1:
            tid = int(tid)
        if len(parts) == 3:
            tid = int(parts[0])
            plan_id = int(parts[1])
            repeat = int(parts[2])

        task_id = int(parts[0])
        tasks = TaskController(controller).fetch_tasks(tid=task_id)
        if tasks is None or len(tasks) == 0:
            raise Http404

        repeat = int(parts[1])

        plans = PlanController(controller).get_plan_for_common_task(task_id)
        if plans is None or len(plans) == 0:
            raise Http404

        PlanController(controller).delete_repeats_from_plan_by_number(plan_id, repeat)

        pid = request.session.get('pid')
        if pid is not None:
            return HttpResponseRedirect(reverse('core:project_tasks', args=[pid]))
        else:
            return HttpResponseRedirect(reverse('core:projects_list'))

def build_task_tree(controller, root, tree, depth=0):
    lib_tasks = TaskController(controller).fetch_tasks(parent_tid=root.tid)
    for task in lib_tasks:
        tree.append(VisualTaskData.from_lib_task(controller, task, 30*depth))
        build_task_tree(controller, task, tree, depth+1)

@login_required
@require_lib
def show_task(controller, request, task_id):
    if request.session.get('parent_task') is not None:
        request.session.pop('parent_task')

    tasks = TaskController(controller).fetch_tasks(tid=task_id)
    if tasks is None or len(tasks) == 0:
        raise Http404

    main_task = VisualTaskData.from_lib_task(controller, tasks[0])

    if request.method == "POST":
        up_status = request.POST.get('status_up')
        if up_status is not None:
            status, tid = tuple(up_status.split(','))
            status = Status.to_str(Status.raise_status(Status.from_str(status)))
            TaskController(controller).edit_task(tid, status=status)
        down_status = request.POST.get('status_down')
        if down_status is not None:
            status, tid = tuple(down_status.split(','))
            status = Status.to_str(Status.downgrade_status(Status.from_str(status)))
            TaskController(controller).edit_task(tid, status=status)
        add_subtask = request.POST.get('add_subtask')
        if add_subtask is not None:
            request.session['parent_task'] = add_subtask
            return HttpResponseRedirect(reverse('core:add_task'))
        restore = request.POST.get('restore')
        if restore is not None:
            success = PlanController(controller).restore_repeat(main_task.plan.plan_id, int(restore))
            main_task = VisualTaskData.from_lib_task(controller, tasks[0])

    child_tasks = []
    build_task_tree(controller, main_task, child_tasks)
    
    return render(request, 'core/show_task.html', {'main_task': main_task, 'child_tasks': child_tasks})    

def temp(request):
    return render(request, 'core/temp.html')