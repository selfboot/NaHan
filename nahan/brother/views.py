#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-09-08 18:06:32

from flask import render_template, redirect, request, url_for, abort, current_app, jsonify
from flask_login import login_user, logout_user, current_user
from flask_babel import gettext
from functools import wraps
from flask_paginate import Pagination
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


@brother.route("/admin/topics/")
@superuser_login
def topic_manage():
    if request.method == 'GET':
        classify = request.args['classify']
        if classify == 'normal':
            return render_template('brother/topic.html', title=gettext('Normal Topics'))
        elif classify == 'deleted':
            return render_template('brother/topic_deleted.html', title=gettext('Deleted Topics'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/comments/")
@superuser_login
def comment_manage():
    if request.method == 'GET':
        classify = request.args['classify']
        if classify == 'normal':
            return render_template('brother/comment.html', title=gettext('Normal Comments'))
        elif classify == 'deleted':
            return render_template('brother/comment_deleted.html', title=gettext('Deleted Comments'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/nodes/")
@superuser_login
def node_manage():
    if request.method == 'GET':
        classify = request.args['classify']
        if classify == 'normal':
            return render_template('brother/node.html', title=gettext('Normal Nodes'))
        elif classify == 'deleted':
            return render_template('brother/node_deleted.html', title=gettext('Deleted Nodes'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/users/")
@superuser_login
def user_manage():
    if request.method == 'GET':
        classify = request.args['classify']
        if classify == 'normal':
            return render_template('brother/user.html', title=gettext('Normal Users'))
        elif classify == 'deleted':
            return render_template('brother/user_deleted.html', title=gettext('Blacklist Users'))
        else:
            abort(404)
    else:
        abort(404)


@brother.route("/admin/topic/<int:tid>/")
@superuser_login
def topic_more(tid):
    """ Delete part or all of one topic.

    Can delete either one or more comment, appendix or the whole topic.
    """
    t = Topic.query.filter_by(id=tid).first_or_404()
    if request.method == 'GET':
        per_page = current_app.config['PER_PAGE']
        page = int(request.args.get('page', 1))
        offset = (page - 1) * per_page

        all_comments = t.extract_comments()
        comments = all_comments[offset:offset + per_page]
        pagination = Pagination(page=page, total=len(all_comments),
                                per_page=per_page,
                                record_name='comments',
                                CSS_FRAMEWORK='bootstrap',
                                bs_version=3)

        return render_template('brother/topic_more.html',
                               title=gettext('More About Topic'),
                               topic=t,
                               comments=comments,
                               pagination=pagination)
    else:
        abort(404)


@brother.route("/admin/node/<int:nid>/", methods=['GET', 'POST'])
@superuser_login
def node_more(nid):
    """ Update the title and description of node despite of node is deleted or not.
    """
    n = Node.query.filter_by(id=nid).first_or_404()
    if request.method == 'GET':
        return render_template('brother/node_more.html',
                               title=gettext('More About Node'),
                               node=n)
    elif request.method == 'POST':
        n.title = request.form['title']
        n.description = request.form['description']
        db.session.commit()
        return redirect(url_for('brother.node_manage', classify="normal"))
    else:
        abort(404)


@brother.route("/admin/user/<int:uid>/")
@superuser_login
def user_more(uid):
    content = request.args['content']
    if content not in ['Topic', 'Comment']:
        abort(404)

    if request.method == 'GET':
        u = User.query.filter_by(id=uid).first_or_404()
        per_page = current_app.config['PER_PAGE']
        page = int(request.args.get('page', 1))
        offset = (page - 1) * per_page

        if content == 'Topic':
            all_topics = u.extract_topics()
            topics = all_topics[offset:offset + per_page]
            pagination_topic = Pagination(page=page, total=len(all_topics),
                                          per_page=per_page,
                                          record_name='topics',
                                          CSS_FRAMEWORK='bootstrap',
                                          bs_version=3)
            return render_template('brother/user_more_topic.html',
                                   title=gettext('More About User'),
                                   user=u,
                                   topics=topics,
                                   pagination_topic=pagination_topic)
        else:
            all_comments = u.extract_comments()
            comments = all_comments[offset:offset + per_page]
            pagination_comment = Pagination(page=page, total=len(all_comments),
                                            per_page=per_page,
                                            record_name='comments',
                                            CSS_FRAMEWORK='bootstrap',
                                            bs_version=3)
            return render_template('brother/user_more_comment.html',
                                   title=gettext('More About User'),
                                   user=u,
                                   comments=comments,
                                   pagination_comment=pagination_comment)
    else:
        abort(404)


@brother.route("/admin/topics/list/")
@superuser_login
def topic_table_list():
    deleted = request.args.get('deleted')
    if deleted not in ["True", "False"]:
        abort(404)
    status = True if deleted == "True" else False

    fields = ['id', 'title', 'reply_count', 'username', 'node_title']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    topics = Topic.query.filter_by(deleted=status).all()
    map(lambda x: setattr(x, 'username', x.user().username), topics)
    map(lambda x: setattr(x, 'node_title', x.node().title), topics)

    # Filter the topic according to the keywords.
    key = request.args.get('sSearch')
    if key:
        topics = list(filter(lambda x: (key == str(x.id) or key == str(x.reply_count) or key in x.title or
                                        key in x.username or key in x.node_title), topics))

    # Sort the data according to specified columns.
    topics.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['aaData'] = []
    data['iTotalDisplayRecords'] = len(topics)
    data['iTotalRecords'] = Topic.query.count()

    topics = topics[start:start + length]
    map(lambda x: setattr(x, 'more',
                          '<a href="%s" class="label label-success">%s</a>' %
                          (url_for('brother.topic_more', tid=x.id), gettext('more'))), topics)
    data['aaData'] = [[t.id, t.title, t.reply_count, t.username, t.node_title, t.more] for t in topics]

    return jsonify(**data)


@brother.route("/admin/nodes/list/")
@superuser_login
def node_table_list():
    deleted = request.args.get('deleted')
    if deleted not in ["True", "False"]:
        abort(404)
    status = True if deleted == "True" else False

    fields = ['id', 'title', 'description', 'count']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    nodes = Node.query.filter_by(deleted=status).all()
    # Filter the users according to the keywords.
    key = request.args.get('sSearch')

    map(lambda x: setattr(x, 'count', 0 if not x.topics else len(x.topics.split(","))), nodes)
    if key:
        nodes = list(filter(lambda x: (key == str(x.id) or key in x.title or
                                       key in x.description or key == str(x.count)), nodes))

    # Sort the data according to specified columns.
    nodes.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['iTotalDisplayRecords'] = len(nodes)
    data['iTotalRecords'] = Node.query.count()
    nodes = nodes[start:start + length]
    map(lambda x: setattr(x, 'more',
                          '<a href="%s" class="label label-success">%s</a>' %
                          (url_for('brother.node_more', nid=x.id), gettext('more'))), nodes)
    data['aaData'] = [[n.id, n.title, n.description, n.count, n.more] for n in nodes]

    return jsonify(**data)


@brother.route("/admin/comments/list/")
@superuser_login
def comment_table_list():
    deleted = request.args.get('deleted')
    if deleted not in ["True", "False"]:
        abort(404)
    status = True if deleted == "True" else False

    fields = ['id', 'content', 'username', 'topic']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    comments = list(filter(lambda x: x.deleted == status, Comment.query.all()))
    map(lambda x: setattr(x, 'username', x.user().username), comments)
    map(lambda x: setattr(x, 'topic', x.topic().title), comments)

    # Filter the comments according to the keywords.
    key = request.args.get('sSearch')
    if key:
        comments = list(filter(lambda x: (key == str(x.id) or key in x.content or
                                          key in x.username or key in x.topic), comments))

    # Sort the data according to specified columns.
    comments.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['iTotalDisplayRecords'] = len(comments)
    data['iTotalRecords'] = Comment.query.count()
    comments = comments[start:start + length]
    data['aaData'] = [[c.id, c.content, c.username, c.topic] for c in comments]
    return jsonify(**data)


@brother.route("/admin/users/list/")
@superuser_login
def user_table_list():
    deleted = request.args.get('deleted')
    if deleted not in ["True", "False"]:
        abort(404)
    status = True if deleted == "True" else False
    fields = ['id', 'username', 'email', 'last_login', 'is_superuser', 'topics_cnt', 'comments_cnt']
    order_dir = request.args.get('sSortDir_0')
    order_field = int(request.args.get('iSortCol_0'))
    length = int(request.args.get('iDisplayLength', 10))
    start = int(request.args.get('iDisplayStart', 0))

    users = User.query.filter_by(deleted=status).all()
    map(lambda x: setattr(x, 'topics_cnt',
                          '<a href="%s" class="label label-success">%s</a>' %
                          (url_for('brother.user_more', uid=x.id, content='Topic'),
                           0 if not x.topics else len(x.topics.split(',')))), users)
    map(lambda x: setattr(x, 'comments_cnt',
                          '<a href="%s" class="label label-success">%s</a>' %
                          (url_for('brother.user_more', uid=x.id, content='Comment'),
                           0 if not x.comments else len(x.comments.split(',')))), users)
    # Filter the users according to the keywords.
    key = request.args.get('sSearch')
    if key:
        users = list(filter(lambda x: (key == str(x.id) or key in x.username or
                                       key in x.email), users))

    # Sort the data according to specified columns.
    users.sort(key=lambda x: getattr(x, fields[order_field]), reverse=False if order_dir == 'asc' else True)

    # Put data together to response.
    data = dict()
    data['iTotalDisplayRecords'] = len(users)
    data['iTotalRecords'] = User.query.count()
    users = users[start:start + length]
    data['aaData'] = [[u.id, u.username, u.email, natural_time(u.last_login),
                       str(u.is_superuser), u.topics_cnt, u.comments_cnt] for u in users]

    return jsonify(**data)


@brother.route("/admin/topics/process/")
@superuser_login
def topic_bulk_process():
    process = request.args.get('process')
    if process not in ['active', 'del']:
        abort(404)
    topic_status = True if process == 'del' else False
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        i_topic = Topic.query.filter_by(id=i).first()
        i_topic.process(status=topic_status, cause=2)

    db.session.commit()
    return "Done"


@brother.route("/admin/nodes/process/")
@superuser_login
def node_bulk_process():
    process = request.args.get('process')
    if process not in ['active', 'del']:
        abort(404)
    node_status = True if process == 'del' else False
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        i_node = Node.query.filter_by(id=i).first()
        i_node.process(status=node_status)

    db.session.commit()
    return "Done"       # Just return to fit the flask syntax.


@brother.route("/admin/comments/process/")
@superuser_login
def comment_bulk_process():
    process = request.args.get('process')
    if process not in ['active', 'del']:
        abort(404)
    comment_status = True if process == 'del' else False
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        i_comment = Comment.query.filter_by(id=i).first()
        i_comment.process(status=comment_status, cause=2)

    db.session.commit()
    return "Done"       # Just return to fit the flask syntax.


@brother.route("/admin/users/process/")
@superuser_login
def user_bulk_process():
    process = request.args.get('process')
    if process not in ['active', 'del']:
        abort(404)
    user_status = True if process == 'del' else False
    ids = request.args.get('ids')
    ids = ids.split(',')
    for i in ids:
        i_user = User.query.filter_by(id=i).first()
        i_user.process(status=user_status)
    db.session.commit()
    return "Done"


@brother.route("/admin/topic/process/<int:tid>/")
@superuser_login
def topic_process(tid):
    process = request.args.get('process')
    if process not in ['active', 'del']:
        abort(404)
    status = True if process == 'del' else False

    t = Topic.query.filter_by(id=tid).first_or_404()
    if t.topic_deleted == status:
        return redirect(request.args.get('next') or
                        url_for("brother.topic_manage", classify="deleted" if status else 'normal'))

    t.process(status=status, cause=2)
    db.session.commit()
    return redirect(request.args.get('next') or
                    url_for('brother.topic_manage', classify="deleted" if status else 'normal'))


@brother.route("/admin/appendix/process/<int:aid>/")
@superuser_login
def appendix_process(aid):
    process = request.args.get('process')
    if process not in ['del', 'active']:
        abort(404)

    status = True if process == "del" else False

    ta = TopicAppend.query.filter_by(id=aid).first_or_404()
    if ta.append_deleted == status:
        return redirect(request.args.get('next') or url_for("brother.topic_more", tid=ta.topic_id))

    ta.process(status=status, cause=1)
    db.session.commit()
    return redirect(url_for("brother.topic_more", tid=ta.topic_id))


@brother.route("/admin/comment/process/<int:cid>/")
@superuser_login
def comment_process(cid):
    process = request.args.get('process')
    if process not in ['del', 'active']:
        abort(404)

    status = True if process == "del" else False

    c = Comment.query.filter_by(id=cid).first_or_404()
    if c.comment_deleted == status:
        return redirect(request.args.get('next') or url_for("brother.topic_more", tid=c.topic_id))

    c.process(status=status, cause=2)
    db.session.commit()
    return redirect(request.args.get('next') or url_for("brother.topic_more", tid=c.topic_id))


@brother.route("/admin/user/process/<int:uid>/")
@superuser_login
def user_process(uid):
    """ Move the user to blacklist.

    Delete or add all the topics and comments the user has made at the same time
    """
    process = request.args.get('process')
    if process not in ['del', 'active']:
        abort(404)

    status = True if process == "del" else False
    u = User.query.filter_by(id=uid).first_or_404()
    if u.is_superuser or u.deleted == status:
        return redirect(request.args.get('next') or
                        url_for("brother.user_manage", classify="deleted" if status else 'normal'))

    u.process(status=True)
    db.session.commit()
    return redirect(request.args.get('next') or
                    url_for("brother.user_manage", classify="deleted" if status else 'normal'))


@brother.route("/admin/node/create/", methods=['GET', 'POST'])
@superuser_login
def node_create():
    if request.method == 'GET':
        return render_template('brother/node_create.html',
                               title=gettext('Create Node'),
                               form=Node)
    elif request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        n = Node(title, description)
        db.session.add(n)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('brother.node_manage', classify="normal"))
    else:
        abort(404)
