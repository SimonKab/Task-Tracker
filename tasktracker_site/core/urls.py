from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('tasks/', views.tasks, name='tasks'),
    path('logout/', views.logout, name='logout'),
]