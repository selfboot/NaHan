#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:03

from flask import render_template, redirect, request, url_for, abort, current_app
from . import voice
from flask_babel import gettext
from ..models import Topic, TopicAppend, Node, Comment
from flask_login import login_required, current_user
import json
import markdown
from .. import db
from ..util import add_user_links_in_content, add_notify_in_content
from flask_paginate import Pagination
from sqlalchemy import and_


@voice.route('/')
def index():
    per_page = current_app.config['PER_PAGE']
    page = int(request.args.get('page', 1))
    offset = (page-1)*per_page
    topics_all = Topic.query.filter_by(deleted=False).order_by(Topic.time_created).all()[:-120:-1]
    topics = topics_all[offset:offset+per_page]
    pagination = Pagination(page=page, total=len(topics_all),
                            per_page=per_page,
                            record_name='topics',
                            CSS_FRAMEWORK='bootstrap',
                            bs_version=3)
    return render_template('voice/index.html',
                           topics=topics,
                           title=gettext('Latest Topics'),
                           post_list_title=gettext('Latest Topics'),
                           pagination=pagination)


@voice.route("/voice/hot")
def hot():
    """ Show the hottest topics recently.

    Sort the topic by reply_count, if have same reply_count, then sort by click.
    """
    per_page = current_app.config['PER_PAGE']
    page = int(request.args.get('page', 1))
    offset = (page-1)*per_page
    topics_all = Topic.query.filter_by(deleted=False).order_by(Topic.reply_count, Topic.click).all()[:-120:-1]
    topics = topics_all[offset:offset+per_page]
    pagination = Pagination(page=page, total=len(topics_all),
                            per_page=per_page,
                            record_name='topics',
                            CSS_FRAMEWORK='bootstrap',
                            bs_version=3)
    return render_template('voice/index.html',
                           topics=topics,
                           title=gettext('Latest Topics'),
                           post_list_title=gettext('Latest Topics'),
                           pagination=pagination)


@voice.route("/voice/view/<int:tid>", methods=['GET', 'POST'])
def view(tid):
    per_page = current_app.config['PER_PAGE']
    topic = Topic.query.filter_by(id=tid).first_or_404()
    live_comments_all = topic.extract_comments()
    page = int(request.args.get('page', 1))
    offset = (page-1)*per_page
    live_comments = live_comments_all[offset:offset + per_page]
    pagination = Pagination(page=page, total=len(live_comments_all),
                            per_page=per_page,
                            record_name="live_comments",
                            CSS_FRAMEWORK='bootstrap',
                            bs_version=3)

    if request.method == 'GET':
        topic.click += 1
        db.session.commit()
        return render_template('voice/topic.html',
                               topic=topic,
                               comments=live_comments,
                               pagination=pagination)

    # Save the comment and update the topic view page.
    elif request.method == 'POST':
        if not current_user.is_authenticated:
            abort(403)

        reply_content = request.form['content']

        if not reply_content or len(reply_content) > 140:
            message = gettext('Comment cannot be empty or too large')
            return render_template("voice/topic.html",
                                   message=message,
                                   topic=topic,
                                   comments=live_comments,
                                   pagination=pagination)

        """
        Need to process the @user notify in the reply.
        We need to generate links about the user who is mentioned.
        And at the same time, we need a simple notify system to generate a message.
        """
        c = Comment(reply_content, current_user.id, tid)
        c.content_rendered = add_user_links_in_content(c.content_rendered)
        db.session.add(c)
        db.session.commit()

        topic.add_comments(c.id)
        db.session.commit()

        # Generate notify from the reply content.
        add_notify_in_content(c.content, current_user.id, tid, c.id)

        # Add the new comment to current page.
        live_comments_all += [c]
        live_comments = live_comments_all[offset:offset + per_page]
        pagination = Pagination(page=page, total=len(live_comments_all),
                                per_page=per_page,
                                record_name="live_comments",
                                CSS_FRAMEWORK='bootstrap',
                                bs_version=3)
        return render_template('voice/topic.html',
                               topic=topic,
                               comments=live_comments,
                               pagination=pagination)
    else:
        abort(404)


@voice.route("/voice/create", methods=['GET', 'POST'])
@login_required
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
        new_topic.content_rendered = add_user_links_in_content(new_topic.content_rendered)
        db.session.add(new_topic)
        db.session.commit()
        topic_id = new_topic.id

        # Generate notify from the topic content.
        add_notify_in_content(new_topic.content, current_user.id, topic_id)

        return redirect(url_for('voice.view', tid=topic_id))
    else:
        abort(404)


@voice.route("/voice/append/<int:tid>", methods=['GET', 'POST'])
@login_required
def appendix(tid):
    topic = Topic.query.filter_by(id=tid).first_or_404()
    if current_user.id != topic.user().id and (not current_user.is_superuser):
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
        topic_append.content_rendered = add_user_links_in_content(topic_append.content_rendered)
        db.session.add(topic_append)
        db.session.commit()
        topic.add_appends(topic_append.id)
        db.session.commit()

        # Generate notify from the topic content.
        add_notify_in_content(topic_append.content, current_user.id, tid)

        return redirect(url_for('voice.view', tid=topic.id, _anchor='append'))
    else:
        abort(404)


@voice.route("/voice/delete/<int:tid>")
def delete(tid):
    return "Delete %d" % tid


@voice.route("/voice/edit/<int:tid>", methods=['GET', 'POST'])
@login_required
def edit(tid):
    topic = Topic.query.filter_by(id=tid).first_or_404()
    if current_user.id != topic.user().id and (not current_user.is_superuser):
        abort(403)
    if request.method == 'GET':
        return render_template('voice/edit.html', topic=topic)
    elif request.method == 'POST':
        topic.content = request.form['content']
        if not topic.content:
            message = gettext('content cannot be empty')
            return render_template('voice/edit.html', topic=topic, message=message)

        content_rendered = markdown.markdown(topic.content, ['codehilite'], safe_mode='escape')
        topic.content_rendered = add_user_links_in_content(content_rendered)
        db.session.commit()

        # Generate notify from the topic content.
        add_notify_in_content(topic.content, current_user.id, topic.id)
        return redirect(url_for('voice.view', tid=topic.id))


@voice.route("/previewer", methods=['POST'])
def previewer():
    """ Return the content after rendered by markdown.

    The previewer.js will need the rendered content.
    """
    c = request.form['content']
    md = dict()
    content = markdown.markdown(c, ['codehilite'], safe_mode='escape')
    content = add_user_links_in_content(content)
    md['marked'] = content
    if request.method == 'POST':
        return json.dumps(md)


@voice.route("/nodes")
def all_nodes():
    return render_template('voice/node_all.html', nodes=Node.query.all())


@voice.route("/node/view/<int:nid>")
def node_view(nid):
    per_page = current_app.config['PER_PAGE']
    page = int(request.args.get('page', 1))
    offset = (page-1)*per_page
    topics_all = Topic.query.filter_by(deleted=False, node_id=nid).order_by(Topic.reply_count,
                                                                            Topic.click).all()[:-120:-1]
    topics = topics_all[offset:offset+per_page]
    pagination = Pagination(page=page, total=len(topics_all),
                            per_page=per_page,
                            record_name='topics',
                            CSS_FRAMEWORK='bootstrap',
                            bs_version=3)
    return render_template('voice/node_view.html',
                           topics=topics,
                           title=gettext('Node view'),
                           post_list_title=gettext("This node's Topics"),
                           pagination=pagination)
    return render_template('voice/node_view.html')


@voice.route("/comment/delete/<int:cid>")
def comment_delete(cid):
    return "Delete %d" % cid


@voice.route("/search/<keywords>")
def search(keywords):
    """ Search the topic which contains all the keywords in title or content.

    Refer to:
    Object Relational Tutorial
    http://docs.sqlalchemy.org/en/rel_0_9/orm/tutorial.html#common-filter-operators
    query.filter(User.name.like('%ed%'))
    query.filter(and_(User.name == 'ed', User.fullname == 'Ed Jones'))
    query.filter(or_(User.name == 'ed', User.name == 'wendy'))
    """

    keys = keywords.split(' ')
    title_topics = Topic.query.filter(and_(*[Topic.title.like("%"+k+"%") for k in keys])).all()
    content_topics = Topic.query.filter(and_(*[Topic.content.like("%"+k+"%") for k in keys])).all()
    all_topics = title_topics + content_topics

    per_page = current_app.config['PER_PAGE']
    page = int(request.args.get('page', 1))
    offset = (page-1)*per_page
    topics = all_topics[offset:offset + per_page]
    pagination = Pagination(page=page, total=len(all_topics),
                            per_page=per_page,
                            record_name="topic",
                            CSS_FRAMEWORK='bootstrap',
                            bs_version=3)
    return render_template(
        'voice/index.html',
        title="%s%s" % (keywords, gettext(' -search result')),
        topics=topics,
        post_list_title="%s%s" % (keywords, gettext("'s search result")),
        pagination=pagination)


#     url(r'^post/(?P<post_id>\d+)/delete/$',
#         'del_reply', name='delete_post'),
# )
