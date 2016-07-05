#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:09

from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext
import re
from . import user
from ..models import User
from ..email import send_email
from .. import db


alphanumeric = re.compile(r'^[0-9a-zA-Z\_]*$')
email_address = re.compile(r'[a-zA-z0-9]+\@[a-zA-Z0-9]+\.+[a-zA-Z]')
token_uid_dict = {}


@user.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for("voice.index"))
        return render_template('user/signin.html', form=None)
    elif request.method == 'POST':
        _form = request.form
        u = User.query.filter_by(email=_form['email']).first()
        if u is not None and u.verify_password(_form['password']):
            login_user(u)
            return redirect(request.args.get('next') or url_for('voice.index'))
        else:
            message = gettext('Invalid username or password.')
            return render_template('user/signin.html', form=_form, message=message)


@user.route('/signout')
@login_required
def signout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('voice.index'))


@user.route('/register', methods=['GET', 'POST'])
def reg():
    if request.method == 'GET':
        return render_template('user/reg.html', form=None)
    elif request.method == 'POST':
        _form = request.form
        username = _form['username']
        email = _form['email']
        password = _form['password']
        password2 = _form['password2']

        message_e, message_u, message_p = "", "", ""
        # Check username is valid or not.
        if not username:
            message_u = gettext('Username can not be empty.')
        elif not alphanumeric.match(username):
            message_u = gettext('Username can only contain letters digits and underscore.')
        elif User.query.filter_by(username=username).first():
            message_u = gettext('Username already exists.')

        # Check email is valid or not.
        if not email:
            message_e = gettext('Email address can not be empty.')
        elif not email_address.match(email):
            message_e = gettext('Email address is invalid.')
        elif User.query.filter_by(email=email).first():
            message_e = gettext('Email already exists.')

        # Check the password is valid or not.
        if password != password2:
            message_p = gettext("Passwords don't match.")
        elif password == "" or password2 == "":
            message_p = gettext("Passwords can not be empty.")

        if message_u or message_p or message_e:
            return render_template("user/reg.html", form=_form,
                                   message_u=message_u,
                                   message_p=message_p,
                                   message_e=message_e)

        # A valid register info, save the info into db.
        else:
            reg_user = User(username=username, email=email, password=password)
            db.session.add(reg_user)
            db.session.commit()
            login_user(reg_user)

            # TODO, Confirm the email.

            return redirect(url_for('user.signin'))


@user.route("/password", methods=['GET', 'POST'])
@login_required
def password_change():
    if request.method == 'GET':
        return render_template('user/passwd_change.html', form=None)
    elif request.method == 'POST':
        _form = request.form
        cur_password = _form['old-password']
        new_password = _form['password']
        new_password_2 = _form['password2']

        if not cur_password:
            message_cur = "The old password can not be empty."
        elif not current_user.verify_passwor(cur_password):
            message_cur = "The old password is not correct."

        if new_password != new_password_2:
            message_new = gettext("Passwords don't match.")
        elif new_password_2 == "" or new_password == "":
            message_new = gettext("Passwords can not be empty.")

        if message_cur or message_new:
            return render_template("user/passwd_change.html", form=_form,
                                   message_cur=message_cur,
                                   message_new=message_new)
        else:
            current_user.password = new_password
            db.session.commit()
            message_success = "Reset password successfully"
            return render_template("user/passwd_change.html", message_success=message_success)


@user.route('/password/reset', methods=['GET', 'POST'])
def password_reset_request():
    if request.method == 'GET':
        return render_template('user/passwd_reset.html', form=None)
    elif request.method == 'POST':
        _form = request.form
        email_addr = _form["email"]
        u = User.query.filter_by(email=email_addr).first()
        message_email = ""
        if not email_addr:
            message_email = gettext("The email can not be empty")
        elif not email_address.match(email_addr):
            message_email = gettext('Email address is invalid.')
        elif not u:
            message_email = gettext("The email has not be registered")

        if message_email:
            return render_template('user/passwd_reset.html', message_email=message_email)
        else:
            token = u.generate_reset_token()
            token_uid_dict[token] = u.id
            send_email(u.email, 'Reset Your Password',
                       'user/passwd_reset_email',
                       user=u, token=token)

            return render_template('user/passwd_reset_sent.html')


@user.route('/password/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if request.method == "GET":
        return render_template('user/passwd_reset_confirm.html', form=None)
    elif request.method == 'POST':
        _form = request.form
        new_password = _form['password']
        new_password_2 = _form['password2']

        message_p = ""
        if new_password != new_password_2:
            message_p = gettext("Passwords don't match.")
        elif new_password_2 == "" or new_password == "":
            message_p = gettext("Passwords can not be empty.")

        if message_p:
            return render_template('user/passwd_reset_confirm.html', message_p=message_p)
        else:
            # Get the token without input the email address.
            if token in token_uid_dict:
                uid = token_uid_dict[token]
                u = User.query.filter_by(id=uid).first()
                if u.reset_password(token, new_password):
                    reset_result = "Successful"
                else:
                    reset_result = "Failed"
            else:
                reset_result = "Failed"

            return render_template('user/passwd_reset_done.html', message=reset_result)


@user.route('/<int:uid>')
def info(uid):
    return "%s" % uid


@user.route('/setting')
def setting():
    return "Setting"


@user.route("/mention")
def mention():
    return "Mention"


# urlpatterns = patterns(
#     'account.views',
#     url(r'^(?P<user_id>\d+)/info/$',
#         'user_info', name='user_info'),
#     url(r'^super/$', 'super_login', name='super_login'),
#     url(r'^avatar/$', 'user_avatar', name='user_avatar'),
#     url(r'^reset/password/done/$',
#         'password_reset_done',
#         name='password_reset_done')
# )