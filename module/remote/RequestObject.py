#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
authored by:  RaNaN

this module handels the incoming requests

"""

class RequestObject(object):
    def __init__(self):
        self.version = 0
        self.sender = "ip"
        self.command = None
        self.function = ""
        self.args = []
        self.response = ""