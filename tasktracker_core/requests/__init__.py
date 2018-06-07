'''Front interface of library

Provide full functionality of library (see documentation of root package)

Whole functionality presented in one module controllers

First of all you should authenticate user, which id will be used to perform actions

is_authenticated = Controller.authentication(user_id_to_authenticate)
If id is not valid, AuthenticationError will be raised

If is_authenticated is True, all activities will be done on behalf of the user
Otherwise most operations will return NotAuthenticatedError. 
Only UserController will not raise the error cause it does not need user id
So, if you know only user name, you can freely use UserController 
to retrieve id of user

After authentication you can work with other controllers

For example, adding task:

success = TaskController.save_task(title='New task', description='This is new task', priority=Priority.HIGH, status=Status.ACTIVE)

Editing task:

success = TaskController.edit_task(task_id=1, title='Edited task', status=Status.COMPLETED)

Getting repeat numbers of a plan by time range:

time_range = () # time range im milliseconds. You can use utils module to convert
                # datetime to milliseconds
numbers = PlanController.get_repeats_by_time_range(plan_id=10, time_range)

To get tasks which are inside of time range including planned repeats:

time_range = () # time range im milliseconds
tasks = TaskController.fetch_tasks(time_range=time_range)

To get timeless tasks:

tasks = TaskController.fetch_tasks(timeless=True)

Combined:

tasks = TaskController.fetch_tasks(time_range=time_range, timeless=True)
'''