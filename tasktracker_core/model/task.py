import datetime

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

    def only_start(self):
        return (self.supposed_start_time is not None
            and self.supposed_end_time is None
            and self.deadline_time is None)

    def only_end(self):
        return (self.supposed_start_time is None
            and (self.supposed_end_time is not None
            or self.deadline_time is not None))

    def get_time_interval(self):
        range = self.get_time_range()
        if len(range) != 2:
            return 0

        return range[1] - range[0]

    def get_left_border(self):
        if self.supposed_start_time is not None:
            return self.supposed_start_time
        if self.supposed_end_time is not None:
            return self.supposed_end_time
        if self.deadline_time is not None:
            return self.deadline_time

    def get_time_range(self):
        left_border = None
        right_border = None
        if self.supposed_end_time is not None:
            right_border = self.supposed_end_time
        if self.deadline_time is not None:
            right_border = self.deadline_time
        if self.supposed_start_time is not None:
            left_border = self.supposed_start_time
        
        if left_border is None and right_border is None:
            return []
        if left_border is not None and right_border is not None:
            return (left_border, right_border)
        if left_border is None:
            return (right_border, )
        if right_border is None:
            return (left_border, )

    def shift_time(self, shift):
        def shift_month(var, shift):
            if var is not None:
                utc = datetime.datetime.utcfromtimestamp(var / 1000.0)
                next = utc.month+1
                if next > 12:
                    next = 1
                if (datetime.date(utc.year, next, 1) - datetime.date(utc.year, utc.month, 1)).days == 31:
                    shift += 24*3600*1000
            return shift

        # if datetime.timedelta(milliseconds=shift).days >= 30 and datetime.timedelta(milliseconds=shift).days < 60:
        #     if self.supposed_start_time is not None:
        #         shift = shift_month(self.supposed_start_time, shift)
        #     if self.supposed_end_time is not None:
        #         shift = shift_month(self.supposed_end_time, shift)
        #     if self.deadline_time is not None:
        #         shift = shift_month(self.deadline_time, shift)

        if self.supposed_start_time is not None:
            self.supposed_start_time += shift
        if self.supposed_end_time is not None:
            self.supposed_end_time += shift
        if self.deadline_time is not None:
            self.deadline_time += shift

    def is_time_overlap(self, time_range):
        return (not self.is_after_time(time_range) 
            and not self.is_before_time(time_range))

    def is_time_overlap_fully(self, time_range):
        if len(time_range) != 2:
            return False

        return (not self.is_after_time((time_range[0], ))
            and not self.is_before_time((time_range[1], )))

    def is_task_inside_of_range(self, time_range):
        if len(time_range) != 2:
            return False

        return (self.is_after_time((time_range[1], ), True)
            and self.is_before_time((time_range[0], ), True))

    def is_task_inside_of_range_parent(self, time_range):
        if len(time_range) != 2:
            return False

        return (self.is_before_time((time_range[1], ), True)
            and self.is_after_time((time_range[0], ), True))


    def is_after_time(self, time_range, not_strong=False):
        if len(time_range) == 0:
            return False

        start_time = time_range[0]
        if len(time_range) == 1:
            end_time = start_time
        else:
            end_time = time_range[1]

        if not_strong:
            after_start = self._compare_time(start_time, 
                lambda to_compare, with_compare: to_compare >= with_compare)
            after_end = self._compare_time(end_time, 
                lambda to_compare, with_compare: to_compare >= with_compare)
        else:
            after_start = self._compare_time(start_time, 
                lambda to_compare, with_compare: to_compare > with_compare)
            after_end = self._compare_time(end_time, 
                lambda to_compare, with_compare: to_compare > with_compare)
        return after_start and after_end

    def is_before_time(self, time_range, not_strong=False):
        if len(time_range) == 0:
            return False

        start_time = time_range[0]
        if len(time_range) == 1:
            end_time = start_time
        else:
            end_time = time_range[1]

        if not_strong:
            print('t', start_time, self.supposed_start_time, self.supposed_end_time, self.deadline_time)
            before_start = self._compare_time(start_time, 
                lambda to_compare, with_compare: to_compare <= with_compare)
            before_end = self._compare_time(end_time, 
                lambda to_compare, with_compare: to_compare <= with_compare)
        else:
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

    @classmethod
    def to_str(cls, status):
        if status == cls.PENDING:
            return "pending"
        if status == cls.ACTIVE:
            return "active"
        if status == cls.COMPLETED:
            return "completed"
        if status == cls.OVERDUE:
            return "overdue"

    @classmethod
    def from_str(cls, status):
        if status == 'pending':
            return cls.PENDING
        if status == 'active':
            return cls.ACTIVE
        if status == 'completed':
            return cls.COMPLETED
        if status == 'overdue':
            return cls.OVERDUE

    @classmethod
    def raise_status(cls, status):
        '''Safely raises status

        If status is COMPLETED, returns COMPLETED
        if status is ACTIVE, returns COMPLETED
        if status is PENDING, returns ACTIVE
        if status is OVERDUE, returns PENDING

        Don't raise status like status + 1, cause it can break status order
        '''
        if status == cls.COMPLETED:
            return cls.COMPLETED
        if status == cls.OVERDUE:
            return cls.PENDING
        return status + 1

    @classmethod
    def downgrade_status(cls, status):
        '''Safely downgrade status

        If status is COMPLETED, returns ACTIVE
        if status is ACTIVE, returns PENDING
        if status is PENDING, returns OVERDUE
        if status is OVERDUE, returns OVERDUE

        Don't raise status like status - 1, cause it can break status order
        '''
        if status == cls.OVERDUE:
            return cls.OVERDUE
        if status == cls.PENDING:
            return cls.OVERDUE
        return status - 1



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