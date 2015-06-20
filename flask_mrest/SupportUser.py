import os
import base64

from flask.ext.login import UserMixin
from flask.ext.login import AnonymousUserMixin as AnonymousUser
from flask.ext.bcrypt import Bcrypt, generate_password_hash

class User(UserMixin):
    # proxy for a database of users
    user_database = {"JohnDoe": ("JohnDoe", "John"),
               "JaneDoe": ("JaneDoe", "Jane")
    }

    def __init__(self, uid, username, upload_inv):
        self.id = uid
        self.username = username
        self.upload_inv = upload_inv
    @classmethod
    def get(cls,id):
        return cls.user_database.get(id)


class Anonymous(AnonymousUser, dict):

    def __init__(self):
        super(Anonymous, self).__init__()
        self.username = None

    def __getattribute__(self, item):
        if item in ['pw', 'password']:
            raise AttributeError("Anonymous users have no '%s' attribute" % item)
        else:
            return super(Anonymous, self).__getattribute__(item)

    def hasBankRights(self):
        return False

    def is_authenticated(self):
        return False

    def is_active(self):
        return True
