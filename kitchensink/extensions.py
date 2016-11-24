from flask_fulfil import Fulfil
from flask_babel import Babel
from flask_login import LoginManager
from flask_debugtoolbar import DebugToolbarExtension
#from flask.ext.celery import Celery

#celery = Celery()
fulfil = Fulfil()
babel = Babel()
toolbar = DebugToolbarExtension()
login_manager = LoginManager()
login_manager.login_view = "user.login"