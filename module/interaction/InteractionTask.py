# -*- coding: utf-8 -*-
"""
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License,
    or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.

    @author: RaNaN
"""

from time import time

from module.Api import InteractionTask as BaseInteractionTask
from module.Api import Input, Output

#noinspection PyUnresolvedReferences
class InteractionTask(BaseInteractionTask):
    """
    General Interaction Task extends ITask defined by thrift with additional fields and methods.
    """
    #: Plugins can put needed data here
    storage = None
    #: Timestamp when task expires
    wait_until = 0
    #: The received result as string representation
    result = None
    #: List of registered handles
    handler = None
    #: Error Message
    error = None

    def __init__(self, *args, **kwargs):
        BaseInteractionTask.__init__(self, *args, **kwargs)

        # additional internal attributes
        self.storage = {}
        self.handler = []
        self.wait_until = 0

    def convertResult(self, value):
        return value

    def getResult(self):
        return self.result

    def setResult(self, value):
        pass

    def setWaiting(self, sec):
        self.wait_until = max(time() + sec, self.wait_until)

    def isWaiting(self, sec):
        if self.result or self.error or time() > self.waitUntil:
            return False

        return True

    def timedOut(self):
        return time() > self.waitUntil

    def correct(self):
        [x.taskCorrect(self) for x in self.handler]

    def invalid(self):
        [x.taskInvalid(self) for x in self.handler]

    def __str__(self):
        return "<InteractionTask '%s'>" % self.id