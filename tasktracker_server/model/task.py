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
        self.plan_tid = None

    def shift_time(self, shift):
        if self.supposed_start_time is not None:
            self.supposed_start_time += shift
        if self.supposed_end_time is not None:
            self.supposed_end_time += shift
        if self.deadline_time is not None:
            self.deadline_time += shift

    def is_time_overlap(self, time_range):
        return (not self.is_after_time(time_range) 
            and not self.is_before_time(time_range))

    def is_after_time(self, time_range):
        start_time = time_range[0]
        if len(time_range) == 1:
            end_time = start_time
        else:
            end_time = time_range[1]

        after_start = self._compare_time(start_time, 
            lambda to_compare, with_compare: to_compare > with_compare)
        after_end = self._compare_time(end_time, 
            lambda to_compare, with_compare: to_compare > with_compare)
        return after_start and after_end

    def is_before_time(self, time_range):
        start_time = time_range[0]
        if len(time_range) == 1:
            end_time = start_time
        else:
            end_time = time_range[1]

        before_start = self._compare_time(start_time, 
            lambda to_compare, with_compare: to_compare < with_compare)
        before_end = self._compare_time(end_time, 
            lambda to_compare, with_compare: to_compare < with_compare)
        return before_start and before_end

    def _compare_time(self, time, comparator):
        def compare(to_compare, with_compare, comparator):
            if to_compare is not None:
                return comparator(to_compare, with_compare)
            else:
                return True
        return (compare(self.supposed_start_time, time, comparator)
            and compare(self.supposed_end_time, time, comparator)
            and compare(self.deadline_time, time, comparator))

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
        plan_tid = 'plan_tid'

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.__dict__ == other.__dict__

class Status():
    PENDING = 0
    ACTIVE = 1
    COMPLETED = 2
    OVERDUE = 3

    @staticmethod
    def to_str(status):
        if status == Status.PENDING:
            return "pending"
        if status == Status.ACTIVE:
            return "active"
        if status == Status.COMPLETED:
            return "completed"
        if status == Status.OVERDUE:
            return "overdue"

    @staticmethod
    def from_str(status):
        if status == 'pending':
            return Status.PENDING
        if status == 'active':
            return Status.ACTIVE
        if status == 'completed':
            return Status.COMPLETED
        if status == 'overdue':
            return Status.OVERDUE

class Priority():
    LOW = 0
    NORMAL = 1
    HIGH = 2
    HIGHEST = 3

    @staticmethod
    def to_str(priority):
        if priority == Priority.LOW:
            return "low"
        if priority == Priority.NORMAL:
            return "normal"
        if priority == Priority.HIGH:
            return "high"
        if priority == Priority.HIGHEST:
            return "highest"

    @staticmethod
    def from_str(priority):
        if priority == 'low':
            return Priority.LOW
        if priority == 'normal':
            return Priority.NORMAL
        if priority == 'high':
            return Priority.HIGH
        if priority == 'highest':
            return Priority.HIGHEST