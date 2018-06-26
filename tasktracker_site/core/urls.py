from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    
    path('projects/', views.projects_list, name='projects_list'),
    path('projects/<int:project_id>/tasks', views.project_tasks, name='project_tasks'),
    path('projects/change', views.add_project, name='add_project'),
    path('projects/change/<int:project_id>', views.edit_project, name='edit_project'),
    path('projects/delete/<int:project_id>', views.delete_project, name='delete_project'),
    
    path('tasks/', views.all_tasks, name='all_tasks'),
    path('tasks/change', views.add_task, name='add_task'),
    path('tasks/change/<int:task_id>', views.edit_task, name='edit_task'),
    path('tasks/delete/<int:task_id>', views.delete_task, name='delete_task'),
    path('temp/', views.temp, name='temp'),
    # path('tasks/delete', views.deleted, name='deleted')
]