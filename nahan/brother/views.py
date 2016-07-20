#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-18 21:33:38

from flask import render_template, redirect, request, url_for, abort, current_app, jsonify
from flask_login import login_user, logout_user, current_user
from flask_babel import gettext
from functools import wraps
from ..util import natural_time
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
            return redirect(request.args.get('next') or url_for('brother.user_manage', classify="normal"))
        return render_template("brother/auth.html", form=None)
    elif request.method == 'POST':
        _form = request.form
        u = User.query.filter_by(email=_form['email']).first()
        if u and u.verify_password(_form['password']) and u.is_superuser:
            login_user(u)
            return redirect(request.args.get('next') or url_for('brother.user_manage', classify="normal"))
        else:
            message = gettext('Invalid username or password.')
            return render_template('brother/auth.html', form=_form, message=message)


@brother.route("/admin/signout/")
@superuser_login
def signout():
    logout_user()
    return redirect(url_for('brother.auth'))


@brother.route("/admin/topics/<string:classify>")
@superuser_login
def topic_manage(classify):
    if request.method == 'GET':
        if classify == 'normal':
            return render_template('brother/topic.html', title=gettext('normal topics'))
        elif classify == 'deleted':
            return render_template('brother/topic_deleted.html', title=gettext('deleted topics'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/nodes/<string:classify>")
@superuser_login
def node_manage(classify):
    if request.method == 'GET':
        if classify == 'normal':
            return render_template('brother/node.html', title=gettext('normal nodes'))
        elif classify == 'deleted':
            return render_template('brother/node_deleted.html', title=gettext('deleted nodes'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/users/<string:classify>")
@superuser_login
def user_manage(classify):
    if request.method == 'GET':
        if classify == 'normal':
            return render_template('brother/user.html', title=gettext('normal users'))
        elif classify == 'deleted':
            return render_template('brother/user_deleted.html', title=gettext('blacklist users'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/topic/<int:tid>/")
@superuser_login
def topic_more(tid):
    return "edit %d" % tid


@brother.route("/admin/node/<int:nid>/")
@superuser_login
def node_more(nid):
    return "edit %d" % nid


@brother.route("/admin/user/<int:uid>/")
@superuser_login
def user_more(uid):
    return "edit %d" % uid


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


@brother.route("/admin/nodes/list/")
@superuser_login
def node_table_list():
    fields = ['id', 'title', 'description']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    nodes = Node.query.filter_by(deleted=False).all()
    # Filter the users according to the keywords.
    key = request.args.get('sSearch')
    if key:
        nodes = list(filter(lambda x: (key == str(x.id) or key in x.title or
                                       key in x.description), nodes))

    # Sort the data according to specified columns.
    nodes.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['aaData'] = []
    data['iTotalDisplayRecords'] = len(nodes)
    nodes = nodes[start:start + length]
    data['iTotalRecords'] = User.query.count()
    for n in nodes:
        info_list = [n.id, n.title, n.description]
        info_list.append('<a href="%s" class="label label-success">%s</a>' %
                         (url_for('brother.node_more', nid=n.id), gettext('more')))
        data['aaData'].append(info_list)

    return jsonify(**data)


@brother.route("/admin/users/list/<string:boolean>")
@superuser_login
def user_table_list(boolean):
    deleted = True if boolean == "True" else False
    fields = ['id', 'username', 'email', 'last_login', 'is_superuser']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    users = User.query.filter_by(deleted=deleted).all()
    # Filter the users according to the keywords.
    key = request.args.get('sSearch')
    if key:
        users = list(filter(lambda x: (key == str(x.id) or key in x.username or
                                       key in x.email or key in x.last_login), users))

    # Sort the data according to specified columns.
    users.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['aaData'] = []
    data['iTotalDisplayRecords'] = len(users)
    users = users[start:start + length]
    data['iTotalRecords'] = User.query.count()
    for u in users:
        info_list = [u.id, u.username, u.email, natural_time(u.last_login),
                     gettext('Yes') if u.is_superuser else gettext('No')]
        info_list.append('<a href="%s" class="label label-success">%s</a>' %
                         (url_for('brother.user_more', uid=u.id), gettext('more')))
        data['aaData'].append(info_list)

    return jsonify(**data)


@brother.route("/admin/topics/delete/")
@superuser_login
def topic_bulk_delete():
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        delete(i)
    return "Done"


@brother.route("/admin/nodes/delete/")
@superuser_login
def node_bulk_delete():
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        node_delete(i)
    return "Done"


@brother.route("/admin/users/process/<string:status>")
@superuser_login
def user_bulk_process(status):
    user_status = True if status == 'active' else False
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        user_process(i, status=user_status)
    return "Done"


@brother.route("/admin/delete_topic/<int:tid>")
@superuser_login
def delete(tid):
    t = Topic.query.filter_by(id=tid, deleted=False).first_or_404()
    t.deleted = True
    db.session.commit()
    # Delete all the comment and appendix in this topic.
    map(lambda a: append_delete(a.id), t.extract_appends())
    map(lambda c: comment_delete(c.id), t.extract_comments())
    return redirect(url_for("brother.topic_manage"))


@brother.route("/admin/delete_appendix/<int:aid>")
@superuser_login
def append_delete(aid):
    ta = TopicAppend.query.filter_by(id=aid, deleted=False).first_or_404()
    ta.deleted = True
    db.session.commit()
    return redirect(url_for("brother.topic_more", tid=ta.topic_id))


@brother.route("/admin/delete_comment/<int:cid>")
@superuser_login
def comment_delete(cid):
    c = Comment.query.filter_by(id=cid, deleted=False).first_or_404()
    c.deleted = True

    # Delete this comment in corresponding topic.  Just need to minus the reply count.
    t = Topic.query.filter_by(id=c.topic_id).first()
    t.reply_count -= 1
    db.session.commit()
    return redirect(url_for("brother.topic_more", tid=c.topic_id))


@brother.route("/admin/delete_node/<int:nid>")
@superuser_login
def node_delete(nid):
    """ Delete the useless node by id. (Delete all the topics under this node.)
    """
    n = Node.query.filter_by(id=nid).first()
    n.deleted = True
    db.session.commit()
    return redirect(url_for("brother.node_manage"))


@brother.route("/admin/process_user/<int:uid>")
@superuser_login
def user_process(uid, status=False):
    """ Move the user to blacklist or reactivate the blocked user.

    Block the user if status == False, or reactivate the user.
    Delete or add all the topics and comments the user has made at the same time
    """
    u = User.query.filter_by(id=uid).first()
    if u.is_superuser or u.deleted:
        return redirect(url_for("brother.user_manage"))

    u.deleted = True

    # Delete all the user's topics
    if u.topics:
        topic_list = list(map(int, u.topics.split(',')))
        for t_id in topic_list:
            t = Topic.query.filter_by(id=t_id).first()
            t.deleted = True

    # Delete all the user's comments
    if u.comments:
        comment_list = list(map(int, u.comments.split(',')))
        for c_id in comment_list:
            c = Comment.query.filter_by(id=c_id).first()
            c.deleted = True

    db.session.commit()
    return redirect(url_for("brother.user_manage"))


@brother.route("/admin/node/create/")
@superuser_login
def node_create():
    return "Create"
