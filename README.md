# TaskTracker: Calendar and TODO-list together written in Python

Provides functionality of TODO-list and calendar-like apps: it is a list of planned or single tasks, grouped in projects. User can work with timing by different ways: tasks with extended time range, planned tasks with excludes.

### Capabilities

1. Managing tasks, planned tasks, users and projects.
2. Task has title and description
3. Task may be with time range or without.
4. Task has start, end and deadline. In fact, end and deadline don't have special meaning for core and almost equal but have an important organizational meaning for user of library
5. Task has status and priority. Status reflects current relation with user:
pending, overdue, complete, active
6. User can establish parent-child relationships between tasks
7. Priority of child is the same as prioriy of parent
8. Parent-child task can not be planned
9. If parent has completed status, all their children have to be completed
If parent has overdue status, all their children have to be overdue
If parent has active status, none of the children can be pending
10. Planned task can have excludes and edited repeats. 
11. Planned tasks can have end of planning
12. User can set notification about start, end or deadline
13. Project is a group of tasks
14. Every person has it's own 'Default' project. If project was not specified, task will be added in 'Default'
15. Project can be public. To set project as public, owner need to invite a user as admin or guest
16. Owner of project is always admin of the project. Admin can invite guest or other admin
17. Admin can exclude everyone except owner of project
18. Owner of project can not be excluded, the only way to do this is to delete project
19. Guest can only read project
20. User is presented by name, password and email

### Structure

#### Library

Library is a core of TaskTracker. All activities about managing tasks, users and projects located inside of core.

You can use library to create your own task tracker, organizer, TODO-list, etc. Library provides base to create your own app by adding features over it.

See tasktracker_core package.

#### Console

You can use console part to try core in action. Console part lets you test features easily.

See tasktracker_console package.

### How to use - Library

First of all you should authenticate user, whose id will be used to perform actions
  			
	is_authenticated = Controller.authentication(user_id_to_authenticate)		

If id is not valid, AuthenticationError will be raised

If is_authenticated is True, all activities will be done on behalf of the user.
Otherwise most operations will return NotAuthenticatedError. 
Only UserController will not raise the error cause it does not need user id.
So, if you know only user name, you can freely use UserController 
to retrieve user's id.

After authentication has occured, you can work with other controllers.

For example, adding task:

	success = TaskController.save_task(title='New task', description='This is new task', priority=Priority.HIGH, status=Status.ACTIVE)

Editing task:

	success = TaskController.edit_task(task_id=1, title='Edited task', status=Status.COMPLETED)

Getting numbers of repeats of a plan by time range:

	time_range = () # time range in milliseconds. You can use utils module to convert datetime to milliseconds
	numbers = PlanController.get_repeats_by_time_range(plan_id=10, time_range)

Getting tasks which are inside of time range including plan repeats:

	time_range = () # time range im milliseconds
	tasks = TaskController.fetch_tasks(time_range=time_range)

Getting timeless tasks:

	tasks = TaskController.fetch_tasks(timeless=True)

Getting both with time range and timeless:

	tasks = TaskController.fetch_tasks(time_range=time_range, timeless=True)

### How to use - Console

There are four menus to use: task, plan, project, user. In each of them there are commands like: add, show, delete, edit and others.

At first use it is necessary to create first user.

Do it like this:

    $ tt user add --login <new-login>

After that you can login in the app:

    $ tt login <new-login>

Now you can work with the app. All actions will be performed on behalf of the new-login user

If you are not login, you will get message: 

    Error. User was not authenticated

Type next command to see most relevant tasks and notifications:

    $ tt task

Type next command to see all tasks of current user:

    $ tt task show

Type next command to see all tasks from now to 7 days forward:

    $ tt task show --start today now --end today+7 

To see all tasks in a project with id 10:

    $ tt project show --pid 10

To see existing projects and to check their ids:

    $ tt project

### How to install

Installation proccess is the same for both library and console

Run script eaither setup_core.py to install core or setup_console.py to install console like this:

    $ python setup_core.py install
    $ python setup_console.py install

After installing core you can import tasktracker_core like regular python module

    import tasktracker_core

Command to start console app is 'tt'. So after installing console you can run app like this:

    $ tt

There is also start.py script. If you dont want to reinstall the app after code has been changed, you can just run start.py script like this:

    $ python start.py

