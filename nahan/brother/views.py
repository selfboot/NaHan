#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-18 21:33:38

from flask import render_template, redirect, request, url_for, abort, current_app, jsonify
from flask_login import login_user, logout_user, current_user
from flask_babel import gettext
from functools import wraps
from ..models import User, Topic, Node, Comment, TopicAppend
from . import brother
from .. import db


def superuser_login(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_superuser:
            return func(*args, **kwargs)
        else:
            return redirect(url_for('brother.auth', next=request.url))
    return wrap


@brother.route("/admin/", methods=['GET', 'POST'])
def auth():
    if request.method == 'GET':
        if current_user.is_authenticated and current_user.is_superuser:
            return redirect(request.args.get('next') or url_for('brother.user_manage'))
        return render_template("brother/auth.html", form=None)
    elif request.method == 'POST':
        _form = request.form
        u = User.query.filter_by(email=_form['email']).first()
        if u and u.verify_password(_form['password']) and u.is_superuser:
            login_user(u)
            return redirect(request.args.get('next') or url_for('brother.user_manage'))
        else:
            message = gettext('Invalid username or password.')
            return render_template('brother/auth.html', form=_form, message=message)


@brother.route("/admin/signout/")
@superuser_login
def signout():
    logout_user()
    return redirect(url_for('brother.auth'))


@brother.route("/admin/topics/")
@superuser_login
def topic_manage():
    return render_template('brother/topic.html', title=gettext('topics'))


@brother.route("/admin/topic/<int:tid>/")
@superuser_login
def topic_more(tid):
    return "edit %d" % tid


@brother.route("/admin/topics/delete/")
@superuser_login
def topic_bulk_delete():
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        delete(i)
    return "Deleted"


@brother.route("/voice/delete/<int:tid>")
def delete(tid):
    t = Topic.query.filter_by(id=tid, deleted=False).first_or_404()
    t.deleted = True
    db.session.commit()
    # Delete all the comment and appendix in this topic.
    map(lambda a: append_delete(a.id), t.extract_appends())
    map(lambda c: comment_delete(c.id), t.extract_comments())
    return redirect(url_for("voice.index"))


@brother.route("/voice/delete_appendix/<int:aid>")
def append_delete(aid):
    ta = TopicAppend.query.filter_by(id=aid, deleted=False).first_or_404()
    ta.deleted = True
    db.session.commit()
    return redirect(url_for("voice.view", tid=ta.topic_id))


@brother.route("/comment/delete/<int:cid>")
def comment_delete(cid):
    c = Comment.query.filter_by(id=cid, deleted=False).first_or_404()
    c.deleted = True

    # Delete this comment in corresponding topic.  Just need to minus the reply count.
    t = Topic.query.filter_by(id=c.topic_id).first()
    t.reply_count -= 1
    db.session.commit()
    return redirect(url_for("voice.view", tid=c.topic_id))


@brother.route("/admin/topics/list/")
@superuser_login
def topic_table_list():
    fields = ['id', 'title']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    topics = Topic.query.filter_by(deleted=False).all()

    # Filter the topic according to the keywords.
    key = request.args.get('sSearch')
    if key:
        topics = list(filter(lambda x: (key == str(x.id) or key in x.title or
                                        key in x.user().username or key in x.node().title), topics))

    # Sort the data according to specified columns.
    if order_field == 2:
        topics.sort(key=lambda x: x.user().username, reverse=False if order_dir == 'asc' else True)
    elif order_field == 3:
        topics.sort(key=lambda x: x.node().title, reverse=False if order_dir == 'asc' else True)
    else:
        topics.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['aaData'] = []
    data['iTotalDisplayRecords'] = len(topics)
    topics = topics[start:start + length]
    data['iTotalRecords'] = Topic.query.count()
    for t in topics:
        info_list = [t.id, t.title, t.user().username, t.node().title]
        info_list.append('<a href="%s" class="label label-success">%s</a>' %
                         (url_for('brother.topic_more', tid=t.id), gettext('more')))
        data['aaData'].append(info_list)

    return jsonify(**data)


@brother.route("/admin/nodes/")
@superuser_login
def node_manage():
    return render_template('brother/node.html', title=gettext('node'))


@brother.route("/admin/users/")
@superuser_login
def user_manage():
    return render_template('brother/user.html', title=gettext('user'))
