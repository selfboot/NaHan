#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 15:57:33
import hashlib
import urllib
from datetime import datetime
from flask_login import UserMixin
from flask import current_app
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

    nickname = db.Column(db.String(64), nullable=True)
    website = db.Column(db.String(64), nullable=True)
    avatar_url = db.Column(db.String(64), nullable=True)
    use_avatar = db.Column(db.Boolean, default=True)

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

    @property
    def print_name(self):
        if self.nickname:
            return self.nickname
        else:
            return self.username

    def avatar(self):
        da = ''  # default avatar
        dic = {}
        if self.use_avatar:
            mail = self.email.lower()
            avatar_url = "http://www.gravatar.com/avatar/"
            base_url = avatar_url + hashlib.md5(mail).hexdigest() + "?"
            dic['small'] = base_url + urllib.urlencode({'d': da, 's': '40'})
            dic['middle'] = base_url + urllib.urlencode({'d': da, 's': '48'})
            dic['large'] = base_url + urllib.urlencode({'d': da, 's': '80'})
            return dic
        elif self.avatar_url:
            dic['small'] = self.avatar_url
            dic['middle'] = self.avatar_url
            dic['large'] = self.avatar_url
        return dic

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_administrator(self):
        return self.is_superuser

    def unread_nofity_count(self):
        # TODO
        return 1

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.commit()
        return True


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Topic(db.Model):
    __tablename__ = "topic"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(128))
    content = db.Column(db.Text())
    content_rendered = db.Column(db.Text())

    click = db.Column(db.Integer, default=0)
    reply_count = db.Column(db.Integer, default=0)

    deleted = db.Column(db.Boolean(), default=False)
    time_created = db.Column(db.DateTime(), default=datetime.utcnow)
    last_replied = db.Column(db.DateTime(), default=datetime.utcnow)

    # User create a topic at topic_id which belong to the node.
    user_id = db.Column(db.Integer)
    node_id = db.Column(db.Integer)

    # Keep all the append and comment about the topic.
    appends = db.Column(db.Text(), default="")
    comments = db.Column(db.Text(), default="")


class TopicAppend(db.Model):
    __tablename__ = "append"
    id = db.Column(db.Integer, primary_key=True)

    time_created = db.Column(db.DateTime(), default=datetime.utcnow)
    content = db.Column(db.Text())
    content_rendered = db.Column(db.Text())
    deleted = db.Column(db.Boolean(), default=False)

    topic_id = db.Column(db.Integer)


class Comment(db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text())
    content_rendered = db.Column(db.Text())

    deleted = db.Column(db.Boolean(), default=False)
    time_created = db.Column(db.DateTime(), default=datetime.utcnow)

    # User make a comment at one topic.
    user_id = db.Column(db.Integer)
    topic_id = db.Column(db.Integer)


class Node(db.Model):
    __tablename__ = "node"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(64))
    description = db.Column(db.Text())

    # Keep all the topics the node have.
    topics = db.Column(db.Text(), default="")

    def __unicode__(self):
        return self.title


class Notify(db.Model):
    __tablename__ = "notify"
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(db.Text())
    is_read = db.Column(db.Boolean(), default=False)
    time_created = db.Column(db.DateTime(), default=datetime.utcnow)

    # Sender send a message at comment_id of topic_id to receiver_id
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)
    comment_id = db.Column(db.Integer)
    topic_id = db.Column(db.Integer)