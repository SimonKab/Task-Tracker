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

def log_in_user(request, username, password):
    try:
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(settings.LOGIN_REDIRECT_URL)
    except Exception:
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
    if len(form.errors) > 0:
        common_error = form.errors.get('__all__')
    return render(request, 'core/index.html', {'form': form, 'common_error': common_error})

def register(request):

    if request.method == "POST":
        form = UserCreationForm(data=request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            return log_in_user(request, username, raw_password)
    else:
        form = UserCreationForm()

    return render(request, 'core/register.html', {'form': form})

@login_required
def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)

@login_required
def tasks(request):
    projects = ['First', 'Second', 'Third']
    return render(request, 'core/tasks.html', {'projects':projects})