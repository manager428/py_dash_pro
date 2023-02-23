from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, username, watchuuids, groups):
        self.id = username
        self.username = username
        self.email = username
        self.watchuuids = watchuuids
        self.groups = groups

    def display(self):
        print("ID: %d \nName: %s" % (self.id, self.username))

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.watchuuids}', '{self.groups}')"