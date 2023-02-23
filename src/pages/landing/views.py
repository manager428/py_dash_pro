import os
from flask import render_template, send_from_directory
from src import application


@application.route('/privacy_policy', methods=['GET'])
def privacy_policy():
    return render_template('landing/privacy_policy.html', title='Privacy Policy')


@application.route('/terms_of_use', methods=['GET'])
def terms_of_use():
    workingdir = os.path.abspath(os.getcwd())
    filepath = workingdir + '/src/static/doc/'
    return send_from_directory(filepath, 'termsofuse.pdf')


@application.route('/support', methods=['GET'])
def support():
    return render_template('landing/support.html', title='support')

@application.route("/about")
def about():
    return render_template('landing/about.html', title='About')
