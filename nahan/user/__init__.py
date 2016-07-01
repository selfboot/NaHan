#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-06-30 21:55:44

from flask import Blueprint
user = Blueprint('user', __name__)
from . import views
