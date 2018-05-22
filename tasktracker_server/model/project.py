class Project():

    def __init__(self):
        self.pid = None
        self.creator = None
        self.name = None
        self.admins = None
        self.guests = None

    class Field():
        pid = 'pid'
        creator = 'creator'
        name = 'name'
        admins = 'admins'
        guests = 'guests'
    
    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.__dict__ == other.__dict__

default_project = Project()
default_project.name = 'Default'