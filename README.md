# Calendar and TODO-list together

Provides functionality of TODO-list and calendar-like apps: it is list of planned or single tasks, grouped in projects. User can work with timing by different ways: tasks with extended time range, planned tasks with excludes.

### Capabilities

1. Managing tasks, planned tasks, users and projects.
2. Task has title and description
3. Task may be with time range or without.
4. Time range of task is start, end and deadline. In fact, end and deadline don't have special meaning for core and almost equal but have an important organizational meaning for user of library
5. Task has status and priority. Status reflects current relation with user:
pending, overdue, complete, active
6) User can establish parent-child relationships between tasks
7. Priority of child will be same as prioriy of parent
8. Parent-child task can not be planned
9. If parent has completed status, all their children have to be completed
If parent has overdue status, all their children have to be overdue
If parent has active status, none of the children can not be pending
10. Planned task can have excludes and edited repeats. 
11. Planned tasks can have end of planning
12. User can set notification about start, end or deadline
13. Project is group of tasks.
14. Every person has it's own Default project. This project contains tasks for which project was not specified. 
15. Project can be public. For this user can invite other user. 
16. Participiants of project can be either guest or admin.
17. Owner of project is always admin of project. Admin can invite guest or admin
18. Admin can exclude overyone except owner of project. 
19. Owner of project can not be excluded, the only way to do it is to delete project
20. Guest can only read project
21. User is name, password and email

### How to use

First of all you should authenticate user, which id will be used to perform actions

'''#python
is_authenticated = Controller.authentication(user_id_to_authenticate)'''

If id is not valid, AuthenticationError will be raised

If is_authenticated is True, all activities will be done on behalf of the user
Otherwise most operations will return NotAuthenticatedError. 
Only UserController will not raise the error cause it does not need user id
So, if you know only user name, you can freely use UserController 
to retrieve id of user

After authentication you can work with other controllers

For example, adding task:

'''#python
success = TaskController.save_task(title='New task', description='This is new task', priority=Priority.HIGH, status=Status.ACTIVE)'''

Editing task:

'''#python
success = TaskController.edit_task(task_id=1, title='Edited task', status=Status.COMPLETED)'''

Getting repeat numbers of a plan by time range:

'''#python
time_range = () # time range im milliseconds. You can use utils module to convert datetime to milliseconds
numbers = PlanController.get_repeats_by_time_range(plan_id=10, time_range)'''

To get tasks which are inside of time range including planned repeats:

'''#python
time_range = () # time range im milliseconds
tasks = TaskController.fetch_tasks(time_range=time_range)''

To get timeless tasks:

'''#python
tasks = TaskController.fetch_tasks(timeless=True)'''

Combined:

'''#python
tasks = TaskController.fetch_tasks(time_range=time_range, timeless=True)'''