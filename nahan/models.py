#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 15:57:33

import markdown
from datetime import datetime
from flask_login import UserMixin
from flask import current_app, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)

    is_superuser = db.Column(db.Boolean, default=False)
    is_password_reset_link_valid = db.Column(db.Boolean, default=True)
    deleted = db.Column(db.Boolean, default=False)

    website = db.Column(db.String(64), nullable=True)
    avatar_url = db.Column(db.String(64), default="http://www.gravatar.com/avatar/")

    last_login = db.Column(db.DateTime(), default=datetime.utcnow)
    date_joined = db.Column(db.DateTime(), default=datetime.utcnow)

    # Keep all the topics, comments the user has created.
    topics = db.Column(db.Text(), default="")
    comments = db.Column(db.Text(), default="")

    # Keep all the notify id.  User can have more than one read or unread notify.
    unread_notify = db.Column(db.Text(), default="")
    read_notify = db.Column(db.Text(), default="")

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def unread_notify_count(self):
        if not self.unread_notify:
            return 0
        return len(self.unread_notify.split(","))

    def generate_reset_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        uid = data.get('id')
        if uid:
            return User.query.get(uid)
        return None

    def extract_unread_notify(self):
        if self.unread_notify:
            notify_id = list(map(int, self.unread_notify.split(',')))
            all_notify = [Notify.query.filter_by(id=i).first() for i in notify_id]
            return all_notify
        else:
            return []

    def extract_read_notify(self):
        if self.read_notify:
            notify_id = list(map(int, self.read_notify.split(',')))
            all_notify = [Notify.query.filter_by(id=i).first() for i in notify_id]
            return all_notify
        else:
            return []

    def add_topic(self, tid):
        if self.topics:
            self.topics += ",%d" % tid
        else:
            self.topics = "%d" % tid

    def add_comment(self, cid):
        if self.comments:
            self.comments += ",%d" % cid
        else:
            self.comments = "%d" % cid


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Topic(db.Model):
    def __init__(self, user_id, title, content, node_id):
        self.user_id = user_id
        self.title = title
        self.content = content
        self.content_rendered = markdown.markdown(content, ['codehilite'], safe_mode='escape')
        self.time_created = datetime.now()
        self.node_id = node_id

    __tablename__ = "topic"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(128))
    content = db.Column(db.Text())
    content_rendered = db.Column(db.Text())

    click = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)

    # Topic can be deleted by three situations.
    topic_deleted = db.Column(db.Boolean(), default=False)
    node_deleted = db.Column(db.Boolean(), default=False)
    user_deleted = db.Column(db.Boolean(), default=False)

    time_created = db.Column(db.DateTime(), default=datetime.now)
    last_replied = db.Column(db.DateTime())

    # User create a topic at topic_id which belong to the node.
    user_id = db.Column(db.Integer)
    node_id = db.Column(db.Integer)

    # Keep all the append and comment about the topic.
    appends = db.Column(db.Text(), default="")
    comments = db.Column(db.Text(), default="")

    @property
    def deleted(self):
        return self.topic_deleted or self.node_deleted or self.user_deleted

    def extract_appends(self):
        if self.appends:
            append_id = list(map(int, self.appends.split(',')))
            all_appends = [TopicAppend.query.filter_by(id=i).first() for i in append_id]
            live_appends = list(filter(lambda x: x and not x.deleted, all_appends))
            return live_appends
        else:
            return []

    def extract_comments(self):
        if self.comments:
            comment_id = list(map(int, self.comments.split(',')))
            all_comments = [Comment.query.filter_by(id=i).first() for i in comment_id]
            live_comments = list(filter(lambda x: x and not x.deleted, all_comments))
            return live_comments
        else:
            return []

    def add_comments(self, cid):
        if self.comments:
            self.comments += ",%d" % cid
        else:
            self.comments = "%d" % cid

        self.last_replied = datetime.now()
        self.reply_count += 1

    def add_appends(self, aid):
        if self.appends:
            self.appends += ",%d" % aid
        else:
            self.appends = "%d" % aid

    def user(self):
        return User.query.filter_by(id=self.user_id).first()

    def node(self):
        return Node.query.filter_by(id=self.node_id).first()


class TopicAppend(db.Model):
    def __init__(self, content, topic_id):
        self.content = content
        self.topic_id = topic_id
        self.content_rendered = markdown.markdown(content, ['codehilite'], safe_mode='escape')
        self.time_created = datetime.now()

    __tablename__ = "append"
    id = db.Column(db.Integer, primary_key=True)

    time_created = db.Column(db.DateTime(), default=datetime.utcnow)
    content = db.Column(db.Text())
    content_rendered = db.Column(db.Text())
    topic_id = db.Column(db.Integer)

    # Topic append can be deleted by two situations.
    topic_deleted = db.Column(db.Boolean(), default=False)
    append_deleted = db.Column(db.Boolean(), default=False)

    @property
    def deleted(self):
        return self.topic_deleted or self.append_deleted


class Comment(db.Model):
    def __init__(self, content, user_id, topic_id):
        self.content = content
        self.content_rendered = markdown.markdown(content, ['codehilite'], safe_mode='escape')
        self.time_created = datetime.now()
        self.user_id = user_id
        self.topic_id = topic_id

    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text())
    content_rendered = db.Column(db.Text())

    deleted = db.Column(db.Boolean(), default=False)
    time_created = db.Column(db.DateTime(), default=datetime.utcnow)

    # User make a comment at one topic.
    user_id = db.Column(db.Integer)
    topic_id = db.Column(db.Integer)

    # Comment can be deleted by two situations.
    topic_deleted = db.Column(db.Boolean(), default=False)
    comment_deleted = db.Column(db.Boolean(), default=False)

    @property
    def deleted(self):
        return self.topic_deleted or self.comment_deleted

    def user(self):
        return User.query.filter_by(id=self.user_id).first()


class Node(db.Model):
    __tablename__ = "node"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(64))
    description = db.Column(db.Text())
    deleted = db.Column(db.Boolean(), default=False)
    # Keep all the topics id the node have.
    topics = db.Column(db.Text(), default="")

    def __unicode__(self):
        return self.title

    def add_topic(self, tid):
        if self.topics:
            self.topics += ",%d" % tid
        else:
            self.topics = "%d" % tid


class Notify(db.Model):
    def __init__(self, sender_id, receiver_id, topic_id, comment_id=None):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.topic_id = topic_id
        self.comment_id = comment_id
        self.time_created = datetime.now()

    __tablename__ = "notify"
    id = db.Column(db.Integer, primary_key=True)

    time_created = db.Column(db.DateTime(), default=datetime.now())

    # User can @somebody at topic, appendix and reply.
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)
    comment_id = db.Column(db.Integer, nullable=True)
    topic_id = db.Column(db.Integer, nullable=True)

    # Comment can be deleted by two situations.
    sender_deleted = db.Column(db.Boolean(), default=False)
    receiver_deleted = db.Column(db.Boolean(), default=False)
    topic_deleted = db.Column(db.Boolean(), default=False)
    comment_deleted = db.Column(db.Boolean(), default=False)

    @property
    def deleted(self):
        return self.sender_deleted or self.receiver_id or self.topic_deleted or self.comment_deleted

    # Need to get more info about this notify:
    # sender_name, topic_title and so on.
    @property
    def topic(self):
        return Topic.query.filter_by(id=self.topic_id).first()

    @property
    def sender(self):
        return User.query.filter_by(id=self.sender_id).first()
