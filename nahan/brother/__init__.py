#! /usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: xuezaigds@gmail.com
# @Last Modified time: 2016-07-18 21:33:24

from flask import Blueprint
brother = Blueprint('brother', __name__)
from . import views