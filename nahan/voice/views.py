#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:03

from flask import render_template, redirect, request, url_for, abort
from . import voice
from flask_babel import gettext
from ..models import Topic, TopicAppend, Node, Notify, Comment, User
from flask_login import login_user, logout_user, login_required, current_user
import json
import markdown
from .. import db
from flask_paginate import Pagination


@voice.route('/')
def index():
    # nodes = Node.query.all()
    # user_count = User.query.count()
    # topic_count = Topic.query.count()
    # comment_count = Comment.query.count()
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page-1)*per_page
    topics_all = Topic.query.filter_by(deleted=False).order_by(Topic.time_created).all()[:120]
    topics = topics_all[offset:offset+per_page]
    pagination = Pagination(page=page, total=len(topics_all), per_page=per_page,record_name='topics',CSS_FRAMEWORK = 'bootstrap',bs_version=3)
    return render_template('voice/index.html',
                           topics=topics,
                           title=gettext('Latest Topics'),
                           post_list_title=gettext('Latest Topics'),
                           pagination=pagination)


@voice.route("/voice/hot")
def hot():
    return "Hot"


@voice.route("/voice/view/<int:tid>", methods=['GET', 'POST'])
def view(tid):
    topic = Topic.query.filter_by(id=tid).first()
    live_comments_all = topic.extract_comments()
    per_page = 10
    page = int(request.args.get('page', 1))
    offset = (page-1)*per_page
    live_comments = live_comments_all[offset:offset+per_page]
    pagination = Pagination(page=page, total=len(live_comments), per_page=15, record_name="live_comments",CSS_FRAMEWORK = 'bootstrap',bs_version=3)

    if request.method == 'GET':
        topic.click += 1
        db.session.commit()
        return render_template('voice/topic.html', topic=topic,
                               comments=live_comments, pagination=pagination)

    # Save the comment and update the topic view page.
    elif request.method == 'POST':
        reply_content = request.form['content']

        if not reply_content or len(reply_content) > 140:
            message = gettext('Comment cannot be empty or too large')
            return render_template("voice/topic.html", message=message,
                                   topic=topic, pagination=pagination)

        r = Comment(reply_content, current_user.id, tid)
        db.session.add(r)
        db.session.commit()

        topic.add_comments(r.id)
        db.session.commit()
        return render_template('voice/topic.html', topic=topic, comments=live_comments+[r],
                               pagination=pagination)
    else:
        abort(404)


@voice.route("/voice/create", methods=['GET', 'POST'])
def create():
    # Add the topic to a specified node.
    if request.method == 'GET':
        return render_template('voice/create.html', nodes=Node.query.all())
    elif request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        node_id = Node.get_id(request.form['node'])
        user_id = current_user.id
        new_topic = Topic(user_id, title, content, node_id)
        db.session.add(new_topic)
        db.session.commit()
        topic_id = new_topic.id
        return redirect(url_for('voice.view', tid=topic_id))


@voice.route("/voice/append/<int:tid>", methods=['GET', 'POST'])
def appendix(tid):
    topic = Topic.query.filter_by(id=tid).first()
    if current_user.id != topic.user().id:
        abort(403)

    if request.method == 'GET':
        return render_template('voice/append.html', topic=topic)

    elif request.method == 'POST':
        append_c = request.form['content']
        if not append_c:
            message = gettext('content cannot be empty')
            return render_template(
                'voice/append.html', topic=topic, message=message)

        topic_append = TopicAppend(append_c, tid)
        db.session.add(topic_append)
        db.session.commit()
        topic.add_appends(topic_append.id)
        db.session.commit()
        return redirect(url_for('voice.view', tid=topic.id, _anchor='append'))


@voice.route("/voice/delete/<int:tid>")
def delete(tid):
    return "Delete %d" % tid


@voice.route("/voice/edit/<int:tid>", methods=['GET', 'POST'])
def edit(tid):
    topic = Topic.query.filter_by(id=tid).first()
    if current_user.id != topic.user().id and (not current_user.is_administrator()):
        return redirect(url_for('voice.view'), tid=topic.id)
    if request.method == 'GET':
        return render_template('voice/edit.html', topic=topic)
    elif request.method == 'POST':
        topic.content = request.form['content']
        if not topic.content:
            message = gettext('content cannot be empty')
            return render_template('voice/edit.html', topic=topic, message=message)

        topic.content_rendered = markdown.markdown(topic.content, ['codehilite'], safe_mode='escape')
        db.session.commit()
        return redirect(url_for('voice.view', tid=topic.id))


@voice.route("/previewer", methods=['POST'])
def previewer():
    """ Return the content after rendered by markdown.

    The previewer.js will need the rendered content.
    """
    c = request.form['content']
    md = dict()
    md['marked'] = markdown.markdown(c, ['codehilite'], safe_mode='escape')
    if request.method == 'POST':
        return json.dumps(md)


@voice.route("/nodes")
def all_nodes():
    return render_template('voice/node_all.html', nodes=Node.query.all())


@voice.route("/node/view/<int:nid>")
def node_view(nid):
    return "Node %d" % nid


@voice.route("/comment/delete/<int:cid>")
def comment_delete(cid):
    return "Delete %d" % cid


#     url(r'^post/(?P<post_id>\d+)/delete/$',
#         'del_reply', name='delete_post'),
#     url(r'^search/(?P<keyword>.*?)/$',
#         'search', name='search'),
#     url(r'^hottest/$', 'hottest', name='hottest'),
# )
