#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:09

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from flask_babel import gettext
import re
from . import user
from ..models import User
from .. import db


alphanumeric = re.compile(r'^[0-9a-zA-Z\_]*$')
email_address = re.compile(r'[a-zA-z0-9]+\@[a-zA-Z0-9]+\.+[a-zA-Z]')


@user.route('/signin', methods=['GET', 'POST'])
def signin():
    _form = request.form
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for("voice.index"))
        return render_template('user/signin.html', form=_form)
    elif request.method == 'POST':
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
    _form = request.form
    if request.method == 'GET':
        return render_template('user/reg.html', form=_form)
    elif request.method == 'POST':
        username = _form['username']
        email = _form['email']
        password = _form['password']
        password2 = _form['password2']

        message_e, message_u, message_p = "", "", ""
        # Check username is valid or not.
        if not username:
            message_u = gettext('username can not be empty.')
        elif not alphanumeric.match(username):
            message_u = gettext('username can only contain letters digits and underscore.')
        elif User.query.filter_by(username=username).first():
            message_u = gettext('username already exists.')

        # Check email is valid or not.
        if not email:
            message_e = gettext('email address can not be empty.')
        elif not email_address.match(email):
            message_e = gettext('email address is invalid.')
        elif User.query.filter_by(email=email).first():
            message_e = gettext('email already exists.')

        # Check the password is valid or not.
        if password != password2:
            message_p = gettext("passwords don't match.")
        elif password == "" or password2 == "":
            message_p = gettext("passwords can not be empty.")

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

            # TODO, Confirm the email.
            return redirect(url_for('user.signin'))


@user.route('/<int:uid>')
def info(uid):
    return "%s" % uid


@user.route('/setting')
def setting():
    return "Setting"


@user.route("/mention")
def mention():
    return "Mention"


@user.route("/password")
def password_reset():
    return "Reset"

# urlpatterns = patterns(
#     'account.views',
#     url(r'^(?P<user_id>\d+)/info/$',
#         'user_info', name='user_info'),
#     url(r'^super/$', 'super_login', name='super_login'),
#     url(r'^signout/$', 'user_logout', name='signout'),
#     url(r'password/$', 'change_password',
#         name='change_password'),
#     url(r'^avatar/$', 'user_avatar', name='user_avatar'),
#     url(r'^reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
#         'reset_confirm', name='password_reset_confirm'),
#     url(r'^reset/$', 'reset', name='password_reset'),
#     url(r'^reset/password/done/$',
#         'password_reset_done',
#         name='password_reset_done')
# )