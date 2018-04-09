from .requests.controllers import TaskController
import argparse

remove_action_list_name = 'remove'

def parse():
    parser = argparse.ArgumentParser(description="Hello) It's task tracker")
    root_subparsers = parser.add_subparsers(dest='action')
    
    init_task_parser(root_subparsers)
    init_user_parser(root_subparsers)

    try:
        parsed = parser.parse_args()
        check_is_parsed_valid(parsed)
    except argparse.ArgumentTypeError as error:
        parser.error(error)

    init_default_subparsers(parsed)
    proccess_parsed(parsed)
    

def check_is_parsed_valid(parsed):
    if hasattr(parsed, 'delete') and parsed.delete is not None:
        for delete_arg in parsed.delete:
                if delete_arg in parsed and getattr(parsed, delete_arg, None) is not None:
                    raise argparse.ArgumentTypeError("{0} is not valid arg".format(delete_arg))

def make_check_valid_delete_args_action():
    class CheckValidDeleteArgs(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            VALID_DELETE_ARGS = ['title', 'descr', 'tid']

            for delete_arg in values:
                if not delete_arg in VALID_DELETE_ARGS:
                    raise argparse.ArgumentTypeError("{0} is not valid arg".format(delete_arg))
            
            setattr(namespace, self.dest, values)
    return CheckValidDeleteArgs;
    
def init_task_parser(root):
    task_parser = root.add_parser('task')
    task_root_subparser = task_parser.add_subparsers(dest='task')

    add_task_parser = task_root_subparser.add_parser('add')
    add_task_parser.add_argument('--tid', type=str, dest='tid')
    add_task_parser.add_argument('--title', type=str, required=True, dest='title')
    add_task_parser.add_argument('--descr', type=str, dest='descr')

    show_task_parser = task_root_subparser.add_parser('show')
    show_task_parser.add_argument('--tid', type=str, dest='tid')
    show_task_parser.add_argument('--title', type=str, dest='title')
    show_task_parser.add_argument('--descr', type=str, dest='descr')

    remove_task_parser = task_root_subparser.add_parser('remove')
    remove_task_parser.add_argument('--tid', type=int, required=True, dest='tid')

    edit_task_parser = task_root_subparser.add_parser('edit')
    edit_task_parser.add_argument('--tid', type=int, required=True, dest='tid')
    edit_task_parser.add_argument('--title', type=str, dest='title')
    edit_task_parser.add_argument('--descr', type=str, dest='descr')
    edit_task_parser.add_argument('--delete', dest='delete', nargs='+', action=make_check_valid_delete_args_action())

def init_user_parser(root):
    user_parser = root.add_parser('user')
    user_root_subparser = user_parser.add_subparsers(dest='user')

    add_user_parser = user_root_subparser.add_parser('add')
    show_task_parser = user_root_subparser.add_parser('show')
    delete_task_parser = user_root_subparser.add_parser('remove')

def init_default_subparsers(parsed):
    if hasattr(parsed, 'task') and parsed.task is None:
        parsed.task = 'show'
    if hasattr(parsed, 'user') and parsed.user is None:
        parsed.task = 'show'

def proccess_parsed(parsed):
    if parsed.action == 'task':
        proccess_task(parsed)
    if parsed.action == 'user':
        proccess_user(parsed)

def proccess_task(parsed):
    if parsed.task == 'add':
        TaskController.save_task(parsed.title, parsed.descr, -1 if parsed.tid is None else int(parsed.tid))
    if parsed.task == 'show':
        TaskController.fetch_tasks(parsed.tid, parsed.title, parsed.descr)
    if parsed.task == 'remove':
        TaskController.remove_task(parsed.tid)
    if parsed.task == 'edit':
        delete_list = []
        if parsed.delete is not None:
            for parsed_delete in parsed.delete:
                if parsed_delete == 'title':
                    delete_list.append('title')
                if parsed_delete == 'descr':
                    delete_list.append('description')
        TaskController.edit_task(parsed.tid, delete_list, title=parsed.title, description=parsed.descr)

def proccess_user(parsed):
    pass
