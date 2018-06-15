from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader

def index(request):
    template = loader.get_template('core/index.html')
    return HttpResponse(template.render({}, request))