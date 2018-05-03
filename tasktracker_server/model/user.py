class User():

    def __init__(self):
        self.uid = 0
        self.login = None
        self.password = None
        self.online = False

    class Field():
        uid = 'uid'
        login = 'login'
        password = 'password'
        online = 'online'

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False

        return self.__dict__ == other.__dict__
