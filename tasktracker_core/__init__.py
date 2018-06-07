'''Core of tasktracker app

Provide core functions of tasktracker app:
Managing tasks, planned tasks, users and projects.
Task has title and description
Task may be with time range or without.
Time range of task is start, end and deadline. In fact, end and deadline have
not special meaning for core and almost equal 
but have an important organizational meaning for user of library
Task has status and priority. Status reflects current relation with user:
pending, overdue, complete, active
User can establish parent-child relationships between tasks
Priority of child will be same as prioriy of parent
Parent-child task can not be planned
If parent has completed status, all their children have to be completed
If parent has overdue status, all their children have to be overdue
If parent has active status, none of the children can not be pending
Planned task can have excludes and edited repeats. 
Planned tasks can have end of planning
User can set notification about start, end or deadline
Project is group of tasks.
Every person has it's own Default project. This project contains tasks
for which project was not specified. 
Project can be public. For this user can invite other user. 
Participiants of project can be either guest or admin.
Owner of project is always admin of project. Admin can invite guest or admin
Admin can exclude overyone except owner of project. 
Owner of project can not be excluded, the only way to do it is to delete project
Guest can only read project
User is name, password and email

requests package provide front interface of library. 
You should use this package to work with library
To find out how to use library, check docs of requests package

model package defines models of library: task, plan, user, project
storage package manages storing data in database

logging module allow you to manage logging of whole library
utils provide simple and routine functionality like converting data, 
fetching home folder path and etc.
'''