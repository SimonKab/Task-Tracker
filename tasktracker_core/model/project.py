class Project():

    default_project_name = 'Default'

    def __init__(self):
        self.pid = None
        self.creator = None
        self.name = None
        self.admins = None
        self.guests = None

    def get_user_kind(self, uid):
        if (self.creator == uid 
            or (self.admins is not None and uid in self.admins)):
            return self.UserKind.ADMIN
        if self.guests is not None and uid in self.guests:
            return self.UserKind.GUEST
        return None

    def participiants_exist(self):
        return ((self.admins is not None and len(self.admins) != 0) and
                (self.guests is not None and len(self.guests) != 0))

    class UserKind():
        ADMIN = 0
        GUEST = 1
        CREATOR = 2

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