from flask import request, flash, redirect, render_template, url_for, current_app, session
from flask.ext.login import login_user, logout_user, current_user, login_required
from flask.ext.bcrypt import Bcrypt

from vmb_db.user_info import get_user_by_name

# from db import loadUserByUsername
from .. import db

def login():
    print current_user
    if current_user.is_authenticated():
        return redirect(request.args.get('next') or '/')

    if not request.form:
        return render_template('login.html')

    if not request.form.get('username') or not request.form.get('password'):
        flash('Please enter your username and password.')
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password'].strip()

    print username
    userdb = get_user_by_name(username)
    if userdb is None or not Bcrypt().check_password_hash(str(userdb['user_pwd']), str(password)):
        return render_template('login.html', invalidCredentials=True)

    user = db.loadUserByUsername(userdb['user_name'])
    if not login_user(user):
        flash('Invalid Info')
        return render_template('login.html')

    assert current_user.is_authenticated()
    flash("Hello %s" % current_user.username)

    return redirect(request.referrer or '/')

@login_required
def logout():
    logout_user()
    return redirect('/')


@login_required
def refresh():
    session.regenerate()
    return 'ok'
