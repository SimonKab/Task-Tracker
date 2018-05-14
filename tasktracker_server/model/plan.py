class Plan():

    def __init__(self):
        self.plan_id = None
        self.tid = None
        self.start = None
        self.end = None
        self.shift = None
        self.exclude = None

    class Field():
        plan_id = 'plan_id'
        tid = 'tid'
        start = 'start'
        end = 'end'
        shift = 'shift'
        exclude = 'exclude'

    
    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.__dict__ == other.__dict__