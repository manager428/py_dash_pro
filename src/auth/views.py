from flask import session
from flask import render_template, url_for, flash, redirect, request
from src.auth.forms import LoginForm, ForgetPasswordForm, ConfirmForgetPasswordForm, ForceChangePasswordForm
from flask_login import login_user, current_user, logout_user
from src.libs.func.cognito import *
from src.libs.func.cognito import user_pool_id, app_client_id
import boto3

dynamodb = boto3.resource('dynamodb')
db_table = dynamodb.Table(application.config['DYNAMODB_TABLE'])
s3client = boto3.client('s3')
s3_bucket_name = application.config['S3_PROCESSED_BUCKET']


@application.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        session['username'] = current_user.username
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = do_cognito_login(form.email.data, form.password.data)
        if user == "ForceChangePasswordException":
            session['force_password_change_user'] = form.email.data
            return redirect(url_for('force_password_change'))
        if user == "NotAuthorizedException":
            flash('Login Unsuccessful. Please check username and password', 'danger')
            return render_template('login.html', title='Login', form=form)
        session['username'] = user.username
        session['group'] = user.groups
        # session['user'] = user
        if do_cognito_login(form.email.data, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')

            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)


@application.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('group', None)
    # session.pop('user', None)
    logout_user()
    return redirect(url_for('home'))


@application.route("/forget_password", methods=['GET', 'POST'])
def forget_password():
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        username = form.username.data
        user = Cognito(user_pool_id, app_client_id, username=username)
        try:
            user.initiate_forgot_password()
            session['forget_password_user'] = username
            flash("Verification code has been sent to your registered email !", 'success')
            return redirect(url_for('forget_password_confirm'))
        except Exception as e:
            print(e)
            flash("Error while initiating froget password !", 'danger')
            return render_template('auth/forget_password.html', title='Change Password', form=form)

    return render_template('auth/forget_password.html', title='Change Password', form=form)


@application.route("/forget_password_confirm", methods=['GET', 'POST'])
def forget_password_confirm():
    form = ConfirmForgetPasswordForm()
    if form.validate_on_submit():
        username = session['forget_password_user']
        verification_code = form.verification_code.data
        new_password = form.new_password.data
        user = Cognito(user_pool_id, app_client_id, username=username)
        try:
            user.confirm_forgot_password(verification_code, new_password)
            del session['forget_password_user']
            flash("Password changed successfully !", 'success')
            return redirect(url_for('login'))
        except Exception as e:
            print(e)
            flash(str(e).split(":")[1], 'danger')
            return render_template('auth/forget_password_confirm.html', title='Change Password', form=form)

    return render_template('auth/forget_password_confirm.html', title='Change Password', form=form)


@application.route("/force_password_change", methods=['GET', 'POST'])
def force_password_change():
    form = ForceChangePasswordForm()
    username = session['force_password_change_user']
    form.username.data = username

    if form.validate_on_submit():
        tem_password = form.tem_password.data
        new_password = form.new_password.data
        confirm_password = form.confirm_password.data
        try:
            user = Cognito(user_pool_id, app_client_id, username=username)
            output = user.new_password_challenge(tem_password, confirm_password)
        except Exception as e:
            print(e)
            flash("Incorrect username or password", 'danger')
            return render_template('auth/force_change_password.html', title='Forget Password', form=form)
        flash("Password changed successfully !", 'success')
        return redirect(url_for('login'))
    return render_template('auth/force_change_password.html', title='Forget Password', form=form)
