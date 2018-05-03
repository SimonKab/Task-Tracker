class Response:

    def __init__(self):
        self.response_code = 0
        self.responce_message = ""

class TaskResponse(Response):

    def __init__(self):
        self.tasks = None

def push_ok_task_response(tasks):
    task_response = TaskResponse()
    console_response.show_tasks_in_console(tasks)