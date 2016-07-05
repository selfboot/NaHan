#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 15:57:33

from threading import Thread
from flask import current_app
from flask import render_template
from flask_mail import Message
from . import mail


def send_async_email(_app, msg):
    with _app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['FORUM_MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['FORUM_MAIL_SENDER'], recipients=[to])
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr
