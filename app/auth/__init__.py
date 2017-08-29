from flask import Blueprint
from flask_login import LoginManager, current_user

from app.models import Operator

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please login first!'

'''
@login_manager.user_loader
def load_user(user_id):
    return User.find(uuid=user_id)
'''


@login_manager.user_loader
def load_user(user_id):
    return Operator.query.get(int(user_id))


auth = Blueprint('auth', __name__)

from . import views


def authorization(func):
    for pri in current_user.roles:
        pass
