from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'),
    
    path('tasks/', views.tasks, name='tasks'),
    path('tasks/change', views.add_task, name='add_task'),
    path('tasks/change/<int:task_id>', views.edit_task, name='edit_task'),
    path('tasks/delete/<int:task_id>', views.delete_task, name='delete_task'),
    path('temp/', views.temp, name='temp'),
    # path('tasks/delete', views.deleted, name='deleted')
]