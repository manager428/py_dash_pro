from flask import Flask, json, session , request , jsonify, redirect
from flask_login import LoginManager
from datetime import timedelta
from config import app_config
from os import environ
import decimal

app_flask = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

app_env = environ.get('app_env', 'dev')
app_flask.config.from_object(app_config[app_env])

application = app_flask

login_manager = LoginManager(application)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@app_flask.before_request
def before_request():
    session.permanent = True
    application.permanent_session_lifetime = timedelta(minutes=30)


@login_manager.unauthorized_handler
def unauth_handler():
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(success=False,data={'login_required': True},
                       message='Authorize, please login to access this page.'), 401
    else:
        return redirect('/login?next=' + request.path)


class MyJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to strings.
            return float(obj)
        return super(MyJSONEncoder, self).default(obj)


from src import auth, pages

