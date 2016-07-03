#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:09

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import user
from ..models import User


@user.route('/signin', methods=['GET', 'POST'])
def signin():
    _form = request.form
    if request.method == 'GET':
        return render_template('user/signin.html', form=_form)
    elif request.method == 'POST':
        u = User.query.filter_by(email=_form['email']).first()
        if u is not None and user.verify_password(_form['password']):
            login_user(user)
            return redirect(request.args.get('next') or url_for('voice.index'))
        else:
            message = 'Invalid username or password.'
            return render_template('user/signin.html', form=_form, message=message)


@user.route('/signout')
@login_required
def signout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('voice.index'))


@user.route('/reg')
def reg():
    return "REG"


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