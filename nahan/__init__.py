#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-01 10:15:12

from flask import Flask
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import config


mail = Mail()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    from .user import user as user_blueprint
    app.register_blueprint(user_blueprint, url_prefix='/user')
    from .voice import voice as voice_blueprint
    app.register_blueprint(voice_blueprint)
    from .brother import brother as brother_blueprint
    app.register_blueprint(brother_blueprint)
    return app
