# -*- coding: utf-8 -*-
###############################################################################
#   Copyright(c) 2009-2017 pyLoad Team
#   https://pyload.net
#
#   This file is part of pyLoad.
#   pyLoad is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Subjected to the terms and conditions in LICENSE
#
#   @author: RaNaN
###############################################################################

from __future__ import unicode_literals
from time import time

from pyload.Api import InteractionTask as BaseInteractionTask
from pyload.Api import Interaction, InputType, Input


# noinspection PyUnresolvedReferences
class InteractionTask(BaseInteractionTask):
    """
    General Interaction Task extends ITask defined by api with additional fields and methods.
    """
    #: Plugins can put needed data here
    storage = None
    #: Timestamp when task expires
    wait_until = 0
    #: The received result
    result = None
    #: List of registered handles
    handler = None
    #: Error Message
    error = None
    #: Timeout locked
    locked = False
    #: A task that was retrieved counts as seen
    seen = False
    #: A task that is relevant to every user
    shared = False
    #: primary uid of the owner
    owner = None

    def __init__(self, *args, **kwargs):
        if 'owner' in kwargs:
            self.owner = kwargs['owner']
            del kwargs['owner']
        if 'shared' in kwargs:
            self.shared = kwargs['shared']
            del kwargs['shared']

        BaseInteractionTask.__init__(self, *args, **kwargs)

        # additional internal attributes
        self.storage = {}
        self.handler = []
        self.wait_until = 0

    def convertResult(self, value):
        if self.input.type == InputType.Click:
            parts = value.split(',')
            return int(parts[0]), int(parts[1])

        #TODO: convert based on input/output
        return value

    def getResult(self):
        return self.result

    def setShared(self):
        """ enable shared mode, should not be reversed"""
        self.shared = True

    def setResult(self, value):
        self.result = self.convertResult(value)

    def setWaiting(self, sec, lock=False):
        """ sets waiting in seconds from now, < 0 can be used as infinitive  """
        if not self.locked:
            if sec < 0:
                self.wait_until = -1
            else:
                self.wait_until = max(time() + sec, self.wait_until)

            if lock: self.locked = True

    def isWaiting(self):
        if self.result or self.error or self.timedOut():
            return False

        return True

    def timedOut(self):
        return time() > self.wait_until > -1

    def correct(self):
        [x.taskCorrect(self) for x in self.handler]

    def invalid(self):
        [x.taskInvalid(self) for x in self.handler]
