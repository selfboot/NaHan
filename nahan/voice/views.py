#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 09:44:03

from flask import render_template, redirect, request, url_for, flash
from . import voice
from ..models import Topic, TopicAppend, Node, Notify, Comment, User
from flask_login import login_user, logout_user, login_required, current_user


@voice.route('/', methods=['GET', 'POST'])
def index():
    nodes = Node.query.all()
    user_count = User.query.count()
    topic_count = Topic.query.count()
    comment_count = Comment.query.count()
    topics = Topic.query.all().filter(
        deleted=False).order_by('-last_replied')[0:30]
    post_list_title = 'Latest Topics'

    return render_template('voice/index.html',
                           {'topics': topics,
                            'title': 'home',
                            'post_list_title': post_list_title})
