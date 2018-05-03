class Task():

    def __init__(self):
        self.tid = 0
        self.uid = None
        self.responsible_uid = None
        self.pid = None
        self.parent_tid = None
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

    class Field():
        tid = 'tid'
        uid = 'uid'
        responsible_uid = 'responsible_uid'
        pid = 'pid'
        parent_tid = 'parent_tid'
        title = 'title'
        description = 'description'
        priority = 'priority'
        status = 'status'
        supposed_start_time = 'supposed_start_time'
        supposed_end_time = 'supposed_end_time'
        deadline_time = 'deadline_time'
        actual_start_time = 'actual_start_time'
        actual_end_time = 'actual_end_time'
        notificate_supposed_start = 'notificate_supposed_start'
        notificate_supposed_end = 'notificate_supposed_end'
        notificate_deadline = 'notificate_deadline'
        tag_id_list = 'tag_id_list'
        block_tid_list = 'block_tid_list'
        block_by_tid = 'block_by_tid'
        relation_tid_list = 'relation_tid_list'

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.__dict__ == other.__dict__

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