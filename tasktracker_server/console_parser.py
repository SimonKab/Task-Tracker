from .requests.controllers import TaskController

def parse(query):
    if query[0] == 'add':
        add_query(query)
    elif query[0] == 'get':
        tasks = TaskController.get_all_tasks()
        for task in tasks:
            print("Task: ", task.title)

def add_query(query):
    if (len(query) != 2):
        print("Error parsing")
        return False
    title = query[1]
    success = TaskController.save_task(3, title, "Some description")
    return success