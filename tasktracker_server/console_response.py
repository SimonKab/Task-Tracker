def show_tasks_in_console(tasks):
    data = [[str(task.tid), task.title, task.description] for task in tasks]
    data.insert(0, ['TID', 'TITLE', "DESCRIPTION"])
    print_in_groups(data)

def show_task_id_present_error(task_id):
    print('Error. Task with id {0} already exists'.format(task_id))

def show_task_id_not_present_error(task_id):
    print('Error. There is not task with id {0}'.format(task_id))

def show_invalid_task_id_error(task_id):
    print('Error. Task id {0} is wrong'.format(task_id))

def print_in_grid(data):
    max_width = []
    count = len(data[0])
    for i in range(count):
        max = 0
        for d in data:
            if d[i] is None:
                d[i] = 'None'
            if len(d[i]) > max:
                max = len(d[i])
        max_width.append(max + 2)
    ri = 0
    for row in data:
        for i in range(count):
            if row[i] is None:
                row[i] = 'None'
            print(row[i].ljust(max_width[i]), '| ', end='')
        print('')
        if ri == 0: 
            print('')
        ri += 1

def print_in_groups(data):
    max = 0
    for h in data[0]:
        if len(h) > max:
            max = len(h)
    max += 2
    for d in data[1:]:
        for i in range(len(data[0])):
            print(data[0][i].ljust(max), '| ', d[i])
        print('')