from vmb_db.user_info import get_user_by_id, get_user_by_name
from SupportUser import User


def loadUserByID(uid):
    user = get_user_by_id(uid)
    return loadUser(user)


def loadUserByUsername(username):
    user = get_user_by_name(username)
    return loadUser(user)

def loadUser(user):
    return User(user['USERS_id'], user['user_name'], user['upload_inv']) if user else None

