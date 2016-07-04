#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:03

from flask import render_template, redirect, request, url_for, flash
from . import voice
from flask_babel import gettext
from ..models import Topic, TopicAppend, Node, Notify, Comment, User
from flask_login import login_user, logout_user, login_required, current_user


@voice.route('/')
def index():
    nodes = Node.query.all()
    user_count = User.query.count()
    topic_count = Topic.query.count()
    comment_count = Comment.query.count()
    topics = Topic.query.filter(Topic.deleted == False).order_by(Topic.last_replied).all()[0:30]
    post_list_title = gettext('Latest Topics')

    return render_template('voice/index.html',
                           topics=topics,
                           title='home',
                           post_list_title=post_list_title)


@voice.route("/voice/hot")
def hot():
    return "Hot"


@voice.route("/voice/view/<int:topic_id>")
def view(topic_id):
    return "%d" % topic_id


@voice.route("/voice/edit/<int:node_id>")
def edit(node_id):
    return "Edit %s" % node_id


@voice.route("/nodes")
def all_nodes():
    return "All"


@voice.route("/node/view/<int:node_id>")
def node_view(node_id):
    return "Node %d" % node_id


# urlpatterns = patterns(
#     'forum.views',
#     url(r'^$', 'index', name='index'),
#     url(r'^topic/(?P<topic_id>\d+)/reply/$',
#         'create_reply', name='create_reply'),
#     url(r'^topic/(?P<topic_id>\d+)/append/$',
#         'add_appendix', name='add_appendix'),
#     url(r'^topic/(?P<topic_id>\d+)/delete/$',
#         'del_topic', name='delete_topic'),
#     url(r'^topic/(?P<topic_id>\d+)/edit/$',
#         'edit_topic', name='edit_topic'),
#     url(r'^post/(?P<post_id>\d+)/delete/$',
#         'del_reply', name='delete_post'),
#     url(r'^node/$', 'node_all', name='node_all'),
#     url(r'^node/(?P<node_id>\d+)/create/$',
#         'create_topic', name='create_topic'),
#     url(r'^search/(?P<keyword>.*?)/$',
#         'search', name='search'),
#     url(r'^hottest/$', 'hottest', name='hottest'),
#     url(r'^previewer/$', 'previewer', name='previewer'),
# )