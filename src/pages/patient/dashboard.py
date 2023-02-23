from flask import render_template, redirect
from flask_login import login_required
import json

from src import application
from src.libs.utils import sleep_time_recommendation


@application.route("/")
@application.route("/home")
def home():
    return redirect("/dashboard")


@application.route("/dashboard")
@login_required
def dashboard():
    sleep_time_rec = json.dumps(sleep_time_recommendation)
    return render_template('patient/dashboard/index.html', title='Dashboard', searchForm=True, sleep_time_rec = sleep_time_rec)
    
