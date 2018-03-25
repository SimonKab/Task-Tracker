
class Task():

    def __init__(self):
        self.tid = 0
        self.uid = 0
        self.responsible_uid = 0
        self.pid = 0
        self.parent_tid = 0
        self.title = None
        self.description = None
        self.priority = None
        self.status = None
        self.supposed_start_time = None
        self.supposed_end_time = None
        self.deadline_time = None
        self.actual_start_time = None
        self.actual_end_time = None
        self.notificate_supposed_start = False
        self.notificate_supposed_end = False
        self.notificate_deadline = False
        self.tag_id_list = None
        self.block_tid_list = None
        self.block_by_tid = None
        self.relation_tid_list = None

class Status():
    PENDING = 0
    ACTIVE = 1
    COMPLETED = 2
    OVERDUE = 3

class Priority():
    LOW = 0
    NORMAL = 1
    HIGH = 2
    HIGHEST = 3